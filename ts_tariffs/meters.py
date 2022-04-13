from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta, datetime, time
from typing import Union, Optional, List
from copy import deepcopy, copy

import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta

from ts_tariffs.ts_utils import period_cascades_map, TimeWindow, FrequencyOption, SampleRate, DateWindow, DatetimeWindow
from ts_tariffs.utils import EnforcedDict


class Validator:
    @staticmethod
    def index_as_dt(consumption: Union[pd.Series, pd.DataFrame]):
        if not isinstance(consumption.index.dtype, datetime):
            raise ValueError('DataFrames and Series index must be dtype datetime')


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

    def timedelta_covered(self) -> timedelta:
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

    def window_covered(
            self,
            window: Union[DateWindow, DatetimeWindow]
    ) -> bool:
        window_covered = True
        if isinstance(window, DateWindow):
            # Start and end of window at the beginning and end of the
            # start and end dates, respectively
            start_of_first_day = datetime.combine(window.start, time(0))
            end_of_last_day = \
                datetime.combine(window.end, time(0)) + \
                timedelta(days=1) - \
                self.sample_rate
            if start_of_first_day < self.first_datetime():
                window_covered = False
            if end_of_last_day > self.last_datetime():
                window_covered = False
        elif isinstance(window, DatetimeWindow):
            if window.start < self.first_datetime():
                window_covered = False
            if window.end > self.last_datetime():
                window_covered = False
        else:
            raise TypeError(f'Wrong type recieved: {window.__class__.__name__}. '
                            f'The window param must be a DateWindow or DatetimeWindow')
        return window_covered

    def window_slice(
            self,
            window: Union[DateWindow, DatetimeWindow]
    ) -> pd.Series:
        return self.between(window.start, window.end)

    def period_slice(
            self,
            from_dt: datetime,
            period_freq: FrequencyOption,
            number_periods: float,
    ) -> pd.Series:
        # Pluralise period so that relativedelta adds to datetime, rather than replaces freq attr
        period_freq += 's'
        to_dt = from_dt + relativedelta(**{period_freq: number_periods * period_freq})
        return self.between(from_dt, to_dt)

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

    def groupby_period_stats(
            self,
            frequency: FrequencyOption,
            within_window: Union[DateWindow, DatetimeWindow] = None,
            stats: Union[str, List[str]] = 'max'
    ):
        if isinstance(stats, str):
            stats = [stats]
        if within_window:
            ts = self.window_slice(within_window)
        else:
            ts = self.tseries
        period_cascade = period_cascades_map[frequency]
        period_bins = list([getattr(ts.index, period) for period in period_cascade])
        return ts.groupby(period_bins).agg(stats).rename_axis(period_cascade)

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