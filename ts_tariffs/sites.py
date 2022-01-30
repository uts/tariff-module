from abc import ABC, abstractmethod
from copy import copy
from dataclasses import dataclass, field
from datetime import timedelta, datetime
from typing import List, Dict, TypedDict, Union
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np

from ts_tariffs.utils import EnforcedDict
from ts_tariffs.tariffs import TariffRegime


@dataclass
class MeterPlotConfig:
    data_name: str
    color: str
    alpha: float = 1.0
    label: str = None

    def __post_init__(self):
        if not self.label:
            self.label = self.data_name


@dataclass
class MeterData(ABC):
    name: str
    tseries: pd.DataFrame
    sample_rate: timedelta
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


@dataclass
class Bill:
    name: str
    itemised_ts: pd.DataFrame = field(init=False)

    def __post_init__(self):
        self.itemised_ts = pd.DataFrame()

    @property
    def itemised_totals(self) -> Dict[str, float]:
        return self.itemised_ts.sum(axis=0).to_dict()

    @property
    def total(self) -> float:
        return sum(self.itemised_totals.values())


class Bills(EnforcedDict):
    def __init__(
            self,
            data: dict = None,
    ):
        super(Bills, self).__init__(
            data,
            key_type=str,
            value_type=Bill
        )

    def append(self, bill: Bill):
        self[bill.name] = bill


@dataclass
class Site:
    name: str
    tariffs: TariffRegime
    meters: Meters
    bills: Bills = field(init=False)

    def __post_init__(self):
        self.bills = Bills()

    def calculate_bill(self):
        for meter_name, meter in self.meters.items():
            bill = Bill(meter_name)
            for charge in self.tariffs.charges:
                bill.itemised_ts[charge.name] = charge.simple_bill_ts(
                    meter.tseries,
                )
            self.bills.append(bill)

    def bill_compare(self, bills: List[str]):
        bill_data = []
        for bill in bills:
            bill_dict = copy(self.bills[bill].itemised_totals)
            bill_dict['total'] = self.bills[bill].total
            bill_series = pd.Series(bill_dict)
            bill_series.rename(bill, inplace=True)
            bill_data.append(bill_series)

        return pd.concat(bill_data, axis=1)

    def add_meter(self, meter: MeterData):
        self.meters.append(meter)
