# TODO und Übergabe für die Serverarbeit

Stand: 23.10.2026. Diese Datei ist der Einstieg für die nächste Arbeitssitzung auf dem VPS. Sie ergänzt [README.md](README.md), [ARCHITEKTURPLAN.md](ARCHITEKTURPLAN.md) und [docs/ENTWICKLUNGSSTAND.md](docs/ENTWICKLUNGSSTAND.md).

## Projekt und Zielumgebung

| Punkt | Stand |
|---|---|
| Produktname im Entwurf | Gemeinsam geplant |
| Repository | `https://github.com/toni2123a/Wedding.git` |
| Zielbranch | `main` |
| Lokales Projekt | `F:\Wedding` |
| Lokale Adresse | `http://localhost:18080` |
| VPS | Hetzner CX33 mit Debian 12 |
| IPv4 | `204.168.172.129` |
| Bestehende Hauptseite | `tsdigitalsolution.de` |
| Vorgeschlagene Subdomain | `hochzeit.tsdigitalsolution.de`, noch nicht eingerichtet |
| Serverzugang und Projektpfad | Noch nicht aufgenommen |

Die Hauptseite läuft bereits auf diesem Server. Der aktuelle Compose-Stack ist ausschließlich für lokale Entwicklung mit künstlichen Daten eingerichtet. Es gibt noch keine produktive Serverkonfiguration. Er darf nicht unverändert als öffentliche Kundenanwendung gestartet werden.

## Bereits umgesetzt

- [x] Architekturplan aus der Blueprint einschließlich Zuordnung aller 44 nummerierten Anforderungen.
- [x] Eigenes lokales Docker-Projekt mit PostgreSQL 18 und Django 5.2 LTS unter Python 3.13.
- [x] Getrennte Laufzeit-, Migrations- und PostgreSQL-Administrationszugänge.
- [x] Erzwungene PostgreSQL-RLS für Hochzeiten, Mitgliedschaften, Aufgaben und Audit-Einträge.
- [x] Anmeldung, Abmeldung, Argon2, CSRF-Schutz, Anmeldelimits und begrenzte Sitzungen.
- [x] Zwei künstliche Hochzeiten mit mehreren Rollen für Berechtigungsprüfungen.
- [x] Geschützte Hochzeitsübersicht und Aufgaben mit Zuständigkeit, Termin, Status und Versionsprüfung.
- [x] Transaktionale Aufgabenänderungen mit Audit-Eintrag.
- [x] Öffentliche Produkt-Landingpage unter `/`, ohne Abfrage privater Hochzeitsinhalte.
- [x] Geschützter Planungsbereich unter `/planung/`; Anmeldung unter `/anmelden/`.
- [x] Produktvorschau mit festen Beispieldaten; spätere Funktionen sind als geplant gekennzeichnet.
- [x] Reproduzierbare Python-Locks mit Paketprüfsummen und festgelegte Containerbasis-Digests.
- [x] Sicherheits- und Funktionstests, HTTP-Smoke-Test und PyPI-Abfrage bekannter Paketmeldungen vorbereitet.
- [x] GitHub-Workflow für dieselben Prüfungen mit ausschließlich künstlichen Daten vorbereitet.
- [x] Geheimnisse und Laufzeitdaten von Git und Docker-Builds ausgeschlossen.

Die lokalen Prüfungen sind unten dokumentiert. Eine automatische visuelle Browserprüfung ist in der aktuellen Sitzung mangels Browseranbindung nicht möglich.

## Als Erstes auf dem Server

### 1. Bestand aufnehmen

- [ ] Administrativen SSH-Zugang und tatsächlich vorgesehenes Projektverzeichnis festhalten. Keine Zugangsdaten in diese Datei schreiben.
- [ ] Repository klonen beziehungsweise den freigegebenen Stand abrufen und zuerst diese TODO, README und Architektur lesen.
- [ ] Vorhandenen Hauptseiten-Stack und seinen Reverse Proxy identifizieren.
- [ ] Belegte Ports, vorhandene Docker-Netze und bereits verwendete Volume- und Projektnamen aufnehmen.
- [ ] RAM, CPU, freien Speicher, bestehende Sicherungen und Serverregion prüfen.
- [ ] Die Hauptseite vor Änderungen über HTTPS einschließlich ihrer relevanten Funktionen prüfen.

Geeignete erste Befehle sind ausschließlich lesend:

```sh
cat /etc/os-release
docker version
docker compose version
docker ps --format 'table {{.Names}}\t{{.Ports}}'
ss -lntup
free -h
df -hT
systemctl --no-pager --type=service --state=running
```

Keine vollständigen Container-Umgebungen oder Geheimnisdateien in Chatprotokolle kopieren. Ein allgemeines Zurücksetzen der Firewall, des Proxys oder des Docker-Daemons gehört nicht zur Bestandsaufnahme.

### 2. Deploymentziel festlegen

- [ ] Endgültigen Subdomainnamen bestätigen und vorhandenen DNS-Stand prüfen.
- [ ] Festlegen, ob zunächst nur die Produktseite öffentlich erreichbar wird. Der unfertige Planungsbereich bleibt bis zur Sicherheitsabnahme gesperrt oder auf den administrativen Zugang begrenzt.
- [ ] Verzeichnis für Quellcode beziehungsweise Releases getrennt von Produktionsdaten und Geheimnissen festlegen.
- [ ] Ressourcenbudget anhand der tatsächlichen Hauptseitenlast prüfen. Scanner und Medienverarbeitung nicht ungeprüft zusätzlich starten.
- [ ] Verschlüsselte Datenablage und unabhängiges Backupziel festlegen. Das im Architekturplan vorgeschlagene zusätzliche Volume ist noch nicht bestellt.

### 3. Produktionskonfiguration erstellen

- [ ] Eigene Produktionseinstellungen anlegen. `APP_ENV=local`, lokale Testkonten und der lokale Stack sind keine Produktionseinstellungen.
- [ ] Eigenes produktives Compose-Projekt mit festgelegten Images, Healthchecks, Ressourcenlimits und geschützten Datenpfaden anlegen.
- [ ] Neue Produktionsgeheimnisse auf dem Server erzeugen und getrennt verwahren. Lokale Geheimnisse oder Testkonten nicht übernehmen.
- [ ] PostgreSQL-Laufzeitkonto auf die bestehenden Minimalrechte begrenzen. Produktions-Migrationszugang ohne das nur lokal benötigte `CREATEDB`-Recht anlegen.
- [ ] Nicht öffentliche Dienste ohne veröffentlichte Hostports betreiben. Docker-, Host- und Hetzner-Firewall einschließlich IPv6 zusammen prüfen.
- [ ] Gültige Hosts, vertrauenswürdige Proxyheader, CSRF-Origin, Secure-Cookies und HTTPS-Einstellungen konkret festlegen.
- [ ] Impressum, Datenschutzhinweise, Betreiberangaben und tatsächliche Produktverfügbarkeit vor Veröffentlichung ausarbeiten.
- [ ] Für einen reinen Landingpage-Start die Freigabe des unfertigen Anmelde- und Planungsbereichs technisch verhindern.

### 4. Vorhandenen Proxy anschließen

- [ ] Bestehende Konfiguration und Wiederherstellungsweg sichern.
- [ ] Nur einen zusätzlichen Hosteintrag für die Hochzeits-Subdomain ergänzen.
- [ ] Bei einem Hostproxy ausschließlich zur Loopback-Adresse des Hochzeit-Webdienstes weiterleiten.
- [ ] Bei einem Proxycontainer ausschließlich den Webdienst an das dafür vorgesehene Ingress-Netz anschließen.
- [ ] Keine zweite Belegung der öffentlichen Ports 80 und 443 einrichten.
- [ ] Zertifikat über die vorhandene TLS-Verwaltung einrichten und HTTPS prüfen.
- [ ] Hauptseite und neue Subdomain getrennt testen. Hochzeitserweiterung bei Fehlern unabhängig zurücksetzen können.

### 5. Deployment und Betrieb prüfen

- [ ] GitHub-CI nach dem Push ausführen und Ergebnis prüfen.
- [ ] Image-Build, Registry, konkreten Image-Digest und Freigabeverfahren einrichten. GitHub erhält keine Produktions-Entschlüsselungs- oder Datenbankzugänge.
- [ ] Vor einem Release Sicherung, Deployment-Lock und kompatible Migrationen prüfen.
- [ ] App-Rollback auf einen vorherigen Digest praktisch testen. Datenbank nicht automatisch auf einen alten Stand zurückschreiben.
- [ ] Alarmierung für Erreichbarkeit, Speicher, Containerfehler, Sicherungen und fehlgeschlagene Aufträge einrichten.
- [ ] Entsperrung einer verschlüsselten Ablage und Wiederanlauf nach einem Hostneustart proben.

## Vor echten Kundendaten

- [ ] MFA für Paarkonten und Plattformadministration einschließlich sicherer Wiederherstellung.
- [ ] Kontowiederherstellung, E-Mail-Verifikation und Missbrauchsgrenzen.
- [ ] Verwaltung von Mitgliedschaften und Freigaben mit Versions- und Auditprüfung.
- [ ] Verarbeitungszwecke, Rechtsgrundlagen, notwendige Verträge und Aufbewahrungsfristen festlegen.
- [ ] Verschlüsselung der persistenten Datenablage und getrennte Sicherung ihrer Schlüssel.
- [ ] Export, endgültige Löschung und Berücksichtigung gelöschter Daten bei Wiederherstellungen.
- [ ] Unabhängige verschlüsselte Backups und vollständigen Restore-Test durchführen.
- [ ] Rollen-, Mandanten- und Dateizugriffe unabhängig prüfen lassen.
- [ ] Mobile Ansicht, Tastaturbedienung und Kontraste mit einem echten Browser prüfen.
- [ ] Registrierung und Preise erst nach tatsächlicher Umsetzung und Festlegung bewerben.

## Anschließende Fachentwicklung

Die Details und Abnahmen stehen in der Blueprint. Die Landingpage ist kein Nachweis, dass diese Module bereits implementiert sind.

- [ ] Gäste, Familien und RSVP, Kontakte, Orte, Ablauf und Budget als gemeinsame Grundlage.
- [ ] Sichere private Uploads mit Quarantäne, Typprüfung, Malware-Prüfung, Quoten und begrenzter Verarbeitung.
- [ ] Gemeinsame Outbox, idempotente Hintergrundaufträge und dauerhafte Zeitpläne.
- [ ] WP-05: Kinderplanung und Betreuung mit gesonderten Zugriffs- und Datenschutzregeln.
- [ ] WP-04: Hochzeitspost mit Moderation und serverseitiger Zeitsperre für jeden Abruf und Export.
- [ ] WP-01: Angebotsvergleich, Quellen und Korrekturen; externe KI erst nach Anbieter- und Datenschutzprüfung.
- [ ] WP-02: Wetterintegration und bestätigte, versionierte Plan-B-Aktivierung.
- [ ] WP-03: Online-Notfallmodus; optionales minimiertes Offline-Paket erst nach eigener Sicherheitsprüfung.
- [ ] WP-06: Archiv, ausdrückliche Veröffentlichung, Export und vereinbarte Langzeitspeicherung.

## Lokale Befehle zur Wiederaufnahme

```sh
python scripts/dev.py setup
python scripts/dev.py build
python scripts/dev.py up
python scripts/dev.py test
python scripts/dev.py check
python scripts/smoke.py
python scripts/audit_dependencies.py
```

Diese Befehle gelten für künstliche lokale Entwicklung. `setup` erzeugt Testgeheimnisse, `up` ergänzt Testkonten. Für Produktion werden separate Befehle und Konfigurationen benötigt.

## Übergabestand

- Lokale Entwicklung einschließlich Landingpage abgeschlossen.
- 59 automatisierte Sicherheits- und Funktionstests bestanden.
- HTTP-Prüfung für öffentliche Landingpage, Anmeldung, Planungsbereich und Zugriff auf fremde Hochzeiten bestanden.
- Ruff-Codeprüfung und Formatprüfung bestanden; keine offenen Schema-Migrationen für diese Änderung erforderlich.
- Der Webdienst ist unter `http://localhost:18080` erreichbar. Die Datenbank hat keinen veröffentlichten Hostport.
- Keine Serveränderung vorgenommen. DNS und Reverse Proxy sind noch unverändert.
- Produktionszugänge und lokale Passwörter befinden sich nicht in diesem Repository.
- Der Übergabestand ist über den `main`-Branch des oben genannten Repositorys abrufbar. Die konkrete Commit-ID auf dem Server mit `git log -1 --oneline` prüfen.
- Als Nächstes auf dem Server mit der lesenden Bestandsaufnahme aus Abschnitt 1 beginnen.
