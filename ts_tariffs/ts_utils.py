from dataclasses import dataclass
from datetime import time, timedelta
from enum import Enum
from types import MappingProxyType
from typing import Union, List


# Immutable dict for helping pd groupby operations which need to report aggs
# for nested times
period_cascades_map = MappingProxyType({
    'year': ['year'],
    'month': ['year', 'month'],
    'week': ['year', 'month', 'week', ],
    'day': ['date'],
    'quarter': ['year', 'quarter']
})

# Immutable dict for mapping frequency strings with resample codes
resample_schema = MappingProxyType({
    'second': 'S',
    'minute': 'T',
    'hour': 'H',
    'day': 'D',
    'week': 'W',
    'month': 'M',
    'quarter': 'Q',
    'year': 'A'
})


class FrequencyOption(str, Enum):
    second = 'second'
    minute = 'minute'
    hour = 'hour'
    day = 'day'
    week = 'week'
    month = 'month'
    year = 'year'
    quarter = 'quarter'

    @staticmethod
    def options_as_list():
        return [e.value for e in FrequencyOption]


class SampleFreqOptions(str, Enum):
    days = 'days'
    seconds = 'seconds'
    microseconds = 'microseconds'
    milliseconds = 'milliseconds'
    minutes = 'minutes'
    hours = 'hours'
    weeks = 'weeks'


@dataclass
class SampleRate(timedelta):
    base_freq: SampleFreqOptions
    multiplier: float

    def __new__(
            cls,
            multiplier: float,
            base_freq: SampleFreqOptions
    ):
        # Would normally use super().__new__(cls,...) here
        # but I think pydantic's @validate_arguments may be messing with
        # __new__ method too. Seems safe enough to use timedelta
        # since it is the parent class
        return multiplier * timedelta(**{base_freq: 1.0})


@dataclass
class TimeBin:
    start: Union[time, int, tuple, dict]
    end: Union[time, int]

    def __post_init__(self):
        if isinstance(self.start, int):
            self.start = time(self.start)
        if isinstance(self.end, int):
            self.end = time(self.end)

        if isinstance(self.start, tuple):
            self.start = time(*self.start)
        if isinstance(self.end, tuple):
            self.end = time(*self.end)

        if isinstance(self.start, dict):
            self.start = time(**self.start)
        if isinstance(self.end, dict):
            self.end = time(**self.end)

    @property
    def as_list(self):
        return [self.start, self.end]

    @property
    def as_tuple(self):
        return tuple(self.as_list)


@dataclass
class TouBins:
    time_bins: List[int]
    bin_rates: List[float]
    bin_labels: List[str]

