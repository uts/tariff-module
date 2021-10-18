from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import timedelta
from typing import List, Dict

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
    itemised_bill: Dict[str, float] = field(init=False)
    bill_ts: pd.DataFrame = field(init=False)
    detailed_bill_ts: pd.DataFrame = field(init=False)

    def __post_init__(self):
        self.itemised_bill = {}

    @property
    def bill_total(self):
        return sum(self.itemised_bill.values())

    def get_itemised_bill(self):
        for charge in self.tariffs.charges:
            self.itemised_bill[charge.name] = charge.simple_bill_total(
                self.meter_data.tseries,
            )

    def get_bill_ts(self):
        bill_data = {}
        for charge in self.tariffs.charges:
            bill_data[charge.name] = charge.simple_bill_ts(
                self.meter_data.tseries,
            )
        self.bill_ts = pd.DataFrame.from_dict(bill_data)
        self.itemised_bill = self.bill_ts.sum(axis=0).to_dict()

    # def get_detailed_bill_ts(self):
    #     bill_data = {}
    #     detailed_bill_data = {}
    #     for charge in self.tariffs.charges:
    #         detailed_bill_data[charge.name] = charge.detailed_bill_ts(
    #             self.meter_data.tseries,
    #         )
    #         bill_ts_columns.append(charge.name)
    #     bill_df = pd.DataFrame.from_dict(detailed_bill_data)
    #     self.itemised_bill = bill_df.sum(axis=1).to_dict()
    #     self.bill_ts = bill_df[]
    #     return pd.DataFrame.from_dict(bill_data)
