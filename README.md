# SolarBuffer voor Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)
[![Release](https://img.shields.io/github/v/release/SolarBuffer/solarbuffer-homeassistant)](https://github.com/SolarBuffer/solarbuffer-homeassistant/releases)

Koppelt je SolarBuffer-hub aan Home Assistant. De integratie praat lokaal met de
REST-API van de hub. Er is geen MQTT-broker nodig en er gaat niets via internet.

## Installatie

[![Open je Home Assistant en voeg deze repository toe aan HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=SolarBuffer&repository=solarbuffer-homeassistant&category=integration)

Klik op de knop hierboven, kies Download en herstart Home Assistant.

<details>
<summary>Handmatig, zonder HACS</summary>

Kopieer de map `custom_components/solarbuffer` naar de map `custom_components`
van je Home Assistant en herstart.

</details>

## Instellen

[![Open je Home Assistant en begin met het instellen van een nieuwe integratie.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=solarbuffer)

| Veld | Waarde |
|---|---|
| Adres | `solarbuffer.local`, of het IP-adres als mDNS niet werkt |
| Poort | `5001` |
| Gebruikersnaam en wachtwoord | Je inlog van de SolarBuffer-webinterface |

Gebruik een beheerdersaccount. De regeling, tijdschema's, anti-legionella en de
vakantiestand zijn met een kijkersaccount niet te bedienen.

## Entiteiten

### Sensoren

| Entiteit | Voorwaarde |
|---|---|
| Netvermogen | |
| Zonnevermogen | omvormer gekoppeld |
| Gas vandaag | gas ingeschakeld |
| Stroomprijs | dynamische tarieven ingeschakeld |
| Laadstand, vermogen, geladen en ontladen van de accu | accu gekoppeld |
| Vermogen, energie vandaag, stand en chiptemperatuur | per SolarBuffer |
| Vermogen en energie vandaag | per verbruiker |
| Temperatuur | per temperatuursensor |

De kWh-sensoren hebben `state_class: total_increasing` en zijn dus direct
bruikbaar in het energiedashboard.

### Bediening

| Entiteit | Type | Voorwaarde |
|---|---|---|
| Regeling | schakelaar | |
| Tijdschema's | schakelaar | |
| Anti-legionella | schakelaar | |
| Vakantiestand | schakelaar | |
| Aan of uit per SolarBuffer | schakelaar | |
| Boost | knop, per SolarBuffer | |
| Accustand: automatisch, handmatig of uit | keuzelijst | Zendure gekoppeld |
| Accurichting: laden of ontladen | keuzelijst | Zendure gekoppeld |
| Handmatig accuvermogen | getal | Zendure gekoppeld |

## Aandachtspunten

**Apparaten worden herkend aan hun IP-adres.** Wijzigt dat, bijvoorbeeld door
een nieuwe DHCP-lease, dan verschijnt het apparaat opnieuw. Een reservering in
de router voorkomt dat.

**Hubs ouder dan versie 0.7.4** kennen de endpoints nog niet die een gevraagde
stand aannemen. De integratie valt dan terug op de omschakelaars van de
webinterface. Alles werkt, maar tegelijk bedienen vanuit Home Assistant en
vanaf de hub kan dan een onverwachte uitkomst geven.

**Inloggegevens worden bewaard** in de configuratie van de integratie, zodat er
na een herstart van de hub automatisch opnieuw kan worden ingelogd.
