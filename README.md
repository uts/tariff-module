# Tariff calculation for time series consumption data.

## Motivation
Calculating tariff's is a common task for technoeconomic modelling, particularly in industries like energy and water.

The ts-tariffs library aims to provide convenient, easy-to-use tools for dealing with tariffs in modelling projects.

The goal of this library is to expand its coverage of tariff structures as widely as possible, and where coverage is not provided, to act as a stable, extensible toolbase for the creation of bespoke tariff models

While coverage of tariff types will increase over time, the scope of this library will remain narrow to ensure maintanability.

## Installation

`pip install ts-tariffs`

## Coverage
ts-tariffs can presently deal with common tariffs (so far all derived from electricity billing, but some are applicable more broadly):
- Connection charges
- Single rate charges
- Time of use charges
- Demand charges, including those which are specify time of use
- Block charges
- Capacity charges

Soon to come:
- Critical peak charges

Coverage will continue to be expanded - feature pull requests are encouraged for all timeseries tariff types

## How to

<details>
  <summary>Create Tariffs</summary>

Tariffs can be instantiated by individually specifying parameters:


```python
from ts_tariffs.tariffs import (
    SingleRateTariff, 
    ConnectionTariff, 
    TouTariff, 
    DemandTariff, 
    BlockTariff, 
    CapacityTariff,
)
from ts_tariffs.ts_utils import SampleRate

single_rate_tariff = SingleRateTariff(
    name='single_rate_tariff',
    charge_type="SingleRateTariff",
    rate=0.07,
    consumption_unit='kWh',
    rate_unit='dollars / kWh',
    sample_rate=SampleRate(multiplier=30, base_freq='minutes'),
    adjustment_factor=1.05
)
```

Or can be easily instantiated given a dict of appropriate structure:


```python
single_rate_dict = {
    "name": "single_rate_tariff",
    "charge_type": "SingleRateTariff",
    "rate": 0.07,
    "consumption_unit": "kWh",
    "sample_rate": {
        "multiplier": 30,
        "base_freq": "minutes"
    },
    "rate_unit": "dollars / kWh",
    "adjustment_factor": 1.005
}

tou_tariff_dict = {
    "name": "retail_tou",
    "charge_type": "TouTariff",
    "consumption_unit": "kWh",
    "sample_rate": {
        "multiplier": 30,
        "base_freq": "minutes"
    },
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
}
connection_tariff_dict = {
    "name": "connection_tariff",
    "charge_type": "ConnectionTariff",
    "rate": 315.0,
    "consumption_unit": "day",
    "frequency_applied": "day",
    "sample_rate": {
        "multiplier": 30,
        "base_freq": "minutes"
    },
    "rate_unit": "dollars / day",
    "adjustment_factor": 1.0
}

single_rate_tariff = SingleRateTariff.from_dict(single_rate_dict)
tou_tariff = TouTariff.from_dict(tou_tariff_dict)
connection_tariff = ConnectionTariff.from_dict(connection_tariff_dict)
```
</details>

<details>
    <summary>Create consumption meter data</summary>

The ts-tariffs library provides a `MeterData` object for handling timeseries consumption data. It accepts a `pd.Series` with a `datetime` index as a representation of consumtion.

The sample rate must be specified manually with a `timedelta` of `SampleRate` object (in future versions this may end up being inferred from the series index, but there are presently issues with this approach).

Consumption units must also be specified such that they are coherent with the tariffs that are applied to them (this is particularly important for `Meters` objects in which multiple tariffs can be bundled together with multi-channel meters - discussed later)

The `meter_data_df` below is a `pd.DataFrame` object with a datetime index at 30min frequency, and a consumption column called `'energy'`. A `MeterData` object is then created as follows:


```python
from ts_tariffs.meters import MeterData
from ts_tariffs.examples.data_getters import houshold_consumption

# Get consumption timeseries at 30min sample rate
meter_data_df = houshold_consumption(30, 'minute')

sample_rate = SampleRate(multiplier=30, base_freq='minutes')    # Alternatively you could use timedelta(minutes=30) here
my_meter_data = MeterData(
    name='energy',
    tseries=meter_data_df['energy'],
    sample_rate=sample_rate,
    units='kWh'
)
```

</details>

<details>
    <summary>Calculate bills</summary>


You can calculate the cost of energy tariffs to meter data by calling the `Tariff.apply() method`*. This returns an `AppliedCharge` object which contains the total sum of charges, as well as other data/metadata, depending on the tariff type

*Note: Presently the `Tariff.sample_rate` must be in agreement with `MeterData.sample_rate`. Future versions may automatically resample, assuming the resample rule (e.g. `mean()` or `sum()`) can be inferred from the units


```python
single_rate_applied_charge = single_rate_tariff.apply(my_meter_data)
```

A `Bill` object can be used to tabulate the charge totals for one or more tariffs if given a `MeterData`. A `Bill` consists of one or many `AppliedCharge` objects:


```python
from ts_tariffs.billing import Bill
my_bill = Bill(
    name='my_bill',
    charges=[
        single_rate_tariff.apply(my_meter_data),
        tou_tariff.apply(my_meter_data),
        connection_tariff.apply(my_meter_data),
    ]
)
print(my_bill.as_series)
```

```python
single_rate_tariff      1357.642382
retail_tou              1688.470396
connection_tariff     229635.000000
Name: my_bill, dtype: float64
```
</details>
