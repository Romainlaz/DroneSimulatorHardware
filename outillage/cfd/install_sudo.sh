#!/usr/bin/env bash
# =============================================================================
# install_sudo.sh : installe OpenFOAM v2512 (openfoam.com) et ParaView.
#
#   Vérifier sans rien modifier (sans sudo) : bash install_sudo.sh --dry-run
#   Installer                               : sudo bash install_sudo.sh
#
# CE QUE LE SCRIPT MODIFIE (rien d'autre) :
#   - ajoute /etc/apt/keyrings/openfoam-com.gpg
#     (clé du dépôt, empreinte contrôlée, valable pour ce seul dépôt) ;
#   - ajoute /etc/apt/sources.list.d/openfoam-com.list ;
#   - installe openfoam2512-default et paraview avec leurs dépendances
#     (environ 240 Mo à télécharger, 1,2 Go sur le disque).
#
# PRÉCAUTIONS POUR ROS 2 JAZZY :
#   - jamais de python3-paraview : il déclare « Conflicts: python3-vtk9 » et
#     apt retirerait ros-jazzy-desktop (constaté en simulation) ;
#   - --no-install-recommends : évite cette recommandation, ainsi que
#     openfoam-selector, qui pose un script dans /etc/profile.d ;
#   - l'installation s'arrête avant toute action si apt prévoit de retirer un
#     paquet, et --no-remove le lui interdit de toute façon.
#
# Le script ne touche ni ~/.bashrc, ni /etc/profile.d, ni l'environnement ROS.
# Il peut être relancé : le résultat est le même.
#
# POUR DÉSINSTALLER :
#   sudo apt-get purge 'openfoam2512*' paraview && sudo apt-get autoremove --dry-run
#   sudo rm /etc/apt/sources.list.d/openfoam-com.list /etc/apt/keyrings/openfoam-com.gpg
#   (relire la liste de autoremove avant de la lancer pour de bon)
# =============================================================================
set -euo pipefail

PAQUETS="openfoam2512-default paraview"
# Variable réservée au test du garde-fou, en --dry-run uniquement.
PAQUETS_TEST="${PAQUETS_TEST:-}"

CLE_URL="https://dl.openfoam.com/pubkey.gpg"
CLE_EMPREINTE="DC93C096174122E256DA24063386DD74948D208F"
CLE_FICHIER="/etc/apt/keyrings/openfoam-com.gpg"
DEPOT_URL="https://dl.openfoam.com/repos/deb"
DEPOT_FICHIER="/etc/apt/sources.list.d/openfoam-com.list"
ATTENTE_VERROU=900   # secondes d'attente si un autre apt est en cours

DRY=0
case "${1:-}" in
    --dry-run) DRY=1 ;;
    "")        ;;
    *) echo "Usage : sudo bash $0   |   bash $0 --dry-run" >&2; exit 2 ;;
esac

info()   { printf '\n==> %s\n' "$*"; }
erreur() { printf '\nERREUR : %s\n' "$*" >&2; exit 1; }

# --- 1. Contrôles préalables, sans aucune modification -----------------------
if [ "$DRY" = 0 ] && [ "$(id -u)" -ne 0 ]; then
    erreur "à lancer avec : sudo bash $0   (ou --dry-run pour vérifier sans sudo)"
fi

# shellcheck disable=SC1091
. /etc/os-release
[ "${UBUNTU_CODENAME:-}" = "noble" ] || erreur "prévu pour Ubuntu 24.04 (noble), trouvé : ${PRETTY_NAME:-?}"
[ "$(dpkg --print-architecture)" = "amd64" ] || erreur "prévu pour amd64"

# Une installation inachevée (autre agent, autre script) ferait échouer apt.
AUDIT="$(dpkg --audit || true)"
if [ -n "$AUDIT" ]; then
    printf '%s\n' "$AUDIT" | head -20
    erreur "dpkg signale des paquets inachevés. Attendre la fin de l'autre installation, puis relancer."
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# --- 2. Clé du dépôt : téléchargée puis contrôlée avant toute écriture --------
info "Téléchargement et contrôle de la clé du dépôt"
mkdir -m 700 "$TMP/gnupg"
curl -fsSL --max-time 60 "$CLE_URL" -o "$TMP/cle.asc"
gpg --homedir "$TMP/gnupg" --batch --quiet --dearmor --output "$TMP/cle.gpg" "$TMP/cle.asc"
EMPREINTE="$(gpg --homedir "$TMP/gnupg" --batch --with-colons --show-keys "$TMP/cle.gpg" \
             | awk -F: '$1=="fpr"{print $10; exit}')"
[ "$EMPREINTE" = "$CLE_EMPREINTE" ] || erreur "empreinte inattendue : $EMPREINTE (attendu : $CLE_EMPREINTE)"
echo "Empreinte conforme : $EMPREINTE"

# --- 3. Déclaration du dépôt, puis lecture de son index seul ------------------
# Seul l'index de ce dépôt est rafraîchi : une panne d'un autre dépôt de la
# machine ne bloque donc pas l'installation et les autres index ne changent pas.
if [ "$DRY" = 1 ]; then
    info "Mode --dry-run : état apt privé dans un dossier temporaire, système inchangé"
    mkdir -p "$TMP/listes/partial" "$TMP/cache/archives/partial"
    cp -r /var/lib/apt/lists/. "$TMP/listes/" 2>/dev/null || true
    LIGNE="deb [arch=amd64 signed-by=$TMP/cle.gpg] $DEPOT_URL noble main"
    SOURCE="$TMP/openfoam-com.list"
    APT_OPTS=(-o "Dir::State::lists=$TMP/listes" -o "Dir::Cache=$TMP/cache"
              -o Debug::NoLocking=1 -o "Dir::Etc::sourcelist=$SOURCE")
    MAJ_SOURCE=("${APT_OPTS[@]}" -o Dir::Etc::sourceparts=- -o APT::Get::List-Cleanup=0)
else
    info "Ajout du dépôt et de sa clé"
    install -d -m 755 /etc/apt/keyrings
    install -m 644 "$TMP/cle.gpg" "$CLE_FICHIER"
    LIGNE="deb [arch=amd64 signed-by=$CLE_FICHIER] $DEPOT_URL noble main"
    SOURCE="$DEPOT_FICHIER"
    APT_OPTS=(-o "DPkg::Lock::Timeout=$ATTENTE_VERROU")
    MAJ_SOURCE=("${APT_OPTS[@]}" -o "Dir::Etc::sourcelist=$SOURCE"
                -o Dir::Etc::sourceparts=- -o APT::Get::List-Cleanup=0)
fi
printf '# OpenFOAM (openfoam.com) : ajouté par outillage/cfd/install_sudo.sh\n%s\n' "$LIGNE" > "$SOURCE"
[ "$DRY" = 1 ] || chmod 644 "$SOURCE"

info "Lecture de l'index du dépôt OpenFOAM"
apt-get "${MAJ_SOURCE[@]}" update

# --- 4. Garde-fou : simulation, arrêt si apt veut retirer quoi que ce soit ----
LISTE="$PAQUETS"
[ "$DRY" = 1 ] && [ -n "$PAQUETS_TEST" ] && LISTE="$PAQUETS $PAQUETS_TEST"

info "Simulation : $LISTE"
# shellcheck disable=SC2086
apt-get "${APT_OPTS[@]}" -s --no-install-recommends install $LISTE > "$TMP/simulation.txt" 2>&1 || {
    cat "$TMP/simulation.txt"
    erreur "la simulation apt a échoué, rien n'a été installé."
}
grep -E 'upgraded,' "$TMP/simulation.txt" || true
if grep -q '^Remv ' "$TMP/simulation.txt"; then
    grep '^Remv ' "$TMP/simulation.txt"
    erreur "apt prévoit de retirer les paquets ci-dessus. Arrêt, rien n'a été installé."
fi
# « Inst nom [version actuelle] » désigne une mise à niveau d'un paquet présent.
if grep -E '^Inst [^ ]+ \[' "$TMP/simulation.txt" | grep -E '^Inst ros-'; then
    erreur "apt prévoit de mettre à niveau des paquets ROS ci-dessus. Arrêt, rien n'a été installé."
fi
echo "Aucun paquet retiré, aucun paquet ROS mis à niveau."

if [ "$DRY" = 1 ]; then
    info "Fin du --dry-run : rien n'a été modifié sur le système."
    exit 0
fi

# --- 5. Installation ----------------------------------------------------------
info "Installation (attente possible si un autre apt tourne, $ATTENTE_VERROU s maximum)"
ROS_AVANT="$(dpkg-query -W -f='${Status}' ros-jazzy-desktop 2>/dev/null || true)"
# shellcheck disable=SC2086
DEBIAN_FRONTEND=noninteractive apt-get "${APT_OPTS[@]}" -y --no-install-recommends --no-remove install $PAQUETS

# --- 6. Contrôle final --------------------------------------------------------
info "Contrôle final"
[ -f /usr/lib/openfoam/openfoam2512/etc/bashrc ] || erreur "OpenFOAM absent de /usr/lib/openfoam/openfoam2512"
command -v paraview >/dev/null || erreur "paraview absent"
ROS_APRES="$(dpkg-query -W -f='${Status}' ros-jazzy-desktop 2>/dev/null || true)"
[ "$ROS_AVANT" = "$ROS_APRES" ] || erreur "état de ros-jazzy-desktop changé : '$ROS_AVANT' -> '$ROS_APRES'"
dpkg-query -W -f='${Package} ${Version}\n' openfoam2512-default paraview
echo "ros-jazzy-desktop : ${ROS_APRES:-non installé}"
info "Terminé. Prévenir l'agent OUTILLEUR pour la suite (icônes et cas de test)."
