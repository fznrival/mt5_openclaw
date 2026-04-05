# opnclaw_automated-trade

mt5_openclaw/
├── mql5/
│   └── TradeExporter.mq5          ← EA di MT5, export trade ke CSV
├── python/
│   ├── trade_summary.py           ← Script utama: baca CSV → kirim Telegram
│   └── generate_sample_data.py    ← Buat data dummy untuk testing
├── openclaw_skill/
│   └── trading-reporter.skill.json ← Skill OpenClaw (trigger via Telegram)
├── setup_mt5_wine.sh              ← Install Wine + MT5 di Linux
├── setup_cron.sh                  ← Setup jadwal otomatis
├── trade_config.example.json      ← Template konfigurasi
└── README.md                      ← Ini
