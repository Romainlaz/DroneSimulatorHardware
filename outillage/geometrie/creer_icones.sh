#!/usr/bin/env bash
# Crée les icônes FreeCAD, Gmsh et CalculiX sur le bureau GNOME, sans sudo. Relançable.
# Prérequis : installer_espace_utilisateur.sh déjà lancé.
set -euo pipefail

# Un terminal VS Code (snap) exporte GIO_MODULE_DIR : gio ne charge alors pas le module gvfs et
# refuse metadata::trusted avec "not supported". On retire ces variables pour ce script seulement.
unset GIO_MODULE_DIR GSETTINGS_SCHEMA_DIR GTK_PATH GTK_EXE_PREFIX LOCPATH LD_LIBRARY_PATH

BASE="${DRONE_TOOLS:-$HOME/drone-tools}"
ICI="$(dirname "$(readlink -f "$0")")"
BUREAU="$(xdg-user-dir DESKTOP)"
ICONES="$BASE/icones"
FC_ICONE="$BASE/freecad-1.1.4/squashfs-root/org.freecad.FreeCAD.svg"
mkdir -p "$ICONES" "$BUREAU"

for commande in freecad gmsh ccx; do
    [ -x "$BASE/bin/$commande" ] || { echo "Absent : $BASE/bin/$commande. Lancer l'installation d'abord." >&2; exit 1; }
done
[ -f "$FC_ICONE" ] || { echo "Icône FreeCAD absente : $FC_ICONE" >&2; exit 1; }

# Gmsh et CalculiX ne fournissent pas d'icône utilisable dans leurs paquets conda.
cat > "$ICONES/gmsh.svg" <<'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="10" fill="#1f5f8b"/><g fill="none" stroke="#fff" stroke-width="2.5" stroke-linejoin="round"><path d="M32 8 56 54H8Z"/><path d="M20 31h24M14 43h36M32 54 20 31 32 8 44 31 32 54M26 54 14 43M38 54 50 43"/></g></svg>
EOF
cat > "$ICONES/calculix.svg" <<'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="10" fill="#2e3440"/><rect x="6" y="10" width="7" height="44" fill="#d8dee9"/><path d="M13 24C30 25 45 30 57 42L57 50C45 38 30 33 13 32Z" fill="#ebcb8b"/><path d="M57 16v18M52 28l5 7 5-7" fill="none" stroke="#bf616a" stroke-width="3"/></svg>
EOF

# Le terminal CalculiX ne lit pas ~/.bashrc : il démarre propre, avec l'environnement chargé.
cat > "$BASE/bin/terminal-calculix.rc" <<EOF
# Généré par creer_icones.sh. Lu par le terminal de l'icône CalculiX.
[ -f /etc/bash.bashrc ] && . /etc/bash.bashrc
. "$ICI/env.sh"
PS1='[calculix] \w\$ '
echo "CalculiX, sans interface. Commande : ccx -i <nom_sans_.inp>"
ccx -v 2>&1 | grep -v '^\$'
echo "Aussi disponibles : gmsh, freecadcmd, drone-cae-python, drone-freecad-python"
cd "$ICI"
EOF

# $1 = nom de fichier, puis Name, Comment, Exec, Icon, et options éventuelles.
ecrire_desktop() {
    local cible="$BUREAU/$1.desktop"
    {
        echo "[Desktop Entry]"
        echo "Type=Application"
        echo "Version=1.0"
        echo "Name=$2"
        echo "Comment=$3"
        echo "Exec=$4"
        echo "Icon=$5"
        echo "Terminal=false"
        echo "Categories=$6"
        [ -n "${7:-}" ] && echo "MimeType=$7"
    } > "$cible"
    chmod 755 "$cible"
    desktop-file-validate "$cible"
    gio set "$cible" metadata::trusted true
    # Relecture : une icône non marquée de confiance ne se lance pas d'un double-clic.
    if ! gio info -a metadata::trusted "$cible" | grep -q 'metadata::trusted: true'; then
        echo "ÉCHEC : $cible n'est pas marqué de confiance." >&2
        return 1
    fi
    echo "$cible : valide, exécutable, de confiance"
}

ecrire_desktop FreeCAD "FreeCAD 1.1.4" "Modeleur CAO paramétrique" \
    "$BASE/bin/freecad %F" "$FC_ICONE" "Graphics;Engineering;" "application/step;model/step;"
ecrire_desktop Gmsh "Gmsh 4.15.2" "Mailleur éléments finis" \
    "$BASE/bin/gmsh %f" "$ICONES/gmsh.svg" "Science;Engineering;"
ecrire_desktop CalculiX "CalculiX 2.23 (terminal)" "Terminal avec CalculiX et les outils chargés" \
    "gnome-terminal --title=CalculiX -- bash --rcfile $BASE/bin/terminal-calculix.rc -i" \
    "$ICONES/calculix.svg" "Science;Engineering;"
