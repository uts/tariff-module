from dataclasses import dataclass, field
from types import MappingProxyType
from typing import List
import pandas as pd
from pydantic import validate_arguments

from ts_tariffs.meters import MeterData, Meters
from ts_tariffs.ts_utils import FrequencyOption
from ts_tariffs.units import ConsumptionUnitOption
from ts_tariffs.utils import EnforcedDict
from ts_tariffs.tariffs import (
    SingleRateTariff,
    TouTariff,
    ConnectionTariff,
    DemandTariff,
    BlockTariff,
    CapacityTariff, Tariff, AppliedCharge,
)

tariffs = MappingProxyType({
    'SingleRateTariff': SingleRateTariff,
    'TouTariff': TouTariff,
    'ConnectionTariff': ConnectionTariff,
    'DemandTariff': DemandTariff,
    'BlockTariff': BlockTariff,
    'CapacityTariff': CapacityTariff,
})

frequency_units = FrequencyOption.options_as_list()

class TariffRegime:
    def __init__(
            self,
            tariff_json: dict[str, str] = None,
            tariff_list: List[Tariff] = None,
    ):
        if tariff_json:
            self.name = tariff_json['name']
            charges = tariff_json['charges']
            self.charges_dict = {}
            errors_dict = {}
            for charge in charges:
                # Instantiate charge with string of type and dict of attrs
                charge = tariffs[charge['charge_type']](**charge)
                self.charges_dict[charge.name] = charge
        if tariff_list:
            self.charges_dict = {x.name: x for x in tariff_list}

    @property
    def charges(self):
        return list(self.charges_dict.values())

    def delete_charge(self, charge_name: str):
        del self.charges_dict[charge_name]

    def add_charge(self, charge: Tariff):
        self.charges_dict[charge.name] = charge

    def calculate_bill(self, name: str, meters: Meters):
        applied_charges = []
        for tariff in self.charges_dict.values():
            if tariff.consumption_unit in frequency_units:
                # Needs only index, so use any meter
                meter = list(meters.values())[0]
            else:
                meter = meters.meters_by_unit[tariff.consumption_unit]
            applied_charges.append(tariff.apply(meter))
        return Bill(name, applied_charges)


@dataclass
class Bill:
    name: str
    charges: List[AppliedCharge]

    @property
    def total(self) -> float:
        return sum([charge.total for charge in self.charges])

    @property
    def item_names(self):
        return [charge.name for charge in self.charges]

    @property
    def itemised_as_dict(self):
        return {charge.name: charge.total for charge in self.charges}

    @property
    def as_series(self) -> pd.Series:
        return pd.Series(self.itemised_as_dict).rename(self.name)


@dataclass
class BillCompare:
    bills: List[Bill]

    @property
    def as_dataframe(self) -> pd.DataFrame:
        bills_series = []
        for bill in self.bills:
            bills_series.append(bill.as_series)
        return pd.concat(bills_series, axis=1)


class Bills(EnforcedDict):
    def __init__(
            self,
            data: dict = None,
    ):
        super(Bills, self).__init__(
            data,
            key_type=str,
            value_type=Bill
        )

    def append(self, bill: Bill):
        self[bill.name] = bill

