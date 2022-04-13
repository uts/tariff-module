from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import Union, List, Optional
from copy import deepcopy, copy

import pandas as pd

from ts_tariffs.ts_utils import period_cascades_map, TimeWindow, FrequencyOption, SampleRate
from ts_tariffs.utils import EnforcedDict


@dataclass
class MeterData:
    name: str
    tseries: pd.Series
    sample_rate: Union[timedelta, SampleRate]
    units: str

    """ Representation of data from an interval metering device, i.e. a
    meter that records data at regular time intervals

    Common examples:
        - electricity smart meter with consumption at 30 minute intervals
        - gas meter with daily consumption data
    """

    def first_datetime(self) -> datetime:
        return self.tseries.first_valid_index()

    def last_datetime(self) -> datetime:
        return self.tseries.last_valid_index()

    def time_covered(self) -> timedelta:
        return self.last_datetime() - self.first_datetime()

    def first_day_slice(self) -> slice:
        start_dt = self.first_datetime()
        end_dt = start_dt + timedelta(days=1)
        return slice(start_dt, end_dt)

    def last_day_slice(self) -> slice:
        end_dt = self.last_datetime()
        start_dt = end_dt - timedelta(days=1)
        return slice(start_dt, end_dt)

    def first_week_slice(self):
        start_dt = self.first_datetime()
        end_dt = start_dt + timedelta(weeks=1)
        return slice(start_dt, end_dt)

    def last_week_slice(self) -> slice:
        end_dt = self.last_datetime()
        start_dt = end_dt - timedelta(weeks=1)
        return slice(start_dt, end_dt)

    def first_day(self) -> pd.Series:
        return self.tseries[self.first_day_slice()]

    def last_day(self) -> pd.Series:
        return self.tseries[self.last_day_slice()]

    def first_week(self) -> pd.Series:
        return self.tseries[self.first_week_slice()]

    def last_week(self) -> pd.Series:
        return self.tseries[self.last_week_slice()]

    def between(self, start: datetime, end: datetime) -> pd.Series:
        return self.tseries[slice(start, end)]

    def max(self) -> float:
        return self.tseries.max()

    def min(self) -> float:
        return self.tseries.min()

    def max_between(self, start: datetime, end: datetime) -> float:
        return self.tseries[slice(start, end)].max()

    def min_between(self, start: datetime, end: datetime) -> float:
        return self.tseries[slice(start, end)].min()

    def kwh_to_kw(self, inplace=False) -> Optional[MeterData]:
        if self.units != 'kWh':
            raise ValueError(f'Can only convert from kWh. Units are set as {self.units} not kWh. ')
        if inplace:
            self.tseries /= self.sample_rate / timedelta(hours=1)
            self.units = 'kW'
        else:
            new_meter = self.copy()
            new_meter.tseries = new_meter.tseries / (new_meter.sample_rate / timedelta(hours=1))
            new_meter.units = 'kW'
            return new_meter

    def year_peaks(self) -> pd.Series:
        return self.tseries.groupby(
            self.tseries.index.year
        ).max().rename_axis('year')

    def month_peaks(self):
        return self.tseries.groupby(
            self.tseries.index.month
        ).max().rename_axis('month')

    def year_sum(self) -> pd.Series:
        return self.tseries.groupby(
            self.tseries.index.year
        ).sum().rename_axis('year')

    def month_sum(self):
        return self.tseries.groupby(
            self.tseries.index.month
        ).sum().rename_axis('month')

    def period_peaks(
            self,
            period: str,
            time_bin: TimeWindow = None
    ) -> pd.Series:
        period_cascade = period_cascades_map[period]
        if time_bin:
            ts = self.tseries.between_time(time_bin.start, time_bin.end, inclusive='left')
        else:
            ts = self.tseries
        period_bins = list([getattr(ts.index, period) for period in period_cascade])
        return ts.groupby(period_bins).max().rename_axis(period_cascade)

    def period_sum(
            self,
            period: str,
            time_bin: TimeWindow = None
    ) -> pd.Series:
        period_cascade = period_cascades_map[period]
        if time_bin:
            ts = self.tseries.between_time(time_bin.start, time_bin.end, inclusive='left')
        else:
            ts = self.tseries
        period_bins = list([getattr(ts.index, period) for period in period_cascade])
        return ts.groupby(period_bins).sum().rename_axis(period_cascade)

    def period_stat(self):
        """ TODO: Generalised groupby option to get aggregations at given frequency
        """
        pass

    def grouped_dt_periods(self, frequency: FrequencyOption):
        period_cascade = period_cascades_map[frequency]
        period_bins = list([getattr(self.tseries.index, period) for period in period_cascade])
        return self.tseries.groupby(period_bins).indices.keys()

    def to_numpy(self):
        return self.tseries.to_numpy(dtype=float)

    def copy(self, deep=True):
        if deep:
            return deepcopy(self)
        else:
            return copy(self)


@dataclass
class Meters(EnforcedDict):
    def __init__(
            self,
            data: dict = None,
    ):
        super().__init__(
            data,
            key_type=str,
            value_type=MeterData
        )

    @property
    def meters_by_unit(self):
        return {meter.units: meter for meter in self.values()}

    def append(self, meter: MeterData):
        self[meter.name] = meter