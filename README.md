#Tariff calculation for time series consumption data.

## Installation

`pip install ts-tariffs`

## Usage and features
ts-tariffs can deal with any combination of typical electricity charges: 
- Connection charges 
- Single rate charges
- Time of use charges
- Demand charges, including those which are split into time of use
- Block charges

## Examples

### Creating Tariffs
`Tariff` objects can be instantiated as follows:

[single rate example](ts_tariffs/example_shorts/single_rate.py)

```python
from ts_tariffs.tariffs import SingleRateTariff

my_tariff = SingleRateTariff(
    name='my_tariff',
    charge_type="SingleRateTariff",
    rate=0.07,
    consumption_unit='kWh',
    rate_unit='dollars / kWh',
    adjustment_factor=1.05
)
```

Or can be easily instantiated using a dict:
```python
my_tariff_dict = {
      "name": "my_tariff",
      "charge_type": "SingleRateTariff",
      "rate": 0.07,
      "consumption_unit": "kWh",
      "rate_unit": "dollars / kWh",
      "adjustment_factor": 1.005
}

my_tariff = SingleRateTariff(**my_tariff_dict)
```

### Consumption data
Consumtion data should be stored in a `MeterData` object using a `pd.Series` with a `datetime` index.

For example, assuming you have a `pd.DataFrame` object `df` with a datetime index at 30min frequency, and a consumption column called `'energy'`, you would create a `MeterData` object as follows:
```python
from ts_tariffs.meters import MeterData

my_meter_data = MeterData(
    'energy',
    df['Consumption (kWh)'], 
    timedelta(hours=0.5),
    units='kWh'
)
```

### Calculating charges and billing
You can apply tariffs to meter data by calling the `Tariff.apply() method`. This returns an `AppliedCharge` object.
```python
applied_charge = my_tariff.apply(my_meter_data)
```

You can construct a `Bill` with one or many `AppliedCharge` objects:
```python
charges = [
    my_tariff_1.apply(my_meter_data),
    my_tariff_2.apply(my_meter_data),
    my_tariff_3.apply(my_meter_data),
]
my_bill = Bill(
    name='my_bill',
    charges=charges
)
```



Many `Tariff` objects can be stored together in a `TariffRegime` object. dict

This makes it convenient to store tariff data in a : 
```python
tariff_data = {
  "charges": [
    {
      "name": "retail_tou",
      "charge_type": "TouTariff",
      "consumption_unit": "kWh",
      "rate_unit": "dollars / kWh",
      "adjustment_factor": 1.005,
      "tou": {
        "time_bins": [
          7,
          21,
          24
        ],
        "bin_rates": [
          0.06,
          0.10,
          0.06
        ],
        "bin_labels": [
          "off-peak",
          "peak",
          "off-peak"
        ]
      },
    },
    {
      "name": "lrecs",
      "charge_type": "SingleRateTariff",
      "rate": 0.007,
      "consumption_unit": "kWh",
      "rate_unit": "dollars / kWh",
      "adjustment_factor": 1.005
    },
    {
      "name": "srecs",
      "charge_type": "SingleRateTariff",
      "rate": 0.0114,
      "consumption_unit": "kWh",
      "rate_unit": "dollars / kWh",
      "adjustment_factor": 1.005
    },
    {
      "name": "connection_tariff",
      "charge_type": "ConnectionTariff",
      "rate": 315.0,
      "consumption_unit": "day",
      "frequency_applied": "day",
      "rate_unit": "dollars / day",
      "adjustment_factor": 1.0
    },
    {
      "name": "tuos_energy",
      "charge_type": "SingleRateTariff",
      "rate": 0.011,
      "consumption_unit": "kWh",
      "rate_unit": "dollars / kWh",
      "adjustment_factor": 1.005

    },
    {
      "name": "ICC11B_energy",
      "charge_type": "SingleRateTariff",
      "rate": 0.0021,
      "consumption_unit": "kWh",
      "rate_unit": "dollars / kWh",
      "adjustment_factor": 1.0
    },
    {
      "name": "ICC11B_demand",
      "charge_type": "DemandTariff",
      "consumption_unit": "kVA",
      "rate": 0.850,
      "frequency_applied": "month",
      "rate_unit": "dollars / kVA / month",
      "adjustment_factor": 1.0
    },
    {
      "name": "ICC11B_location",
      "charge_type": "DemandTariff",
      "consumption_unit": "kW",
      "rate": 1.190,
      "frequency_applied": "month",
      "rate_unit": "dollars / kW / month",
      "adjustment_factor": 1.0
    },
    {
      "name": "duos_capacity",
      "charge_type": "CapacityTariff",
      "consumption_unit": "kVA",
      "capacity": 10000.0,
      "rate": 0.400,
      "frequency_applied": "month",
      "rate_unit": "dollars / kVA / month",
      "adjustment_factor": 1.0
    },
    {
      "name": "aemo_market_energy_fee",
      "charge_type": "SingleRateTariff",
      "rate": 0.00055,
      "consumption_unit": "kWh",
      "rate_unit": "dollars / kWh",
      "adjustment_factor": 1.005
    },
    {
      "name": "aemo_market_daily_fee",
      "charge_type": "ConnectionTariff",
      "rate": 0.003700,
      "consumption_unit": "day",
      "frequency_applied": "day",
      "rate_unit": "dollars / day",
      "adjustment_factor": 1.0
    },
    {
      "name": "aemo_market_ancillary_fee",
      "charge_type": "SingleRateTariff",
      "rate": 0.00121,
      "consumption_unit": "kWh",
      "rate_unit": "dollars / kWh",
      "adjustment_factor": 1.005
    },
    {
      "name": "metering_charge",
      "charge_type": "ConnectionTariff",
      "rate": 100.0,
      "consumption_unit": "month",
      "frequency_applied": "month",
      "rate_unit": "dollars / month",
      "adjustment_factor": 1.0
    },
  ]
}
```


## Under development
- units handling

