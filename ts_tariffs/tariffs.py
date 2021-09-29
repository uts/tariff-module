from abc import ABC, abstractmethod
from pydantic import BaseModel, ValidationError
from enum import Enum, IntEnum
import pandas as pd
import numpy as np
from datetime import timedelta
from typing import (
    List,
    NamedTuple,
    Type
)
from ts_tariffs.ts_utils import get_period_statistic
from ts_tariffs.datetime_schema import period_schema, resample_schema
from ts_tariffs.units import consumption_units


def timedelta_builder(deltas: dict):
    return sum([timedelta()])


class FrequencyValidator(BaseModel):
    minutes: int
    hours: int
    days: int
    weeks: int


class TOUValidator(BaseModel):
    time_bins: List[int]
    bin_rates: List[float]
    bin_labels: List[str]


class ConsumptionUnit(str, Enum):
    kWh = 'kWh'
    kVA = 'kVA'
    day = 'day'


class Block(NamedTuple):
    min: float
    max: float


class Charge(BaseModel, ABC):
    name: str
    charge_type: str
    consumption_unit: ConsumptionUnit
    rate_unit: str

    @abstractmethod
    def calculate_charge(self, meter_ts: pd.DataFrame) -> pd.DataFrame:
        """
        :param meter_ts:
        :return:
        """
        pass


class SingleRateCharge(Charge):
    rate: float


    def calculate_charge(
            self,
            meter_ts: pd.DataFrame,
            detailed_bill=False
    ) -> pd.DataFrame:

        bill = meter_ts.copy()
        bill[self.name] = meter_ts['meter_data'] * self.rate
        if detailed_bill:
            bill[f'rate ({self.rate_unit})'] = self.rate
            return bill
        else:
            return bill[[self.name]]


class ConnectionCharge(Charge):
    rate: float
    frequency_applied: str

    def calculate_charge(
            self,
            meter_ts: pd.DataFrame,
            detailed_bill=False
    ) -> pd.DataFrame:
        bill = meter_ts.copy().resample(
            resample_schema[self.frequency_applied]
        ).sum()
        bill[self.name] = self.rate * bill['meter_data']
        bill = pd.concat([meter_ts, bill], axis=1)
        if detailed_bill:
            bill[f'rate ({self.rate_unit})'] = self.rate
            return bill
        else:
            return bill[[self.name]]

class TOUCharge(Charge):
    tou: TOUValidator

    def calculate_charge(
            self,
            meter_ts: pd.DataFrame,
            detailed_bill=False
    ) -> pd.DataFrame:
        prices = np.array(self.tou.bin_rates)
        bins = np.digitize(
            meter_ts.index.hour.values,
            bins=self.tou.time_bins[1:]
        )
        bill = meter_ts.copy()

        bill[self.name] = prices[bins] * meter_ts['meter_data'].to_numpy()
        if detailed_bill:
            bill['tou'] = pd.cut(
                x=meter_ts.index.hour,
                bins=self.tou.time_bins,
                labels=self.tou.bin_labels,
                ordered=False,
                include_lowest=True
            )
            bill[f'rate ({self.rate_unit})'] = prices[bins]
            return bill
        else:
            return bill[[self.name]]


class DemandCharge(Charge):
    #TODO: Add handler for kWh -> kVA

    rate: float
    frequency_applied: str
    tou: TOUValidator = None

    # def cross_validate(self):
    #     if not any([self.rate, self.tou]):
    #         raise ValidationError(
    #             f'{self.name} schema not valid: Schema for '
    #             f'DemandChargeValidator must contain either '
    #             f'a tou or rate field'
    #         )

    def calculate_charge(
            self,
            meter_ts: pd.DataFrame,
            detailed_bill=False
    ) -> pd.DataFrame:
        bill = meter_ts.copy()
        periods = period_schema[self.frequency_applied]
        bins = list([getattr(meter_ts.index, period) for period in periods])
        if self.tou:
            time_bins = pd.cut(
                meter_ts.index.hour,
                self.tou.time_bins,
                include_lowest=True
            )
            bins.append(time_bins)

            rate = pd.cut(
                x=meter_ts.index.hour,
                bins=self.tou.time_bins,
                labels=self.tou.bin_rates,
                ordered=False,
                include_lowest=True
            )

        bill[f'rate ({self.rate_unit})'] = rate.astype(float)
        max_idx = meter_ts.groupby(bins)['meter_data'].transform(max) == meter_ts['meter_data']
        bill['peaks'] = meter_ts['meter_data'][max_idx]
        bill[self.name] = bill['peaks'] * bill[f'rate ({self.rate_unit})']
        if detailed_bill:
            bill['tou'] = pd.cut(
                x=meter_ts.index.hour,
                bins=self.tou.time_bins,
                labels=self.tou.bin_labels,
                ordered=False,
                include_lowest=True
            )
            return bill
        else:
            return bill[[self.name]]


class BlockCharge(Charge):
    frequency_applied: str
    blocks: List[Block]
    bin_rates: List[float]
    bin_labels: List[str]

    def calculate_charge(
            self,
            meter_ts: pd.DataFrame,
            detailed_bill=False
    ) -> pd.DataFrame:
        periods = period_schema[self.frequency_applied]
        cumulative = get_period_statistic(
            meter_ts,
            'meter_data',
            'sum',
            periods,
        )
        cumulative[self.name] = 0.0
        for j, block in enumerate(self.blocks):
            rate = self.bin_rates[j]
            rate_col_name = f'block_{j + 1}_energy'
            cumulative[rate_col_name] = np.clip(
                cumulative['sum'],
                block.min,
                block.max
            ) - block.min
            cumulative[self.name] += rate * cumulative[rate_col_name]
            cumulative[f'block_{j + 1}_rate ({self.rate_unit})'] = rate
        cumulative.set_index('period_start', inplace=True)
        bill = pd.concat([meter_ts, cumulative], axis=1)

        if detailed_bill:
            return bill
        else:
            return bill[[self.name]]


class TariffRegime:
    def __init__(
            self,
            tariff_json: dict[str] = None,
            tariff_list: List[Type[Charge]] = None,
    ):
        if tariff_json:
            self.name = tariff_json['name']
            charges = tariff_json['charges']
            self.charges = []
            errors_dict = {}
            for charge in charges:
                try:
                    # Instantiate charge with string of type and dict of attrs
                    validated_charge = globals()[charge['charge_type']](**charge)
                    self.charges.append(validated_charge)
                except ValidationError as e:
                    errors_dict[charge['name']] = e.errors()
            print(errors_dict)
        if tariff_list:
            self.charges = tariff_list