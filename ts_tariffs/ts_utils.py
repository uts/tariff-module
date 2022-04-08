from dataclasses import dataclass
from datetime import time
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
    'quarter': 'Q'
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

