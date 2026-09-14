"""Constanten voor de SolarBuffer-integratie."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "solarbuffer"

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
