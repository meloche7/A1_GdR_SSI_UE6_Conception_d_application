# Database Structure

This document describes the structure of the SQLite database (`barrage.db`).

## Table: `meteo`

Stores meteorological and hydrological data.

| Column              | Type    | Description                                  |
| ------------------- | ------- | -------------------------------------------- |
| `id`                | INTEGER | Primary Key (auto-incrementing)              |
| `date`              | TEXT    | Date of the reading (format: YYYY-MM-DD)     |
| `debit_riviere_m3s` | REAL    | River flow in cubic meters per second (m³/s) |
| `pluviometrie_mm`   | REAL    | Rainfall in millimeters (mm)                 |

---

## Table: `meteo_previsions`

Stores weather and hydrological forecast data.

| Column                    | Type    | Description                                                     |
| ------------------------- | ------- | --------------------------------------------------------------- |
| `id`                      | INTEGER | Primary Key (auto-incrementing)                                 |
| `date_prevision`          | TEXT    | The future date for which the forecast is made (YYYY-MM-DD)     |
| `date_creation`           | TEXT    | The date on which the forecast was generated (YYYY-MM-DD)       |
| `debit_riviere_m3s_prevu` | REAL    | The forecasted river flow in cubic meters per second (m³/s)     |
| `pluviometrie_mm_prevue`  | REAL    | The forecasted rainfall in millimeters (mm)                     |

---

## Table: `maintenance`

Stores maintenance intervention tickets.

| Column           | Type    | Description                                                     |
| ---------------- | ------- | --------------------------------------------------------------- |
| `id`             | INTEGER | Primary Key (auto-incrementing)                                 |
| `id_equipement`  | TEXT    | A unique identifier for the piece of equipment (e.g., "T1")     |
| `nom_equipement` | TEXT    | The name of the equipment (e.g., "Turbine 1")                   |
| `statut`         | TEXT    | The status of the ticket (e.g., "En cours", "Terminé")          |
| `description`    | TEXT    | A description of the issue or the intervention requested.       |
| `date_creation`  | TEXT    | The creation date of the ticket (format: YYYY-MM-DD)            |

---

## Table: `production`

Stores electricity production data.

| Column          | Type    | Description                                             |
| --------------- | ------- | ------------------------------------------------------- |
| `id`            | INTEGER | Primary Key (auto-incrementing)                         |
| `date`          | TEXT    | Date of the production summary (format: YYYY-MM-DD)     |
| `production_mwh`| REAL    | Total power produced in megawatt-hours (MWh)            |
| `volume_eau_m3` | INTEGER | Total volume of water used in cubic meters (m³)         |
