"""French content for contextual help."""


HELP_TOPICS = {'overview': ('Aperçu',
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
              "<p>Le bouton ou l'élément de menu «\xa0Missions\xa0» vous amène à la vue complète "
              'de la mission avec les objectifs de mission connus et les informations sur '
              "l'état.</p>\n"
              '\n'
              '<h3>Dernier combat</h3>\n'
              '<p>«\xa0Dernier état\xa0» résume le dernier état persistant connu du commandant. '
              'Cela permet de restaurer les informations importantes même après le redémarrage du '
              'Elite Dangerous ou du CMDRHelper.</p>\n'
              '\n'
              '<h3>Systèmes finaux</h3>\n'
              '<p>Les systèmes récemment visités ou reconnus dans le journal sont affichés '
              'ici.</p>\n'
              '<p>La liste constitue un aperçu rapide du récent voyage du commandant.</p>\n'
              '\n'
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
              'du journal défini sous « Paramètres ».</p>'),
 'missions': ('Missions',
              '<h2>Missions</h2>\n'
              '<p>La vue des missions montre les missions du commandant actuellement consulté, '
              'connues dans le Elite Dangerous Journal. Le CMDRHelper enregistre les données de '
              'mission commandant par commandement afin que les missions ouvertes soient '
              'conservées même après un redémarrage du Elite Dangerous ou du CMDRHelper.</p>\n'
              '\n'
              '<h3>Missions ouvertes</h3>\n'
              '<p>De nouvelles missions sortent<code>MissionAccepted</code>repris et sauvegardé '
              'définitivement.</p>\n'
              "<p>Tant qu'il n'y a pas d'événement final de mission, la mission reste ouverte. Une "
              'nouvelle session de jeu sans liste de missions peut ne pas supprimer '
              'automatiquement les missions ouvertes connues.</p>\n'
              '\n'
              '<h3>Statut de la mission</h3>\n'
              '<p>CMDRHelper traite, entre autres, les changements de statut suivants\xa0:</p>\n'
              '<ul>\n'
              '<li>Mission acceptée</li>\n'
              '<li>Mission terminée</li>\n'
              '<li>La mission a échoué</li>\n'
              '<li>Mission annulée</li>\n'
              '<li>Objectif de mission détourné</li>\n'
              '<li>Progrès réalisés dans les missions de fret/dépôt prises en charge</li>\n'
              '</ul>\n'
              '<p>Un événement final ne change que la mission associée.</p>\n'
              '\n'
              '<h3>Missions du Journal</h3>\n'
              '<p>Elite Dangerous fournit des informations de mission sur divers événements du '
              'journal. CMDRHelper fusionne ces événements dans un état de mission '
              'persistant.</p>\n'
              '<p>Un véritable événement de mission complète peut servir d’instantané faisant '
              'autorité. Si un tel événement manque, les anciennes missions ouvertes ne seront pas '
              'fermées pour cette seule raison.</p>\n'
              '\n'
              '<h3>Destinations et lieux</h3>\n'
              '<p>Dans la mesure où Elite fournit les informations dans le journal, CMDRHelper '
              'montre\xa0:</p>\n'
              '<ul>\n'
              '<li>Système cible</li>\n'
              '<li>Gare de destination ou destination</li>\n'
              '<li>Planète ou corps cible</li>\n'
              '<li>Désignation de la mission</li>\n'
              '<li>progrès connus</li>\n'
              '<li>état actuel</li>\n'
              '</ul>\n'
              '<p>Toutes les missions ne fournissent pas toutes les informations. Les données '
              'manquantes ne sont pas inventées par CMDRHelper.</p>\n'
              '\n'
              '<h3>Persistance et redémarrage</h3>\n'
              '<p>Les missions ouvertes sont enregistrées dans la base de données relative au '
              'commandant.</p>\n'
              "<p>Cela signifie qu'ils sont conservés même si\xa0:</p>\n"
              '<ul>\n'
              '<li>Elite Dangerous est terminé et redémarré plus tard</li>\n'
              '<li>CMDRHelper est fermé entre les deux</li>\n'
              '<li>La nouvelle session du journal ne contient initialement aucun événement de '
              'mission</li>\n'
              '</ul>\n'
              "<p>Seul un événement de mission documenté modifie l'état enregistré.</p>\n"
              '\n'
              '<h3>Plusieurs commandants</h3>\n'
              '<p>Les missions sont strictement séparées par le commandant.</p>\n'
              "<p>Un événement de mission n'est attribué qu'au commandant dont la session de "
              "journal a été identifiée de manière unique. Les missions d'un autre commandant ne "
              'peuvent pas être affichées ou modifiées.</p>\n'
              '\n'
              '<h3>Missions orphelines ou plus valides</h3>\n'
              '<p>Si des données de journal plus anciennes ou une importation précédente '
              "maintiennent une mission ouverte même si elle n'existe plus dans le jeu, la "
              'fonction de réinitialisation/nettoyage des missions orphelines existante peut être '
              'utilisée.</p>\n'
              "<p>Cette fonction ne doit être utilisée que s'il est clair que la mission affichée "
              "n'est plus active.</p>\n"
              '\n'
              '<h3>Services en ligne</h3>\n'
              '<p>Les événements de mission pris en charge peuvent en outre être transmis à Inara '
              'si un accès Inara valide et activé est configuré pour le journal actif FID.</p>\n'
              "<p>Une connexion Inara manquante ou inaccessible n'affecte pas le stockage de "
              'mission local.</p>\n'
              '\n'
              '<h3>Conseil</h3>\n'
              "<p>Si une mission n'apparaît pas ou affiche un statut incorrect, vérifiez d'abord "
              "si Elite Dangerous a déjà écrit l'événement de mission correspondant dans le "
              'journal.</p>\n'
              '<p>CMDRHelper ne peut afficher que les informations que le journal fournit '
              "réellement ou qui ont déjà été stockées lors d'événements de mission uniques "
              'précédents.</p>'),
 'explorer': ('Explorateur',
              '<h2>Explorateur</h2>\n'
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
              '<h3>BIOLOGIQUE ×N</h3>\n'
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
              '<p><b>ABBAU ×24</b></p>\n'
              '<p>Cela signifie que 24 sites miniers planétaires ont été signalés pour cet '
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
              '<p><b>Cuivre – 56 tonnes</b></p>\n'
              '<p>Cette information signifie que ce commandant y a effectivement extrait 56 t de '
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
              '<p>Le premier indicateur de découverte identifie les organismes pour lesquels, '
              'selon les données disponibles, une première découverte est possible ou a été '
              "documentée en conséquence par le propre journal de l'organisme.</p>\n"
              '<p>La note finale est basée sur les conditions signalées par Elite Dangerous ou sur '
              'les données disponibles.</p>\n'
              '\n'
              '<h3>Première cartographie</h3>\n'
              '<p>CMDRHelper fait la distinction entre\xa0:</p>\n'
              '<ul>\n'
              '<li>Une première cartographie peut être disponible</li>\n'
              '<li>cartographié par le commandant</li>\n'
              '<li>Première cartographie revendiquée par le commandant</li>\n'
              '</ul>\n'
              '<p>Cela permet de voir si un corps a déjà été cartographié et si votre commandant '
              'revendique le premier statut de cartographie.</p>\n'
              '\n'
              '<h3>Bar de campagne</h3>\n'
              "<p>L'indicateur d'atterrissage identifie les corps sur lesquels, selon les données "
              "connues, l'atterrissage est possible.</p>\n"
              '\n'
              '<h3>Cadres en or / corps précieux</h3>\n'
              "<p>Les corps particulièrement précieux peuvent être mis en évidence dans l'écran de "
              "l'explorateur.</p>\n"
              "<p>Le cadre doré sert d'orientation visuelle rapide pour les corps dépassant le "
              'seuil de valeur fourni dans CMDRHelper.</p>\n'
              "<p>Il ne remplace pas l'affichage détaillé de la valeur du corps.</p>\n"
              '\n'
              '<h3>Liste de valeurs</h3>\n'
              '<p>La liste de valeurs fournit une vue plus compacte des corps connus et de leurs '
              "valeurs d'exploration/cartographie.</p>\n"
              '<p>Il est particulièrement adapté pour comparer rapidement des corps intéressants '
              'ou précieux dans un système.</p>\n'
              '\n'
              '<h3>BIOLOGIQUE / GÉO / DÉGRADATION</h3>\n'
              '<p>Cette vision regroupe les corps présentant des signaux de dégradation '
              'biologiques, géologiques ou planétaires.</p>\n'
              "<p>Cela signifie qu'il n'est pas nécessaire de rechercher individuellement les "
              'corps intéressants dans la carte complète du système.</p>\n'
              '<p>Si vous disposez de vos propres données d’exploitation minière à ciel ouvert, '
              'vos découvertes minières personnelles peuvent également être visibles.</p>\n'
              '\n'
              '<h3>Détail du corps</h3>\n'
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
              '<h3>Montrer la voiture</h3>\n'
              "<p>Les indices de l'Explorateur pris en charge, tels que les corps précieux ou les "
              "découvertes BIO, peuvent être automatiquement affichés à l'aide des commutateurs "
              'dans la barre latérale gauche.</p>\n'
              "<p>Ces petites fenêtres en direct servent d'indices supplémentaires pendant la "
              "lecture et ne remplacent pas la vue complète de l'Explorateur.</p>\n"
              '<p>« Cargo » affiche le stock confirmé du Ship ou du SRV déterminé par la FID active du Journal. Le Cargo du SRV n’est jamais repris comme Cargo du Ship ; les Limpets comptent dans l’occupation totale et sont affichés séparément dans le tableau Nom | Quantité.</p>\n'
              '\n'
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
              'réelles documentées par votre propre commandant.</p>'),
 'chronicle': ('chronique',
               '<h2>chronique</h2>\n'
               "<p>La chronique est l'histoire personnelle des voyages et des découvertes du "
               'commandant. Il utilise les informations stockées en permanence dans le journal '
               'pour rechercher des systèmes déjà visités, les représenter spatialement et '
               'rechercher des découvertes connues.</p>\n'
               '\n'
               '<h3>Systèmes visités</h3>\n'
               '<p>La Chronique montre les systèmes visités et leurs emplacements dans la galaxie '
               'connus du Commandant.</p>\n'
               '<p>Si disponibles, la première et la dernière visite ainsi que les informations '
               'corporelles connues sont prises en compte.</p>\n'
               "<p>La chronique n'est donc pas seulement une carte, mais aussi un outil permettant "
               'de retrouver des destinations de voyage et des découvertes antérieures.</p>\n'
               '\n'
               '<h3>carte 3D</h3>\n'
               '<p>Les systèmes visités sont représentés spatialement en utilisant leurs '
               'coordonnées galactiques X/Y/Z.</p>\n'
               "<p>Le mode d'emploi se trouve directement au-dessus de la carte\xa0:</p>\n"
               '<ul>\n'
               '<li>Maintenez le bouton gauche de la souris enfoncé → faire pivoter la vue</li>\n'
               '<li>Maintenez le bouton central de la souris enfoncé → Zoom</li>\n'
               '<li>Maintenez le bouton droit de la souris enfoncé → déplacer la vue</li>\n'
               '</ul>\n'
               "<p>L'affichage à petit axe facilite l'orientation dans l'espace.</p>\n"
               '\n'
               '<h3>Poste actuel</h3>\n'
               '<p>Avec «\xa0Position actuelle\xa0», la vue de la carte peut être alignée ou '
               "renvoyée à l'emplacement actuellement connu du commandant actif.</p>\n"
               '<p>La condition préalable est que le commandant connaisse une position actuelle '
               'valide.</p>\n'
               '\n'
               '<h3>Aligner</h3>\n'
               "<p>«\xa0Aligner\xa0» renvoie l'orientation de la carte à l'orientation de base "
               'prévue.</p>\n'
               '<p>Ceci est utile si la carte est devenue confuse après avoir été beaucoup tournée '
               'ou déplacée.</p>\n'
               '\n'
               '<h3>Mettre à jour la chronologie</h3>\n'
               "<p>«\xa0Historique de mise à jour\xa0» met à jour l'affichage avec les données "
               'actuellement connues.</p>\n'
               '<p>La fonction ne modifie pas les fichiers journaux et ne crée pas de nouvelles '
               "données d'exploration. Il met simplement à jour l'affichage de l'historique en "
               'fonction des données CMDRHelper existantes.</p>\n'
               '\n'
               '<h3>Recherche de texte libre</h3>\n'
               '<p>Le contenu déjà connu peut être recherché à l’aide du champ « Historique de '
               'recherche… ».</p>\n'
               '<p>La recherche prend en compte – si disponible dans la base de données – entre '
               'autres :</p>\n'
               '<ul>\n'
               '<li>Noms du système</li>\n'
               '<li>Caractéristiques du corps</li>\n'
               '<li>données biologiques</li>\n'
               '<li>Matériels</li>\n'
               '<li>Données du Codex</li>\n'
               '</ul>\n'
               '<p>Le bouton « Rechercher » effectue uniquement cette recherche en texte '
               'libre.</p>\n'
               "<p>Le DÉMONTAGE des filtres séparés, par contre, s'effectue avec «\xa0Appliquer\xa0"
               '».</p>\n'
               '\n'
               '<h3>Résultats de la recherche</h3>\n'
               '<p>Les résultats sont affichés dans la liste des résultats existante sous la fiche '
               'de la chronique.</p>\n'
               '<p>Selon le type de frappe, le système et le corps ainsi que des informations '
               'supplémentaires peuvent apparaître.</p>\n'
               "<p>Un hit peut être utilisé pour trouver le système ou l'organisme correspondant "
               'déjà connu et pour ouvrir les informations détaillées existantes.</p>\n'
               '\n'
               '<h3>Sites miniers planétaires</h3>\n'
               '<p>Le filtre « Sites miniers planétaires » peut être utilisé pour rechercher '
               'spécifiquement des corps connus pour lesquels Elite Dangerous a signalé des sites '
               'miniers planétaires.</p>\n'
               "<p>L'affichage sous-jacent correspond à celui connu depuis Explorer\xa0:</p>\n"
               '<p><b>ABBAU ×N</b></p>\n'
               "<p>Le numéro appartient au corps lui-même et n'a aucun rapport avec le "
               'commandant.</p>\n'
               '\n'
               '<h3>Au moins</h3>\n'
               '<p>En utilisant « Au moins », vous pouvez spécifier le nombre minimum '
               'd’emplacements miniers planétaires qu’un corps doit avoir.</p>\n'
               '<p>Exemple:</p>\n'
               '<p><b>Au moins 20</b></p>\n'
               '<p>ne montre que les corps connus avec au moins\xa0:</p>\n'
               '<p><b>ABBAU ×20</b></p>\n'
               '<p>Cela permet de localiser spécifiquement des zones minières particulièrement '
               'étendues.</p>\n'
               '\n'
               '<h3>Propres découvertes minières</h3>\n'
               '<p>Avec «\xa0Propres découvertes minières\xa0», la recherche est limitée aux corps '
               'sur lesquels le commandant en question a manifestement effectué lui-même des '
               'fouilles à ciel ouvert.</p>\n'
               '<p>Ces informations proviennent de l’historique personnel des mines à ciel ouvert '
               'et sont strictement séparées par le commandant.</p>\n'
               '<p>Un corps peut donc disposer de signaux globaux ABBAU ×N sans que son propre '
               "commandant n'y ait déjà rien retiré.</p>\n"
               '\n'
               '<h3>matière première</h3>\n'
               '<p>Si «\xa0Propres découvertes minières\xa0» est activé, la sélection «\xa0'
               'Matières premières\xa0» est également disponible.</p>\n'
               '<p>La liste ne contient que les produits que le commandant en question a déjà '
               'acquis grâce à l’exploitation minière à ciel ouvert.</p>\n'
               '<p>Il ne s’agit pas d’une liste théorique de toutes les matières premières '
               'minières possibles.</p>\n'
               '<p>Par exemple, FABER38 peut apparaître\xa0:</p>\n'
               '<ul>\n'
               '<li>Tous</li>\n'
               '<li>cuivre</li>\n'
               '</ul>\n'
               '<p>Si des matières premières supplémentaires sont effectivement extraites '
               'ultérieurement, elles apparaîtront automatiquement dans votre sélection '
               'personnelle.</p>\n'
               '\n'
               '<h3>Recherche ciblée de matières premières</h3>\n'
               '<p>Par exemple, si «\xa0Cuivre\xa0» est sélectionné, puis «\xa0Appliquer\xa0» est '
               "enfoncé, l'historique affichera uniquement les corps sur lesquels le commandant en "
               'question a manifestement extrait du cuivre.</p>\n'
               '<p>Exemple:</p>\n'
               '<p><b>Prua Hypai NV-E c28-66 / 2 — ABBAU ×24 — cuivre 56 tonnes</b></p>\n'
               '<p>Cela signifie que la chronique peut être utilisée comme base de données de '
               'localisation personnelle : une matière première déjà extraite peut être retrouvée '
               'ultérieurement.</p>\n'
               '\n'
               '<h3>Toutes les matières premières</h3>\n'
               '<p>Avec «\xa0Matières premières\xa0:\xa0toutes\xa0», toutes les découvertes '
               "personnelles correspondantes en matière d'exploitation minière à ciel ouvert sont "
               'prises en compte.</p>\n'
               '<p>Si plusieurs marchandises sont connues sur un corps, elles peuvent être '
               "affichées avec les quantités obtenues jusqu'à présent.</p>\n"
               '<p>Exemple:</p>\n'
               '<p><b>ABBAU ×24 — Hélium-3 18 t, cuivre 56 t</b></p>\n'
               '<p>Les quantités sont les valeurs minières personnelles du commandant concerné, '
               'qui sont en fait documentées à partir des événements du journal.</p>\n'
               '\n'
               '<h3>Combiner les filtres</h3>\n'
               '<p>Les filtres miniers peuvent être combinés entre eux.</p>\n'
               '<p>Par exemple:</p>\n'
               '<ul>\n'
               '<li>Sites miniers planétaires actifs</li>\n'
               '<li>Au moins 20</li>\n'
               '<li>Ses propres découvertes minières sont actives</li>\n'
               '<li>Cuivre matière première</li>\n'
               '</ul>\n'
               '<p>recherche des corps connus avec au moins 20 sites miniers planétaires où le '
               'commandant en question a déjà extrait lui-même du cuivre.</p>\n'
               '\n'
               '<h3>Appliquer</h3>\n'
               "<p>«\xa0Appliquer\xa0» n'exécute que les filtres d'exploration de données "
               'visibles.</p>\n'
               '<p>Le bouton « Rechercher » à côté est réservé aux recherches en texte libre.</p>\n'
               "<p>Cela signifie que les filtres de recherche de texte et d'exploration de données "
               'sont délibérément séparés les uns des autres.</p>\n'
               '\n'
               '<h3>Réinitialiser</h3>\n'
               '<p>«\xa0Réinitialiser\xa0» supprime la recherche de texte libre en cours et '
               'réinitialise également les filtres de minage à leur état initial.</p>\n'
               '<p>La sélection des matières premières revient à «\xa0Tous\xa0».</p>\n'
               '\n'
               '<h3>Sélection du commandant</h3>\n'
               '<p>La chronique peut afficher les données de divers commandants bien connus.</p>\n'
               '<p>Cependant, les informations personnelles telles que vos propres découvertes '
               'minières et listes de matières premières sont toujours évaluées séparément pour le '
               'commandant réellement consulté.</p>\n'
               '<p>Un commandant ne voit dans sa sélection de matières premières aucune découverte '
               'minière appartenant exclusivement à un autre commandant.</p>\n'
               '\n'
               '<h3>Tous les commandants</h3>\n'
               "<p>L'affichage de la carte/chronique peut prendre en compte plusieurs "
               'commandants.</p>\n'
               "<p>Cela ne modifie pas l'attribution personnelle des données relatives au "
               "commandant. Les propriétés astronomiques globales d'un système ou d'un corps "
               'restent partagées, les découvertes personnelles restent séparées.</p>\n'
               '\n'
               '<h3>Aide à la recherche / légende</h3>\n'
               '<p>Des informations complémentaires sur la recherche de chroniques et la '
               "signification de l'affichage sont accessibles via « Aide à la recherche / Légende "
               '».</p>\n'
               '<p>Cette aide principale contextuelle complète les brèves instructions '
               "d'utilisation qui y sont disponibles.</p>\n"
               '\n'
               '<h3>Conseil</h3>\n'
               '<p>La chronique est particulièrement adaptée pour retrouver des lieux intéressants '
               "découverts au cours d'un voyage plus long.</p>\n"
               '<p>Pour le Surface Mining, par exemple, il peut répondre :</p>\n'
               '<p>« Sur quelle planète ai-je déjà extrait du cuivre ?</p>\n'
               '<p>ou:</p>\n'
               '<p>«\xa0Laquelle de mes planètes connues possède un nombre particulièrement élevé '
               'de sites miniers\xa0?\xa0»</p>'),
 'jump_tip': ('Astuce de saut',
              '<h2>Astuce de saut</h2>\n'
              "<p>La pointe de saut prend en charge l'exploration en évaluant les données système "
              'déjà connues et en mettant en évidence les systèmes cibles intéressants.</p>\n'
              '<p>La fonction est conçue comme une aide à la décision. Cela ne garantit pas qu’un '
              'système recommandé contienne réellement des trouvailles rares ou particulièrement '
              'précieuses.</p>\n'
              '\n'
              "<h3>Base de l'évaluation</h3>\n"
              '<p>CMDRHelper utilise les informations de journal et de base de données existantes '
              'pour évaluer les modèles connus dans les noms de système et les classes '
              'système.</p>\n'
              '<p>Entre autres choses, les abréviations du système, les types de corps déjà connus '
              'et les découvertes antérieures peuvent être pris en compte.</p>\n'
              '\n'
              '<h3>Abréviation du système</h3>\n'
              '<p>De nombreux systèmes générés de manière procédurale dans Elite Dangerous '
              'contiennent des combinaisons de lettres et de chiffres qui identifient des groupes '
              'de systèmes spécifiques.</p>\n'
              '<p>CMDRHelper peut évaluer statistiquement ces abréviations et montrer dans quels '
              'groupes les découvertes intéressantes se sont produites plus fréquemment dans les '
              'données connues à ce jour.</p>\n'
              '\n'
              '<h3>Réévaluer</h3>\n'
              '<p>Avec «\xa0Réévaluer\xa0», la base de données existante est à nouveau '
              'analysée.</p>\n'
              '<p>Les données enregistrées par le commandant sont utilisées. La fonction ne crée '
              "pas de nouvelles données d'élite ni ne modifie les fichiers journaux.</p>\n"
              '\n'
              '<h3>Liste des résultats</h3>\n'
              '<p>La liste des résultats montre les abréviations de système ou les candidats les '
              "plus intéressants selon l'évaluation actuelle.</p>\n"
              '<p>En fonction de la base de données existante, il peut y avoir des informations '
              'sur\xa0:</p>\n'
              '<ul>\n'
              '<li>cours planétaires intéressants</li>\n'
              '<li>découvertes biologiques</li>\n'
              '<li>Mondes aquatiques</li>\n'
              '<li>corps terraformables</li>\n'
              "<li>autres résultats d'exploration notables</li>\n"
              '</ul>\n'
              '<p>apparaître.</p>\n'
              '\n'
              '<h3>La probabilité au lieu de la garantie</h3>\n'
              "<p>Une valeur élevée ou un bon classement signifie simplement qu'un certain modèle "
              'était plus souvent associé à des résultats intéressants dans les données évaluées '
              "jusqu'à présent.</p>\n"
              "<p>Ce n'est pas une garantie.</p>\n"
              "<p>Un système recommandé peut rester totalement inintéressant, tandis qu'un système "
              'mal noté peut contenir des découvertes précieuses.</p>\n'
              '\n'
              '<h3>Propre base de données</h3>\n'
              '<p>La pointe de saut fonctionne avec les données déjà connues du commandant.</p>\n'
              '<p>Plus les systèmes et les organismes sont enregistrés au fil du temps, plus la '
              'base de données personnelle destinée à l’évaluation s’agrandit.</p>\n'
              '<p>Cela signifie que le classement peut changer ultérieurement.</p>\n'
              '\n'
              '<h3>Plusieurs commandants</h3>\n'
              '<p>Les évaluations personnelles sont traitées commandant par commandement.</p>\n'
              "<p>Les données provenant d'un autre commandant ne doivent pas falsifier la "
              "qualification personnelle sans que l'on s'en aperçoive.</p>\n"
              '<p>En revanche, les données de référence astronomiques mondiales peuvent être '
              'partagées à condition qu’elles ne représentent pas des découvertes personnelles '
              'liées au commandant.</p>\n'
              '\n'
              '<h3>Utilisation en pratique</h3>\n'
              "<p>La pointe de saut est particulièrement adaptée s'il existe plusieurs "
              'destinations possibles parmi lesquelles choisir et si une aide supplémentaire à la '
              'décision est souhaitée.</p>\n'
              "<p>Il ne remplace pas un planificateur d'itinéraire complet et ne calcule pas un "
              'itinéraire sûr et optimal.</p>\n'
              "<p>L'élément de menu «\xa0Planificateur d'itinéraire\xa0» est disponible pour la "
              "planification d'itinéraires spécifiques.</p>\n"
              '\n'
              '<h3>Conseil</h3>\n'
              "<p>Utilisez la pointe de saut comme aide à l'exploration supplémentaire\xa0:</p>\n"
              '<p>"D\'après mes données précédentes, quel système semble le plus intéressant '
              '?"</p>\n'
              '<p>Pas comme une prédiction\xa0:</p>\n'
              '<p>"Il est garanti qu\'il y aura une découverte spécifique dans ce système."</p>'),
 'route_planner': ("Planificateur d'itinéraire",
                   "<h2>Planificateur d'itinéraire</h2>\n"
                   "<p>Le planificateur d'itinéraire prend en charge la planification de voyages "
                   'plus longs en bateau ou en Fleet Carrier. Le CMDRHelper peut utiliser les '
                   "données d'itinéraire externes du Spansh et préparer l'itinéraire planifié pour "
                   'une utilisation ultérieure.</p>\n'
                   '\n'
                   '<h3>Commencer et terminer</h3>\n'
                   '<p>Un système de départ et de destination est requis pour le calcul de '
                   "l'itinéraire.</p>\n"
                   '<p>Dans la mesure du possible, le CMDRHelper peut utiliser le système connu '
                   'actuel du Commander comme point de départ. Le début et la fin doivent être '
                   'vérifiés avant le calcul.</p>\n'
                   '\n'
                   '<h3>Navire ou Fleet Carrier</h3>\n'
                   "<p>Le planificateur d'itinéraire fait la différence entre les voyages avec un "
                   'navire normal et avec un Fleet Carrier.</p>\n'
                   '<p>Les deux utilisent des exigences et des méthodes de calcul différentes. Par '
                   "conséquent, le type d'itinéraire approprié doit être sélectionné avant la "
                   'planification.</p>\n'
                   '\n'
                   '<h3>Itinéraire du navire</h3>\n'
                   '<p>Pour une route de navire, les propriétés de saut connues ou saisies pour le '
                   'navire actif sont prises en compte.</p>\n'
                   '<p>En fonction des données disponibles, les données FSD, les données du '
                   "navire, la masse, le carburant et d'autres paramètres de saut peuvent être "
                   'intégrés dans la planification.</p>\n'
                   '<p>Un itinéraire calculé est une aide à la planification. Les modifications '
                   'apportées au vaisseau ou à sa masse peuvent modifier la distance de saut '
                   'réelle réalisable dans le jeu.</p>\n'
                   '\n'
                   '<h3>Itinéraire du transporteur de flotte</h3>\n'
                   '<p>Les Fleet Carrier ont des règles de saut différentes de celles des navires '
                   'normaux.</p>\n'
                   '<p>CMDRHelper utilise la planification du transporteur Spansh désignée pour '
                   'les itinéraires correspondants.</p>\n'
                   "<p>L'itinéraire est utilisé pour planifier la séquence de sauts. La "
                   "consommation réelle de tritium et l'autonomie disponible peuvent également "
                   "dépendre de la masse et de l'état actuel du transporteur.</p>\n"
                   '\n'
                   '<h3>Spansh</h3>\n'
                   "<p>Pour le calcul de l'itinéraire réel, CMDRHelper peut utiliser le service "
                   'externe Spansh.</p>\n'
                   "<p>La requête est traitée en arrière-plan afin que l'interface reste "
                   "opérationnelle lors d'un calcul plus long.</p>\n"
                   '<p>CMDRHelper n’a aucune influence sur la disponibilité ou le temps de réponse '
                   'du service externe.</p>\n'
                   '\n'
                   '<h3>calcul</h3>\n'
                   '<p>Après avoir lancé un calcul, la demande est transmise au planificateur '
                   "d'itinéraire sélectionné.</p>\n"
                   "<p>Selon l'itinéraire et le service, le calcul peut prendre un certain temps. "
                   'Pendant ce temps, aucun deuxième calcul identique ne doit être lancé '
                   'inutilement.</p>\n'
                   '\n'
                   '<h3>Résultat</h3>\n'
                   '<p>Un itinéraire calculé avec succès montre les systèmes ou points de saut '
                   'prévus dans leur ordre.</p>\n'
                   "<p>Selon le type d'itinéraire, des informations supplémentaires apparaissent "
                   "sur la distance, les sauts, le carburant ou le tritium et d'autres données "
                   "d'itinéraire disponibles.</p>\n"
                   '\n'
                   '<h3>Itinéraire et commandant actuel</h3>\n'
                   "<p>Le système et le vaisseau actuels peuvent - à condition qu'ils soient "
                   "clairement connus dans l'AppState actif - être utilisés pour la "
                   'pré-affectation ou pour prendre en charge la planification.</p>\n'
                   "<p>Cependant, l'itinéraire réel reste un plan et ne modifie aucune donnée du "
                   'journal ou du commandant.</p>\n'
                   '\n'
                   '<h3>Exportation CTSVision</h3>\n'
                   '<p>Les itinéraires calculés des transporteurs de flotte peuvent être exportés '
                   'au format CSV pour CTSVision.</p>\n'
                   "<p>Cela signifie qu'un itinéraire porteur planifié dans CMDRHelper peut "
                   'ensuite être utilisé dans CTSVision pour le contrôle des sauts ou le '
                   "traitement de l'itinéraire.</p>\n"
                   "<p>L'export ne modifie pas l'itinéraire dans CMDRHelper.</p>\n"
                   '\n'
                   '<h3>Fichier CSV</h3>\n'
                   "<p>Le fichier exporté contient les données d'itinéraire requises pour "
                   "CTSVision dans l'ordre prévu.</p>\n"
                   '<p>Le fichier ne doit pas être modifié structurellement de manière incontrôlée '
                   "après l'exportation s'il doit ensuite être lu par CTSVision.</p>\n"
                   '\n'
                   '<h3>Erreurs et services externes</h3>\n'
                   '<p>Si Spansh ne peut pas être atteint ou si le service renvoie une erreur, '
                   "CMDRHelper affiche un message d'erreur correspondant.</p>\n"
                   "<p>Une erreur dans le calcul d'itinéraire en ligne ne modifie pas les données "
                   'du commandant local ou du journal.</p>\n'
                   '\n'
                   "<h3>Planificateur d'itinéraire et conseil de saut</h3>\n"
                   "<p>La pointe de saut et le planificateur d'itinéraire remplissent différentes "
                   'tâches\xa0:</p>\n'
                   '<ul>\n'
                   "<li>La pointe de saut évalue les cibles d'exploration intéressantes possibles "
                   'en fonction des données existantes.</li>\n'
                   "<li>Le planificateur d'itinéraire calcule un itinéraire spécifique entre le "
                   'départ et la destination.</li>\n'
                   '</ul>\n'
                   "<p>Une bonne astuce de saut ne fait donc pas automatiquement partie d'un "
                   'parcours optimal.</p>\n'
                   '\n'
                   '<h3>Plusieurs commandants</h3>\n'
                   '<p>Si des données relatives au commandant telles que le système actuel ou le '
                   "navire sont utilisées, elles proviennent de l'AppState actif en direct et "
                   'doivent y être clairement attribuées.</p>\n'
                   '<p>Le simple fait de regarder un autre commandant dans la vue CMDR ne fait pas '
                   "basculer le planificateur d'itinéraire vers son système ou son navire.</p>\n"
                   "<p>Un calcul d'itinéraire en lui-même ne modifie pas les données personnelles "
                   "d'un autre commandant.</p>\n"
                   '\n'
                   '<h3>Conseil</h3>\n'
                   '<p>Avant un long voyage, vérifiez toujours à nouveau\xa0:</p>\n'
                   '<ul>\n'
                   '<li>Système de démarrage</li>\n'
                   '<li>Système cible</li>\n'
                   "<li>Type d'itinéraire navire/transporteur</li>\n"
                   '<li>pour les itinéraires des navires, le navire sous-jacent, le FSD et les '
                   'paramètres de saut</li>\n'
                   '<li>pour les itinéraires transporteurs, la réserve de tritium disponible</li>\n'
                   '</ul>\n'
                   '<p>Pour les déplacements en flotte, il convient de prévoir également des '
                   'réserves suffisantes pour le retour ou les détours imprévus.</p>'),
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
            '<h3>Traitement automatique</h3>\n'
            '<p>Si «\xa0Convertir automatiquement\xa0» est activé et que des dossiers source et de '
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
            "<p>Par défaut, le fichier BMP d'origine est conservé. Si «\xa0Supprimer le BMP après "
            "la conversion\xa0» est activé, le BMP source ne sera supprimé qu'une fois l'image "
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
            '<p><b>FABER38_F12520967/</b></p>\n'
            '<p>Le FID maintient la mission claire même avec plusieurs commandants. Cela permet de '
            'distinguer deux commandants portant le même nom.</p>\n'
            '\n'
            '<h3>noms de fichiers</h3>\n'
            "<p>Les nouvelles images traitées reçoivent un nom avec l'heure de capture, le nom du "
            'commandant et - si disponible - le système stellaire connu lors de la file '
            "d'attente.</p>\n"
            '<p>Exemple:</p>\n'
            '<p><b>2026-09-04_13-18-22_FABER38_Prua-Hypai-RB-D-c29-71.png</b></p>\n'
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
            'continuellement<code>_2</code>,<code>_3</code>,<code>_4</code>et ainsi de suite.</p>\n'
            "<p>Cela signifie qu'une autre capture d'écran avec le même horodatage n'écrasera pas "
            'une image cible existante.</p>\n'
            '\n'
            '<h3>Changement de commandant pendant le traitement</h3>\n'
            '<p>Le Commander, le FID et le système sont capturés ensemble lors de la mise en file '
            "d'attente d'une capture d'écran.</p>\n"
            '<p>Un changement ultérieur de commandant ne modifie pas l’affectation de cette image '
            "déjà en attente. Cela signifie qu'une capture d'écran de FABER38 n'est pas ensuite "
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
            '<p>Ce sera dans le sous-dossier<b>UNKNOWN_UNKNOWN/</b>traité; le nom de fichier '
            'également utilisé pour le Commander<b>INCONNU</b>. Ce dossier peut être consulté via '
            'Tous les commandants, et non via le filtre du dossier racine non alloué.</p>\n'
            '\n'
            '<h3>Plusieurs commandants</h3>\n'
            "<p>Deux règles distinctes s'appliquent à la gestion des images\xa0:</p>\n"
            '<ul>\n'
            "<li><b>Enregistrer de nouvelles images\xa0:</b>L'identité du journal actif avec "
            "Commander et FID lorsqu'ils sont mis en file d'attente détermine le dossier de "
            'destination.</li>\n'
            '<li><b>Voir les images\xa0:</b>Le commandant visualisé ou le filtre de galerie '
            'sélectionné détermine les images visibles.</li>\n'
            '</ul>\n'
            "<p>Cela signifie que la galerie d'un autre commandant peut être consultée pendant la "
            "lecture de FABER38 sans que de nouvelles captures d'écran ne finissent dans le "
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
 'commander_view': ('Vue CMDR',
                    '<h2>Vue CMDR</h2>\n'
                    '<p>La vue CMDR résume les informations personnelles stockées en permanence '
                    "d'un commandant.</p>\n"
                    '<p>Il vous permet également de basculer entre les commandants connus '
                    "CMDRHelper et d'afficher leurs propres données. Les informations personnelles "
                    "sont séparées à l'aide de l'ID Frontier (FID).</p>\n"
                    '\n'
                    '<h3>Sélectionnez le commandant</h3>\n'
                    '<p>Si plusieurs commandants sont connus, vous pouvez utiliser la sélection '
                    'ci-dessus pour déterminer dont les informations enregistrées sont affichées. '
                    'Ce commandant est le commandant considéré.</p>\n'
                    "<p>L'écran le marque comme « Live Active » ou « View Only ».</p>\n"
                    '\n'
                    '<h3>Considéré comme commandant et Live Commander</h3>\n'
                    "<p>La sélection d'un autre commandant dans la vue CMDR n'en fait pas le "
                    'commandant de journal actif.</p>\n'
                    '<p>Le commandant réel est déterminé exclusivement à partir de la session de '
                    'journal Elite Dangerous actuellement identifiée de manière unique. De cette '
                    "façon, l'historique d'un autre commandant peut être consulté pendant que le "
                    'Elite Dangerous continue de fonctionner avec FABER38.</p>\n'
                    '\n'
                    '<h3>ID Frontier (FID)</h3>\n'
                    "<p>Le FID est l'identifiant stable Frontier d'un commandant.</p>\n"
                    "<p>CMDRHelper l'utilise et l'ID de commandant interne résolu à partir de "
                    'celui-ci pour séparer en toute sécurité les données personnelles. Les '
                    'commandants portant des noms similaires ou identiques restent également '
                    'séparés.</p>\n'
                    '\n'
                    '<h3>Aperçu</h3>\n'
                    "<p>L'onglet «\xa0Aperçu\xa0» affiche uniquement les informations enregistrées "
                    'de manière permanente pour le commandant en question\xa0:</p>\n'
                    '<ul>\n'
                    '<li>Nom du commandant, FID et statut «\xa0Live actif\xa0» ou «\xa0Affichage '
                    'uniquement\xa0»</li>\n'
                    '<li>première et dernière heure connue</li>\n'
                    '<li>Nombre de systèmes visités, découvertes bio et géo, entrées de codex et '
                    'ventes de cartographie</li>\n'
                    '<li>Dernier emplacement connu et nombre de missions ouvertes</li>\n'
                    '<li>navire actuel ou dernier</li>\n'
                    '<li>Fleet Carrier et emplacement du transporteur</li>\n'
                    '<li>Actifs</li>\n'
                    '<li>biodonnées ouvertes et données cartographiques ouvertes, y compris les '
                    'estimations existantes</li>\n'
                    '</ul>\n'
                    '\n'
                    '<h3>Actifs/Crédits</h3>\n'
                    '<p>Le champ « Actifs » affiche le solde créditeur le plus récemment '
                    "enregistré du commandant en question à partir d'un événement de journal "
                    'approprié, au format, par exemple :<b>1\xa0234\xa0567 Cr</b>.</p>\n'
                    '<p>CMDRHelper n’ajoute pas de revenus ou de dépenses fictifs s’il n’existe '
                    'pas de nouveau statut de journal sécurisé.</p>\n'
                    '\n'
                    '<h3>Pièces de mercenaires</h3>\n'
                    '<p>Les pièces de mercenaires proviennent des champs MercCoins fournis par '
                    'Elite Dangerous<code>Statistics → Bank_Account</code>et sont enregistrés en '
                    "relation avec le commandant en tant qu'instantané Frontier.</p>\n"
                    '<p>Sont visibles\xa0:</p>\n'
                    '<ul>\n'
                    '<li>Actuel</li>\n'
                    '<li>Total dépensé</li>\n'
                    '<li>Ingénierie</li>\n'
                    '<li>équipement</li>\n'
                    '<li>Rapporté par Frontier\xa0: gagné globalement</li>\n'
                    '</ul>\n'
                    '\n'
                    '<h3>Actuel et éditions</h3>\n'
                    '<p>Spectacles « actuels »<code>MercCoins_Current</code>. Le « Total dépensé » '
                    'prend le relais<code>MercCoins_Total_Spent</code>.</p>\n'
                    '<p>«\xa0Ingénierie\xa0» et «\xa0Équipement\xa0» montrent les parts déclarées '
                    'séparément par '
                    'Frontier<code>MercCoins_Spent_On_Engineering</code>et<code>MercCoins_Spent_On_MercGear</code>.</p>\n'
                    '<p>Pour FABER38, par exemple, un inventaire actuel de<b>1 275</b>, au '
                    "total<b>220</b>dépensé et parti<b>220</b>signalé pour l'ingénierie.</p>\n"
                    '\n'
                    '<h3>Globalement mérité</h3>\n'
                    '<p>«\xa0Rapporté par Frontier\xa0: gagné globalement\xa0» '
                    'montre<code>MercCoins_Total_Earned</code>. CMDRHelper ne calcule pas son '
                    'propre bilan à partir de cela.</p>\n'
                    "<p>Il n'est pas nécessaire que la valeur cumulée de Frontier corresponde "
                    "mathématiquement à l'inventaire actuel et aux dépenses déclarées. Par "
                    'exemple, 1\xa0275\xa0actuels, 25\xa0au total gagnés et 220 au total dépensés '
                    'peuvent être déclarés en même temps.</p>\n'
                    '<p>CMDRHelper ne corrige pas ces valeurs, mais affiche les compteurs '
                    'individuels Frontier inchangés.</p>\n'
                    '\n'
                    '<h3>Pourquoi ne pas avoir votre propre bilan MercCoins\xa0?</h3>\n'
                    "<p>Elite Dangerous ne fournit pas d'enregistrement de journal unique pour "
                    'chaque réception ou dépense individuelle de pièces de mercenaires. Les '
                    'MercCoins apparaissent sous forme de totaux dans Statistics.</p>\n'
                    '<p>Un historique de réservation auto-calculé ne serait donc pas fiable. '
                    'CMDRHelper enregistre à la place le dernier instantané Frontier connu.</p>\n'
                    '\n'
                    '<h3>Missions</h3>\n'
                    "<p>L'onglet « Missions » affiche les missions sauvegardées du commandant en "
                    'question sous forme de tableau avec le statut, le nom de la mission, '
                    "l'objectif, le délai d'expiration et la récompense.</p>\n"
                    '\n'
                    '<h3>exploration</h3>\n'
                    "<p>L'onglet Exploration affiche les biodonnées ouvertes, les données de "
                    'cartographie ouverte, les biodécouvertes, les premières visites, les corps '
                    'auto-cartographiés et efficacement cartographiés, ainsi que le nombre de '
                    'systèmes visités.</p>\n'
                    "<p>L'onglet dédié «\xa0Chronique\xa0» dans la vue CMDR est actuellement "
                    "encore un espace réservé. La chronique complète se trouve dans l'élément de "
                    'menu principal du même nom.</p>\n'
                    '\n'
                    '<h3>Navires/Flotte</h3>\n'
                    "<p>L'onglet «\xa0Navires\xa0» affiche initialement le navire actif ou le plus "
                    "récemment utilisé avec le nom du navire, le type de navire, l'emplacement et "
                    'le ShipID.</p>\n'
                    '<p>Les navires sauvegardés du commandant en question apparaissent en dessous '
                    'sous forme de cartes extensibles. Ils peuvent être triés par ordre croissant '
                    'ou décroissant :</p>\n'
                    '<ul>\n'
                    '<li>dernier ou actuellement utilisé</li>\n'
                    '<li>Nom ou type de navire</li>\n'
                    '<li>portée de saut maximale</li>\n'
                    '<li>Capacité de chargement ou masse à vide</li>\n'
                    '<li>dernier lieu ou heure connu</li>\n'
                    '</ul>\n'
                    '<p>Vous pouvez également filtrer tous les navires, les navires avec un hangar '
                    'pour véhicules ou les navires avec un hangar pour chasseurs.</p>\n'
                    '\n'
                    '<h3>Détails du navire</h3>\n'
                    "<p>Une carte de navire ouverte affiche - si elle est enregistrée - l'ID du "
                    "navire, le ShipID, l'emplacement, la dernière fois, la portée maximale de "
                    'saut, le booster FSD et Guardian, la masse, les capacités de chargement et de '
                    "réservoir ainsi que le temps et l'état de chargement.</p>\n"
                    '<p>Si les données du module sont disponibles, le hangar de véhicules et de '
                    'chasseurs, le générateur de bouclier et le booster de bouclier, les renforts '
                    'de bouclier Guardian, les armes, les renforts de coque et de module et les '
                    'cabines de passagers sont également résumés.</p>\n'
                    "<p>L'état du chargement peut être complet, incomplet ou obsolète. Les "
                    'informations manquantes sont affichées sous la forme « – » et ne sont pas '
                    'inventées.</p>\n'
                    '\n'
                    '<h3>Fleet Carrier</h3>\n'
                    '<p>Pour un Fleet Carrier personnalisé enregistré, la vue affiche le nom de '
                    "l'opérateur, l'indicatif d'appel, l'ID de l'opérateur, le dernier emplacement "
                    "et l'heure de la dernière mise à jour.</p>\n"
                    '\n'
                    '<h3>État commandant persistant</h3>\n'
                    '<p>Les informations importantes sur le commandant restent enregistrées en '
                    "permanence. Cela permet d'afficher à nouveau les valeurs connues après un "
                    'redémarrage de CMDRHelper ou Elite Dangerous sans réévaluer complètement '
                    'chaque journal.</p>\n'
                    '<p>De nouveaux événements de journal uniques mettent à jour l’état '
                    'enregistré.</p>\n'
                    '\n'
                    '<h3>Reconstitution historique</h3>\n'
                    '<p>Pour les fonctions ajoutées ultérieurement, le CMDRHelper peut rechercher '
                    'des informations déjà connues dans les zones de journal existantes qui sont '
                    'clairement attribuées une fois à un commandant.</p>\n'
                    "<p>Par exemple, d'anciens instantanés MercCoins peuvent être adoptés. Les "
                    'contrôles répétés ne visent pas à produire des données en double et ne '
                    'modifient pas les positions normales de lecture du journal.</p>\n'
                    '\n'
                    '<h3>Plusieurs commandants</h3>\n'
                    '<p>En particulier, les éléments suivants restent distincts en termes de '
                    'commandants\xa0:</p>\n'
                    '<ul>\n'
                    '<li>Atouts et missions</li>\n'
                    '<li>propre cartographie et trouvailles organiques</li>\n'
                    '<li>Histoire des mines à ciel ouvert et pièces de mercenaires</li>\n'
                    '<li>Identifiants en ligne</li>\n'
                    "<li>captures d'écran liées au commandant</li>\n"
                    '</ul>\n'
                    '<p>Les propriétés astronomiques globales d’un système ou d’un corps peuvent '
                    'cependant être utilisées ensemble.</p>\n'
                    '\n'
                    "<h3>Impact sur d'autres points de vue</h3>\n"
                    '<p>Changer le commandant en question met à jour la vue CMDR elle-même, la '
                    'sélection personnelle des matières premières minières de la chronique et, '
                    "avec le filtre approprié, la galerie de captures d'écran.</p>\n"
                    '<p>Il ne remplace pas le véritable commandant en direct pour le traitement du '
                    'journal ou les téléchargements en ligne.</p>\n'
                    '\n'
                    '<h3>Inara et EDSM</h3>\n'
                    '<p>Les accès Inara et EDSM sont gérés séparément par commandant et FID, '
                    'respectivement.</p>\n'
                    '<p>Le simple fait de regarder un commandant ne démarre pas une transmission '
                    'avec son API-Key. Seul le journal actif FID est pertinent pour les '
                    'téléchargements en direct.</p>\n'
                    "<p>Les données d'accès sont gérées sous « Paramètres » dans la zone des "
                    'services en ligne.</p>\n'
                    '\n'
                    '<h3>Conseil</h3>\n'
                    '<p>Utilisez la vue CMDR si vous souhaitez afficher les informations '
                    'personnelles enregistrées pour un commandant spécifique.</p>\n'
                    '<p><b>Vue CMDR = Qui dois-je voir\xa0?</b></p>\n'
                    '<p><b>Active Journal-FID = Qui joue actuellement\xa0?</b></p>\n'
                    '<p>Cette séparation évite que les données personnelles ou les téléchargements '
                    'en ligne de différents commandants ne soient mélangés.</p>'),
 'settings': ('Paramètres',
              '<h2>Paramètres</h2>\n'
              '<p>La zone « Paramètres » détermine comment le CMDRHelper fonctionne avec le Elite '
              'Dangerous, les fichiers journaux, la base de données, les services en ligne, '
              "l'interface et les mises à jour.</p>\n"
              '<p>Les modifications des informations d’identification et des parcours doivent être '
              'effectuées avec soin. Les paramètres liés au contrôleur sont gérés séparément par '
              "l'ID Frontier si nécessaire.</p>\n"
              '\n'
              '<h3>journal</h3>\n'
              "<p>Le dossier du journal est l'un des paramètres les plus importants. Il doit "
              'pointer vers le dossier où Elite Dangerous le<code>Journal*.log</code>fichiers du '
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
              '\n'
              '<h3>Mises à jour</h3>\n'
              "<p>Le groupe de mise à jour affiche la version installée et l'état de GitHub. "
              'Vérifier maintenant recherche manuellement une nouvelle version planifiée de '
              'CMDRHelper\xa0; De plus, un contrôle automatique différé a lieu après le '
              'départ.</p>\n'
              '<p>Si une nouvelle version est disponible, CMDRHelper vous le demandera avant de '
              "télécharger et d'installer. Une mise à jour de base de données annoncée est "
              'affichée séparément dans cette boîte de dialogue.</p>\n'
              '\n'
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
              "s'appliquent les données d'accès en ligne visibles.</p>")}

DIALOG_TITLE = 'Aide – {area}'
CLOSE_LABEL = 'Fermer'
