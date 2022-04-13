import warnings
from abc import ABC, abstractmethod
from types import MappingProxyType

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import (
    List,
    Union, Optional
)
from dataclasses import dataclass, field

from ts_tariffs.meters import MeterData
from ts_tariffs.ts_utils import FrequencyOption, resample_schema, TouBins, TimeWindow, SampleRate, DatetimeWindow, \
    DateWindow
from ts_tariffs.units import ConsumptionUnitOption
from ts_tariffs.utils import Block


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
    sample_rate: Union[SampleRate, timedelta]
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
    time_window: TimeWindow = None

    def apply(
            self,
            consumption: MeterData,
    ) -> AppliedCharge:
        peaks = consumption.period_peaks(
            self.frequency_applied,
            self.time_window
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


@dataclass
class CriticalPeakDemandTariff(Tariff):
    """ Charge calculated by multiplying the tariff rate by the
    average of peak demands during the critical time window on each
    nominated critical demand days
    """
    rate: float
    frequency_applied: FrequencyOption
    period_active: DateWindow
    critical_period: DateWindow
    critical_peak_windows: List[DatetimeWindow]

    def apply(
            self,
            consumption: MeterData,
    ) -> AppliedCharge:

        if not consumption.window_covered(self.critical_period):
            warnings.warn(
                f'The critical period tariff, {self.name}, was not applied '
                f'because the consumption MeterData did not cover the full'
                f' critical period (must include full days within period)\n'
                f'Period covered by consumption: '
                f'{consumption.first_datetime().strftime("%Y-%m-%d %H:%M")} to {consumption.last_datetime().strftime("%Y-%m-%d %H:%M")} \n'
                f'Critical time period coverage: '
                f'{self.critical_period.start.strftime("%Y-%m-%d")} to {self.critical_period.end.strftime("%Y-%m-%d")}',
            )

        if not consumption.window_covered(self.period_active):
            warnings.warn(
                f'The critical period tariff, {self.name}, was not applied to the full period_active window'
                f' because the consumption MeterData did not cover the full window'
            )

        # Check critical peak windows are in critical period


        mean_of_peaks = np.mean([
            consumption.max_between(*window.as_tuple)
            for window in self.critical_peak_windows
        ])
        charge = mean_of_peaks * self.rate

        # Get index grouped by frequency_applied period
        charge_df = pd.DataFrame(index=consumption.groupby_period_stats(
            frequency=self.frequency_applied,
            within_window=self.period_active
        ).index
        )
        charge_df['charge'] = charge

        return AppliedCharge(
            self.name,
            charge_df['charge'],
            self.rate_unit,
            consumption.units,
            sum(charge_df['charge'])
        )


# All tariffs should be added here - map facilitates
# multi tarif instantiation via dicts etc
tariffs_map = MappingProxyType({
    'SingleRateTariff': SingleRateTariff,
    'TouTariff': TouTariff,
    'ConnectionTariff': ConnectionTariff,
    'DemandTariff': DemandTariff,
    'BlockTariff': BlockTariff,
    'CapacityTariff': CapacityTariff,
    # 'CriticalPeakDemandTariff': CriticalPeakDemandTariff
})
