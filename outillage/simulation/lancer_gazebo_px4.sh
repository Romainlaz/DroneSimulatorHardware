#!/usr/bin/env bash
# lancer_gazebo_px4.sh : Gazebo + PX4 SITL avec fenêtre 3D, rendu NVIDIA (PRIME on-demand).
# Lancé par l'icône du bureau, ou à la main dans un terminal. La console PX4 (pxh>) reste au premier
# plan : « commander takeoff », « commander land ». Fermer le terminal arrête aussi Gazebo.
# QGroundControl se connecte tout seul à cette simulation (UDP 14550).
ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=env.sh disable=SC1091
source "$ICI/env.sh"

if [[ ! -x "$PX4_BUILD_DIR/bin/px4" ]]; then
	echo "PX4 non compilé : $PX4_BUILD_DIR/bin/px4"
	read -r -p "Entrée pour fermer..."
	exit 2
fi

# Rendu NVIDIA pour la fenêtre 3D ; réseau gz limité à cette machine et à cette simulation.
export __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia
export GZ_IP=127.0.0.1 GZ_PARTITION="px4gui_$$"
export PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=gz_x500 PX4_GZ_WORLD="${PX4_GZ_WORLD:-default}"
unset HEADLESS

# Arrêt de PX4 et de Gazebo (même groupe de processus) à la fermeture du terminal.
# setsid garantit que ce script dirige son groupe si on le lance depuis un autre programme.
if [[ "$(ps -o pgid= $$ | tr -d ' ')" != "$$" ]]; then
	exec setsid --ctty --wait "$0" "$@"
fi
arret() { trap - EXIT INT TERM HUP; kill 0 2>/dev/null; }
trap arret EXIT INT TERM HUP

cd "$PX4_BUILD_DIR/rootfs" || exit 1
"$PX4_BUILD_DIR/bin/px4"
