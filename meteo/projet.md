hydro_dashboard/
│
├── meteo/
│   ├── main.py
│   │
│   ├── database.py          ← connexion SQLite
│   │
│   ├── models/
│   │   └── forecast.py
│   │
│   ├── services/
│   │   ├── forecast_service.py
│   │   ├── alerts_service.py
│   │   └── plotting_service.py
│   │
│   └── routers/
│       └── forecast_router.py
│
└── barrage.db