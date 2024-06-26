#!/bin/bash
set -ex
export DISPLAY=:1

sudo killall nr-uesoftmodem nr-softmodem iperf3 oai-watchdog.sh || true

cd /opt/oai-cn5g-fed/docker-compose
sudo python3 ./core-network.py --type stop-basic --scenario 1
sudo python3 ./core-network.py --type start-basic --scenario 1

xterm -e bash -c "sudo docker logs -f oai-amf" &
sleep 1
xterm -e bash -c "cd /opt/openairinterface5g/cmake_targets; sudo RFSIMULATOR=server ./ran_build/build/nr-softmodem --rfsim --sa -O /local/repository/etc/gnb1.conf -d" &
sleep 5
xterm -e bash -c "cd /opt/openairinterface5g/cmake_targets; sudo sudo RFSIMULATOR=127.0.0.1 ./ran_build/build/nr-uesoftmodem -r 106 --numerology 3 --band 78 -C 3619200000 --rfsim --sa --nokrnmod -O /local/repository/etc/ue1.conf -d" &
sleep 10
xterm -e bash -c "iperf3 -s" &
sleep 1
UEIP=$(ip -o -4 addr list oaitun_ue1 | awk '{print $4}' | cut -d/ -f1)
xterm -e bash -c "sudo docker exec -it oai-ext-dn iperf3 -c $UEIP -t 50000" &
sleep 2
wmctrl -a "DL SCOPE" && wmctrl -r "DL SCOPE" -e 0,0,0,-1,-1 && wmctrl -a "UL SCOPE" && wmctrl -r "UL SCOPE" -e 0,870,0,-1,-1

nohup /local/repository/bin/oai-watchdog.sh &
