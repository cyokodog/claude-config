#!/usr/bin/env python3
"""Resolve browser tooling/workflow; does not open a browser or execute a skill."""
import argparse
import json
from pathlib import Path


def resolve(client, purpose, config=None):
    if config is None:
        config = json.loads(Path(__file__).with_name("routes.json").read_text())
    if config.get("version") != 1:
        raise ValueError("Unsupported browser routes version")
    try:
        route = config["clients"][client][purpose]
    except KeyError:
        raise ValueError("Unknown client or purpose; no automatic fallback") from None
    provider = route.get("provider")
    if provider not in {"claude-in-chrome", "playwright-mcp"}:
        raise ValueError("Unsupported browser provider")
    result = {"client": client, "purpose": purpose, **route}
    if purpose in {"e2e", "spa-e2e"} and not isinstance(result.get("skill"), str):
        raise ValueError("Workflow route requires a skill")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", required=True, choices=["claude", "codex"])
    parser.add_argument("--purpose", default="browser", choices=["browser", "research", "e2e", "spa-e2e"])
    args = parser.parse_args()
    try:
        print(json.dumps(resolve(args.client, args.purpose), ensure_ascii=False))
    except (OSError, ValueError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()
