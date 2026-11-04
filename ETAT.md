# État du projet

_Tenu à jour par le chef. Dernière mise à jour : 2026-11-04_

## Objectif

Banc d'essai virtuel de drones multirotors : à partir du seul hardware (assemblage 3D, matériaux,
références des composants), obtenir automatiquement un vol simulé en 3D avec un vrai firmware et une
fiche de performances indiquant l'origine de chaque valeur. Priorité : comportement en vol. Classe visée : FPV 3 à 7 pouces.
But : tester du nouveau hardware et prédire les performances de drones que personne n'a mesurés, donc
le plus souvent hors du domaine validé. Centre de l'expérience : piloter son drone à la main pour en juger
le ressenti.

## Phase actuelle

1 — Outillage (cadrage validé)

## Contrats figés

| Contrat | Fichier | Validé le |
|---|---|---|
| — | — | — |

## En cours

| Agent | Tâche | Lancé à | Durée estimée |
|---|---|---|---|
| — | — | — | — |

## File prête (validée, en attente d'une place libre)

- [6] Suite, à reprendre après un `/usage` à jour : corriger `pilot.py` (`self.st = None` dans `Pilote.__init__`), premier
  vol, puis icône, notice et latence. Commandes dans `~/drone-tools/betaflight-proto/ETAT_REPRISE.md`, section « Pilotage à la main »

## Bloqué (en attente d'une entrée non figée)

| Tâche | Attend |
|---|---|
| Contrats d'interface, dont le format de la fiche hardware | Fiches [1] à [5], choix du firmware |
| Chaîne minimale de bout en bout | Contrats d'interface |
| [2] Reprise CFD, reportée : niveau 6, banc motorBike, ParaView | Chaîne minimale |

## File de décisions pour l'utilisateur

_Ce que tu peux trancher ou relire pendant que les agents travaillent._

- Double-cliquer sur les icônes (FreeCAD, Gmsh, CalculiX, Gazebo + PX4, QGroundControl, terminal PX4, OpenFOAM,
  ParaView, Betaflight) entre deux fiches, pas pendant les vols de mesure, et confirmer que les fenêtres s'ouvrent
- Choix du firmware, après le premier vol à la main de [6] Suite (recommandation de [4] : Betaflight, PX4 en
  repli, firmware isolé derrière une interface)
- Supprimer ou non `~/drone-tools/betaflight-proto/run/` (859 Mo, contient l'EEPROM au mélangeur corrigé)
- Fusionner ou non `initialisation` dans `main` (e987ee4 : fusion à faire par l'utilisateur, pas encore relue par un vérificateur)

### Périmètre (validé par « go pour tout » le 2026-11-03)

- Inclus : multirotors, logiciels gratuits ou open source, sur ce PC
- Exclu : voilures fixes et VTOL, essais sur hardware réel, optimisation automatique des designs
- CFD : en option, pour les configurations finalistes seulement

## Consommation de la session

- Dernière mesure : 60 % de la session, 22 % de la semaine (`/usage`, 2026-11-04, après la fin de [6])
- Seuil atteint : 50 % (tâches à fort impact seulement, pas d'exploration coûteuse)
- Réinitialisation : session à 17:19 ; semaine le dimanche 8 novembre à 19:59

## Journal

- 2026-11-03 : cadrage. Validés : comportement en vol prioritaire, FPV 3 à 7 pouces, pas de drone pour
  l'instant, installation par scripts lancés par l'utilisateur
  (`docs/decisions/2026-11-03-cadrage-initial.md`). Fiches [1] à [5] proposées.
- 2026-11-03 17:42 : « go pour tout ». Ajout de l'utilisateur : une icône sur le bureau à chaque
  installation. Pas d'agents configurés : agents généraux avec le rôle dans la consigne. [1] à [4]
  lancées, [5] en file (limite de 4 agents).
- 2026-11-03 17:48 : [4] terminée (rapport reçu, recommandations non testées à l'exécution). [5] lancée.
  Fiche hardware décidée : matériaux par nom de pièce, CAO complète obligatoire, YAML commenté, question
  groupée pour les données manquantes (`docs/decisions/2026-11-03-fiche-hardware.md`). Fiche [6] proposée.
- 2026-11-03 : [1] en pause, script sudo prêt et relu, jamais exécuté. PX4 v1.17.0 cloné dans
  `~/drone-tools/`. Ni compilation, ni vol, ni icône pour l'instant.
- 2026-11-03 : [6] validée, en attente de Gazebo. [5] terminée : TII Racing recommandé, NeuroBEM en
  complément pour la dynamique moteur. Données non téléchargées ni analysées. Fiche [7] proposée.
- 2026-11-03 17:55 : script sudo de [1] exécuté, Gazebo Sim 8.15.0 constaté. Suite de [1] et [7] lancées.
  [6] débloquée, en file (limite de 4 agents). STL : un fichier par pièce. Vent et autonomie : marqués
  « non validés », approximation écartée pour l'instant
  (`docs/decisions/2026-11-03-validation-vent-autonomie.md`).
- 2026-11-03 17:57 : [3] terminée sans sudo (FreeCAD 1.1.4, Gmsh 4.15.2, CalculiX 2.23), réserve sur la
  contrainte max brute de la poutre, à traiter pour les bras. [2] en pause, script sudo relu. [6] lancée à
  43 % de session.
- 2026-11-03 : [7] terminée : TII Racing retenu par l'éclaireur pour les performances de vol, pas pour la
  CAO ni l'inertie. Agilicious et NeuroBEM sans CAO exploitable, et ce sont deux drones différents.
  Données dans `~/drone-tools/validation-tii/`. Fiche [8] proposée, choix du drone non encore validé.
- 2026-11-03 18:01 : script sudo de [2] exécuté, OpenFOAM v2512 et ParaView constatés, ROS intact. Suite de
  [2] lancée.
- 2026-11-03 : TII Racing validé comme drone de validation. Exigence de l'utilisateur : la chaîne ne doit
  pas marcher que pour lui (`docs/decisions/2026-11-03-drone-validation-et-generalite.md`). [8] lancée.
  `/usage` : 55 %, seuil de 50 % franchi.
- 2026-11-03 : [8] terminée. Table 2020KV + T5147-3 trouvée chez un revendeur, table T-Motor non lue, aucune
  source indépendante consultée. Vols autonomes sans échelons. L'agent a tenté un curl avec faux User-Agent
  malgré la consigne, refusé par le système et non réessayé. Domaine de validité par étiquette validé.
- 2026-11-03 : but précisé et validé : tester du nouveau hardware. Quatre points de conception retenus
  pour les contrats (décision 4 de `docs/decisions/2026-11-03-drone-validation-et-generalite.md`).
- 2026-11-03 : changement d'orientation : estimation à partir du modèle 3D par défaut, valeurs externes en
  option. Test à l'aveugle et répartition des vols validés. Comparaison entre drones confirmée. Marges
  d'incertitude remises en question. Fiche [9] proposée.
- 2026-11-03 : précision : la source dépend du composant. Châssis : 3D et matériau. Moteur et batterie : modèle
  commercial et recherche de données. Fiche [9] non lancée, son périmètre change.
- 2026-11-03 : validés : hélice par référence si commerciale et par le 3D si conçue par l'utilisateur, ESC et
  contrôleur de vol par référence. Fiche [9] reportée après la chaîne minimale.
- 2026-11-03 : marges « ± » retirées : origine de chaque valeur et écart du test à l'aveugle. `/usage` : 72 %.
- 2026-11-03 18:29 : arrêt propre demandé par l'utilisateur, [1], [2] et [6] non closes, toutes leurs mesures
  de temps prises sur PC saturé. [1] : PX4 v1.17.0 compilé, 9 vols complets dont 4 réussis, erreur d'altitude
  inexpliquée. [2] : sphère Re=100, Cd=1,0928 au niveau 5, banc turbulent non abouti, projection drone non
  mesurée. [6] : Betaflight 2026.6.2 vole et charge ses paramètres, 2 armements échoués sur 5, vent et échelon
  jamais lancés. Firmware non tranché. Travail commité et poussé sur `initialisation`.
- 2026-11-04 12:29 : reprise autorisée par l'utilisateur, PC au repos. L'utilisateur a fusionné ce travail dans
  `main` (demande n°2, sans relecture par un vérificateur). [1] relancée seule, [6] et [2] en file.
- 2026-11-04 : le pilotage à la main devient le centre de l'expérience, tests généraux retenus
  (`docs/decisions/2026-11-04-pilotage-et-tests.md`). Fiche [6] à représenter avec le pilotage temps réel.
- 2026-11-04 12:37 : [1] partielle : 3 vols sur 3 réussis sur machine libre, erreur d'altitude disparue, charge CPU
  fortement suspectée, non prouvée. Suite de [1] relancée pendant la pause de l'utilisateur, sans essai de charge.
- 2026-11-04 12:55 : [1] critère atteint : 5 vols consécutifs réussis sur machine libre, facteur temps réel 0,98 à
  vitesse 1 et 5,7 au maximum, MAVSDK a volé. Restent à tester par l'utilisateur : fenêtre 3D, icône, QGroundControl.
  [6] relancée dans son périmètre validé, sans pilotage à la main.
- 2026-11-04 : validés : manette et clavier, vues FPV et extérieure, suite de [6] avec pilotage, [2] reportée, pas
  d'essai de charge pour l'instant.
- 2026-11-04 15:16 : [6] reprise terminée, sans vol manuel ni fenêtre 3D. Betaflight : stationnaire tenu par une boucle
  Python, 18 vols sur 18 toutes séries de stationnaire confondues, plus petit pas fiable 1,25 ms (0,5 ms en build 8 kHz,
  stationnaire seulement) contre 4 ms pour PX4. Mélangeur d'origine inadapté, corrigé par CLI. Un interblocage de démarrage
  prouvé et corrigé, mais la panne d'hier n'est pas reproduite. Maintien de position firmware en échec sous essai de
  vent. Choix du firmware reporté au premier vol à la main.
- 2026-11-04 : commit e987ee4 poussé sur `initialisation` à la demande de l'utilisateur. `/usage` : 60 %. [6] Suite lancée,
  arrêt imposé à 17:00, avant la réinitialisation de 17:19.
- 2026-11-04 15:32 : arrêt propre de [6] Suite à la demande de l'utilisateur, critère non atteint. Aucun vol : le seul lancement de
  `pilot.py` a planté avant le vol. `test_entree.py` : 32 OK (logique seule, manette simulée). Icône Betaflight inchangée, sans
  pilotage. Notice non écrite. Choix de fenêtre et de vues de l'agent non validés. Scripts hors dépôt.
