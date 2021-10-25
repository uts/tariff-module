from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import timedelta
from typing import List, Dict, TypedDict

import pandas as pd
import numpy as np

from ts_tariffs.utils import EnforcedDict
from ts_tariffs.tariffs import TariffRegime


@dataclass
class MeterData(ABC):
    name: str
    tseries: pd.DataFrame
    sample_rate: timedelta
    units: dict

    # def __post_init__(self):
        # Ensure no missing timesteps
        # For valid freq strings see: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases
        # self.tseries = self.tseries.asfreq(self.sample_rate)
        # self.tseries.interpolate(inplace=True)

    def set_sample_rate(self, sample_rate):
        pass

    def fist_datetime(self):
        return self.tseries.first_valid_index()

    @classmethod
    def from_dataframe(
            cls,
            name: str,
            df: pd.DataFrame,
            sample_rate: timedelta,
            column_map: dict
    ):
        units = {}
        # Create cols according to column_map and cherry pick them for
        # instantiation of class object
        for meter_col, data in column_map.items():
            df[meter_col] = df[data['ts']]
            units[meter_col] = data['units']
        return cls(name, df[column_map.keys()], sample_rate, units)


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

    def add_meter(self, meter: MeterData):
        self.meters.append(meter)
