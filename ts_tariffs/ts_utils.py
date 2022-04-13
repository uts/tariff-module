from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import time, timedelta, datetime, date
from enum import Enum
from types import MappingProxyType
from typing import Union, List, Tuple, Dict, Callable
from dateutil.relativedelta import relativedelta


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


def params_to_dt_obj(
        param: Union[time, date, datetime, int, dict, tuple, list],
        dt_dtype: Callable[..., Union[time, date, datetime]]
):
    """ Instantiate datetime time specifying object (time, date or datetime) with optional
    params, OR if object already provided as param simply pass it through
    """
    dt_type_value_error = ValueError(
        f'ValueError: param must must be appropriate type/s and value/s to instantiate a datetime.{dt_dtype.__name__} object'
        f'OR must be a datetime.{dt_dtype.__name__} object'
        f'See datetime.time docs for approptiate types/values to instantiate datetime.{dt_dtype.__name__} : '
        f'https://docs.python.org/3/library/datetime.html'
    )

    if not isinstance(param, (time, date, datetime)):
        raise dt_type_value_error

    if isinstance(param, (datetime, date, time)):
        # Param is already instance of target object
        return param

    elif isinstance(param, int):
        #Only valid for datetime.time
        if isinstance(dt_dtype, (date, datetime)):
            raise dt_type_value_error
        else:
            return time(param)
    # Cases valid for all three types
    elif isinstance(param, (tuple, list)):
        return dt_dtype(*param)
    elif isinstance(param, dict):
        return dt_dtype(**param)
    elif isinstance(param, str):
        return dt_dtype.fromisoformat(param)
    else:
        raise dt_type_value_error


@dataclass
class TemporalWindow(ABC):
    start: Union[datetime, time, date]
    end: Union[datetime, time, date]
    temporal_type: Callable[..., Union[datetime, time, date]]

    @property
    def as_list(self) -> List[time]:
        return [self.start, self.end]

    @property
    def as_tuple(self) -> Tuple[time]:
        return tuple(self.as_list)

    @property
    def as_dict(self) -> Dict[str, time]:
        return {
            'start': self.start,
            'end': self.end
        }

    def __post_init__(self):
        self.start = params_to_dt_obj(self.start, self.temporal_type)
        self.end = params_to_dt_obj(self.end, self.temporal_type)

    def shift_period(
            self,
            freq: FrequencyOption,
            periods: int,
            start: bool = True,
            end: bool = True
    ):
        if freq == 'quarter':
            freq = 'month'
            periods *= 4

        try:
            # Validate freq
            getattr(self.start, freq)
        except TypeError:
            valid_fields = {
                time: ('hour', 'minute', 'second', 'microsecond',),
                date: ('year', 'month', 'day',),
                datetime: ('year', 'month', 'day', 'hour', 'minute', 'second', 'microsecond',),
            }
            raise ValueError(
                f'Cannot shift "{freq}" for {self.__class__.__name__}.'
                f'Must shift using any of {valid_fields[self.temporal_type]}'
            )
        # modify freq string to align with the params relativedelta uses to add deltas
        # (note that if you do not use plural here - e.g. months, as opposed to month - relativedelta
        # will replace the attr, not add to it)
        freq += 's'
        if start:
            self.start += relativedelta(**{freq: periods})
        if end:
            self.end += relativedelta(**{freq: periods})


@dataclass
class TimeWindow(TemporalWindow):
    temporal_type: Callable[..., time] = field(init=False, default=time)


@dataclass
class DateWindow(TemporalWindow):
    temporal_type: Callable[..., date] = field(init=False, default=date)


@dataclass
class DatetimeWindow(TemporalWindow):
    temporal_type: Callable[..., datetime] = field(init=False, default=datetime)


@dataclass
class TouBins:
    time_bins: List[int]
    bin_rates: List[float]
    bin_labels: List[str]

