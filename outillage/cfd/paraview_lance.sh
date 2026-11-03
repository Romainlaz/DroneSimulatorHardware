#!/usr/bin/env bash
# paraview_lance.sh [fichier] : ouvre ParaView, sur la carte NVIDIA si elle répond (PRIME on-demand),
# sinon sur la carte Intel.
#
# Environnement vierge plus la session graphique : ni ROS, ni venv_stage, ni les variables d'un
# terminal VS Code en snap, qui font échouer ParaView sur une bibliothèque de /snap/core20.
ENVS=(env -i HOME="$HOME" USER="${USER:-$(id -un)}" PATH=/usr/bin:/bin LANG="${LANG:-C.UTF-8}"
      DISPLAY="${DISPLAY:-:0}" XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"
      XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
      DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}")
if "${ENVS[@]}" __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia glxinfo -B 2>/dev/null \
    | grep -q 'renderer string: Quadro'; then
    ENVS+=(__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia)
fi
exec "${ENVS[@]}" paraview "$@"
