tou_schema = {
    'name': 'tou_tariff',
    'charge_type': 'TOUCharge',
    'consumption_unit': 'kWh',
    'tou': {
        'time_bins': [0, 7, 17, 20, 24],
        'bin_rates': [0.12, 0.20, 0.28, 0.12],
        'bin_labels': ['off-peak', 'shoulder', 'peak', 'off-peak'],
    },
    'rate_unit': 'dollars / kWh',
}

demand_charge_schema = {
    'name': 'demand_tariff',
    'charge_type': 'DemandCharge',
    'consumption_unit': 'kWh',
    'rate': 17.35,
    'frequency_applied': 'day',
    'tou': {
        'name': 'tou_tariff',
        'charge_type': 'time_of_use',
        'consumption_unit': 'kWh',
        'time_bins': [0, 7, 17, 20, 24],
        'bin_rates': [1.4565, 6.0031, 6.6351, 1.4565],
        'bin_labels': ['off-peak', 'shoulder', 'peak', 'off-peak'],
        'rate_unit': 'dollars / kWh',
    },
    'rate_unit': 'cents / kWh'
}

block_schema = {
    'name': 'block_tariff',
    'charge_type': 'BlockCharge',
    'frequency_applied': 'month',
    'blocks': [(0, 300.), (300, 450.), (450, float('inf'))],
    'bin_rates': [.27, .29, .23],
    'bin_labels': ['', '', '', ''],
    'consumption_unit': 'kWh',
    'rate_unit': 'dollars / kWh',
}

connection_schema = {
    'name': 'connection_tariff',
    'charge_type': 'ConnectionCharge',
    'rate': 0.9,
    'consumption_unit': 'day',
    'frequency_applied': 'day',
    'rate_unit': 'dollars / kWh',
}

single_schema = {
    'name': 'single_tariff',
    'charge_type': 'SingleRateCharge',
    'rate': 25,
    'consumption_unit': 'kWh',
    'rate_unit': 'cents / kWh',
}

regime_1 = {
    'name': 'regime_example',
    'metering_sample_rate': {
        'minutes': 30
    },
    'charges': [
        single_schema,
        tou_schema,
        block_schema,
        connection_schema,
        demand_charge_schema,
    ]
}

single_schema_errors = {
    'name': 'single_tariff',
    'charge_type': 'single_rate',
    'rate': 'dodgy text',
    'consumption_unit': 'kWh',
    'rate_unit': 'cents',
}

regime_2 = {
    'name': 'regime_errors_example',
    'metering_sample_rate': {
        'minutes': 30
    },
    'charges': [
        single_schema_errors,
        tou_schema,
        block_schema,
        connection_schema,
        demand_charge_schema,
    ]
}