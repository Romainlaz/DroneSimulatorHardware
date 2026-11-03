# env.sh : environnement PX4 v1.17.0 SITL + Gazebo Harmonic. À SOURCER, pas à exécuter :
#     source outillage/simulation/env.sh
#
# Ne modifie que le shell courant : ni ~/.bashrc, ni ROS, ni ~/venv_stage.
# ~/.bashrc source ROS 2 Jazzy et ~/venv_stage : leurs variables masqueraient les bibliothèques
# gz-math/gz-utils de Gazebo Harmonic et les modules Python de PX4. On les retire donc ici.
# Pour retrouver ROS : ouvrir un nouveau terminal.

# Vrai dossier de ce fichier, même sourcé depuis ailleurs.
DRONE_SIM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export DRONE_SIM_DIR

export DRONE_TOOLS="${DRONE_TOOLS:-$HOME/drone-tools}"
export PX4_DIR="$DRONE_TOOLS/PX4-Autopilot"
export PX4_VENV="$DRONE_TOOLS/venv-px4"
export PX4_BUILD_DIR="$PX4_DIR/build/px4_sitl_default"
export QGC_APPIMAGE="$DRONE_TOOLS/qgroundcontrol/QGroundControl-x86_64.AppImage"

# --- Sortie du venv actif (venv_stage en général), sans l'altérer.
if declare -F deactivate >/dev/null 2>&1; then
	deactivate nondestructive 2>/dev/null || true
fi
unset VIRTUAL_ENV VIRTUAL_ENV_PROMPT PYTHONHOME

# --- Retrait de ROS et de venv_stage de l'environnement du shell.
unset PYTHONPATH LD_LIBRARY_PATH CMAKE_PREFIX_PATH AMENT_PREFIX_PATH COLCON_PREFIX_PATH
unset ROS_VERSION ROS_PYTHON_VERSION ROS_DISTRO ROS_AUTOMATIC_DISCOVERY_RANGE
unset GZ_SIM_RESOURCE_PATH GZ_SIM_SYSTEM_PLUGIN_PATH GZ_SIM_SERVER_CONFIG_PATH
PATH="$(printf '%s' "$PATH" | tr ':' '\n' | grep -v -E '^/opt/ros/|/venv_stage/' | paste -sd ':' -)"

# --- Terminal du snap VS Code : ses variables GTK/GIO/locale gêneraient les applications système.
if [ -n "${XDG_DATA_DIRS_VSCODE_SNAP_ORIG:-}" ]; then
	export XDG_DATA_DIRS="$XDG_DATA_DIRS_VSCODE_SNAP_ORIG"
fi
unset GIO_MODULE_DIR GTK_PATH GTK_EXE_PREFIX GTK_IM_MODULE_FILE GSETTINGS_SCHEMA_DIR LOCPATH

# --- Venv dédié (ajouté au PATH si déjà créé).
if [ -d "$PX4_VENV/bin" ]; then
	export VIRTUAL_ENV="$PX4_VENV"
	PATH="$PX4_VENV/bin:$PATH"
fi
export PATH

# --- PX4 : ne cherche que Gazebo Harmonic (voir gz_bridge/CMakeLists.txt).
export GZ_DISTRO=harmonic

# --- Compilation partagée : 6 threads au plus (d'autres agents utilisent la machine).
export DRONE_NICE="nice -n 10"
export CMAKE_BUILD_PARALLEL_LEVEL=6
export CCACHE_DIR="$DRONE_TOOLS/.ccache"

# --- Rendu NVIDIA (PRIME on-demand) : à préfixer pour les lancements avec fenêtre 3D.
drone_nvidia() {
	__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia "$@"
}
