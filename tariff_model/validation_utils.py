from dataclasses import dataclass
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

def test():
    pass


@dataclass
class Charge(ABC):
    name: str
    charge_type: str
    consumption_unit: str
    rate_unit: str

    @abstractmethod
    def apply_charge(self, meter_ts: pd.DataFrame) -> np.array:
        '''
        Docs go here
        :param meter_ts:
        :return:
        '''
        pass


class SingleRateCharge(Charge):
    rate: float

    def apply_charge(self, meter_ts: pd.DataFrame) -> np.array:
        '''
        Docs go here
        :param meter_ts:
        :return:
        '''
        pass


d = {
    'name': 'tou_tariff',
    'charge_type': 'time_of_use',
    'consumption_unit': 'kWh',
    'rate_unit': 'dollars',
}

single = SingleRateCharge(**d)
print(single)