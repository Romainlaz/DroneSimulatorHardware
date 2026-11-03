# État du projet

_Tenu à jour par le chef. Dernière mise à jour : 2026-11-03_

## Objectif

Banc d'essai virtuel de drones multirotors : à partir du seul hardware (assemblage 3D, matériaux,
références des composants), obtenir automatiquement un vol simulé en 3D avec un vrai firmware et une
fiche de performances indiquant l'origine de chaque valeur. Priorité : comportement en vol. Classe visée : FPV 3 à 7 pouces.
But : tester du nouveau hardware et prédire les performances de drones que personne n'a mesurés, donc
le plus souvent hors du domaine validé.

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

_Tous les agents arrêtés proprement à la demande de l'utilisateur, le 2026-11-03 vers 18:29._

## File prête (validée, en attente d'une place libre)

_À reprendre sur PC peu chargé, une à la fois, pour des mesures de temps fiables :_

- [1] Reprise : cause de l'erreur d'altitude (4 vols sur 9 réussis), puis vitesses et MAVSDK. Commandes dans
  `outillage/simulation/NOTES.md`
- [6] Reprise : balayage des pas, vent, échelon de roulis. Commandes dans
  `~/drone-tools/betaflight-proto/ETAT_REPRISE.md`
- [2] Reprise : niveau 6, banc motorBike, ParaView. Commandes dans `outillage/cfd/NOTES.md`

## Bloqué (en attente d'une entrée non figée)

| Tâche | Attend |
|---|---|
| Contrats d'interface, dont le format de la fiche hardware | Fiches [1] à [5], choix du firmware |
| Chaîne minimale de bout en bout | Contrats d'interface |

## File de décisions pour l'utilisateur

_Ce que tu peux trancher ou relire pendant que les agents travaillent._

- Double-cliquer sur les icônes (FreeCAD, Gmsh, CalculiX, Gazebo + PX4, QGroundControl, terminal PX4, OpenFOAM,
  ParaView) une fois le PC au repos, et confirmer que les fenêtres s'ouvrent
- Choix du firmware, après les reprises de [1] et [6] (recommandation de [4] : Betaflight, PX4 en repli,
  firmware isolé derrière une interface)
- Autoriser la reprise de [1], [6] et [2] avec un `/usage` à jour, et fusionner ou non la branche
  `initialisation` dans `main`

### Périmètre (validé par « go pour tout » le 2026-11-03)

- Inclus : multirotors, logiciels gratuits ou open source, sur ce PC
- Exclu : voilures fixes et VTOL, essais sur hardware réel, optimisation automatique des designs
- CFD : en option, pour les configurations finalistes seulement

## Consommation de la session

- Dernière mesure : 72 % de la session, 13 % de la semaine (`/usage`, 2026-11-03) ; mesure précédente : 55 % et 11 %
- Seuil atteint : 50 à 80 %, seuil de 80 % proche : aucune nouvelle tâche avant la réinitialisation
- Réinitialisation : session à 18:40 ; semaine le dimanche 8 novembre à 20:00

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
