from ts_tariffs.tariffs import SingleRateTariff

my_tariff = SingleRateTariff(
    name='my_tariff',
    charge_type="SingleRateTariff",
    rate=0.07,
    consumption_unit='kWh',
    rate_unit='dollars / kWh',
    adjustment_factor=1.05
)

print(my_tariff)