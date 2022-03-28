from abc import ABC
from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import Union, List

import pandas as pd
from matplotlib import pyplot as plt

from ts_tariffs.sites import SampleRate, MeterPlotConfig
from ts_tariffs.utils import EnforcedDict


@dataclass
class MeterData(ABC):
    """ Representation of data from an interval metering device, i.e. a
    meter that records data at regular time intervals

    Common examples:
        - electricity smart meter with consumption at 30 minute intervals
        - gas meter with daily consumption data

    """
    name: str
    tseries: pd.DataFrame
    sample_rate: Union[SampleRate, timedelta]
    units: dict
    plot_configs: List[MeterPlotConfig]

    # def __post_init__(self):
        # Ensure no missing timesteps
        # For valid freq strings see: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases
        # self.tseries = self.tseries.asfreq(self.sample_rate)
        # self.tseries.interpolate(inplace=True)

    def set_sample_rate(self, sample_rate):
        pass

    def first_datetime(self) -> datetime:
        return self.tseries.first_valid_index()

    def last_datetime(self) -> datetime:
        return self.tseries.last_valid_index()

    def first_day_slice(self) -> slice:
        start_dt = self.first_datetime()
        end_dt = start_dt + timedelta(days=1)
        return slice(start_dt, end_dt)

    def last_day_slice(self) -> slice:
        end_dt = self.last_datetime()
        start_dt = end_dt - timedelta(days=1)
        return slice(start_dt, end_dt)

    def last_week_slice(self) -> slice:
        end_dt = self.last_datetime()
        start_dt = end_dt - timedelta(weeks=1)
        return slice(start_dt, end_dt)

    def max(self, col: Union[str, List[str]] = None):
        if col:
            return self.tseries[col].max(axis=0)
        else:
            return self.tseries.max(axis=0)

    def min(self, col: Union[str, List[str]]):
        if col:
            return self.tseries[col].min(axis=0)
        else:
            return self.tseries.min(axis=0)

    def add_column(self, column: pd.Series, name: str, units: str):
        self.tseries[name] = column
        self.units.update({name: units})

    def ts_plot(self):
        number_subplots = len(self.plot_configs)
        fig, axs = plt.subplots(number_subplots, sharex=True)
        for i, plot in enumerate(self.plot_configs):
            axs[i].plot(self.tseries)

    @classmethod
    def from_dataframe(
            cls,
            name: str,
            df: pd.DataFrame,
            sample_rate: timedelta,
            column_map: dict,
            plot_configs: Union[None, List[MeterPlotConfig]],
    ):
        units = {}
        # Create cols according to column_map and cherry pick them for
        # instantiation of class object
        for meter_col, data in column_map.items():
            df[meter_col] = df[data['ts']]
            units[meter_col] = data['units']
        return cls(name, df[column_map.keys()], sample_rate, units, plot_configs)


@dataclass
class Meters(EnforcedDict):
    def __init__(
            self,
            data: dict = None,
    ):
        super(Meters, self).__init__(
            data,
            key_type=str,
            value_type=MeterData
        )

    def append(self, meter: MeterData):
        self[meter.name] = meter