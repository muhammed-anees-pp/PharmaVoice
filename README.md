VoiceAgent
==========

VoiceAgent is a Twilio and Deepgram powered pharmacy voice assistant. It can
answer medication questions, place pharmacy orders, and look up existing order
status over a phone call.

Persistent Storage
------------------

The pharmacy data is stored in SQLite. By default, the app creates and uses
`pharmacy.db` in the project directory.

The database stores:

- Customers
- Drug inventory
- Orders
- Order status history

Drug inventory is seeded from `pharmacy_inventory.json`. This file is ignored
by Git so local medicine data is not committed. Use
`pharmacy_inventory.example.json` as the structure reference.

You can override the database and inventory paths with:

```bash
PHARMACY_DB_PATH=/path/to/pharmacy.db \
PHARMACY_DATA_PATH=/path/to/pharmacy_inventory.json \
python main.py
```

The database schema and drug inventory are initialized automatically the first
time a pharmacy function runs.

Development
-----------

Run the tests with:

```bash
python -m unittest discover -s tests
```

Run the voice agent server with:

```bash
python main.py
```

Required environment variables:

- `DEEPGRAM_API_KEY`
