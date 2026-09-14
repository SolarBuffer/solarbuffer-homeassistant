# SolarBuffer voor Home Assistant

Koppelt je SolarBuffer-hub rechtstreeks aan Home Assistant. Geen MQTT-broker
nodig: de integratie praat lokaal met de REST-API die de hub zelf al heeft.

## Wat je krijgt

**Sensoren**

| | |
|---|---|
| Netvermogen | live vermogen van de P1-meter |
| Zonnevermogen | alleen bij een gekoppelde omvormer |
| Laadstand, vermogen, geladen en ontladen | bij een gekoppelde accu |
| Gas vandaag | alleen als gas aanstaat |
| Stroomprijs | alleen bij dynamische tarieven |
| Per SolarBuffer | vermogen, energie vandaag, stand en chiptemperatuur |
| Per verbruiker | vermogen en energie vandaag |
| Per temperatuursensor | temperatuur |

De kWh-sensoren hebben `state_class: total_increasing`, dus je kunt ze
rechtstreeks in het energiedashboard van Home Assistant gebruiken.

**Bediening**

- Regeling aan of uit
- Tijdschema's aan of uit
- Anti-legionella aan of uit
- Vakantiestand
- Elke SolarBuffer handmatig aan of uit
- Boost per SolarBuffer
- Accustand (automatisch, handmatig, uit), richting en vermogen, bij een
  gekoppelde Zendure

## Installeren

Via HACS: voeg deze repository toe als custom repository van het type
Integration, installeer SolarBuffer en herstart Home Assistant.

Handmatig: kopieer `custom_components/solarbuffer` naar de map
`custom_components` van je Home Assistant en herstart.

Daarna: Instellingen → Apparaten en diensten → Integratie toevoegen →
SolarBuffer. Vul het adres van je hub in (standaard poort 5001) en een account
dat op de webinterface kan inloggen.

## Goed om te weten

**Beheerdersrechten.** De regeling, tijdschema's, anti-legionella en de
vakantiestand vragen een beheerdersaccount op de hub. Met een kijkersaccount
werken de sensoren wel, maar geven die schakelaars een foutmelding.

**Aan- en uitzetten is omschakelen.** De hub kent voor een aantal functies
alleen een omschakel-endpoint en geen losse aan en uit. De integratie kijkt
daarom eerst naar de huidige stand en schakelt alleen als die afwijkt. Druk je
in Home Assistant en op de hub tegelijk, dan kan de uitkomst afwijken van wat
je verwacht.

**Opnieuw inloggen na een herstart van de hub.** De hub bewaart API-tokens
alleen in het geheugen. Na een herstart is elk token ongeldig; de integratie
merkt dat aan een 401 en logt automatisch opnieuw in. Daarom worden je
gebruikersnaam en wachtwoord in de config entry bewaard.

**Apparaten worden op IP herkend.** Wijzigt het IP-adres van een SolarBuffer,
bijvoorbeeld door een nieuwe DHCP-lease, dan verschijnt hij als nieuw apparaat.
Een vaste lease of een reservering in je router voorkomt dat.

## Wat er nog niet in zit

- Binaire sensoren voor bereikbaarheid van de hub, P1 en accu
- Maandtotalen uit `/api/monthly`
- Het instellen van tijdschema's
- Langlevende tokens, zodat gebruikersnaam en wachtwoord niet bewaard hoeven
  te worden. Dat vraagt een wijziging aan de hub zelf.
