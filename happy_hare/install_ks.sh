#!/bin/bash
#
# ERCF KlipperScreen Happy Hare edition supplemental installer
#
# Copyright (C) 2023  moggieuk#6538 (discord)
#                     moggieuk@hotmail.com
#
# Screen Capture: scrot -s -D :0.0
#
KLIPPER_CONFIG_HOME="${HOME}/klipper_config"
PRINTER_DATA_CONFIG_HOME="${HOME}/printer_data/config"

declare -A PIN 2>/dev/null || {
    echo "Please run this script with ./bash $0"
    exit 1
}

# Screen Colors
OFF='\033[0m'             # Text Reset
BLACK='\033[0;30m'        # Black
RED='\033[0;31m'          # Red
GREEN='\033[0;32m'        # Green
YELLOW='\033[0;33m'       # Yellow
BLUE='\033[0;34m'         # Blue
PURPLE='\033[0;35m'       # Purple
CYAN='\033[0;36m'         # Cyan
WHITE='\033[0;37m'        # White

B_RED='\033[1;31m'        # Bold Red
B_GREEN='\033[1;32m'      # Bold Green
B_YELLOW='\033[1;33m'     # Bold Yellow
B_CYAN='\033[1;36m'       # Bold Cyan

INFO="${CYAN}"
EMPHASIZE="${B_CYAN}"
ERROR="${B_RED}"
WARNING="${B_YELLOW}"
PROMPT="${CYAN}"
INPUT="${OFF}"

function nextsuffix {
    local name="$1"
    local -i num=0
    while [ -e "$name.0$num" ]; do
        num+=1
    done
    printf "%s.0%d" "$name" "$num"
}

verify_not_root() {
    if [ "$EUID" -eq 0 ]; then
        echo -e "${ERROR}This script must not run as root"
        exit -1
    fi
}

check_klipper() {
    if [ "$(sudo systemctl list-units --full -all -t service --no-legend | grep -F "klipper.service")" ]; then
        echo -e "${INFO}Klipper service found"
    else
        echo -e "${ERROR}Klipper service not found! Please install Klipper first"
        exit -1
    fi

}

verify_home_dirs() {
    if [ ! -d "${KLIPPER_CONFIG_HOME}" ]; then
        if [ ! -d "${PRINTER_DATA_CONFIG_HOME}" ]; then
            echo -e "${ERROR}Klipper config directory (${KLIPPER_CONFIG_HOME} or ${PRINTER_DATA_CONFIG_HOME}) not found. Use '-c <dir>' option to override"
            exit -1
        fi
        KLIPPER_CONFIG_HOME="${PRINTER_DATA_CONFIG_HOME}"
    fi
}

install_klipper_screen() {
    echo -e "${INFO}Adding KlipperScreen support for ERCF"
    do_install=0
    ks_config="$KLIPPER_CONFIG_HOME/KlipperScreen.conf"
    hh_config="$KLIPPER_CONFIG_HOME/ercf_klipperscreen.conf"

    # Backup old Klippersreen Happy Hare menus
    if [ -f "${hh_config}" ]; then
        next_hh_config="$(nextsuffix "$hh_config")"
        echo -e "${WARNING}Pre upgrade config file moved to ${next_hh_config} for reference"
        mv ${hh_config} ${next_hh_config}
    fi

    # Ensure KlipperScreen.conf includes Happy Hare menus
    cat << EOF > /tmp/KlipperScreen.conf.tmp
# 
# ERCF "Happy Hare edition" menus
#
[include ercf_klipperscreen.conf]

EOF

    if [ -f "${ks_config}" ]; then
        update_section=$(grep -c '\[include ercf_klipperscreen.conf\]' ${ks_config} || true)
        if [ "${update_section}" -eq 0 ]; then
            cat ${ks_config} >> /tmp/KlipperScreen.conf.tmp && cp /tmp/KlipperScreen.conf.tmp ${ks_config}
        else
            echo -e "${INFO}KlipperScreen ERCF include already exists in conf. Skipping install"
        fi
    else
        cp /tmp/KlipperScreen.conf.tmp ${ks_config}
    fi

    echo -e "${INFO}Installing Happy Hare menus..."
    max_gate=$(expr $num_gates - 1)
    cp ${SRCDIR}/menus.conf "${hh_config}"

    for file in `ls ${SRCDIR}/iter*.conf`; do
        token=`basename $file .conf`
        echo -e "    ${INFO}Expanding menu ${token} for ${num_gates} gates"
	expanded=$(for i in $(eval echo "{0..`expr $num_gates - 1`}"); do
            cat ${SRCDIR}/${token}.conf | sed -e "s/{i}/${i}/g"
        done)
        expanded="# Generated menus for each tool/gate...\n${expanded}"
        awk -v r="$expanded" "{gsub(/^ERCF_${token}/,r)}1" "${hh_config}" > /tmp/ercf_klipperscreen.conf.tmp && mv /tmp/ercf_klipperscreen.conf.tmp "${hh_config}"
    done

    # Always ensure images are linked for every style
    for style in `ls -d ${HOME}/KlipperScreen/styles/*/images`; do
        for img in `ls ${SRCDIR}/images`; do
            ln -sf "${SRCDIR}/images/${img}" "${style}/${img}"
        done
    done

    restart_klipperscreen
}

restart_klipperscreen() {
    echo -e "${INFO}Restarting KlipperScreen..."
    sudo systemctl restart KlipperScreen
}

# Force script to exit if an error occurs
set -e
clear

# Find SRCDIR from the pathname of this script
SRCDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/ && pwd )"

while getopts "c:g:" arg; do
    case $arg in
        c) KLIPPER_CONFIG_HOME=${OPTARG};;
        g) num_gates=$OPTARG;;
    esac
done
if [ -z "$num_gates" ]; then
    echo "Must specify the number of gates (selectors) with the -g <num_gates> argument" >&2
    exit 1
fi

verify_not_root
verify_home_dirs
install_klipper_screen

