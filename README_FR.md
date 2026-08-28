# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) | [🇬🇧 English](README.md) | [🇫🇷 Français](README_FR.md) | [🇮🇹 Italiano](README_IT.md) | [🇳🇴 Norsk](README_NO.md) | [🇸🇪 Svenska](README_SV.md) | [🇫🇮 Suomi](README_FI.md) | [🇵🇱 Polski](README_PL.md) | [🇳🇱 Nederlands](README_NL.md) | [🇪🇸 Español](README_ES.md) | [🇹🇷 Türkçe](README_TR.md) | [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper](/docs/cmdrh.png)

**Compagnon personnel pour Elite Dangerous — exploration, analyse des systèmes et données du Commandant**

Le projet est en développement actif.

## Fonctionnalités

### Journaux Elite Dangerous

CMDRHelper lit les fichiers Journal locaux d’Elite Dangerous et traite les systèmes stellaires, étoiles, planètes, lunes, amas d’astéroïdes, scans, cartographies ainsi que les signaux biologiques et géologiques. Les données personnelles du Commandant restent distinctes des informations externes complémentaires.

### Missions

CMDRHelper analyse les événements de mission des Journaux Elite Dangerous et présente clairement les missions actives. L’état des missions et les événements Journal associés sont suivis. Les offres reçues via les messages PNJ (`ReceiveText`) peuvent également être détectées et prises en compte progressivement.

### Vue système et Explorateur

Les corps connus sont affichés graphiquement et peuvent être sélectionnés directement. CMDRHelper affiche notamment le type de corps, la distance, l’état de scan et de cartographie, les possibilités de première découverte/First Mapping, les signaux BIO/GEO et les valeurs de scan/cartographie.

### Détails des corps

Un clic sur un corps ouvre une vue détaillée avec, selon les données disponibles, le type, la masse, la distance, la gravité, l’atmosphère, le volcanisme, l’atterrissabilité, le statut de terraformation, les matériaux, les signaux BIO/GEO et les valeurs d’exploration.

## Version 0.9.9

### Interface multilingue et contrôle des traductions

- CMDRHelper prend désormais en charge **12 langues d’interface** : allemand, anglais, français, italien, norvégien (Bokmål), suédois, finnois, polonais, néerlandais, espagnol, turc et grec.
- la langue peut être sélectionnée et enregistrée dans les paramètres.
- ordre de repli des traductions : **langue choisie → anglais → allemand → clé de traduction**.
- `tools/check_i18n.py` contrôle les clés `tr("...")`, les clés manquantes/supplémentaires, les doublons et les paramètres de formatage.
- sous Linux, ce contrôle est exécuté automatiquement par `start.sh` sans bloquer le démarrage en cas d’avertissement.

### Autres nouveautés de la version 0.9.9

La version 0.9.9 reprend toutes les améliorations de la branche 0.9.8 : carte système hiérarchique, aperçu « Tout afficher », liste de valeurs Explorer, valeurs non vendues, fenêtres live pour corps précieux et découvertes BIO, progression BIO détaillée, amélioration des missions et de `MissionRedirected`, galerie de captures d’écran, transfert EDSM, choix de police, page de paramètres défilante, protection contre plusieurs instances et améliorations de stabilité.

## Plateformes et installation

CMDRHelper est développé avec Python et PySide6 pour **Linux et Windows**. Les dépendances principales sont `PySide6>=6.7,<7`, `numpy` et `Pillow>=10.0`.

Sous Linux :
```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Sous Windows, utilisez `install.bat` puis `start.bat`.

## Licence

CMDRHelper est un logiciel libre publié sous **GNU General Public License Version 3 (GPL-3.0)**.

Copyright © 2026 **Holger Mangold (Faber38)**.

CMDRHelper est un projet communautaire/de loisir indépendant et n’est pas un produit officiel de Frontier Developments. **Elite Dangerous** et les noms et contenus associés appartiennent à leurs détenteurs respectifs.
