import pandas as pd

from ts_tariffs.examples.data_urls import minute_household_consumption
from ts_tariffs.ts_utils import FrequencyOption, resample_schema


def houshold_consumption(
        sample_rate_multiplier: int = None,
        sample_rate_base: FrequencyOption = None
):
    df = pd.read_csv(minute_household_consumption)
    df['datetime'] = pd.to_datetime(df['datetime'], format='%Y-%m-%d %H:%M:%S')
    df.set_index('datetime', inplace=True)
    if sample_rate_base:
        df = df.resample(f'{sample_rate_multiplier}{resample_schema[sample_rate_base]}').agg({
            'energy': 'sum',
            'active_power': 'mean',
            'apparent_power': 'mean',
            'reactive_power': 'mean'
        })
    return df

