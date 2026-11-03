# Notes OpenFOAM (fiche [2])

**État au 2026-11-03 : travail partiel, arrêté à la demande de l'utilisateur (extinction du PC).**
Le cas de la sphère a abouti aux niveaux de maillage 4 et 5. Le niveau 6 et le banc motorBike ont été
interrompus. La fenêtre ParaView n'a pas été vérifiée.

## Reprise

Depuis `outillage/cfd/`, à lancer à tour de rôle, quand le PC est peu chargé si possible :

```bash
cas_test_sphere/lancer.sh 6 4     # niveau 6 : convergence en maillage, jamais terminé
./banc_motorbike.sh               # banc RANS sur géométrie complexe, jamais lancé jusqu'au bout
./paraview_lance.sh ~/drone-tools/cfd/runs/sphere_Re100_L5/cas.foam   # ouvre une fenêtre à l'écran
```

Reste à faire :

- [ ] Niveau 6, pour juger la convergence en maillage.
- [ ] Banc motorBike, puis remplacer la projection ci-dessous par des mesures.
- [ ] Refaire les mesures de temps sur un PC au repos.
- [ ] Faire confirmer par l'utilisateur la fenêtre ParaView et le double-clic sur les deux icônes.
- [ ] Tester `pyFoamRunner.py` sur un cas réel.
- [ ] Supprimer `~/drone-tools/cfd/runs/sphere_Re100_L6/`, qui est incomplet (`lancer.sh 6 4` le recrée).

## Résultat : sphère à Re = 100

Cas laminaire stationnaire (`simpleFoam`), du STL au Cd, sur 4 processus sous `nice -n 15`.

| Niveau | Cellule à la paroi | Cellules | Itérations | Cd | Écart à 1,09 | Écart à Schiller-Naumann |
| --- | --- | --- | --- | --- | --- | --- |
| 4 | D/16 | 23 814 | 123 | 1,09424 | +0,39 % | +0,23 % |
| 5 | D/32 | 122 531 | 129 | 1,09281 | +0,26 % | +0,10 % |
| 6 | D/64 | non terminé | | | | |

Par rapport à Johnson et Patel (1,08), le niveau 5 donne +1,19 %.

`checkMesh` répond `Mesh OK` aux niveaux 4 et 5.

Réserves sur ce résultat :

- **Convergence en maillage non démontrée.** Les niveaux 4 et 5 diffèrent de 0,13 %, mais il n'y a que
  deux points, et une compensation d'erreurs reste possible.
- **Valeur de référence de seconde main.** L'article de Johnson et Patel est payant et je ne l'ai pas
  lu. Les valeurs 1,09 (Mittal) et 1,08 (Johnson et Patel) viennent du tableau de validation de Notus.
- **Sensibilité au domaine non étudiée** (domaine de 28 D x 16 D x 16 D, parois latérales en glissement).
- **`Cd_moyen_100_dernieres` et `amplitude_100_dernieres` ne prouvent pas la convergence** sur ces
  calculs courts : leur fenêtre contient encore le transitoire de démarrage. Un calcul antérieur au
  niveau 5, poursuivi jusqu'à l'itération 805, donnait Cd = 1,09281232, stable sur plusieurs
  centaines d'itérations. Son journal a été écrasé par le calcul suivant.
- Ce cas ne valide que la chaîne d'outils. Il ne dit rien de la précision sur un drone, où
  l'écoulement est turbulent et la géométrie complexe.

Références :

- Schiller et Naumann (1933), corrélation : Cd = 24/Re (1 + 0,15 Re^0,687), soit 1,0917 à Re = 100.
- Johnson T.A., Patel V.C., *Flow past a sphere up to a Reynolds number of 300*, J. Fluid Mech. 378,
  19-70, 1999, DOI 10.1017/S0022112098003206 (régime stationnaire axisymétrique jusqu'à Re = 200).
- Tableau de validation : <https://doc.notus-cfd.org/d1/d68/group__doc__validation__spehre__3d.html>
- Corrélation évaluée à Re = 100 : <https://mfix.netl.doe.gov/doc/mfix-exa/guide/latest/tutorials/fluid/steady-flow-around-sphere.html>

## Temps mesurés, sur un PC saturé

**Ces temps sont pessimistes et peu reproductibles.** D'autres agents compilaient et simulaient en même
temps, et le calcul tournait sous `nice`. La charge a atteint environ 15 pour 8 threads selon le
coordinateur ; j'ai mesuré jusqu'à 18,5 sur la dernière étape du niveau 5.

| Niveau | snappyHexMesh | simpleFoam | Temps par itération | Charge moyenne | Mémoire max |
| --- | --- | --- | --- | --- | --- |
| 4 | 16,3 s | 15,2 s | 0,12 s | 10,0 | 362 Mo |
| 5 | 54,5 s | 106,1 s | 0,82 s | 12,6 | 555 Mo |

**La contention fausse nettement les mesures.** Le même niveau 4 a pris à charge 4,7 : snappyHexMesh
4,6 s, simpleFoam 5,7 s pour 156 itérations, soit 0,037 s par itération. C'est environ 3,3 fois plus
rapide par itération, et 3,5 fois pour le maillage. La mémoire additionne la RSS des processus et compte
donc plusieurs fois les bibliothèques partagées.

## Projection pour un drone complet : estimation, pas une mesure

Je n'ai mesuré aucun cas turbulent ni aucune géométrie complexe : le banc motorBike devait servir à cela
et n'a pas abouti. Les hypothèses ci-dessous sont des ordres de grandeur.

| Grandeur | Valeur retenue | Origine |
| --- | --- | --- |
| Maillage | 5 millions de cellules | hypothèse, un drone FPV détaillé peut demander davantage |
| Coût par cellule et par itération | 1,5 à 6,7 µs | mesuré sur la sphère, PC calme à saturé |
| Surcoût RANS | x 1,5 | hypothèse |
| Itérations | 1 500 | hypothèse |
| Mémoire | environ 10 Go | extrapolé de 2 Mo pour 1 000 cellules, sur deux points seulement |

Soit **environ 5 à 20 heures de solveur pour un seul point de vol** (une vitesse, une attitude), hélices
absentes, plus le maillage, non estimé de façon fiable. Plusieurs erreurs possibles vont dans le sens du
pire : snappyHexMesh n'est pas linéaire en nombre de cellules et une géométrie de drone peut exiger des
reprises manuelles. La mémoire de 31 Gio semble suffire jusqu'à environ 10 millions de cellules, sans
garantie pour le pic de snappyHexMesh.

Conséquence : sur ce PC, la CFD reste réservée à quelques points sur des configurations finalistes, ce
qui est cohérent avec son rôle d'option. Un balayage complet n'est pas réaliste. Les hélices en rotation
(MRF, AMI ou overset) coûteraient davantage et n'ont pas été testées.

## Commandes pilotables par un agent

Passer par `of.sh`, qui part d'un environnement vierge et applique `nice` :

```bash
./of.sh simpleFoam -help
./of.sh foamDictionary -entry endTime -value <cas>/system/controlDict
./of.sh foamDictionary -entry endTime -set 777 <cas>/system/controlDict
./of.sh mpirun -np 4 --bind-to none simpleFoam -parallel -case <cas>
cas_test_sphere/lancer.sh <niveau> <np>
```

Chaque cas produit `log.<étape>`, `temps.tsv`, `charge.tsv` et `resultat.json`, et `lancer.sh` rend un code
non nul si une étape échoue. L'historique de Cd est dans
`postProcessing/forceCoeffs/0/coefficient.dat`. Pour réutiliser le cas, changer le STL, `Aref`, `lRef`,
`magUInf`, `nu` et les zones de raffinement.

PyFoam 2026.6 est installé depuis PyPI dans `~/drone-tools/cfd/pyfoam/`, hors de `venv_stage`. Vérifié sur
une copie de cas : `pyFoamVersion.py` tourne, et `ParsedParameterFile` détecte v2512, lit et réécrit un
`controlDict`. `pyFoamRunner.py` n'a pas été essayé. `foamDictionary` suffit pour les modifications
simples.

`overPimpleDyMFoam` (overset) est présent dans v2512 ; seule sa présence a été vérifiée.

## Fichiers

| Fichier | Rôle |
| --- | --- |
| `install_sudo.sh` | Installation avec root, déjà exécutée par l'utilisateur. |
| `env_openfoam.sh` | Environnement à sourcer, isolé de ROS et de `venv_stage`. |
| `of.sh` | Lance une commande en environnement vierge, sous `nice`. |
| `terminal_openfoam.rc` | Démarrage du terminal ouvert par l'icône. |
| `paraview_lance.sh` | Lance ParaView, sur la carte NVIDIA si elle répond. |
| `creer_icones.sh` | Crée les icônes du bureau, sans sudo. |
| `cas_test_sphere/` | Modèle de cas, `lancer.sh`, STL et analyse. |
| `banc_motorbike.sh` | Banc RANS, **jamais mené à son terme**. |

## Choix de la version : openfoam.com v2512 (2512.0-2)

Index apt officiels pour Ubuntu 24.04, consultés le 2026-11-03 :

| Source | Version | Décision |
| --- | --- | --- |
| Ubuntu universe | `openfoam` 1912.200626 | Écartée : base de 2019. |
| openfoam.com, stable | `openfoam2512` 2512.0-2 | **Retenue.** |
| openfoam.com, récente | `openfoam2606` 2606.0~rc2-1 | Écartée : pré-version dans le dépôt (index du 22 juin 2026). |
| openfoam.org | `openfoam14` 20261008 | Viable et plus récente, installation non simulée ici. |

v2512 garde les solveurs classiques (`simpleFoam`, etc.), plus simples à piloter ; openfoam.org 14 passe
par `foamRun`. C'est un jugement, à réviser si un besoin propre à openfoam.org apparaît.

Sources : [index openfoam.com](https://dl.openfoam.com/repos/deb/dists/noble/main/binary-amd64/Packages.gz),
[script du dépôt](https://dl.openfoam.com/add-debian-repo.sh),
[annonce v2606](https://www.openfoam.com/news/main-news/openfoam-v2606),
[index openfoam.org](https://dl.openfoam.org/ubuntu/dists/noble/main/binary-amd64/Packages),
[installation openfoam.org](https://openfoam.org/download/14-ubuntu/).

## Pièges et limites constatés

- **Ne pas installer `python3-paraview`.** Il déclare `Conflicts: python3-vtk9` : en simulation, apt
  retire alors `ros-jazzy-desktop` et 5 autres paquets. Le module Python `paraview` reste donc absent du
  python système ; le post-traitement scripté avec `pvpython` ou `pvbatch` n'est pas disponible en l'état.
- **Terminal VS Code en snap.** Il transmet `GIO_MODULE_DIR` et d'autres variables. Conséquences :
  `gio set` répond `metadata::trusted not supported` et ParaView échoue sur une bibliothèque de
  `/snap/core20`. `creer_icones.sh` et `paraview_lance.sh` s'en protègent.
- **`bashrc` d'OpenFOAM.** Il lit les arguments du shell appelant comme des options : le charger avec
  un argument vide (`. bashrc ''`), comme le fait `env_openfoam.sh`.
- **Seuil de résidu.** Uy et Uz plafonnent vers 1,6e-6 au niveau 5 alors que Cd ne bouge plus. Avec un
  seuil U de 1e-6, le calcul ne s'arrêtait pas ; le seuil est passé à 1e-5.
- **`QT_QPA_PLATFORM=offscreen` ne permet pas de tester ParaView ici :** sans écran, il échoue sur le
  greffon `xcb`. Xvfb n'est pas installé.
- **`openfoam-selector`** pose un script dans `/etc/profile.d` : écarté par `--no-install-recommends`.
- **`~/.bashrc` charge ROS et `venv_stage`** (lignes 118-119) : ne pas lancer OpenFOAM depuis un shell
  ordinaire sans `of.sh` ou `env_openfoam.sh`.

## Vérifié et non vérifié

Vérifié :

- Chaîne complète scriptée (STL, blockMesh, snappyHexMesh, checkMesh, simpleFoam, Cd) aux niveaux 4 et 5.
- `env_openfoam.sh` dans un shell ayant chargé ROS et `venv_stage` : plus aucune entrée de ces deux
  environnements dans `PATH` et `LD_LIBRARY_PATH`, et `~/.bashrc` sans mention d'OpenFOAM.
- Icônes : présentes, exécutables, validées par `desktop-file-validate`, `metadata::trusted` à `true`.
- Démarrage du terminal simulé sans fenêtre, avec le même `--rcfile` que l'icône.

Non vérifié :

- **Fenêtre ParaView** : jamais ouverte, seul `pvbatch --version` a répondu (5.11.2). L'absence du module
  Python pourrait avoir un effet au démarrage.
- **Double-clic sur les icônes** sous GNOME, et fenêtre réelle du terminal.
- Lecture du fichier `cas.foam` dans ParaView.
- Niveau 6, banc motorBike, temps sur PC au repos, cas turbulent, hélices.
