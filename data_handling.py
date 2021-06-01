from dataclasses import dataclass
import pandas as pd


@dataclass
class MeterData:
    name: str
    meter_ts: pd.DataFrame
    units: str

