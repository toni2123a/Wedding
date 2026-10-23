# Hochzeitsplattform

Hier entsteht die Hochzeitsplattform. Der lokale Entwicklungsstand enthält eine öffentliche Produkt-Landingpage sowie Anmeldung, getrennte Hochzeiten, Rollen und eine Aufgabenverwaltung.

- [Funktionale Anforderungen](blueprint.txt)
- [Architekturplan mit Sicherheits- und Betriebskonzept](ARCHITEKTURPLAN.md)
- [TODO und Übergabe für die Weiterarbeit auf dem Server](TODO.md)

Geplante Produktionsumgebung ist der vorhandene Hetzner CX33 mit Debian 12 neben `tsdigitalsolution.de`. Als erste Adresse ist `hochzeit.tsdigitalsolution.de` vorgeschlagen.

## Lokal starten

Voraussetzungen sind Docker mit Linux-Containern, Docker Compose und Python ab 3.10 für die Bedienungsskripte. Die Anwendung selbst läuft mit Python 3.13 im Container. Die vorhandenen Docker-Projekte werden nicht angehalten oder mitbenutzt.

```powershell
python scripts/dev.py setup
python scripts/dev.py build
python scripts/dev.py up
```

Die Anwendung ist anschließend unter [http://localhost:18080](http://localhost:18080) erreichbar. Nur der Webdienst veröffentlicht einen Port, ausschließlich an `127.0.0.1`. PostgreSQL hat keinen veröffentlichten Hostport.

| Adresse | Inhalt |
|---|---|
| `/` | Öffentliche Produktseite mit Vorschau, Funktionen, Ausblick und Fragen |
| `/anmelden/` | Persönliche Anmeldung |
| `/planung/` | Geschützte Auswahl der eigenen Hochzeiten |
| `/hochzeiten/<id>/` | Geschützte Übersicht einer freigegebenen Hochzeit |

Nach der Anmeldung öffnet sich der geschützte Planungsbereich. Die Produktseite verwendet ausschließlich feste Beispieldaten und fragt keine privaten Hochzeitsinhalte ab. Geplante Module sind dort als noch nicht verfügbar gekennzeichnet.

`setup` erzeugt eigene zufällige lokale Geheimnisse und überschreibt vorhandene Werte nicht. Die Testzugänge stehen in [secrets/local/demo-accounts.txt](secrets/local/demo-accounts.txt). Diese Datei und alle Geheimnisse sind von Git und Docker-Builds ausgeschlossen. Die Datei entsteht erst durch `setup` und wird nicht versioniert.

| Testkonto | Zugang |
|---|---|
| `mara@demo.invalid` | Brautpaar in Hochzeit A |
| `lea@demo.invalid` | Brautpaar in Hochzeit B |
| `sam@demo.invalid` | Mitplaner in A, Trauzeuge in B |
| `toni@demo.invalid` | Trauzeuge mit einer zugewiesenen Aufgabe in A |
| `gast@demo.invalid` | Gast in A ohne interne Aufgabenrechte |
| `anbieter@demo.invalid` | Dienstleister in A ohne interne Aufgabenrechte |
| `ohne-zugang@demo.invalid` | Technisches Testkonto ohne Zugriff auf eine Hochzeit, auch mit Django-Administratormerkmal |

Eine erneute Ausführung von `up` führt offene Migrationen aus und ergänzt fehlende Testdaten. Bereits bearbeitete Testaufgaben werden dabei nicht zurückgesetzt. Nach Quellcodeänderungen zuerst `build` und anschließend `up` ausführen.

## Prüfen und stoppen

```powershell
python scripts/dev.py test
python scripts/dev.py check
python scripts/smoke.py
python scripts/audit_dependencies.py
python scripts/dev.py status
python scripts/dev.py down
```

`test` erzeugt eine eigene zufällig benannte PostgreSQL-Testdatenbank, migriert sie und löscht ausschließlich diese Datenbank anschließend wieder. Die eigentlichen Tests verbinden sich als `wedding_app`, ohne Superuser-, Besitzer- oder RLS-Umgehungsrechte. Die normale lokale Datenbank bleibt erhalten.

`check` prüft die laufende Sicherheitskonfiguration und die Django-Einstellungen. `smoke.py` prüft Anmeldung, Sitzung und Hochzeitszugriff zusätzlich über den echten HTTP-Anschluss der gestarteten Anwendung. `down` stoppt ausschließlich das Compose-Projekt `wedding_local` und behält sein Datenvolume.

`audit_dependencies.py` fragt die veröffentlichten PyPI-Sicherheitsmeldungen für die vollständig gesperrten Laufzeitabhängigkeiten ab. Dafür werden nur öffentliche Paketnamen und Versionen übermittelt. Eine nicht erreichbare Prüfung wird als Fehler behandelt. Die Abfrage ist kein vollständiger Container- oder Sicherheits-Scan.

Die vorbereitete [GitHub-Prüfung](.github/workflows/ci.yml) baut denselben Stack und führt Tests sowie HTTP-Prüfung mit neu erzeugten künstlichen Daten aus. Sie veröffentlicht nichts und benötigt keine Produktionsgeheimnisse. Sie wurde lokal entsprechend ihrer einzelnen Schritte geprüft; ein Lauf auf GitHub erfolgt erst nach dem späteren Hochladen.

## Umgesetzte Sicherheitsgrenzen

- Hochzeitkontext und aktuelle Mitgliedschaft werden bei jeder geschützten Anfrage serverseitig geprüft.
- PostgreSQL erzwingt Row Level Security zusätzlich zur Anwendung. Ohne Kontext sind private Fachtabellen nicht lesbar. Eine begrenzte Bootstrap-Funktion liefert nur die Hochzeitsauswahl des angemeldeten Kontos.
- Rollen gelten je Hochzeit. Trauzeugen sehen ausschließlich zugewiesene Aufgaben. Gäste und Dienstleister erhalten keine impliziten internen Planungsrechte.
- Ein zusammengesetzter Fremdschlüssel verhindert Aufgaben mit einer zuständigen Person aus einer anderen Hochzeit.
- Aufgabenänderung und Audit-Eintrag erfolgen gemeinsam. Versionsprüfungen erkennen veraltete Statusänderungen.
- Der Webcontainer bekommt weder Migrations- noch PostgreSQL-Administrationsgeheimnisse. Die privilegierte Migrationsrolle hat nur lokal für die isolierten Testdatenbanken `CREATEDB`; dieses Recht gehört nicht in einen späteren Produktions-Migrationszugang.
- Der Webprozess läuft unprivilegiert und mit schreibgeschütztem Dateisystem. Er prüft seine Datenbankrechte vor dem Start.
- Anmeldung verwendet Argon2, CSRF-Schutz, begrenzte Versuche und serverseitige Sitzungen mit Inaktivitäts- und Gesamtlaufzeit. Cookies gehören nur zum jeweiligen Host.
- Es gibt keine öffentliche Registrierung, unbeschränkte Django-Adminseite oder externen E-Mail- beziehungsweise KI-Aufrufe.

Technische Einzelheiten und Grenzen stehen in [docs/ENTWICKLUNGSSTAND.md](docs/ENTWICKLUNGSSTAND.md).

## Umfang dieses Entwicklungsstands

Dieser Stand ist ausschließlich für lokale, künstliche Daten eingerichtet. Die lokale HTTP-Anmeldung verwendet absichtlich keine als `Secure` markierten Cookies; die spätere HTTPS-Konfiguration ist getrennt umzusetzen. Die Einstellungen verweigern einen Start ohne `APP_ENV=local`.

Noch fehlen insbesondere MFA, Kontowiederherstellung, Gästeeinladungen, sichere Dateiuploads, die sechs Fachmodule, Datenexport und Löschung, Verschlüsselung der persistenten Datenablage, Backup und Wiederherstellung sowie die Produktionskonfiguration. Der Stand ist deshalb noch nicht für echte Kundendaten oder eine öffentliche Bereitstellung freigegeben.

Kundendaten, Uploads, Backups und Produktionsschlüssel gehören nicht in dieses Verzeichnis oder das spätere GitHub-Repository. Die Architekturplanung berücksichtigt weiterhin den gemeinsamen VPS mit `tsdigitalsolution.de`; auf diesem Server wurde für die lokale Entwicklung nichts geändert.
