"""French content for contextual help."""


HELP_TOPICS = {
    "materials": (
        'Matériaux',
        """<h2>Matériaux</h2>
<h3>CMDRHelper</h3>
<p>Gestion des matériaux d’ingénierie : les 146 matériaux Raw, Manufactured et Encoded, avec grades, capacités et cas particuliers. Stocks actualisés par commandant, recherche, filtres, cinq fonds de ligne discrets et mémorisation de la largeur et de l’ordre des colonnes. Un stock inconnu reste distinct de zéro.</p>
<p>Inventaire Odyssey : le quatrième onglet contient 223 identités de catalogue pour les marchandises, matériaux, données et consommables. Casier, sac à dos et total fiable restent distincts ; lots de mission, statut et usages en ingénierie sont visibles. Les quantités positives apparaissent en doré. Les noms non traduits utilisent l’anglais.</p>
<p>Recherche de marchands de matériaux  (Chercher un négociant → Ouvrir le planificateur): sur demande, Spansh recherche séparément Raw, Manufactured et Encoded depuis le système actuel du commandant. Les carriers sont exclus et les détails des stations vérifiés. La distance en ly est directe entre systèmes ; les données communautaires ne garantissent pas l’accès. Le transfert au planificateur définit seulement le système cible, sans lancer de route. Aucune recherche de marchands Odyssey.</p>
<p>Cette rubrique principale affiche les matériaux d’ingénierie du commandant actuellement consulté. La sélection de la vue CMDR s’applique également ici ; les données des autres commandants restent séparées.</p>
<h3>Trois catégories</h3>
<p>Les onglets Matériaux bruts, Matériaux manufacturés et Données encodées contiennent les 146 matériaux du catalogue, y compris les matériaux Guardian et Thargoid. La liste est triée par grade, puis par ordre alphabétique au sein de chaque grade.</p>
<h3>Stock et barres</h3>
<p>Les nombres indiquent le stock / maximum, par exemple Vanadium 244 / 250. La barre correspondante indique 97,6 %. Les matériaux jamais possédés apparaissent également avec 0 lorsque le stock est connu de manière fiable.</p>
<p>Les stocks vides sont signalés en rouge discret, les stocks faibles en jaune/orange et les stocks presque pleins ou pleins en vert. Les nombres restent visibles indépendamment des couleurs.</p>
<h3>Recherche et filtres</h3>
<p>La recherche prend en compte le nom affiché et le nom anglais du matériau. Elle peut être combinée avec tous les filtres : Tous, Vide (0), Faible (plus de 0 jusqu’à 20 %), Presque plein (de 80 % à moins de 100 %) et Plein (100 %). Les valeurs entre 20 % et 80 % apparaissent uniquement sous Tous. Les onglets et filtres sont restaurés au prochain démarrage.</p>
<h3>Valeurs inconnues</h3>
<p>Sans inventaire complet fiable, l’affichage indique par exemple ? / 250. Si le maximum est inconnu, il peut indiquer 12 / ?. Dans les deux cas, aucun pourcentage ni aucune barre n’est affiché ; ces matériaux apparaissent uniquement sous Tous. Un grade inconnu figure dans un groupe distinct en fin de liste.</p>
<h3>Actualisation en direct</h3>
<p>Les nouveaux événements du journal actualisent automatiquement le stock, y compris après un échange de matériaux, une opération d’ingénierie, une synthèse ou une récompense en matériaux. Un message de chargement apparaît pendant la lecture initiale. Un matériau nouvellement collecté est brièvement mis en évidence avec une indication telle que Vanadium +1 ; la consommation ne produit pas de notification de collecte.</p>
<h3>Noms des matériaux</h3>
<p>Si le nom d’un matériau n’est pas encore disponible dans la langue choisie, son nom d’affichage anglais est utilisé. Les symboles internes du journal ne remplacent pas les noms d’affichage existants.</p>
<h3>Odyssey</h3>
<p>« Volé » marque une pile explicitement signalée comme volée dans les données Elite enregistrées. Une indication absente ne confirme pas que la pile n’est pas volée. Si un identifiant de propriétaire est connu, l’infobulle l’affiche sous « Propriétaire » ; aucun nom inconnu n’est ajouté.</p>
<p>L’infobulle « Disponibilité actuelle non confirmée » indique une source d’obtention non confirmée pour les matériaux spéciaux concernés. CMDRHelper ne peut fournir d’information actuelle vérifiée sur leur acquisition ; cela ne signifie pas que l’objet est introuvable.</p>

<p>Le quatrième onglet de Matériaux contient Marchandises, Matériaux, Données et Consommables. Le casier et le sac à dos affichent les stocks personnels. Porte-vaisseaux ✎ affiche le stock privé confirmé manuellement sur votre propre porte-vaisseaux pour les marchandises, matériaux et données. Double-cliquez pour confirmer, corriger ou définir comme inconnu. — signifie inconnu ; 0 doit être confirmé explicitement. La colonne « Total » inclut casier, sac à dos et porte-vaisseaux uniquement si les valeurs sont connues et cohérentes. Avec plusieurs lots, le stock du porte-vaisseaux apparaît une fois dans le récapitulatif ; les lots restent séparés. Les consommables conservent le total personnel sans porte-vaisseaux. FCMaterials n’est pas un inventaire complet du porte-vaisseaux et n’est pas utilisé comme tel. La limite de 1000 du casier s’applique par catégorie, pas par objet. Le stock du porte-vaisseaux est estimé depuis la dernière confirmation. Les variations du casier sont compensées uniquement à bord de votre propre porte-vaisseaux, après déduction des transactions personnelles explicites. Les achats et ventes au bar, notamment par d’autres joueurs, peuvent modifier le stock réel sans être enregistrés automatiquement. Double-cliquez pour confirmer à nouveau si nécessaire. Le total utilise une projection du dernier stock confirmé, sans garantie de consultation en direct. Le stockage privé Odyssey partage 1 000 places entre marchandises, matériaux et données. La somme des stocks est complète uniquement lorsque toutes les positions et les matériaux supplémentaires sont confirmés, y compris les zéros. Sinon, un minimum est affiché. En cas de dépassement, les valeurs sont conservées et Total devient inconnu. Casier, sac à dos et réservations du marché ne sont pas du stock privé du porte-vaisseaux.<br><b>! – Configurer le stock du porte-vaisseaux</b><br>Double-cliquez dans la colonne Porte-vaisseaux et saisissez la quantité actuelle pour CHAQUE position. Confirmez explicitement TOUTES les positions vides avec 0.<br>— = pas encore confirmé / inconnu<br>0 = stock vide explicitement confirmé</p>
<p>Les ordres d’achat ouverts du barman réservent de la capacité. L’occupation en jeu peut donc dépasser le stock de matériaux. Les réservations ne sont pas des matériaux et ne comptent pas dans leurs totaux. Sans données de marché suffisamment actuelles, l’occupation reste inconnue. Les échanges des autres joueurs peuvent modifier cet instantané.</p>
<p>Utilisation affiche les indications d’usage de l’objet. Mission désigne l’affectation à une mission de la pile d’inventaire concernée, et non une propriété générale du type d’objet. Les piles ordinaires et celles liées à une mission restent séparées. Même après la fin d’une mission, l’objet reste marqué tant que le journal le répertorie dans l’inventaire ; une mission terminée ne le fait pas disparaître automatiquement. L’infobulle indique le numéro de mission et son statut connu. Ingénierie signifie que le catalogue statique Odyssey connaît au moins une utilisation confirmée : amélioration de combinaison, amélioration d’arme, modification de combinaison, modification d’arme ou déblocage d’ingénieur. Les utilisations détaillées figurent dans l’infobulle. L’absence de cette indication ne signifie pas que l’objet est inutile ou uniquement échangeable. Les objets Powerplay et d’autres objets spéciaux peuvent également apparaître.</p>
<p>La recherche porte sur les noms affichés des matériaux/objets et sur leurs noms anglais. Les six filtres Odyssey sont Tous (tous les objets), Mission (piles affectées à une mission), Ingénierie (objets ayant une utilisation d’ingénierie confirmée), Sac à dos (stock du sac à dos supérieur à zéro), Casier (stock du casier supérieur à zéro) et Stock nul (stock total de 0 connu de manière fiable). Un stock inconnu — n’est pas 0 et est exclu de Stock nul. Si un nom n’est pas traduit, le nom anglais est utilisé ; certains noms peuvent donc rester en anglais dans la langue choisie. Ce comportement est voulu et ne constitue pas une erreur de traduction de la logique d’inventaire.</p>
<p>L’inventaire personnel est actualisé automatiquement en arrière-plan. Les nouvelles collectes confirmées peuvent être brièvement mises en évidence. Lors d’un changement de commandant, les anciens stocks sont immédiatement retirés. Les sous-onglets, les filtres, la largeur et l’ordre des colonnes sont enregistrés séparément pour Odyssey.</p>
<h3>Mining</h3>
<p>Matériaux → Mining regroupe les 57 marchandises minières échangeables actuellement connues, distinctes des matériaux d’ingénierie. Un seul tableau couvre l’extraction à la surface des planètes et dans les astéroïdes/anneaux. Les prix de référence fixes sont indicatifs, pas des prix de marché en direct.</p>
<p><b>Colonnes</b><br><b>Marchandise :</b> nom de la marchandise ou de la ressource.<br><b>SRV:</b> stock vérifié dans le SRV.<br><b>Vaisseau:</b> stock vérifié dans le vaisseau.<br><b>Porte-vaisseaux :</b> stock de votre propre carrier ; Elite ne fournit pas d’inventaire personnel complet, le stock initial doit donc être confirmé manuellement.<br><b>Total :</b> SRV + Vaisseau + Carrier, uniquement si les trois stocks sont connus. Sinon — ; inconnu ne signifie pas zéro.<br><b>Prix moyen Cr/t :</b> valeur indicative fixe, sans garantie de prix de vente actuel. Un prix de référence absent reste inconnu.<br><b>Classe de valeur :</b> ÉLEVÉE à partir de 100 000 Cr/t ; MOYENNE de 25 000–99 999 Cr/t ; FAIBLE sous 25 000 Cr/t. Un prix inconnu n’a pas de classe de valeur.</p>
<p><b>Confirmer le stock du carrier</b><br>Elite Dangerous ne transmet pas à CMDRHelper d’inventaire personnel complet du carrier. Pour définir un point de départ connu pour une marchandise : 1. Double-cliquez sur sa cellule Carrier. 2. Saisissez le stock actuel, un nombre entier supérieur ou égal à 0. 3. Appliquez la valeur pour la confirmer manuellement. 4. CMDRHelper suit ensuite automatiquement les événements CargoTransfer non ambigus entre votre vaisseau et votre propre carrier. L’infobulle indique la confirmation manuelle et le suivi ultérieur éventuel.</p>
<p><b>— = stock inconnu</b><br>Sans stock initial confirmé, des transferts isolés ne permettent pas de calculer un stock absolu fiable. Un double-clic permet à tout moment de modifier, corriger ou réinitialiser la valeur à inconnu. Si un transfert devait produire un résultat contradictoire ou négatif, le stock redevient inconnu et doit être confirmé à nouveau manuellement.</p>
<p><b>Vaisseau et SRV</b><br>Les stocks du SRV et du vaisseau sont reconstitués séparément à partir de données de fret vérifiées. Les stocks inconnus restent —. Les instantanés complets priment sur les variations calculées.</p>
<p><b>↻ Actualiser</b><br>Les stocks du SRV et du vaisseau sont actualisés séparément à partir de données vérifiées. Le stock confirmé du carrier est conservé indépendamment. Les mises à jour automatiques continuent normalement. Vert signifie prêt ou réussi, l’animation colorée indique une actualisation en cours et rouge un échec. Des données absentes ou non vérifiables ne sont pas présentées comme un stock vide.</p>
<p><b>Combiner les filtres</b><br>La recherche filtre les ressources par nom. La classe propose Tous, ÉLEVÉE, MOYENNE et FAIBLE ; l’origine propose Tous, Extraction planétaire et Astéroïdes/Anneaux. « En stock uniquement » affiche une marchandise si au moins un stock connu dans le SRV, le vaisseau ou le carrier est positif. Un stock inconnu n’est pas considéré comme 0 et ne masque pas un stock positif connu ailleurs. Recherche, classe, origine et filtre de stock se combinent.</p>
<p><b>ABBAU ×N dans l’explorateur</b><br>Un clic ouvre Matériaux → Mining et règle automatiquement le filtre d’origine sur Extraction planétaire. Il n’existe pas de second tableau minier dans l’explorateur.</p>
<p><b>Tri et largeurs</b><br>Cliquez sur les en-têtes pour trier en ordre croissant ou décroissant. Stocks et prix sont triés numériquement, les valeurs inconnues en dernier. Faites glisser les limites des colonnes pour ajuster leur largeur. Le tri, les largeurs et les filtres de classe, d’origine et En stock uniquement sont enregistrés.</p>
<p><b>Origine</b><br>Surface désigne l’extraction à la surface des planètes ; Asteroid, celle des astéroïdes/anneaux. Certaines ressources proviennent des deux (Both) et apparaissent dans les deux filtres d’origine correspondants.</p>""",
    ),'overview': ('Aperçu',
              '<h2>Aperçu</h2>\n'
              "<p>L'aperçu est la page d'accueil du CMDRHelper. Il résume les informations les "
              "plus importantes sur le commandant actuellement actif et montre en un coup d'œil si "
              'le journal, la localisation et les services en ligne sont correctement '
              'reconnus.</p>\n'
              '\n'
              '<h3>Commandant et navire</h3>\n'
              '<p>Le commandant reconnu dans le Elite Dangerous Journal et le navire actuellement '
              'utilisé sont affichés ici.</p>\n'
              '<p>CMDRHelper attribue des données personnelles au commandant respectif sur la base '
              "de l'ID Frontier (FID). Cela permet de séparer les données des différents "
              'commandants les unes des autres.</p>\n'
              '<p>Lors du changement de commandant, les informations enregistrées associées au '
              'nouveau commandant sont chargées.</p>\n'
              '\n'
              '<p>CMDRHelper affiche le dernier mode de jeu signalé par Elite. Open, Solo et Groupe privé sont reconnus à partir de LoadGame. Pour les groupes privés, le nom du groupe signalé par Elite est affiché sans modification. Cela ne signifie pas qu’Elite est actuellement en cours d’exécution.</p>\n'
              '<h3>journal</h3>\n'
              '<p>CMDRHelper utilise les fichiers journaux de Elite Dangerous comme source de '
              'données principale.</p>\n'
              "<p>L'affichage du journal indique si les fichiers du journal ont été trouvés et "
              'attribués au commandant actif. Les nouvelles entrées de journal complètes sont '
              'automatiquement traitées pendant le jeu.</p>\n'
              '<p>Les zones de journal qui ont déjà été traitées sont enregistrées afin que '
              "CMDRHelper n'ait pas à réévaluer entièrement chaque journal au prochain "
              'démarrage.</p>\n'
              '\n'
              '<h3>Emplacement actuel</h3>\n'
              '<p>Affiche le système stellaire actuellement connu et - pour autant que le journal '
              "le sache - l'emplacement exact du commandant.</p>\n"
              "<p>L'emplacement est mis à jour par des événements tels que des sauts, des "
              "amarrages et d'autres rapports de position et stocké commandant par "
              'commandement.</p>\n'
              '\n'
              '<h3>Missions</h3>\n'
              '<p>Cette zone affiche le nombre de missions ouvertes actuellement connues.</p>\n'
              "<p>« Missions → » ouvr"
              'e la rubrique principale « Missions et récompenses » avec les objectifs de mission connus et leur '
              "état.</p>\n"
              '\n'
              '<h3>Dernier état</h3>\n'
              '<p>«\xa0Dernier état\xa0» résume le dernier état persistant connu du commandant. '
              'Cela permet de restaurer les informations importantes même après le redémarrage du '
              'Elite Dangerous ou du CMDRHelper.</p>\n'
              '\n'
              '<h3>Systèmes récemment visités</h3>\n'
              '<p>Les systèmes récemment visités ou reconnus dans le journal sont affichés '
              'ici.</p>\n'
              '<p>La liste constitue un aperçu rapide du récent voyage du commandant.</p>\n'
              '<p>L’historique des visites tient compte de Location, FSDJump et CarrierJump lors du suivi du journal en direct. Plusieurs événements de position pendant un séjour ininterrompu comptent pour une visite : A → A → A compte une fois. Un véritable retour est conservé : A → B → C → A compte quatre visites.</p>\n\n'
              '<h3>Statut en ligne</h3>\n'
              "<p>Il y a des indicateurs d'état supplémentaires en haut de la fenêtre "
              'principale\xa0:</p>\n'
              '<ul>\n'
              '<li><b>Revue reconnue</b>– CMDRHelper a détecté une source de journal et une '
              'identité de commandant valides.</li>\n'
              "<li><b>EDSM</b>– affiche l'état actuel de la transmission EDSM pour le journal "
              'actif FID.</li>\n'
              "<li><b>INARA</b>– affiche l'état actuel de la transmission Inara pour le journal "
              'actif FID.</li>\n'
              '</ul>\n'
              "<p>Les données d'accès en ligne sont gérées séparément pour chaque commandant. Un "
              "commandant n'utilise jamais automatiquement le API-Key d'un autre commandant.</p>\n"
              '\n'
              '<h3>Important pour plusieurs commandants</h3>\n'
              '<p>Les données en direct dépendent toujours du commandant qui a été clairement '
              'identifié par la session actuelle du journal Elite Dangerous.</p>\n'
              "<p>Le simple fait d'afficher un commandant différent dans une vue ne modifie pas le "
              "commandant en direct actif ni n'affecte les diffusions EDSM ou Inara.</p>\n"
              '\n'
              '<h3>Conseil</h3>\n'
              "<p>Si le commandant, le navire ou l'emplacement ne correspond pas à l'état actuel "
              "du jeu, vérifiez d'abord l'affichage du journal en haut, puis vérifiez le dossier "
              'du journal défini sous « Paramètres ».</p>'
              '<p>Le mode Ouvert apparaît en rouge, Solo en doré et Groupe privé en vert, avec le nom de groupe signalé. Le mode est reconstitué à partir des journaux disponibles et actualisé avec les nouvelles entrées LoadGame.</p>\n<p>Un simple clic sur une entrée des systèmes récents copie son nom dans le presse-papiers. « ✓ Copié : &lt;Système&gt; » apparaît brièvement. L’icône ⧉ à côté de chaque nom de système copie également uniquement ce nom dans le presse-papiers.</p>\n'),
 'missions': (
        'Missions et récompenses',
        """<h2>Missions et récompenses</h2>
<p>Cette page principale affiche les missions et les récompenses observées du commandant actuellement actif dans le journal. Sélectionner un autre commandant dans la vue CMDR séparée ne modifie pas cette page. Les données restent distinctes pour chaque commandant.</p>

<h3>Utiliser cette page</h3>
<ol>
<li>Ouvrez « Missions et récompenses » et sélectionnez une mission dans la liste.</li>
<li>Consultez « État » et « DÉTAILS DE LA MISSION ». « Étape suivante » vous aide à vous orienter.</li>
<li>Au besoin, utilisez « Actualiser le journal » pour relire les données disponibles du journal.</li>
<li>Examinez séparément les récompenses de mission, « Primes » et « Obligations de combat ».</li>
</ol>

<h3>Liste et détails</h3>
<p>La liste contient les missions ouvertes confirmées et les offres provisoires détectées lors de rencontres. Elle affiche la mission, le système, la planète / le lieu, l'état, l'étape suivante, la récompense et l'échéance. Sélectionner une ligne affiche les détails disponibles sur la destination et la progression. Les informations absentes du journal restent inconnues ; l'échéance des offres provisoires est inconnue.</p>

<h3>État des missions</h3>
<p>L'état suit les informations disponibles sur la mission, la position et la progression. Tous les types de missions ne fournissent pas toutes les étapes intermédiaires.</p>
<ul>
<li><b>Mission acceptée / En route :</b> La mission est connue ; l'arrivée à destination n'a pas encore été détectée.</li>
<li><b>Dans le système cible :</b> Vous êtes dans le système cible, mais pas encore à la destination identifiée de la mission.</li>
<li><b>À la destination de la mission :</b> La station ou le corps céleste correspondant à la destination a été atteint.</li>
<li><b>Destination modifiée :</b> Une nouvelle destination a été signalée.</li>
<li><b>Marchandise récupérée :</b> Le chargement de marchandises de mission a été détecté.</li>
<li><b>Livraison en cours :</b> Une livraison a été enregistrée ; la progression connue des quantités est affichée.</li>
<li><b>Tâche terminée / Données reçues :</b> La tâche ou la collecte de données est terminée. La mission peut rester ouverte, par exemple avec « Retourner au terminal de missions ». Cela ne confirme pas encore un paiement.</li>
</ul>
<p>Une fin de mission, un échec ou un abandon détecté retire la mission concernée de la liste ouverte. Un nouvel état complet des missions peut identifier d'anciennes entrées comme inactives.</p>

<h3>Récompense totale</h3>
<p>« Récompense totale » additionne les récompenses connues en crédits des missions ouvertes confirmées. Ce n'est pas un solde déjà versé. Les offres provisoires de rencontres, les primes et les obligations de combat en sont exclues.</p>

<h3>Missions de rencontre</h3>
<p>Les rencontres spatiales prises en charge peuvent apparaître sous forme d'offres provisoires « Mission de rencontre », avant même qu'un identifiant MissionID définitif existe. « Récompense proposée » n'est donc pas encore une récompense de mission ouverte confirmée et ne compte pas dans la récompense totale.</p>
<p>Si des données ultérieures du journal relient sans ambiguïté une offre à une mission, elles sont fusionnées. Sinon, l'offre reste provisoire. Les offres non confirmées disparaissent localement après 24 heures ; cela n'indique pas une échéance de mission dans le jeu.</p>

<h3>Primes</h3>
<p>Cette zone affiche les primes observées localement, avec un total et des montants par faction. Elle ne connaît que les données enregistrées, pas un solde du jeu dont l'exhaustivité serait garantie. « Enregistrement à partir de maintenant. » indique le début de l'enregistrement ; les lacunes sont signalées par « Synchronisation incomplète : certains événements peuvent manquer. ».</p>
<p>Un encaissement de primes ou une mort détectés remettent à zéro tout le solde local des primes, indépendamment de l'état des missions.</p>

<h3>Obligations de combat</h3>
<p>Cette zone affiche par faction les obligations de combat observées dont l'encaissement n'a pas été détecté. Un éventuel solde antérieur au début de l'enregistrement manque. En cas d'incertitude, « Montant observé » apparaît avec « Solde non entièrement vérifié. ».</p>
<p>Un encaissement attribué sans ambiguïté efface le montant observé de la faction indiquée ; les autres factions restent inchangées. Si l'attribution est incertaine, les montants restent affichés avec « Encaissement détecté – vérifier le solde. ». Une mort détectée efface les obligations de combat observées.</p>

<h3>Réinitialisation locale</h3>
<p>« Réinitialiser… » dans une zone de récompenses remet uniquement son solde local à zéro pour le commandant actif, après confirmation. <b>Cela ne modifie aucune valeur dans Elite Dangerous.</b> Les primes et les obligations de combat sont réinitialisées séparément ; les missions ne sont ni nettoyées ni terminées.</p>

<h3>Actualisation et redémarrage</h3>
<p>Les missions ouvertes connues et les soldes locaux des récompenses sont conservés après un redémarrage du Helper. Une nouvelle session du journal sans liste de missions ne supprime pas automatiquement les missions ouvertes. Des lacunes d'enregistrement peuvent notamment laisser les soldes des récompenses incomplets. « Actualiser le journal » ne peut que lire les informations existantes, pas créer les données manquantes du jeu.</p>
<p>L'affichage local des missions ne nécessite aucune connexion à Inara. Si une connexion adaptée au commandant actif est configurée et activée, les événements de mission pris en charge peuvent aussi être transmis.</p>""",
    ),
 'explorer': ('Explorateur',
              '<h2>Explorateur</h2><p>L’en-tête affiche aussi le même statut EDSM que le HUD de statut EDSM : bleu = connu dans EDSM, jaune = aucune correspondance EDSM, gris = aucune réponse exploitable. « EDSM: — » signifie aucun résultat pour le moment, par exemple si le HUD est désactivé ou si une requête est en cours. Le réglage existant du HUD contrôle la requête. Cela ne confirme pas une première découverte dans Elite.</p>\n<h3>CMDRHelper</h3>\n<p>Vue d’ensemble du système : la nouvelle présentation inspirée d’Elite remplace l’ancienne miniature dans Explorer et la Chronique. Étoiles et planètes forment la structure principale, les lunes se ramifient en dessous ; les systèmes multiples restent lisibles. Zoom, défilement, ajustement à la fenêtre et clic sur un corps donnent accès aux détails.</p>\n<p>Ceintures d’astéroïdes compactes : les amas sont regroupés en ceintures dans la vue d’ensemble et les cartes habituelles d’Explorer et de la Chronique. Toutes les données individuelles sont conservées.</p>\n<p>Cartographie corrigée : un scan après une cartographie DSS ne réinitialise plus les valeurs d’exploration invendues, l’heure de cartographie ni l’efficacité. Les créances incorrectes sont réparées au démarrage à partir des journaux disponibles et attribués sans ambiguïté. Sans ces sources, la réparation reste en attente ; inutile de supprimer la base.</p>\n'
              "<p>L'Explorateur évalue les systèmes et corps célestes découverts et scannés par le "
              'commandant actif. Il combine vos propres données de journal Elite Dangerous avec '
              'des informations supplémentaires déjà disponibles et affiche ensemble les données '
              "d'exploration, de cartographie, de signaux biologiques/géologiques et "
              "d'exploitation minière à ciel ouvert.</p>\n"
              '\n'
              '<h3>Système actuel</h3>\n'
              '<p>Le niveau actuel des connaissances sur le système est résumé dans la zone '
              'supérieure.</p>\n'
              '<p>Ceux-ci incluent, entre autres :</p>\n'
              '<ul>\n'
              '<li>des corps bien connus et même enregistrés dans le journal</li>\n'
              '<li>signaux existants</li>\n'
              "<li>Valeurs d'analyse</li>\n"
              '<li>valeur cartographique déjà atteinte</li>\n'
              '<li>valeur totale possible si entièrement cartographiée</li>\n'
              '<li>Statut BIO et valeurs BIO estimées</li>\n'
              '<li>Cartographie et données BIO non encore soumises</li>\n'
              '</ul>\n'
              '<p>Les valeurs affichées sont basées sur les données réellement disponibles. Les '
              'informations manquantes ne sont pas présentées comme une découverte distincte.</p>\n'
              '\n'
              '<h3>Carte du système</h3>\n'
              '<p>La carte du système représente graphiquement les étoiles, planètes, lunes et '
              'autres corps connus dans le système actuel.</p>\n'
              '<p>Il est possible de cliquer sur un corps pour ouvrir sa vue détaillée.</p>\n'
              "<p>L'écran affiche, entre autres, le type de corps, la distance et – si disponible "
              '– les valeurs de numérisation et de cartographie ainsi que les propriétés '
              "d'exploration spéciales.</p>\n"
              '\n'
              '<p>« Ajuster automatiquement à la fenêtre » est activé par défaut et conserve votre choix après un redémarrage. Chaque nouvelle vue générale est ajustée une seule fois à la fenêtre ; activer cette option dans une fenêtre ouverte effectue également un seul ajustement. Vous pouvez ensuite zoomer et déplacer la vue manuellement. « Adapter à la fenêtre » reste disponible pour un nouvel ajustement manuel.</p>\n'
              '\n'
              '<h3>Stations et installations</h3>\n'
              '<p>L’onglet « STATIONS (N) » présente les stations et installations connues du système actuel de l’Explorer sous forme de fiches dépliables. Le nombre dans le titre inclut toutes les entrées connues, même celles masquées par les filtres. Ce n’est pas un catalogue complet des stations de la galaxie.</p>\n'
              '<p>La base provient des observations du journal Elite connues localement. Si le complément Spansh est activé, le cache de stations séparé ajoute des informations. La source peut être « Journal », « Spansh » ou « Journal + Spansh » ; en cas de contradiction, les informations du journal priment. Spansh n’ajoute pas de Fleet Carriers ici. Votre propre carrier peut apparaître s’il est connu localement.</p>\n'
              '\n'
              '<h3>Recherche, filtres et tri des stations</h3>\n'
              '<p>« Rechercher un nom de station… » recherche immédiatement les noms de stations ou parties de noms, sans distinguer majuscules et minuscules. Une recherche vide ne restreint pas les noms. La recherche et les deux filtres doivent être satisfaits ensemble.</p>\n'
              '<ul>\n'
              '<li><b>Type :</b> Limite la liste aux stations orbitales, avant-postes, stations de surface, colonies, mégavaisseaux, Fleet Carriers ou autres installations. « Tous les types » retire cette restriction.</li>\n'
              '<li><b>Corps associé :</b> Sélectionne un corps associé connu. « Tous les astres » accepte tous les emplacements ; « Inconnu » apparaît lorsque des entrées ne peuvent pas être rattachées avec certitude à un corps connu.</li>\n'
              '<li><b>Trier par :</b> Le tri initial est alphabétique par « Nom ». Vous pouvez aussi trier par « Type », « Corps associé » ou « Distance du point d’arrivée » en ordre croissant. La distance est numérique ; les distances ou corps inconnus viennent en dernier pour leur tri respectif.</li>\n'
              '</ul>\n'
              '<p>Il n’y a pas d’en-têtes de colonnes de stations à cliquer : les listes de sélection trient les fiches. Recherche, filtres et tri ne lancent aucune requête réseau. Changer de système réinitialise la recherche et les filtres de type et de corps. Une liste vide distingue l’absence d’entrées connues des entrées ne correspondant pas aux filtres.</p>\n'
              '\n'
              '<h3>Détails des stations et services</h3>\n'
              '<p>Cliquez sur l’en-tête d’une fiche pour déplier ou replier les détails. S’ils sont connus, ceux-ci indiquent nom, type, système, corps associé, MarketID, dernière actualisation et source. Un double-clic sur l’aperçu ouvre la visionneuse d’images.</p>\n'
              '<p>Spansh peut ajouter la distance d’arrivée en secondes-lumière, l’allégeance, le gouvernement, la faction dirigeante, les données économiques et le nombre de grandes, moyennes et petites plateformes. Les dates des données de station, de système et de récupération sont affichées séparément si disponibles ; une nouvelle récupération ne garantit pas des données de station plus récentes.</p>\n'
              '<p>Les « Services » connus apparaissent sous forme de champs libellés, par exemple « Marché », « Chantier naval », « Équipement », « Réparation », « Ravitaillement » ou « Courtier en matériaux ». L’en-tête montre au plus trois services et, le cas échéant, le nombre d’entrées supplémentaires ; la fiche dépliée montre tous les services reconnus par CMDRHelper. Les informations manquantes ne sont pas inventées et ne prouvent pas l’absence d’un service.</p>\n'
              '\n'
              '<h3>Stations sur la carte et actualisation</h3>\n'
              '<p>La carte du système et « Vue d’ensemble » utilisent les mêmes informations de stations connues. Les installations rattachées avec certitude à un corps apparaissent près de celui-ci, les autres sous « Autres installations ». Un clic ouvre les détails ou, pour un groupe, d’abord une liste de sélection.</p>\n'
              '<p>Dans « Vue d’ensemble », « Actualiser les données Spansh » actualise les informations Spansh des stations du système affiché dans cette fenêtre. L’option Spansh doit être activée et l’identité du système connue. La ligne d’état indique une requête en cours, sa réussite, son échec ou une actualisation déjà faite aujourd’hui. En cas d’échec, les informations locales et les données utilisables en cache restent disponibles. L’aide des paramètres explique les requêtes automatiques, le cache et l’actualisation manuelle.</p>\n'
              '\n'
              '<h3>BIO ×N</h3>\n'
              "<p>BIO ×N désigne le nombre de signaux biologiques d'un corps rapportés par le "
              'jeu.</p>\n'
              '<p>Au départ, le nombre indique uniquement combien de signaux biologiques ou de '
              'genres ont été signalés. Cela ne signifie pas automatiquement que toutes les '
              'espèces biologiques ont déjà été trouvées ou analysées.</p>\n'
              '<p>Les propres découvertes organiques réelles sont conservées séparément.</p>\n'
              '\n'
              '<h3>GÉO ×N</h3>\n'
              "<p>GEO ×N indique le nombre de signaux géologiques d'un corps rapportés par le "
              'jeu.</p>\n'
              "<p>Il peut s'agir, par exemple, de caractéristiques géologiques telles que des "
              'fumerolles ou des geysers. CMDRHelper affiche uniquement les informations qui '
              'apparaissent à partir des données de journal/corps existantes.</p>\n'
              '\n'
              '<h3>ABBAU ×N</h3>\n'
              "<p>ABBAU ×N montre le nombre de sites miniers planétaires d'un corps rapporté par "
              'Elite Dangerous.</p>\n'
              '<p>Exemple:</p>\n'
              '<p><b>ABBAU ×12</b></p>\n'
              '<p>Cela signifie que 12 sites miniers planétaires ont été signalés pour cet '
              'organisme.</p>\n'
              '<p>Le chiffre ne précise pas quelle matière première peut être extraite en un seul '
              'endroit.</p>\n'
              '\n'
              '<h3>Propres découvertes minières</h3>\n'
              '<p>Si le commandant a effectivement effectué une exploitation minière à ciel ouvert '
              'avec le Rhino, le CMDRHelper stocke les découvertes personnelles documentées '
              'séparément.</p>\n'
              '<p>Une distinction est faite entre :</p>\n'
              '<ul>\n'
              '<li>Produits réellement obtenus, par ex. B. Cuivre en tonnes</li>\n'
              "<li>matières secondaires collectées lors de l'exploitation minière</li>\n"
              '<li>matériaux de surface généraux du corps</li>\n'
              '</ul>\n'
              '<p>Un exemple de découverte personnelle serait\xa0:</p>\n'
              '<p><b>Cuivre – 40 tonnes</b></p>\n'
              '<p>Cette information signifie que ce commandant y a effectivement extrait 40 t de '
              'cuivre.</p>\n'
              '<p>Les découvertes minières personnelles sont enregistrées pour chaque commandant '
              'et ne sont pas mélangées avec les découvertes des autres commandants.</p>\n'
              '\n'
              '<h3>Matériaux de surface du corps</h3>\n'
              '<p><code>Scan.Materials</code>décrit la composition générale des matériaux de '
              "surface d'un corps.</p>\n"
              "<p>Par exemple, le fer, le nickel, le soufre ou d'autres matériaux peuvent être "
              'affichés avec des valeurs en pourcentage.</p>\n'
              "<p>Ces valeurs ne doivent pas être confondues avec les matières premières d'un "
              'dépôt minier planétaire. Frontier ne fournit aucune association directe documentée '
              "entre ces matériaux généraux du corps et le contenu d'un site minier individuel "
              'dans le Journal.</p>\n'
              '\n'
              '<h3>Terraformation</h3>\n'
              "<p>Le symbole ou l'étiquette de terraformation montre qu'un corps est considéré "
              'comme un candidat à la terraformation sur la base des données disponibles.</p>\n'
              '\n'
              '<h3>Première découverte</h3>\n'
              '<p>« Déjà découvert lors de votre scan » décrit l’état avant votre scan de l’époque. Oui signifie déjà découvert, Non signifie pas encore découvert à ce moment-là ; une information absente reste Inconnue. ★ indique un candidat à la première découverte au moment du scan, pas une attribution officielle encore garantie aujourd’hui.</p>\n<p>Une ancienne valeur WasDiscovered=false ou WasMapped=false ne signifie pas que le corps est encore non découvert ou non cartographié aujourd’hui. Ces observations restent historiques après la vente des données ou une nouvelle visite. La présence dans EDSM est une information distincte, sans valeur de preuve d’une découverte officielle dans Elite. Aucun premier découvreur officiel n’en est déduit.</p>\n'
              '\n'
              '<h3>Première cartographie</h3>\n'
              '<p>CMDRHelper fait la distinction entre\xa0:</p>\n'
              '<ul>\n'
              '<li>◉ Candidat First Mapping au moment du scan : pas encore cartographié lors de votre scan</li>\n<li>◎ Cartographié par vous : votre propre cartographie DSS terminée est enregistrée</li>\n<li>◉✓ Candidat lors du scan et votre propre cartographie attestés ; attribution officielle de la première cartographie non confirmée</li>\n'
              '</ul>\n'
              '<p>« Déjà cartographié lors de votre scan » est évalué indépendamment de la découverte. Une information absente reste Inconnue. Un corps déjà découvert pouvait ne pas encore être cartographié lors du scan. Votre cartographie ne confirme pas une attribution officielle First Mapping ; après plusieurs visites, son ordre par rapport au scan enregistré n’est pas toujours établi non plus.</p>\n<p>La fin de votre propre cartographie DSS enregistre désormais de manière fiable l’heure de cartographie, les sondes utilisées et l’objectif d’efficacité. Les scans ultérieurs ne font plus perdre les informations existantes.</p>\n'
              '\n'
              '<h3>Atterrissage possible</h3>\n'
              "<p>L'indicateur d'atterrissage identifie les corps sur lesquels, selon les données "
              "connues, l'atterrissage est possible.</p>\n"
              '\n'
              '<h3>Cadres en or / corps précieux</h3>\n'
              "<p>Les corps particulièrement précieux peuvent être mis en évidence dans l'écran de "
              "l'explorateur.</p>\n"
              '<p>Le cadre doré indique une estimation de cartographie dépassant le seuil configuré. Ce n’est pas une marque de première découverte et il ne confirme ni des données invendues ni des bonus de première découverte ou cartographie encore disponibles aujourd’hui.</p>\n'
              "<p>Il ne remplace pas l'affichage détaillé de la valeur du corps.</p>\n"
              '\n'
              '<h3>Liste de valeurs</h3>\n'
              '<p>La liste des valeurs présente des estimations selon le scan enregistré, pas des paiements encore dus garantis. Les bonus de première découverte ou cartographie restent non confirmés. Les infobulles de la carte et de la liste ainsi que les détails du corps utilisent les mêmes états situés dans le temps.</p>\n'
              '<p>Il est particulièrement adapté pour comparer rapidement des corps intéressants '
              'ou précieux dans un système.</p>\n'
              '\n'
              '<h3>BIO / GEO / ABBAU</h3>\n'
              '<p>Cette vue regroupe les corps présentant des signaux biologiques, géologiques ou d’extraction '
              'minière planétaire.</p>\n'
              "<p>Cela signifie qu'il n'est pas nécessaire de rechercher individuellement les "
              'corps intéressants dans la carte complète du système.</p>\n'
              '<p>Si vous disposez de vos propres données d’exploitation minière à ciel ouvert, '
              'vos découvertes minières personnelles peuvent également être visibles.</p>\n'
              '<p>Les largeurs ajustées manuellement dans la table commune BIO / GEO / ABBAU de l’Explorateur sont conservées à la réouverture et au redémarrage. La restauration des largeurs des fenêtres contextuelles est plus robuste ; les valeurs invalides sont remplacées par des largeurs par défaut utilisables.</p>\n\n'
              '<h3>Utiliser les tableaux</h3>\n<p>Dans la liste des valeurs et BIO / GEO / ABBAU, cliquez sur '
              'un en-tête pour trier, puis à nouveau pour inverser le sens. Faites glisser les limites des '
              'colonnes pour changer leur largeur. Le tri et les largeurs sont enregistrés séparément pour '
              'chaque tableau. Les noms des corps suivent un ordre naturel, par exemple A 2 avant A 10. '
              'Distances, crédits et quantités sont triés numériquement. Les colonnes de statut, d’analyse et '
              'de visite sont triées selon leur signification, pas alphabétiquement.</p>\n\n<h3>Détail du '
              'corps</h3>\n'
              '<p>Cliquer sur un corps ouvre la vue détaillée.</p>\n'
              "<p>Pour autant que l'on sache, les éléments suivants peuvent y apparaître\xa0:</p>\n"
              '<ul>\n'
              '<li>Type de corps</li>\n'
              '<li>masse</li>\n'
              '<li>distance</li>\n'
              '<li>Pesanteur</li>\n'
              '<li>atmosphère</li>\n'
              '<li>Atterrissage</li>\n'
              '<li>Statut de terraformation</li>\n'
              '<li>Signaux BIO/GEO</li>\n'
              '<li>sites miniers planétaires</li>\n'
              '<li>Matériaux de surface</li>\n'
              '<li>propres découvertes minières</li>\n'
              '<li>Valeur de numérisation</li>\n'
              '<li>valeur cartographique</li>\n'
              '<li>valeur actuelle</li>\n'
              '</ul>\n'
              '<p>Tout le monde ne dispose pas de toutes les informations.</p>\n'
              '\n'
              '<h3>Prévisions BIO</h3>\n'
              "<p>CMDRHelper peut estimer d'éventuelles découvertes biologiques sur la base des "
              'données existantes sur des corps appropriés.</p>\n'
              '<p>Les prédictions ne garantissent pas qu’une espèce particulière sera réellement '
              'présente. Ils servent d’aide à la décision pour l’exploration.</p>\n'
              '<p>Les valeurs BIO estimées sont également des prédictions et sont traitées '
              'séparément des résultats réels confirmés.</p>\n'
              '\n'
              '<h3>Pas encore soumis</h3>\n'
              '<p>CMDRHelper conserve la cartographie connue et les données BIO liées au '
              "commandant qui n'ont pas encore été soumises.</p>\n"
              '<p>Les ventes de cartographie et les redevances biologiques sont comptabilisées à '
              'partir des événements de revue correspondants.</p>\n'
              '<p>Les données cartographiques déjà vendues ne doivent plus apparaître comme '
              'ouvertes après la reconstruction.</p>\n'
              '\n'
              '<h3>Affichage automatique</h3>\n'
              "<p>Les indices de l'Explorateur pris en charge, tels que les corps précieux ou les "
              "découvertes BIO, peuvent être automatiquement affichés à l'aide des commutateurs "
              'dans la barre latérale gauche.</p>\n'
              "<p>Ces petites fenêtres en direct servent d'indices supplémentaires pendant la "
              "lecture et ne remplacent pas la vue complète de l'Explorateur.</p>\n"
              '<p>« Cargo » affiche le stock confirmé du Ship ou du SRV déterminé par la FID active du Journal. Le Cargo du SRV n’est jamais repris comme Cargo du Ship ; les Limpets comptent dans l’occupation totale et sont affichés séparément dans le tableau Nom | Quantité.</p>\n'
              '<p>La progression BIO est compacte : 1/3 en jaune, 2/3 en bleu et 3/3 en vert ; l’état terminé « Terminé » est également vert. Sous « afficher automatiquement », GEO dispose de son propre interrupteur mémorisé : BIO seul, GEO seul ou les deux ensemble sont possibles.</p>\n<p>La fenêtre de soute adapte automatiquement sa hauteur au contenu. Avec de nombreuses entrées, la hauteur reste limitée et la table défile ; la largeur choisie et la position sont conservées. L’interrupteur existant « HUD de soute » se trouve désormais sous « afficher automatiquement », sans interrupteur supplémentaire dans la fenêtre de soute.</p>\n\n'
              '<h3>Plusieurs commandants</h3>\n'
              "<p>Les résultats d'exploration personnels, la cartographie, les découvertes BIO et "
              'les propres découvertes minières à ciel ouvert sont attribués au commandant '
              'respectif.</p>\n'
              "<p>Les propriétés astronomiques globales d'un corps - par exemple le nombre de "
              'sites miniers planétaires connus - restent des propriétés du corps lui-même.</p>\n'
              '\n'
              '<h3>Conseil</h3>\n'
              '<p>Si vous avez un corps intéressant, cela vaut la peine de cliquer sur la vue '
              "détaillée. C'est le meilleur endroit pour faire la différence entre les données "
              "corporelles générales, les résultats d'exploration possibles et les découvertes "
              'réelles documentées par votre propre commandant.</p>'
              """

<h3>★ Favoris</h3>
<p>Le bouton « ★ Favoris » en haut de l’Explorer ouvre une fenêtre de favoris distincte et réutilisable. Tu y enregistres des systèmes, des planètes/lunes et des lieux en surface pour le commandant actif.</p>
<p>La liste défilante, triée par ordre alphabétique des noms, affiche le nom, le type, le système, le corps et la latitude/longitude le cas échéant, la catégorie et un petit aperçu d’image. La recherche en texte libre et les filtres de type et de catégorie sont combinables. La recherche porte sur le nom, le système, le corps et la note.</p>
<p>« Ouvrir / Afficher » affiche les informations enregistrées, la note et un aperçu d’image plus grand. « Afficher dans l’Explorer » ouvre la vue d’ensemble du système ou la fiche du corps existante si le favori appartient au système actuel de l’Explorer et si les données correspondantes sont disponibles. Pour les autres systèmes, les données enregistrées du favori restent visibles ; aucun itinéraire entre systèmes n’est calculé.</p>

<h3>Filtre de distance</h3>
<p>« Filtre de distance » est désactivé par défaut. « Distance max. : » vaut initialement 500 al, avec une plage de 1 à 100 000 al. La distance est mesurée depuis le système actuellement connu, avec les coordonnées de systèmes disponibles localement. Aucune requête en direct n’est faite uniquement pour ce filtre.</p>
<p>Les favoris dont la distance connue dépasse la limite sont masqués. Ceux dont la distance est inconnue restent visibles. Si les coordonnées du système actuel manquent, le filtre de distance ne masque aucune entrée. La recherche et les filtres de type et de catégorie restent appliqués. Le filtrage est recalculé automatiquement après un changement de système. L’activation et la distance maximale sont enregistrées.</p>

<h3>Exporter les favoris</h3>
<p>« Exporter » crée un ZIP portable contenant tous les favoris du commandant actif, pas seulement ceux affichés par la recherche ou les filtres de type, de catégorie ou de distance. favorites.json contient les données structurées des favoris ; les images disponibles figurent sous images/. Le paquet peut être transféré entre Linux et Windows.</p>
<p>Les favoris existants et les images originales restent inchangés. Les images de contenu identique ne sont stockées qu’une fois dans le paquet. Les images absentes ou endommagées n’empêchent pas l’export des données des favoris. L’import et l’export autorisent au maximum 32 MiB par fichier et 256 MiB au total pour le contenu non compressé du paquet.</p>

<h3>Importer les favoris</h3>
<p>« Importer » vérifie d’abord le ZIP et présente un résumé des favoris nouveaux et existants avant toute modification. Les favoris importés sont attribués au commandant actuellement actif. Les doublons sont identifiés par type, catégorie, nom et lieu : identifiants de système/corps et coordonnées connus, sinon noms de système/corps. Les doublons internes au paquet sont aussi pris en compte.</p>
<p>Un même choix s’applique à tous les doublons détectés : « Ignorer », par défaut, conserve les entrées existantes ; « Remplacer le favori existant » applique les données importées au favori existant ; « Importer comme nouvelle entrée » crée une entrée supplémentaire. Annuler n’importe rien.</p>
<p>Des données de favoris invalides bloquent tout l’import. En cas d’erreur d’import, les modifications de la base de données sont annulées pour éviter un import partiel. Les images absentes ou endommagées n’empêchent pas l’import de données valides ; ces favoris sont importés sans image. CMDRHelper gère localement les images importées.</p>

<h3>Enregistrer un système, une planète ou la position actuelle</h3>
<ul>
<li>« ★ Enregistrer le système actuel » enregistre le système actuel sans coordonnées de surface.</li>
<li>« ★ Enregistrer une planète / lune » permet de sélectionner une planète ou une lune connue du système actuel. Ce favori ne reçoit pas non plus de coordonnées de surface.</li>
<li>« ★ Enregistrer la position actuelle » se trouve en haut de la fenêtre des favoris, à côté des deux autres options d’enregistrement, et est également disponible dans le navigateur planétaire. Dans la fenêtre des favoris, le bouton reste toujours visible et est désactivé en l’absence de données de position planétaire actuelles valides et d’un commandant actif. Le clic fige le commandant, le système, le corps, la latitude et la longitude. Les déplacements ultérieurs dans le jeu ne modifient pas ces valeurs dans la boîte de dialogue ouverte.</li>
</ul>
<p>Saisis un nom de ton choix et sélectionne exactement une catégorie : Bio, Géo, Extraction, Panorama, Site d’atterrissage, Intéressant ou Autre. Une note et une image sont facultatives. Les identifiants techniques connus sont repris en interne ; tu n’as pas à les saisir. Une latitude ou une longitude de 0,0 est également valide.</p>
<p>« Modifier » modifie le nom, la catégorie, la note et l’image. Le système, le corps et les coordonnées enregistrées sont conservés. Pour enregistrer un autre lieu en surface, crée un nouveau favori à cette position.</p>

<h3>Favori rapide sans souris</h3>
<p>Dans « Paramètres → Favori rapide », tu peux librement définir, modifier ou supprimer un raccourci clavier global. Après l’installation, il est « Non attribué » par défaut : CMDRHelper n’enregistre aucune touche sans demande explicite. L’attribution est sauvegardée. Si une combinaison est déjà utilisée ou indisponible sur ton système, un message d’erreur s’affiche ; toute attribution qui fonctionnait auparavant est conservée.</p>
<p>Sous Linux/X11 et Windows, le raccourci fonctionne aussi lorsque Elite a le focus – à pied, en SRV et à bord du vaisseau. Une pression enregistre immédiatement la position actuelle à la surface pour le commandant actif, sans boîte de dialogue ni utilisation de la souris. Le commandant, le système, le corps et les valeurs actuelles de Latitude/Longitude sont figés à cet instant. Sans coordonnées planétaires actuelles valides, rien n’est enregistré ; les anciennes coordonnées ne sont pas réutilisées.</p>
<p>Le favori reçoit un nom provisoire unique, par exemple « Repère 07.09.2026 06:32:15 », et la catégorie « Autre ». Dans la fenêtre habituelle des favoris, tu peux ensuite le renommer, lui attribuer une autre catégorie, ajouter une note ou une image. Aucune capture d’écran n’est automatiquement prise ni importée.</p>
<p>Pendant environ deux secondes, « ★ FAVORI ENREGISTRÉ » s’affiche directement au-dessus de la fenêtre active d’Elite avec le corps et les coordonnées ; si la position est indisponible, « ⚠ AUCUNE COORDONNÉE PLANÉTAIRE » s’affiche brièvement. Cet affichage ne prend pas le focus et n’intercepte aucune entrée. Il fonctionne aussi lorsque le HUD de navigation est désactivé, puis disparaît complètement. Lorsque le HUD est activé, l’affichage normal de navigation reste ensuite visible. Le réglage enregistré du commutateur du HUD n’est pas modifié. L’affichage utilise la même infrastructure de superposition et les mêmes prérequis de plateforme que le HUD de navigation.</p>

<h3>Images des favoris</h3>
<p>Les images des favoris sont séparées de la rubrique Images. « Choisir une image … » accepte PNG, JPEG et WebP. CMDRHelper ne copie l’image sélectionnée dans son propre dossier d’images de favoris qu’à l’enregistrement. Le fichier original n’est ni déplacé ni modifié.</p>
<p>« Utiliser la dernière capture » relit à chaque clic le dossier source configuré et recherche des captures lisibles dont le nom est typique d’Elite. Sans configuration, les dossiers habituels de captures Elite sous Windows ou Steam/Proton sont pris en compte. Le dossier du commandant actif dans la destination de conversion configurée est également parcouru pour trouver les captures Elite converties correspondantes. Une capture convertie reste ainsi trouvable si son BMP original a été supprimé. Pour déterminer la capture la plus récente, une date et une heure non ambiguës dans le nom de fichier font foi, sinon la date du fichier ; pour les images converties, c’est l’heure de capture enregistrée dans le nom qui compte, et non l’heure de conversion. CMDRHelper ne déclenche pas lui-même de capture et ne parcourt pas des dossiers d’images quelconques.</p>
<p>Avant utilisation, le nom de fichier, la date et l’heure de capture et un aperçu fraîchement chargé sont affichés. Confirme avec « Utiliser cette image ». Si aucune capture appropriée n’est trouvée, tu peux toujours utiliser « Choisir une image … ». Les captures BMP d’Elite sont enregistrées sous forme de copie PNG interne.</p>
<p>Une image peut être remplacée dans la boîte de dialogue de modification ou désélectionnée avec « Retirer l’image ». L’enregistrement supprime la copie interne qui n’est plus utilisée. Si un fichier image manque, le favori reste utilisable sans aperçu.</p>
<p>Les images des favoris peuvent être exportées et sont copiées localement à l’import. Une copie interne partagée est conservée tant qu’un autre favori en a besoin. Lorsqu’un import remplace des favoris, les anciens fichiers image sont actuellement conservés par précaution.</p>

<h3>Cible du favori et commandant</h3>
<p>« ▶ Vers l’itinéraire » définit le système connu du favori comme destination dans le planificateur. Le départ suit le comportement existant et utilise l’AppState actuel ; un départ saisi manuellement est conservé. Aucun itinéraire n’est calculé automatiquement. « ◎ Vers les coordonnées » lance la navigation planétaire existante vers le lieu en surface avec le HUD existant si le système, le corps et des coordonnées valides sont enregistrés. Le voyage vers le système et la navigation en surface sont deux étapes distinctes, sans enchaînement automatique. Sans coordonnées de surface, seule l’action d’itinéraire est disponible ; les actions sans les données nécessaires sont masquées.</p>
<p>Pour les lieux en surface, « ◎ Vers les coordonnées » transmet le corps, la latitude, la longitude et le nom du favori enregistrés au navigateur planétaire existant. La nouvelle cible remplace la précédente. Les favoris n’ont aucune logique de navigation propre. Le navigateur continue de décider lui-même : des données planétaires valides et correspondantes activent la navigation ; sinon, il attend ces données.</p>
<p>Les favoris appartiennent exclusivement au commandant actif. Un changement de commandant actualise la liste et abandonne toute boîte de dialogue de modification ouverte. Une cible encore gérée comme cible favorite du commandant précédent est arrêtée. La sélection des commandants dans la chronique n’étend pas cette liste de favoris.</p>
<p>« Supprimer » demande une confirmation et ne supprime que l’enregistrement du favori et sa copie d’image interne. La capture originale ou l’image originale sélectionnée ainsi que toutes les données de l’Explorer, du journal et des corps sont conservées.</p>"""),
 'chronicle': (
        'Chronique',
        """<h2>Chronique</h2>
<h3>CMDRHelper</h3>
<p>Vue d’ensemble du système : la nouvelle présentation inspirée d’Elite remplace l’ancienne miniature dans Explorer et la Chronique. Étoiles et planètes forment la structure principale, les lunes se ramifient en dessous ; les systèmes multiples restent lisibles. Zoom, défilement, ajustement à la fenêtre et clic sur un corps donnent accès aux détails.</p>
<p>Ceintures d’astéroïdes compactes : les amas sont regroupés en ceintures dans la vue d’ensemble et les cartes habituelles d’Explorer et de la Chronique. Toutes les données individuelles sont conservées.</p>
<p>La chronique est l’historique personnel des voyages et des découvertes du commandant. Elle utilise les informations du journal enregistrées durablement pour retrouver les systèmes déjà visités, les représenter dans l’espace et rechercher des découvertes connues.</p>

<h3>Systèmes visités</h3>
<p>La Chronique montre les systèmes visités et leurs emplacements dans la galaxie connus du Commandant.</p>
<p>Si elles sont disponibles, la première et la dernière visite ainsi que les informations connues sur les corps célestes sont prises en compte.</p>
<p>Lorsqu’une période est active, le nombre de visites, la première visite et la dernière visite dans la carte se rapportent aux visites réelles de systèmes retenues par le filtre.</p>
<p>La chronique n'est donc pas seulement une carte, mais aussi un outil permettant de retrouver des destinations de voyage et des découvertes antérieures.</p>

<h3>carte 3D</h3>
<p>Les systèmes visités sont représentés spatialement en utilisant leurs coordonnées galactiques X/Y/Z.</p>
<p>Le mode d'emploi se trouve directement au-dessus de la carte :</p>
<ul>
<li>Maintenez le bouton gauche de la souris enfoncé → faire pivoter la vue</li>
<li>maintenir le bouton central de la souris et faire glisser → tracer une fenêtre de zoom</li>
<li>Maintenez le bouton droit de la souris enfoncé → déplacer la vue</li>
</ul>
<p>Le petit indicateur des axes aide à s’orienter dans l’espace.</p>

<p>La molette permet de zoomer ou dézoomer sans touche supplémentaire.</p>
<p>Un double-clic dans une zone vide de la carte rétablit la vue inclinée initiale, annule le déplacement et ajuste tous les systèmes actuellement affichés à la fenêtre. Les filtres et le système sélectionné sont conservés.</p>
<p>Au début d’une rotation avec le bouton gauche, le système cliqué devient le pivot. Dans une zone vide, le point sous le pointeur sur le plan galactique sert de pivot ; si la vue est presque horizontale, le centre de la carte sur ce plan est utilisé. L’alignement tourne lui aussi autour du pivot actuel.</p>
<p>Cliquez sur un système pour ouvrir sa fenêtre de détails. Un clic gauche sur son nom en haut ou sur l’icône ⧉ voisine copie uniquement le nom du système dans le presse-papiers. Un bref ✓ confirme la copie.</p>

<h3>Position actuelle</h3>
<p>Avec « Position actuelle », la vue de la carte peut être alignée ou renvoyée à l'emplacement actuellement connu du commandant actif.</p>
<p>Les filtres actuels sont d’abord appliqués. La vue n’est centrée sur le système actuel que s’il figure dans la carte obtenue.</p>
<p>Sinon, le message « Le système actuel n’est pas inclus dans cette sélection de filtres. » apparaît. Les filtres ne sont pas supprimés pour autant.</p>

<h3>Aligner</h3>
<p>« Aligner » rétablit une vue de dessus du plan galactique. Le déplacement et le zoom sont conservés.</p>
<p>C’est utile lorsque de nombreuses rotations ont rendu la carte difficile à lire.</p>

<h3>Actualiser la Chronique</h3>
<p>« Actualiser la Chronique » recharge les données de la chronique selon les filtres combinés actuels et actualise l’affichage. Le texte libre, les bornes de date activées et les filtres miniers sont de nouveau évalués ensemble ; les filtres actifs ne sont pas ignorés.</p>
<p>La fonction ne modifie pas les fichiers journaux et ne crée pas de nouvelles données d’exploration. Elle actualise simplement l’affichage de la chronique à partir des données CMDRHelper existantes.</p>

<h3>Recherche de texte libre</h3>
<p>Le champ « Rechercher dans la chronique … » permet de rechercher du contenu déjà connu.</p>
<p>La recherche prend en compte – si disponible dans la base de données – entre autres :</p>
<ul>
<li>Noms de systèmes</li>
<li>Caractéristiques du corps</li>
<li>données biologiques</li>
<li>Matériaux</li>
<li>Données du Codex</li>
</ul>
<p>Le texte libre, la période et l’extraction minière partagent une même zone de filtres. « Appliquer » évalue ensemble les filtres définis. Entrée dans le champ de texte libre lance le même filtrage combiné que « Appliquer ».</p>

<h3>Période Du/Au (UTC)</h3>
<p>Active « Du » et « Au » à l’aide de leurs cases respectives et choisis la date souhaitée. Une seule borne est également possible. Sans case activée, il n’y a aucune restriction temporelle de ce côté ; si aucune des deux cases n’est activée, aucune période n’est imposée.</p>
<ul>
<li><b>Du :</b> À partir du début du jour calendaire UTC sélectionné, inclus.</li>
<li><b>Au :</b> L’intégralité du jour calendaire UTC sélectionné est prise en compte, jusqu’à l’instant précédant le début du jour suivant.</li>
</ul>
<p>UTC signifie temps universel coordonné. Les bornes de date portent sur les jours calendaires UTC, pas sur ceux de ton fuseau horaire local.</p>
<p>Le filtre porte sur les visites réelles de systèmes enregistrées dans <code>system_visits</code>. Une visite réelle du commandant concerné pendant la période est nécessaire. Les valeurs enregistrées <code>first_seen</code> et <code>last_seen</code> ne remplacent pas une visite réelle : une période située simplement entre une première visite antérieure et une dernière visite postérieure ne suffit pas.</p>
<p>La période filtre les visites, pas les événements individuels de découverte, BIO, GEO ou d’extraction minière. Les informations sur les découvertes connues et les quantités extraites restent des totaux enregistrés. Du/Au peuvent être utilisés seuls ou avec le texte libre et les filtres miniers.</p>
<p>Si Du est postérieur à Au, le message « La date Du ne doit pas être postérieure à la date Au. » apparaît. Aucune requête de base de données n’est lancée. Corrige les bornes de date et applique de nouveau les filtres.</p>

<h3>Résultats de la recherche</h3>
<p>Les résultats apparaissent dans la liste existante sous la carte de la chronique.</p>
<p>Selon le type de résultat, le système, le corps céleste et des informations complémentaires peuvent apparaître.</p>
<p>Un résultat permet de retrouver le système ou le corps céleste correspondant déjà connu et d’ouvrir les informations détaillées existantes.</p>

<h3>Aucun résultat</h3>
<p>Si un filtrage valide ne trouve aucune correspondance, la carte et les itinéraires sont vidés. La liste des résultats est vidée et masquée, l’affichage détaillé est réinitialisé et toute fenêtre ouverte de détails d’un système de la chronique est fermée.</p>
<p>Les anciens résultats ne restent pas visibles. Dans ce cas, vérifie la combinaison du texte recherché, de la période et des filtres miniers, ainsi que le commandant utilisé pour la vue concernée.</p>

<h3>Sites miniers planétaires</h3>
<p>Le filtre « Sites miniers planétaires » peut être utilisé pour rechercher spécifiquement des corps connus pour lesquels Elite Dangerous a signalé des sites miniers planétaires.</p>
<p>L'affichage sous-jacent correspond à celui connu depuis Explorer :</p>
<p><b>ABBAU ×N</b></p>
<p>Le nombre appartient au corps lui-même et ne dépend pas du commandant.</p>

<h3>Au moins</h3>
<p>En utilisant « Au moins », vous pouvez spécifier le nombre minimum d’emplacements miniers planétaires qu’un corps doit avoir.</p>
<p>Exemple:</p>
<p><b>Au moins 20</b></p>
<p>ne montre que les corps connus avec au moins :</p>
<p><b>ABBAU ×20</b></p>
<p>Cela permet de localiser spécifiquement des zones minières particulièrement étendues.</p>

<h3>Mes découvertes minières</h3>
<p>« Mes découvertes minières » limite la recherche aux corps sur lesquels le commandant consulté a effectivement pratiqué lui-même l’extraction de surface.</p>
<p>Ces informations proviennent de l’historique personnel d’extraction de surface et sont strictement séparées pour chaque commandant.</p>
<p>Un corps peut donc présenter des signaux globaux ABBAU ×N sans que le commandant y ait déjà extrait quoi que ce soit.</p>

<h3>Marchandise</h3>
<p>Lorsque « Mes découvertes minières » est activé, la sélection « Marchandise » est également disponible.</p>
<p>La liste ne contient que les marchandises que le commandant consulté a réellement extraites en surface.</p>
<p>Il ne s’agit pas d’une liste théorique de toutes les matières premières minières possibles.</p>
<p>Pour EXAMPLE, la sélection peut par exemple contenir :</p>
<ul>
<li>Tous</li>
<li>cuivre</li>
</ul>
<p>Si des matières premières supplémentaires sont effectivement extraites ultérieurement, elles apparaîtront automatiquement dans votre sélection personnelle.</p>

<h3>Recherche ciblée de matières premières</h3>
<p>Si « Cuivre » est sélectionné puis « Appliquer » activé, la chronique ne montre que les corps sur lesquels le commandant consulté a effectivement extrait du cuivre.</p>
<p>Exemple:</p>
<p><b>Example System / 2 — ABBAU ×12 — cuivre 40 t</b></p>
<p>Cela signifie que la chronique peut être utilisée comme base de données de localisation personnelle : une matière première déjà extraite peut être retrouvée ultérieurement.</p>

<h3>Toutes les matières premières</h3>
<p>« Marchandise : Tous » prend en compte toutes les découvertes personnelles d’extraction de surface correspondantes.</p>
<p>Si plusieurs marchandises sont connues sur un corps, elles peuvent être affichées avec les quantités que le commandant a lui-même extraites jusqu’à présent.</p>
<p>Exemple:</p>
<p><b>ABBAU ×12 — Hélium-3 10 t, cuivre 40 t</b></p>
<p>Les quantités sont les quantités personnelles extraites par le commandant concerné, effectivement attestées par les événements du journal.</p>
<p>Même lorsqu’une période est active, les quantités personnelles extraites restent des quantités totales enregistrées. <b>Cuivre 40 t</b> ne signifie pas automatiquement <b>40 t pendant la période sélectionnée</b>. La période exige une visite de système correspondante, mais ne limite pas la quantité extraite affichée à cette période.</p>

<h3>Combiner les filtres</h3>
<p>Le texte libre, les bornes Du/Au activées et les filtres miniers peuvent être combinés. Un résultat doit satisfaire simultanément les conditions définies.</p>
<p>Par exemple:</p>
<ul>
<li>Sites miniers planétaires actifs</li>
<li>Au moins 20</li>
<li>Mes découvertes minières activé</li>
<li>Marchandise cuivre</li>
</ul>
<p>recherche des corps connus avec au moins 20 sites miniers planétaires où le commandant en question a déjà extrait lui-même du cuivre.</p>
<p>Tout texte de recherche supplémentaire est également pris en compte. Si une période est ajoutée, le commandant consulté doit avoir réellement visité le système concerné pendant cette période ; l’extraction du cuivre elle-même ne doit pas nécessairement avoir eu lieu pendant cette période.</p>

<h3>Appliquer</h3>
<p>« Appliquer » lance un filtrage combiné avec tous les filtres de recherche, de période et d’extraction minière actuellement définis :</p>
<ul>
<li>Texte libre</li>
<li>Du, si activé</li>
<li>Au, si activé</li>
<li>Sites miniers planétaires</li>
<li>Nombre minimal</li>
<li>Mes découvertes minières</li>
<li>Marchandise, si « Mes découvertes minières » est activé</li>
</ul>
<p>Entrée dans le champ de texte libre lance exactement le même filtrage. Sans texte libre ni filtres miniers, la carte normale est chargée pour les commandants cochés sur la carte, avec une restriction Du/Au le cas échéant.</p>

<h3>Réinitialiser</h3>
<p>« Réinitialiser » rétablit l’état initial de la zone de filtres commune :</p>
<ul>
<li>Le texte libre est effacé.</li>
<li>Du et Au sont désactivés ; les champs de date affichent de nouveau la date du jour et sont désactivés.</li>
<li>Sites miniers planétaires est désactivé.</li>
<li>Le nombre minimal est remis à 0.</li>
<li>Mes découvertes minières est désactivé.</li>
<li>Marchandise est remis sur « Tous ».</li>
</ul>
<p>La sélection des commandants est conservée. La chronique normale est ensuite rechargée pour cette sélection de carte ; les anciens résultats de recherche et affichages détaillés sont réinitialisés.</p>

<h3>Sélection du commandant</h3>
<p>La chronique peut afficher les données de différents commandants connus.</p>
<p>Deux concepts de sélection sont distingués :</p>
<ul>
<li><b>Sélection des commandants de la carte :</b> Les cases des commandants déterminent quels itinéraires de commandants apparaissent dans la carte normale sans recherche de texte libre ou minière. Une période activée est prise en compte.</li>
<li><b>Commandant consulté :</b> Les recherches personnelles de texte libre ou minières utilisent le commandant consulté (<code>viewed_commander_id</code>), à défaut le commandant actif. Les listes personnelles de marchandises dépendent également de ce commandant.</li>
</ul>
<p>Cependant, les informations personnelles telles que vos propres découvertes minières et listes de matières premières sont toujours évaluées séparément pour le commandant réellement consulté.</p>
<p>Un commandant ne voit dans sa sélection de matières premières aucune découverte minière appartenant exclusivement à un autre commandant.</p>

<h3>Tous les commandants</h3>
<p>L'affichage de la carte/chronique peut prendre en compte plusieurs commandants.</p>
<p>« Tous les commandants » concerne la sélection des commandants de la carte. Les cases des commandants n’étendent pas automatiquement les recherches personnelles de texte libre ou minières à plusieurs commandants.</p>
<p>Cela ne modifie pas l'attribution personnelle des données relatives au commandant. Les propriétés astronomiques globales d'un système ou d'un corps restent partagées, les découvertes personnelles restent séparées.</p>

<h3>Aide à la recherche / légende</h3>
<p>Des informations complémentaires sur la recherche de chroniques et la signification de l'affichage sont accessibles via « Aide à la recherche / Légende ».</p>
<p>Un clic sur un terme de recherche le place dans le champ de recherche et lance la recherche avec les filtres de période et miniers déjà définis.</p>
<p>Cette aide principale contextuelle complète les brèves instructions d'utilisation qui y sont disponibles.</p>

<h3>Conseil</h3>
<p>La chronique est particulièrement adaptée pour retrouver des lieux intéressants découverts au cours d'un voyage plus long.</p>
<p>Pour l’extraction de surface, par exemple, elle peut répondre :</p>
<p>« Sur quelle planète ai-je déjà extrait du cuivre ? »</p>
<p>ou:</p>
<p>« Laquelle de mes planètes connues possède un nombre particulièrement élevé de sites miniers ? »</p>""",
    ),
 'jump_tip': (
        'Analyse',
        """
<h2>Analyse</h2>
<p>L’analyse utilise votre historique personnel d’exploration. Analyse du système évalue un nom procédural saisi ; Données historiques conserve l’ancienne analyse des codes avec les résultats passés et la réévaluation. Ces deux outils aident à décider sans garantir de découvertes.</p>
<h3>Base de comparaison</h3>
<p>Le code de masse fournit l’estimation de base. La région et la famille l’affinent prudemment. Les petits échantillons locaux sont lissés vers la base plus large. Peu de données signifie une incertitude, pas une mauvaise évaluation. Les systèmes insuffisamment étudiés ne comptent pas comme résultats négatifs.</p>
<h3>Indice de potentiel</h3>
<p>L’indice de potentiel 100 représente votre moyenne historique personnelle du potentiel d’exploration atténué. Ce n’est pas une probabilité en pourcentage. Un scénario de cartographie uniforme et des valeurs extrêmes atténuées permettent la comparaison ; médiane et potentiel lissé sont des crédits estimés, pas des gains garantis.</p>
<h3>Découvertes remarquables</h3>
<p>Le numéro final du système n’est pas évalué : Plio Aip KN-B d13-201 appartient à la famille Plio Aip KN-B d13. BIO est informatif et ne contribue pas à l’évaluation principale. L’absence d’analyses ne prouve pas une valeur nulle.</p>
<h3>Analyse du système</h3>
<p>Saisissez un système et cliquez sur Analyser ou appuyez sur Entrée. Utiliser le système actuel reprend le nom de l’état de jeu existant. Le recalcul nécessite une action de l’utilisateur. La base et les résultats précisent leur niveau ; sans comparaison locale, l’expérience du niveau supérieur est utilisée. La qualité des données est distincte de la recommandation.</p>
<p>Le champ « Système » accepte un nom saisi librement. « Utiliser le système actuel » remplit seulement ce champ ; lancez ensuite « Analyser » ou appuyez sur Entrée. Le nom est vérifié localement selon le modèle de nom procédural pris en charge. Il n’y a ici ni recherche de système en ligne ni liste pour départager les noms ambigus.</p>
<p>Une saisie vide, un nom non pris en charge, l’absence de données comparatives qualifiées ou une erreur remplace le résultat précédent par un message. Une analyse réussie affiche la recommandation, l’indice de potentiel et la base de données locale. Le tableau compare code de masse, région et famille avec le nombre de systèmes et la base de données ; les valeurs historiques et découvertes particulières connues figurent dessous.</p>
<h3>Données historiques</h3>
<p>Résultats historiques par code système. Ces valeurs décrivent votre expérience d’exploration passée et ne constituent pas une prédiction directe pour un système cible individuel. La base et la solidité des données décrivent la fiabilité des comparaisons selon l’échantillon disponible et sa répartition entre les secteurs.</p>
<p>Dans « Données historiques », choisissez sous « Cible » un type de découverte, et non une destination : par exemple une cible d’exploration, un genre ou une espèce BIO. La première évaluation se fait à la création de la vue. Après modification de la cible ou du minimum, le classement précédent reste affiché jusqu’à « Réévaluer ».</p>
<p>Le champ numérique à côté du choix de cible fixe l’échantillon minimal par code : de 1 à 50 systèmes étudiés, initialement 3. Les codes ayant moins de systèmes ou aucune découverte historique du type choisi sont exclus du classement.</p>
<p>Le tableau « Tendances historiques » présente jusqu’à 50 codes avec rang, succès passés (systèmes avec découverte / systèmes étudiés), taux de réussite et solidité des données. L’ordre repose sur l’évaluation historique lissée, pas uniquement sur le taux de réussite. Les deux tableaux ont un ordre fixe, sans tri par colonne ni action de détail. Un message signale l’absence de motifs correspondants ; une erreur d’évaluation vide le classement et affiche un message d’erreur. L’analyse ne calcule aucun itinéraire.</p>
""",
    ),
 'route_planner': ("Planificateur d'itinéraire",
                   """<h2>Planificateur d'itinéraire</h2>
<h3>Vue d’ensemble</h3>
<p>Le planificateur calcule des trajets entre systèmes via Spansh. Choisissez « Itinéraire du vaisseau » ou « Fleet Carrier / CTSVision ». Une connexion réseau est nécessaire ; CMDRHelper ne pilote ni vaisseau ni porte-vaisseaux.</p>

<h3>Départ et destination</h3>
<p>« Système de départ » suit le système actuel connu du commandant actif jusqu’à la saisie d’un départ personnel. Vider le champ rétablit ce comportement. Saisissez le nom complet dans « Système de destination » ; une destination reprise des favoris prépare la route du vaisseau sans lancer le calcul.</p>
<p>Le départ et la destination doivent être identifiés sans ambiguïté. Aucun nom approchant n’est substitué. Un nom inconnu ou ambigu entraîne un message : corrigez la saisie.</p>

<h3>Route de vaisseau</h3>
<p>Il n’y a pas de sélecteur de vaisseau : les données connues du vaisseau actif préremplissent les champs techniques. Vos modifications restent prioritaires. « Appliquer les données du vaisseau » reprend les données disponibles. Vérifiez l’indication de données complètes, incomplètes, anciennes ou de FSD inconnu.</p>
<p>Vérifiez « Capacité du réservoir principal », « Cargaison actuelle », « Masse de base », « Capacité du réservoir de réserve », « Carburant de réserve », « Masse optimale du FSD », « Carburant FSD maximal par saut », « Puissance carburant », « Multiplicateur carburant » et « Bonus de portée ». La capacité de saut découle de ces valeurs ; aucun champ unique ne définit la portée normale du vaisseau. Cargaison et équipement peuvent modifier la portée réelle.</p>

<h3>Options du vaisseau et calcul</h3>
<p>« Algorithme de routage » propose optimistic, pessimistic, fuel, fuel_jumps et guided. Ce choix est transmis à Spansh.</p>
<p>Les options sont « Utiliser la surcharge/les étoiles à neutrons », « Le vaisseau démarre déjà surchargé », « Utiliser les injections FSD », « Exclure les étoiles secondaires » et « Faire le plein à chaque étoile récupérable » : assistance neutronique, départ déjà renforcé, injections FSD, étoiles secondaires et ravitaillement. Lancez « Calculer l’itinéraire avec Spansh ».</p>

<h3>Route de porte-vaisseaux</h3>
<p>« Fleet Carrier / CTSVision » planifie sans sélectionner ni commander un porte-vaisseaux particulier. Renseignez « Tritium dans le réservoir » et « Tritium dans le stockage du porte-vaisseaux », au maximum 25 000 t ensemble. « Masse calculée du porte-vaisseaux » indique 25 000 t plus ces deux quantités.</p>
<p>« Portée de saut maximale » accepte de 1 à 500 ly, avec 500 ly par défaut. « Calculer avec Spansh » lance le calcul. Le bouton est désactivé pendant cette requête.</p>

<h3>Spansh et attente</h3>
<p>Le calcul est effectué en arrière-plan par Spansh. L’état indique la requête puis la réussite ou l’échec. Il s’agit de routes, pas de prix commerciaux ni d’informations de stations. Cette vue n’a pas de bouton pour annuler un calcul en cours.</p>

<h3>Résultat de la route</h3>
<p>La liste conserve l’ordre de la route : numéro, système, distance du saut et distance restante. Elle n’est pas librement triable. Pour les vaisseaux s’ajoutent consommation, carburant restant, neutron et ravitaillement ; pour les porte-vaisseaux, consommation de tritium.</p>
<p>Les totaux indiquent distance, nombre de sauts et consommation ou tritium estimé. Les valeurs absentes restent « – ». Comparez le plan à la situation réelle en jeu.</p>

<h3>Progression et prochaine cible</h3>
<p>Une route de vaisseau calculée avec succès est adoptée automatiquement. « Système actuel », « Prochaine destination » et « État de l’itinéraire » indiquent position, prochaine étape et état. La liste reste affichée, sans coches supplémentaires pour les étapes parcourues.</p>
<p>Un saut de vaisseau reconnu vers le prochain système ou un système ultérieur de la route fait avancer la progression et copie automatiquement le nom du système suivant. Les messages de position répétés et les sauts de porte-vaisseaux ne font pas avancer ainsi la route.</p>
<p>Charger la route ne copie aucun nom automatiquement. Utilisez « Copier la prochaine destination », au début ou plus tard tant qu’une cible suivante existe. Seul le nom du système est copié : aucun collage automatique ni pilotage d’Elite.</p>

<h3>Écart et arrivée</h3>
<p>Un saut hors de la suite de la route affiche « Le système actuel est hors itinéraire ». La route et la précédente prochaine cible restent disponibles, sans recalcul automatique. Un saut ultérieur correspondant peut reprendre la progression. Vous pouvez aussi recalculer volontairement une route.</p>
<p>Au dernier système, « Itinéraire terminé » apparaît. « Prochaine destination » devient « – », la copie est désactivée et aucun autre nom n’est copié. Le presse-papiers n’est pas vidé. La liste reste affichée.</p>

<h3>Export CTSVision</h3>
<p>Seule la route de porte-vaisseaux propose « Exporter pour CTSVision ». Après le calcul, choisissez un nouveau fichier CSV. Il contient la succession des systèmes et les données disponibles de distance, carburant, tritium et réapprovisionnement pour une utilisation ultérieure dans CTSVision.</p>
<p>C’est un export de fichier, sans connexion directe ni commande automatique du porte-vaisseaux. Aucun fichier existant n’est écrasé. Annuler le dialogue ne crée rien ; les erreurs d’écriture sont signalées.</p>

<h3>Erreurs et conseils</h3>
<p>Les systèmes manquants, paramètres incomplets ou invalides et quantités excessives de tritium sont signalés. Les valeurs requises de réservoir, masse et FSD doivent être positives ; la réserve ne doit pas dépasser la capacité du réservoir de réserve.</p>
<p>L’absence de route, les problèmes réseau, une attente excessive ou une réponse inutilisable de Spansh donnent un message, jamais un résultat inventé. Vérifiez noms, données du vaisseau et options avant de relancer.</p>

<h3>Analyse et commandant</h3>
<p>« Analyse », avec « Analyse du système » et « Données historiques », évalue les systèmes et les expériences disponibles. Le planificateur calcule le trajet concret entre départ et destination.</p>
<p>Les valeurs proposées viennent du commandant actif et de son vaisseau. Consulter un autre commandant dans la vue CMDR ne change pas cette base.</p>"""),
 'images': ('Photos',
            '<h2>Photos</h2>\n'
            "<p>La section « Images » gère les captures d'écran prises avec Elite Dangerous. Le "
            'CMDRHelper peut reconnaître automatiquement les nouveaux enregistrements, les traiter '
            'et les stocker dans une galerie basée sur le commandant.</p>\n'
            '\n'
            '<h3>Dossier source</h3>\n'
            '<p>Le dossier source est le dossier dans lequel Elite Dangerous enregistre ses '
            "captures d'écran au format BMP.</p>\n"
            '<p>CMDRHelper peut surveiller ce dossier pour détecter de nouveaux fichiers BMP. Pour '
            "que le traitement automatique fonctionne, le dossier de capture d'écran correct doit "
            'être défini.</p>\n'
            '\n'
            '<h3>Dossier de destination</h3>\n'
            '<p>Le dossier de destination est le dossier racine commun aux images traitées par '
            'CMDRHelper.</p>\n'
            "<p>L'utilisateur définit ce dossier racine. CMDRHelper crée automatiquement les "
            'sous-dossiers requis liés au commandant pendant le traitement.</p>\n'
            '\n'
            '<h3>Enregistrer les paramètres</h3>\n<p>« Enregistrer les paramètres » enregistre les dossiers source et destination, le format de sortie, l’éclaircissement et les deux cases à cocher. La surveillance est réinitialisée avec ces choix ; les BMP existants sont marqués comme connus. La galerie est également actualisée.</p>\n<p>« Actualiser la galerie » recharge la galerie à partir des images existantes pour le filtre actuel. Cette action ne lance aucune conversion BMP.</p>\n\n<h3>Traitement automatique</h3>\n'
            '<p>Si «Convertir automatiquement les nouveaux fichiers BMP» est activé et que des dossiers source et de '
            'destination valides sont définis, CMDRHelper vérifie régulièrement le dossier source '
            "pour de nouvelles captures d'écran BMP.</p>\n"
            "<p>Lorsqu'ils sont activés, les fichiers BMP existants sont initialement marqués "
            'comme connus et ne sont pas automatiquement convertis sans que cela vous soit '
            'demandé. La fonction distincte de conversion des BMP existants est disponible à cet '
            'effet.</p>\n'
            "<p>Un nouveau fichier n'est pas mis en file d'attente tant qu'il n'a pas la même "
            'taille non nulle lors de deux vérifications consécutives. Par conséquent, une '
            'opération d’écriture toujours en cours n’est pas traitée immédiatement.</p>\n'
            '\n'
            "<h3>Conversion d'images</h3>\n"
            '<p>En tant que source, CMDRHelper traite les fichiers BMP. « PNG » ou « JPG » peuvent '
            'être sélectionnés comme format cible.</p>\n'
            '<p>Les fichiers JPG sont enregistrés au niveau de qualité 95. Les fichiers PNG sont '
            'enregistrés de manière optimisée.</p>\n'
            "<p>Par défaut, le fichier BMP d'origine est conservé. Si «Supprimer le BMP après "
            "une conversion réussie» est activé, le BMP source ne sera supprimé qu'une fois l'image "
            'cible enregistrée avec succès.</p>\n'
            '\n'
            "<h3>Éclaircir l'image</h3>\n"
            "<p>L'éclaircissement est ajusté de 0 à 50 pour cent à l'aide d'un curseur et d'un "
            'champ numérique lié. Le réglage est enregistré.</p>\n'
            '<p>Il est automatiquement appliqué lors de chaque conversion démarrée par la suite, à '
            'la fois pour les fichiers BMP existants nouvellement surveillés et lancés '
            "manuellement. 0 pour cent reprend la luminosité d'origine ; des valeurs plus élevées "
            "augmentent en conséquence la luminosité de l'image PNG ou JPG générée.</p>\n"
            "<p>La fonction n'est pas un pur aperçu et n'est pas appliquée ultérieurement à une "
            'image sélectionnée dans la galerie. La luminosité modifiée est enregistrée dans le '
            'nouveau fichier cible.</p>\n'
            '<p>Le BMP source reste inchangé sauf si la suppression du fichier BMP est également '
            "activée. Les données du journal, du commandant et de l'exploration ne sont pas "
            'modifiées.</p>\n'
            '\n'
            '<h3>Stockage lié au commandant</h3>\n'
            "<p>De nouvelles captures d'écran sont attribuées au commandant en cours de jeu en "
            "fonction de l'identité du journal présente dans l'AppState en direct actif.</p>\n"
            "<p>La structure des dossiers contient le nom du commandant et l'ID Frontier, par "
            'exemple\xa0:</p>\n'
            '<p><b>EXAMPLE_F12345678/</b></p>\n'
            '<p>Le FID maintient la mission claire même avec plusieurs commandants. Cela permet de '
            'distinguer deux commandants portant le même nom.</p>\n'
            '\n'
            '<h3>noms de fichiers</h3>\n'
            "<p>Les nouvelles images traitées reçoivent un nom avec l'heure de capture, le nom du "
            'commandant et - si disponible - le système stellaire connu lors de la file '
            "d'attente.</p>\n"
            '<p>Exemple:</p>\n'
            '<p><b>2026-09-04_&#8203;13-18-22_&#8203;EXAMPLE_&#8203;Sol.png</b></p>\n'
            '<p>Le FID se trouve dans le nom du dossier associé au commandant, et non dans le nom '
            'du fichier image.</p>\n'
            '\n'
            '<h3>Noms de fichiers sécurisés</h3>\n'
            '<p>CMDRHelper nettoie les noms de commandant et de système pour les utiliser comme '
            'composants de fichiers et de dossiers.</p>\n'
            '<p>Les contrôles illégaux et les caractères Windows sont remplacés, les espaces sont '
            'unifiés, les points problématiques ou les espaces de fin sont supprimés et les noms '
            'Windows réservés tels que CON ou NUL sont sécurisés.</p>\n'
            '\n'
            "<h3>Durée d'enregistrement</h3>\n"
            "<p>Pour le nommage, CMDRHelper utilise l'heure de modification du fichier BMP reconnu "
            "stable. Ce n'est que si celle-ci ne peut pas être lue que l'heure actuelle sera "
            'utilisée.</p>\n'
            '<p>Cela signifie que le nom dépend généralement du fichier source et non du temps de '
            'conversion ultérieur.</p>\n'
            '\n'
            '<h3>Plusieurs images dans la même seconde</h3>\n'
            '<p>Si le nom de fichier souhaité existe déjà ou est réservé pour une conversion en '
            "cours, CMDRHelper l'ajoute "
            'continuellement <code>_2</code>,<code>_3</code>,<code>_4</code> et ainsi de suite.</p>\n'
            "<p>Cela signifie qu'une autre capture d'écran avec le même horodatage n'écrasera pas "
            'une image cible existante.</p>\n'
            '\n'
            '<h3>Changement de commandant pendant le traitement</h3>\n'
            '<p>Le Commander, le FID et le système sont capturés ensemble lors de la mise en file '
            "d'attente d'une capture d'écran.</p>\n"
            '<p>Un changement ultérieur de commandant ne modifie pas l’affectation de cette image '
            "déjà en attente. Cela signifie qu'une capture d'écran de EXAMPLE n'est pas ensuite "
            "écrite dans le dossier d'un autre commandant.</p>\n"
            '\n'
            '<h3>galerie</h3>\n'
            '<p>La galerie affiche les fichiers PNG, JPG et JPEG des répertoires associés au '
            'filtre sélectionné. Des images nouvelles, supprimées ou déplacées sont régulièrement '
            'détectées.</p>\n'
            "<p>Le filtre de galerie ne modifie pas l'emplacement de stockage ni l'affectation du "
            'commandant des fichiers.</p>\n'
            '\n'
            '<h3>Commandant actuel</h3>\n'
            '<p>Le filtre Current Commander affiche les images du dossier du commandant '
            'actuellement affiché dans la vue CMDR.</p>\n'
            "<p>Le commandant en question détermine uniquement l'affichage de la galerie. D'un "
            "autre côté, l'attribution d'une nouvelle capture d'écran en direct utilise l'identité "
            "du journal active lors de la mise en file d'attente.</p>\n"
            '\n'
            '<h3>Tous les commandants</h3>\n'
            '<p>Le filtre « Tous les commandants » affiche ensemble les images des sous-dossiers '
            'valides de tous les commandants connus. Le dossier spécial pour les enregistrements '
            'sans identité reconnue est également pris en compte.</p>\n'
            '<p>Les fichiers ne sont ni déplacés ni fusionnés.</p>\n'
            '\n'
            '<h3>Non attribué</h3>\n'
            '<p>Le filtre Non attribué affiche les fichiers image pris en charge situés '
            'directement dans le dossier racine cible partagé.</p>\n'
            '<p>En particulier, les images plus anciennes sans sous-dossiers liés au commandant '
            'restent visibles. CMDRHelper n’essaie pas de deviner leur affiliation après '
            'coup.</p>\n'
            '\n'
            '<h3>Images existantes</h3>\n'
            '<p>Les images existantes dans le dossier racine ne sont pas automatiquement déplacées '
            'ou renommées.</p>\n'
            "<p>Ils restent accessibles via « Non attribués » tant qu'ils sont disponibles au "
            'format PNG, JPG ou JPEG.</p>\n'
            '\n'
            "<h3>Sélectionner et afficher l'image</h3>\n"
            "<p>Un simple clic sur une image d'aperçu montre l'image mise à l'échelle dans la zone "
            "d'aperçu et affiche son nom de fichier.</p>\n"
            "<p>Un double clic ouvre le fichier avec l'application du système d'exploitation "
            'définie pour les images.</p>\n'
            '<p>Plusieurs images peuvent être marquées en même temps. Lorsque vous modifiez la '
            "taille de la fenêtre, l'aperçu de l'image actuelle est redimensionné pour "
            "s'adapter.</p>\n"
            '\n'
            "<h3>Supprimer l'image</h3>\n"
            "<p>Les images marquées peuvent être supprimées à l'aide de «\xa0Supprimer la "
            'sélection\xa0» ou de la touche Suppr. Avant la suppression, une requête de sécurité '
            "apparaît\xa0; Sans sélection, la sélection nécessaire est d'abord indiquée.</p>\n"
            '<p>Seuls les fichiers cibles PNG/JPG/JPEG sélectionnés sont supprimés des répertoires '
            "du filtre de galerie actuel. Le fichier source BMP d'origine n'est pas affecté.</p>\n"
            '\n'
            '<h3>Ouvrir le dossier cible</h3>\n'
            "<p>«\xa0Ouvrir le dossier cible\xa0» ouvre l'emplacement de stockage dans le "
            'gestionnaire de fichiers et crée le dossier racine partagé si nécessaire.</p>\n'
            "<p>Le filtre « Current Commander » ouvre son sous-dossier Commander existant. S'il "
            "n'existe pas encore ou qu'un autre filtre est actif, le dossier racine partagé sera "
            'ouvert.</p>\n'
            '\n'
            "<h3>Sécurité des chemins d'images</h3>\n"
            '<p>Avant la suppression, CMDRHelper vérifie le chemin canonique de chaque fichier. Il '
            'doit se trouver dans le dossier cible configuré et directement dans un répertoire '
            'autorisé par le filtre de galerie actuel.</p>\n'
            '<p>Les liens symboliques ne sont pas utilisés comme dossiers de commande ou images de '
            'galerie et ne sont pas supprimés via la galerie. Les chemins en dehors de la zone '
            'cible et les chemins de traversée sont rejetés.</p>\n'
            '\n'
            "<h3>Si aucun commandant n'a été détecté</h3>\n"
            "<p>Si Commander et FID sont manquants lors de la mise en file d'attente d'un nouvel "
            'enregistrement, le fichier ne sera pas mis en attente et ne sera pas attribué à un '
            'Commander connu.</p>\n'
            '<p>Ce sera dans le sous-dossier <b>UNKNOWN_&#8203;UNKNOWN/</b> traité; le nom de fichier '
            'également utilisé pour le Commander <b>UNKNOWN</b>. Ce dossier peut être consulté via '
            'Tous les commandants, et non via le filtre du dossier racine non alloué.</p>\n'
            '\n'
            '<h3>Plusieurs commandants</h3>\n'
            "<p>Deux règles distinctes s'appliquent à la gestion des images\xa0:</p>\n"
            '<ul>\n'
            "<li><b>Enregistrer de nouvelles images\xa0:</b> L'identité du journal actif avec "
            "Commander et FID lorsqu'ils sont mis en file d'attente détermine le dossier de "
            'destination.</li>\n'
            '<li><b>Voir les images\xa0:</b> Le commandant visualisé ou le filtre de galerie '
            'sélectionné détermine les images visibles.</li>\n'
            '</ul>\n'
            "<p>Cela signifie que la galerie d'un autre commandant peut être consultée pendant la "
            "lecture de EXAMPLE sans que de nouvelles captures d'écran ne finissent dans le "
            'dossier du commandant en question.</p>\n'
            '\n'
            '<h3>Conseil</h3>\n'
            '<p>Un dossier racine de capture d’écran partagé est suffisant. Le CMDRHelper sépare '
            'automatiquement les images nouvellement traitées entre Commander et FID.</p>\n'
            '<p>Avec "Current Commander", "All Commanders" et "Unassigned", vous pouvez basculer '
            'entre la galerie personnelle, les sous-dossiers de tous les commandants et les '
            'anciennes images du dossier racine.</p>\n'
            '<p>Une luminosité plus élevée peut aider avec les photos sombres ; cela affecte '
            "l'image cible nouvellement créée lors de la conversion.</p>"),
 'commander_view': (
        'Vue CMDR',
        """<h2>Vue CMDR</h2>
<h3>Choisir un commandant</h3>
<p>La liste en haut détermine de qui vous consultez les données enregistrées. ● Actif en direct désigne le commandant actif du journal ; Consultation seule désigne un autre profil enregistré. Ce choix ne change pas le commandant actif du journal : la page principale « Missions et récompenses » utilise toujours celui qui joue réellement. Les données personnelles restent séparées par FID, même en cas de noms identiques. Consulter un profil ne déclenche aucun envoi en ligne.</p>

<h3>Aperçu, fortune et MercCoins</h3>
<p>« Aperçu » affiche nom, FID, état, premières et dernières observations, systèmes visités, découvertes biologiques/géologiques, entrées Codex et ventes cartographiques, position, missions ouvertes, vaisseau, porte-vaisseaux et données biologiques/cartographiques invendues avec les estimations connues. « Fortune » est le dernier solde de crédits enregistré. « Mercenary credits » reprend les valeurs de Frontier : « Current », « Total spent », « Engineering », « Gear » et « Reported by Frontier: total earned ». Ces compteurs ne concordent pas forcément arithmétiquement ; CMDRHelper ne les corrige pas et n’invente aucun historique de transactions. Les valeurs inconnues restent « – ».</p>

<h3>Missions et exploration</h3>
<p>« Missions » affiche les missions ouvertes enregistrées du commandant consulté : état, nom, destination, expiration et récompense. Ce tableau sert à consulter ; il ne propose ni détails ni actions de mission comme la page principale. « Exploration » affiche les données biologiques/cartographiques invendues, découvertes biologiques, premiers pas, corps cartographiés personnellement ou efficacement et systèmes visités. « Chronique » est ici un espace réservé ; la chronique complète s’ouvre depuis le menu principal.</p>

<h3>Flotte et détails des vaisseaux</h3>
<p>« Vaisseaux » affiche en haut le vaisseau actuel ou utilisé en dernier, puis la flotte enregistrée de ce commandant. Cliquez sur l’en-tête d’une fiche pour déplier ses détails. Triez dans les deux sens par utilisation, nom, type, portée de saut, capacité de soute, masse à vide, position ou date ; affichez tous les vaisseaux ou ceux avec hangar à véhicules/chasseurs. Le vert désigne le vaisseau actif en direct ; les autres couleurs regroupent les positions connues. Les détails comprennent immatriculation, ShipID, position, dates, FSD/propulseur Guardian, portée, masse, capacités de soute/carburant et état de l’équipement (complet, incomplet ou ancien). Les modules connus ajoutent hangars, boucliers et renforts, armes et cabines. Les données manquantes restent « – ».</p>

<h3>Votre propre porte-vaisseaux</h3>
<p>« Porte-vaisseaux personnel » indique le nom, l’indicatif, le CarrierID, la dernière position et la dernière actualisation de votre porte-vaisseaux enregistré. Il ne s’agit ni d’offres commerciales ni de stocks miniers.</p>

<h3>Images personnelles des vaisseaux et du porte-vaisseaux</h3>
<p>Utilisez « Choisir une image du vaisseau… » dans les détails dépliés ou « Choisir une image du porte-vaisseaux… » pour le porte-vaisseaux. PNG, JPG/JPEG et WEBP sont acceptés. CMDRHelper conserve une copie locale propre, séparée par commandant et vaisseau ou porte-vaisseaux, même après redémarrage. Un nouveau choix remplace cette copie. « Retirer l’image personnelle » supprime la copie et son association ; le fichier original est conservé. Sans image personnelle, un aperçu standard disponible ou un symbole de remplacement apparaît. Le choix d’image est désactivé sans identification certaine du porte-vaisseaux. Aucune capture d’écran n’est associée automatiquement.</p>

<h3>Visionneuse d’images</h3>
<p>Double-cliquez sur une image disponible pour ouvrir la visionneuse séparée avec le fichier image, et non la seule miniature. L’image s’adapte proportionnellement à la fenêtre. Vous pouvez agrandir ou maximiser celle-ci et la fermer avec Échap ou son bouton de fermeture. Il n’y a ni navigation entre images ni commande de zoom. La rubrique principale « Images » gère, elle, les captures d’écran.</p>

<h3>Supprimer un vaisseau</h3>
<p>« Supprimer le vaisseau… » demande une confirmation explicite ; Annuler est présélectionné. L’action supprime la fiche locale, les données d’équipement enregistrées et la copie de l’image personnelle. Le vaisseau actuel ou utilisé en dernier et celui identifié comme actif en direct sont protégés ; la suppression est bloquée pendant la relecture. Une marque locale empêche les anciennes données du journal de le faire réapparaître aussitôt. Un nouveau signalement certain de ce vaisseau comme actif dans le journal en direct après sa suppression peut le rétablir. Une relecture confirmée peut aussi retirer cette marque. L’image personnelle supprimée n’est pas restaurée.</p>

<h3>Relire tous les vaisseaux</h3>
<p>« Relire tous les vaisseaux… » permet de récupérer des informations de flotte dans les journaux existants ou de retrouver des vaisseaux supprimés localement. Après confirmation, les fichiers connus et ceux du dossier de journaux configuré sont relus pour le commandant consulté, uniquement pour la flotte. Elite n’a pas besoin d’être lancé. Les informations enregistrées plus récentes et les vaisseaux absents des journaux disponibles sont conservés ; les ventes reconnues sont prises en compte. En cas de réussite, les marques de suppression manuelle de ce commandant sont retirées. Les images personnelles existantes restent, les images supprimées ne reviennent pas. Les autres commandants ne sont pas affectés. Si la lecture ou l’application échoue, les marques restent : vérifiez l’accès aux journaux et réessayez.</p>

<h3>Données locales et sécurité</h3>
<p>Les informations enregistrées restent consultables hors ligne et après redémarrage ; elles représentent le dernier état connu. Images, suppression et relecture ne concernent que CMDRHelper. Elles ne modifient aucun vaisseau, porte-vaisseaux ou crédit dans Elite Dangerous et ne réécrivent pas les journaux.</p>""",
    ),
 'settings': ('Paramètres',
              '<h2>Paramètres</h2>\n<h3>CMDRHelper</h3>\n<p>Informations de mise à jour améliorées : la fenêtre Oui/Non affiche les versions installée et disponible et jusqu’à six nouveautés si un résumé existe. Les longues listes défilent et les actions restent accessibles.</p>\n'
              '<p>La zone « Paramètres » détermine comment le CMDRHelper fonctionne avec le Elite '
              'Dangerous, les fichiers journaux, la base de données, les services en ligne, '
              "l'interface et les mises à jour.</p>\n"
              '<p>Les modifications des informations d’identification et des parcours doivent être '
              'effectuées avec soin. Les paramètres liés au contrôleur sont gérés séparément par '
              "l'ID Frontier si nécessaire.</p>\n\n<h3>Favori rapide</h3>\n<p>Dans « Favori rapide », utilisez « Définir le raccourci » pour définir un raccourci global ou « Modifier le raccourci » pour le modifier. « Supprimer le raccourci » supprime l’affectation ; l’état initial est « Non attribué ». Le choix est enregistré. Un conflit d’enregistrement affiche un message. Le raccourci sauvegarde sans dialogue une position actuelle valide en surface comme favori du commandant, sans capture d’écran. Sans données de position adaptées, rien n’est enregistré.</p>\n"
              '\n'
              '<h3>journal</h3>\n'
              "<p>Le dossier du journal est l'un des paramètres les plus importants. Il doit "
              'pointer vers le dossier où Elite Dangerous le <code>Journal*.log</code> fichiers du '
              'profil Windows ou Proton utilisé.</p>\n'
              '<p>Les revues fournissent, entre autres :</p>\n'
              '<ul>\n'
              '<li>Identité, localisation et déplacement du commandant</li>\n'
              '<li>Missions, navires et actifs</li>\n'
              '<li>Données d’exploration, cartographie et BIO</li>\n'
              '<li>Exploitation minière à ciel ouvert, pièces de mercenaires et autres États pris '
              'en charge</li>\n'
              '</ul>\n'
              '\n'
              '<h3>Affichage et fonctionnement du journal</h3>\n'
              "<p>Le groupe de journaux affiche l'ensemble de dossiers, le nombre de journaux "
              'trouvés, les journaux les plus anciens et les plus récents, le nom du fichier le '
              "plus récent et l'heure de la dernière entrée lue.</p>\n"
              '<p>«\xa0Sélectionner le dossier du journal\xa0» modifie le dossier. «\xa0Lire '
              'maintenant\xa0» déclenche immédiatement la mise à jour normale.</p>\n'
              '<p>Des sessions clairement identifiables sont attribuées à l’aide de FID. Les '
              'nouvelles entrées complètes sont traitées progressivement\xa0; Des positions de '
              'lecture sécurisées évitent que chaque journal soit inutilement relu dans son '
              'intégralité lors de son prochain démarrage.</p>\n'
              '\n'
              '<h3>base de données</h3>\n'
              '<p>CMDRHelper stocke en permanence les données requises dans une base de données '
              'locale SQLite. Cela inclut les données globales du système et du corps ainsi que '
              'les informations explicitement attribuées à un commandant.</p>\n'
              '<p>La page des paramètres affiche des statistiques sur les données enregistrées. La '
              "base de données ne doit pas être modifiée manuellement pendant l'exécution de "
              'CMDRHelper.</p>\n'
              '\n'
              '<h3>Importer les archives du journal</h3>\n'
              "<p>«\xa0Importer l'archive du journal\xa0» compare complètement les fichiers "
              'journaux du dossier de journal défini avec la base de données. Les zones de journal '
              "déjà connues sont prises en compte sur la base des informations d'importation "
              'enregistrées et ne sont pas aveuglément dupliquées en tant que nouvelles '
              'données.</p>\n'
              "<p>Lors d'une importation visible manuellement, la progression, le numéro et le "
              'fichier en cours de traitement sont affichés. Une fois terminé, CMDRHelper signale '
              'les données importées ou déjà connues ou une erreur.</p>\n'
              "<p>L'importation d'archives sert également à réapprendre les informations "
              'historiques prises en charge à partir de revues clairement attribuées.</p>\n'
              '\n'
              '<h3>Données relatives au commandant</h3>\n'
              "<p>Le CMDRHelper sépare les informations personnelles en fonction du FID et de l'ID "
              "de commandant interne associé. Ceux-ci incluent, sans s'y limiter, les missions, "
              "les actifs, le MercCoins, l'exploration personnelle et l'accès en ligne.</p>\n"
              '<p>Une session de journal inconnue ou ambiguë ne peut pas être arbitrairement '
              'attribuée à un commandant.</p>\n'
              '\n'
              '<h3>Services en ligne</h3>\n'
              '<p>CMDRHelper prend en charge EDSM et Inara. Les deux accès sont traités et '
              'enregistrés séparément pour chaque commandant connu ou chaque FID.</p>\n'
              '<p>La sélection dans les paramètres détermine uniquement quel accès est '
              'actuellement modifié ou testé. Seul le commandant clairement identifié par la '
              'session de journal active est autorisé à envoyer en direct.</p>\n'
              '\n'
              '<h3>Informations de stations Spansh</h3>\n'
              '<p>Dans « SERVICES EN LIGNE », « Ajouter les informations de stations Spansh » active le complément facultatif sur les stations et installations de l’Explorer et des vues système. L’option est désactivée par défaut. Seul l’identifiant public du système est transmis, sans information de commandant ; aucune clé API personnelle n’est nécessaire. Cette option ne commande pas les recherches de marchés commerciaux.</p>\n'
              '<p>Lorsque l’option est désactivée, seules les informations locales du journal sont affichées et aucune nouvelle requête de stations Spansh n’est lancée ; l’actualisation manuelle est également désactivée. Le cache de stations existant n’est pas supprimé, mais n’enrichit plus l’affichage. Réactiver l’option rend le cache disponible sans déclencher à lui seul une requête réseau.</p>\n'
              '\n'
              '<h3>Requêtes automatiques et cache des stations</h3>\n'
              '<p>La vérification automatique intervient uniquement lors d’une nouvelle entrée en direct du commandant actif du journal dans un autre système, par exemple après un saut du vaisseau, du carrier ou un nouveau signalement de position confirmé. Le démarrage, un changement de commandant, un import d’archives ou la simple ouverture de l’Explorer ou d’une vue système ne lancent aucune requête automatique.</p>\n'
              '<p>Le cache de stations séparé est conservé après un redémarrage du Helper. Une récupération datant de moins de 7 jours est considérée comme récente et évite une nouvelle requête automatique. Les données absentes ou plus anciennes peuvent être actualisées à la prochaine entrée en direct admissible. Au plus une tentative automatique par système et par jour du calendrier local est prévue ; un échec compte aussi, même après redémarrage. Tous les systèmes enregistrés ne sont pas actualisés en continu en arrière-plan. Les anciennes données utilisables du cache peuvent rester affichées, même hors ligne.</p>\n'
              '<p>Ce cache contient des informations complémentaires sur les stations, pas les prix des marchés commerciaux. Les données communautaires Spansh pour vente, achat et recommandations ont leur propre cache de recherche temporaire en mémoire vive. Les relevés commerciaux observés personnellement dans Elite sont encore stockés séparément : ils survivent au redémarrage, mais ne sont valides que pendant moins de 24 heures.</p>\n'
              '\n'
              '<h3>Actualiser manuellement les stations</h3>\n'
              '<p>Ouvrez « Vue d’ensemble » et choisissez « Actualiser les données Spansh ». Seules les informations de stations Spansh du système affiché dans cette fenêtre sont actualisées, pas tous les systèmes enregistrés ni les prix des marchés. L’option doit être activée ; pendant une requête pour ce système, l’action est désactivée.</p>\n'
              '<p>L’action manuelle peut ignorer le délai de 7 jours et une tentative automatique échouée le même jour. Si le système a déjà été récupéré avec succès aujourd’hui selon le calendrier local, aucune nouvelle requête n’est faite : « Les données Spansh ont déjà été mises à jour aujourd’hui. » Une récupération réussie renouvelle le cache de stations. En cas d’échec, les informations locales et les données utilisables du cache sont conservées et la ligne d’état indique l’échec. Une tentative manuelle échouée peut être relancée.</p>\n\n<h3>Données des corps EDSM et cache</h3>\n<p>« Utiliser EDSM » contrôle aussi les données complémentaires des corps du système actuel du commandant actif du journal dans Explorer. Après « Enregistrer les accès en ligne » et lors des mises à jour normales du journal, un cache utilisable est chargé ou EDSM est interrogé en arrière-plan. Cette consultation publique nécessite le réseau mais aucune clé API ; l’envoi du journal est une opération distincte.</p>\n<p>Les données de corps obtenues sont conservées localement par système et réutilisables depuis le cache pendant au plus 24 heures, même après un redémarrage. Les données plus anciennes déclenchent une nouvelle demande lors d’une mise à jour appropriée. Si la fonction est désactivée, ce cache n’enrichit pas l’affichage et aucune nouvelle demande de corps ne démarre ; les fichiers du cache ne sont pas supprimés. Les données locales du journal restent utilisables. Un échec ne crée aucun corps fictif.</p>\n'
              '\n'
              '<h3>Accès EDSM pour</h3>\n'
              '<p>«\xa0Accès EDSM pour\xa0:\xa0» sélectionne le commandant à modifier. La '
              "sélection affichera «\xa0configuré\xa0» ou «\xa0non configuré\xa0» selon qu'un "
              'API-Key est stocké.</p>\n'
              '<p>Le nom du commandant, le champ API-Key masqué, « Utiliser EDSM », un test de '
              'connexion et son dernier état de test sont visibles.</p>\n'
              '<p>Chaque commandant a besoin de son propre accès EDSM approprié. La sélection ne '
              'fait pas basculer le programme de téléchargement en direct vers ce commandant.</p>\n'
              '\n'
              '<h3>Utiliser et tester EDSM</h3>\n'
              '<p>«\xa0Utiliser EDSM\xa0» active ou désactive le service pour le FID sélectionné. '
              "Les informations d'identification manquantes ou désactivées n'affectent pas le "
              'traitement du journal local.</p>\n'
              "<p>«\xa0Test de connexion EDSM\xa0» vérifie les données d'accès actuellement "
              'visibles dans le formulaire. Un test réussi confirme la connexion, mais ne modifie '
              'pas le journal actif FID ou le Live Commander.</p>\n'
              '\n'
              '<h3>Accès Inara pour</h3>\n'
              "<p>«\xa0Inara Access for\xa0:\xa0» suit le même principe multi-CMDR. L'activation, "
              'le nom du commandant Inara et le API-Key sont enregistrés séparément pour chaque '
              'FID.</p>\n'
              "<p>Ici aussi, la sélection indique « configuré » ou « non configuré ». Une clé d'un "
              "commandant n'est pas automatiquement utilisée pour un autre commandant.</p>\n"
              '\n'
              '<h3>Utiliser et tester Inara</h3>\n'
              '<p>Avec Inara configuré et activé pour le journal actif FID, CMDRHelper peut '
              'transmettre les événements de voyage, de localisation, de mission et de navire pris '
              'en charge. Tous les événements du journal ne sont pas envoyés à Inara.</p>\n'
              "<p>«\xa0Test de connexion Inara\xa0» vérifie les données d'accès actuellement "
              'visibles sans changer le commandant en direct.</p>\n'
              '\n'
              "<h3>Boîte d'envoi Inara</h3>\n"
              '<p>Les événements Inara pris en charge sont signalés de manière persistante dans '
              "une boîte d'envoi avant la transmission réseau.</p>\n"
              '<p>Les erreurs temporaires permettent de conserver ces entrées pour des tentatives '
              "ultérieures. Le collaborateur traite uniquement la boîte d'envoi du journal "
              'uniquement actif FID\xa0; Les entrées d’autres commandants ne sont pas '
              'incluses.</p>\n'
              '\n'
              "<h3>Statut en ligne dans l'en-tête</h3>\n"
              '<p>EDSM affiche actuellement\xa0:</p>\n'
              '<ul>\n'
              '<li><b>EDSM</b>– ne peut pas être utilisé ou désactivé pour le FID actif</li>\n'
              '<li><b>EDSM attend</b>– mis en place et sans transmission continue</li>\n'
              "<li><b>Transmission EDSM</b>– le dernier traitement EDSM s'est terminé sans "
              "erreur\xa0; L'info-bulle indique si des événements ont été envoyés, si les données "
              "du journal ont été traitées ou si aucune nouvelle donnée n'a été trouvée.</li>\n"
              '<li><b>Erreur EDSM</b>– le dernier état de transmission est incorrect</li>\n'
              '</ul>\n'
              "<p>Il n'existe actuellement aucun état supplémentaire, étiqueté séparément «\xa0"
              'EDSM actif\xa0» pour EDSM.</p>\n'
              '<p>Inara distingue plus précisément :</p>\n'
              '<ul>\n'
              '<li><b>INARA absente</b>– désactivé pour le journal actif FID</li>\n'
              '<li><b>INARA prêt</b>– mis en place, mais toujours sans transmission confirmée dans '
              'cette session</li>\n'
              '<li><b>Boîte de vitesses INARA</b>– le travailleur envoie actuellement</li>\n'
              '<li><b>INARA actif</b>– le dernier transfert effectif a été confirmé avec '
              'succès</li>\n'
              '<li><b>Erreur INARA</b>– la dernière tentative de transfert a échoué</li>\n'
              '</ul>\n'
              '\n'
              '<h3>Sécurité API-Key</h3>\n'
              "<p>Les API-Key sont des informations d'identification personnelles. Les champs de "
              'saisie sont masqués\xa0; Ils sont stockés liés au commandant dans les paramètres de '
              "l'application et non dans la base de données CMDRHelper.</p>\n"
              "<p>Les clés ne doivent pas être publiées, partagées dans des captures d'écran ou "
              'ajoutées à des référentiels publics.</p>\n'
              '\n'
              "<h3>Images/Captures d'écran</h3>\n"
              '<p>Le dossier source, le dossier de destination, PNG/JPG, le traitement '
              "automatique, la suppression BMP et l'éclaircissement de 0 à 50 % se trouvent "
              'exclusivement dans le menu principal Images, pas sur la page Paramètres.</p>\n'
              "<p>L'aide contextuelle « Images » décrit ces options en détail.</p>\n"
              '\n'
              '<h3>surface</h3>\n'
              "<p>Le groupe d'interface comprend l'apparence, la langue, la police, la taille de "
              "la police et le seuil de valeur pour les corps d'explorateur précieux.</p>\n"
              '\n'
              '<h3>Mode sombre et clair</h3>\n'
              '<p>Vous pouvez basculer directement entre l’apparence sombre et claire. Le thème '
              'est immédiatement appliqué à l’interface et aux cartes système et historique '
              'existantes et enregistré.</p>\n'
              '\n'
              '<h3>Langue</h3>\n'
              "<p>L'interface propose douze langues parmi lesquelles choisir. «\xa0Enregistrer la "
              'langue\xa0» enregistre la sélection\xa0; Un redémarrage de CMDRHelper est alors '
              'nécessaire pour une conversion complètement uniforme des widgets existants.</p>\n'
              '\n'
              '<h3>Police et taille de police</h3>\n'
              '<p>La famille de polices et la taille de police de 7 à 24 pts peuvent être '
              'sélectionnées et enregistrées.</p>\n'
              '<p>Les deux modifications ne prendront pleinement effet qu’après un redémarrage. '
              "L'interface l'indique explicitement.</p>\n"
              '\n'
              '<h3>Seuil de valeur</h3>\n'
              '<p>Le seuil de valeur Explorer détermine la valeur de crédit estimée à partir de '
              'laquelle les corps sont mis en évidence comme particulièrement précieux. La '
              "modification est enregistrée immédiatement et met à jour l'affichage de "
              "l'Explorateur correspondant.</p>\n"
              '\n'
              '<h3>Masquer automatiquement</h3>\n'
              '<p>«\xa0Corps précieux\xa0» et «\xa0BIO Finds\xa0» sont fermement situés dans la '
              'barre latérale gauche, et non dans la page Paramètres.</p>\n'
              '<p>Les commutateurs sont enregistrés et contrôlent les petites fenêtres '
              "d'indications en direct prises en charge pendant l'exploration. Le seuil de valeur "
              "pour les corps précieux est défini dans les paramètres de l'interface.</p>\n"
              '\n'
              '<p>La fenêtre Cargo utilise exclusivement le snapshot Cargo confirmé pour la FID active du Journal. Le commander consulté dans CMDR View et viewed_commander_id n’influencent pas cette fenêtre en direct. Pour un Ship, elle affiche occupé / maximum · libre ; si CargoCapacity est inconnue, aucune valeur n’est estimée.</p>\n'
              '<p>« HUD de statut EDSM », sous « afficher automatiquement », est DÉSACTIVÉ par défaut. Après l’entrée dans un système, un bref message apparaît sur Elite pendant environ 2,5 secondes. Plusieurs événements Location pendant le même séjour ne produisent pas de doublons ; un véritable retour peut déclencher une nouvelle vérification.</p>\n<p>« EDSM : CONNU » signifie une correspondance EDSM valide pour le système. « EDSM : INCONNU » signifie une réponse EDSM valide sans correspondance. « EDSM : AUCUNE RÉPONSE » signifie une erreur réseau, HTTP, un délai dépassé ou une réponse invalide, jamais une absence de correspondance confirmée. La présence dans EDSM ne vaut pas découverte officielle dans Elite ; aucun nom de premier découvreur ou déclarant n’est promis.</p>\n<p>Le message fonctionne indépendamment des HUD de navigation et de soute. Les affichages permanents et les messages de favori rapide sont préservés. La requête ne bloque pas l’interface ; les réponses tardives concernant un système déjà quitté sont ignorées.</p>\n\n'
              '<p>Les interrupteurs « afficher automatiquement » de la barre latérale sont indépendants : « Corps de grande valeur », « Découvertes BIO », « GEO » et « Soute » contrôlent leurs fenêtres respectives. « HUD de soute » affiche la cargaison en surimpression, « HUD de navigation » la navigation planétaire active. Ces interrupteurs d’affichage ne lancent pas eux-mêmes de requête en ligne ; les HUD nécessitent Elite au premier plan et des données adaptées.</p>\n<p>« HUD de statut EDSM » nécessite en revanche sa propre requête publique à EDSM, indépendamment de « Utiliser EDSM », de son cache des corps et d’une clé API. L’envoi Inara et les informations de stations Spansh ont leurs propres interrupteurs ; ceux des HUD ne les activent pas.</p>\n\n<h3>Mises à jour</h3>\n'
              "<p>Le groupe de mise à jour affiche la version installée et l'état de GitHub. "
              'Vérifier maintenant recherche manuellement une nouvelle version planifiée de '
              'CMDRHelper\xa0; De plus, un contrôle automatique différé a lieu après le '
              'départ.</p>\n'
              '<p>Si une nouvelle version est disponible, CMDRHelper vous le demandera avant de '
              "télécharger et d'installer. Une mise à jour de base de données annoncée est "
              'affichée séparément dans cette boîte de dialogue.</p>\n'
              '<p>Pour une installation existante, il suffit normalement d’installer la mise à jour → démarrer CMDRHelper. Les corrections historiques nécessaires des données BIO, des visites et des métadonnées DSS sont automatiques ; une sauvegarde de la base précède toute réparation écrivant des données. Les réparations sont versionnées et idempotentes : les révisions réussies ne sont pas entièrement réexécutées à chaque démarrage. La reconstruction exige des journaux Elite encore présents, lisibles et attribuables sans ambiguïté à un commandant. Les sources absentes ne sont ni inventées ni considérées comme un succès ; les réparations en attente sont retentées au démarrage suivant. Suppression de la base, scripts manuels et réimportation sont normalement inutiles.</p>\n\n'
              '<h3>Progression du téléchargement</h3>\n'
              "<p>Le téléchargement s'exécute en arrière-plan. Si la taille totale est connue, "
              'CMDRHelper affiche le nom du fichier, les MiB reçus et totaux, le pourcentage, le '
              'taux de transfert et le temps restant estimé.</p>\n'
              '<p>Sans taille totale connue, la barre de progression fonctionne en mode occupé et '
              "continue d'afficher la quantité de données reçues et - si déterminable - le débit. "
              "Avant l'installation, le ZIP téléchargé est vérifié.</p>\n"
              '\n'
              '<h3>Annuler la mise à jour</h3>\n'
              '<p>«\xa0Annuler le téléchargement\xa0» met fin de manière contrôlée à un '
              'téléchargement en cours. Un téléchargement interrompu, incomplet ou invalide ne '
              'sera pas installé.</p>\n'
              '\n'
              '<h3>Mise à jour sous Windows</h3>\n'
              '<p>Sous Windows, le processus de mise à jour se poursuit quelle que soit la console '
              "de démarrage d'origine. Un arrêt de la console ne doit donc pas y mettre fin "
              'involontairement.</p>\n'
              '<p>Si une erreur se produit après le début des modifications de fichiers, la '
              'sauvegarde de restauration existante tente de restaurer la version précédente.</p>\n'
              '\n'
              '<h3>Redémarrer après la mise à jour</h3>\n'
              '<p>Après une installation réussie, le programme de mise à jour CMDRHelper redémarre '
              'via le chemin de démarrage prévu et vérifie brièvement si le nouveau processus '
              "s'exécute de manière stable.</p>\n"
              "<p>Si une version nécessite une mise à jour unique de la base de données, l'archive "
              'du journal sera également réévaluée après le redémarrage.</p>\n'
              '\n'
              '<h3>Plusieurs commandants</h3>\n'
              "<p><b>Sélection des paramètres = De qui suis-je en train de modifier l'accès en "
              'ligne\xa0?</b></p>\n'
              '<p><b>Active Journal-FID = Qui est autorisé à diffuser en direct\xa0?</b></p>\n'
              '<p>Ni la sélection de compte en ligne ni la vue CMDR ne sont autorisées à passer '
              "d'un téléchargeur en direct à un commandant en visualisation uniquement.</p>\n"
              '\n'
              '<h3>Aide</h3>\n'
              '<p>"? Aide" se trouve dans la barre latérale gauche au-dessus de "Affichage '
              'automatique" et ouvre l\'aide de la zone du menu principal actuellement '
              'visible.</p>\n'
              '<p>Dans la zone « Paramètres », le bouton ouvre directement cette aide aux '
              'paramètres.</p>\n'
              '\n'
              '<h3>Conseil</h3>\n'
              "<p>Si vous réinstallez ou rencontrez des problèmes, vérifiez d'abord\xa0:</p>\n"
              '<ul>\n'
              '<li>dossier de journal correct et identité du commandant reconnu</li>\n'
              "<li>seuil de valeur de langue, de thème, de police et d'explorateur souhaité</li>\n"
              '<li>Accès en ligne au bon FID</li>\n'
              "<li>En cas de problèmes d'image, dossiers source et cible dans le menu principal « "
              'Images »</li>\n'
              '</ul>\n'
              "<p>S'il y a plusieurs commandants, faites toujours attention à quel FID "
              "s'appliquent les données d'accès en ligne visibles.</p>"),
    "planet_navigation": (
        'Navigation planétaire',
        """<h2>Navigation planétaire</h2>
<p>Le navigateur planétaire sert exclusivement à rejoindre une latitude/longitude précise sur une planète ou une lune. Tu définis une cible par ses coordonnées et obtiens la distance et la direction pour la rejoindre.</p>
<p>Ce n’est pas un planificateur d’itinéraire interstellaire et il ne prend en charge ni la navigation entre systèmes ni les sauts. Tu pilotes toi-même ton vaisseau.</p>

<h3>Ouvrir le navigateur et saisir une cible</h3>
<p>Ouvre « Navigation planétaire » dans l’Explorer puis « Saisie manuelle … ». La fenêtre et la saisie d’une cible sont disponibles même avant de recevoir une position de surface.</p>
<ul>
<li><b>Corps céleste :</b> Sélectionne la planète ou la lune cible dans la liste, ou utilise le corps déjà détecté. Tu peux aussi saisir toi-même son nom s’il ne figure pas encore dans la liste. En cas de doute, utilise le nom complet, y compris celui du système.</li>
<li><b>Latitude :</b> Saisis la latitude cible entre −90° et +90°.</li>
<li><b>Longitude :</b> Saisis la longitude cible entre −180° et +180°. Fais attention au signe des deux coordonnées.</li>
<li><b>Nom de la cible :</b> Tu peux saisir un libellé facultatif pour reconnaître plus facilement ta cible.</li>
</ul>
<p>« Définir la cible » valide ta saisie. Tu n’as pas à saisir d’identifiants techniques comme BodyID et SystemAddress ; ce ne sont pas des données normalement saisies par l’utilisateur.</p>

<h3>Quand la boussole démarre-t-elle ?</h3>
<p>Dès qu’une cible est définie et qu’Elite fournit des données de position planétaire valides pour le corps correspondant, la navigation s’active automatiquement. Tu n’as pas à appuyer sur un bouton de démarrage distinct.</p>
<p>Si ces données manquent encore ou concernent un autre corps, le navigateur attend en affichant « En attente des coordonnées planétaires … ». Tu peux saisir une cible avant même de recevoir ces données.</p>

<p>La navigation active nécessite les coordonnées, le nom du corps, le cap et le rayon planétaire valides fournis par Elite pour le corps cible. Atterrir n’est pas obligatoire : ces données peuvent arriver pendant l’approche. Sans position valide ou sur un autre corps, le navigateur attend sans inventer de position.</p>

<h3>Enregistrer la position actuelle</h3>
<p>« ★ Enregistrer la position actuelle » enregistre ta position actuelle confirmée, pas la cible saisie. Une position Elite valide, un commandant identifié et un système connu sont requis. Sinon, l’action est désactivée ou un message apparaît.</p>
<p>Le système, le corps et les coordonnées sont figés à l’ouverture. Le dialogue des favoris permet de modifier nom, catégorie et note et d’ajouter une image. Seul « Enregistrer » enregistre localement pour ce commandant ; annuler ne sauvegarde rien. Les déplacements ultérieurs ne modifient pas la position figée.</p>

<h3>Utiliser les positions enregistrées</h3>
<p>Ouvre « ★ Favoris » dans l’Explorer. Choisis un lieu de surface enregistré puis « ◎ Vers les coordonnées » pour reprendre son corps, ses coordonnées et son nom comme cible. Cela remplace la cible précédente ; sur un autre corps, le navigateur attend les bonnes données de position.</p>
<p>« Modifier » permet de changer nom, catégorie et note. « Supprimer » supprime le favori après confirmation, sans supprimer de données Elite. Les favoris survivent aux redémarrages et sont séparés par commandant ; la cible de navigation actuelle ne dure que pendant la session.</p>

<h3>Globe planétaire : au-delà de 380 km</h3>
<p>Lorsque la distance à la cible est supérieure à 380 km, le navigateur affiche le globe planétaire.</p>
<ul>
<li>Le <b>cercle blanc</b> indique ta position.</li>
<li>Le <b>petit point cible</b> est orange lorsque la cible se trouve sur la face visible de la planète.</li>
<li>Si la cible se trouve sur la face arrière cachée, le point cible est affiché en rouge.</li>
<li>Ta position reste fixe dans la représentation. La planète et la cible sont représentées par rapport à ta position et à ton orientation.</li>
</ul>
<p>La flèche blanche pointe vers l’avant ; la flèche jaune indique la direction relative de la cible. Le globe est une aide à l’orientation schématique, pas une vue géographiquement exacte du terrain. Un point rouge signifie la face arrière du globe, pas automatiquement « derrière ton vaisseau ».</p>

<h3>Grille en perspective : jusqu’à 380 km inclus</h3>
<p>À une distance de la cible inférieure ou égale à 380 km, l’affichage passe automatiquement à une grille inclinée en perspective. Si la distance repasse au-dessus de 380 km, le globe réapparaît.</p>
<p>Les lignes transversales forment une <b>grille de distance par pas de 50 km</b>. Le point cible est placé dans la grille en fonction de la distance et de la direction relative. La perspective t’aide à poursuivre l’approche ; l’inclinaison fait paraître les espacements plus serrés vers l’arrière. Pour le cap à suivre, observe également le cap cible et la direction relative.</p>

<h3>Bien lire les valeurs de navigation</h3>
<ul>
<li><b>Distance à la cible :</b> Le grand affichage indique la distance restante jusqu’à la cible le long de la surface planétaire théorique.</li>
<li><b>Coordonnées de la cible :</b> La paire de coordonnées saisie pour la cible, d’abord la latitude, puis la longitude. Elle reste inchangée pendant tes déplacements.</li>
<li><b>Coordonnées actuelles :</b> Ta dernière paire de coordonnées confirmée par Elite, également latitude / longitude.</li>
<li><b>Distance en surface :</b> La même distance de surface que la distance à la cible, éventuellement arrondie plus précisément dans l’affichage détaillé. Ce n’est ni un second trajet ni une distance directe dans l’espace à travers les airs.</li>
<li><b>Relèvement :</b> La direction absolue vers la cible depuis ta position actuelle, exprimée en angle de boussole : 000° correspond au nord, 090° à l’est, 180° au sud et 270° à l’ouest.</li>
<li><b>Cap :</b> Ton orientation actuelle telle qu’Elite la fournit. Il indique vers où tu es orienté et ne correspond pas nécessairement encore au relèvement.</li>
<li><b>Direction relative :</b> La différence entre ton orientation et le relèvement, par exemple « 23° à droite », « 10° à gauche » ou « Tout droit ». À 180°, la cible est derrière toi.</li>
<li><b>Cap cible :</b> Le relèvement mis en évidence sous forme de cap absolu sur lequel tu peux t’aligner dans le HUD d’Elite. Ce n’est pas un angle de rotation supplémentaire.</li>
</ul>
<p>Exemple : avec un cap de 051° et un cap cible de 074°, tourne de 23° à droite jusqu’à ce que ta boussole Elite indique environ 074°. En poursuivant le vol, le relèvement et le cap cible peuvent changer ; fie-toi aux valeurs actualisées.</p>
<p>À la même position que la cible, à un pôle ou au point exactement opposé sur la planète, la direction peut être indéterminée. Le navigateur affiche alors le message correspondant plutôt qu’un cap inventé.</p>

<h3>Taille de la fenêtre</h3>
<p>La fenêtre du navigateur est librement redimensionnable. Le globe ou la grille en perspective s’adapte proportionnellement à l’espace disponible. La taille minimale préserve la lisibilité des valeurs détaillées ; le globe reste rond. La position et la taille de la fenêtre sont enregistrées.</p>

<h3>Activer le HUD de navigation</h3>
<p>À gauche dans la fenêtre principale, coche la case sous <b>affichage automatique → HUD de navigation</b>. Lorsque la navigation planétaire est valide, le HUD apparaît directement au-dessus de la fenêtre Elite visible au premier plan.</p>
<p>Il affiche trois lignes :</p>
<ul>
<li>direction relative</li>
<li>cap cible</li>
<li>distance</li>
</ul>
<p>Le HUD est transparent, laisse passer les clics et ne prend pas le focus : il ne masque pas le jeu par une zone opaque, n’intercepte pas les clics de souris et ne retire pas le focus de saisie à Elite lorsqu’il apparaît automatiquement.</p>
<p>Sans navigation valide ou direction non ambiguë, il devient automatiquement invisible. Il est également masqué si Elite est réduit ou n’est pas au premier plan. La case de la barre latérale peut néanmoins rester cochée ; elle représente ton souhait d’affichage automatique, pas la visibilité actuelle.</p>
<p>Le HUD n’est qu’un affichage supplémentaire. Le navigateur normal fonctionne indépendamment, même si le HUD est désactivé ou indisponible.</p>

<h3>Définir une nouvelle cible</h3>
<p>Sur le même corps, tu peux rouvrir « Saisie manuelle … » à tout moment et définir d’autres coordonnées. La nouvelle cible remplace la cible de navigation précédente. Avec des données de position correspondantes, la boussole s’actualise immédiatement.</p>
<p>« Arrêter la navigation » supprime la cible actuelle. Pour une nouvelle approche, définis simplement une nouvelle cible.</p>

<p>Fermer la fenêtre ne supprime pas la cible. Le HUD de navigation activé peut continuer ; « Arrêter la navigation » retire la cible. Quitter le corps correspondant ou perdre les données de position met la navigation en attente et masque le HUD de navigation.</p>

<h3>Actualité des données et limites</h3>
<p>La navigation repose sur les données d’état fournies par Elite. Selon l’état du jeu, les mises à jour peuvent arriver avec du retard. L’indication d’âge dans le navigateur montre le temps écoulé depuis le dernier message d’état confirmé.</p>
<p>La distance en surface décrit l’arc le plus court sur une sphère théorique. Ce n’est pas un itinéraire de terrain ou routier. Le navigateur ne connaît ni les obstacles ni les altitudes du terrain le long du trajet ; l’altitude de vol, une vitesse sûre et l’évitement des obstacles restent de ta responsabilité.</p>

<p>La position actuelle vient de Status.json ; le journal complète les associations de corps et de système. La fenêtre et le HUD activé maintiennent les mises à jour selon les besoins. L’affichage dépend des données Elite disponibles, sans précision métrique garantie.</p>

<h3>Conseil</h3>
<p>Avant l’approche, vérifie le nom du corps et les signes des coordonnées de la cible. Aligne-toi ensuite sur le cap cible dans la boussole Elite et observe la direction relative et la distance. Si le navigateur attend, vérifie si Elite fournit déjà des coordonnées planétaires pour le corps cible.</p>""",
    ),
}

DIALOG_TITLE = 'Aide – {area}'
CLOSE_LABEL = 'Fermer'


# Database update guidance; help itself remains version independent.
HELP_TOPICS["overview"] = (HELP_TOPICS["overview"][0], HELP_TOPICS["overview"][1] + '<h3>Mise à jour de la base de données nécessaire</h3><p>La mise à jour corrige d’anciennes relations enregistrées entre étoiles, planètes et lunes. Les journaux sont uniquement lus. Ferme Elite Dangerous et rends les anciens journaux disponibles si possible. La base CMDRHelper est intégralement sauvegardée au préalable ; en cas d’erreur, les changements sont annulés et la sauvegarde est restaurée si nécessaire. Elle est conservée par sécurité. Annuler permet de reporter la mise à jour.</p>')

HELP_TOPICS["settings"] = (HELP_TOPICS["settings"][0], HELP_TOPICS["settings"][1] + '<h3>Diagnostic et journaux techniques</h3><p>Dans Paramètres → Diagnostic et journaux techniques, ouvrez le journal ou créez un paquet de diagnostic. Les journaux se trouvent dans logs/ sous le dossier d’installation (cmdrhelper.log et jusqu’à quatre archives). Le ZIP contient les journaux techniques expurgés, system_info.json et diagnose_summary.txt ; aucun journal Elite, base de données, identifiant FID, donnée de commandant, identifiant de connexion, favori ou image. Les chemins personnels sont remplacés par des indications génériques. Le contenu des anciens journaux antérieurs au filtrage de confidentialité est omis. Choisissez où enregistrer le ZIP et transmettez-le au support si nécessaire ; il n’est jamais envoyé automatiquement.</p>')

HELP_TOPICS["trade"] = (
    'Commerce',
    """<h2>Commerce</h2>
<h3>Le commerce en bref</h3>
<p>« Vendre » trouve les marchés qui achètent votre marchandise. « Acheter » trouve une marchandise précise à acheter. « Recommandations » indique ce que vous pouvez acheter à votre station actuelle puis revendre avec un bénéfice selon vos critères.</p>

<h3>Données de marché et ancienneté</h3>
<p>La vente et l'achat combinent automatiquement vos relevés de marché valides enregistrés avec les données communautaires obtenues via Spansh. Les recommandations achètent exclusivement sur votre marché Elite actuel observé ; les destinations proviennent normalement de vos observations et de Spansh. Les résultats communautaires sont conservés temporairement en mémoire uniquement.</p>
<p>Toutes les données sont des instantanés, y compris vos observations. Prix, offre et demande peuvent changer avant votre arrivée. Vérifiez leur ancienneté : ni la disponibilité ni le bénéfice ne sont garantis.</p>
<p>Si le même marché est connu par votre observation et par la communauté, CMDRHelper utilise le relevé valide le plus récent.</p>

<h3>Choisir une marchandise</h3>
<p>Cliquez sur « Marchandise », recherchez le nom affiché, le nom anglais ou le symbole, puis sélectionnez la marchandise. Les noms allemands proviennent du catalogue allemand entretenu. En l'absence de traduction disponible, le nom du catalogue anglais ou un nom lisible est affiché.</p>

<h3>Vendre</h3>
<p>La recherche utilise vos relevés de marché valides et les données communautaires. Choisissez la marchandise, « Quantité (t) » et les filtres, puis « Chercher la meilleure vente ». La recherche trouve des offres d'achat dont la demande couvre la quantité saisie. « Prix / t » est le prix que vous recevez en vendant. « Recette possible » = prix × quantité saisie. Le point de départ est le système actuel du commandant. Par défaut, le prix de vente le plus élevé apparaît en premier.</p>

<h3>Acheter</h3>
<p>La recherche utilise vos relevés de marché valides et les données communautaires. Choisissez la marchandise, la quantité souhaitée et les filtres, puis « Trouver l’achat le moins cher ». L'« Offre » annoncée doit couvrir toute la quantité. « Prix / t » est votre prix d'achat ; « Coût total » = prix × quantité souhaitée. Le départ est votre système actuel. Par défaut, le prix d'achat le plus bas apparaît en premier. Il s'agit d'une recherche ciblée de marchandise, pas d'une recommandation de bénéfice.</p>

<h3>Filtres et tableaux de résultats</h3>
<ul>
<li><b>Rayon (ly) :</b> distance maximale entre le système de départ et le système cible.</li>
<li><b>Âge maximal des données du marché / Ancienneté des données de destination :</b> ancienneté maximale autorisée des données ; pour les recommandations, le filtre concerne la destination.</li>
<li><b>Taille de plateforme :</b> taille minimale requise de la plateforme, pas taille exacte de la station. « Moyenne » autorise aussi les grandes plateformes ; « Toutes » ne limite pas la taille.</li>
<li><b>Inclure les Fleet Carriers :</b> inclure ou exclure les porte-vaisseaux.</li>
<li><b>Distance d’arrivée max. (Ls) :</b> distance maximale entre l'étoile d'arrivée et la station. Un champ vide n'impose aucune limite. Une destination sans distance d'approche connue ne satisfait pas ce filtre.</li>
</ul>
<p>Les résultats personnels et communautaires utilisent les mêmes filtres d’ancienneté, de rayon, de plateforme d’atterrissage, de carriers et de distance d’arrivée. Les données manquantes ne sont pas estimées. Les destinations sans distance intersystème connue ou sans preuve qu'elles satisfont une restriction activée sont exclues. Pour vos marchés, cela concerne notamment les plateformes et distances d'approche manquantes ; si les porte-vaisseaux sont exclus, la destination doit être identifiée comme n'en étant pas un.</p>
<p>Cliquez sur les en-têtes pour trier : nombres selon leur valeur, ancienneté selon l'âge réel et plateformes selon leur taille. Vente et achat affichent au maximum 100 résultats. « Il existe d’autres résultats. Affinez les filtres. » signale une recherche limitée. Les résultats personnels et communautaires disponibles sont triés ensemble par prix avant de limiter la liste. Les limites de recherche du service communautaire empêchent de garantir qu’il s’agit des meilleures offres dans l’ensemble.</p>
<p>Si la recherche communautaire échoue lors d’une vente ou d’un achat, les résultats personnels correspondants restent utilisables. CMDRHelper indique alors que la recherche est incomplète : de meilleures offres communautaires peuvent manquer.</p>

<h3>Vos données de marché</h3>
<p>Ouvrez le marché des marchandises dans Elite une fois amarré. Lorsque CMDRHelper fonctionne, il enregistre automatiquement le marché si son association à la station actuelle est sûre. Aucun import manuel n'est nécessaire. Une nouvelle ouverture actualise l'instantané.</p>
<p>Un seul instantané actuel est conservé par marché et commandant, âgé de moins de 24 heures. Les anciens sont supprimés automatiquement ; aucun historique permanent des prix n'est créé. Les observations valides survivent au redémarrage du Helper. « Données de marché personnelles : X stations » compte les marchés observés valides du commandant actif. La limite d’ancienneté des données de marché choisie s’applique aussi aux résultats personnels.</p>
<ul>
<li><b>✓ Relevé effectué :</b> Dans les recommandations, un instantané personnel valide existe pour la station actuelle.</li>
<li><b>Ouvrir le marché :</b> Aucun instantané personnel utilisable n'est disponible pour cette station.</li>
<li><b>Données périmées :</b> Un instantané précédemment affiché n'est plus valide. Ouvrez à nouveau le marché.</li>
</ul>
<p>Si l'ancien instantané a été supprimé avant l'ouverture de la vue, « Ouvrir le marché » apparaît également. En vol, aucun état positif n'est affiché pour la station précédente.</p>

<h3>Recommandations</h3>
<p>Il faut une station actuelle, son instantané personnel valide et un vaisseau actuel connu dont l'espace libre en soute est établi avec certitude. L'espace occupé est déduit. Si la soute est pleine ou sa capacité libre inconnue, aucune nouvelle recherche ne démarre ; les quantités ne sont pas inventées. Après le départ, aucun nouveau calcul ne repose sur l'ancien lieu de séjour.</p>
<p>Réglez « Bénéfice minimum » : 10 % ne retient que les possibilités offrant au moins 10 % de marge. La recherche porte sur les marchandises proposées localement. La station d'achat n'est pas une destination. Pour une même station cible (même MarketID), l'instantané valide le plus récent est retenu. Chaque marchandise affiche la destination vérifiée offrant le plus grand « Bénéfice potentiel » avec vos filtres, pas nécessairement la meilleure de la galaxie. Le tableau commence par le bénéfice possible le plus élevé ; « Source » indique « Elite local » ou « Spansh », et « Ancienneté des données de destination » l'ancienneté des données de destination.</p>

<h3>Uniquement mes données de marché</h3>
<p>Cette case est disponible uniquement dans Recommandations. La vente et l’achat utilisent automatiquement les deux sources. Cette case limite les recommandations aux marchés de destination valides que vous avez observés. Aucune requête communautaire n'est effectuée ; Spansh n'est pas nécessaire. Rayon, limite supplémentaire d'ancienneté à destination, bénéfice minimal, plateforme, porte-vaisseaux et approche restent applicables et doivent pouvoir être vérifiés avec les données présentes. Ignorer volontairement la recherche communautaire n'est pas une erreur et ne rend pas la recherche incomplète. Vous pouvez ainsi chercher rapidement entre des stations déjà visitées.</p>

<h3>Bénéfice possible et quantité</h3>
<ul>
<li><b>Bénéfice / t :</b> prix de vente à destination − prix d'achat ici. « Bénéfice % » = bénéfice par tonne ÷ prix d'achat × 100.</li>
<li><b>Quantité (t) :</b> le minimum entre l'espace libre en soute, l'offre du marché d'achat et la demande à destination.</li>
<li><b>Bénéfice potentiel :</b> bénéfice par tonne × quantité possible ; une estimation fondée sur les instantanés connus.</li>
</ul>
<p>Exemple : 280 t libres, offre de 150 t, demande de 20 000 t → quantité possible de 150 t. Chaque marchandise ne remplit pas automatiquement toute la soute libre.</p>

<h3>Vol commercial mémorisé</h3>
<p>Cochez une recommandation pour la mémoriser ; une seule peut l'être à la fois. En choisir une autre la remplace. La zone séparée affiche marchandise, station cible, système cible et « Bénéfice potentiel » au moment du choix. C'est un pense-bête, pas une recommandation recalculée en continu.</p>
<p>Il reste après achat, changement de soute, départ, changement de système, amarrage et ouverture d'un marché. Il disparaît avec « Retirer » ou en décochant, au démarrage effectif d'une nouvelle recherche de recommandations, au changement de commandant et à la fermeture du Helper. Il n'est pas conservé au redémarrage.</p>
<p>« Copier le système » copie uniquement le nom du système cible dans le presse-papiers. La station reste visible dans le pense-bête ; aucun itinéraire n'est créé.</p>

<h3>Recherche, progression et annulation</h3>
<p>Lancez les recherches manuellement. Les recommandations examinent plusieurs marchandises et peuvent prendre plus de temps. Une fois le périmètre défini, la barre et « Vérification des marchandises : x sur y … » indiquent les marchandises réellement vérifiées. « Annuler » n'est disponible que pendant une recherche annulable ; une réponse réseau en cours peut retarder l'annulation. Changer d'onglet annule la recherche en cours ; les filtres communs de vente/achat sont conservés.</p>
<p>Si certaines requêtes communautaires échouent ou si des limites sont atteintes, les recommandations vérifiées et valides peuvent rester affichées. Une recherche incomplète signifie que les résultats concernent les données vérifiées, mais que toutes les marchandises ou destinations n'ont pas été entièrement examinées. Lisez le message, resserrez les filtres en cas de limite ou réessayez plus tard. Une annulation manuelle supprime la liste de résultats actuelle.</p>

<h3>Diagnostic en cas de problème</h3>
<p>« Copier le diagnostic » copie des informations techniques sur la dernière recherche de recommandations terminée pour aider au dépannage. Le texte ne contient ni données de commandant/FID ni prix de marché. Le diagnostic reste en mémoire ; aucun fichier permanent n'est créé et rien n'est transmis automatiquement. Transmettez vous-même le texte copié au support si nécessaire.</p>

<h3>Effectuer un trajet commercial</h3>
<ol>
<li>Amarrez-vous à une station et ouvrez le marché dans Elite.</li>
<li>Ouvrez « Commerce » → « Recommandations » et vérifiez « Relevé effectué ».</li>
<li>Réglez le bénéfice minimal et les filtres, puis choisissez « Chercher des recommandations ».</li>
<li>Cochez la recommandation à mémoriser et achetez la marchandise dans Elite.</li>
<li>Utilisez « Copier le système » au besoin, puis rejoignez la destination ; la station reste visible dans le pense-bête.</li>
<li>Vendez dans Elite. Ouvrez le marché sur place pour actualiser aussi vos propres données de ce nouveau marché.</li>
</ol>""",
)


HELP_TOPICS["explorer"] = (
    HELP_TOPICS["explorer"][0],
    HELP_TOPICS["explorer"][1] + '<h3>PREMIER PAS</h3><p>PREMIER PAS apparaît en jaune dans la colonne Statut du corps, en complément de son état de cartographie. CMDRHelper le déduit des informations disponibles dans les journaux d’Elite, indépendamment des découvertes biologiques. Aucun dépôt auprès d’Universal Cartographics ou de Vista Genomics n’est nécessaire ; une vente ne fait pas passer le jaune au vert.</p>',
)


HELP_TOPICS["explorer"] = (
    HELP_TOPICS["explorer"][0],
    HELP_TOPICS["explorer"][1] + '<p>« Adapter à la largeur de la fenêtre » répartit automatiquement les colonnes de la liste des valeurs sur la largeur disponible. Cette option est activée par défaut et mémorisée. Une fenêtre très étroite ou une grande police peut encore nécessiter un défilement horizontal. Une fois désactivée, les largeurs restent réglables manuellement. Cette option est indépendante de l’ajustement automatique de la vue graphique générale.</p>',
)
