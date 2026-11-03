# Outils de géométrie et de résistance : FreeCAD, Gmsh, CalculiX

État constaté le 2026-11-03, sur Ubuntu 24.04. Aucun droit root n'a été nécessaire, donc il n'y a
pas de `install_sudo.sh`.

## Démarrer

```bash
./installer_espace_utilisateur.sh   # idempotent, écrit dans ~/drone-tools
./creer_icones.sh                   # idempotent, écrit sur le bureau
source outillage/geometrie/env.sh   # à sourcer dans chaque shell
./lancer_tests.sh                   # journal : ~/drone-tools/resultats/journal_tests.txt
```

`env.sh` ajoute seulement `~/drone-tools/bin` au `PATH`. `ros2` et `rclpy` ont été vérifiés après
l'avoir sourcé. `~/.bashrc` et `~/venv_stage` n'ont pas été modifiés.

## Versions installées

| Outil | Version | Source | Commande |
|---|---|---|---|
| FreeCAD | 1.1.4, révision 20260928 | AppImage officielle extraite | `freecad`, `freecadcmd` |
| Python de FreeCAD | 3.11.14, numpy 1.26.4 | inclus dans l'AppImage | `drone-freecad-python` |
| OCCT de FreeCAD | 7.8.1 | inclus dans l'AppImage | |
| Gmsh | 4.15.2, OCCT 8.0.1, FLTK 1.3.10 | conda-forge, environnement `cae` | `gmsh` |
| CalculiX | 2.23 | conda-forge, environnement `cae` | `ccx` |
| Python de `cae` | 3.12, numpy 2.5.4, gmsh 4.15.2 | conda-forge | `drone-cae-python` |
| micromamba | 2.10.0 | GitHub, SHA-256 vérifié | `micromamba` |

L'AppImage contient aussi `ccx` 2.23 et `gmsh` 4.15.0. L'atelier FEM de FreeCAD utilise ces copies,
et les commandes `gmsh` et `ccx` utilisent l'environnement `cae`. Il existe donc deux versions de Gmsh.

Espace occupé : 6,5 Go dans `~/drone-tools`, dont 820 Mo pour l'AppImage conservée.

## Choix de la source de FreeCAD

Critère : `freecadcmd` et le module Python fonctionnent sans `DISPLAY`, avec Part, Mesh et FEM, et
FEM sait créer un maillage. Script : `tests/verifier_freecad.py`.

| Source | Version | Critère | Remarques |
|---|---|---|---|
| **AppImage officielle (retenue)** | 1.1.4 | **Réussi** (commande et Python) | SHA-256 publié et vérifié. Inclut `ccx` et `gmsh`. Sans root. |
| conda-forge | 1.1.3 | Réussi (commande et Python) | Pas de `ccx`. Python 3.14. Somme contrôlée par micromamba, pas par FreeCAD. 4,2 Go. Environnement supprimé après l'essai. |
| Snap | 1.1 (rév. 2904) | **Non testé** | `snap install` demande root. Annonce `freecad.cmd`. |
| PPA `freecad-stable` | 0.21.2 | **Non testé** | Demande root, et version trop ancienne pour ce projet. |

Raison du choix : 1.1.4 corrige deux failles à l'ouverture de fichiers FCStd, d'après ses notes de
version, et 1.1.3 les contient. Le projet ouvrira des fichiers venus de tiers. L'AppImage non extraite
démarre aussi ici, car `libfuse2t64` est déjà installé. L'extraction supprime cette dépendance.

Apt proposait Gmsh 4.12 et CalculiX 2.21 avec root. conda-forge donne 4.15.2 et 2.23 sans root.

## Piloter chaque outil

**FreeCAD.** `drone-freecad-python script.py` donne accès à `FreeCAD`, `Part`, `Import`, `Mesh`,
`MeshPart`, `Fem`, `ObjectsFem`, `femtools.ccxtools`.

- Ce module n'est pas importable depuis le Python du système ni depuis ROS, car ils sont en 3.12 et
  lui en 3.11. Il faut un sous-processus qui échange du JSON avec le reste du projet.
- Importer `FreeCAD` avant `ObjectsFem`, sinon le module est introuvable.
- Terminer par `sys.stdout.flush(); os._exit(code)` : sous `freecadcmd`, la console reste sinon ouverte.
- Après `FreeCADGui.showMainWindow()`, `print` part dans la vue rapport. Utiliser `os.write(1, ...)`.
- Après `ccx_run()` et `load_results()`, le résultat se trouve dans `analyse.Group`
  (type `Fem::FemResultObject`). Exemple complet : `tests/test_fem_freecad.py`.

**Gmsh.** `drone-cae-python` avec `import gmsh`. L'API donne aussi masse, centre et inertie d'un
volume : `gmsh.model.occ.getMass`, `getCenterOfMass`, `getMatrixOfInertia`. Pour le C3D10, CalculiX
attend les nœuds 9 et 10 permutés par rapport à Gmsh. `tests/test_poutre_calculix.py` fait cette
permutation et la contrôle sur la géométrie.

**CalculiX.** Pas d'API : on écrit `nom.inp`, on lance `ccx -i nom` (sans l'extension), on lit
`nom.frd` en colonnes fixes. Le fichier `.log` de chaque cas confirme « Using up to 4 cpu(s) » avec
`OMP_NUM_THREADS=4`, valeur par défaut des lanceurs. CalculiX peut sortir sans code d'erreur : chercher
aussi `*ERROR` dans sa sortie.

## API Python et serveurs MCP

Conclusion : **l'API Python et les fichiers suffisent, aucun MCP n'a été installé.** Les tests
pilotent les trois outils de bout en bout sans MCP. Un serveur MCP ajouterait du code tiers capable
d'exécuter des actions sur ce poste.

Dépôts trouvés par recherche GitHub le 2026-11-03. **Aucun n'a été installé ni testé**, et les
descriptions sont celles des auteurs.

| Dépôt | Étoiles | Intérêt possible |
|---|---|---|
| `neka-nat/freecad-mcp` | 3198 | Le plus suivi. Vérifier s'il exige une interface ouverte avant tout usage. |
| `spkane/freecad-addon-robust-mcp-server` | 265 | Serveur et atelier passerelle, actif. |
| `bonninr/freecad_mcp` | 227 | Dernière activité en mars 2025. |
| `contextform/freecad-mcp` | 139 | Dernière activité en août 2025. |
| `ymiya55/freecad-fem-mcp` | 0 | Vise exactement FreeCAD 1.1 + Gmsh + CalculiX, mais très récent. |
| `superWorldSavior/mcp-calculix` | 0 | Gmsh + CalculiX sur fichiers STEP, très récent. |
| `OFFTECH/gmsh-mcp-server` | 0 | Orienté maillage OpenFOAM. |

## Résultats des tests

Journal complet : `~/drone-tools/resultats/journal_tests.txt`. Les seuils ont été fixés par l'auteur
des tests : 1e-6 en relatif pour la géométrie, 2 % pour la résistance.

### Géométrie : assemblage STEP de 5 pièces et 4 densités

Sous-assemblage imbriqué, pièces tournées, tube creux. Le STEP est relu dans un document vierge.
Le calcul analytique n'appelle aucune fonction de FreeCAD.

| Grandeur | Mesuré | Théorie | Écart relatif FreeCAD | Écart relatif Gmsh |
|---|---|---|---|---|
| Masse | 283,8461401 g | 283,8461401 g | 1,96e-16 | 1,96e-16 |
| Centre de gravité | (0,73928 ; 9,59456 ; 18,30649) mm | identique | 5,03e-16 | 1,94e-16 |
| Inertie au CG | Ixx 1083,60 ; Iyy 1724,26 ; Izz 2740,44 ; Ixy -1266,43 kg.mm² | identique | 2,66e-15 | 2,57e-15 |

Position des moteurs exacte, axe du moteur incliné retrouvé à moins de 1e-6 degré.

Ces écarts sont la précision machine, car les formes sont des primitives exactes. Ils prouvent que la
chaîne de composition est juste, pas que de vrais fichiers de CAO se liront aussi bien. Gmsh et FreeCAD
reposent tous deux sur OCCT : ce sont deux lecteurs, pas deux méthodes indépendantes.

### Résistance : poutre console 200 x 20 x 10 mm, aluminium, 50 N en bout

Théorie : flèche 1,14286 mm (1,14514 mm avec le cisaillement), contrainte 30 MPa à l'encastrement,
15 MPa à mi-longueur.

| Cas | Nœuds | Flèche (mm) | Écart flèche | SXX max brut (MPa) | Écart brut | SXX extrapolé (MPa) | Écart extrapolé |
|---|---|---:|---:|---:|---:|---:|---:|
| C3D4, h=5 | 680 | 0,684 | **-40,1 %** | 21,7 | -27,6 % | 13,96 | -53,5 % |
| C3D10, h=10 | 955 | 1,1308 | -1,06 % | 33,6 | +11,8 % | 30,03 | +0,10 % |
| C3D10, h=5 | 3 949 | 1,1338 | -0,79 % | 34,2 | +13,9 % | 30,00 | -0,01 % |
| C3D10, h=2,5 | 22 074 | 1,1352 | -0,67 % | 37,2 | **+24,1 %** | 30,00 | 0,00 % |
| FreeCAD FEM + ccx, h=5 | 3631 | 1,1337 | -0,80 % | 33,4 | +11,3 % | non calculé | SXX à L/2 : -0,17 % |

À lire avant d'utiliser ces chiffres :

- **La contrainte maximale brute ne passe pas le seuil de 2 %, et elle ne converge pas.** Elle augmente
  quand on raffine, car l'encastrement bloque l'effet Poisson et crée une singularité. Le test est
  déclaré réussi sur la valeur extrapolée : un ajustement linéaire de SXX en fibre supérieure entre 25 % et
  75 % de la longueur, prolongé jusqu'à l'encastrement. Cette méthode n'est valable que si la théorie
  prédit une variation linéaire, ce qui ne se généralise pas à un bras de drone quelconque.
- Gmsh n'a pas donné le même maillage d'un lancement à l'autre. Sur trois lancements à h=2,5, SXX brut
  a valu 40,2, 38,6 et 37,2 MPa ; la flèche et la valeur extrapolée n'ont pas bougé de façon visible.
- L'écart de flèche de -0,67 % continue de diminuer avec le raffinement. La limite de convergence n'a
  pas été établie : aucun maillage plus fin que h=2,5 n'a été calculé.
- **Le C3D4 est inutilisable en flexion** (-40 %) : blocage en cisaillement à ce maillage.

## Limites constatées

### STEP multi-pièces (`tests/test_limites_step.py`)

Constaté :

- **Pas de densité** dans un STEP exporté par FreeCAD : aucun matériau, il faut une table externe.
- **Noms perdus avec `Part.read`** : les solides sont bien placés, mais anonymes. `Import.insert` les
  conserve.
- **Instances renommées** : un même produit placé 4 fois revient sous `moteur`, `moteur001`,
  `moteur002`, `moteur003`, sans lien. Une table de densités doit tolérer ce suffixe. Le test
  d'assemblage, lui, exige un nom exact et utilise des noms uniques.
- **Noms Gmsh** : un chemin avec répétitions, par exemple
  `Shapes/assemblage_drone/moteurs/moteurs/moteur_avant/moteur_avant`. Garder le dernier segment.
- **Corps surfacique piégeux** : dans un composé d'un solide de 1000 mm³ et d'une coque fermée de
  1000 mm³, `Shape.Volume` vaut 2000 alors que `Shape.Solids` n'en contient qu'un. Sommer sur `.Solids`
  et signaler toute coque restante.
- **Chevauchements non signalés** : la masse les compte deux fois. Il faut tester `common()` entre pièces.
- **Unités bien gérées** : changer l'unité déclarée de mm en m multiplie le volume par 1e9.
- **Placement global** : `o.getGlobalPlacement()` a donné les bonnes positions dans un sous-assemblage.

Non testé : STEP issus d'un autre logiciel (SolidWorks, Fusion 360, Onshape), fichier en pouces, matériaux
AP242, solides invalides, assemblage de plusieurs centaines de pièces.

### STL (`tests/test_limites_stl.py`)

- **Unités absentes** : l'en-tête ne contient que `solid Mesh`. Le même cube pèse 5,5 g lu en mm,
  90 129 g lu en pouces, 5,5e9 g lu en m. L'unité doit être fournie ou confirmée.
- **Volume fermé requis** : avec une facette retirée d'un cube de 1000 mm³, `isSolid` passe bien à False,
  mais `Mesh.Volume` renvoie 916,67 sans alerte. Une intégrale directe donne 916,67 ou 2583,33 mm³ selon
  la position du cube. Tester `isSolid()` avant tout calcul.
- **Chevauchement invisible** : deux cubes fusionnés se recouvrant de moitié donnent `isSolid=True` et
  2000 mm³ pour 1500 mm³ réels, sans alerte.
- **Assemblage fusionné** : `getSeparateComponents()` retrouve des pièces disjointes, sans nom ni densité.
- **Facettage**, sur un cylindre R14 H15 :

| Corde (mm) | Facettes | Écart volume | Écart Ixx | Écart Izz |
|---:|---:|---:|---:|---:|
| 1 | 100 | -0,970 % | -1,664 % | -1,930 % |
| 0,1 | 148 | -0,455 % | -0,782 % | -0,908 % |
| 0,01 | 468 | -0,047 % | -0,081 % | -0,094 % |
| 0,001 | 1484 | -0,005 % | -0,008 % | -0,010 % |

Le facettage sous-estime toujours un cylindre, et davantage l'inertie que le volume.

## Icônes et interfaces

`creer_icones.sh` crée `FreeCAD.desktop`, `Gmsh.desktop` et `CalculiX.desktop` sur le bureau. Vérifié :
`desktop-file-validate` sans erreur, exécutable, `metadata::trusted: true` relu, extension `ding` active,
et le fichier de démarrage du terminal CalculiX charge bien `ccx`.

**Non vérifié, à confirmer par l'utilisateur : l'affichage des icônes, le double-clic, les fenêtres FreeCAD
et Gmsh, et l'ouverture du terminal CalculiX.** Aucune fenêtre n'a été ouverte sur le bureau, et Xvfb n'est
pas disponible. L'interface FreeCAD a seulement été chargée hors écran (`QT_QPA_PLATFORM=offscreen`), avec
l'atelier FEM activé. Pour Gmsh, seul le lien aux bibliothèques FLTK a été contrôlé, et le rendu OpenGL
n'a pas été essayé.

Depuis un terminal VS Code installé en snap, `GIO_MODULE_DIR` empêche `gio set metadata::trusted`
(erreur « not supported »). `creer_icones.sh` retire cette variable pour lui-même, et les lanceurs
retirent les variables graphiques du snap pour eux-mêmes.

## Fichiers créés hors du dépôt

- `~/drone-tools/` : binaires, environnements, icônes, résultats.
- `~/Desktop/{FreeCAD,Gmsh,CalculiX}.desktop`.
- Créés par les outils eux-mêmes : `~/.config/FreeCAD`, `~/.local/share/FreeCAD`, `~/.fltk`, `~/.mamba`,
  `~/.conda/environments.txt`. Ce sont de petits fichiers, à retirer aussi pour une désinstallation complète.

Désinstaller : supprimer `~/drone-tools`, les trois `.desktop` et les dossiers ci-dessus.
