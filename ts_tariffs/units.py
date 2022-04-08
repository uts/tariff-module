from enum import Enum


class ConsumptionUnitOption(str, Enum):
    kWh = 'kWh'
    kVA = 'kVA'
    kW = 'kW'
    day = 'day'
    month = 'month'
    J = 'J'