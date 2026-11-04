# Simulation PX4 + Gazebo : notes

**État au 2026-11-04 à 12 h 55 : mesures sur machine libre faites, critère des 5 vols atteint.**
À vitesse 1, tous les vols allés au bout passent tous les critères, seuils inchangés. Restent les essais qui
demandent l'utilisateur (voir Reprise). La cause des écarts du 3 novembre reste une hypothèse, non prouvée.

## Reprise

Reste à faire :
1. **Utilisateur :** double-cliquer l'icône de `lancer_gazebo_px4.sh`, vérifier la fenêtre 3D et l'arrêt à la
   fermeture du terminal, puis lancer `$QGC_APPIMAGE` : il doit se connecter seul en UDP 14550. Jamais lancés.
2. **Décision de l'utilisateur :** essai de charge provoquée. C'est le seul moyen de prouver le rôle de la
   charge et de voir si `--attente 45` protège sous charge. Non fait.

Pour refaire les mesures :

```bash
cd ~/Documents/DroneSimulatorHardware/outillage/simulation
uptime                                       # machine libre obligatoire pour une mesure exploitable
./test_minimal.sh --delai 150                # options : --vitesse N, --attente S, --points N
~/drone-tools/venv-px4/bin/python3 diagnostic_vols.py 'test_20261104_*'   # à lancer entre les vols
source env.sh && python3 exemple_mavsdk.py   # voie MAVSDK
```

Résultat dans `~/drone-tools/logs/test_<date>/resultat.json`. Code de sortie 0 si tous les critères passent.
Charge notée avant et après chaque vol dans `~/drone-tools/logs/serie_*.log`.

## Mesures sur machine libre (2026-11-04)

Sans affichage, 5 lectures `gz model` par vol. Valeurs du palier. La charge (moyenne sur 1 min) inclut la
simulation elle-même et le vol précédent. Tous ces vols : code 0, aucun critère en échec, aucun `TIMEOUT`.

| Run `test_20261104_` | Vitesse / attente | Charge avant → après | Facteur temps réel palier | Facteur vol complet | Cœurs | IMU > 6 ms | Écart IMU max (ms) | Écart-type estimé (m) | Hauteur `gz model` (m) | Hauteur vérité `.ulg` (m) | Erreur d'estimation max (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 122947 | 1 / 0 | 1,11 → 3,35 | 0,978 | 0,989 | 1,78 | 0,01 % | 12 | 0,009 | 2,993 | 2,992 | 0,057 |
| 123115 | 1 / 0 | 2,52 → 3,31 | 0,978 | 0,989 | 1,80 | 0 % | 4 | 0,011 | 3,014 | 3,018 | 0,038 |
| 123242 | 1 / 0 | 2,57 → 2,87 | 0,978 | 0,988 | 1,61 | 0,08 % | 20 | 0,010 | 3,019 | 3,015 | 0,042 |
| 123702 | 1 / 0 | 0,42 → 1,13 | 0,978 | 0,989 | 1,80 | 0,01 % | 8 | 0,008 | 3,006 | 3,010 | 0,044 |
| 123829 | 1 / 0 | 0,87 → 1,26 | 0,978 | 0,989 | 1,79 | 0,01 % | 8 | 0,009 | 3,012 | 3,009 | 0,033 |
| 123956 | 1 / 45 | 0,97 → 3,30 | 0,978 | 0,988 | 1,77 | 0 % | 8 | 0,007 | 2,990 | 2,990 | 0,040 |
| 124207 | 1 / 45 | 2,52 → 2,67 | 0,978 | 0,988 | 1,79 | 0 % | 4 | 0,012 | 3,032 | 3,034 | 0,066 |
| 124417 | 1 / 45 | 1,91 → 1,75 | 0,978 | 0,988 | 1,78 | 0 % | 8 | 0,011 | 2,963 | 2,964 | 0,072 |
| 124628 | 2 / 0 | 1,25 → 1,29 | 1,913 | 1,952 | 2,46 | 0,02 % | 8 | 0,009 | 2,976 | 2,974 | 0,030 |
| 124735 | 2 / 0 | 0,92 → 1,37 | 1,910 | 1,951 | 2,59 | 0,02 % | 8 | 0,009 | 2,971 | 2,971 | 0,041 |
| 124841 | 4 / 0 | 0,98 → 0,96 | 3,552 | 3,778 | 2,30 | 0,02 % | 8 | 0,011 | 2,982 | 2,982 | 0,034 |
| 124939 | 4 / 0 | 1,27 → 2,01 | 3,552 | 3,775 | 2,26 | 0,03 % | 12 | 0,008 | 3,006 | 3,010 | 0,054 |
| 125036 | 8 / 0 | 1,44 → 1,85 | 5,729 | 6,011 | 3,20 | 0,26 % | 16 | 0,009 | 3,018 | 3,009 | 0,048 |
| 125133 | 8 / 0 | 1,33 → 1,64 | 5,710 | 6,049 | 3,22 | 0,31 % | 16 | 0,009 | 2,975 | 2,973 | 0,050 |

`test_20261104_123434` a été arrêté volontairement en plein stationnaire : ce n'est pas un échec de vol, il n'a
ni `resultat.json` ni `.ulg`. Il sépare les vols 123242 et 123702.

- **Critère des 5 vols consécutifs : atteint.** Les 5 vols d'affilée sans interruption (123702 à 124417) passent,
  dont 3 avec attente. Les 5 vols sans attente passent aussi, mais avec l'arrêt ci-dessus entre les deux groupes.
- **Effet de `--attente 45` : aucun visible sur machine libre**, sur 3 vols contre 5. Sous charge : non testé.
  `182553` (attente 45 s, `.ulg` seul, charge inconnue) est bon, mais attente et charge y sont confondues.
- **Facteur temps réel maximal mesuré : 5,7 en stationnaire, 6,0 sur le vol complet, à `--vitesse 8`.** Le vol
  reste bon à ce régime. Aucune vitesse au-delà de 8 essayée. L'écart entre palier et vol complet n'a pas été
  expliqué ; les lectures `gz model` du palier sont une piste, non testée.
- La vérité `.ulg` (`vehicle_local_position_groundtruth`, publiée par `gz_bridge`) concorde à moins de 1 cm avec
  la moyenne des lectures `gz model` sur chacun de ces 14 vols.

**MAVSDK : vol réussi** (`~/drone-tools/logs/mavsdk_20261104_125319/`) : connexion, PX4 1.17.0 lu, armement,
décollage, 2,47 m pour 2,5 m demandés (télémétrie PX4 seule), atterrissage, désarmement. Premier armement refusé
(« No connection to the GCS »), accepté au réessai 2 s plus tard. Le script d'origine échouait dès `System()` :
`mavsdk` 4.x est une liaison native, à l'API différente. Il a été réécrit pour cette API, sans changer de version.

**Cause des écarts d'altitude du 3 novembre : hypothèse de la charge CPU, forte mais non prouvée.**
- Fait : vols du 3 novembre avec beaucoup de trous IMU (5,6 à 10,6 % au-delà de 6 ms) : vérité très dispersée
  (écart-type 0,28 à 0,57 m). Machine libre à vitesse 1 : trous < 0,1 %, écart-type 0,051 à 0,075 m. Même fenêtre
  de calcul (`diagnostic_vols.py`), qui inclut la fin de montée.
- Fait : EKF2 ne rejette aucune mesure de hauteur, baro ou GNSS, sur le palier de tous ces vols. L'estimateur
  n'a donc pas signalé le problème par ce biais.
- Fait : `gz_bridge` n'a pas de lockstep. Il horodate l'IMU à la réception (`hrt_absolute_time()`) et Gazebo
  n'attend pas PX4 (lecture de `GZBridge.cpp`).
- Limites : la charge du 3 novembre n'a pas été mesurée vol par vol, aucun essai sous charge provoquée, mécanisme
  reliant trous et altitude non démontré. Le run 181444 reste à expliquer (voir Limites).
- **Armement précoce : écarté comme cause nécessaire**, les vols sans attente étant bons sur machine libre.

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
- `exemple_mavsdk.py` : vol court avec l'API native de MAVSDK 4.x, sans contrôle du journal.
- `diagnostic_vols.py` : pour chaque `.ulg`, trous IMU, vérité, erreur d'estimation, rejets EKF2 (motifs de dossiers en arguments).

## Compilation

```bash
source env.sh && cd "$PX4_DIR" && nice -n 10 make j=6 px4_sitl_default
```

7 min 47 s (452 % CPU, 914 Mo de mémoire au maximum par processus, 521 Mo de `build/`), machine chargée.
Passer `j=6` : la détection de `-j` du Makefile de PX4 est fragile.

## Résultat du vol de contrôle sur PC saturé (2026-11-03)

Charge d'environ 9 à 19 pour 8 threads, avec OpenFOAM et d'autres agents : ces vols ne décrivent pas la
machine au repos. Sur les 9 vols allés au bout, tous ont décollé, tenu le stationnaire, atterri et désarmé sans affichage,
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
| 182553 (attente 45 s) | 1 | - | - | 0,04 % | 0,054 (`.ulg`) | **interrompu**, sans `resultat.json` |

Pas simulé constant de 4,00 ms (250 Hz visés). Cible : 3 m pendant 20 s simulées. Seuils : altitude
à ±0,3 m (journal) et ±0,5 m (Gazebo), écart-type < 0,15 m. Les seuils n'ont pas été ajustés aux résultats.
Le run 181031 a tourné à nice 5. La vérité Gazebo repose sur un seul point sauf pour le run 182427 (5 points).

## Limites constatées

- **PC saturé : altitude réelle éloignée de l'estimation.** Run 182427, paires (hauteur Gazebo, estimation
  PX4) en mètres : (2,84 ; 2,86), (2,20 ; 2,72), (1,72 ; 2,51), (1,69 ; 2,39), (3,15 ; 3,02). L'erreur
  atteint 0,8 m et l'altitude réelle s'écarte de 1,3 m de la cible. Absent des 3 vols sur machine libre.
  **Conséquence : un vol sur machine chargée n'est pas exploitable pour juger un comportement en vol.**
- **PC saturé : trous dans le flux IMU.** Jusqu'à 68 ms en temps simulé, avec l'erreur `Accel #0 fail: TIMEOUT!`.
  Le run 181444 reste à expliquer : 0,37 % de trous seulement, mais 4 trous > 20 ms (max 52 ms) et une hauteur
  vérité descendue à 2,39 m. Le lien entre ces trous et ses excursions n'a pas été vérifié.
- **Machine libre : facteur 0,978 en stationnaire à `--vitesse 1`** (244,4 Hz au lieu de 250). Cause non cherchée.
- **Le facteur de vitesse n'est pas tenu sur machine chargée** : 8 demandé, 0,87 obtenu. Maximum sur machine
  libre : voir ci-dessus. Le run à 0,98 sous nice 5 montre que la charge des autres processus pèse plus que le nice.
- **Consommation sur machine libre :** 1,6 à 1,8 cœur à vitesse 1, 3,2 cœurs à vitesse 8. 11 à 12 s de démarrage
  jusqu'à MAVLink (23 s sur PC saturé). Journal de 11 à 25 Mo par vol sur PC saturé.
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
- **MAVSDK 4.x**, `udpin://0.0.0.0:14540` : `Mavsdk` -> `first_autopilot` -> plugins `Action`, `Telemetry`, `Info`.

## Non vérifié

- **Fenêtre 3D Gazebo et rendu NVIDIA :** jamais ouverts. Seul l'utilisateur peut confirmer la fenêtre.
- **Icônes :** fichiers valides (`desktop-file-validate`), exécutables, `metadata::trusted` à `true`.
  Le double-clic n'a pas été essayé.
- **QGroundControl :** AppImage téléchargée et somme vérifiée, jamais lancée. Connexion à PX4 non testée.
- **MAVSDK :** journal et vérité Gazebo non contrôlés pour ce vol (télémétrie PX4 seule), un seul vol.
- **Vol sous charge provoquée** et option `--points 0` : jamais exécutés.
- **`lancer_gazebo_px4.sh` :** syntaxe seule, y compris son arrêt à la fermeture du terminal.

## Betaflight : ce qui resservira

Le firmware n'est pas tranché (Betaflight recommandé, PX4 en repli).

**Resservira :** Gazebo Harmonic et son dépôt apt ; le nettoyage de `env.sh` (ROS, snap, venv) ;
`GZ_PARTITION` et `GZ_IP` ; la mesure par `/world/<monde>/stats` et la vérité par `gz model` (`StatsGazebo` et
`altitude_gazebo` de `test_minimal.py`) ; le modèle d'icônes. Le test du flux capteurs est à refaire
côté Betaflight : le rôle de la charge n'est pas prouvé. Tout autopilote couplé à Gazebo sans attente mutuelle
serait exposé de la même façon (déduction, rien n'a été testé avec Betaflight).

**Propre à PX4 :** les sources et la compilation, `gz_bridge`, `px4-rc.gzsim`, `PX4_SIM_SPEED_FACTOR`, le modèle
`x500` et ses paramètres (reste à voir ce qui se réutilise de son SDF), l'absence de lockstep de `gz_bridge`, les modes de vol et commandes
MAVLink du test, le format `.ulg` et pyulog, MAVSDK. La compatibilité de QGroundControl avec Betaflight
n'a pas été étudiée.
