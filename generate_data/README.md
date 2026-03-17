# Data Generation for SI Barrage Project

This directory contains scripts and raw data to generate a synthetic SQLite database for the project.

The data is separated into CSV files:

* `meteo_data.csv`: Synthetic weather and river data.
* `maintenance_data.csv`: Synthetic maintenance tickets.
* `production_data.csv`: Synthetic electricity production data.
* `meteo_previsions_data.csv`: Synthetic weather forecast data.
* `intervention_data.csv`: Detailed maintenance intervention records.
* `centrale_parametres_data.csv`: Technical and economic parameters for the plant.

## How to use

To generate the SQLite database (`barrage.db`), run the following command from the root of the project:

```shell
uv run python generate_data/create_database.py
```

This will create a `barrage.db` file in the root directory, containing six tables (`meteo`, `maintenance`, `production`, `meteo_previsions`, `intervention`, `centrale_parametres`) populated with the data from the CSV files.

You can explore the database structure in the `database_structure.md` file.
