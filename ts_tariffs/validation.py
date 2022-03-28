from enum import Enum
from typing import List

from pydantic.main import BaseModel


class FrequencySchema(BaseModel):
    minutes: int
    hours: int
    days: int
    weeks: int


class TOUSchema(BaseModel):
    time_bins: List[int]
    bin_rates: List[float]
    bin_labels: List[str]


class ConsumptionUnitSchema(str, Enum):
    kWh = 'kWh'
    kVA = 'kVA'
    kW = 'kW'
    day = 'day'
    month = 'month'
    J = 'J'


