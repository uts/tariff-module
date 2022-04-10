from dataclasses import dataclass, field
from types import MappingProxyType
from typing import List, Union
import pandas as pd

from ts_tariffs.meters import Meters
from ts_tariffs.ts_utils import FrequencyOption
from ts_tariffs.utils import EnforcedDict
from ts_tariffs.tariffs import (
    SingleRateTariff,
    TouTariff,
    ConnectionTariff,
    DemandTariff,
    BlockTariff,
    CapacityTariff,
    Tariff,
    AppliedCharge,
    tariffs_map,
)

frequency_units = FrequencyOption.options_as_list()


@dataclass
class TariffRegime:
    name: str
    tariffs: List[Tariff]

    @property
    def as_dict(self):
        return {x.name: x for x in self.tariffs}

    @classmethod
    def from_dict(cls, tariffs_dict: dict):
        if 'name' not in tariffs_dict.keys() or 'tariffs' not in tariffs_dict.keys():
            raise ValueError('Tariff dict must contain a "name" and a "tariffs" key')
        tariffs = []
        for tariff_data in tariffs_dict['tariffs']:
            tariff_data = tariffs_map[tariff_data['charge_type']].from_dict(tariff_data)
            tariffs.append(tariff_data)

        return cls(
            name=tariffs_dict['name'],
            tariffs=tariffs
        )

    def delete_charge(self, charge_name: str):
        del self.from_dict[charge_name]

    def add_charge(self, charge: Tariff):
        self.from_dict[charge.name] = charge

    def calculate_bill(self, name: str, meters: Meters):
        applied_charges = []
        for tariff in self.from_dict.values():
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

