#!/usr/bin/python

tourDescription = """
## OAI 5G with Simulated RF Hands-on

This profile deploys a single compute node with software for experimenting with
an end-to-end OpenAirInterface5G (OAI) network in standalone mode using a
simulated RF link. The included instructions detail how to:

1. Start the basic 5G core network functions using docker.
2. Use the RF simulator included with OAI to stand up a single gNodeB/UE pair.
   (IQ samples passed via sockets).
3. Generate some traffic between the UE and a traffic generation container
   deployed along side the 5G core network functions.
4. Use the channel modeling capabilities of the RF simulator to add noise to
   the channel and witness changes in the constellation diagrams displayed by
   downlink soft scope.

"""

tourInstructions = """

Note: After you instantiate your experiment, you have to wait until the POWDER
portal shows your experiment status in green as "Your experiment is ready!"
before proceeding.


### Start the "minimal" OAI 5G core network deployment

```
# The next 2 commands are done to make the containers visible from an external server
# You SHALL do these if your EPC containers are not on the same server as your gNB
# Not the case in our experiment. But good practice.
sudo sysctl net.ipv4.conf.all.forwarding=1
sudo iptables -P FORWARD ACCEPT

# Let's deploy now
cd /opt/oai-cn5g-fed/docker-compose
sudo python3 ./core-network.py --type start-mini --fqdn no --scenario 1
```

It will take the `core-network.py` script several seconds to deploy the network
function containers and indicate that they are healthy.

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
...
[2021-11-24T16:41:33.348997] [AMF] [amf_app] [info ] |----------------------------------------------------UEs' information--------------------------------------------|
[2021-11-24T16:41:33.349004] [AMF] [amf_app] [info ] | Index |      5GMM state      |      IMSI        |     GUTI      | RAN UE NGAP ID | AMF UE ID |  PLMN   |Cell ID|
[2021-11-24T16:41:33.349010] [AMF] [amf_app] [info ] |----------------------------------------------------------------------------------------------------------------|
[2021-11-24T16:41:33.349016] [AMF] [amf_app] [info ]
```

### Start the monolithic gNodeB

In another terminal session on `node`, run the monolithic gNodeB using the
configuration file provided by the profile::

```
cd /opt/openairinterface5g/cmake_targets
sudo RFSIMULATOR=server ./ran_build/build/nr-softmodem \
  -O /local/repository/etc/gnb.conf \
  -d \
  --sa \
  --rfsim
```

The `gNodeB` options are:
*  `-O` to pass config file path
*  `-d` to start the gNodeB scope (remote use requires X-forwarding or VNC/similar)
*  `--sa` to use 5G `STANDALONE` mode
*  `--rfsim` to pass baseband IQ samples via sockets rather than real radio hardware

Note: the configuration file is just a copy of
`/opt/openairinterface5g/targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb.sa.band78.fr1.106PRB.usrpb210.conf`
that has been adjusted to use the tracking area code and mobile network code
that the minimal OAI 5G core network deployment expects.

You will notice the gNodeB connecting to the AMF if you are watching oai-amf log
and the gNodeB scope will open up and start showing various plots for the uplink.

### Start the UE

In another terminal on `node`, run the UE using the configuration file provided
by the profile and the following parameters:

```
cd /opt/openairinterface5g/cmake_targets
sudo RFSIMULATOR=127.0.0.1 ./ran_build/build/nr-uesoftmodem \
  -O /local/repository/etc/ue.conf \
  -r 106 \
  -C 3619200000 \
  -d \
  --sa \
  --numerology 1 \
  --band 78 \
  --rfsim \
  --rfsimulator.options chanmod \
  --telnetsrv
```

The `nrUE`-specific options are:
*  `-r` to set the number of resource blocks
*  `-C` to set the center carrier frequency
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

### Generate some traffic

You can generate some traffic by pinging the external data network service that
gets deployed along with the OAI 5G core network functions:

```
ping -I oaitun_ue1 192.168.70.135
```

Let's stress the downlink a bit more using `iperf3` and watch the constellation
diagram change as the modulation and coding scheme (MCS) changes to accomodate
the traffic.

```
# start the server
iperf3 -s

# in another terminal, start the client on the external data network container
# and point it at the UE ip address
UEIP=$(ip -o -4 addr list oaitun_ue1 | awk '{print $4}' | cut -d/ -f1)
sudo docker exec -it oai-ext-dn iperf3 -c $UEIP -t 50000
```

Notice the changes in the plots on the UE scope.. the MCS changes to a higher
order QAM and the energy plots in the upper sections of the scope show more
resource blocks being scheduled.

Let's leave `iperf3` running and increase the noise the UE sees in the downlink.
To do so, we'll use another session to connect to the telnet server running in
the UE softmodem.

```
$ telnet 127.0.0.1 9090
Trying 127.0.0.1...
Connected to 127.0.0.1.
Escape character is '^]'.
```

Press `enter` to yeild the following prompt:

```
$ telnet 127.0.0.1 9090
Trying 127.0.0.1...
Connected to 127.0.0.1.
Escape character is '^]'.

softmodem_5Gue>
```

We can type `channelmod help` to see available options:
Type the `channelmod` help:

```
softmodem_5Gue> channelmod help
channelmod commands can be used to display or modify channel models parameters
channelmod show predef: display predefined model algorithms available in oai
channelmod show current: display the currently used models in the running executable
channelmod modify <model index> <param name> <param value>: set the specified parameters in a current model to the given value
                  <model index> specifies the model, the show current model command can be used to list the current models indexes
                  <param name> can be one of "riceanf", "aoa", "randaoa", "ploss", "noise
```

We started with an `AWGN` model with effectively zero noise in the downlink. We
can see the current model by typeing `channelmod show current`:

```
$ softmodem_5Gue> channelmod show current
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

Keep an eye on the UE scope while we add some noise to the downlink:

```
softmodem_5Gue> channelmod modify 0  noise_power_dB -20
model owner: rfsimulator
nb_tx: 1    nb_rx: 1    taps: 1 bandwidth: 0.000000    sampling: 61440000.000000
channel length: 1    Max path delay: 0.000000   ricean fact.: 0.000000    angle of arrival: 0.000000 (randomized:No)
max Doppler: 0.000000    path loss: 0.000000  noise: -20.000000 rchannel offset: 0    forget factor; 0.000000
Initial phase: 0.000000   nb_path: 10
taps: 0   lin. ampli. : 1.000000    delay: 0.000000
```

You'll notice a bit more noise in the PDSCH and the MCS might drop to lower order QAM.


### Build OAI RAN (optional)

Log into `node` and clone the OAI repository. Note that we are using a local
mirror of the OAI repository and only making a shallow clone of a specific
branch in order to speed up the cloning process.

```
bash
# We will use a dedicated tag since one package is sometimes difficult to install
git clone --branch 2022.w32 --depth 1 https://gitlab.flux.utah.edu/powder-mirror/openairinterface5g ~/openairinterface5g
```

Next, install dependencies and build OAI:

```
cd ~/openairinterface5g
source oaienv
cd cmake_targets/

# include UHD (driver for USRP SDRs) build
export BUILD_UHD_FROM_SOURCE=True
export UHD_VERSION=4.0.0.0

# The next command takes around 8 minutes
# This command SHALL be done ONCE in the life of your server
./build_oai -I -w USRP

# Let's build now the gNB and nrUE soft modems
# The next command takes around 6 minutes
./build_oai --gNB --nrUE -w SIMU --build-lib all --ninja
```


"""


import geni.portal as portal
import geni.rspec.pg as rspec
import geni.urn as URN
import geni.rspec.igext as IG
import geni.rspec.emulab.pnext as PN
import geni.rspec.emulab as emulab

pc = portal.Context()
pc.defineParameter(
    name="auto_deploy",
    description="Deploy and run tutorial commands",
    typ=portal.ParameterType.BOOLEAN,
    defaultValue=True,
    advanced=False
)

params = pc.bindParameters()
request = portal.context.makeRequestRSpec()

node = request.RawPC( "node" )
node.hardware_type = "d430"
node.disk_image = "urn:publicid:IDN+emulab.net+image+INLWorkshop2022:oai-cn5g-rfsim"
node.startVNC()

if params.auto_deploy:
    node.addService(rspec.Execute(shell="bash", command="/local/repository/bin/deploy-and-start.sh"))

tour = IG.Tour()
tour.Description(IG.Tour.MARKDOWN, tourDescription)
tour.Instructions(IG.Tour.MARKDOWN, tourInstructions)
request.addTour(tour)

portal.context.printRequestRSpec()
