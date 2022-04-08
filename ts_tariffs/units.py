from enum import Enum


class ConsumptionUnitOption(str, Enum):
    kWh = 'kWh'
    kVA = 'kVA'
    kW = 'kW'
    day = 'day'
    month = 'month'
    J = 'J'

    @staticmethod
    def options_as_list():
        return [e.value for e in ConsumptionUnitOption]
