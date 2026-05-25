# Battlegrounds — Opstartgids

## 1. Python installeren (éénmalig)

1. Ga naar https://www.python.org/downloads/
2. Download Python 3.11 of nieuwer
3. **Belangrijk bij installatie**: vink "Add Python to PATH" aan
4. Herstart je terminal/PowerShell na installatie

## 2. Dependencies installeren (éénmalig)

Open PowerShell in de `battlegrounds` map en voer uit:

```powershell
pip install flask flask-socketio eventlet
```

## 3. Server starten

```powershell
python server.py
```

De server start op **http://localhost:5000**

## 4. Spelen

1. Open een browser en ga naar http://localhost:5000
2. Voer je naam in en maak een lobby (of join een bestaande)
3. Deel de 4-letter kamer code met vrienden
4. De host kan het spel starten (lege plekken worden gevuld met AI bots)

## Meerdere spelers op 1 computer (testen)

Open meerdere browsertabbladen op http://localhost:5000 — elk tabblad is een aparte speler.

## Meerdere spelers via netwerk

Andere spelers op hetzelfde netwerk kunnen verbinden via:
```
http://<jouw-ip-adres>:5000
```
Jouw IP vind je met: `ipconfig` in PowerShell.

---

## Spel uitleg

| Fase | Beschrijving |
|---|---|
| **Hero selectie** | Kies een held met een speciale ability |
| **Shop fase** | Koop, verkoop, herrol en upgrade minions |
| **Klaar!** | Druk op Klaar als je tevreden bent |
| **Gevecht** | Minions vechten automatisch — bekijk de replay |
| **Schade** | Verliezer krijgt schade op basis van overlevende minions |

### Shop acties
- **Kopen** — Klik op een minion in de winkel (kost 3 goud)
- **Verkopen** — Rechtsklik op een minion op je board
- **Herrol** — Ververs de winkel voor 1 goud
- **Bevries** — Houd huidige winkel voor volgende ronde (gratis)
- **Upgrade** — Verhoog je tavern tier voor betere minions

### Tips
- 3 dezelfde minions = golden versie (2× stats)!
- Positie op je board maakt uit (links valt het eerst aan)
- Taunt minions beschermen je andere minions
