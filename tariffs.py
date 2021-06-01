from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import odin
from odin.codecs import dict_codec

from input_validation import SingleRateValidator
from ts_utils import get_period_statistic, get_intervals_list
from schema.datetime_schema import period_schema, periods_slice_schema, resample_schema


class Charge(ABC):
    def __init__(self, charge_schema, schema_validator):
        # Load/validate charge schema and map to self
        charge_properties = dict_codec.load(
            charge_schema,
            schema_validator
        )
        self.__dict__.update(charge_properties.__dict__)

    @abstractmethod
    def apply_charge(self, meter_ts: pd.DataFrame) -> np.array:
        '''
        Docs go here
        :param meter_ts:
        :return:
        '''
        pass

    def check_sample_rate(self):
        pass

class SingleRateCharge(Charge):
    def __init__(self, charge_schema):
        super().__init__(charge_schema, SingleRateValidator)

    def apply_charge(self, meter_ts: pd.DataFrame) -> np.array:
        bill = meter_ts.copy()
        bill['bill'] = meter_ts['meter_data'] * self.rate
        return bill


class ConnectionCharge:
    def __init__(self, charge_schema):
        super().__init__(charge_schema, SingleRateValidator)

    def apply_charge(self, meter_ts: pd.DataFrame) -> np.array:
        bill = meter_ts.resample(
            resample_schema[self.schema['frequency_applied']]
        ).sum()
        bill['bill'] = self.schema['rate']

        return bill


class TOUCharge:
    type: str = 'tou'

    def apply_charge(self, meter_ts: pd.DataFrame) -> np.array:
        prices = np.array(self.schema['bin_rates'])
        bins = np.digitize(
            meter_ts.index.hour.values,
            bins=self.schema['time_bins']
        )
        charge = meter_ts.copy()
        charge['bill'] = prices[bins] * meter_ts['meter_data'].to_numpy()
        return charge


class DemandCharge:
    type: str = 'demand'

    def apply_charge(self, meter_ts: pd.DataFrame) -> np.array:
        periods = period_schema[self.schema['frequency_applied']]
        period_peaks = get_period_statistic(
            meter_ts,
            'meter_data',
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
                slices = periods_slice_schema[self.schema['frequency_applied']].copy()
                slices.append(interval)
                period_peaks.loc[tuple(slices), 'rate'] =\
                    self.schema['time_of_use']['bin_rates'][j]
        else:
            period_peaks['rate'] = self.schema['rate']
        period_peaks['bill'] = period_peaks['rate'] * period_peaks['max']
        return period_peaks


class BlockCharge:
    type: str = 'block'

    def apply_charge(self, meter_ts: pd.DataFrame) -> np.array:
        periods = period_schema[self.schema['frequency_applied']]
        cumulative = get_period_statistic(
            meter_ts,
            'meter_data',
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


class TariffRegime:
    name: str
    charges = dict[Charge]




