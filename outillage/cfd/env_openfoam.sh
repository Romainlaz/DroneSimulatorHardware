# env_openfoam.sh : charge OpenFOAM v2512 dans le shell courant, isolé de ROS 2 et de venv_stage.
#
#   source outillage/cfd/env_openfoam.sh
#
# Seul le shell courant est touché : ni ~/.bashrc, ni venv_stage, ni l'installation de ROS.
# ROS et OpenFOAM ne cohabitent pas dans un même shell : ouvrir un autre terminal pour ROS.

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    echo "À sourcer : source ${BASH_SOURCE[0]}" >&2
    exit 1
fi

# OpenFOAM ne supporte ni « set -u » ni « set -e » pendant son chargement.
_of_opts="$-"
set +eu

# Retire d'une variable de type PATH les entrées ROS et venv_stage.
_of_nettoie() {
    local var="$1" sortie="" entree
    local IFS=':'
    for entree in ${!var-}; do
        case "$entree" in
            /opt/ros/*|*/venv_stage|*/venv_stage/*) ;;
            *) sortie="${sortie:+$sortie:}$entree" ;;
        esac
    done
    if [ -n "$sortie" ]; then export "$var=$sortie"; else unset "$var"; fi
}
for _of_v in PATH LD_LIBRARY_PATH PYTHONPATH PKG_CONFIG_PATH CMAKE_PREFIX_PATH; do
    _of_nettoie "$_of_v"
done
for _of_v in $(compgen -e | grep -E '^(ROS_|RMW_|AMENT_|COLCON_)'); do unset "$_of_v"; done
unset VIRTUAL_ENV VIRTUAL_ENV_PROMPT PYTHONHOME
unset -f deactivate 2>/dev/null

# L'argument vide empêche bashrc d'interpréter les arguments du shell appelant comme des options.
. /usr/lib/openfoam/openfoam2512/etc/bashrc ''

# Limites de la machine partagée : 4 processus au maximum, sans fils supplémentaires.
export OMP_NUM_THREADS=1
export DRONE_CFD="$HOME/drone-tools/cfd"
export OF_NP_MAX=4

# PyFoam, ajouté en fin de PATH : /usr/bin/python3 reste le python par défaut.
[ -x "$DRONE_CFD/pyfoam/bin/pyFoamVersion.py" ] && export PATH="$PATH:$DRONE_CFD/pyfoam/bin"

unset -f _of_nettoie
unset _of_v
case "$_of_opts" in *e*) set -e ;; esac
case "$_of_opts" in *u*) set -u ;; esac
unset _of_opts
