from abc import ABC, abstractmethod
from types import MappingProxyType

import pandas as pd
import numpy as np
from datetime import datetime
from typing import (
    List,
    Union, Optional
)
from dataclasses import dataclass

from ts_tariffs.meters import MeterData
from ts_tariffs.ts_utils import FrequencyOption, resample_schema, TouBins, TimeBin, SampleRate
from ts_tariffs.units import ConsumptionUnitOption
from ts_tariffs.utils import Block


class Validator:
    @staticmethod
    def index_as_dt(consumption: Union[pd.Series, pd.DataFrame]):
        if not isinstance(consumption.index.dtype, datetime):
            raise ValueError('DataFrames and Series index must be dtype datetime')


@dataclass(frozen=True)
class AppliedCharge:
    """ Charges related to a tariff and given consumption meter data
    """
    name: str
    charge_ts: Union[pd.DataFrame, pd.Series]
    rate_unit: str
    consumption_units: str
    total: float


@dataclass
class Tariff(ABC):
    name: str
    charge_type: str
    consumption_unit: ConsumptionUnitOption
    rate_unit: str
    sample_rate: Union[SampleRate, datetime]
    adjustment_factor: Optional[float]

    def __post_init__(self):
        if not self.adjustment_factor:
            self.adjustment_factor = 1.0

    @abstractmethod
    def apply(
            self,
            consumption: MeterData,
    ) -> AppliedCharge:
        pass

    @classmethod
    def from_dict(cls, tariff_dict: dict):
        return cls(**tariff_dict)


@dataclass
class SingleRateTariff(Tariff):
    """ Single charge per unit of consumption
    """
    rate: float

    def apply(
            self,
            consumption: MeterData,
    ) -> AppliedCharge:

        charge_vector = consumption.tseries * self.adjustment_factor * self.rate

        return AppliedCharge(
            self.name,
            charge_vector,
            self.rate_unit,
            consumption.units,
            sum(charge_vector)
        )


@dataclass
class ConnectionTariff(Tariff):
    """ Charge applied for having service - applied periodically
    """
    rate: float
    frequency_applied: FrequencyOption

    def apply(
            self,
            consumption: MeterData,
    ) -> AppliedCharge:
        cost_ts = consumption.tseries.resample(
            resample_schema[self.frequency_applied]
        ).sum()
        cost_ts = pd.DataFrame(cost_ts)
        cost_ts['periods'] = 1.0
        cost_ts['charge'] = self.rate * cost_ts['periods']
        cost_ts[f'rate ({self.rate_unit})'] = self.rate
        return AppliedCharge(
            self.name,
            cost_ts,
            self.rate_unit,
            consumption.units,
            sum(cost_ts['charge'])
        )


@dataclass
class TouTariff(Tariff):
    """ Variable charge rate depending on time of day
    """
    tou: TouBins

    def __post_init__(self):
        if isinstance(self.tou, dict):
            self.tou = TouBins(**self.tou)

    def apply(
            self,
            consumption: MeterData,
    ) -> AppliedCharge:
        prices = np.array(self.tou.bin_rates)
        bins = np.digitize(
            consumption.tseries.index.hour.values,
            bins=self.tou.time_bins,
        )
        charge_vector = prices[bins] * consumption.to_numpy()
        cost_ts = pd.DataFrame(consumption.tseries)
        cost_ts['charge'] = charge_vector
        cost_ts[f'rate ({self.rate_unit})'] = prices[bins]

        return AppliedCharge(
            self.name,
            cost_ts,
            self.rate_unit,
            consumption.units,
            sum(charge_vector)
        )


@dataclass
class DemandTariff(Tariff):
    """ Charge applied to the peak consumption value for a given period
    May additionally be specific to times of day (e.g. peak in a month between 3pm and 6pm)
    """
    rate: float
    frequency_applied: str
    times: TimeBin = None

    def __post_init__(self):
        if isinstance(self.times, dict):
            self.times = TimeBin(**self.times)

    def apply(
            self,
            consumption: MeterData,
    ) -> AppliedCharge:
        peaks = consumption.period_peaks(
            self.frequency_applied,
            self.times
        )
        charge_vector = peaks * self.rate
        return AppliedCharge(
            self.name,
            charge_vector,
            self.rate_unit,
            consumption.units,
            sum(charge_vector)
        )


@dataclass
class BlockTariff(Tariff):
    """ Variable charge applied to sum of consumption for a given period,
    between an upper and lower threshold
    (e.g. $0.10/kWh for the first 1000kWh per month, $0.20/kWh for the second 1000kWh in same month)

    """
    frequency_applied: str
    blocks: List[Block]
    bin_rates: List[float]
    bin_labels: List[str]

    def apply(
            self,
            consumption: MeterData,
    ) -> AppliedCharge:
        period_sums = consumption.period_sum(self.frequency_applied)
        charge_ts = pd.DataFrame(period_sums)
        charge_ts['charge_total'] = 0.0
        for j, block in enumerate(self.blocks):
            rate = self.bin_rates[j]
            consumption_in_block = np.clip(
                period_sums,
                block.min,
                block.max
            ) - block.min
            charge_col_name = f'block_{j + 1}_charge'
            charge_ts[charge_col_name] = rate * consumption_in_block * self.adjustment_factor
            charge_ts[f'block_{j + 1}_rate ({self.rate_unit})'] = rate
            charge_ts['charge_total'] += charge_ts[charge_col_name]

        return AppliedCharge(
            self.name,
            charge_ts,
            self.rate_unit,
            consumption.units,
            sum(charge_ts['charge_total'])
        )


@dataclass
class CapacityTariff(Tariff):
    """ Essentially a connection tariff that is multiplied by a specific capacity
    """
    capacity: float
    rate: float
    frequency_applied: FrequencyOption

    def apply(
            self,
            consumption: MeterData,
    ) -> AppliedCharge:
        cost_ts = consumption.tseries.resample(
            resample_schema[self.frequency_applied]
        ).sum()
        cost_ts = pd.DataFrame(cost_ts)
        cost_ts['periods'] = self.capacity
        cost_ts['charge'] = self.rate * cost_ts['periods']
        cost_ts[f'rate ({self.rate_unit})'] = self.rate
        return AppliedCharge(
            self.name,
            cost_ts,
            self.rate_unit,
            consumption.units,
            sum(cost_ts['charge'])
        )


tariffs_map = MappingProxyType({
    'SingleRateTariff': SingleRateTariff,
    'TouTariff': TouTariff,
    'ConnectionTariff': ConnectionTariff,
    'DemandTariff': DemandTariff,
    'BlockTariff': BlockTariff,
    'CapacityTariff': CapacityTariff,
})
