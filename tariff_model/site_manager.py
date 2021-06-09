from dataclasses import dataclass
import pandas as pd
from time import time
from typing import Type

from tariffs import Charge, TariffRegime
from data_models import MeterData


@dataclass
class Site:
    name: str
    tariffs: TariffRegime
    meter_data: MeterData
    bill_ledgers: dict[pd.DataFrame] = None
    bill: dict[float] = None

    def __post_init__(self):

        self.meter_data.set_sample_rate(self.tariffs.metering_sample_rate)

    def calculate_bill(self):
        self.bill_ledgers = {}
        self.bill = {}
        for charge in self.tariffs.charges:
            self.bill_ledgers[charge.name] = charge.apply_charge(
                self.meter_data.meter_ts
            )
            self.bill[charge.name] = self.bill_ledgers[charge.name]['bill'].sum()