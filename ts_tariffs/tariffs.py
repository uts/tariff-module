from abc import ABC, abstractmethod
from pydantic import BaseModel, ValidationError
from enum import Enum, IntEnum
import pandas as pd
import numpy as np
from datetime import timedelta
from typing import (
    List,
    NamedTuple
)
from ts_tariffs.ts_utils import get_period_statistic, get_intervals_list
from ts_tariffs.datetime_schema import period_schema, periods_slice_schema, resample_schema
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
    max: float
    min: float


class Charge(BaseModel, ABC):
    name: str
    charge_type: str
    consumption_unit: ConsumptionUnit
    rate_unit = str

    @abstractmethod
    def apply_charge(self, meter_ts: pd.DataFrame) -> pd.DataFrame:
        """
        :param meter_ts:
        :return:
        """
        pass


class SingleRateCharge(Charge):
    rate: float

    def apply_charge(self, meter_ts: pd.DataFrame) -> pd.Series:
        return meter_ts['meter_data'] * self.rate


class ConnectionCharge(Charge):
    rate: float
    frequency_applied: str

    def apply_charge(self, meter_ts: pd.DataFrame) -> pd.DataFrame:
        bill = meter_ts.resample(
            resample_schema[self.frequency_applied]
        ).sum()
        bill['bill'] = self.rate
        return bill


class TOUCharge(Charge):
    tou: TOUValidator

    def apply_charge(self, meter_ts: pd.DataFrame) -> pd.DataFrame:
        prices = np.array(self.tou.bin_rates)
        bins = np.digitize(
            meter_ts.index.hour.values,
            bins=self.tou.time_bins
        )
        charge = meter_ts.copy()
        charge['bill'] = prices[bins] * meter_ts['meter_data'].to_numpy()
        return charge


class DemandCharge(Charge):
    #TODO: Add handler for kWh -> kVA

    rate: float
    frequency_applied: str
    tou: TOUValidator

    # def cross_validate(self):
    #     if not any([self.rate, self.tou]):
    #         raise ValidationError(
    #             f'{self.name} schema not valid: Schema for '
    #             f'DemandChargeValidator must contain either '
    #             f'a tou or rate field'
    #         )

    def apply_charge(self, meter_ts: pd.DataFrame) -> pd.DataFrame:
        periods = period_schema[self.frequency_applied]
        period_peaks = get_period_statistic(
            meter_ts,
            'meter_data',
            ['max'],
            periods,
            self.tou
        )
        if self.tou:
            tou_intervals = get_intervals_list(
                self.tou.time_bins,
            )
            for j, interval in enumerate(tou_intervals):
                slices = periods_slice_schema[self.frequency_applied].copy()
                slices.append(interval)
                period_peaks.loc[tuple(slices), 'rate'] =\
                    self.tou.bin_rates[j]
        else:
            period_peaks['rate'] = self.rate
        period_peaks['bill'] = period_peaks['rate'] * period_peaks['max']
        return period_peaks


class BlockCharge(Charge):
    frequency_applied: str
    blocks: List[Block]
    bin_rates: List[float]
    bin_labels: List[str]


    def apply_charge(self, meter_ts: pd.DataFrame) -> pd.DataFrame:
        periods = period_schema[self.frequency_applied]
        cumulative = get_period_statistic(
            meter_ts,
            'meter_data',
            ['sum'],
            periods,
        )
        cumulative['bill'] = 0.0
        for j, block in enumerate(self.blocks):
            rate = self.bin_rates[j]
            rate_col_name = f'block_{j + 1}_energy'
            cumulative[rate_col_name] = np.clip(
                cumulative['sum'],
                block.min,
                block.max
            ) - block.min
            cumulative['bill'] += rate * cumulative[rate_col_name]

        return cumulative


charge_types = {
    'single_rate': SingleRateCharge,
    'time_of_use': TOUCharge,
    'demand_charge': DemandCharge,
    'block': BlockCharge,
    'connection': ConnectionCharge
}


class TariffRegime:
    def __init__(self, tariff_regime: dict):
        self.name = tariff_regime['name']
        # Unpack charges data and instantiate as
        # Charge subclasses
        charges = tariff_regime['charges']
        # self.charges = list([
        #     charge_dict[charge['charge_type']](charge)
        #     for charge in charges]
        # )
        self.charges = []
        errors_dict = {}
        for charge in charges:
            try:
                validated_charge = charge_types[charge['charge_type']](**charge)
                self.charges.append(validated_charge)
            except ValidationError as e:
                errors_dict[charge['name']] = e.errors()
        print(errors_dict)