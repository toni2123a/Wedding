"""Lokale Bedienung. Greift ausschließlich auf das Compose-Projekt wedding_local zu."""

import argparse
import os
import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECRET_DIR = ROOT / "secrets" / "local"
ACCOUNTS = [
    ("mara@demo.invalid", "Brautpaar in Hochzeit A"),
    ("lea@demo.invalid", "Brautpaar in Hochzeit B"),
    ("sam@demo.invalid", "Mitplaner in A und Trauzeuge in B"),
    ("toni@demo.invalid", "Trauzeuge in Hochzeit A"),
    ("gast@demo.invalid", "Gast in A ohne interne Aufgabenrechte"),
    ("anbieter@demo.invalid", "Dienstleister in A ohne interne Aufgabenrechte"),
    ("ohne-zugang@demo.invalid", "Konto ohne Hochzeitsfreigabe"),
]


def setup():
    SECRET_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(SECRET_DIR, 0o700)
    for name in [
        "django_secret_key",
        "db_admin_password",
        "db_migrator_password",
        "db_app_password",
        "demo_password",
    ]:
        path = SECRET_DIR / name
        if not path.exists():
            path.write_text(secrets.token_urlsafe(64) + "\n", encoding="utf-8", newline="\n")
        # Linux-Compose bindet Dateien mit ihren Hostrechten ein. Das private
        # Elternverzeichnis schützt sie auf dem Host; nur zugewiesene Mounts
        # geben unprivilegierten Containerprozessen eine lesbare Datei.
        os.chmod(path, 0o600 if os.name == "nt" else 0o444)
    env = ROOT / ".env"
    if not env.exists():
        env.write_text((ROOT / ".env.example").read_text(encoding="utf-8"), encoding="utf-8")
    password = (SECRET_DIR / "demo_password").read_text(encoding="utf-8").strip()
    lines = ["Nur künstliche lokale Testkonten", "", "Adresse: http://localhost:18080", ""]
    for email, role in ACCOUNTS:
        lines.extend([f"{email} | {role}", f"Passwort: {password}", ""])
    account_file = SECRET_DIR / "demo-accounts.txt"
    account_file.write_text("\n".join(lines), encoding="utf-8")
    os.chmod(account_file, 0o600)
    print("Lokale Konfiguration und getrennte Zufallsgeheimnisse sind vorbereitet.")
    print("Testzugänge stehen in secrets/local/demo-accounts.txt.")


def compose(*args):
    command = [
        "docker",
        "compose",
        "--project-name",
        "wedding_local",
        "--env-file",
        str(ROOT / ".env"),
        "--file",
        str(ROOT / "docker" / "compose.local.yml"),
        *args,
    ]
    subprocess.run(command, cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=["setup", "up", "build", "test", "check", "down", "status", "logs"]
    )
    action = parser.parse_args().action
    if action == "setup":
        setup()
        return
    if not (ROOT / ".env").exists():
        parser.error("Zuerst python scripts/dev.py setup ausführen.")
    if action == "build":
        compose("build", "web", "tools")
    elif action == "up":
        compose("up", "--detach", "db")
        compose("run", "--rm", "migrate")
        compose("run", "--rm", "seed")
        compose("up", "--detach", "--wait", "--wait-timeout", "60", "web")
        print("Die lokale Anwendung ist unter http://localhost:18080 erreichbar.")
    elif action == "test":
        compose("up", "--detach", "db")
        compose("run", "--rm", "tools")
    elif action == "check":
        compose("run", "--rm", "web", "python", "manage.py", "check_isolation")
        compose("run", "--rm", "web", "python", "manage.py", "check")
    elif action == "down":
        compose("down")
    elif action == "status":
        compose("ps")
    elif action == "logs":
        compose("logs", "--tail", "60", "web")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        sys.exit(error.returncode)
