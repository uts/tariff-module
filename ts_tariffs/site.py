from dataclasses import dataclass
import pandas as pd

from ts_tariffs.tariffs import TariffRegime


@dataclass
class MeterData:
    name: str
    meter_ts: pd.DataFrame
    units: str

    def set_sample_rate(self, sample_rate):
        self.meter_ts = self.meter_ts.resample(sample_rate).sum()


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

    def calculate_bill(self):
        self.bill_ledgers = {}
        self.bill = {}
        for charge in self.tariffs.charges:
            self.bill_ledgers[charge.name] = charge.apply_charge(
                self.meter_data.meter_ts
            )
            self.bill[charge.name] = self.bill_ledgers[charge.name]['bill'].sum()
