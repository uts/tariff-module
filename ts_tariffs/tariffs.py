from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import odin
from odin.codecs import dict_codec
from odin.exceptions import ValidationError
from datetime import timedelta

from ts_tariffs.ts_utils import get_period_statistic, get_intervals_list
from ts_tariffs.datetime_schema import period_schema, periods_slice_schema, resample_schema
from ts_tariffs.units import consumption_units



def load_properties(obj, schema, validator):
    properties = dict_codec.load(
        schema,
        validator
    )
    # properties.full_validation()
    obj.__dict__.update(dict_codec.dump(properties))


def timedelta_builder(deltas: dict):
    return sum([timedelta()])


class SampleRateValidator(odin.Resource):
    minutes = odin.IntegerField(null=True)
    hours = odin.IntegerField(null=True)
    days = odin.IntegerField(null=True)
    weeks = odin.IntegerField(null=True)

    # def full_validation(self):
    #
    #     self.resample_str =


class TOUValidator(odin.Resource):
    time_bins = odin.TypedArrayField(odin.IntegerField())
    bin_rates = odin.TypedArrayField(odin.FloatField())
    bin_labels = odin.TypedArrayField(odin.StringField())


class ChargeValidator(odin.Resource):
    name = odin.StringField()
    charge_type = odin.StringField()
    consumption_unit = odin.StringField(choices=consumption_units)
    rate_unit = odin.StringField()


class Charge(ABC):
    def __init__(self, charge_schema, schema_validator):

        load_properties(self, charge_schema, schema_validator)

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

        class SingleRateChargeValidator(ChargeValidator):
            rate = odin.FloatField()

        super().__init__(charge_schema, SingleRateChargeValidator)


    def apply_charge(self, meter_ts: pd.DataFrame) -> pd.DataFrame:
        bill = meter_ts.copy()
        bill['bill'] = meter_ts['meter_data'] * self.rate
        return bill


class ConnectionCharge(Charge):
    def __init__(self, charge_schema):

        class ConnectionChargeValidator(ChargeValidator):
            rate = odin.FloatField()
            frequency_applied = odin.ObjectAs(SampleRateValidator)

        super().__init__(charge_schema, ConnectionChargeValidator)

    def apply_charge(self, meter_ts: pd.DataFrame) -> pd.DataFrame:
        bill = meter_ts.resample(
            resample_schema[self.frequency_applied]
        ).sum()
        bill['bill'] = self.rate

        return bill


class TOUCharge(Charge):
    def __init__(self, charge_schema):

        class TOUChargeValidator(ChargeValidator):
            tou = odin.ObjectAs(TOUValidator)

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

        class DemandChargeValidator(ChargeValidator):
            rate = odin.FloatField(null=True)
            frequency_applied = odin.ObjectAs(SampleRateValidator)
            tou = odin.ObjectAs(TOUValidator, null=True)

            def cross_validate(self):
                if not any([self.rate, self.tou]):
                    raise ValidationError(
                        f'{self.name} schema not valid: Schema for '
                        f'DemandChargeValidator must contain either '
                        f'a tou or rate field'
                    )

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

        class BlockChargeValidator(ChargeValidator):
            frequency_applied = odin.ObjectAs(SampleRateValidator)
            threshold_bins = odin.TypedArrayField(
                odin.TypedArrayField(odin.FloatField())
            )
            bin_rates = odin.TypedArrayField(odin.FloatField())
            bin_labels = odin.TypedArrayField(odin.StringField())

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
        # self.charges = list([
        #     charge_dict[charge['charge_type']](charge)
        #     for charge in charges]
        # )
        self.charges = []
        for charge in charges:
            validated_charge = charge_dict[charge['charge_type']](charge)
            self.charges.append(validated_charge)
        # self.metering_sample_rate = SampleRate(
        #     tariff_regime['metering_sample_rate']
        # )




