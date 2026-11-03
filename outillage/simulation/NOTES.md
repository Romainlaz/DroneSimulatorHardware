# Simulation PX4 + Gazebo : notes

**État au 2026-11-03 à 18 h 30 : travail interrompu par l'arrêt du PC, fiche [1] non close.**
Toutes les mesures ont été prises sur un PC saturé (charge d'environ 9 à 19 pour 8 threads, avec
OpenFOAM et d'autres agents en parallèle). Elles ne décrivent pas les performances de la machine au
repos, et aucune mesure n'a été faite sur machine libre.

## Reprise

```bash
cd ~/Documents/DroneSimulatorHardware/outillage/simulation
uptime                                 # noter la charge ; viser une machine libre
./test_minimal.sh --delai 120          # sans attente au sol, charge faible
./test_minimal.sh --attente 45 --delai 120   # test interrompu : effet de l'attente avant armement
```

Résultat dans `~/drone-tools/logs/test_<date>/resultat.json`. Code de sortie 0 si tous les critères passent.

Reste à faire, dans l'ordre :
1. Refaire 3 vols à `--vitesse 1` sur machine libre. C'est ce qui dira si les écarts d'altitude viennent
   de la charge. Refaire aussi `--vitesse 2`, `4` et `8` pour le facteur temps réel maximal.
2. Trancher l'effet de `--attente 45` : `test_20261103_182553` a été interrompu sans `resultat.json`.
   Son `.ulg` existe mais n'a pas été analysé.
3. Exécuter `exemple_mavsdk.py` (dans un shell où `env.sh` est chargé) : **jamais lancé**.
4. Essayer `lancer_gazebo_px4.sh` et QGroundControl : **jamais lancés** (voir « Non vérifié »).

## Versions

| Élément | Version | Emplacement |
|---|---|---|
| PX4-Autopilot | v1.17.0, `d6f12ad1c4f70ad3230afd7d86e971421e02fef4` | `~/drone-tools/PX4-Autopilot` |
| Gazebo | Harmonic : `gz-harmonic` 1.0.0, Gazebo Sim 8.15.0 | apt |
| QGroundControl | v5.1.5, sha256 vérifié | `~/drone-tools/qgroundcontrol/` |
| Python | 3.12.3 ; mavsdk 4.1.0, pymavlink 2.4.50, pyulog 1.3.0, numpy 2.5.4 | `~/drone-tools/venv-px4` |

## Fichiers

- `install_sudo.sh` : dépendances système, déjà exécuté par l'utilisateur.
- `env.sh` : à sourcer. Retire ROS, `venv_stage` et les variables du snap VS Code, pour ce shell seulement.
- `creer_icones.sh` et `terminal_env.rc` : icônes du bureau, sans sudo, relançable.
- `lancer_gazebo_px4.sh` : fenêtre 3D avec rendu NVIDIA.
- `test_minimal.sh` et `test_minimal.py` : vol de contrôle sans affichage.
- `exemple_mavsdk.py` : même principe avec MAVSDK, non exécuté.

## Compilation

```bash
source env.sh && cd "$PX4_DIR" && nice -n 10 make j=6 px4_sitl_default
```

7 min 47 s (452 % CPU, 914 Mo de mémoire au maximum par processus, 521 Mo de `build/`), machine chargée.
Passer `j=6` : la détection de `-j` du Makefile de PX4 est fragile.

## Résultat du vol de contrôle

Sur les 9 vols allés au bout, tous ont décollé, tenu le stationnaire, atterri et désarmé sans affichage,
et produit un `.ulg` lisible, sans corruption, avec tous les topics requis. Mais **seuls 4 passent tous
les critères**. Les 5 échecs portent sur la précision de l'altitude ou sa stabilité.

| Run `test_20261103_` | Vitesse demandée | Facteur temps réel | Physique (Hz réels) | IMU : part d'écarts > 6 ms | Écart-type altitude (m) | Verdict |
|---|---|---|---|---|---|---|
| 181031 | 1 | 0,71 | 177,5 | non calculée (7,2 % > 8 ms) | 0,140 | OK |
| 181307 | 1 | 0,71 | 177,4 | 8,7 % | 0,239 | stabilité, altitude Gazebo |
| 181444 (nice 5) | 1 | 0,98 | 245,7 | 0,4 % | 0,083 | altitude Gazebo (2,41 m) |
| 181600 | 0,5 | 0,49 | 123,6 | 1,0 % | 0,039 | OK |
| 181758 | 2 | 0,77 | 193,4 | 10,4 % | 0,201 | stabilité |
| 181939 | 4 | 1,03 | 257,0 | 9,9 % | 0,106 | OK |
| 182055 | 8 | 0,87 | 217,5 | 10,4 % | 0,149 | OK |
| 182219 | 1 | 0,77 | 191,2 | 8,4 % | 0,079 | altitude journal (3,35 m), altitude Gazebo |
| 182427 | 1 | 0,86 | 213,8 | 5,6 % | 0,214 | stabilité, altitude Gazebo |
| 182553 (attente 45 s) | 1 | - | - | - | - | **interrompu** |

Pas simulé constant de 4,00 ms (250 Hz visés). Cible : 3 m pendant 20 s simulées. Seuils : altitude
à ±0,3 m (journal) et ±0,5 m (Gazebo), écart-type < 0,15 m. Les seuils n'ont pas été ajustés aux résultats.
Le run 181031 a tourné à nice 5. La vérité Gazebo repose sur un seul point sauf pour le run 182427 (5 points).

## Limites constatées

- **Altitude réelle éloignée de l'estimation.** Run 182427, paires (hauteur Gazebo, estimation PX4) en
  mètres : (2,84 ; 2,86), (2,20 ; 2,72), (1,72 ; 2,51), (1,69 ; 2,39), (3,15 ; 3,02). L'erreur atteint
  0,8 m et l'altitude réelle s'écarte de 1,3 m de la cible. Ces valeurs ne sont pas exploitables pour
  juger un comportement en vol tant que la cause n'est pas établie.
- **Trous dans le flux IMU.** Jusqu'à 68 ms en temps simulé, avec l'erreur `Accel #0 fail: TIMEOUT!`.
  Les deux vols où ces trous sont rares (181444 et 181600) ont aussi les écarts-types les plus faibles
  après 182219. **Hypothèse non démontrée :** la charge CPU en est la cause. Gazebo ne semble pas attendre
  PX4. Autre piste non testée : l'armement dès que PX4 l'autorise, avant convergence de l'estimateur.
- **Le facteur de vitesse n'est pas tenu sur machine chargée** : 8 demandé, 0,87 obtenu. Le maximum réel
  reste inconnu. Le run à 0,98 sous nice 5 montre que la charge des autres processus pèse plus que le nice.
- **Consommation :** 1,6 à 1,7 cœur pour PX4 + Gazebo à vitesse 1. 23 s de démarrage jusqu'à MAVLink.
  Journal de 11 à 25 Mo par vol.
- **Détachement :** `gz sim` quitte son parent. Pour arrêter à la main, viser le groupe de processus de
  `px4` (`kill -- -<pgid>`) : tuer le script Python seul laisse PX4 et Gazebo tourner.
- `px4-rc.gzsim` s'attache à tout monde Gazebo déjà visible. D'où `GZ_PARTITION` unique et `GZ_IP=127.0.0.1`
  à chaque lancement, indispensables avec plusieurs simulations en parallèle.

## Pilotage par un agent

Sans affichage, depuis un shell où `env.sh` est chargé :

```bash
cd "$PX4_BUILD_DIR/rootfs"
HEADLESS=1 PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=gz_x500 PX4_GZ_WORLD=default \
  GZ_IP=127.0.0.1 GZ_PARTITION=monrun setsid ../bin/px4 -d
```

Vérifié pendant les vols :
- **Console PX4**, depuis `rootfs` : `../bin/px4-commander check`, `../bin/px4-listener <topic>`, `../bin/px4-ekf2 status`.
- **pymavlink**, `udpin:127.0.0.1:14540` : armement, `MAV_CMD_NAV_TAKEOFF`, `MAV_CMD_NAV_LAND`, `MIS_TAKEOFF_ALT`.
  **Il faut envoyer un heartbeat `MAV_TYPE_GCS` à 1 Hz**, sinon l'armement est refusé (`No connection to the GCS`).
- **Gazebo**, avec la même partition : `gz model -m x500_0 -p` (vérité terrain, environ 1 s par appel),
  `gz topic -e -t /world/default/stats` (temps simulé, temps réel, itérations). À lancer une fois le
  monde démarré, sinon `gz topic -e` s'arrête aussitôt.
- **pyulog** : lecture et contrôle du `.ulg`, dans `rootfs/log/<date>/`. Copie dans le dossier du run.

Non vérifié : **MAVSDK** (`udpin://0.0.0.0:14540`, script écrit mais jamais lancé).

## Non vérifié

- **Fenêtre 3D Gazebo et rendu NVIDIA :** jamais ouverts. Seul l'utilisateur peut confirmer la fenêtre.
- **Icônes :** fichiers valides (`desktop-file-validate`), exécutables, `metadata::trusted` à `true`.
  Le double-clic n'a pas été essayé.
- **QGroundControl :** AppImage téléchargée et somme vérifiée, jamais lancée. Connexion à PX4 non testée.
- **`lancer_gazebo_px4.sh` :** syntaxe seule, y compris son arrêt à la fermeture du terminal.

## Betaflight : ce qui resservira

Le firmware n'est pas tranché (Betaflight recommandé, PX4 en repli).

**Resservira :** Gazebo Harmonic et son dépôt apt ; le nettoyage de `env.sh` (ROS, snap, venv) ;
`GZ_PARTITION` et `GZ_IP` ; la mesure par `/world/<monde>/stats` et la vérité par `gz model` (`StatsGazebo` et
`altitude_gazebo` de `test_minimal.py`) ; le modèle d'icônes. Le test du flux capteurs est à refaire
côté Betaflight : on ignore si les trous IMU viennent de la charge, de Gazebo ou du pont PX4.

**Propre à PX4 :** les sources et la compilation, `gz_bridge`, `px4-rc.gzsim`, `PX4_SIM_SPEED_FACTOR`, le modèle
`x500` et ses paramètres (reste à voir ce qui se réutilise de son SDF), les modes de vol et commandes
MAVLink du test, le format `.ulg` et pyulog, MAVSDK. La compatibilité de QGroundControl avec Betaflight
n'a pas été étudiée.
