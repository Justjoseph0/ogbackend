import json
import os
from typing import Any

import requests


REPORT_KEYS = {
    "summary": "",
    "risk_level": "medium",
    "key_behaviors": [],
    "insights": [],
    "recommendation": "",
}


def generate_report(query: str, raw_data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    prompt = _build_prompt(query, raw_data)
    errors = []
    for provider_name, provider in [
        ("generic-openai-compatible", _call_generic_openai_compatible),
        ("deepseek", _call_deepseek),
        ("openai", _call_openai),
    ]:
        api_report, error = _safe_call(provider, prompt)
        if error:
            errors.append(f"{provider_name}: {error}")
        if api_report:
            return normalize_report(api_report), {
                "ai_provider": provider_name,
                "ai_model": _provider_model(provider_name),
                "ai_status": "live",
            }
    return _fallback_report(query, raw_data), {
        "ai_provider": "fallback",
        "ai_model": "local-rules",
        "ai_status": "fallback",
        "ai_error": " | ".join(errors) if errors else "No configured AI provider responded.",
    }


def _safe_call(provider, prompt: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return provider(prompt), None
    except Exception as exc:
        return None, _format_error(exc)


def _format_error(exc: Exception) -> str:
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        body = exc.response.text[:500].replace(os.getenv("DEEPSEEK_API_KEY", ""), "<redacted>")
        return f"HTTP {exc.response.status_code}: {body}"
    return str(exc)[:500]


def _provider_model(provider_name: str) -> str:
    if provider_name == "generic-openai-compatible":
        return os.getenv("AI_MODEL", "")
    if provider_name == "deepseek":
        return os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    if provider_name == "openai":
        return os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return ""


def _build_prompt(query: str, raw_data: dict[str, Any]) -> str:
    subject_type = raw_data.get("input_type", "web3 subject")
    return (
        "You are AgentVault AI, a Web3 intelligence analyst. Convert the raw data into strict JSON "
        "with keys: summary, risk_level, key_behaviors, insights, recommendation. "
        "If data_source is real-json-rpc, base the wallet analysis on the real RPC fields and say when recent scanned "
        "blocks do not show transfers. Do not invent transactions that are not present in raw_data. "
        "risk_level must be one of low, medium, high. If the subject is a website, analyze credibility, security posture, "
        "clarity of product messaging, and any obvious Web3 risk signals from the fetched page data. "
        "Do not include markdown.\n\n"
        f"Subject type: {subject_type}\nSubject: {query}\nRaw data:\n{json.dumps(raw_data, indent=2)}"
    )


def _call_deepseek(prompt: str) -> dict[str, Any] | None:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return None
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    response = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        },
        timeout=30,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return _parse_json_content(content)


def _call_openai(prompt: str) -> dict[str, Any] | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    response = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        },
        timeout=30,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return _parse_json_content(content)


def _call_generic_openai_compatible(prompt: str) -> dict[str, Any] | None:
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "").rstrip("/")
    model = os.getenv("AI_MODEL", "")
    if not api_key or not base_url or not model:
        return None
    response = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        },
        timeout=30,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return _parse_json_content(content)


def _parse_json_content(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def normalize_report(report: dict[str, Any]) -> dict[str, Any]:
    normalized = {**REPORT_KEYS, **report}
    risk = str(normalized.get("risk_level", "medium")).lower()
    normalized["risk_level"] = risk if risk in {"low", "medium", "high"} else "medium"
    for key in ["key_behaviors", "insights"]:
        value = normalized.get(key)
        normalized[key] = value if isinstance(value, list) else [str(value)]
    normalized["summary"] = str(normalized.get("summary", ""))
    normalized["recommendation"] = str(normalized.get("recommendation", ""))
    return normalized


def _fallback_report(query: str, raw_data: dict[str, Any]) -> dict[str, Any]:
    if raw_data["input_type"] == "website":
        missing_security = 4 - len(raw_data.get("security_headers", {}))
        has_error = bool(raw_data.get("fetch_error"))
        risk = "high" if has_error or missing_security >= 3 else "medium" if missing_security else "low"
        title = raw_data.get("title") or raw_data.get("domain") or query
        return {
            "summary": f"{title} was scanned from the live website URL and evaluated using visible page metadata and basic security headers.",
            "risk_level": risk,
            "key_behaviors": [
                "website metadata scan",
                "security header review",
                "project messaging extraction",
                "external link surface check",
            ],
            "insights": [
                f"HTTP status: {raw_data.get('status_code') or 'unavailable'}; final URL: {raw_data.get('final_url')}.",
                f"Detected title: {raw_data.get('title') or 'not found'}.",
                f"Security headers found: {', '.join(raw_data.get('security_headers', {}).keys()) or 'none detected'}.",
                f"Top headings: {', '.join(raw_data.get('headings', [])[:3]) or 'none detected'}.",
            ],
            "recommendation": "Verify the team, contracts, documentation, and social channels before trusting claims made on the website.",
        }

    if raw_data["input_type"] == "wallet":
        if raw_data.get("data_source") == "real-json-rpc":
            recent_count = raw_data.get("recent_transfer_count", 0)
            high_value = raw_data.get("high_value_transfer_count", 0)
            is_contract = raw_data.get("is_contract", False)
            risk = "high" if high_value > 3 or is_contract else "medium" if recent_count == 0 else "low"
            return {
                "summary": (
                    f"{query} was analyzed from live JSON-RPC data on chain {raw_data.get('chain_id')}. "
                    f"The wallet has nonce {raw_data.get('transaction_count')} and a native balance of "
                    f"{raw_data.get('balance_native')}."
                ),
                "risk_level": risk,
                "key_behaviors": raw_data.get("dominant_behaviors", []),
                "insights": [
                    f"Scanned {raw_data.get('scanned_block_count')} recent blocks up to block {raw_data.get('latest_scanned_block')}.",
                    f"Found {recent_count} matching recent transfers with {raw_data.get('counterparty_count')} counterparties.",
                    f"Recent incoming/outgoing split: {raw_data.get('incoming_transfer_count')} incoming, {raw_data.get('outgoing_transfer_count')} outgoing.",
                    f"Contract account: {'yes' if is_contract else 'no'}.",
                ],
                "recommendation": "Use a broader indexer scan before making final risk decisions, especially if recent scanned blocks show limited activity.",
            }

        if raw_data.get("data_source") == "etherscan-v2-indexer":
            failed = raw_data["failed_transaction_ratio"]
            high_value = raw_data["high_value_transfer_count"]
            risk = "high" if failed > 0.12 or high_value > 5 else "medium" if failed > 0.04 or high_value else "low"
            return {
                "summary": (
                    f"{query} was analyzed from indexed chain history on chain {raw_data.get('chain_id')}. "
                    f"The sample includes {raw_data.get('transaction_count')} recent transactions across "
                    f"{raw_data.get('active_days')} active days."
                ),
                "risk_level": risk,
                "key_behaviors": raw_data.get("dominant_behaviors", []),
                "insights": [
                    f"Incoming/outgoing split: {raw_data.get('incoming_transfer_count')} incoming, {raw_data.get('outgoing_transfer_count')} outgoing.",
                    f"Estimated native transfer volume in sample: {raw_data.get('estimated_volume_eth')}.",
                    f"Failed transaction ratio: {failed}.",
                    f"Unique counterparties in sample: {raw_data.get('counterparty_count')}.",
                ],
                "recommendation": "Review recent counterparties and failed transactions before approving high-value interactions.",
            }

        failed = raw_data["failed_transaction_ratio"]
        high_value = raw_data["high_value_transfer_count"]
        risk = "high" if failed > 0.16 or high_value > 6 else "medium" if failed > 0.08 else "low"
        return {
            "summary": f"{query} shows {raw_data['transaction_count']} observed transactions across {raw_data['active_days']} active days.",
            "risk_level": risk,
            "key_behaviors": raw_data["dominant_behaviors"],
            "insights": [
                f"Estimated movement volume is {raw_data['estimated_volume_eth']} ETH.",
                f"Failed transaction ratio is {failed}, indicating {'elevated execution friction' if failed > 0.1 else 'normal execution quality'}.",
                f"Interacted with {raw_data['counterparty_count']} counterparties.",
            ],
            "recommendation": "Monitor high-value transfers and new counterparties before approving large interactions.",
        }

    flags = raw_data["contract_risk_flags"]
    risk = "high" if flags >= 3 else "medium" if flags else "low"
    return {
        "summary": f"{query} has measurable activity across community, liquidity, and developer signals.",
        "risk_level": risk,
        "key_behaviors": raw_data["tracked_signals"],
        "insights": [
            f"Community score is {raw_data['community_score']} and liquidity score is {raw_data['liquidity_score']}.",
            f"{flags} contract risk flags were detected in the simulated scan.",
            f"Recent mention count is {raw_data['recent_mentions']}.",
        ],
        "recommendation": "Validate contract ownership, liquidity depth, and public roadmap before committing capital.",
    }
