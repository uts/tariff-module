import pandas as pd
import numpy as np

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
        statistic,
        periods,
        tou=None,
) -> pd.DataFrame:
    axis_names = periods
    bins = list([getattr(ts.index, period) for period in periods])
    ts[col].fillna(method='bfill', inplace=True)
    ts[col].replace([np.inf, -np.inf], np.nan, method='bfill', inplace=True)
    grouped = ts.groupby(bins)[col]\
        .agg([statistic])\
        .rename_axis(axis_names)
    ts_dt = ts.copy()
    ts_dt['dt'] = ts_dt.index
    grouped['period_start'] = ts_dt['dt'].groupby(bins).min()
    # Remove non-existent bin combos by removing blanks
    # (e.g. month 2 combined with date 2013-01-01)
    grouped.dropna(subset=[statistic], inplace=True)
    return grouped

