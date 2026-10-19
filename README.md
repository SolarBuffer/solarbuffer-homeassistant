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

Draait je hub op een recente versie, dan kondigt hij zichzelf aan op het
netwerk en verschijnt hij vanzelf onder Ontdekt bij Apparaten en diensten. Je
hoeft dan alleen je gebruikersnaam en wachtwoord in te vullen.

Verschijnt hij niet, stel hem dan met de hand in:

[![Open je Home Assistant en begin met het instellen van een nieuwe integratie.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=solarbuffer)

| Veld | Waarde |
|---|---|
| Adres | `solarbuffer.local`, of het IP-adres als mDNS niet werkt |
| Poort | `5001` |
| Gebruikersnaam en wachtwoord | Je inlog van de SolarBuffer-webinterface |

Gebruik een beheerdersaccount. De regeling, tijdschema's, anti-legionella en de
vakantiestand zijn met een kijkersaccount niet te bedienen.

## Entiteiten

### Sensoren van de hub

| Entiteit | Eenheid | Voorwaarde |
|---|---|---|
| Netvermogen | W | |
| Status | tekst | |
| Zonnevermogen | W | omvormer gekoppeld |
| Gas vandaag | m³ | gas ingeschakeld |
| Stroomprijs | ct/kWh | dynamische tarieven ingeschakeld |
| Laadstand accu | % | accu gekoppeld |
| Accuvermogen | W | accu gekoppeld |
| Accu geladen vandaag | kWh | accu gekoppeld |
| Accu ontladen vandaag | kWh | accu gekoppeld |

### Sensoren per SolarBuffer

| Entiteit | Eenheid | Voorwaarde |
|---|---|---|
| Status | tekst | |
| Vermogen | W | |
| Energie vandaag | kWh | |
| Stand | % | |
| Chiptemperatuur | °C | als de dimmer die meldt |
| Warmtevoorraad | kWh | hub 0.8.1 of nieuwer |
| Inhoud van het vat | kWh | hub 0.8.1 of nieuwer |
| Vat gevuld | % | hub 0.8.1 of nieuwer |
| Nog te gaan | minuten | hub 0.8.1 of nieuwer |
| Legionellaronde gestart | tijdstip | |

### Sensoren per verbruiker

| Entiteit | Eenheid | Voorwaarde |
|---|---|---|
| Vermogen | W | |
| Energie vandaag | kWh | |
| Temperatuur | °C | per temperatuursensor |

### Binaire sensoren

| Entiteit | Eenheid | Voorwaarde |
|---|---|---|
| Legionellaronde | aan of uit | per SolarBuffer |
| Legionellaronde nodig | aan of uit | per SolarBuffer |

De sensoren voor energie per dag hebben `state_class: total_increasing` en zijn
dus direct bruikbaar in het energiedashboard. De warmtevoorraad hoort daar
nadrukkelijk niet bij: die stand loopt op tijdens verwarmen en zakt terug zodra
de boiler uit staat, dus hij is `measurement`. Als oplopende teller zou Home
Assistant elke daling als een meterreset zien en het verschil als verbruik
optellen.

Stand is de dimstand op dezelfde schaal als de webinterface toont, dus 0 tot 100
en niet de ruwe 30 tot 100 waar de hub intern mee rekent.

"Nog te gaan" is geen vaste looptijd maar wat er nog in moet gedeeld door wat er
op dat moment in gaat. Die waarde beweegt dus mee met de zon, en blijft leeg als
er niets in gaat, bijvoorbeeld omdat de thermostaat heeft afgeslagen.

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
| Handmatige stand per SolarBuffer | invulveld | automatische besturing uit |
| Handmatig accuvermogen | invulveld | Zendure gekoppeld |

## Aandachtspunten

Draait je hub een versie ouder dan 0.8.1, dan levert die de warmtevoorraad niet
en worden die entiteiten niet aangemaakt. Dat is bewust: liever geen entiteit dan
een die voor altijd op niet beschikbaar staat. Werk je de hub later bij, herlaad
dan de integratie of herstart Home Assistant, dan verschijnen ze alsnog.

**De hub wordt herkend aan een vaste aanduiding**, niet aan zijn IP-adres, dus
een nieuwe DHCP-lease is geen probleem: het adres wordt dan vanzelf bijgewerkt.
Dat vraagt wel een hub die die aanduiding meestuurt. De losse SolarBuffers
worden nog wel aan hun IP-adres herkend; een reservering in de router voorkomt
dat ze na een adreswijziging opnieuw verschijnen.

**Oudere hubs** kennen de endpoints nog niet die een gevraagde stand aannemen.
De integratie valt dan terug op de omschakelaars van de webinterface. Alles
werkt, maar tegelijk bedienen vanuit Home Assistant en vanaf de hub kan dan een
onverwachte uitkomst geven. Werk de hub bij om dat te voorkomen.

**De handmatige stand is een invulveld, geen weergave.** Hij houdt vast wat
je hebt ingevuld en volgt niet de stand van de hub, anders zou hij elke paar
seconden veranderen en loopt je geschiedenis vol. Wat de boiler werkelijk doet
staat in de sensor Stand. Instellen kan alleen met de automatische besturing
uit; anders overschrijft de hub de waarde toch binnen enkele seconden.

**Inloggegevens worden bewaard** in de configuratie van de integratie, zodat er
na een herstart van de hub automatisch opnieuw kan worden ingelogd.
