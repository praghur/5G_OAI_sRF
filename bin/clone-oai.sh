#!/bin/bash
source /local/repository/bin/typer.sh
typer "sudo rm -rf /opt/openairinterface5g"
typer "sudo git clone --branch develop --depth 1 https://gitlab.flux.utah.edu/powder-mirror/openairinterface5g /opt/openairinterface5g"
typer "sudo chown -R $USER:$GROUP /opt/openairinterface5g"
