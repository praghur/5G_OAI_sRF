#!/usr/bin/python
#TODO: working OTA demo
#

tourDescription = """
## OAI 5G with Simulated RF Hands-on

This profile deploys a single compute node with software for experimenting with
an end-to-end OpenAirInterface5G (OAI) network in standalone mode using a
simulated RF link. The node is provisioned with a VNC server so users can access
the desktop environment of the node in a web browser after instantiation. The
included instructions show how to use shells in a browser-based VNC session to:

1. Start the basic 5G core network functions using docker.
2. Use the RF simulator included with OAI to stand up a single gNodeB/UE pair.
   (IQ samples passed via sockets) and view channel metrics using the gNodeB and
   UE soft scopes.
3. Generate some traffic between the UE and a traffic generation container
   deployed along side the 5G core network functions.
4. Use the channel modeling capabilities of the OAI RF simulator to add noise to
   the channel and witness changes in the constellation diagrams displayed by
   the UE downlink soft scope.

"""

tourInstructions = """

Note: After you instantiate your experiment, you have to wait until the POWDER
portal shows your experiment status in green as "Your experiment is ready!"
before proceeding. This may take a few minutes.

### Open a VNC session to the node in your web browser

**We recommend using Chrome or Firefox. There are known issues with the VNC
apparatus in Safari.**

Once your experiment becomes ready, you should see a green box in the "Topology
View" labeled "node". This box represents the single compute node deployed as
part of the profile. It uses a hard drive image with the OAI RAN and 5G core
network software pre-installed. Click on it to reveal a context menu and
select "Open VNC window". This will open a VNC session to "node" in a second
browser window and there will be a single "xterm" shell on the desktop with a
command prompt.

We will be using several shells during this tutorial. You can create a new shell
at any time by clicking on an empty section of desktop and selecting "XTerm" in
the menu that appears. (If there are windows covering the whole desktop, just
minimize or move them around to reveal an empty spot on the desktop to click on.
You can also hide/reveal windows by clicking on them in the list on the right
side of the desktop.)

There are some commands in the following instructions that are quite long.
Depending on your OS/Browser, you may be able to copy/paste these commands
directly into the VNC shells using the keyboard shortcuts that you are used to.
If direct copy/paste doesn't work (we've found that it doesn't in some cases for
Window/Linux users), you'll need to first paste into the white box at the top of
the VNC window, then focus the VNC shell window you want to paste into and press
`Shift-Insert` to paste into it. Note that on some laptops the `Insert` key may
require the use of a `Func` key as well.

### Start the "minimal" OAI 5G core network deployment

In the first shell, we will use a helper script provided as part of the OAI CN5G
federated repository to deploy a minimal 5G core network (AMF, SMF, UPF, NRF,
and a special container for generating traffic).

```
cd /opt/oai-cn5g-fed/docker-compose
sudo python3 ./core-network.py --type start-mini --fqdn no --scenario 1
```

It will take the `core-network.py` script several seconds to deploy the network
function containers and indicate that they are healthy:

```
...
[2021-11-24 09:39:33,916] root:DEBUG:  AMF, SMF and UPF are registered to NRF....
[2021-11-24 09:39:33,916] root:DEBUG:  Checking if SMF is able to connect with UPF....
[2021-11-24 09:39:34,075] root:DEBUG:  UPF receiving heathbeats from SMF....
[2021-11-24 09:39:34,075] root:DEBUG:  OAI 5G Core network is configured and healthy....
```

Use the same terminal session to follow the logs for the AMF so you can verify
that the UE registers later on:

```
sudo docker logs -f oai-amf
```

You should see output similar to the following:

```
...
[2021-11-24T16:41:33.348997] [AMF] [amf_app] [info ] |----------------------------------------------------UEs' information--------------------------------------------|
[2021-11-24T16:41:33.349004] [AMF] [amf_app] [info ] | Index |      5GMM state      |      IMSI        |     GUTI      | RAN UE NGAP ID | AMF UE ID |  PLMN   |Cell ID|
[2021-11-24T16:41:33.349010] [AMF] [amf_app] [info ] |----------------------------------------------------------------------------------------------------------------|
[2021-11-24T16:41:33.349016] [AMF] [amf_app] [info ]
```

### Start the monolithic gNodeB (i.e., no CU/DU/RU split)

Open another shell (click on an empty section of desktop and select "XTerm"),
and start the monolithic gNodeB using the configuration file provided by the
profile and appropriate parameters:

```
cd /opt/openairinterface5g/cmake_targets
sudo RFSIMULATOR=server ./ran_build/build/nr-softmodem \
  -O /local/repository/etc/gnb.conf \
  -d \
  --sa \
  --rfsim
```

The gNodeB options are:
*  `-O` to pass config file path
*  `-d` to start the gNodeB scope (remote use requires X-forwarding or VNC/similar)
*  `--sa` to use 5G `STANDALONE` mode
*  `--rfsim` to pass baseband IQ samples via sockets rather than real radio hardware

Note: the configuration file is just a copy of
`/opt/openairinterface5g/targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb.sa.band78.fr1.106PRB.usrpb210.conf`
that has been adjusted to use the tracking area code and mobile network code
that the minimal OAI 5G core network deployment expects.

You will notice the gNodeB connecting to the AMF if you are watching oai-amf log
and the gNodeB scope will open up and start showing various plots for the
uplink. There won't be anything interesting happening in the scope yet, since we
haven't started/attached a UE.

### Start the UE

Open another shell and start the UE using the configuration file provided
by the profile and parameters that match the gNodeB configuration:

```
cd /opt/openairinterface5g/cmake_targets
sudo RFSIMULATOR=127.0.0.1 ./ran_build/build/nr-uesoftmodem \
  -O /local/repository/etc/ue.conf \
  -r 106 \
  -C 3619200000 \
  -d \
  --sa \
  --nokrnmod \
  --numerology 1 \
  --band 78 \
  --rfsim \
  --rfsimulator.options chanmod \
  --telnetsrv
```

The `nrUE`-specific options are:
*  `-r` to set the number of resource blocks
*  `-C` to set the center carrier frequency
*  `--nokrnmod` to allow UE process to create interface for PDU session
*  `--numerology` to set 5G numerology (sub-carrer spacing)
*  `--band` to set 3GPP band
*  `--rfsimulator.options` to set simulator options (channel modeling in this case)
*  `--telnetsrv` to start the telnet server at the UE to allow realtime channel model updates

Note: the UE configuration file sets various credentials (IMSI, Ki, OPC, etc) to
match records that exist in the minimal OAI 5G core network deployment and
includes a channel model configuration file for the RF simulator.

The UE will associate with the network, as indicated by log output from the AMF,
gNodeB, and UE processes, and the UE scope will open up showing various plots
for the downlink.

If you look again at the gNodeB scope, you'll notice the plots now indicating
that there is uplink traffic as well, but it is mostly control-plane traffic.

### Generate some traffic

Let's generate some bi-directional user-plane traffic at the UE by pinging the
external data network service that gets deployed along with the OAI 5G core
network functions. Open another shell issue the following command.

```
ping -I oaitun_ue1 192.168.70.135
```

Note that we are telling `ping` to use the network interface associated with the
UE PDU session. You should see output similar to the following:

```
PING 192.168.70.135 (192.168.70.135) from 12.1.1.130 oaitun_ue1: 56(84) bytes of data.
64 bytes from 192.168.70.135: icmp_seq=1 ttl=63 time=40.2 ms
64 bytes from 192.168.70.135: icmp_seq=2 ttl=63 time=34.7 ms
64 bytes from 192.168.70.135: icmp_seq=3 ttl=63 time=43.4 ms
64 bytes from 192.168.70.135: icmp_seq=4 ttl=63 time=37.4 ms
64 bytes from 192.168.70.135: icmp_seq=5 ttl=63 time=39.2 ms
```

Stop the `ping` process with the key combination `ctrl-C`. We'll reuse the same
shell to start an `iperf3` server so we can generate some heavy downlink
traffic:

```
iperf3 -s
```

You should see output like the following:

```
-----------------------------------------------------------
Server listening on 5201
-----------------------------------------------------------
```

Now open another shell and use it to start an `iperf3` client inside the traffic
generation Docker container. We need to point the `iperf3` client at our UE, so
we grab the UE IP address and put it in a variable, then use it in the command
we execute in the Docker container (`oai-ext-dn`).

```
UEIP=$(ip -o -4 addr list oaitun_ue1 | awk '{print $4}' | cut -d/ -f1)
sudo docker exec -it oai-ext-dn iperf3 -c $UEIP -t 50000
```

You should see output similar to the following:

```
Connecting to host 12.1.1.130, port 5201
[  4] local 192.168.70.135 port 41616 connected to 12.1.1.130 port 5201
[ ID] Interval           Transfer     Bandwidth       Retr  Cwnd
[  4]   0.00-1.00   sec  1.17 MBytes  9.79 Mbits/sec    0   76.4 KBytes
[  4]   1.00-2.00   sec  1.30 MBytes  10.9 Mbits/sec    7    100 KBytes
[  4]   2.00-3.00   sec  1.43 MBytes  12.0 Mbits/sec    0    110 KBytes
[  4]   3.00-4.00   sec  1.55 MBytes  13.0 Mbits/sec    0    120 KBytes
[  4]   4.00-5.00   sec  1.55 MBytes  13.0 Mbits/sec    0    129 KBytes
...
```

Now bring the UE scope back into view (window titled "NR DL SCOPE UE 0"). Notice
the changes in the "PDSCH I/Q of MF Output" plot on the UE scope.. the MCS
changes to a higher order QAM (more clusters of dots) and the energy plots in
the upper sections of the scope show more resource blocks being scheduled. There
will probably be 64 clusters apparent (64-QAM).

Note: if you've run into issues getting to this point, you can catch up by
running `nohup /local/repository/bin/restart-all.sh` in any shell. It will take
a few minutes to stop running processes (if necessary), then start them again.

#### Add some AWGN noise to the downlink

Let's leave `iperf3` running and increase the noise the UE sees in the downlink.
To do so, we'll open yet another shell and connect to the telnet server running in
the UE softmodem where we can manipulate the channel model.

```
telnet 127.0.0.1 9090
```

You'll see output like this:

```
Trying 127.0.0.1...
Connected to 127.0.0.1.
Escape character is '^]'.
```

Press `enter` to yield the following prompt:

```
softmodem_5Gue>
```

We can enter

```
channelmod help
```

to see available options. The output will look like this:

```
channelmod commands can be used to display or modify channel models parameters
channelmod show predef: display predefined model algorithms available in oai
channelmod show current: display the currently used models in the running executable
channelmod modify <model index> <param name> <param value>: set the specified parameters in a current model to the given value
                  <model index> specifies the model, the show current model command can be used to list the current models indexes
                  <param name> can be one of "riceanf", "aoa", "randaoa", "ploss", "noise
```

We started with an `AWGN` model with effectively zero noise in the downlink. We
can see the current model by entering

```
channelmod show current
```

which will generate the following output:

```
model 0 rfsimu_channel_enB0 type AWGN:
----------------
model owner: rfsimulator
nb_tx: 1    nb_rx: 1    taps: 1 bandwidth: 0.000000    sampling: 61440000.000000
channel length: 1    Max path delay: 0.000000   ricean fact.: 0.000000    angle of arrival: 0.000000 (randomized:No)
max Doppler: 0.000000    path loss: 0.000000  noise: -100.000000 rchannel offset: 0    forget factor; 0.000000
Initial phase: 0.000000   nb_path: 10
taps: 0   lin. ampli. : 1.000000    delay: 0.000000
model 1 rfsimu_channel_ue0 type AWGN:
----------------
model owner: not set
nb_tx: 1    nb_rx: 1    taps: 1 bandwidth: 0.000000    sampling: 61440000.000000
channel length: 1    Max path delay: 0.000000   ricean fact.: 0.000000    angle of arrival: 0.000000 (randomized:No)
max Doppler: 0.000000    path loss: 0.000000  noise: -100.000000 rchannel offset: 0    forget factor; 0.000000
Initial phase: 0.000000   nb_path: 10
taps: 0   lin. ampli. : 1.000000    delay: 0.000000
```

We'll ignore everything but the noise parameter today. Arrange your windows such
that the UE scope and the telnet prompt are both visible and keep an eye on the
UE scope while we add some noise to the downlink by entering

```
channelmod modify 0 noise_power_dB -15
```

and you'll see the following output from the telnet server indicating the noise
parameters has been updated to -15:

```
model owner: rfsimulator
nb_tx: 1    nb_rx: 1    taps: 1 bandwidth: 0.000000    sampling: 61440000.000000
channel length: 1    Max path delay: 0.000000   ricean fact.: 0.000000    angle of arrival: 0.000000 (randomized:No)
max Doppler: 0.000000    path loss: 0.000000  noise: -15.000000 rchannel offset: 0    forget factor; 0.000000
Initial phase: 0.000000   nb_path: 10
taps: 0   lin. ampli. : 1.000000    delay: 0.000000
```

You'll notice a bit more noise in the "PDSCH I/Q of MF Output" plot (clusters
are little less tight) and the MCS might drop to lower order QAM (fewer
clusters, e.g., from 64 to 16).

Let's make the SNR even worse:

```
channelmod modify 0 noise_power_dB -5
```

Now the MCS is almost guaranteed to drop to 16-QAM or 4-QAM. The downlink
throughput measured by `iperf3` might drop to zero while the gNodeB figures out
that it needs to adjust the MCS to counter the increase in noise.

You can always go back to the setting we started with to remind yourself of the
difference.

```
channelmod modify 0 noise_power_dB -100
```

### Build OAI RAN (optional)

Let's open a shell and use it to kill most of our processes and clean up our
workspace:

```
sudo killall iperf3 nr-uesoftmodem nr-softmodem xterm
```

Open another shell and remove the current build of OAI:

```
sudo rm -rf /opt/openairinterface5g
```

Now, we'll clone a specific tag of the OAI RAN repository:

```
sudo git clone --branch 2022.w32 --depth 1 https://gitlab.flux.utah.edu/powder-mirror/openairinterface5g /opt/openairinterface5g
sudo chown -R $USER:$GROUP /opt/openairinterface5g
```

Next, we setup the build environment:

```
cd /opt/openairinterface5g
source oaienv
```

In general, you would then install dependencies with `cd cmake_targets/;
./build_oai -I`, but we don't need to do this, since they are already installed
on the image used by this profile. So, we move on to the actual build:

```
cd cmake_targets
./build_oai --gNB --nrUE -w SIMU --build-lib all --ninja
```

At this point all of the tutorial steps should work with your fresh OAI build.

"""


import geni.portal as portal
import geni.rspec.pg as rspec
import geni.urn as URN
import geni.rspec.igext as IG
import geni.rspec.emulab.pnext as PN
import geni.rspec.emulab as emulab

pc = portal.Context()
request = portal.context.makeRequestRSpec()

node = request.RawPC( "node" )
node.hardware_type = "d430"
node.disk_image = "urn:publicid:IDN+emulab.net+image+INLWorkshop2022:oai-cn5g-rfsim"
node.startVNC()

tour = IG.Tour()
tour.Description(IG.Tour.MARKDOWN, tourDescription)
tour.Instructions(IG.Tour.MARKDOWN, tourInstructions)
request.addTour(tour)

portal.context.printRequestRSpec()
