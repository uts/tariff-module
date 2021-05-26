

period_schema = {
    'month': ['year', 'month'],
    'week': ['year', 'month', 'week',],
    'day': ['year', 'month', 'day'],
    'quarter': ['year', 'quarter']
}

period_slice = {
    'month': [1, ],
    'week': ['year', 'month', 'week', ],
    'day': ['year', 'month', 'week', 'day'],
    'quarter': ['year', 'quarter']
}