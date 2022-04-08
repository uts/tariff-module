from dataclasses import dataclass, field
from typing import List
import pandas as pd
from pydantic import validate_arguments

from ts_tariffs.utils import EnforcedDict
from ts_tariffs.tariffs import AppliedCharge


@validate_arguments
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


@validate_arguments
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

