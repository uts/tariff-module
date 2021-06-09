import odin
from odin.exceptions import ValidationError
from datetime import timedelta

from tariff_model.units import consumption_units


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


class ChargeValidator(odin.Resource):
    name = odin.StringField()
    charge_type = odin.StringField()
    consumption_unit = odin.StringField(choices=consumption_units)
    rate_unit = odin.StringField()

    class Meta:
        abstract = True


class SingleRateChargeValidator(ChargeValidator):
    rate = odin.FloatField()


class TOUChargeValidator(ChargeValidator):
    time_bins = odin.TypedArrayField(odin.IntegerField())
    bin_rates = odin.TypedArrayField(odin.FloatField())
    bin_labels = odin.TypedArrayField(odin.StringField())


class DemandChargeValidator(ChargeValidator):
    rate = odin.FloatField(null=True)
    frequency_applied = odin.ObjectAs(SampleRateValidator)
    tou = odin.ObjectAs(TOUChargeValidator, null=True)

    def cross_validate(self):
        if not any([self.rate, self.tou]):
            raise ValidationError(
                f'{self.name} schema not valid: Schema for '
                f'DemandChargeValidator must contain either '
                f'a tou or rate field'
            )


class ConnectionChargeValidator(ChargeValidator):
    rate = odin.FloatField()
    frequency_applied = odin.ObjectAs(SampleRateValidator)


class BlockChargeValidator(ChargeValidator):
    frequency_applied = odin.ObjectAs(SampleRateValidator)
    threshold_bins = odin.TypedArrayField(
        odin.TypedArrayField(odin.FloatField())
    )
    bin_rates = odin.TypedArrayField(odin.FloatField())
    bin_labels = odin.TypedArrayField(odin.StringField())