#!/usr/bin/env bash
# of.sh : lance une commande OpenFOAM pour un agent, en environnement vierge et sous nice.
#
#   outillage/cfd/of.sh simpleFoam -help
#   outillage/cfd/of.sh mpirun -np 4 --bind-to none simpleFoam -parallel -case <dossier>
#
# L'environnement appelant (ROS, venv_stage) n'est pas hérité. Priorité réglable par OF_NICE.
set -eu
ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ $# -ge 1 ] || { echo "Usage : $0 <commande> [arguments]" >&2; exit 2; }
exec env -i HOME="$HOME" USER="${USER:-$(id -un)}" LANG=C.UTF-8 PATH=/usr/bin:/bin \
    TERM="${TERM:-dumb}" OF_ICI="$ICI" \
    nice -n "${OF_NICE:-15}" bash -c '. "$OF_ICI/env_openfoam.sh"; exec "$@"' of.sh "$@"
