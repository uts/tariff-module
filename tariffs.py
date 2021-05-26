from dataclasses import dataclass
import pandas as pd
import numpy as np
from time import time

from ts_utils import get_period_statistic, get_intervals_list
from schema.tariff_schema import period_schema, period_slice


@dataclass
class Charge:
    """A charge component of a tariff structure"""
    name: str
    code: str
    schema: dict


class TOUCharge(Charge):
    def apply_charge(self, meter_ts: pd.DataFrame) -> np.array:
        prices = np.array(self.schema['bin_rates'])
        bins = np.digitize(
            meter_ts.index.hour.values,
            bins=self.schema['time_bins']
        )
        charge = meter_ts.copy()
        charge['bill'] = prices[bins] * meter_ts['energy_kwh'].to_numpy()
        return charge


class DemandCharge(Charge):
    def apply_charge(self, meter_ts: pd.DataFrame) -> np.array:
        periods = period_schema[self.schema['frequency_applied']]
        period_peaks = get_period_statistic(
            meter_ts,
            'energy_kwh',
            ['max'],
            periods,
            self.schema['time_of_use']
        )
        idx = pd.IndexSlice
        if self.schema['time_of_use']:
            tou_intervals = get_intervals_list(
                self.schema['time_of_use']['time_bins'],
            )
            for j, interval in enumerate(tou_intervals):
                slices = period_slice[self.schema['frequency_applied']].copy()
                slices.append(interval)
                period_peaks.loc[tuple(slices), 'rate'] =\
                    self.schema['time_of_use']['bin_rates'][j]
        else:
            period_peaks['rate'] = self.schema['rate']
        period_peaks['cost'] = period_peaks['rate'] * period_peaks['max']
        return period_peaks


class BlockCharge(Charge):
    def apply_charge(self, meter_ts: pd.DataFrame) -> np.array:
        periods = period_schema[self.schema['frequency_applied']]
        cumulative = get_period_statistic(
            meter_ts,
            'energy_kwh',
            ['sum'],
            periods,
        )
        cumulative['bill'] = 0.0
        for j, block in enumerate(self.schema['rate_thresholds']):
            rate = self.schema['rate_bins'][j]
            rate_col_name = f'block_{j + 1}_energy'
            cumulative[rate_col_name] = np.clip(
                cumulative['sum'],
                block[0],
                block[1]
            ) - block[0]
            cumulative['bill'] += rate * cumulative[rate_col_name]

        return cumulative


