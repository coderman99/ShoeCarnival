"""Fetch datasets used to project sales and margins."""
from __future__ import annotations

import argparse
import os
import pathlib
from typing import Any, Dict

import requests
import yaml


def resolve_env(value: str) -> str:
    """Replace ${VARNAME} tokens with environment values."""
    if "${" not in value:
        return value
    resolved = value
    for part in value.split("${"):
        if "}" not in part:
            continue
        name, remainder = part.split("}", 1)
        env_val = os.getenv(name, "").strip()
        resolved = resolved.replace(f"${{{name}}}", env_val)
    return resolved


def load_sources(config_path: pathlib.Path) -> Dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    sources: Dict[str, Any] = {}
    for name, config in raw.items():
        entry = dict(config)
        source = entry.get("source", {})
        if "url" in source and isinstance(source["url"], str):
            source["url"] = resolve_env(source["url"])
        entry["source"] = source
        sources[name] = entry
    return sources


def ensure_directory(path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def download_http(session: requests.Session, url: str, dest: pathlib.Path, params: Dict[str, Any] | None,
                  headers: Dict[str, str] | None) -> None:
    response = session.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    ensure_directory(dest)
    dest.write_bytes(response.content)


def copy_fallback(fallback_path: pathlib.Path, dest: pathlib.Path) -> None:
    if not fallback_path.exists():
        raise FileNotFoundError(f"Fallback path not found: {fallback_path}")
    ensure_directory(dest)
    dest.write_bytes(fallback_path.read_bytes())


def sync_source(name: str, details: Dict[str, Any], force: bool, session: requests.Session) -> None:
    output = pathlib.Path(details["output"])
    source = details.get("source", {})
    source_type = source.get("type", "http")
    url = source.get("url", "")
    fallback_local = source.get("fallback_local")

    if output.exists() and not force:
        print(f"[skip] {name}: {output} already exists")
        return

    if source_type == "http" and url:
        print(f"[http] Fetching {name} from {url}")
        download_http(session, url, output, source.get("params"), source.get("headers"))
        print(f"[done] Saved {output}")
        return

    if fallback_local:
        fallback_path = pathlib.Path(fallback_local)
        print(f"[fallback] Copying {fallback_path} -> {output}")
        copy_fallback(fallback_path, output)
        print(f"[done] Saved {output} from fallback")
        return

    raise ValueError(f"No valid source defined for {name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch datasets for sales and margin projections.")
    parser.add_argument("--config", default="config/data_sources.yml", help="Path to the data source configuration file.")
    parser.add_argument("--source", action="append", dest="sources", help="Limit fetch to specific source names.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = pathlib.Path(args.config)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    sources = load_sources(config_path)
    requested = set(args.sources) if args.sources else set(sources.keys())

    with requests.Session() as session:
        for name, details in sources.items():
            if name not in requested:
                continue
            try:
                sync_source(name, details, args.force, session)
            except Exception as exc:  # noqa: BLE001
                print(f"[error] {name}: {exc}")


if __name__ == "__main__":
    main()
