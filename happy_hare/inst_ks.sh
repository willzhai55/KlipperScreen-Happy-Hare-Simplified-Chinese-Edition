#!/bin/bash
KLIPPER_HOME="${HOME}/klipper"
KLIPPER_CONFIG_HOME="${HOME}/klipper_config"
PRINTER_DATA_CONFIG_HOME="${HOME}/printer_data/config"

declare -A PIN 2>/dev/null || {
    echo "Please run this script with ./bash $0"
    exit 1
}

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
    if [ ! -d "${KLIPPER_HOME}" ]; then
        echo -e "${ERROR}Klipper home directory (${KLIPPER_HOME}) not found. Use '-k <dir>' option to override"
        exit -1
    fi
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
    if [ -f "${KLIPPER_CONFIG_HOME}/KlipperScreen.conf" ]; then
        update_section=$(grep -c '# ERCF Happy Hare' \
        ${KLIPPER_CONFIG_HOME}/KlipperScreen.conf || true)
        if [ "${update_section}" -eq 0 ]; then
            next_ks_config="$(nextsuffix "$ks_config")"
            echo -e "${INFO}Pre upgrade config file ${ks_config} moved to ${next_ks_config} for reference"
            cp ${ks_config} ${next_ks_config}
            do_install=1
        else
            echo -e "${INFO}KlipperSreen ERCF menus may already exist - skipping install"
        fi
    else
        echo -e "${WARNING}KlipperScreen.conf not found, will create new one"
        touch ${KLIPPER_CONFIG_HOME}/KlipperScreen.conf
        do_install=1
    fi

    if [ "${do_install}" -eq 1 ]; then
        max_gate=$(expr $num_gates - 1)
        cp ${SRCDIR}/menus.conf /tmp/KlipperScreen.hh
        cat ${KLIPPER_CONFIG_HOME}/KlipperScreen.conf >> /tmp/KlipperScreen.hh && mv /tmp/KlipperScreen.hh ${KLIPPER_CONFIG_HOME}/KlipperScreen.conf

        for file in `ls ${SRCDIR}/iter*.conf`; do
            token=`basename $file .conf`
            expanded=$(for i in {0..8..1}; do
                cat ${SRCDIR}/${token}.conf | sed -e "s/{i}/${i}/g"
            done)
            expanded="# Generated menus for each tool/gate..\n${expanded}"
            awk -v r="$expanded" "{gsub(/^ERCF_${token}/,r)}1" "${KLIPPER_CONFIG_HOME}/KlipperScreen.conf" > /tmp/KlipperScreen.hh && mv /tmp/KlipperScreen.hh "${KLIPPER_CONFIG_HOME}/KlipperScreen.conf"
        done
    fi

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

num_gates=9
while getopts "g" arg; do
    case $arg in
        g) num_gates=$OPTARG;;
    esac
done

verify_not_root
verify_home_dirs
install_klipper_screen

