# Icoon voor Home Assistant

Home Assistant haalt iconen en logo's niet uit de integratie zelf, maar uit een
aparte repository: [home-assistant/brands](https://github.com/home-assistant/brands).
Zolang die er niet in staat, toont Home Assistant een standaard puzzelstukje bij
de integratie.

De bestanden hieronder staan al in de goede mappenstructuur en het goede formaat.

```
custom_integrations/solarbuffer/
├── icon.png      256 x 256
└── icon@2x.png   512 x 512
```

## Indienen

1. Fork `home-assistant/brands`
2. Kopieer de map `custom_integrations/solarbuffer` uit deze map naar de fork
3. Open een pull request

Het domein in de mapnaam moet exact overeenkomen met `domain` in
`custom_components/solarbuffer/manifest.json`, dus `solarbuffer`.

Een logo is optioneel. Laat je dat weg, dan gebruikt Home Assistant het icoon
overal waar anders het logo zou staan.

## Bron

Gemaakt van `static/icons/icon-1024.png` uit de SolarBuffer-app, zodat het
icoon in Home Assistant hetzelfde is als op de hub en op de telefoon.
