import hashlib
from html.parser import HTMLParser
import os
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import requests

WALLET_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def detect_input_type(query: str) -> str:
    value = query.strip()
    if WALLET_RE.match(value):
        return "wallet"
    if URL_RE.match(value):
        return "website"
    return "project"


def build_activity_snapshot(query: str, chain_id: int | None = None) -> dict:
    seed = int(hashlib.sha256(query.lower().encode("utf-8")).hexdigest()[:12], 16)
    rng = random.Random(seed)
    input_type = detect_input_type(query)
    now = datetime.now(timezone.utc)

    if input_type == "wallet":
        return build_wallet_snapshot(query, rng, now, chain_id)

    if input_type == "website":
        return build_website_snapshot(query)

    return {
        "entity": query,
        "input_type": input_type,
        "tracked_signals": rng.sample(
            ["developer activity", "social traction", "liquidity growth", "token distribution", "partnership mentions"],
            k=4,
        ),
        "community_score": rng.randint(35, 96),
        "liquidity_score": rng.randint(25, 92),
        "contract_risk_flags": rng.randint(0, 4),
        "recent_mentions": rng.randint(120, 4200),
        "last_seen": (now - timedelta(hours=rng.randint(1, 72))).isoformat(),
    }


def build_wallet_snapshot(address: str, rng: random.Random, now: datetime, chain_id: int | None = None) -> dict:
    fallback = build_mock_wallet_snapshot(address, rng, now)
    etherscan_key = os.getenv("ETHERSCAN_API_KEY", "").strip()
    if etherscan_key:
        try:
            return build_etherscan_wallet_snapshot(address, etherscan_key, chain_id)
        except Exception as exc:
            fallback["indexer_error"] = str(exc)

    rpc_url = os.getenv("WALLET_RPC_URL") or os.getenv("OG_BLOCKCHAIN_RPC") or "https://evmrpc-testnet.0g.ai"
    scan_blocks = int(os.getenv("WALLET_SCAN_BLOCKS", "8"))
    scan_seconds = float(os.getenv("WALLET_SCAN_SECONDS", "6"))

    try:
        chain_id = int(_rpc(rpc_url, "eth_chainId", []), 16)
        latest_block = int(_rpc(rpc_url, "eth_blockNumber", []), 16)
        balance_wei = int(_rpc(rpc_url, "eth_getBalance", [address, "latest"]), 16)
        nonce = int(_rpc(rpc_url, "eth_getTransactionCount", [address, "latest"]), 16)
        code = _rpc(rpc_url, "eth_getCode", [address, "latest"])

        recent_txs = _scan_recent_wallet_transactions(rpc_url, address, latest_block, scan_blocks, scan_seconds)
        outgoing = [tx for tx in recent_txs if tx["direction"] == "outgoing"]
        incoming = [tx for tx in recent_txs if tx["direction"] == "incoming"]
        counterparties = {tx["counterparty"] for tx in recent_txs if tx["counterparty"]}
        transferred_native = round(sum(tx["value_native"] for tx in recent_txs), 8)

        behaviors = []
        if outgoing:
            behaviors.append("outgoing transfers")
        if incoming:
            behaviors.append("incoming transfers")
        if nonce == 0:
            behaviors.append("new or inactive wallet")
        if code and code != "0x":
            behaviors.append("contract account")
        if balance_wei > 0:
            behaviors.append("holds native balance")
        if not behaviors:
            behaviors.append("no recent transfer activity in scanned window")

        return {
            "entity": address,
            "input_type": "wallet",
            "data_source": "real-json-rpc",
            "rpc_url": rpc_url,
            "chain_id": chain_id,
            "latest_scanned_block": latest_block,
            "scanned_block_count": min(scan_blocks, latest_block + 1),
            "balance_native": round(balance_wei / 10**18, 8),
            "transaction_count": nonce,
            "recent_transfer_count": len(recent_txs),
            "incoming_transfer_count": len(incoming),
            "outgoing_transfer_count": len(outgoing),
            "estimated_volume_eth": transferred_native,
            "counterparty_count": len(counterparties),
            "high_value_transfer_count": sum(1 for tx in recent_txs if tx["value_native"] >= 1),
            "failed_transaction_ratio": None,
            "dominant_behaviors": behaviors,
            "recent_transactions": recent_txs[:10],
            "is_contract": bool(code and code != "0x"),
            "last_seen": recent_txs[0]["block_number"] if recent_txs else None,
            "fetch_error": "",
        }
    except Exception as exc:
        fallback["data_source"] = "fallback-simulated"
        fallback["rpc_url"] = rpc_url
        fallback["fetch_error"] = str(exc)
        return fallback


def build_etherscan_wallet_snapshot(address: str, api_key: str, chain_id: int | None = None) -> dict:
    selected_chain_id = str(chain_id or os.getenv("ETHERSCAN_CHAIN_ID", "1"))
    limit = int(os.getenv("ETHERSCAN_TX_LIMIT", "40"))
    api_url = os.getenv("ETHERSCAN_API_URL", "https://api.etherscan.io/v2/api")
    with ThreadPoolExecutor(max_workers=3) as executor:
        normal_future = executor.submit(_etherscan_account_action, api_url, api_key, selected_chain_id, "txlist", address, limit)
        internal_future = executor.submit(_etherscan_account_action, api_url, api_key, selected_chain_id, "txlistinternal", address, limit)
        token_future = executor.submit(_etherscan_account_action, api_url, api_key, selected_chain_id, "tokentx", address, limit)
        normal_txs = normal_future.result()
        internal_txs = internal_future.result()
        token_txs = token_future.result()
    return _summarize_indexed_transactions(address, selected_chain_id, normal_txs, internal_txs, token_txs, api_url)


def _etherscan_account_action(api_url: str, api_key: str, chain_id: str, action: str, address: str, limit: int) -> list[dict]:
    response = requests.get(
        api_url,
        params={
            "chainid": chain_id,
            "module": "account",
            "action": action,
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": limit,
            "sort": "desc",
            "apikey": api_key,
        },
        timeout=8,
    )
    response.raise_for_status()
    payload = response.json()
    result = payload.get("result")
    if isinstance(result, list):
        return result
    message = str(result or payload.get("message") or "")
    if "No transactions found" in message:
        return []
    raise RuntimeError(f"Etherscan {action} failed: {message}")


def _summarize_indexed_transactions(
    address: str,
    chain_id: str,
    normal_txs: list[dict],
    internal_txs: list[dict],
    token_txs: list[dict],
    api_url: str,
) -> dict:
    target = address.lower()
    incoming = []
    outgoing = []
    failed = []
    counterparties = set()
    recent = []
    total_value = 0.0
    token_symbols = set()
    first_ts = None
    last_ts = None

    for tx in normal_txs:
        tx_from = (tx.get("from") or "").lower()
        tx_to = (tx.get("to") or "").lower()
        is_outgoing = tx_from == target
        is_incoming = tx_to == target
        if not is_outgoing and not is_incoming:
            continue

        timestamp = int(tx.get("timeStamp") or 0)
        first_ts = timestamp if first_ts is None else min(first_ts, timestamp)
        last_ts = timestamp if last_ts is None else max(last_ts, timestamp)
        value_native = int(tx.get("value") or 0) / 10**18
        total_value += value_native
        errored = tx.get("isError") == "1" or tx.get("txreceipt_status") == "0"
        if errored:
            failed.append(tx)

        direction = "outgoing" if is_outgoing else "incoming"
        if is_outgoing:
            outgoing.append(tx)
            counterparty = tx_to
        else:
            incoming.append(tx)
            counterparty = tx_from
        if counterparty:
            counterparties.add(counterparty)

        recent.append(
            {
                "hash": tx.get("hash"),
                "block_number": int(tx.get("blockNumber") or 0),
                "timestamp": datetime.fromtimestamp(timestamp, timezone.utc).isoformat() if timestamp else None,
                "direction": direction,
                "counterparty": counterparty,
                "value_native": round(value_native, 8),
                "asset": "native",
                "transfer_type": "normal",
                "status": "failed" if errored else "success",
            }
        )

    for tx in internal_txs:
        _append_indexed_transfer(tx, target, "internal", incoming, outgoing, counterparties, recent, failed, token_symbols)

    for tx in token_txs:
        _append_indexed_transfer(tx, target, "erc20", incoming, outgoing, counterparties, recent, failed, token_symbols)

    behaviors = []
    if outgoing:
        behaviors.append("outgoing transfers")
    if incoming:
        behaviors.append("incoming transfers")
    if failed:
        behaviors.append("failed transactions")
    if token_txs:
        behaviors.append("ERC-20 token transfers")
    if internal_txs:
        behaviors.append("internal contract transfers")
    if any(item["value_native"] >= 1 for item in recent):
        behaviors.append("high-value transfers")
    if len(counterparties) >= 10:
        behaviors.append("broad counterparty activity")
    if not behaviors:
        behaviors.append("no indexed transaction activity returned")

    timestamps = [
        int(datetime.fromisoformat(item["timestamp"]).timestamp())
        for item in recent
        if item.get("timestamp")
    ]
    if timestamps:
        first_ts = min(timestamps)
        last_ts = max(timestamps)
        active_days = max(1, int((last_ts - first_ts) / 86400) + 1)
    else:
        active_days = 0

    return {
        "entity": address,
        "input_type": "wallet",
        "data_source": "etherscan-v2-indexer",
        "chain_id": int(chain_id),
        "indexer_api": api_url,
        "indexed_transaction_sample_size": len(normal_txs) + len(internal_txs) + len(token_txs),
        "normal_transaction_count": len(normal_txs),
        "internal_transaction_count": len(internal_txs),
        "erc20_transfer_count": len(token_txs),
        "transaction_count": len(normal_txs) + len(internal_txs) + len(token_txs),
        "active_days": active_days,
        "incoming_transfer_count": len(incoming),
        "outgoing_transfer_count": len(outgoing),
        "estimated_volume_eth": round(total_value, 8),
        "failed_transaction_ratio": round(len(failed) / len(normal_txs), 4) if normal_txs else 0,
        "dominant_behaviors": behaviors,
        "counterparty_count": len(counterparties),
        "high_value_transfer_count": sum(1 for tx in recent if tx["value_native"] >= 1),
        "token_symbols_seen": sorted(token_symbols)[:20],
        "last_seen": datetime.fromtimestamp(last_ts, timezone.utc).isoformat() if last_ts else None,
        "recent_transactions": sorted(recent, key=lambda item: item.get("timestamp") or "", reverse=True)[:15],
        "fetch_error": "",
    }


def _append_indexed_transfer(
    tx: dict,
    target: str,
    transfer_type: str,
    incoming: list,
    outgoing: list,
    counterparties: set,
    recent: list,
    failed: list,
    token_symbols: set,
) -> None:
    tx_from = (tx.get("from") or "").lower()
    tx_to = (tx.get("to") or "").lower()
    is_outgoing = tx_from == target
    is_incoming = tx_to == target
    if not is_outgoing and not is_incoming:
        return

    timestamp = int(tx.get("timeStamp") or 0)
    direction = "outgoing" if is_outgoing else "incoming"
    counterparty = tx_to if is_outgoing else tx_from
    if is_outgoing:
        outgoing.append(tx)
    else:
        incoming.append(tx)
    if counterparty:
        counterparties.add(counterparty)

    token_symbol = tx.get("tokenSymbol") or ("native" if transfer_type == "internal" else "")
    if token_symbol:
        token_symbols.add(token_symbol)
    decimals = int(tx.get("tokenDecimal") or 18)
    raw_value = int(tx.get("value") or 0)
    value_native = raw_value / 10**decimals if decimals >= 0 else 0
    errored = tx.get("isError") == "1" or tx.get("txreceipt_status") == "0"
    if errored:
        failed.append(tx)

    recent.append(
        {
            "hash": tx.get("hash"),
            "block_number": int(tx.get("blockNumber") or 0),
            "timestamp": datetime.fromtimestamp(timestamp, timezone.utc).isoformat() if timestamp else None,
            "direction": direction,
            "counterparty": counterparty,
            "value_native": round(value_native, 8) if transfer_type != "erc20" else 0,
            "token_amount": round(value_native, 8) if transfer_type == "erc20" else None,
            "asset": token_symbol or "native",
            "transfer_type": transfer_type,
            "status": "failed" if errored else "success",
        }
    )


def build_mock_wallet_snapshot(address: str, rng: random.Random, now: datetime) -> dict:
    tx_count = rng.randint(12, 240)
    active_days = rng.randint(3, 90)
    failed_ratio = round(rng.uniform(0.01, 0.22), 3)
    protocols = rng.sample(
        ["DEX swaps", "NFT minting", "staking", "bridging", "lending", "airdrops"],
        k=3,
    )
    volume = round(rng.uniform(0.8, 180.0), 2)
    return {
        "entity": address,
        "input_type": "wallet",
        "data_source": "fallback-simulated",
        "active_days": active_days,
        "transaction_count": tx_count,
        "estimated_volume_eth": volume,
        "failed_transaction_ratio": failed_ratio,
        "dominant_behaviors": protocols,
        "last_seen": (now - timedelta(days=rng.randint(0, 8))).isoformat(),
        "counterparty_count": rng.randint(4, 76),
        "high_value_transfer_count": rng.randint(0, 9),
    }


def _rpc(rpc_url: str, method: str, params: list) -> str:
    response = requests.post(
        rpc_url,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        timeout=6,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("error"):
        raise RuntimeError(payload["error"].get("message", payload["error"]))
    return payload["result"]


def _scan_recent_wallet_transactions(rpc_url: str, address: str, latest_block: int, scan_blocks: int, scan_seconds: float) -> list[dict]:
    target = address.lower()
    recent_txs = []
    start_block = max(0, latest_block - scan_blocks + 1)
    deadline = time.monotonic() + scan_seconds

    for block_number in range(latest_block, start_block - 1, -1):
        if time.monotonic() > deadline:
            break
        block = _rpc(rpc_url, "eth_getBlockByNumber", [hex(block_number), True])
        if not block:
            continue
        for tx in block.get("transactions", []):
            tx_from = (tx.get("from") or "").lower()
            tx_to = (tx.get("to") or "").lower()
            if tx_from != target and tx_to != target:
                continue
            value_native = int(tx.get("value", "0x0"), 16) / 10**18
            direction = "outgoing" if tx_from == target else "incoming"
            counterparty = tx_to if direction == "outgoing" else tx_from
            recent_txs.append(
                {
                    "hash": tx.get("hash"),
                    "block_number": int(tx.get("blockNumber", "0x0"), 16),
                    "direction": direction,
                    "counterparty": counterparty,
                    "value_native": round(value_native, 8),
                }
            )

    return recent_txs


def build_website_snapshot(url: str) -> dict:
    started_at = datetime.now(timezone.utc)
    parsed = urlparse(url)
    snapshot = {
        "entity": url,
        "input_type": "website",
        "domain": parsed.netloc,
        "fetched_at": started_at.isoformat(),
        "status_code": None,
        "final_url": url,
        "title": "",
        "description": "",
        "headings": [],
        "external_link_count": 0,
        "has_https": parsed.scheme == "https",
        "security_headers": {},
        "fetch_error": "",
    }

    try:
        response = requests.get(
            url,
            timeout=12,
            headers={
                "User-Agent": "AgentVaultAI/0.1 website intelligence scanner",
                "Accept": "text/html,application/xhtml+xml",
            },
            allow_redirects=True,
        )
        snapshot["status_code"] = response.status_code
        snapshot["final_url"] = response.url
        snapshot["security_headers"] = {
            key: response.headers.get(key, "")
            for key in [
                "content-security-policy",
                "strict-transport-security",
                "x-frame-options",
                "x-content-type-options",
            ]
            if response.headers.get(key)
        }
        parser = WebsiteHTMLParser()
        parser.feed(response.text[:300_000])
        snapshot.update(
            {
                "title": parser.title[:180],
                "description": parser.description[:300],
                "headings": parser.headings[:8],
                "external_link_count": parser.external_link_count,
            }
        )
    except Exception as exc:
        snapshot["fetch_error"] = str(exc)

    return snapshot


class WebsiteHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.description = ""
        self.headings = []
        self.external_link_count = 0
        self._capture = ""
        self._buffer = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        if tag == "title":
            self._capture = "title"
            self._buffer = []
        elif tag in {"h1", "h2"}:
            self._capture = tag
            self._buffer = []
        elif tag == "meta" and attrs_dict.get("name", "").lower() == "description":
            self.description = attrs_dict.get("content", "").strip()
        elif tag == "a" and attrs_dict.get("href", "").startswith(("http://", "https://")):
            self.external_link_count += 1

    def handle_endtag(self, tag):
        if self._capture == tag:
            text = " ".join("".join(self._buffer).split())
            if tag == "title":
                self.title = text
            elif text:
                self.headings.append(text[:180])
            self._capture = ""
            self._buffer = []

    def handle_data(self, data):
        if self._capture:
            self._buffer.append(data)
