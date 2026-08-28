# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) | [🇬🇧 English](README.md) | [🇫🇷 Français](README_FR.md) | [🇮🇹 Italiano](README_IT.md) | [🇳🇴 Norsk](README_NO.md) | [🇸🇪 Svenska](README_SV.md) | [🇫🇮 Suomi](README_FI.md) | [🇵🇱 Polski](README_PL.md) | [🇳🇱 Nederlands](README_NL.md) | [🇪🇸 Español](README_ES.md) | [🇹🇷 Türkçe](README_TR.md) | [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper](/docs/cmdrh.png)

**Compañero personal para Elite Dangerous — exploración, análisis de sistemas y datos del Commander**

El proyecto está en desarrollo activo.

## Funciones

### Journals de Elite Dangerous

CMDRHelper lee los archivos Journal locales de Elite Dangerous y procesa sistemas estelares, estrellas, planetas, lunas, Belt Clusters, escaneos, cartografía y señales biológicas y geológicas.

### Misiones

CMDRHelper analiza los eventos de misión de los Journals y muestra claramente las misiones activas. También puede detectar ofertas recibidas mediante mensajes NPC (`ReceiveText`).

### Vista de sistema y Explorer

Los cuerpos conocidos se muestran gráficamente con tipo, distancia, estado de escaneo/cartografía, señales BIO/GEO y valores.

### Detalles de cuerpos

Al seleccionar un cuerpo se abre una vista detallada con los datos físicos disponibles, materiales, señales BIO/GEO y valores de exploración.

## Versión 0.9.9

### Interfaz multilingüe y comprobación de traducciones

- CMDRHelper admite ahora **12 idiomas de interfaz**: alemán, inglés, francés, italiano, noruego (Bokmål), sueco, finés, polaco, neerlandés, español, turco y griego.
- el idioma puede seleccionarse y guardarse en Ajustes.
- fallback: **idioma seleccionado → inglés → alemán → clave de traducción**.
- `tools/check_i18n.py` comprueba claves `tr("...")`, claves ausentes/adicionales, duplicados y marcadores de formato.
- en Linux la comprobación se ejecuta automáticamente mediante `start.sh` sin impedir el inicio.


### Weitere / Additional 0.9.9 improvements

Version 0.9.9 also contains the Explorer, system-map, BIO valuation, mission, screenshot, EDSM, usability and stability improvements documented in the German and English main README files. Those two files remain the most detailed release documentation.

## Technical requirements

`PySide6>=6.7,<7`, `numpy`, `Pillow>=10.0`

Linux:
```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Windows: `install.bat`, then `start.bat`.

## License

CMDRHelper is free software released under **GNU General Public License Version 3 (GPL-3.0)**.

Copyright © 2026 **Holger Mangold (Faber38)**.

CMDRHelper is an independent community/hobby project and is not an official Frontier Developments product. **Elite Dangerous** and related names and content belong to their respective rights holders.

