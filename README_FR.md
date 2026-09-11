# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) \| [🇬🇧 English](README.md) \| [🇫🇷
Français](README_FR.md) \| [🇮🇹 Italiano](README_IT.md) \| [🇳🇴
Norsk](README_NO.md) \| [🇸🇪 Svenska](README_SV.md) \| [🇫🇮
Suomi](README_FI.md) \| [🇵🇱 Polski](README_PL.md) \| [🇳🇱
Nederlands](README_NL.md) \| [🇪🇸 Español](README_ES.md) \| [🇹🇷
Türkçe](README_TR.md) \| [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper -- Votre copilote pour Elite Dangerous](cmdrhelper/assets/readme/cmdrhelper_readme_fr.png)

**Compagnon personnel pour Elite Dangerous – exploration, navigation et données du commandant en un coup d’œil**

CMDRHelper est une application de bureau autonome qui analyse les journaux locaux d’Elite Dangerous et utilise les données de position planétaire de `Status.json`. Elle t’aide à repérer les corps intéressants, à retrouver des lieux enregistrés et à consulter tes voyages et découvertes. Les données personnelles sont conservées après un redémarrage et séparées par commandant.

## Nouveautés de la version 3.3

- Nouvelle analyse de système fondée sur votre expérience personnelle d’exploration.
- Mode de jeu Ouvert / Solo / Groupe privé directement dans la vue d’ensemble.
- Copiez les noms des systèmes récents en un clic.
- Données historiques et analyse plus claires et plus compréhensibles.
- Import des archives de journaux plus fiable lorsque les fichiers sont complétés ultérieurement.

L’ancien conseil de saut devient Analyse, avec l’analyse de système et les données historiques toujours disponibles. L’analyse compare une cible à votre historique personnel : le code de masse fournit l’estimation de base, affinée prudemment par la région et la famille. Un indice de potentiel de 100 correspond à votre moyenne historique personnelle du potentiel d’exploration atténué, pas à une probabilité en pourcentage. La base de données de comparaison et sa fiabilité restent distinctes de l’évaluation ; le numéro final n’influence pas le score et BIO reste uniquement informatif.

## Nouveautés de v3.2 par rapport à v3.1

- Gestion des matériaux d’ingénierie : les 146 matériaux Raw, Manufactured et Encoded, avec grades, capacités et cas particuliers. Stocks actualisés par commandant, recherche, filtres, cinq fonds de ligne discrets et mémorisation de la largeur et de l’ordre des colonnes. Un stock inconnu reste distinct de zéro.

- Inventaire Odyssey : le quatrième onglet contient 223 identités de catalogue pour les biens, composants, données et consommables. Casier, sac à dos et total fiable restent distincts ; lots de mission, statut et usages en ingénierie sont visibles. Les quantités positives apparaissent en doré. Les noms non traduits utilisent l’anglais.

- Recherche de marchands de matériaux  (Chercher un négociant → Ouvrir le planificateur): sur demande, Spansh recherche séparément Raw, Manufactured et Encoded depuis le système actuel du commandant. Les carriers sont exclus et les détails des stations vérifiés. La distance en ly est directe entre systèmes ; les données communautaires ne garantissent pas l’accès. Le transfert au planificateur définit seulement le système cible, sans lancer de route. Aucune recherche de marchands Odyssey.

- Vue d’ensemble du système : la nouvelle présentation inspirée d’Elite remplace l’ancienne miniature dans Explorer et la Chronique. Étoiles et planètes forment la structure principale, les lunes se ramifient en dessous ; les systèmes multiples restent lisibles. Zoom, défilement, ajustement à la fenêtre et clic sur un corps donnent accès aux détails.

- Ceintures d’astéroïdes compactes : les amas sont regroupés en ceintures dans la vue d’ensemble et les cartes habituelles d’Explorer et de la Chronique. Toutes les données individuelles sont conservées.

- Cartographie corrigée : un scan après une cartographie DSS ne réinitialise plus les valeurs d’exploration invendues, l’heure de cartographie ni l’efficacité. Les créances incorrectes sont réparées au démarrage à partir des journaux disponibles et attribués sans ambiguïté. Sans ces sources, la réparation reste en attente ; inutile de supprimer la base.

- Planificateur amélioré : le départ suit automatiquement le système actuel jusqu’à votre saisie manuelle ; vider le champ réactive le suivi. Vaisseaux et carriers utilisent des adresses ID64 exactement vérifiées, sans choisir de noms similaires. « Unable to find route » indique qu’aucune route n’a été trouvée ; vérifiez destinations, portée et paramètres.

- Informations de mise à jour améliorées : la fenêtre Oui/Non affiche les versions installée et disponible et jusqu’à six nouveautés si un résumé existe. Les longues listes défilent et les actions restent accessibles. Cette présentation arrive avec v3.2 ; un client v3.1 inchangé ne l’affiche pas encore.

## v3.1 (v3.0.3 → v3.1)

- La progression BIO est compacte : 1/3 en jaune, 2/3 en bleu et 3/3 en vert ; l’état terminé « Terminé » est également vert. Sous « afficher automatiquement », GEO dispose de son propre interrupteur mémorisé : BIO seul, GEO seul ou les deux ensemble sont possibles. Les largeurs ajustées manuellement dans la table commune BIO / GEO / ABBAU de l’Explorateur sont conservées à la réouverture et au redémarrage. La restauration des largeurs des fenêtres contextuelles est plus robuste ; les valeurs invalides sont remplacées par des largeurs par défaut utilisables.

- Découverte et cartographie sont séparées et rapportées à votre scan : « Déjà découvert lors de votre scan » et « Déjà cartographié lors de votre scan ». Les données absentes restent Inconnues. Les candidats First Discovery et First Mapping concernent uniquement le moment du scan ; un ancien Non ne prouve pas que le corps reste à découvrir ou cartographier aujourd’hui. Votre cartographie ne confirme aucune attribution officielle de première découverte ou cartographie. La présence dans EDSM reste distincte.

- « HUD de statut EDSM », sous « afficher automatiquement », est DÉSACTIVÉ par défaut. Après l’entrée dans un système, un bref message apparaît sur Elite pendant environ 2,5 secondes. « EDSM : CONNU » signifie une correspondance EDSM valide pour le système. « EDSM : INCONNU » signifie une réponse EDSM valide sans correspondance. « EDSM : AUCUNE RÉPONSE » signifie une erreur réseau, HTTP, un délai dépassé ou une réponse invalide, jamais une absence de correspondance confirmée. La présence dans EDSM ne vaut pas découverte officielle dans Elite ; aucun nom de premier découvreur ou déclarant n’est promis. Le message fonctionne indépendamment des HUD de navigation et de soute.

- L’historique des visites tient compte de Location, FSDJump et CarrierJump lors du suivi du journal en direct. Plusieurs événements de position pendant un séjour ininterrompu comptent pour une visite : A → A → A compte une fois. Un véritable retour est conservé : A → B → C → A compte quatre visites.

- La fin de votre propre cartographie DSS enregistre désormais de manière fiable l’heure de cartographie, les sondes utilisées et l’objectif d’efficacité. Les scans ultérieurs ne font plus perdre les informations existantes.

- La fenêtre de soute adapte automatiquement sa hauteur au contenu. Avec de nombreuses entrées, la hauteur reste limitée et la table défile ; la largeur choisie et la position sont conservées. L’interrupteur existant « HUD de soute » se trouve désormais sous « afficher automatiquement », sans interrupteur supplémentaire dans la fenêtre de soute.

- Pour une installation existante, il suffit normalement d’installer la mise à jour → démarrer CMDRHelper. Les corrections historiques nécessaires des données BIO, des visites et des métadonnées DSS sont automatiques ; une sauvegarde de la base précède toute réparation écrivant des données. Les réparations sont versionnées et idempotentes : les révisions réussies ne sont pas entièrement réexécutées à chaque démarrage. La reconstruction exige des journaux Elite encore présents, lisibles et attribuables sans ambiguïté à un commandant. Les sources absentes ne sont ni inventées ni considérées comme un succès ; les réparations en attente sont retentées au démarrage suivant. Suppression de la base, scripts manuels et réimportation sont normalement inutiles.

## Explorer

L’Explorer présente le système actuel dans trois vues :

- **Carte du système :** représentation graphique des étoiles, planètes et lunes connues. Un clic sur un corps ouvre ses détails. « Tout afficher » ouvre la vue d’ensemble du système.
- **Liste des valeurs :** La liste des valeurs présente des estimations selon le scan enregistré, pas des paiements encore dus garantis. Les bonus de première découverte ou cartographie restent non confirmés. Les infobulles de la carte et de la liste ainsi que les détails du corps utilisent les mêmes états situés dans le temps.
- **BIO / GEO / EXTRACTION :** signaux biologiques et géologiques, sites d’extraction planétaires et découvertes personnelles attestées.

Les analyses distinguent les signaux signalés des découvertes personnelles réelles. **BIO ×N** indique le nombre de signaux signalés, pas la confirmation d’espèces entièrement analysées. **EXTRACTION ×N** compte les sites d’extraction planétaires sans révéler leurs ressources individuelles. Les marchandises personnellement extraites, les matériaux secondaires collectés pendant l’extraction et la composition générale en matériaux d’un corps restent séparés.

L’Explorer affiche aussi les valeurs BIO estimées, la progression des analyses personnelles et les données cartographiques et BIO non vendues. Les valeurs reposent sur les informations disponibles des journaux et des corps ; les données manquantes ne sont pas présentées comme des découvertes personnelles. Les données EDSM complémentaires sont des informations externes à distinguer des découvertes personnelles.

Les détails des corps comprennent les propriétés physiques disponibles, l’atmosphère, les anneaux, les matériaux et les informations de découverte. Les représentations utilisent des textures adaptées et des animations pour certains objets astronomiques particuliers. La rubrique Cargo affiche la cargaison et la capacité connues du vaisseau ou SRV actuellement utilisé ; pour le Rhino, cargaison et découvertes minières personnelles restent des données distinctes.

En haut de l’Explorer se trouvent **★ Favoris | Navigation planétaire | Tout afficher**. Les favoris et la navigation planétaire ouvrent leurs propres fenêtres ; les trois vues de l’Explorer restent disponibles.

## Navigation planétaire

Le navigateur planétaire sert exclusivement à rejoindre une **latitude/longitude précise sur une planète ou une lune**. Un planificateur d’itinéraire distinct est disponible pour les voyages entre systèmes stellaires.

### Saisir une cible et partir

Sélectionne le corps cible ou utilise le corps actuel, détecté automatiquement dans la mesure du possible. Saisis la latitude et la longitude et, éventuellement, un nom de cible. Tu n’as pas à saisir d’informations techniques comme BodyID ou SystemAddress. **0,0** est également une coordonnée valide.

Dès qu’Elite fournit des données de position planétaire valides pour le corps correspondant, le compas s’active automatiquement. Sans données correspondantes, le navigateur affiche un état d’attente. Tu peux définir à tout moment une nouvelle cible de coordonnées sur le même corps ; elle remplace la précédente.

### Affichage pendant l’approche

| Distance à la cible | Affichage |
| --- | --- |
| **Plus de 380 km** | Globe planétaire avec ta position représentée par un cercle blanc et la cible par un petit point. La cible est orange sur la face visible et rouge sur la face cachée. La position du joueur reste fixe dans l’affichage ; la planète et la cible sont représentées par rapport à elle. |
| **Jusqu’à 380 km inclus** | Passage automatique à une grille en perspective inclinée avec un **maillage de distance de 50 km** et la position de la cible tracée à l’intérieur pour poursuivre l’approche. |

La fenêtre du navigateur est librement redimensionnable. Le globe ou la grille en perspective s’adaptent proportionnellement à l’espace disponible ; les valeurs détaillées restent lisibles.

### Comprendre les valeurs de navigation

- **Coordonnées de la cible :** latitude et longitude enregistrées de la cible.
- **Coordonnées actuelles :** ta dernière position planétaire valide.
- **Distance à la cible / Distance en surface :** distance calculée jusqu’à la cible sur la surface sphérique ; la grande indication de distance et la valeur détaillée montrent la même distance avec un arrondi différent.
- **Relèvement :** direction absolue de la position actuelle vers la cible.
- **Heading :** ton orientation actuelle signalée par Elite.
- **Direction relative :** écart entre le heading et le relèvement, par exemple « 23° à droite », « à gauche » ou « tout droit ».
- **Cap cible :** cap absolu vers lequel tu peux tourner dans le HUD d’Elite. Il correspond au relèvement et n’est pas un angle de rotation relatif supplémentaire.

Exemple : **Heading 051° → Cap cible 074° = 23° à droite**.

La navigation dépend des données d’état du jeu ; les mises à jour peuvent arriver avec retard selon l’état du jeu. La distance en surface n’est pas un itinéraire routier ou tenant compte du terrain. Les obstacles et les altitudes du terrain sur le trajet ne sont pas pris en compte.

## HUD de navigation

À gauche, sous **afficher automatiquement → HUD de navigation**, tu peux activer un affichage supplémentaire facultatif directement sur Elite. Lorsque la navigation planétaire est valide, il indique :

- la direction relative,
- le cap cible absolu,
- la distance.

Le HUD est transparent, laisse passer les clics et ne prend pas le focus : il ne détourne ni les clics de souris ni la saisie du jeu. Sans navigation valide, il devient automatiquement invisible ; la case de la barre latérale peut rester cochée. Le navigateur normal fonctionne indépendamment du HUD.

Le HUD a été testé en jeu sous **Linux/X11** et **Windows 11 avec Elite**. Sous Windows, l’association de plusieurs moniteurs utilise leur géométrie et la position de la fenêtre Elite, pas la correspondance de leurs noms.

## Favoris

**Explorer → ★ Favoris** ouvre une fenêtre distincte et réutilisable. Les favoris appartiennent au **commandant actif**. Un changement de commandant actualise la vue ; la sélection des commandants dans la chronique n’étend pas la liste des favoris.

### Enregistrer trois types

La rangée d’actions supérieure propose :

| Action | Favori enregistré |
| --- | --- |
| **★ Enregistrer le système actuel** | Le système actuel, sans coordonnées de surface. |
| **★ Enregistrer une planète / lune** | Une planète ou lune connue sélectionnée dans le système actuel, sans coordonnées de surface. |
| **★ Enregistrer la position actuelle** | Un lieu en surface avec le système, le corps, la latitude et la longitude actuels. |

Le bouton de position reste toujours visible et n’est disponible qu’avec des données de position planétaire actuelles valides et un commandant actif. **Le clic fige le commandant, le système, le corps et les coordonnées avant l’ouverture du dialogue de modification.** Les déplacements ultérieurs dans le jeu ne changent pas cette position. Le même mécanisme d’enregistrement est disponible dans le navigateur planétaire. Les identifiants internes connus sont repris automatiquement ; aucune coordonnée n’est inventée.

Choisis un nom et exactement une catégorie : **Bio, Géo, Extraction, Panorama, Site d’atterrissage, Intéressant ou Autre**. Une note et une image sont facultatives.

### Rechercher, consulter et modifier

La liste défilante, triée alphabétiquement par nom, affiche nom, type, système, corps et coordonnées le cas échéant, catégorie et petit aperçu d’image. **Recherche en texte libre et filtres de type et de catégorie** sont combinables. La recherche porte sur le nom, le système, le corps et la note.

**Ouvrir / Afficher** montre les informations enregistrées, la note et un aperçu plus grand. **Afficher dans l’Explorer** utilise la vue d’ensemble du système ou la fiche du corps existante si le favori appartient au système actuel de l’Explorer et si les données correspondantes sont disponibles. Pour les autres systèmes, les informations enregistrées du favori restent disponibles.

**Modifier** change le nom, la catégorie, la note et l’image. Le système, le corps et les coordonnées enregistrées ne sont pas remplacés par des valeurs en direct. Pour une autre position, crée un nouveau favori de surface.

**Supprimer** demande une confirmation et ne retire que l’enregistrement du favori et sa copie d’image interne. Les données de l’Explorer, du journal et des corps sont conservées.

### Images des favoris et dernière capture

Les images des favoris sont **entièrement séparées de la rubrique Images normale**. CMDRHelper gère sa propre copie interne dans le dossier d’images des favoris (`data/favorites/images/` dans l’organisation habituelle des données). L’original n’est ni déplacé ni modifié.

- **Choisir une image …** accepte PNG, JPEG ou WebP et affiche un aperçu. La copie interne n’est créée qu’à l’enregistrement.
- **Utiliser la dernière capture** relit le dossier source réel des captures à chaque clic. Il prend aussi en compte les captures Elite converties correspondantes dans le dossier du commandant actif à l’intérieur de la destination de conversion configurée. Une nouvelle capture reste ainsi disponible si la conversion automatique a déjà supprimé son BMP.
- Seuls des fichiers lisibles aux noms Elite ou de conversion correspondants sont proposés, pas des images quelconques de dossiers généraux. L’ordre utilise une heure de capture non ambiguë dans le nom de fichier, sinon la date du fichier. Pour les images converties, l’heure de capture enregistrée dans le nom est utilisée, pas celle de la conversion.
- Avant d’accepter une capture trouvée, tu vois le nom du fichier, la date et l’heure de capture et un aperçu fraîchement chargé. Confirme avec **Utiliser cette image**. Sans capture appropriée, la sélection manuelle reste disponible. CMDRHelper ne déclenche pas lui-même de capture.

Une image peut être remplacée ou retirée ultérieurement. Les copies internes inutilisées sont supprimées à l’enregistrement ou à la suppression du favori. **Les actions sur les favoris ne suppriment jamais la capture originale ni une image originale sélectionnée.** Si un fichier image interne manque, le favori reste utilisable sans aperçu.

### Favori de surface comme cible

**▶ Aller à la cible** transmet le corps, la latitude, la longitude et le nom du favori enregistrés au navigateur planétaire existant et remplace sa cible précédente. Les favoris n’ont aucune logique de navigation propre. Des données planétaires valides et correspondantes lancent la navigation ; sinon, le navigateur attend comme d’habitude.

Les favoris d’autres commandants ne peuvent pas servir de cibles personnelles. Un changement de commandant arrête une cible encore gérée comme cible favorite du commandant précédent. Les favoris de système et de corps affichent des informations existantes ; ils ne planifient pas leurs propres itinéraires.

## Chronique

La chronique conserve l’historique de tes voyages et découvertes. Sa **carte de voyage 3D** affiche les systèmes visités et les itinéraires des commandants. Les détails des systèmes et corps aident à retrouver les informations connues sur BIO, GEO, matériaux, Codex et extraction.

### Filtres combinés

**Appliquer** ou **Entrée dans le champ de texte libre** exécute ensemble tous les filtres définis :

- texte libre,
- éventuellement **Du** et **Au**,
- **Sites miniers planétaires** et **Au moins**,
- **Mes découvertes minières** et **Marchandise**.

Un terme de **Aide à la recherche / Légende** est repris dans le champ de recherche et exécuté avec les filtres de période et d’extraction déjà définis.

### Période en UTC

Du et Au s’activent chacun par leur case. Une seule borne est possible ; sans case activée, aucune restriction temporelle ne s’applique de ce côté. **Du** inclut le début du jour calendaire UTC choisi. **Au** inclut la totalité du jour UTC choisi. UTC est la base de temps commune, pas ton heure calendaire locale.

Les **visites réelles de systèmes** font foi : au moins une visite enregistrée doit être dans la période. Le simple fait qu’un système soit connu pour la première ou la dernière fois ne remplace pas une visite. Avec une période active, le nombre de visites ainsi que la première et la dernière visite sur la carte concernent les visites filtrées.

La période filtre les visites, pas les événements individuels de découverte, BIO, GEO ou d’extraction. Les informations de découverte connues et les quantités minières personnelles restent des **totaux** enregistrés. **« Cuivre 56 t » avec une période active ne signifie pas automatiquement « 56 t pendant cette période ».** Si Du est postérieur à Au, un message d’erreur apparaît ; aucune requête à la base n’est lancée.

### Commandant et actualisation

La **sélection des commandants de la carte** détermine les itinéraires affichés. Les recherches personnelles de texte libre et d’extraction concernent en revanche le commandant consulté ou actif. Les cases de la carte n’étendent pas automatiquement les recherches personnelles à plusieurs commandants.

**Actualiser la chronique** recharge les données et réexécute les filtres actifs. **Position actuelle** applique d’abord l’état actuel des filtres et ne centre sur le système actuel que s’il figure dans la carte résultante. Sinon, un message apparaît ; les filtres restent en place.

**Réinitialiser** vide le texte libre, désactive Du/Au et réinitialise les champs de date visibles. Les cases d’extraction sont décochées, le nombre minimum passe à 0 et la marchandise à Toutes. La sélection des commandants est conservée ; la chronique normale est ensuite chargée.

Avec **aucun résultat**, la carte et les itinéraires sont vidés, la liste des résultats est vidée et masquée, les détails sont réinitialisés et toute fenêtre de détails de système de la chronique ouverte est fermée. Les anciens résultats ne restent pas affichés.

### Manipuler la carte

- Glisser avec le bouton gauche : tourner.
- Glisser avec le bouton droit : déplacer.
- Glisser avec le bouton central : tracer une fenêtre de zoom.
- Molette : zoomer.
- **Aligner:** rétablir l’orientation en vue galactique de dessus ; déplacement et zoom sont conservés.

## Images et conversion automatique des captures

Dans **Images**, tu règles le dossier source des captures Elite et la destination de conversion. La conversion automatique transforme les nouveaux BMP en **PNG ou JPEG**. Un éclaircissement réglable est disponible. Les BMP déjà présents au démarrage ne sont pas rétroactivement convertis par la seule activation de la surveillance ; une conversion manuelle est prévue pour eux.

Les noms des fichiers convertis contiennent l’heure de capture, le commandant et le système, et les fichiers sont rangés par commandant. L’attribution automatique suit le commandant du journal actif. Une autre sélection dans la galerie ne change pas ce commandant actif.

L’option de **suppression du BMP original après conversion réussie** appartient exclusivement à cette conversion et possède son propre réglage. Elle est indépendante de la gestion des images des favoris.

La galerie affiche les images converties correspondantes avec aperçu. Elle est relue lorsqu’elle est affichée à nouveau ; l’actualisation tient également compte des fichiers actuels. Sélection et grand aperçu sont mis à jour ensemble. Si l’image sélectionnée disparaît, une image encore présente est sélectionnée ou l’aperçu est vidé. La rubrique Images possède aussi sa propre sélection d’images et sa fonction de suppression avec confirmation.

## Autres vues

- **Vue d’ensemble :** commandant actif, vaisseau, position, détection du journal, missions ouvertes et état en ligne.
- **Missions :** missions ouvertes enregistrées durablement avec cibles connues, progression et état d’achèvement. Les informations manquantes ne sont ni complétées ni inventées.
- **CMDR :** patrimoine, rangs, statistiques, MercCoins, vaisseaux/flotte et position connue du Fleet Carrier. Les MercCoins sont affichés comme totaux signalés par Frontier, pas comme solde calculé par l’application.
- **Planificateur d’itinéraire :** planification distincte pour vaisseau et Fleet Carrier avec Spansh. Les itinéraires de carrier calculés peuvent être exportés en CSV pour CTSVision. Le calcul nécessite une connexion au service externe.

## Commandant, données locales et services en ligne

CMDRHelper identifie le commandant actif par l’identifiant Frontier de la session de journal actuelle. Exploration personnelle, missions, patrimoine, favoris et accès en ligne sont stockés séparément. Consulter un autre commandant ne change ni le commandant en direct ni l’attribution de ses envois.

La base SQLite locale conserve systèmes, corps et historique personnel après les redémarrages. Les nouvelles entrées complètes du journal sont traitées pendant le jeu ; les positions de lecture enregistrées évitent des relectures inutiles. Si la position ou le commandant est incorrect, vérifie d’abord la détection du journal et son dossier dans les paramètres.

**EDSM** peut fournir des données système complémentaires. Les données de journal prises en charge peuvent être envoyées à **EDSM et Inara** si le service est configuré et activé avec les identifiants propres au commandant actif. Un commandant n’utilise pas automatiquement la clé API d’un autre. Le stockage local fonctionne indépendamment d’une connexion en ligne disponible.

## Langues et aide contextuelle

L’interface prend en charge **12 langues** : **DE, EN, FR, IT, NO, SV, FI, PL, NL, ES, TR, EL** – allemand, anglais, français, italien, norvégien, suédois, finnois, polonais, néerlandais, espagnol, turc et grec.

Il existe actuellement **937 clés UI-i18n par langue**. **? Aide** propose **10 rubriques détaillées d’aide contextuelle dans les 12 langues**. Les favoris font partie de l’aide Explorer ; la navigation planétaire possède sa propre rubrique, accessible directement depuis le navigateur. L’aide utilise la langue actuelle de l’interface et conserve l’allemand comme repli si un catalogue ou une entrée manque.

## Prérequis

| Plateforme | Python |
| --- | --- |
| **Windows** | **Python 3.10 ou plus récent, x64 obligatoire.** Aucune limite supérieure artificielle pour les versions existantes. Les vérifications réelles des paquets et imports sont ensuite déterminantes. |
| **Linux** | **Python 3.10 ou version ultérieure**, 64 bits recommandé. Le module venv correspondant à la version de Python doit être disponible. |

Les paquets requis figurent dans `requirements.txt` :

```text
PySide6>=6.7,<7
numpy
Pillow>=10.0
```

L’installation télécharge ces dépendances. Les fichiers Elite locaux doivent être accessibles pour analyser les journaux et naviguer sur les planètes. Sous Linux, Elite peut fonctionner via Steam/Proton ; les chemins réels des journaux et captures se règlent dans CMDRHelper. La prise en charge du HUD Linux décrite ci-dessus concerne X11.

## Installation sous Linux

Décompresse le projet ou la version complète et exécute dans le dossier du projet :

```bash
./install.sh
./start.sh
```

Les scripts utilisent exclusivement le `venv` local de cette installation. Ils résolvent les liens symboliques des scripts, vérifient Python et pip et peuvent réparer un environnement local endommagé sans toucher aux données personnelles ni aux journaux Elite. Les paquets système manquants ne sont pas installés automatiquement ; l’installateur signale un module venv absent. La procédure Linux existante reste inchangée.

## Installation sous Windows

1. Décompresse le ZIP complet dans un dossier dédié.
2. Lance **install.bat**, qui appelle le fichier fourni **install-windows.ps1**.
3. Après une installation réussie, lance CMDRHelper avec **start.bat**.

Une installation existante de **Python à partir de 3.10 x64** est acceptée sans plafond artificiel. Une future version de Python n’est pas rejetée uniquement à cause de son numéro. Un Python existant adapté ou un venv local utilisable évite une installation automatique inutile de Python.

Si aucun Python adapté n’est disponible, l’installateur propose, après accord, une installation automatique via **winget**. La série fixe **Python 3.14 x64** est volontairement choisie à cet effet ; ce choix est distinct de la règle ouverte pour les versions existantes. Si l’installation automatique est impossible, l’installateur signale l’erreur.

L’installateur crée, vérifie ou répare uniquement le **venv local de cette copie de CMDRHelper**, installe les dépendances et exécute **pip check** ainsi que des vérifications d’import de **PySide6, PySide6.QtWidgets, numpy et PIL**. Seules ces vérifications réelles déterminent si l’environnement est utilisable. En cas d’échec, l’installation s’arrête avec un message compréhensible. Les autres environnements virtuels ne sont ni réparés ni remplacés.

## Diagnostic et paquets de distribution

En cas de problème, les indicateurs de journal et d’état en ligne et les fichiers du dossier `logs` peuvent aider. Les données personnelles sont stockées localement ; une sauvegarde des favoris doit inclure leurs copies d’images internes en plus de la base de données.

`./create_release.sh` permet de créer ton propre paquet de distribution. La version du programme est gérée centralement dans `cmdrhelper/version.py` et lue par le script de distribution. Le paquet contient code et ressources, mais aucune base personnelle, aucun venv et aucun fichier Git ou cache.

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
