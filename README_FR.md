# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) \| [🇬🇧 English](README.md) \| [🇫🇷
Français](README_FR.md) \| [🇮🇹 Italiano](README_IT.md) \| [🇳🇴
Norsk](README_NO.md) \| [🇸🇪 Svenska](README_SV.md) \| [🇫🇮
Suomi](README_FI.md) \| [🇵🇱 Polski](README_PL.md) \| [🇳🇱
Nederlands](README_NL.md) \| [🇪🇸 Español](README_ES.md) \| [🇹🇷
Türkçe](README_TR.md) \| [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper -- Votre copilote pour Elite Dangerous](cmdrhelper/assets/readme/cmdrhelper_readme_fr.png)

**Compagnon personnel pour Elite Dangerous -- exploration, analyse des
systèmes et données du Commander en un coup d'œil**

CMDRHelper est une application de bureau indépendante pour **Elite
Dangerous** qui analyse les informations provenant des fichiers Journal
locaux du jeu et les présente de manière claire. L'objectif est de
proposer un assistant personnel qui, lors de l'exploration d'un système,
indique rapidement ce qui est déjà connu, quels corps célestes sont
intéressants et quelles découvertes et cartographies ont été réalisées
par le Commander lui-même.

Le projet est toujours en développement actif.

## Vue d'ensemble des fonctions

### Journaux Elite Dangerous

CMDRHelper lit les fichiers Journal locaux et traite notamment les
systèmes stellaires, les étoiles, les planètes, les lunes, les Belt
Clusters, les scans, les cartographies ainsi que les signaux biologiques
et géologiques. Les données propres au Commander restent distinctes des
informations externes complémentaires.

### Missions

CMDRHelper analyse les événements de mission des Journaux Elite
Dangerous et présente clairement les missions actives. L'état des
missions et les événements Journal associés sont suivis.

Les offres de mission reçues pendant le jeu via des messages de PNJ
(`ReceiveText`) peuvent également être reconnues et prises en compte
pour l'affectation ultérieure des missions. Comme Elite Dangerous ne
fournit pas, pour chaque type de mission, toutes les informations dans
un même événement Journal, l'affectation est construite progressivement
à partir des données Journal disponibles.

### Vue Système et Explorer

Les corps connus d'un système sont représentés graphiquement et peuvent
être sélectionnés directement. CMDRHelper peut notamment afficher :

-   le nom et le type du corps
-   la distance dans le système
-   scanné personnellement ou connu uniquement par une source externe
-   déjà découvert et cartographié
-   première découverte possible et First Mapping possible
-   cartographié par le Commander
-   cartographie efficace
-   signaux biologiques et géologiques
-   valeurs de scan et de cartographie

Les signaux BIO sont clairement mis en évidence sur le corps concerné.
L'affectation est effectuée par système afin d'éviter toute confusion
entre les BodyID de différents systèmes stellaires.

### Vue détaillée des corps

Un clic sur un corps ouvre une vue détaillée. Selon les données
disponibles, elle affiche le type de corps, la masse, la distance, la
gravité, l'atmosphère, le volcanisme, la possibilité d'atterrir, l'état
de terraformation, les matériaux, les signaux BIO/GEO, la valeur de
scan, la valeur de cartographie et l'état de découverte.

Les informations manquantes sont indiquées comme inconnues et ne sont
pas présentées comme des données certaines.

## Représentation graphique des corps

CMDRHelper dispose de ses propres graphismes pour de nombreux types de
corps, notamment High Metal Content Worlds, Metal Rich Bodies, Rocky
Bodies, Icy Bodies, Rocky Ice Worlds, Earth-like Worlds, Water Worlds,
Ammonia Worlds, plusieurs classes de géantes gazeuses, des géantes
gazeuses avec vie basée sur l'eau ou l'ammoniac, des géantes gazeuses
riches en hélium, différentes classes d'étoiles et des Belt Clusters.

Les images PNG normales sont utilisées dans les vues d'ensemble. Pour de
nombreux corps, une **texture équirectangulaire 2:1 `_texture.png`** est
également disponible pour la vue détaillée animée.

### Planètes 3D en rotation

Les textures 2:1 appropriées sont projetées sur une sphère en rotation.
Le moteur de rendu CPU fonctionne avec **PySide6 et NumPy** sans
dépendance supplémentaire à OpenGL/PyOpenGL. Il comprend la projection
sphérique, une rotation lente, l'éclairage, l'assombrissement des bords
et un liseré atmosphérique.

### Formes de vie animées

Différentes animations existent pour les géantes gazeuses abritant de la
vie :

**Water Life :** organismes flottants cyan/turquoise avec halo et queues
en mouvement.

**Ammonia Life :** organismes spécifiques violet/ambre,
semi-transparents, avec un noyau pulsant, de courts filaments et des
mouvements plus lents.

### Belt Clusters animés

Les Belt Clusters ne sont pas représentés sous forme de sphères. La vue
détaillée génère un champ d'astéroïdes procédural avec des astéroïdes
individuels, différentes tailles et profondeurs, leur propre rotation,
une dérive individuelle, un effet de parallaxe, des cratères ainsi que
des effets discrets de poussière et de particules.

## EDSM comme source de données complémentaire

CMDRHelper peut distinguer les données de son propre Journal des
informations EDSM. La source est indiquée en conséquence comme Journal
propre, EDSM ou Journal propre + EDSM. Les données du Journal personnel
sont particulièrement importantes, car elles montrent ce que le
Commander concerné a réellement scanné ou cartographié lui-même.

CMDRHelper peut transférer automatiquement les nouvelles données Journal
vers EDSM. La liste dynamique EDSM Discard actuelle est prise en compte,
de sorte que seuls les événements souhaités par EDSM sont envoyés. La
progression du transfert est enregistrée de manière sûre pour chaque
fichier Journal. Lors de la première activation, les anciens Journaux
déjà présents ne sont pas retransmis intégralement.

L'état EDSM est affiché directement en haut de la vue d'ensemble. Un
indicateur vert signale un transfert fonctionnel ; les erreurs sont
affichées en rouge et consignées en plus dans le journal de CMDRHelper.

## Base de données locale

CMDRHelper utilise SQLite. Les règles suivantes s'appliquent :

-   `cmdrhelper/database.py` est du code du programme et fait partie de
    la release.
-   `data/cmdrhelper.db` contient des données personnelles du Commander
    et **n'est pas** distribué.
-   Lors d'une nouvelle installation, la base de données locale est
    reconstruite pour l'utilisateur concerné.

Ainsi, aucune donnée personnelle du Commander n'est fournie avec une
release.

## Diagnostic et fichier journal

CMDRHelper tient son propre fichier journal rotatif pour le diagnostic
et la recherche d'erreurs. Les événements importants du programme, du
Journal, de la base de données et d'EDSM sont consignés. La
journalisation EDSM a été réduite afin que les événements Journal
simplement rejetés par EDSM ne remplissent pas inutilement le journal
normal, tandis que les transferts réussis, les avertissements et les
erreurs restent visibles.

## Plateformes

CMDRHelper est développé avec Python et PySide6 et est destiné à **Linux
et Windows**. Le développement est principalement effectué sous Linux ;
Windows peut être configuré à l'aide des fichiers batch fournis.

## Prérequis

Python 3 ainsi que les paquets indiqués dans `requirements.txt` :

``` text
PySide6>=6.7,<7
numpy
Pillow>=10.0
```

## Installation sous Linux

``` bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Les scripts de démarrage Linux existants peuvent également être
utilisés.

## Installation sous Windows

Pour Windows, `install.bat` et `start.bat` sont prévus.

`install.bat` vérifie Python 3, crée `venv`, met pip à jour et installe
`requirements.txt`. CMDRHelper est ensuite lancé via `start.bat`.

## Créer une release

``` bash
./create_release.sh
```

La version de la release est définie directement dans le script. Le ZIP
généré contient le code du programme et les assets, mais aucune base de
données personnelle, aucun environnement Python virtuel ni fichier Git,
cache ou éditeur.

## Version 2.0

La **version 2.0** apporte une véritable prise en charge Multi-CMDR tout en
conservant le planificateur d’itinéraires de la version 1.5 et les fonctions
existantes.

### Multi-CMDR et Vue CMDR

-   les Commanders sont identifiés automatiquement par leur FID Frontier. Le
    Commander en direct dépend uniquement du Journal ; consulter un autre
    profil ne modifie ni l’attribution ni les écritures en direct.
-   visites, exploration, missions, positions, vaisseaux, Fleet Carrier,
    fortune et données biologiques et cartographiques invendues sont séparés
    pour chaque Commander.
-   la **Vue CMDR** permet de consulter hors ligne tout Commander connu :
    missions, dernière position et dernier vaisseau, Fleet Carrier et sa
    position, fortune et estimations des données invendues.

### Chronique Multi-CMDR

-   chaque Commander possède une couleur stable et des filtres individuels
    ou communs.
-   les itinéraires chronologiques restent séparés et ne relient jamais les
    sauts de Commanders différents.
-   les systèmes visités par plusieurs Commanders affichent plusieurs visites.

### Flottes des Commanders

-   chaque Commander possède une flotte persistante avec tous ses vaisseaux
    connus et des détails dépliables sur l’équipement, la portée, les
    réservoirs, la cargaison et la dernière position.
-   le vaisseau en direct est vert ; les autres reçoivent des couleurs stables
    selon leur position, avec défilement vertical pour les grandes flottes.
-   combinaisons, SRV Scarab, Scorpion et Nomad, chasseurs embarqués, taxis et
    navettes de débarquement ne sont pas enregistrés comme vaisseaux normaux.

### Bases de données existantes

Les migrations de schéma intégrées conservent les bases existantes. Les
données Multi-CMDR sont séparées par FID Frontier. Si d’anciennes données
peuvent appartenir à plusieurs profils, CMDRHelper ne devine pas et ne les
supprime pas globalement : une attribution ambiguë reste non résolue.

CMDRHelper prend toujours en charge **Linux et Windows** et inclut le
planificateur pour vaisseaux et Fleet Carriers de la version 1.5.

## Version 1.5

La **version 1.5** est une mise à jour fonctionnelle majeure. Elle ajoute le
nouveau planificateur d’itinéraires pour les vaisseaux et Fleet Carriers,
relie plus étroitement la progression au Journal d’Elite Dangerous et
améliore sa fiabilité et ses performances, notamment sous Windows.

### Planificateur et itinéraires de vaisseau

-   le nouveau **Planificateur d’itinéraires** calcule les trajets de
    vaisseau avec le Spansh Galaxy Plotter et affiche tous les systèmes
    intermédiaires dans CMDRHelper.
-   CMDRHelper détecte dans le Journal le vaisseau, le FSD, son engineering
    et le Guardian FSD Booster actif. Les valeurs de réservoir, cargaison,
    masse et FSD disponibles sont reprises automatiquement.
-   les valeurs détectées restent modifiables. Les remplacements manuels sont
    conservés lors des mises à jour ultérieures du Loadout, de la cargaison
    et du carburant, jusqu’à une nouvelle application explicite des données.
-   les changements de Loadout, cargaison et carburant ne mettent à jour que
    les entrées concernées. Les valeurs inconnues restent visiblement vides
    et ne sont pas estimées.
-   les systèmes de départ et d’arrivée sont vérifiés par correspondance
    exacte auprès de Spansh avant le calcul, avec un message compréhensible
    lorsqu’un système est inconnu.
-   la progression utilise les véritables événements `FSDJump` du Journal.
    Après un saut réussi, le prochain système est copié automatiquement dans
    le presse-papiers Qt et peut aussi être recopié manuellement.

### Fleet Carrier et CTSVision

-   un mode **Fleet Carrier / CTSVision** dédié utilise le Spansh Fleet
    Carrier Router.
-   les routes calculées contiennent les informations de saut et de Tritium
    et peuvent être exportées en CSV compatible avec CTSVision.

### Fiabilité du Journal et performances

-   une erreur d’accès temporaire au Journal actif ne valide plus la mise à
    jour prématurément : le cycle normal de surveillance réessaie sans boucle
    d’attente agressive.
-   l’apprentissage BIO et cartographique ne reparcourt plus l’intégralité
    des Journals pour des événements ordinaires sans rapport. Les analyses
    complètes sont limitées aux événements BIO ou de vente pertinents et à
    l’import d’archives prévu.
-   cela réduit le travail effectué à chaque ajout au Journal et améliore la
    fiabilité et la réactivité, particulièrement sous Windows.

## Version 1.0.8

La **version 1.0.8** ajoute une recommandation de saut personnelle pour
l’exploration, complète l’internationalisation et améliore les fenêtres
Explorer en direct ainsi que l’affichage de la carte de la Chronique.

### Conseil et recommandation de saut

-   la nouvelle section **« Conseil de saut »** analyse votre propre base de
    données d’exploration locale et indique quels codes de systèmes
    procéduraux peuvent être particulièrement intéressants pour une cible
    d’exploration donnée.
-   les cibles disponibles comprennent notamment les découvertes BIO en
    général, les genres et espèces BIO connus, les corps d’exploration de
    grande valeur, les candidats à la terraformation, les mondes aquatiques,
    les mondes de type terrestre et les mondes ammoniacaux.
-   le classement tient compte des systèmes déjà examinés avec un code, des
    résultats, du taux de réussite, des découvertes enregistrées et de la
    taille d’échantillon disponible. Un nombre minimal réglable de systèmes
    examinés évite de surévaluer les échantillons trop petits.
-   CMDRHelper met en évidence les codes à privilégier sur la carte
    galactique, par exemple des combinaisons telles que `ZL-Z b` ou `NR-C d`.
-   la recommandation repose exclusivement sur **votre propre historique
    d’exploration** et les découvertes qui y sont enregistrées. Elle fournit
    une orientation statistique et **ne garantit aucune découverte**.

### Internationalisation

-   l’internationalisation a encore été complétée et vérifiée par rapport à
    la référence allemande.
-   les **12 langues d’interface prises en charge** disposent désormais du
    même ensemble complet de **560 clés de traduction**.
-   les traductions nouvelles et auparavant manquantes pour le **conseil et
    la recommandation de saut** ont été ajoutées dans toutes les langues.
-   l’ensemble et l’ordre des clés ainsi que les paramètres de formatage ont
    été harmonisés dans tous les fichiers de langue.

### Fenêtres Explorer en direct et paramètres

-   les paramètres de l’Explorer comportent de nouvelles infobulles pour
    l’affichage automatique des fenêtres **« Corps de grande valeur »** et
    **« Découvertes BIO »**.
-   ces infobulles expliquent quand chaque fenêtre apparaît automatiquement
    selon le seuil de valeur défini ou les signaux BIO ou GEO détectés.
-   les corps de grande valeur déjà cartographiés par le Commander ne sont
    plus présentés comme des cibles ouvertes dans la petite fenêtre.
-   les corps BIO entièrement analysés disparaissent de la fenêtre BIO ; une
    composante GEO du même corps qui n’a pas encore été cartographiée au DSS
    reste visible.

### Chronique

-   l’orientation de la carte de la Chronique a été corrigée afin que l’axe
    Z positif pointe vers le haut. Les coordonnées Elite `StarPos`
    enregistrées restent inchangées.

## Version 1.0

Avec la **Version 1.0**, CMDRHelper atteint le premier état de
développement complet de l'étendue de base prévue.

Modifications et extensions importantes jusqu'à la Version 1.0 :

### Représentation des corps et des étoiles complétée

-   le matériel graphique pour les types de planètes, d'étoiles et
    d'objets spéciaux pris en charge a encore été complété.
-   des classes d'étoiles supplémentaires et des types d'étoiles
    particuliers sont représentés avec leurs propres graphismes au lieu
    de revenir à la représentation standard générale.
-   pour les corps appropriés, des textures équirectangulaires 2:1 en
    rotation restent disponibles dans la vue détaillée.
-   des objets astronomiques particuliers peuvent également être
    représentés dans la vue détaillée à l'aide de vidéos adaptées.
-   les étoiles à neutrons, les naines blanches, les trous noirs et les
    trous noirs supermassifs bénéficient ainsi d'une représentation
    nettement plus individuelle.
-   les images et vidéos externes utilisées sont documentées avec leur
    source et leur crédit dans la section **« Images et vidéos / Media
    Credits »**.

### Multilinguisme complété

-   les traductions de l'interface utilisateur ont été complétées pour
    les langues prises en charge et harmonisées avec un ensemble commun
    de clés.
-   les **12 langues de l'interface** utilisent le même ensemble complet
    de clés de traduction.
-   le contrôle automatique des traductions vérifie les clés manquantes,
    supplémentaires et dupliquées ainsi que les placeholders de
    formatage divergents.
-   l'allemand sert de référence entièrement maintenue pour l'interface
    utilisateur et la documentation future.

### Modifications depuis la Version 0.9.9

### Multilinguisme et contrôle des traductions

-   l'interface utilisateur a été convertie vers un système multilingue
    centralisé.
-   CMDRHelper prend désormais en charge **12 langues d'interface** :
    **allemand, anglais, français, italien, norvégien (Bokmål), suédois,
    finnois, polonais, néerlandais, espagnol, turc et grec**.
-   la langue peut être sélectionnée et enregistrée dans les paramètres
    ; les noms des langues sont affichés dans le champ de sélection
    chacun dans sa propre langue.
-   les traductions manquantes utilisent un ordre de fallback défini :
    **langue sélectionnée → anglais → allemand → clé de traduction**.
-   les traductions sont centralisées dans les fichiers de langue sous
    `cmdrhelper/i18n/`.
-   le nouvel outil de développement `tools/check_i18n.py` vérifie
    automatiquement :
    -   les clés `tr("...")` utilisées dans le programme,
    -   les clés de traduction manquantes ou supplémentaires,
    -   les clés dupliquées,
    -   les placeholders de formatage divergents tels que `{system}` ou
        `{count}`.
-   sous Linux, le contrôle i18n est exécuté automatiquement au
    démarrage via `start.sh`. Les problèmes de traduction détectés sont
    clairement signalés, mais n'empêchent pas le démarrage du programme.
-   le traitement des missions et du Journal reste séparé de la langue
    d'interface choisie dans CMDRHelper afin que les données internes
    d'Elite Dangerous ne dépendent pas de textes d'affichage localisés.

### Explorer et carte du système

-   la structure Parent/Child de la carte du système a été remaniée :
    étoiles, planètes, lunes et Belt Clusters sont disposés selon leur
    hiérarchie Journal.
-   nouvelle fonction **« Tout afficher »** avec une vue miniature
    compacte de l'ensemble du système.
-   les corps peuvent être cliqués dans la vue miniature ; la carte
    principale passe ensuite directement au corps sélectionné.
-   navigation améliorée dans les grandes cartes de systèmes :
    -   la molette de la souris déplace la carte horizontalement.
    -   maintenir le bouton droit de la souris enfoncé et faire glisser
        vers le haut/bas déplace la carte verticalement.
-   les tailles visuelles des corps sont davantage mises à l'échelle en
    fonction de leur rayon réel.
-   l'affichage et le marquage de BIO, GEO, Terraforming, première
    découverte et First Mapping ont encore été améliorés.
-   nouvelle **liste de valeurs** dans Explorer : les planètes et les
    lunes sont triées ligne par ligne selon leur valeur de cartographie
    estimée actuelle.
-   la liste de valeurs distingue désormais clairement **First Mapping
    possible**, **déjà cartographié** et **cartographié
    personnellement**.
-   la valeur de cartographie actuellement obtenue est volontairement
    mise en évidence dans la liste de valeurs, tandis que l'état et les
    métadonnées sont affichés de manière plus discrète.
-   nouvel affichage **« Pas encore remis »** pour les valeurs de
    cartographie et BIO encore ouvertes dans tous les systèmes depuis la
    dernière vente ; la cartographie et BIO sont réinitialisées
    séparément.
-   les valeurs Explorer encore ouvertes sont mises en évidence en jaune
    dans la fenêtre principale afin que les données pas encore vendues
    soient immédiatement reconnaissables.

### Fenêtres live d'Explorer

-   nouvelles **fenêtres live librement positionnables pour les corps de
    valeur et les découvertes BIO**, qui apparaissent automatiquement
    pendant l'exploration.
-   la position et la taille des fenêtres live sont enregistrées et
    réutilisées lors de leur prochaine apparition.
-   lors du passage dans un autre système stellaire, les fenêtres live
    sont automatiquement fermées et vidées ; elles ne réapparaissent que
    lorsque des données appropriées sont détectées dans le nouveau
    système.
-   la fenêtre **« Corps de valeur »** reprend automatiquement toutes
    les planètes et lunes dont la valeur de cartographie actuellement
    accessible atteint le seuil sélectionné dans les paramètres.
-   le même seuil réglable contrôle désormais la mise en évidence jaune
    de la liste de valeurs, la fenêtre live des corps de valeur et le
    **cadre doré de la carte du système**.
-   la **fenêtre live BIO** affiche de façon compacte pendant le jeu les
    corps, les genres ou espèces reconnus, la progression du scan et les
    valeurs Vista Genomics connues.
-   les découvertes BIO utilisent la même logique de couleurs que dans
    la fenêtre principale : gris = détecté par DSS/FSS, blanc = premier
    échantillon, jaune = deuxième échantillon, vert = analyse terminée.
-   pour les signaux BIO partiellement déterminés, une planète se
    déploie automatiquement et affiche les différentes découvertes sur
    des lignes séparées ; les signaux encore inconnus restent visibles.
-   dès que toutes les espèces BIO d'un corps ont été entièrement
    analysées, la planète est à nouveau réduite à une ligne de résumé
    verte et compacte.
-   les noms génériques de genres DSS/FSS sont automatiquement remplacés
    par l'espèce BIO concrète dès qu'elle est connue via `ScanOrganic`.
-   les valeurs individuelles connues sont affichées directement avec la
    découverte BIO correspondante ; les corps entièrement connus
    affichent en plus la valeur totale.
-   les fenêtres live disposent d'un fond rouge-brun discret afin de se
    distinguer clairement de la fenêtre principale de CMDRHelper pendant
    le jeu.

### Analyse BIO

-   les données biologiques sont analysées et affichées séparément des
    valeurs de cartographie normales.
-   une **liste de planètes BIO** distincte contient tous les corps sur
    lesquels des signaux biologiques ont été détectés.
-   les genres BIO provenant de `SAASignalsFound` ou `FSSBodySignals`
    sont également repris rétroactivement à partir des Journaux
    existants.
-   les espèces et variantes BIO concrètes provenant de `ScanOrganic`
    sont affichées directement dans la liste.
-   la progression du scan de chaque découverte BIO est indiquée par des
    couleurs :
    -   gris = connu uniquement par DSS/FSS
    -   blanc = premier échantillon
    -   jaune = deuxième échantillon
    -   vert = troisième échantillon / analyse terminée
-   la valeur de base Vista Genomics connue est affichée dès qu'une
    espèce BIO est identifiée sans ambiguïté.
-   affichage de la valeur de base des échantillons BIO entièrement
    analysés.
-   affichage de la **valeur totale First Logged possible ×5**.
-   les valeurs BIO connues peuvent être complétées à partir de données
    de vente existantes.
-   les espèces dont la valeur est inconnue sont signalées dans
    l'analyse.
-   l'état BIO distingue les états ouvert, visité et entièrement
    analysé.

### Missions

-   amélioration du traitement de `MissionRedirected`.
-   les missions redirigées peuvent reprendre le nom, le nouveau système
    cible ou la nouvelle station cible ainsi que les informations sur la
    cible précédente.
-   dans certains cas, les missions peuvent également être reconstruites
    lorsqu'aucune entrée `MissionAccepted` complète n'était auparavant
    disponible.
-   la largeur des colonnes de mission peut être réglée librement ; les
    largeurs choisies sont enregistrées.
-   affichage de la **récompense totale de toutes les missions
    actuellement ouvertes**.

### Images et captures d'écran

-   espace dédié aux captures d'écran avec galerie et aperçu.
-   conversion automatique des nouvelles captures BMP d'Elite Dangerous.
-   sortie au format PNG ou JPG.
-   suppression facultative du fichier BMP après une conversion réussie.
-   correction de luminosité réglable de 0 à 50 %.
-   utilisation plus pratique du dossier de captures d'écran Elite sous
    Steam/Proton.
-   la galerie est également actualisée après la suppression externe de
    fichiers.
-   meilleure visibilité des options de conversion automatique et de
    suppression.

### Services en ligne

-   le transfert automatique des Journaux vers EDSM est davantage
    intégré et visible via la zone d'état de la fenêtre principale.
-   états pour transfert, attente, erreur et EDSM désactivé.
-   affichage de l'état Inara en préparation d'un futur transfert
    automatique.

### Utilisation et stabilité

-   la police et la taille de police de l'interface peuvent être
    sélectionnées dans les paramètres et appliquées à toute l'interface
    après un redémarrage.
-   la page des paramètres peut défiler afin que toutes les options
    restent accessibles même avec des fenêtres plus petites.
-   bouton **« Quitter »** visible dans la barre latérale gauche.
-   le verrouillage Single Instance empêche le lancement accidentel
    simultané d'une deuxième instance du programme.
-   vue miniature sûre du système sans rendu direct du widget Explorer
    déjà visible.
-   diverses améliorations de l'interface, du traitement du Journal, de
    la base de données et du processus de mise à jour.

## État du projet

CMDRHelper est en cours de développement. L'interface utilisateur, le
modèle de données et la représentation peuvent encore évoluer. D'autres
types de corps, fonctions Journal, fonctions Explorer, sources de
données et calculs sont prévus. Linux et Windows continuent d'être
testés.

CMDRHelper est né comme outil personnel et évolue progressivement vers
un helper Elite Dangerous plus complet.

## Images et vidéos / Media Credits

CMDRHelper utilise, pour certains objets astronomiques particuliers, des
visualisations du **NASA Scientific Visualization Studio (NASA SVS)**.
Les médias concernés restent la propriété de leurs ayants droit et les
crédits sont indiqués conformément aux informations fournies sur les
pages NASA SVS.

### Étoile à neutrons

-   Fichier CMDRHelper : `star_neutron.webm`
-   Source : NASA Scientific Visualization Studio, **Neutron Star
    Animations** (SVS ID 20267)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animateurs : Walt Feimer (KBR Wyle Services, LLC) et Lisa Poje
    (USRA)
-   Source : https://svs.gsfc.nasa.gov/20267/

### Trou noir

-   Fichier CMDRHelper : `black_hole.mp4` ou l'extension vidéo utilisée
    dans le projet
-   Source : NASA Scientific Visualization Studio, **Black Hole
    Accretion Disk Visualization** (SVS ID 13326)
-   Credit: **NASA's Goddard Space Flight Center/Jeremy Schnittman**
-   Source : https://svs.gsfc.nasa.gov/13326/

### Trou noir supermassif

-   Fichier CMDRHelper : `black_hole_supermassive.mp4` ou l'extension
    vidéo utilisée dans le projet
-   Source : NASA Scientific Visualization Studio (SVS ID 14576)
-   Credit: **NASA's Goddard Space Flight Center/J. Schnittman and B.
    Powell**
-   Source : https://svs.gsfc.nasa.gov/14576/

### Naine blanche

-   Fichier CMDRHelper : `star_white_dwarf.webm`
-   média NASA utilisé : **White Dwarf establishing shot**
    (`WDStar_4k_60fps_ProRes.webm`)
-   Source : NASA Scientific Visualization Studio, **Type Ia Supernovae
    Animations** (SVS ID 20344)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animatrice : Adriana Manrique Gutierrez (USRA)
-   Producer: Scott Wiessinger (USRA)
-   Source : https://svs.gsfc.nasa.gov/20344/

La mention de ces sources et crédits ne signifie pas que CMDRHelper est
soutenu, certifié ou publié par la NASA. Pour toute réutilisation des
médias de la NASA, les indications et directives de reproduction des
sources originales s'appliquent.

## Licence

CMDRHelper est un logiciel libre publié sous la **GNU General Public
License Version 3 (GPL-3.0)**.

Le code source peut être utilisé, modifié et redistribué conformément
aux conditions de la GPL-3.0. La distribution de versions dérivées est
également soumise aux conditions de la GPL-3.0.

Copyright © 2026 **Holger Mangold (Faber38)**.

Les conditions complètes de la licence se trouvent dans le fichier
`LICENSE`.

## Remarque concernant Elite Dangerous

CMDRHelper est un projet communautaire/de loisir indépendant et n'est
pas un produit officiel de Frontier Developments.

**Elite Dangerous** ainsi que les noms et contenus associés
appartiennent à leurs ayants droit respectifs.
