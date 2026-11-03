#!/usr/bin/env bash
# Lance tous les tests, sans interface, sous nice et avec 4 threads au plus.
# Journal : ~/drone-tools/resultats/journal_tests.txt. Code de sortie non nul si un test échoue.
set -uo pipefail

ICI="$(dirname "$(readlink -f "$0")")"
# shellcheck source=env.sh
source "$ICI/env.sh"
export OMP_NUM_THREADS=4
SORTIE="$DRONE_TOOLS/resultats"
JOURNAL="$SORTIE/journal_tests.txt"
mkdir -p "$SORTIE"
: > "$JOURNAL"
echecs=0

lancer() {
    local nom="$1"; shift
    echo "===== $nom =====" | tee -a "$JOURNAL"
    # Le filtre retire un message répété de Qt hors écran, sans effet sur le résultat.
    nice -n 15 timeout 900 "$@" 2>&1 | grep --line-buffered -v propagateSizeHints | tee -a "$JOURNAL"
    local code=${PIPESTATUS[0]}
    echo "[$nom : code de sortie $code]" | tee -a "$JOURNAL"
    echo | tee -a "$JOURNAL"
    [ "$code" -eq 0 ] || echecs=$((echecs + 1))
}

lancer "Critère FreeCAD (freecadcmd)" freecadcmd "$ICI/tests/verifier_freecad.py"
lancer "Critère FreeCAD (module Python)" drone-freecad-python "$ICI/tests/verifier_freecad.py"
lancer "Interface FreeCAD hors écran" env QT_QPA_PLATFORM=offscreen drone-freecad-python "$ICI/tests/verifier_interfaces.py"
lancer "Géométrie : assemblage STEP (FreeCAD)" drone-freecad-python "$ICI/tests/test_assemblage_step.py" "$SORTIE/assemblage"
lancer "Géométrie : relecture par Gmsh" drone-cae-python "$ICI/tests/test_assemblage_gmsh.py" "$SORTIE/assemblage"
lancer "Limites des STL" drone-freecad-python "$ICI/tests/test_limites_stl.py" "$SORTIE/stl"
lancer "Limites des STEP" drone-freecad-python "$ICI/tests/test_limites_step.py" "$SORTIE/limites_step"
lancer "Résistance : Gmsh + CalculiX" drone-cae-python "$ICI/tests/test_poutre_calculix.py" "$SORTIE/poutre"
lancer "Résistance : FreeCAD FEM + CalculiX" drone-freecad-python "$ICI/tests/test_fem_freecad.py" "$SORTIE/fem_freecad"

echo "Tests en échec : $echecs" | tee -a "$JOURNAL"
[ "$echecs" -eq 0 ]
