#!/bin/bash
set -x
while true; do
    if ! ip a | grep --quiet oaitun_ue1; then
        /local/repository/bin/deploy-and-start.sh
    else
        if ! ping -c1 -I oaitun_ue1 192.168.70.135 &>/dev/null; then
            /local/repository/bin/deploy-and-start.sh
        fi
        sleep 5
    fi
done



