"""Prepare the ignored local token and extension configuration."""

import argparse
import secrets
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    token_path = data_dir / "server-token.txt"
    token = token_path.read_text(encoding="utf-8").strip() if token_path.exists() else ""
    if len(token) < 32 or any(character.isspace() for character in token):
        token = secrets.token_urlsafe(32)
        token_path.write_text(token + "\n", encoding="utf-8")

    config = (
        "// Generated locally. Do not commit this file.\n"
        'globalThis.INSTAGRAM_EXPORTER_API_BASE = "http://127.0.0.1:8765";\n'
        f'globalThis.INSTAGRAM_EXPORTER_TOKEN = "{token}";\n'
    )
    Path(args.config).write_text(config, encoding="utf-8")


if __name__ == "__main__":
    main()
