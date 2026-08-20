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

You can override the database path with:

```bash
PHARMACY_DB_PATH=/path/to/pharmacy.db python main.py
```

The database schema and default drug inventory are initialized automatically
the first time a pharmacy function runs.

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
