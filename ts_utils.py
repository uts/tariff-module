import pandas as pd

def get_intervals_dict(bins, bin_names) -> dict:
    return {
        name: pd.Interval(left, right) for name, left, right in zip(
            bin_names,
            bins[:-1],
            bins[1:]
        )
    }


def get_intervals_list(bins) -> list:
    return [pd.Interval(left, right) for left, right in zip(bins[:-1], bins[1:])]

def get_period_statistic(
        ts: pd.DataFrame,
        col, statistics,
        periods,
        time_of_use=None,
):
    axis_names = periods
    bins = list([getattr(ts.index, period) for period in periods])
    if time_of_use:
        time_bins = pd.cut(
            ts.index.hour,
            time_of_use['time_bins'],
            time_of_use['bin_labels'],
        )
        bins.append(time_bins)
        axis_names.append('hour')

    return ts.groupby(bins)[col]\
        .agg(statistics)\
        .rename_axis(periods)
