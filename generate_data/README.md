# Data Generation for SI Barrage Project

This directory contains scripts and raw data to generate a synthetic SQLite database for the project.

The data is separated into three CSV files:

*   `meteo_data.csv`: Synthetic weather and river data.
*   `maintenance_data.csv`: Synthetic maintenance tickets.
*   `production_data.csv`: Synthetic electricity production data.

## How to use

To generate the SQLite database (`barrage.db`), run the following command from the root of the project:

```shell
uv run python generate_data/create_database.py
```

This will create a `barrage.db` file in the root directory, containing three tables (`meteo`, `maintenance`, `production`) populated with the data from the CSV files.

You can explore the database structure in the `database_structure.md` file.
