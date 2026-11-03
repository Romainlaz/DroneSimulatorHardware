# Environnement des outils de géométrie. À sourcer : source outillage/geometrie/env.sh
#
# Ajoute uniquement ~/drone-tools/bin au PATH. Ne touche pas au PYTHONPATH ni au
# LD_LIBRARY_PATH : ROS 2 et ~/venv_stage restent fonctionnels dans ce shell, et les
# lanceurs de ~/drone-tools/bin nettoient leur propre environnement.
#
# Commandes : freecad, freecadcmd, drone-freecad-python, gmsh, ccx, drone-cae-python, micromamba
export DRONE_TOOLS="${DRONE_TOOLS:-$HOME/drone-tools}"
export MAMBA_ROOT_PREFIX="$DRONE_TOOLS/micromamba"
case ":$PATH:" in
    *":$DRONE_TOOLS/bin:"*) ;;
    *) export PATH="$DRONE_TOOLS/bin:$PATH" ;;
esac
