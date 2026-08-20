# PharmaVoice

PharmaVoice is a pharmacy voice assistant that connects Twilio phone-call
audio to Deepgram's agent API. It can answer medication questions, place
pharmacy orders, and look up order status during a live call.

## Features

- Real-time voice conversation over Twilio Media Streams
- Deepgram agent integration for listening, reasoning, and speaking
- Pharmacy tool calls for drug lookup, order placement, and order lookup
- SQLite persistence for customers, inventory, orders, and order history
- JSON-based seed inventory for local pharmacy data
- Unit tests for the pharmacy function layer

## Requirements

- Python 3.14 or newer
- A Deepgram API key
- Twilio voice number and Media Streams configuration
- `uv` or another Python environment/dependency manager

## Project Structure

```text
.
|-- main.py                         # WebSocket bridge between Twilio and Deepgram
|-- config.json                     # Deepgram agent settings and tool definitions
|-- pharmacy_functions.py           # Tool functions exposed to the agent
|-- pharmacy_storage.py             # SQLite storage and inventory seeding
|-- pharmacy_inventory.example.json # Example inventory format
|-- pharmacy_inventory.json         # Local inventory file, ignored by Git
|-- pharmacy.db                     # Local SQLite database, generated at runtime
`-- tests/                          # Unit tests
```

## Setup

Install dependencies:

```bash
uv sync
```

If you are not using `uv`, create a virtual environment and install the
dependencies listed in `pyproject.toml`.

Create your local inventory file:

```bash
cp pharmacy_inventory.example.json pharmacy_inventory.json
```

Add your environment variables. You can place them in a `.env` file or export
them in your shell:

```bash
DEEPGRAM_API_KEY=your_deepgram_api_key
```

Optional storage overrides:

```bash
PHARMACY_DB_PATH=/path/to/pharmacy.db
PHARMACY_DATA_PATH=/path/to/pharmacy_inventory.json
```

## Running the App

Start the local WebSocket server:

```bash
uv run python main.py
```

The server listens on:

```text
ws://localhost:5000
```

For Twilio to reach your local server, expose port `5000` with a tunnel such as
ngrok, then configure the Twilio voice webhook or TwiML app to start a Media
Stream to your public WebSocket URL.

## Pharmacy Data

PharmaVoice stores pharmacy data in SQLite. By default, it creates and uses
`pharmacy.db` in the project directory.

The database contains:

- Customers
- Drug inventory
- Orders
- Order status history

Inventory is seeded from `pharmacy_inventory.json` when the database is
initialized. The local inventory file is ignored by Git so private medicine data
does not get committed. Use `pharmacy_inventory.example.json` as the structure
reference.

Each drug entry should include:

- `slug`: lowercase identifier used by tool calls
- `name`: display name
- `description`: short medication description
- `price`: package price
- `currency`: currency code, such as `INR`
- `quantity`: package quantity
- `stock`: available package count

## Agent Tools

The Deepgram agent is configured in `config.json` with these tool functions:

- `get_drug_info`: returns medication description, price, quantity, and stock
- `place_order`: creates a pending pharmacy order for a customer
- `lookup_order`: returns order details and status history by order ID

The Python implementation for these tools lives in `pharmacy_functions.py`, with
persistent storage handled by `pharmacy_storage.py`.

## Testing

Run the test suite:

```bash
uv run python -m unittest discover -s tests
```

Without `uv`, run the same command from an activated virtual environment:

```bash
python -m unittest discover -s tests
```

## Notes

- `pharmacy_inventory.json` should be created locally from the example file.
- `pharmacy.db` is generated automatically when the app starts or a pharmacy
  function runs.
- Keep real API keys and production inventory data out of Git.
