#!/bin/bash
source /local/repository/bin/typer.sh
typer "sudo RFSIMULATOR=server $HOME/openairinterface5g/cmake_targets/ran_build/build/nr-softmodem --rfsim \
--sa -d -O /local/repository/etc/gnb.conf"
