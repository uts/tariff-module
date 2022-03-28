from copy import copy
from dataclasses import dataclass, field
from datetime import timedelta
from typing import List, Dict
import pandas as pd

from ts_tariffs.meters import MeterData, Meters
from ts_tariffs.utils import EnforcedDict
from ts_tariffs.tariffs import TariffRegime


class SampleRate(timedelta):
    pass


@dataclass
class MeterPlotConfig:
    data_name: str
    color: str
    alpha: float = 1.0
    label: str = None

    def __post_init__(self):
        if not self.label:
            self.label = self.data_name


@dataclass
class Bill:
    name: str
    itemised_ts: pd.DataFrame = field(init=False)

    def __post_init__(self):
        self.itemised_ts = pd.DataFrame()

    @property
    def itemised_totals(self) -> Dict[str, float]:
        return self.itemised_ts.sum(axis=0).to_dict()

    @property
    def total(self) -> float:
        return sum(self.itemised_totals.values())


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


@dataclass
class Site:
    name: str
    tariffs: TariffRegime
    meters: Meters
    bills: Bills = field(init=False)

    def __post_init__(self):
        self.bills = Bills()

    def calculate_bill(self):
        for meter_name, meter in self.meters.items():
            bill = Bill(meter_name)
            for charge in self.tariffs.charges:
                bill.itemised_ts[charge.name] = charge.apply(
                    meter.tseries,
                )
            self.bills.append(bill)

    def bill_compare(self, bills: List[str]):
        bill_data = []
        for bill in bills:
            bill_dict = copy(self.bills[bill].itemised_totals)
            bill_dict['total'] = self.bills[bill].total
            bill_series = pd.Series(bill_dict)
            bill_series.rename(bill, inplace=True)
            bill_data.append(bill_series)

        return pd.concat(bill_data, axis=1)

    def add_meter(self, meter: MeterData):
        self.meters.append(meter)
