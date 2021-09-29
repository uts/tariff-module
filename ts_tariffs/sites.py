from abc import ABC, abstractmethod
from dataclasses import dataclass
import pandas as pd
import numpy as np

from ts_tariffs.tariffs import TariffRegime

class Validator:
    @staticmethod
    def electricity_data_cols(df):
        mandatory_cols = np.array([
            'demand_energy',
            'demand_power',
            'generation_energy',
            'generation_power',
            'power_factor'
        ])
        not_present = list([col not in df.columns for col in mandatory_cols])
        if any(not_present):
            content = ', '.join(mandatory_cols[not_present])
            raise ValueError(f'The following columns must be present in dataframe: {content}')


@dataclass
class MeterData(ABC):
    name: str
    meter_ts: pd.DataFrame

    def set_sample_rate(self, sample_rate):
        pass


@dataclass
class ElectricityMeterData(MeterData):
    units: dict

    def __post_init__(self):
        Validator.electricity_data_cols(self.meter_ts)

    @classmethod
    def from_dataframe(cls, name, df, column_map: dict):
        units = {}
        for meter_col, data in column_map.items():
            df[meter_col] = df[data['ts']]
            units[meter_col] = data['units']
        return cls(name, df[column_map.keys()], units)

    def set_sample_rate(self, sample_rate):
        pass


my_df = pd.DataFrame(columns=[
            'demand_power',
            'generation_energy',
            'power_factor'
        ])
meter = ElectricityMeterData('test', my_df)


@dataclass
class Site:
    name: str
    tariffs: TariffRegime
    meter_data: MeterData
    bill_ledgers: dict[pd.DataFrame] = None
    bill: dict[float] = None

    # def __post_init__(self):
    #
    #     self.meter_data.set_sample_rate(self.tariffs.metering_sample_rate)

    def calculate_bill(self, detailed_bill=True):
        self.bill_ledgers = {}
        self.bill = {}
        for charge in self.tariffs.charges:
            self.bill_ledgers[charge.name] = charge.calculate_charge(
                self.meter_data.meter_ts,
                detailed_bill=detailed_bill
            )
            self.bill[charge.name] = float(self.bill_ledgers[charge.name].sum())
