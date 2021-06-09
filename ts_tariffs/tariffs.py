from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from odin.codecs import dict_codec

from input_validation import (
    SingleRateChargeValidator,
    TOUChargeValidator,
    DemandChargeValidator,
    ConnectionChargeValidator,
    BlockChargeValidator,
    SampleRateValidator
)
from ts_utils import get_period_statistic, get_intervals_list
from datetime_schema import period_schema, periods_slice_schema, resample_schema



def validate_and_load(obj, schema, validator):
    properties = dict_codec.load(
        schema,
        validator
    )
    properties.full_validation()
    obj.__dict__.update(properties.__dict__)


class SampleRate:
    def __init__(self, sample_rate_schema: dict):
        validate_and_load(
            self,
            sample_rate_schema,
            SampleRateValidator
        )


class Charge(ABC):
    def __init__(self, charge_schema, schema_validator):
        validate_and_load(self, charge_schema, schema_validator)

    @abstractmethod
    def apply_charge(self, meter_ts: pd.DataFrame) -> np.array:
        '''
        Docs go here
        :param meter_ts:
        :return:
        '''
        pass


class SingleRateCharge(Charge):
    def __init__(self, charge_schema):
        super().__init__(charge_schema, SingleRateChargeValidator)

    def apply_charge(self, meter_ts: pd.DataFrame) -> pd.DataFrame:
        bill = meter_ts.copy()
        bill['bill'] = meter_ts['meter_data'] * self.rate
        return bill


class ConnectionCharge(Charge):
    def __init__(self, charge_schema):
        super().__init__(charge_schema, ConnectionChargeValidator)

    def apply_charge(self, meter_ts: pd.DataFrame) -> pd.DataFrame:
        bill = meter_ts.resample(
            resample_schema[self.frequency_applied]
        ).sum()
        bill['bill'] = self.rate

        return bill


class TOUCharge(Charge):
    def __init__(self, charge_schema):
        super().__init__(charge_schema, TOUChargeValidator)

    def apply_charge(self, meter_ts: pd.DataFrame) -> pd.DataFrame:
        prices = np.array(self.bin_rates)
        bins = np.digitize(
            meter_ts.index.hour.values,
            bins=self.time_bins
        )
        charge = meter_ts.copy()
        charge['bill'] = prices[bins] * meter_ts['meter_data'].to_numpy()
        return charge


class DemandCharge(Charge):
    #TODO: Add handler for kWh -> kVA
    def __init__(self, charge_schema):
        super().__init__(charge_schema, DemandChargeValidator)

    def apply_charge(self, meter_ts: pd.DataFrame) -> pd.DataFrame:
        periods = period_schema[self.frequency_applied]
        period_peaks = get_period_statistic(
            meter_ts,
            'meter_data',
            ['max'],
            periods,
            self.tou
        )
        if self.tou:
            tou_intervals = get_intervals_list(
                self.tou.time_bins,
            )
            for j, interval in enumerate(tou_intervals):
                slices = periods_slice_schema[self.frequency_applied].copy()
                slices.append(interval)
                period_peaks.loc[tuple(slices), 'rate'] =\
                    self.tou.bin_rates[j]
        else:
            period_peaks['rate'] = self.rate
        period_peaks['bill'] = period_peaks['rate'] * period_peaks['max']
        return period_peaks


class BlockCharge(Charge):
    def __init__(self, charge_schema):
        super().__init__(charge_schema, BlockChargeValidator)

    def apply_charge(self, meter_ts: pd.DataFrame) -> pd.DataFrame:
        periods = period_schema[self.frequency_applied]
        cumulative = get_period_statistic(
            meter_ts,
            'meter_data',
            ['sum'],
            periods,
        )
        cumulative['bill'] = 0.0
        for j, block in enumerate(self.threshold_bins):
            rate = self.bin_rates[j]
            rate_col_name = f'block_{j + 1}_energy'
            cumulative[rate_col_name] = np.clip(
                cumulative['sum'],
                block[0],
                block[1]
            ) - block[0]
            cumulative['bill'] += rate * cumulative[rate_col_name]

        return cumulative


charge_dict = {
    'single_rate': SingleRateCharge,
    'time_of_use': TOUCharge,
    'demand_charge': DemandCharge,
    'block': BlockCharge,
    'connection': ConnectionCharge
}


class TariffRegime:
    def __init__(self, tariff_regime: dict):
        self.name = tariff_regime['name']
        # Unpack charges data and instantiate as
        # Charge subclasses
        charges = tariff_regime['charges']
        self.charges = list([
            charge_dict[charge['charge_type']](charge)
            for charge in charges]
        )
        self.metering_sample_rate = SampleRate(
            tariff_regime['metering_sample_rate']
        )




