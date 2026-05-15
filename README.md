# AgentVault AI

AI x Web3 hackathon MVP for the 0G APAC Hackathon. AgentVault AI accepts a wallet address or crypto project name, generates an AI intelligence report, stores the report on 0G Storage testnet, and displays persistent report history.

## Stack

- Frontend: React, Vite, TailwindCSS
- Backend: Django, Django REST Framework, SQLite
- AI: OpenAI/DeepSeek/OpenAI-compatible providers, deterministic local fallback for demos
- Wallet data: Etherscan V2 indexed transaction history with JSON-RPC fallback
- Storage: 0G Storage testnet through the official Python SDK

## Project Structure

```text
agentvault-ai/
  backend/
    agentvault/
    reports/
    manage.py
    requirements.txt
    .env.example
  frontend/
    src/
    package.json
    tailwind.config.js
  README.md
```

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

Edit `backend/.env`:

```env
DJANGO_SECRET_KEY=replace-me
DEBUG=True
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
AI_API_KEY=
AI_BASE_URL=
AI_MODEL=
OG_PRIVATE_KEY=0x-your-funded-0g-testnet-private-key
OG_BLOCKCHAIN_RPC=https://evmrpc-testnet.0g.ai
WALLET_RPC_URL=https://evmrpc-testnet.0g.ai
WALLET_SCAN_BLOCKS=8
WALLET_SCAN_SECONDS=6
ETHERSCAN_API_KEY=
ETHERSCAN_CHAIN_ID=1
ETHERSCAN_TX_LIMIT=40
OG_INDEXER_RPC=https://indexer-storage-testnet-turbo.0g.ai
OG_EXPLORER_TX_URL=https://chainscan-galileo.0g.ai/tx/{tx_hash}
```

`OG_PRIVATE_KEY` must belong to a funded 0G testnet wallet for real storage uploads. If it is missing, `/api/store/` returns a local demo storage record marked as `local-demo`.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL, usually `http://localhost:5173`.

## API

### `POST /api/analyze/`

Request:

```json
{ "query": "0x1234...abcd", "chain_id": 1 }
```

Response:

```json
{
  "query": "0x1234...abcd",
  "input_type": "wallet",
  "raw_data": {},
  "ai": {
    "ai_provider": "openai",
    "ai_model": "gpt-4o-mini",
    "ai_status": "live"
  },
  "report": {
    "summary": "",
    "risk_level": "low",
    "key_behaviors": [],
    "insights": [],
    "recommendation": ""
  }
}
```

### `POST /api/store/`

Request:

```json
{
  "query": "0x1234...abcd",
  "input_type": "wallet",
  "raw_data": {},
  "report": {}
}
```

Response includes `root_hash`, `tx_hash`, `explorer_url`, and the saved report record.

### `GET /api/history/`

Returns stored report metadata and report JSON.

### `GET /api/report/<id>/`

Returns one stored report. If a 0G `root_hash` exists, the backend attempts to retrieve the report from 0G Storage and falls back to the database copy while files propagate.

## Demo Flow

1. Enter a wallet address, project name, or website URL.
2. Select the wallet chain for Etherscan-indexed analysis.
3. Click `Generate Report`.
4. Review the AI report on the dashboard.
5. Click `Store on 0G`.
6. Open `History` to see persistent reports and blockchain proof links.

## Notes for Judges

- Real 0G Storage integration lives in `backend/reports/storage_0g.py`.
- The upload code uses the official Python SDK package `0g-storage-sdk` and testnet endpoints.
- Wallet analysis uses Etherscan V2 indexed normal, internal, and ERC-20 transfer history when `ETHERSCAN_API_KEY` is configured.
- The dashboard displays whether AI came from a live provider or local fallback.
- AI output is normalized and validated into the required JSON shape.
- JSON-RPC and deterministic fallback paths keep the demo usable if third-party APIs are unavailable.
