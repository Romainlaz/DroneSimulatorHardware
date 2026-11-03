#!/usr/bin/env bash
# creer_icones.sh : icônes du bureau pour la simulation (sans sudo, relançable).
#   - « Gazebo + PX4 SITL »   : fenêtre 3D, rendu NVIDIA, console PX4 dans un terminal
#   - « QGroundControl »      : station sol, si l'AppImage est installée
#   - « Terminal PX4-Gazebo » : terminal avec l'environnement chargé, pour pyulog, MAVSDK, gz, etc.
# Les icônes pointent vers ce dossier : si le dépôt est déplacé, relancer ce script.
set -euo pipefail

ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUREAU="$(xdg-user-dir DESKTOP)"
OUTILS="${DRONE_TOOLS:-$HOME/drone-tools}"
QGC="$OUTILS/qgroundcontrol/QGroundControl-x86_64.AppImage"
ICONES="$OUTILS/icones"
mkdir -p "$BUREAU" "$ICONES"

# Le snap de VS Code exporte GIO_MODULE_DIR : sans gvfs, gio refuse metadata::trusted dans ses terminaux.
unset GIO_MODULE_DIR

# Écrit, valide et marque de confiance un fichier .desktop. Le contenu arrive sur l'entrée standard.
installer() {
	local fichier="$BUREAU/$1"
	cat > "$fichier"
	chmod 755 "$fichier"
	command -v desktop-file-validate >/dev/null && desktop-file-validate "$fichier"
	gio set "$fichier" metadata::trusted true
	echo "OK $fichier (trusted=$(gio info -a metadata::trusted "$fichier" | awk '/metadata::trusted/{print $2}'))"
}

installer drone-gazebo-px4.desktop <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=Gazebo + PX4 SITL
Comment=Simulation PX4 v1.17.0 avec fenêtre 3D (rendu NVIDIA)
Exec=gnome-terminal --title="PX4 SITL + Gazebo" -- "$ICI/lancer_gazebo_px4.sh"
Icon=gz-logo8
Terminal=false
Categories=Development;
EOF

if [[ -x "$QGC" ]]; then
	# Icône extraite de l'AppImage, une seule fois, dans un dossier temporaire.
	if [[ ! -f "$ICONES/QGroundControl.svg" ]]; then
		TMP="$(mktemp -d)"
		CHEMIN_SVG=usr/share/icons/hicolor/scalable/apps/QGroundControl.svg
		( cd "$TMP" && "$QGC" --appimage-extract "$CHEMIN_SVG" >/dev/null )
		cp "$TMP/squashfs-root/$CHEMIN_SVG" "$ICONES/"
		rm -rf "$TMP"
	fi
	# env -u : si GNOME hérite de l'environnement ROS, il ne doit pas perturber l'AppImage.
	installer drone-qgroundcontrol.desktop <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=QGroundControl
Comment=Station sol v5.1.5 : voir et piloter la simulation PX4
Exec=env -u LD_LIBRARY_PATH -u PYTHONPATH "$QGC"
Icon=$ICONES/QGroundControl.svg
Terminal=false
Categories=Utility;
EOF
else
	echo "QGroundControl absent ($QGC) : pas d'icône."
fi

installer drone-terminal-px4.desktop <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=Terminal PX4-Gazebo
Comment=Terminal avec l'environnement de simulation chargé (sans ROS ni venv_stage)
Exec=gnome-terminal --title="Environnement PX4-Gazebo" -- bash --rcfile "$ICI/terminal_env.rc" -i
Icon=org.gnome.Terminal
Terminal=false
Categories=Development;
EOF
