"""Prüft gesperrte Laufzeitpakete gegen die veröffentlichten PyPI-Sicherheitsmeldungen."""

import json
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_release(package):
    name, version = package
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=15) as response:  # noqa: S310
            data = json.load(response)
    except (OSError, ValueError, urllib.error.URLError):
        return f"{name} {version}: Die Sicherheitsprüfung war nicht erreichbar."
    vulnerabilities = [
        item for item in data.get("vulnerabilities", []) if not item.get("withdrawn")
    ]
    if vulnerabilities:
        identifiers = ", ".join(item["id"] for item in vulnerabilities)
        return f"{name} {version}: Sicherheitsmeldung {identifiers}"
    return None


def main():
    contents = (ROOT / "requirements.lock").read_text(encoding="utf-8")
    packages = re.findall(r"^([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+!-]+)", contents, re.MULTILINE)
    if not packages:
        raise SystemExit("Die gesperrten Laufzeitabhängigkeiten fehlen.")
    with ThreadPoolExecutor(max_workers=4) as executor:
        errors = [result for result in executor.map(check_release, packages) if result]
    for error in errors:
        print(error)
    if errors:
        return 1
    print(
        f"PyPI meldet für die {len(packages)} gesperrten Laufzeitpakete keine Sicherheitswarnung."
    )
    print("Diese Abfrage ersetzt keinen vollständigen Sicherheitsreview oder Container-Scan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
