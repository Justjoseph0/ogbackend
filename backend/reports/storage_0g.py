import json
import os
import tempfile
from pathlib import Path
from typing import Any


def upload_report_to_0g(payload: dict[str, Any]) -> dict[str, str]:
    private_key = os.getenv("OG_PRIVATE_KEY", "").strip()
    if not private_key:
        return _local_demo_storage(payload)

    try:
        from eth_account import Account
        from core import Indexer, ZgFile
    except Exception as exc:
        raise RuntimeError(
            f"0G Storage SDK import failed: {exc}. "
            "Upgrade the SDK with: python -m pip install --upgrade -r requirements.txt"
        ) from exc

    blockchain_rpc = os.getenv("OG_BLOCKCHAIN_RPC", "https://evmrpc-testnet.0g.ai")
    indexer_rpc = os.getenv("OG_INDEXER_RPC", "https://indexer-storage-testnet-turbo.0g.ai")
    explorer_tpl = os.getenv("OG_EXPLORER_TX_URL", "https://chainscan-galileo.0g.ai/tx/{tx_hash}")
    account = Account.from_key(private_key)

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        json.dump(payload, tmp, separators=(",", ":"))
        tmp_path = tmp.name

    zg_file = None
    try:
        indexer = Indexer(indexer_rpc)
        zg_file = ZgFile.from_file_path(tmp_path)
        result, err = indexer.upload(
            zg_file,
            blockchain_rpc,
            account,
            {
                "tags": b"AgentVault AI",
                "finalityRequired": True,
                "taskSize": 10,
                "expectedReplica": 1,
                "skipTx": False,
                "account": account,
            },
        )
        tx_hash = result.get("txHash", "")
        root_hash = result.get("rootHash", "")
        if err is not None and not (tx_hash and root_hash):
            raise RuntimeError(str(err))
        return {
            "root_hash": root_hash,
            "tx_hash": tx_hash,
            "explorer_url": explorer_tpl.format(tx_hash=tx_hash),
            "storage_status": "stored-on-0g" if err is None else "stored-on-0g-pending",
        }
    finally:
        if zg_file is not None:
            zg_file.close()
        Path(tmp_path).unlink(missing_ok=True)


def retrieve_report_from_0g(root_hash: str) -> dict[str, Any] | None:
    if not root_hash or root_hash.startswith("local-demo-"):
        return None
    try:
        from core import Indexer
    except Exception:
        return None

    indexer_rpc = os.getenv("OG_INDEXER_RPC", "https://indexer-storage-testnet-turbo.0g.ai")
    with tempfile.NamedTemporaryFile("r", suffix=".json", delete=False, encoding="utf-8") as tmp:
        tmp_path = tmp.name
    try:
        err = Indexer(indexer_rpc).download(root_hash, tmp_path, proof=False)
        if err is not None:
            return None
        with open(tmp_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _local_demo_storage(payload: dict[str, Any]) -> dict[str, str]:
    import hashlib

    content = json.dumps(payload, sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(content).hexdigest()
    return {
        "root_hash": f"local-demo-{digest}",
        "tx_hash": "",
        "explorer_url": "",
        "storage_status": "local-demo",
    }
