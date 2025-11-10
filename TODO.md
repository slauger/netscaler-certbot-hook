# TODO: Repository Verbesserungen

## ✅ Phase 1: Code-Qualität & Struktur (COMPLETED)

### 1.1 Fehlerbehandlung verbessern ✅
- [x] Spezifische Exception-Typen statt leerer `except:` Blöcke verwenden
- [x] Fehlerbehandlung in `nitro_check_cert()` (netscaler-certbot-hook.py:72-82)
- [x] Fehlerbehandlung in `nitro.py` request() Methode (nitro.py:64-67)
- [x] Validierung hinzufügen: Dateien existieren vor dem Öffnen prüfen
- [x] Validierung: Umgebungsvariablen auf Vollständigkeit prüfen

### 1.2 Code-Struktur refactoring ✅
- [x] Hauptlogik in Funktionen aufteilen (statt linearer Code)
- [x] Code-Duplikation eliminieren (Update vs. Initial Install Pfad)
- [x] Argumente-Parser in eigene Funktion auslagern
- [x] Konfiguration in eigene Klasse/Funktion auslagern
- [x] Main-Funktion erstellen mit `if __name__ == '__main__':`

### 1.3 Logging-Framework 🔄
- [ ] `print()` Statements durch `logging` Modul ersetzen
- [ ] Log-Level konfigurierbar machen (DEBUG, INFO, WARNING, ERROR)
- [ ] Strukturiertes Logging für bessere Nachvollziehbarkeit

### 1.4 Type Hints & Docstrings ✅
- [x] Type Hints zu allen Funktionen hinzufügen
- [x] Docstrings im Google/NumPy Style hinzufügen
- [x] Modul-Level Docstrings vervollständigen

### 1.5 Sicherheit & Bug Fixes ✅
- [x] `verify_ssl` Boolean-Konvertierung fixen (aktuell String)
- [x] SSL-Verifikation standardmäßig aktiviert lassen
- [x] Sensible Daten nicht in Logs ausgeben

## ✅ Phase 2: Dokumentation (COMPLETED)

### 2.1 README.md verbessern ✅
- [x] Voraussetzungen-Sektion (Python-Version, Dependencies)
- [x] Installation-Anleitung erweitern
- [x] Umgebungsvariablen-Tabelle erstellen
- [x] Fehlerbehandlung & Troubleshooting Sektion
- [x] Cronjob-Beispiele für Automatisierung
- [x] Sicherheitshinweise ergänzen

### 2.2 Projekt-Dateien ✅
- [x] `requirements.txt` erstellen mit allen Dependencies
- [x] `.gitignore` erstellen (falls nicht vorhanden)
- [x] `setup.py` oder `pyproject.toml` für Installation erstellen
- [x] `LICENSE` Datei hinzufügen (MIT laut Code-Header)
- [ ] `CHANGELOG.md` für Versions-Historie

### 2.3 API-Dokumentation ✅
- [x] Nitro Client API dokumentieren
- [x] Beispiele für direkte Verwendung des Nitro Clients
- [x] Rückgabewerte und Exceptions dokumentieren

## Phase 3: Tests & CI/CD

### 3.1 Unit Tests
- [ ] Test-Struktur einrichten (tests/ Verzeichnis)
- [ ] Unit Tests für Nitro Client (`test_nitro.py`)
- [ ] Unit Tests für Hauptfunktionen (`test_main.py`)
- [ ] Mock-Objekte für API-Calls erstellen
- [ ] Test-Coverage messen

### 3.2 Integration Tests
- [ ] Integration Tests mit Test-NetScaler (falls möglich)
- [ ] Test mit verschiedenen Zertifikatsformaten
- [ ] Fehlerfall-Tests (ungültige Credentials, Netzwerkfehler)

### 3.3 CI/CD Pipeline
- [ ] GitHub Actions Workflow erstellen
- [ ] Linting (pylint, flake8) integrieren
- [ ] Type-Checking (mypy) integrieren
- [ ] Tests automatisch ausführen
- [ ] Code-Coverage Reporting

## Phase 4: Features & Erweiterungen

### 4.1 Konfiguration
- [ ] Konfigurations-Datei unterstützen (YAML/JSON)
- [ ] Multiple Zertifikate in einem Durchlauf verarbeiten
- [ ] Dry-Run Modus für Tests

### 4.2 Monitoring & Reporting
- [ ] Erfolgs-/Fehler-Status per Exit-Code zurückgeben
- [ ] Optional: Benachrichtigungen (E-Mail, Webhook)
- [ ] Metrics/Statistiken ausgeben

### 4.3 Cleanup & Wartung
- [ ] Alte Zertifikats-Dateien automatisch aufräumen
- [ ] Retention Policy für alte Dateien auf dem NetScaler
- [ ] Backup vor Update optional

## Phase 5: Code-Modernisierung

### 5.1 Python Best Practices
- [ ] Black für Code-Formatting verwenden
- [ ] isort für Import-Sortierung
- [ ] Pre-commit Hooks einrichten
- [ ] Typing mit Protocol/TypedDict wo sinnvoll

### 5.2 Dependencies aktualisieren
- [ ] Dependency-Versionen prüfen und aktualisieren
- [ ] Kompatibilität mit neueren Python-Versionen testen
- [ ] Deprecated Features ersetzen

---

## Prioritäten

**Hoch:**
- Phase 1.1 (Fehlerbehandlung)
- Phase 1.5 (Sicherheit)
- Phase 2.1 (README)
- Phase 2.2 (requirements.txt)

**Mittel:**
- Phase 1.2 (Refactoring)
- Phase 1.3 (Logging)
- Phase 2.3 (API-Docs)
- Phase 3.1 (Unit Tests)

**Niedrig:**
- Phase 1.4 (Type Hints)
- Phase 3.2-3.3 (Integration Tests, CI/CD)
- Phase 4 (Features)
- Phase 5 (Modernisierung)
