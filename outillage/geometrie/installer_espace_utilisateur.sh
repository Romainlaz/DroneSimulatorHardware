#!/usr/bin/env bash
# Installe FreeCAD, Gmsh et CalculiX dans ~/drone-tools, sans sudo. Relançable sans effet de bord.
#
# Sources et raisons : voir NOTES.md.
#   - FreeCAD 1.1.4 : AppImage officielle, extraite, somme SHA-256 vérifiée.
#   - Gmsh 4.15.2 et CalculiX 2.23 : conda-forge, environnement micromamba "cae".
#
# Ne touche ni à ~/.bashrc, ni à ROS 2, ni à ~/venv_stage, ni au système.
# Usage : ./installer_espace_utilisateur.sh
set -euo pipefail

BASE="${DRONE_TOOLS:-$HOME/drone-tools}"
BIN="$BASE/bin"
TELE="$BASE/downloads"
export MAMBA_ROOT_PREFIX="$BASE/micromamba"

MICROMAMBA_VERSION="2.10.0-0"
MICROMAMBA_SHA256="701f39c06f8e6a670a0e186c8479b9e5c0502a2f0cda6cef65d83bdd2875e8bd"
FREECAD_VERSION="1.1.4"
FREECAD_FICHIER="FreeCAD_${FREECAD_VERSION}-Linux-x86_64-py311.AppImage"
FREECAD_SHA256="f6dc6ba676e5ac96a565ebc8d657232f94c6158e85b4352141bd1a46f6b43434"
FREECAD_DIR="$BASE/freecad-$FREECAD_VERSION/squashfs-root"
CAE_ENV="$MAMBA_ROOT_PREFIX/envs/cae"

# Télécharge $2 vers $1 si besoin, puis vérifie $3. Un fichier incorrect arrête tout.
telecharger() {
    local cible="$1" url="$2" somme="$3"
    if [ ! -f "$cible" ] || ! echo "$somme  $cible" | sha256sum -c --status -; then
        echo "Téléchargement de $url"
        curl -fL --retry 3 -o "$cible.part" "$url"
        mv "$cible.part" "$cible"
    fi
    echo "$somme  $cible" | sha256sum -c -
}

mkdir -p "$BIN" "$TELE/micromamba" "$TELE/freecad-appimage"

# 1. micromamba : un seul binaire, n'active rien et n'écrit dans aucun fichier du shell.
telecharger "$TELE/micromamba/micromamba-linux-64" \
    "https://github.com/mamba-org/micromamba-releases/releases/download/$MICROMAMBA_VERSION/micromamba-linux-64" \
    "$MICROMAMBA_SHA256"
install -m 755 "$TELE/micromamba/micromamba-linux-64" "$BIN/micromamba"

# 2. Gmsh et CalculiX. Variables ROS retirées : elles ne doivent pas influencer conda.
if [ ! -x "$CAE_ENV/bin/ccx" ] || [ ! -x "$CAE_ENV/bin/gmsh" ]; then
    env -u PYTHONPATH -u LD_LIBRARY_PATH -u VIRTUAL_ENV -u AMENT_PREFIX_PATH \
        nice -n 15 "$BIN/micromamba" create -y -q -n cae -c conda-forge --override-channels --no-rc \
        'calculix=2.23' 'gmsh=4.15.2' 'python-gmsh=4.15.2' 'python=3.12' numpy
fi

# 3. FreeCAD : l'extraction évite la dépendance à FUSE et accélère chaque lancement.
telecharger "$TELE/freecad-appimage/$FREECAD_FICHIER" \
    "https://github.com/FreeCAD/FreeCAD/releases/download/$FREECAD_VERSION/$FREECAD_FICHIER" \
    "$FREECAD_SHA256"
chmod +x "$TELE/freecad-appimage/$FREECAD_FICHIER"
if [ ! -x "$FREECAD_DIR/usr/bin/freecadcmd" ]; then
    mkdir -p "$BASE/freecad-$FREECAD_VERSION"
    ( cd "$BASE/freecad-$FREECAD_VERSION" && \
      nice -n 15 "$TELE/freecad-appimage/$FREECAD_FICHIER" --appimage-extract >/dev/null )
fi

# 4. Lanceurs. Chacun nettoie l'environnement de SON processus seulement, le shell appelant garde
#    le sien. Précaution : sans lanceur, un essai sous l'environnement ROS a aussi fonctionné, mais
#    rien ne garantit qu'aucun module de ROS ne masquera un jour celui de FreeCAD ou de Gmsh.
ecrire_lanceur() {
    local nom="$1" prefixe_path="$2" exports="$3" commande="$4"
    cat > "$BIN/$nom" <<EOF
#!/usr/bin/env bash
# Généré par installer_espace_utilisateur.sh. Ne pas modifier à la main.
unset PYTHONPATH PYTHONHOME LD_LIBRARY_PATH VIRTUAL_ENV AMENT_PREFIX_PATH CONDA_PREFIX QT_PLUGIN_PATH QT_QPA_PLATFORM_PLUGIN_PATH
# Variables du snap VS Code, héritées par ses terminaux : elles gênent les bibliothèques graphiques.
unset GIO_MODULE_DIR GSETTINGS_SCHEMA_DIR GTK_PATH GTK_EXE_PREFIX GTK_IM_MODULE_FILE LOCPATH GDK_PIXBUF_MODULE_FILE GDK_PIXBUF_MODULEDIR
export PATH="$prefixe_path:\$PATH"
export OMP_NUM_THREADS="\${OMP_NUM_THREADS:-4}"
$exports
exec $commande "\$@"
EOF
    chmod 755 "$BIN/$nom"
}

FC_EXPORTS=''
FC_PY_EXPORTS="export PYTHONHOME=\"$FREECAD_DIR/usr\" PYTHONPATH=\"$FREECAD_DIR/usr/lib\""
ecrire_lanceur freecad              "$FREECAD_DIR/usr/bin" "$FC_EXPORTS"    "\"$FREECAD_DIR/AppRun\" freecad"
ecrire_lanceur freecadcmd           "$FREECAD_DIR/usr/bin" "$FC_EXPORTS"    "\"$FREECAD_DIR/AppRun\" freecadcmd"
ecrire_lanceur drone-freecad-python "$FREECAD_DIR/usr/bin" "$FC_PY_EXPORTS" "\"$FREECAD_DIR/usr/bin/python\""
ecrire_lanceur gmsh                 "$CAE_ENV/bin"         ""               "\"$CAE_ENV/bin/gmsh\""
ecrire_lanceur ccx                  "$CAE_ENV/bin"         ""               "\"$CAE_ENV/bin/ccx\""
ecrire_lanceur drone-cae-python     "$CAE_ENV/bin"         ""               "\"$CAE_ENV/bin/python\""

echo "Installation terminée dans $BASE"
echo "Étape suivante : source $(dirname "$(readlink -f "$0")")/env.sh"
