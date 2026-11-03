#!/usr/bin/env bash
# creer_icones.sh : pose sur le bureau les icônes du terminal OpenFOAM et de ParaView. Sans sudo.
# Peut être relancé : les deux fichiers sont réécrits à l'identique.
set -euo pipefail
ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUREAU="$(xdg-user-dir DESKTOP)"
[ -d "$BUREAU" ] || { echo "Dossier du bureau introuvable : $BUREAU" >&2; exit 1; }
case "$ICI" in *[[:space:]]*) echo "Chemin avec espace non géré : $ICI" >&2; exit 1 ;; esac
chmod +x "$ICI/of.sh" "$ICI/paraview_lance.sh"

cat > "$BUREAU/OpenFOAM-v2512.desktop" <<FIN
[Desktop Entry]
Type=Application
Version=1.0
Name=OpenFOAM v2512
Comment=Terminal avec l'environnement OpenFOAM chargé, sans ROS ni venv_stage
Exec=gnome-terminal --title="OpenFOAM v2512" -- bash --rcfile $ICI/terminal_openfoam.rc -i
Icon=utilities-terminal
Terminal=false
Categories=Science;Engineering;
FIN

cat > "$BUREAU/ParaView.desktop" <<FIN
[Desktop Entry]
Type=Application
Version=1.0
Name=ParaView
Comment=Visualisation des résultats OpenFOAM (ouvrir le fichier .foam du cas)
Exec=$ICI/paraview_lance.sh %f
Icon=paraview
Terminal=false
Categories=Science;
MimeType=application/x-paraview;
FIN

# Un GIO_MODULE_DIR hérité (terminal de VS Code en snap, par exemple) masque le module gvfs :
# gio répond alors « metadata::trusted not supported ». On lance donc gio sans cet héritage.
GIO=(env -u GIO_MODULE_DIR -u LD_LIBRARY_PATH gio)
for f in "$BUREAU/OpenFOAM-v2512.desktop" "$BUREAU/ParaView.desktop"; do
    chmod +x "$f"
    desktop-file-validate "$f"
    "${GIO[@]}" set "$f" metadata::trusted true
    etat="$("${GIO[@]}" info -a metadata::trusted "$f" | awk '/metadata::trusted/{print $2}')"
    [ "$etat" = "true" ] || { echo "Marquage de confiance absent sur $f" >&2; exit 1; }
    echo "$f : exécutable, valide, trusted=$etat"
done
