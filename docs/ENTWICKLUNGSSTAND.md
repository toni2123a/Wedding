# Lokale Grundlage

Stand: 23.10.2026. Entwicklungsphase 1 aus dem Architekturplan.

## Was implementiert ist

Die Anwendung enthält persönliche Konten, Anmeldung und Abmeldung, serverseitige Sitzungen, zwei künstliche Hochzeiten sowie Rollen pro Mitgliedschaft. Sie bietet eine geschützte Übersicht und eine Aufgabenverwaltung mit Zuweisung, Status und Versionsprüfung. Kritische Aufgabenänderungen erzeugen ein nicht über den Webzugang veränderbares Audit-Ereignis.

Die Aufgaben dienen zugleich dazu, die Mandantentrennung an echten Lese- und Schreibvorgängen zu prüfen. Weitere Fachmodule werden erst auf dieser Grundlage aufgebaut.

Die öffentliche Landingpage unter `/` stellt das Produkt vor. Ihre Vorschau besteht ausschließlich aus festen Beispieldaten. Der geschützte Bereich beginnt unter `/planung/`; Anmeldung, Rollen und die bestehenden Hochzeitsadressen bleiben erforderlich. Die öffentliche Seite liest keine privaten Hochzeits-, Aufgaben- oder Audit-Tabellen. Geplante Funktionen sind als noch nicht verfügbar gekennzeichnet.

## Datenbankrollen und RLS

`wedding_app` ist der tatsächliche Anmeldebenutzer des Webprozesses. Er besitzt keine Tabellen, kann keine Datenbanken oder Rollen erstellen, kann keine Tabellen leeren und ist kein Mitglied der Migrationsrolle. Bei Hochzeiten, Mitgliedschaften, Aufgaben und Audit-Einträgen sind RLS und `FORCE ROW LEVEL SECURITY` aktiv.

`wedding_migrator` richtet Schema und lokale Testdaten ein. Seine ausdrücklich benannten Migrationsrichtlinien erlauben ihm den notwendigen administrativen Datenzugriff. Seine Zugangsdaten werden ausschließlich in kurzlebige Migrations-, Seed- oder Testcontainer eingebunden. Der PostgreSQL-Administratorzugang bleibt im Datenbankcontainer.

Unter Linux schützt das lokale Setup den Geheimnisordner mit Modus `0700`. Einzelne eingebundene Secret-Dateien sind lesbar, weil dateibasierte Compose-Secrets die Host-Dateirechte durchreichen und die Prozesse im Container unprivilegiert laufen. Andere Hostnutzer können den geschützten Ordner nicht durchlaufen. Windows verwendet die vorhandenen NTFS-Zugriffsrechte. Das ist ein lokales Entwicklungsmodell und keine Vorlage für die produktive Schlüsselablage.

Die `SECURITY DEFINER`-Funktionen befinden sich in einem nicht öffentlich beschreibbaren Schema. Ihr `search_path` ist festgelegt, ihre Tabellenzugriffe sind voll qualifiziert und Ausführung durch `PUBLIC` ist widerrufen. Sie liefern entweder die aktuelle Mitgliedschaft oder eine begrenzte Hochzeitsauswahl anhand des serverseitig gesetzten Kontokontextes.

Der Kontext wird mit transaktionslokalen Einstellungen gesetzt und bei verschachtelten Aufrufen wiederhergestellt. Fehlender Hochzeitkontext sperrt private Fachtabellen. Der Bootstrap-Zugang ist eine ausdrückliche Ausnahme für die Hochzeitsauswahl und gibt keine Aufgaben oder privaten Planungsdaten zurück.

Die Anwendung ist die Vertrauensgrenze für die geprüfte Identität. Ein vollständig übernommener Webprozess könnte seine eigenen Zugangsdaten und Kontextmöglichkeiten missbrauchen. Die RLS-Implementierung ist eine zusätzliche Absicherung und keine Behauptung, dass sie einen kompromittierten Anwendungsprozess oder Host unschädlich macht.

## Teststrategie

Die Tests erzeugen pro Lauf eine eigene Datenbank mit zufälligem Namen. Einrichtung und Migration erfolgen administrativ. Danach schließen die Tests diese Verbindung und melden sich tatsächlich als `wedding_app` an. `current_user` und `session_user` werden geprüft. Die Tests laufen nicht lediglich mit einem umgeschalteten Superuser.

Geprüft werden Anmeldegrenzen, CSRF, Hostprüfung, Sitzungsablauf, Weiterleitungsziele, direkte SQL-Zugriffe, fehlende Kontexte, wechselnde Hochzeiten auf derselben Verbindung, fremde IDs, Schreibverbote, falsche Zuständigkeiten, Rollen je Hochzeit, Audit-Rollback, veraltete Änderungen und der Entzug einer bestehenden Freigabe.

Der HTTP-Smoke-Test prüft den real gestarteten Gunicorn-/Django-Anschluss. Ein automatisierter visueller Browsercheck setzt eine verfügbare Browseranbindung voraus und ist durch diese HTTP-Prüfung nicht ersetzt.

## Bewusste Grenzen

Dieser Entwicklungsstand hat noch keine MFA, Gasttoken, Uploads, Offline-Pakete, KI oder produktive Verschlüsselungs- und Sicherungslösung. Im lokalen Docker-Volume liegen ausschließlich künstliche Daten. Das ist keine produktive Datenablage für Kundendaten.

Es existiert noch kein produktiver Compose-Stack und keine Serveränderung. Für den Einsatz auf dem vorhandenen CX33 sind die Bestandsaufnahme des Proxys, der Ressourcenabgleich und sämtliche Freigabekriterien des Architekturplans weiterhin erforderlich.
