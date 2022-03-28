from abc import ABC, abstractmethod
from pydantic import ValidationError, validate_arguments
import pandas as pd
import numpy as np
from datetime import timedelta, datetime
from typing import (
    List,
    NamedTuple,
    Union
)
from dataclasses import dataclass

from ts_tariffs.meters import MeterData
from ts_tariffs.ts_utils import get_period_statistic
from ts_tariffs.datetime_schema import period_schema, resample_schema
from ts_tariffs.validation import TOUSchema, ConsumptionUnitSchema


class Validator:
    @staticmethod
    def index_as_dt(consumption: Union[pd.Series, pd.DataFrame]):
        if not isinstance(consumption.index.dtype, datetime):
            raise ValueError('DataFrames and Series index must be dtype datetime')


class Block(NamedTuple):
    min: float
    max: float


@dataclass(frozen=True)
class AppliedCharge:
    tseries: pd.DataFrame
    rate_units: str
    consumption_units: str

    @property
    def total(self):
        return self.tseries['charge'].sum()


@dataclass
class Charge(ABC):
    name: str
    charge_type: str
    consumption_unit: ConsumptionUnitSchema
    rate_unit: str
    calculate_on: str
    adjustment_factor: Union[float, None]

    def __post_init__(self):
        if not self.adjustment_factor:
            self.adjustment_factor = 1.0

    @abstractmethod
    def apply(
            self,
            meter_ts: pd.DataFrame,

    ) -> AppliedCharge:
        """
        """
        pass


@validate_arguments
@dataclass
class SingleRateCharge(Charge):
    rate: float

    def apply(
            self,
            meter: MeterData,
            detailed: bool = True,
    ) -> AppliedCharge:

        tseries = meter.tseries[[self.calculate_on]]
        tseries['charge'] = self.adjustment_factor * tseries[self.calculate_on] * self.rate
        if detailed:
            tseries[f'rate ({self.rate_unit})'] = self.rate
        return AppliedCharge(
            tseries,
            self.rate_unit,
            meter.units[meter.units[self.calculate_on]],
        )


@validate_arguments
@dataclass
class ConnectionCharge(Charge):
    rate: float
    frequency_applied: str

    def apply(
            self,
            meter_ts: pd.DataFrame,
            detailed_bill=False
    ) -> pd.DataFrame:
        bill = meter_ts.copy().resample(
            resample_schema[self.frequency_applied]
        ).sum()
        bill[self.name] = self.adjustment_factor * self.rate
        bill = pd.concat([meter_ts, bill], axis=1)
        if detailed_bill:
            bill[f'rate ({self.rate_unit})'] = self.rate
            return bill
        else:
            return bill[self.name]


@validate_arguments
@dataclass
class TOUCharge(Charge):
    tou: TOUSchema

    def apply(
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

        bill[self.name] = self.adjustment_factor *\
                          prices[bins] * meter_ts[self.calculate_on].to_numpy()
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
            return bill[self.name]


@validate_arguments
@dataclass
class DemandCharge(Charge):
    # TODO: Add handler for kWh -> kVA

    rate: float
    frequency_applied: str

    # def cross_validate(self):
    #     if not any([self.rate, self.tou]):
    #         raise ValidationError(
    #             f'{self.name} schema not valid: Schema for '
    #             f'DemandChargeValidator must contain either '
    #             f'a tou or rate field'
    #         )

    def apply(
            self,
            meter_ts: pd.DataFrame,
            detailed_bill=False
    ) -> pd.DataFrame:
        periods = period_schema[self.frequency_applied]
        grouped_by_max = get_period_statistic(
            meter_ts,
            self.calculate_on,
            'max',
            periods,
        )
        grouped_by_max.set_index('period_start', inplace=True)
        bill = pd.concat([meter_ts, grouped_by_max], axis=1)
        bill[f'rate ({self.rate_unit})'] = self.rate
        bill['period_peak'] = bill['max']
        bill[self.name] = self.adjustment_factor * bill['period_peak'] * bill[f'rate ({self.rate_unit})']

        if detailed_bill:
            return bill
        else:
            return bill[self.name]


@validate_arguments
@dataclass
class TOUDemandCharge(Charge):
    rate: float
    frequency_applied: str
    tou: Union[TOUSchema, None] = None

    #TODO: Fix: This calc works but only for unique peak demand values
    def apply(
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

            self.rate = pd.cut(
                x=meter_ts.index.hour,
                bins=self.tou.time_bins,
                labels=self.tou.bin_rates,
                ordered=False,
                include_lowest=True
            ).astype(float)

            bill['tou'] = pd.cut(
                x=meter_ts.index.hour,
                bins=self.tou.time_bins,
                labels=self.tou.bin_labels,
                ordered=False,
                include_lowest=True
            )

        bill[f'rate ({self.rate_unit})'] = self.rate
        max_mask = meter_ts.groupby(bins)[self.calculate_on].transform(max) == meter_ts[self.calculate_on]
        bill['peaks'] = meter_ts[self.calculate_on][max_mask]
        bill[self.name] = self.adjustment_factor * bill['peaks'] * bill[f'rate ({self.rate_unit})']

        if detailed_bill:
            return bill
        else:
            return bill[self.name]

@validate_arguments
@dataclass
class CapacityCharge(Charge):
    capacity: float
    rate: float
    frequency_applied: str

    def apply(
            self,
            meter_ts: pd.DataFrame,
            detailed_bill=False
    ) -> pd.DataFrame:
        bill = meter_ts.copy().resample(
            resample_schema[self.frequency_applied]
        ).sum()
        bill[self.name] = self.adjustment_factor * self.rate * self.capacity
        bill = pd.concat([meter_ts, bill], axis=1)
        if detailed_bill:
            bill[f'rate ({self.rate_unit})'] = self.rate
            return bill
        else:
            return bill[self.name]


@validate_arguments
@dataclass
class BlockCharge(Charge):
    frequency_applied: str
    blocks: List[Block]
    bin_rates: List[float]
    bin_labels: List[str]

    def apply(
            self,
            meter_ts: pd.DataFrame,
            detailed_bill=False
    ) -> pd.DataFrame:
        periods = period_schema[self.frequency_applied]
        cumulative = get_period_statistic(
            meter_ts,
            self.calculate_on,
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
        cumulative[self.name] *= self.adjustment_factor
        cumulative.set_index('period_start', inplace=True)
        bill = pd.concat([meter_ts, cumulative], axis=1)

        if detailed_bill:
            return bill
        else:
            return bill[self.name]


class TariffRegime:
    def __init__(
            self,
            tariff_json: dict[str] = None,
            tariff_list: List[Charge] = None,
    ):
        if tariff_json:
            self.name = tariff_json['name']
            charges = tariff_json['charges']
            self.charges_dict = {}
            errors_dict = {}
            for charge in charges:
                try:
                    # Instantiate charge with string of type and dict of attrs
                    validated_charge = globals()[charge['charge_type']](**charge)
                    self.charges_dict[validated_charge.name] = validated_charge
                except ValidationError as e:
                    errors_dict[charge['name']] = e.errors()
            print(errors_dict)
        if tariff_list:
            self.charges_dict = {x.name: x for x in tariff_list}

    @property
    def charges(self):
        return list(self.charges_dict.values())

    def delete_charge(self, charge_name: str):
        del self.charges_dict[charge_name]

    def add_charge(self, charge: Charge):
        self.charges_dict[charge.name] = charge
