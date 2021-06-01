from abc import abstractmethod
import odin
from odin.exceptions import ValidationError


class SampleRateValidator(odin.Resource):
    minutes = odin.IntegerField()


class ChargeValidator(odin.Resource):
    name = odin.StringField()
    consumption_unit = odin.StringField()
    rate_unit = odin.StringField()
    metering_sample_rate = odin.ObjectAs(SampleRateValidator)

    class Meta:
        abstract = True


class SingleRateValidator(ChargeValidator):
    rate = odin.FloatField()


class TOUChargeValidator(ChargeValidator):
    time_bins = odin.TypedArrayField(odin.IntegerField())
    bin_rates = odin.TypedArrayField(odin.FloatField())
    bin_labels = odin.TypedArrayField(odin.StringField())


class DemandChargeValidator(ChargeValidator):
    rate = odin.FloatField(null=True)
    frequency_applied = odin.StringField()
    tou = odin.ObjectAs(TOUChargeValidator, null=True)

    def clean(self):
        if not any([self.rate, self.tou]):
            raise ValidationError(f'{self.name}')


class ConnectionChargeValidator(ChargeValidator):
    rate = odin.FloatField()

test = DemandChargeValidator()