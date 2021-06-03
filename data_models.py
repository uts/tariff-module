from dataclasses import dataclass
import pandas as pd


@dataclass
class MeterData:
    name: str
    meter_ts: pd.DataFrame
    units: str

    def set_sample_rate(self, sample_rate):
        self.meter_ts = self.meter_ts.resample(sample_rate).sum()
