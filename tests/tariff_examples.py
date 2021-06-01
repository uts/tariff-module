tou_schema = {
    'name': 'tou_tariff',
    'consumption_unit': 'kWh',
    'time_bins': [7, 17, 20, 24],
    'bin_rates': [0.12, 0.20, 0.28, 0.12],
    'bin_labels': ['off-peak', 'shoulder', 'peak', 'off-peak'],
    'rate_unit': 'dollars',
}

demand_charge_schema = {
    'name': 'demand_tariff',
    'consumption_unit': 'kWh',
    'rate': 17.35,
    'frequency_applied': 'month',
    'tou': {
        'name': 'tou_tariff',
        'consumption_unit': 'kWh',
        'time_bins': [7, 17, 20, 22, 24],
        'bin_rates': [1.4565, 6.0031, 6.6351, 1.4565],
        'bin_labels': ['off-peak', 'shoulder', 'peak', 'off-peak'],
        'rate_unit': 'dollars',
    },
    'rate_unit': 'cents'
}

block_schema = {
    'name': 'Block',
    'frequency_applied': 'month',
    'threshold_bins': [(0, 300.), (300, 450.), (450, float('inf'))],
    'bin_rates': [.27, .29, .23],
    'bin_labels': ['', '', '', ''],
    'consumption_unit': 'kWh',
    'rate_unit': 'dollars',
}

connection_schema = {
    'name': 'connection_tariff',
    'rate': 0.9,
    'consumption_unit': 'day',
    'frequency_applied': 'day',
    'rate_unit': 'dollars',
}

single_schema = {
    'name': 'single_tariff',
    'rate': 25,
    'consumption_unit': 'kWh',
    'rate_unit': 'cents',
}

regime_1 = {
    'name': 'regime_example',
    'metering_sample_rate': {
        'minutes': 30
    },
    'charges': [
        tou_schema,
        block_schema,
        single_schema,
        connection_schema,
        demand_charge_schema,
    ]
}