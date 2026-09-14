"""Constanten voor de SolarBuffer-integratie."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "solarbuffer"

# De hub heet standaard "SolarBuffer", dus die naam is via mDNS te bereiken
# zonder dat je het IP hoeft op te zoeken. Werkt alleen als de machine waarop
# Home Assistant draait mDNS kan opzoeken; Home Assistant OS kan dat, een kale
# Docker-container vaak niet. Vandaar dat het veld gewoon aanpasbaar blijft.
DEFAULT_HOST = "solarbuffer.local"
DEFAULT_PORT = 5001
DEFAULT_SCAN_INTERVAL = timedelta(seconds=5)

# De hub bewaart API-tokens alleen in het geheugen, dus na een herstart is elk
# token ongeldig. We loggen daarom opnieuw in zodra een verzoek 401 teruggeeft,
# en bewaren gebruikersnaam en wachtwoord in de config entry. Zodra de hub
# langlevende tokens ondersteunt kan dat hier vervallen.
TOKEN_PATH = "/api/token"
STATUS_PATH = "/status_json"

# Accustanden zoals de hub ze kent
BATTERY_MODES = ["auto", "manual", "off"]
BATTERY_DIRECTIONS = ["charge", "discharge"]

# De hub begrenst het handmatige vermogen zelf op zendure_max_power, dus een
# ruimere bovengrens hier is veilig: te veel vragen wordt gewoon afgetopt.
MAX_MANUAL_POWER_W = 2500

# De dimmer werkt betrouwbaar tussen 30 en 100. De hub rekent in die ruwe
# waarden, maar toont de gebruiker een schaal van 0 tot 100, en dat is ook wat
# de webinterface doet. Zonder omrekenen zou een boiler die net aanslaat in
# Home Assistant op 31% staan terwijl het dashboard 1% zegt.
MIN_BRIGHTNESS = 30
MAX_BRIGHTNESS = 100


def zichtbaar_naar_ruw(zichtbaar: float) -> int:
    """Schaal 0-100 zoals de gebruiker die ziet naar de ruwe stand van de hub."""
    v = float(zichtbaar or 0)
    if v <= 0:
        return 0
    if v >= 100:
        return MAX_BRIGHTNESS
    return round(MIN_BRIGHTNESS + (v / 100) * (MAX_BRIGHTNESS - MIN_BRIGHTNESS))


def ruw_naar_zichtbaar(ruw: float | None) -> float | None:
    """De ruwe stand van de hub terug naar de schaal die de gebruiker kent."""
    if ruw is None:
        return None
    r = float(ruw)
    if r <= 0:
        return 0.0
    return max(0.0, min(100.0,
                        (r - MIN_BRIGHTNESS) / (MAX_BRIGHTNESS - MIN_BRIGHTNESS) * 100))
