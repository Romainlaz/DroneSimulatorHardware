# Cadrage initial : priorités et mode d'installation

Date : 2026-11-03
Statut : validé par l'utilisateur, y compris le périmètre (voir `ETAT.md`).

## Contexte

Le projet est un banc d'essai virtuel de drones multirotors : l'utilisateur fournit le hardware, le
système produit un vol simulé en 3D et une fiche de performances avec incertitudes.

Machine constatée le 2026-11-03 : Ubuntu 24.04, i7-7820HQ (4 cœurs / 8 threads), 31 Gio de RAM,
Quadro M1200 (4 Gio), 395 Go libres, ROS 2 Jazzy présent. Absents : Docker, Gazebo, PX4, FreeCAD,
CalculiX, OpenFOAM.

## Décision 1 : réalisme prioritaire

- Options : chiffres fiables ; comportement en vol ; structure et sécurité ; rendu visuel.
- Choix : **comportement en vol**.
- Raison : choix de l'utilisateur. Il donne la priorité à la dynamique, au réglage du pilote
  automatique, à la réponse aux commandes et à la tenue au vent.

## Décision 2 : classe de drones visée

- Options : micro (< 250 g) ; FPV 3 à 7 pouces ; moyen (450 à 800 mm) ; lourd (> 2 kg).
- Choix : **FPV 3 à 7 pouces**.
- Raison : choix de l'utilisateur. Il oriente le choix des drones de validation et des sources de
  données moteur + hélice.
- Conséquence à instruire : ces drones volent le plus souvent sous Betaflight, alors que le cahier des
  charges cite PX4 comme exemple. Le choix du firmware reste ouvert.

## Décision 3 : premier drone

- Options : drone réel et fichiers ; fichiers seuls ; drone réel sans CAO ; rien pour l'instant.
- Situation : **aucun drone ni fichier pour l'instant**.
- Conséquence : on commence par les drones de validation publiés, ce que la règle de validation du
  projet impose de toute façon.

## Décision 4 : mode d'installation

- Options : script lancé par l'utilisateur ; Docker ; sans droits administrateur.
- Choix : **installation native, par des scripts relisibles que l'utilisateur lance avec sudo**.
- Raison : les agents ne peuvent pas saisir le mot de passe sudo, et l'installation native donne le
  meilleur accès au GPU pour la 3D.
- Exigence ajoutée par l'utilisateur : chaque installation fait apparaître une icône lançable sur le
  bureau. Pour un outil sans interface, l'icône ouvre un terminal avec l'environnement chargé.

## Décision 5 : agents

- Options : copier le dossier `.claude/agents/` du kit ; agents généraux avec le rôle dans la consigne.
- Choix : **agents généraux avec le rôle dans la consigne**.
- Raison : l'utilisateur n'a pas d'agents configurés.
