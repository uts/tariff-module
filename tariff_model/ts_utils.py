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
        col,
        statistics,
        periods,
        tou=None,
):
    axis_names = periods
    bins = list([getattr(ts.index, period) for period in periods])
    if tou:
        time_bins = pd.cut(
            ts.index.hour,
            tou.time_bins,
            tou.bin_labels,
        )
        bins.append(time_bins)
        axis_names.append('hour')
    grouped = ts.groupby(bins)[col]\
        .agg(statistics)\
        .rename_axis(axis_names)
    # Remove non-existent bin combos by removing blanks
    # (e.g. month 2 combined with date 2013-01-01)
    grouped.dropna(subset=statistics, inplace=True)
    return grouped

