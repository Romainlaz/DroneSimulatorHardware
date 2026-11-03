#!/usr/bin/env bash
# lancer.sh [niveau] [np] : traînée d'une sphère à Re = 100, du STL jusqu'au Cd comparé à la référence.
#
#   niveau : raffinement à la paroi, cellule de taille D / 2^niveau (défaut 5)
#   np     : processus MPI, 4 au maximum (défaut 4)
#
# Le calcul s'écrit dans ~/drone-tools/cfd/runs/sphere_Re100_L<niveau>/ (recréé à chaque lancement).
# Sorties : log.* par étape, temps.tsv, charge.tsv, resultat.json.
# Code de retour non nul si une étape échoue : le dernier log est alors affiché.
set -euo pipefail
ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Se relance en environnement vierge et sous nice.
if [ -z "${WM_PROJECT_DIR:-}" ] || [ -z "${OF_CAS_NETTOYE:-}" ]; then
    export OF_CAS_NETTOYE=1
    exec "$ICI/../of.sh" env OF_CAS_NETTOYE=1 bash "${BASH_SOURCE[0]}" "$@"
fi

NIVEAU="${1:-5}"
NP="${2:-4}"
[ "$NP" -le "$OF_NP_MAX" ] || { echo "np limité à $OF_NP_MAX" >&2; exit 2; }
CAS="$DRONE_CFD/runs/sphere_Re100_L$NIVEAU"

rm -rf -- "$CAS"
mkdir -p "$CAS/constant/triSurface"
cp -r "$ICI/modele/." "$CAS/"
cd "$CAS"
touch cas.foam     # à ouvrir dans ParaView
printf 'niveau %d;\nniveauM1 %d;\nniveauM2 %d;\n' "$NIVEAU" $((NIVEAU-1)) $((NIVEAU-2)) > system/params
sed -i "s/numberOfSubdomains .*/numberOfSubdomains $NP;/" system/decomposeParDict

MPI=(mpirun -np "$NP" --bind-to none)
[ "$NP" -gt 1 ] || MPI=()
PAR=(); [ "$NP" -le 1 ] || PAR=(-parallel)

# Échantillonne la charge de la machine toutes les 10 s pendant tout le cas.
# Colonnes : date, charge à 1 min, mémoire totale des processus OpenFOAM en Mo.
( while :; do
    printf '%s %s %s\n' "$(date +%s)" "$(cut -d' ' -f1 /proc/loadavg)" \
        "$(ps -u "$(id -u)" -o rss=,comm= | awk '/Foam|snappyHexMesh|checkMesh/{s+=$1}END{printf "%.0f", s/1024}')"
    sleep 10
done ) > charge.tsv &
ECHANTILLON=$!
trap 'kill "$ECHANTILLON" 2>/dev/null || true' EXIT

printf 'etape\tsecondes\tcharge_debut\tcharge_fin\n' > temps.tsv
etape() {
    local nom="$1"; shift
    local debut charge0 ; debut=$(date +%s.%N); charge0=$(cut -d' ' -f1 /proc/loadavg)
    echo "--- $nom"
    if ! "$@" > "log.$nom" 2>&1; then
        echo "ÉCHEC de l'étape $nom. Fin de log.$nom :" >&2
        tail -30 "log.$nom" >&2
        exit 1
    fi
    printf '%s\t%.1f\t%s\t%s\n' "$nom" "$(echo "$(date +%s.%N) - $debut" | bc -l)" "$charge0" "$(cut -d' ' -f1 /proc/loadavg)" >> temps.tsv
}

etape stl            /usr/bin/python3 -I "$ICI/generer_sphere_stl.py" constant/triSurface/sphere.stl 1 6
etape blockMesh      blockMesh
etape decomposePar   decomposePar -force
etape snappyHexMesh  "${MPI[@]}" snappyHexMesh -overwrite "${PAR[@]}"
etape champs_initiaux bash -c 'for d in processor*; do cp -r 0.orig "$d/0"; done'
etape checkMesh      "${MPI[@]}" checkMesh -constant "${PAR[@]}"
grep -q 'Mesh OK' log.checkMesh && echo "checkMesh : Mesh OK" || echo "checkMesh : défauts de maillage, voir log.checkMesh"
etape potentialFoam  "${MPI[@]}" potentialFoam -writephi "${PAR[@]}"
etape simpleFoam     "${MPI[@]}" simpleFoam "${PAR[@]}"
etape reconstruction bash -c 'reconstructParMesh -constant && reconstructPar -latestTime'
rm -rf processor*

/usr/bin/python3 -I "$ICI/analyser.py" "$CAS"
echo
cat temps.tsv
echo "Maillage : $(grep -m1 -E '^\s+cells:' log.checkMesh)"
echo "simpleFoam : $(grep ExecutionTime log.simpleFoam | tail -1)"
awk '{if($3>m)m=$3; c+=$2; n++} END{printf "Mémoire OpenFOAM max : %d Mo ; charge moyenne : %.1f (%d mesures)\n", m, c/n, n}' charge.tsv
echo "Cas : $CAS"
