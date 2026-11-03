#!/usr/bin/env bash
# install_sudo.sh : dépendances système pour PX4 v1.17.0 SITL + Gazebo Harmonic (Ubuntu 24.04).
#
# À lancer par l'utilisateur :
#     sudo bash outillage/simulation/install_sudo.sh
#
# Idempotent : on peut le relancer sans dommage.
#
# CE QUE CE SCRIPT MODIFIE
#   1. /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg  clé du dépôt Gazebo (empreinte vérifiée)
#   2. /etc/apt/sources.list.d/gazebo-stable.list         dépôt apt officiel Gazebo
#   3. Listes apt (apt-get update) et paquets de la liste PAQUETS ci-dessous, sans « recommends ».
#      Simulation du 2026-11-03 : 199 paquets nouveaux, 0 mis à jour, 0 supprimé, aucun paquet ros-*.
#
# CE QU'IL NE FAIT PAS (contrairement à Tools/setup/ubuntu.sh de PX4, volontairement non utilisé)
#   - pas de pip : ubuntu.sh lance « python3 -m pip install --break-system-packages », ce qui
#     écrirait dans ~/venv_stage (actif par défaut) ou dans le Python système. Les modules Python
#     iront dans un venv dédié, ~/drone-tools/venv-px4, créé sans sudo.
#   - pas de chaîne NuttX (cartes de vol réelles), pas de compilateur Xtensa dans /opt,
#     pas d'écriture dans ~/.bashrc ou ~/.profile.
#   - pas de usermod : le compte est déjà dans le groupe dialout.
#   - ModemManager n'est ni masqué ni supprimé : la doc QGroundControl le présente comme facultatif,
#     et il ne gêne que les liaisons série, pas le SITL qui passe par UDP.
#   - pas de redémarrage requis.
#
# SÉCURITÉ ROS 2 : avant l'installation réelle, le script simule apt et s'arrête sans rien installer
# si un paquet devait être supprimé.
#
# RETOUR ARRIÈRE
#     sudo apt remove gz-harmonic && sudo apt autoremove
#     sudo rm /etc/apt/sources.list.d/gazebo-stable.list /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
#     sudo apt-get update
#
# SOURCES
#   https://gazebosim.org/docs/harmonic/install_ubuntu/   (clé, dépôt, paquet)
#   https://docs.px4.io/v1.17/en/dev_setup/dev_env_linux_ubuntu   (Harmonic pour Ubuntu 24.04)
#   PX4-Autopilot v1.17.0, Tools/setup/ubuntu.sh   (liste des paquets, dont cppzmq-dev pour la 24.04)

set -euo pipefail

CLE_URL="https://packages.osrfoundation.org/gazebo.gpg"
CLE_CHEMIN="/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg"
CLE_EMPREINTE="D2486D2DD83DB69272AFE98867170598AF249743"   # « OSRF Repository »
DEPOT_CHEMIN="/etc/apt/sources.list.d/gazebo-stable.list"

PAQUETS=(
	# Compilation de PX4 (sous-ensemble utile au SITL de la liste de ubuntu.sh)
	build-essential cmake git make ninja-build ccache rsync unzip zip file gdb pkg-config bc
	libssl-dev libxml2-dev libxml2-utils python3-dev python3-venv
	# Gazebo Harmonic et dépendances des plugins PX4 (mêmes paquets que ubuntu.sh)
	gz-harmonic libunwind-dev cppzmq-dev protobuf-compiler libeigen3-dev libopencv-dev
	libimage-exiftool-perl
	gstreamer1.0-plugins-bad gstreamer1.0-plugins-base gstreamer1.0-plugins-good
	gstreamer1.0-plugins-ugly gstreamer1.0-libav libgstreamer-plugins-base1.0-dev
	# Dépendances de l'AppImage QGroundControl (doc QGC), déjà présentes : garanties ici
	libfuse2t64 libxcb-xinerama0 libxkbcommon-x11-0 libxcb-cursor0
)

journal() { printf '\n[install_sudo] %s\n' "$*"; }
echec() { printf '\n[install_sudo] ERREUR : %s\n' "$*" >&2; exit 1; }

[[ ${EUID} -eq 0 ]] || echec "à lancer avec sudo : sudo bash $0"

# shellcheck disable=SC1091
. /etc/os-release
[[ "${VERSION_CODENAME:-}" == "noble" ]] || echec "prévu pour Ubuntu 24.04 (noble), trouvé : ${VERSION_CODENAME:-inconnu}"
ARCH="$(dpkg --print-architecture)"

export DEBIAN_FRONTEND=noninteractive

# ---- 1. Clé du dépôt : téléchargée à part, installée seulement si l'empreinte correspond.
journal "Clé du dépôt Gazebo"
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT
curl -fsSL "${CLE_URL}" -o "${TMP}/gazebo.gpg"
# Clés principales seulement (la clé OSRF a aussi une sous-clé) ; plusieurs clés feraient échouer le test.
EMPREINTES="$(gpg --homedir "${TMP}" --show-keys --with-colons "${TMP}/gazebo.gpg" 2>/dev/null | awk -F: '$1=="pub"{p=1;next} p&&$1=="fpr"{print $10;p=0}')"
[[ "${EMPREINTES}" == "${CLE_EMPREINTE}" ]] || echec "empreinte inattendue : ${EMPREINTES}"
install -m 0644 -o root -g root "${TMP}/gazebo.gpg" "${CLE_CHEMIN}"
echo "OK ${CLE_EMPREINTE} -> ${CLE_CHEMIN}"

# ---- 2. Dépôt apt (fichier réécrit à l'identique si déjà présent).
journal "Dépôt apt Gazebo"
echo "deb [arch=${ARCH} signed-by=${CLE_CHEMIN}] https://packages.osrfoundation.org/gazebo/ubuntu-stable noble main" > "${DEPOT_CHEMIN}"
cat "${DEPOT_CHEMIN}"

# ---- 3. Mise à jour des listes. Un dépôt tiers en panne (zoom, etc.) ne doit pas tout bloquer :
#         seul compte le fait que gz-harmonic soit disponible ensuite.
journal "apt-get update"
apt-get update -y --quiet || echo "Attention : apt-get update a signalé une erreur, on vérifie gz-harmonic."
CANDIDAT="$(apt-cache policy gz-harmonic | awk '/Candidate:/{print $2}')"
[[ -n "${CANDIDAT}" && "${CANDIDAT}" != "(none)" ]] || echec "gz-harmonic introuvable après apt-get update"
echo "gz-harmonic candidat : ${CANDIDAT}"

# ---- 4. Simulation : on s'arrête si apt veut supprimer quoi que ce soit.
#         --no-upgrade : les paquets nommés déjà installés (cmake, git...) gardent leur version.
journal "Simulation de l'installation"
apt-get -s --no-install-recommends --no-upgrade install "${PAQUETS[@]}" > "${TMP}/simulation.txt"
SUPPRIMES="$(grep -c '^Remv ' "${TMP}/simulation.txt" || true)"
NOUVEAUX="$(grep -c '^Inst ' "${TMP}/simulation.txt" || true)"
echo "${NOUVEAUX} paquet(s) à installer ou mettre à jour, ${SUPPRIMES} à supprimer."
if [[ "${SUPPRIMES}" != "0" ]]; then
	grep '^Remv ' "${TMP}/simulation.txt" >&2
	echec "apt voudrait supprimer les paquets ci-dessus : rien n'a été installé (voir ROS 2)."
fi

# ---- 5. Installation réelle.
journal "Installation"
apt-get -y --quiet --no-install-recommends --no-upgrade install "${PAQUETS[@]}"

# ---- 6. Vérification finale.
journal "Vérification"
gz sim --version
ninja --version
protoc --version
dpkg-query -W -f='${Package} ${Version}\n' gz-harmonic libgz-sim8-dev libgz-transport13-dev
NB_ROS="$(dpkg-query -W -f='${Package}\n' 'ros-jazzy-*' 2>/dev/null | wc -l)"
echo "Paquets ros-jazzy-* toujours installés : ${NB_ROS}"

journal "Terminé. Vous pouvez relancer l'agent OUTILLEUR."
