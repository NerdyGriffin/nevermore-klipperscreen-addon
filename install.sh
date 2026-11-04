#!/usr/bin/env bash
# Nevermore KlipperScreen Add-On installer
#
# Copyright (C) 2026 NerdyGriffin
#
# This file may be distributed under the terms of the GNU GPLv3 license.

printer_config=$HOME/printer_data/config
klipperscreen_dir=$HOME/KlipperScreen
addon_path=$HOME/nevermore-klipperscreen-addon
branch="main"
uninstall=False
test_mode=False

function show_help() {
  echo "Usage: $0 [-p <printer_config>] [-k <klipperscreen_dir>] [-b <branch>] [-u] [-h]"
  echo "Options:"
  echo "  -p <printer_config>    Printer configuration directory (default: \$HOME/printer_data/config)"
  echo "  -k <klipperscreen_dir> KlipperScreen directory (default: \$HOME/KlipperScreen)"
  echo "  -b <branch>            Git branch of this add-on to use (default: main)"
  echo "  -u                     Uninstall"
  echo "  -t                     Skip the service and clone checks (for testing)"
  echo "  -h                     Show this help message"
}

function checks() {
  if [ "$EUID" -eq 0 ]; then
    echo "[ERROR] This script must not be run as root!"
    exit 1
  fi
  if ! systemctl list-units --full -all -t service --no-legend | grep -Fq 'KlipperScreen.service'; then
    echo "[ERROR] KlipperScreen service not found, please install KlipperScreen first!"
    exit 1
  fi
  if [ ! -d "$klipperscreen_dir/.git" ]; then
    echo "[ERROR] KlipperScreen repository not found at $klipperscreen_dir."
    exit 1
  fi
  if ! grep -q "_load_addons" "$klipperscreen_dir/screen.py"; then
    echo "[ERROR] This KlipperScreen has no add-on loader. Update KlipperScreen to a build newer than v0.4.7 (September 2026)."
    exit 1
  fi
  if [ ! -f "$printer_config/KlipperScreen.conf" ]; then
    echo "[ERROR] KlipperScreen.conf is missing. Expected path: $printer_config/KlipperScreen.conf."
    exit 1
  fi
}

function clone_repo() {
  if [ ! -d "$addon_path/.git" ]; then
    echo "[INFO] Cloning nevermore-klipperscreen-addon..."
    git clone --branch "$branch" https://github.com/NerdyGriffin/nevermore-klipperscreen-addon.git "$addon_path" || exit 1
  else
    echo "[INFO] nevermore-klipperscreen-addon already cloned at $addon_path."
  fi
}

function install_files() {
  mkdir -pv "$klipperscreen_dir/addons"
  ln -sfnv "$addon_path/KlipperScreen/nevermore.py" "$klipperscreen_dir/addons/nevermore.py"
}

function link_icons() {
  local exclude_file="$klipperscreen_dir/.git/info/exclude"
  local exclude_glob="styles/*/images/nevermore-*.svg"
  local icons_dir="$addon_path/KlipperScreen/nevermore_icons"
  for theme_dir in "$klipperscreen_dir"/styles/*/; do
    [ -d "$theme_dir/images" ] || continue
    for stale in "$theme_dir"/images/nevermore-*.svg; do
      [ -L "$stale" ] && [ ! -e "$stale" ] && rm -fv "$stale"
    done
    for icon in "$icons_dir"/*.svg; do
      ln -sfv "$icon" "$theme_dir/images/"
    done
  done
  if ! grep -Fxq "$exclude_glob" "$exclude_file" 2>/dev/null; then
    echo "$exclude_glob" >> "$exclude_file"
  fi
}

function check_enable_addons() {
  if grep -Eq '^(#~# )?enable_addons *[:=] *True' "$printer_config/KlipperScreen.conf"; then
    echo "[INFO] Add-ons are enabled in KlipperScreen.conf."
  else
    echo "[WARN] Add-ons are OFF. Open KlipperScreen Settings, turn on 'Enable Add-ons',"
    echo "       or add 'enable_addons: True' under [main] in $printer_config/KlipperScreen.conf."
  fi
}

function restart_klipperscreen() {
  if [ "$test_mode" == "False" ] && sudo -n systemctl try-restart KlipperScreen 2>/dev/null; then
    echo "[INFO] Restarted KlipperScreen."
  else
    echo "[INFO] Restart KlipperScreen: sudo systemctl restart KlipperScreen"
  fi
}

function uninstall() {
  local exclude_file="$klipperscreen_dir/.git/info/exclude"
  rm -fv "$klipperscreen_dir/addons/nevermore.py"
  for link in "$klipperscreen_dir"/styles/*/images/nevermore-*.svg; do
    [ -L "$link" ] && rm -fv "$link"
  done
  if [ -f "$exclude_file" ]; then
    sed -i '\#^styles/\*/images/nevermore-\*\.svg$#d' "$exclude_file"
  fi
  echo "[INFO] Uninstalled."
  restart_klipperscreen
  exit 0
}

while getopts "p:k:b:uth" arg; do
  case ${arg} in
  p) printer_config=$OPTARG ;;
  k) klipperscreen_dir=$OPTARG ;;
  b) branch=$OPTARG ;;
  u) uninstall=True ;;
  t) test_mode=True ;;
  h) show_help; exit 0 ;;
  *) exit 1 ;;
  esac
done

main() {
  if [ "$uninstall" == "True" ]; then
    uninstall
  fi
  if [ "$test_mode" == "False" ]; then
    checks
    clone_repo
  fi
  install_files
  link_icons
  check_enable_addons
  echo "[INFO] Nevermore KlipperScreen Add-On installed."
  restart_klipperscreen
  echo "[INFO] Install on every host that runs KlipperScreen; the add-on stays idle on printers without [nevermore]."
}

main
