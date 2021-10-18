from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta
from typing import List

import pandas as pd
import numpy as np

from ts_tariffs.tariffs import TariffRegime


@dataclass
class MeterData(ABC):
    name: str
    tseries: pd.DataFrame
    sample_rate: timedelta
    units: dict

    def __post_init__(self):
        # Ensure no missing timesteps
        # For valid freq strings see: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases
        self.tseries = self.tseries.asfreq(self.sample_rate)
        self.tseries.interpolate(inplace=True)

    def set_sample_rate(self, sample_rate):
        pass

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
class Site:
    name: str
    tariffs: TariffRegime
    meter_data: MeterData
    bill_ledgers: dict[pd.DataFrame] = None
    bill: dict[float] = None

    def calculate_bill(self, detailed_bill=True):
        self.bill_ledgers = {}
        self.bill = {}
        for charge in self.tariffs.charges:
            self.bill_ledgers[charge.name] = charge.calculate_charge(
                self.meter_data.tseries,
                detailed_bill=detailed_bill
            )
            self.bill[charge.name] = float(self.bill_ledgers[charge.name].sum())
