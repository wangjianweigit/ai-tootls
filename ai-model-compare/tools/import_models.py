from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import sys
import urllib.request
import urllib.error


def _post_multipart(url: str, data: Dict[str, str]) -> Dict[str, Any]:
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body_lines: List[bytes] = []
    for k, v in data.items():
        body_lines.append(f"--{boundary}\r\n".encode())
        body_lines.append(
            f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode()
        )
        body_lines.append((v if isinstance(v, str) else str(v)).encode())
        body_lines.append(b"\r\n")
    body_lines.append(f"--{boundary}--\r\n".encode())
    body = b"".join(body_lines)

    req = urllib.request.Request(url, method="POST")
    req.add_header(
        "Content-Type", f"multipart/form-data; boundary={boundary}"
    )
    req.data = body
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {e.code}: {detail}") from e


def import_models(api_base: str, input_file: Path, override_enabled: bool | None = None) -> int:
    with input_file.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    items: List[Dict[str, Any]] = payload.get("items", [])
    if not items:
        print("No models to import.")
        return 0

    created = 0
    for m in items:
        data = {
            "provider": str(m.get("provider", "")).strip(),
            "label": str(m.get("label", "")),
            "base_url": str(m.get("base_url", "")).strip(),
            "api_key": str(m.get("api_key", "")).strip(),
            "model": str(m.get("model", "")).strip(),
            "enabled": (
                "1" if (override_enabled if override_enabled is not None else bool(m.get("enabled", 1))) else "0"
            ),
        }
        url = api_base.rstrip("/") + "/models"
        _post_multipart(url, data)
        created += 1
    print(f"Imported {created} models into {api_base}")
    return created


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Import models JSON via API")
    parser.add_argument("api_base", help="Remote API base, e.g. http://host:8000")
    parser.add_argument(
        "--in",
        dest="input_file",
        type=Path,
        default=Path("models-export.json"),
        help="Input JSON file path",
    )
    parser.add_argument(
        "--enable-all",
        action="store_true",
        help="Force enable imported models",
    )
    args = parser.parse_args()
    try:
        import_models(args.api_base, args.input_file, True if args.enable_all else None)
    except Exception as e:
        print("Import failed:", e, file=sys.stderr)
        sys.exit(1)


