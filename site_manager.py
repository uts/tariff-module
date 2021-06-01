from dataclasses import dataclass
import pandas as pd
from time import time
from typing import Type

from tariffs import Charge
from data_handling import MeterData


@dataclass
class Site:
    name: str
    charges: list[Type[Charge]]
    meter_data: MeterData
    bill_ledgers: dict[pd.DataFrame] = None
    bill: dict[float] = None

    def calculate_bill(self):
        self.bill_ledgers = {}
        self.bill = {}
        for charge in self.charges:
            self.bill_ledgers[charge.name] = charge.apply_charge(
                self.meter_data.meter_ts
            )
            self.bill[charge.name] = self.bill_ledgers[charge.name]['bill'].sum()