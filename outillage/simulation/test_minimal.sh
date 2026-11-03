#!/usr/bin/env bash
# test_minimal.sh : vol de contrôle sans affichage (voir test_minimal.py).
# Exemples :
#     outillage/simulation/test_minimal.sh
#     outillage/simulation/test_minimal.sh --vitesse 2 --stationnaire 30 --altitude 5
# Sortie : ~/drone-tools/logs/test_<date>/ (resultat.json, px4.log, *.ulg). Code 0 = réussite.
set -euo pipefail
ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
set +u
# shellcheck source=env.sh disable=SC1091
source "$ICI/env.sh"
set -u
[[ -x "$PX4_BUILD_DIR/bin/px4" ]] || { echo "PX4 non compilé : $PX4_BUILD_DIR/bin/px4" >&2; exit 2; }
exec "$PX4_VENV/bin/python3" "$ICI/test_minimal.py" "$@"
