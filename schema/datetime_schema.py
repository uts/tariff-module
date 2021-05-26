

period_schema = {
    'month': ['year', 'month'],
    'week': ['year', 'month', 'week', ],
    'day': ['year', 'month', 'date'],
    'quarter': ['year', 'quarter']
}

periods_slice_schema = {
    'month': [slice(None), slice(None)],
    'week': [slice(None), slice(None), slice(None)],
    'day': [slice(None), slice(None), slice(None), ],
    'quarter': [slice(None), slice(None)]
}

resample_schema = {
    'second': 'S',
    'minute': 'T',
    'hour': 'H',
    'week': 'W',
    'day': 'D',
    'month': 'M',
    'quarter': 'Q'
}