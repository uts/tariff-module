

period_schema = {
    'month': ['year', 'month'],
    'week': ['year', 'month', 'week', ],
    'day': ['year', 'month', 'date'],
    'quarter': ['year', 'quarter']
}

period_slice = {
    'month': [slice(None), slice(None)],
    'week': [slice(None), slice(None), slice(None)],
    'day': [slice(None), slice(None), slice(None), ],
    'quarter': [slice(None), slice(None)]
}