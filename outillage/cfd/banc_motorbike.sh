#!/usr/bin/env bash
# banc_motorbike.sh : mesure de temps sur le tutoriel officiel motorBike (géométrie complexe, RANS),
# ramené à 4 processus. Sert uniquement à étayer la projection pour un drone complet de NOTES.md.
# Le calcul s'écrit dans ~/drone-tools/cfd/runs/motorBike/ (recréé à chaque lancement).
set -euo pipefail
ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -z "${OF_CAS_NETTOYE:-}" ]; then
    exec "$ICI/of.sh" env OF_CAS_NETTOYE=1 bash "${BASH_SOURCE[0]}" "$@"
fi
CAS="$DRONE_CFD/runs/motorBike"
rm -rf -- "$CAS"
mkdir -p "$DRONE_CFD/runs"
cp -r "$FOAM_TUTORIALS/incompressible/simpleFoam/motorBike" "$CAS"
cd "$CAS"
sed -i -e 's/^numberOfSubdomains.*/numberOfSubdomains 4;/' -e 's/n *(3 2 1)/n (2 2 1)/' -e 's/^method.*/method scotch;/' system/decomposeParDict.6
# Pas d'épinglage des processus : la machine est partagée avec d'autres calculs.
export OMPI_MCA_hwloc_base_binding_policy=none
( while :; do
    printf '%s %s %s\n' "$(date +%s)" "$(cut -d' ' -f1 /proc/loadavg)" \
        "$(ps -u "$(id -u)" -o rss=,comm= | awk '/Foam|snappyHexMesh|checkMesh/{s+=$1}END{printf "%.0f", s/1024}')"
    sleep 10
done ) > charge.tsv &
ECHANTILLON=$!
trap 'kill "$ECHANTILLON" 2>/dev/null || true' EXIT
debut=$(date +%s)
./Allrun
echo "Durée totale : $(( $(date +%s) - debut )) s"
for l in log.snappyHexMesh log.simpleFoam; do
    echo "$l : $(grep -E 'ExecutionTime' "$l" | tail -1)"
done
grep -m1 -E '^\s+cells:' log.checkMesh
tail -1 postProcessing/forceCoeffs1/0/coefficient.dat | cut -c1-60
awk '{if($3>m)m=$3; c+=$2; n++} END{printf "Mémoire OpenFOAM max : %d Mo ; charge moyenne : %.1f\n", m, c/n}' charge.tsv
