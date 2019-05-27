#!/usr/bin/env bash
set -xue -o pipefail -o posix

check_installed() {
    if ! which "$1" 1>/dev/null; then
        echo "[ERROR] You need to install: $1"
        exit 1
    fi
}

check_path() {
    if [ ! -d "$1" ]; then
        echo "[ERROR] Path does not exists: $1"
        exit 1
    fi
}

ensure_path() {
    mkdir -p "$1"
    echo $(realpath "$1")
}

DEFAULT_PROJECTS_PATH=$(ensure_path ~/games/mods/civ6)
PROJECTS_PATH="${VAR1:=$DEFAULT_PROJECTS_PATH}"
MOD_NAME="CQUI_Community-Edition"
GAME_DATA_PATH=$(realpath ~/.local/share/aspyr-media/Sid\ Meier\'s\ Civilization\ VI)
MOD_PATH="${PROJECTS_PATH}/${MOD_NAME}"

echo "Checking game data directory..."
check_path "$GAME_DATA_PATH"

echo "Checking installed packages..."
check_installed python3
check_installed pip3

echo "Installing python3 marisa-trie to user environment..."
pip3 install marisa-trie --user

cd "$PROJECTS_PATH"
rm -rf "$MOD_NAME"
git clone https://github.com/azorej/CQUI_Community-Edition.git
cd "$MOD_NAME"
git checkout linux_fix
./create_linux_symlinks.py -p ArtDefs Assets Integrations -eq
rm -f "${GAME_DATA_PATH}/Mods/${MOD_NAME}" #expects symlink, will fail if meets directory
ln -s "$MOD_PATH" "${GAME_DATA_PATH}/Mods/"
