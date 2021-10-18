from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta
from typing import List, Union

import pandas as pd
import numpy as np

from ts_tariffs.tariffs import TariffRegime

MANDATORY_METER_COLS = (
            'demand_energy',
            'demand_power',
            'generation_energy',
            'power_factor',
            'demand_apparent'
        )


class Validator:
    @staticmethod
    def data_cols(df, mandatory_cols: tuple):
        not_present = list([col not in df.columns for col in mandatory_cols])
        if any(not_present):
            content = ', '.join(np.array(mandatory_cols)[not_present])
            raise ValueError(f'The following columns must be present in dataframe: {content}')


@dataclass
class MeterData(ABC):
    name: str
    meter_ts: pd.DataFrame
    sample_rate: timedelta
    units: dict

    def __post_init__(self):
        # Ensure no missing timesteps
        # For valid freq strings see: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases
        self.meter_ts = self.meter_ts.asfreq(self.sample_rate)
        self.meter_ts.interpolate(inplace=True)

    def set_sample_rate(self, sample_rate):
        pass


@dataclass
class ElectricityMeterData(MeterData):
    sub_load_cols: List[str]

    def __post_init__(self):
        Validator.data_cols(self.meter_ts, MANDATORY_METER_COLS)

    @classmethod
    def from_dataframe(
            cls,
            name: str,
            df: pd.DataFrame,
            sample_rate: timedelta,
            column_map: dict
    ):
        units = {}
        for meter_col, data in column_map.items():
            df[meter_col] = df[data['ts']]
            units[meter_col] = data['units']
        return cls(name, df[column_map.keys()], sample_rate, units)

    def set_sample_rate(self, sample_rate):
        pass


@dataclass
class Site:
    name: str
    tariffs: TariffRegime
    meter_data: ElectricityMeterData
    bill_ledgers: dict[pd.DataFrame] = None
    bill: dict[float] = None

    def calculate_bill(self, detailed_bill=True):
        self.bill_ledgers = {}
        self.bill = {}
        for charge in self.tariffs.charges:
            self.bill_ledgers[charge.name] = charge.calculate_charge(
                self.meter_data.meter_ts,
                detailed_bill=detailed_bill
            )
            self.bill[charge.name] = float(self.bill_ledgers[charge.name].sum())
