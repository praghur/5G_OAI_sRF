#!/usr/bin/python

tourDescription = """
### OAI 5G E2E with Simulated RF

This profile deploys a single compute node with an image that includes
docker, docker-compose, tshark, oai-cn5g-fed v1.2.1, and docker images for all
of the OAI 5G core network functions. It was originally used for the OAI Fall
2021 Workshop RAN Lab hands-on sessions. The associated slides and instructions
for this session, which show how to download, build, and run OAI 5G RAN
alongside the OAI 5GCN, can be found at:

https://gitlab.flux.utah.edu/powderrenewpublic/oai_fall_2021_workshop.

Some of these instructions have been reproduced below, with adjustments for
logging into the associated node directly, as opposed to using the browser-based
VNC client that workshop participants used.

"""

tourInstructions = """

Note: After you instantiate your experiment, you have to wait until the POWDER
portal shows your experiment status in green as "Your experiment is ready!"
before proceeding.

### Build OAI RAN

Log into `node` and clone the OAI repository. Note that we are using a local
mirror of the OAI repository and only making a shallow clone of a specific
branch in order to speed up the cloning process.

```
bash
# We will use a dedicated tag since one package is sometimes difficult to install
git clone --branch 2021.w46-powder --depth 1 https://gitlab.flux.utah.edu/powder-mirror/openairinterface5g ~/openairinterface5g
```

Next, install dependencies and build OAI:

```
cd ~/openairinterface5g
source oaienv
cd cmake_targets/

# Even if we won't be using USRP in this experiment, let's install UHD
export BUILD_UHD_FROM_SOURCE=True
export UHD_VERSION=3.15.0.0

# The next command takes around 8 minutes
# This command SHALL be done ONCE in the life of your server
./build_oai -I -w USRP

# Let's build now the gNB and nrUE soft modems
# The next command takes around 6 minutes
./build_oai --gNB --nrUE -w SIMU --build-lib nrscope --ninja
```

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
cd ~/openairinterface5g/cmake_targets
sudo RFSIMULATOR=server ./ran_build/build/nr-softmodem --rfsim --sa \
    -O /local/repository/etc/gnb.conf
```

The `gNB` options are:
*  `--rfsim` to indicate no real Radio Equipement will be used and RF simulation will transport IQ samples though Ethernet link
*  `--sa` to indicate `STANDALONE` mode. If omitted, the gNB would be running in `NON-STANDALONE` mode (Currently not available w/ RF sim)

Optionally, if your remote host supports X-forwarding, and you've started this
SSH session with X-forwarding enabled, you can add the `-d` to start the gNB NR
scope.

Note: the configuration file is just a copy of
`~/openairinterface5g/targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb.sa.band78.fr1.106PRB.usrpb210.conf`
that has been adjusted to use the tracking area code and mobile network code
that the minimal OAI 5G core network deployment expects.

You will notice the gNodeB connecting to the AMF if you are watching oai-amf
log. Also, if you passed the `-d` flag, the gNodeB soft-scope will open up and
start showing various plots.

### Start the UE

In yet another terminal session on `node`, run the UE using the configuration file
provided by the profile:

```
cd ~/openairinterface5g/cmake_targets
sudo RFSIMULATOR=127.0.0.1 ./ran_build/build/nr-uesoftmodem -r 106 --numerology 1 --band 78 -C 3619200000 \
   --rfsim --sa --nokrnmod -O /local/repository/etc/ue.conf
```

Note that some options are very similar to the `LTE-UE`:
*  `-r` for the number of resource blocks
*  `--band` to specify the band to operate
*  `-C` to specify the central carrier frequency

Again, you can pass the `-d` option if you are using X-forwarding.

Note: the UE configuration file sets various credentials (IMSI, Ki, OPC, etc) to
match records that exist in the minimal OAI 5G core network deployment.

The UE will associate with the network, as indicated by log output from the AMF,
gNodeB, and UE processes, and the UE soft-scope will open up showing various
plots if you have passed the `-d` flag.

### Generate some traffic

You can generate some traffic by pinging the external data network service that
gets deployed along with the OAI 5G core network functions:

```
ping -I oaitun_ue1 192.168.70.135
PING 192.168.70.135 (192.168.70.135) from 12.1.1.129 oaitun_ue1: 56(84) bytes of data.
64 bytes from 192.168.70.135: icmp_seq=1 ttl=63 time=15.2 ms
64 bytes from 192.168.70.135: icmp_seq=2 ttl=63 time=24.3 ms
64 bytes from 192.168.70.135: icmp_seq=3 ttl=63 time=34.3 ms
64 bytes from 192.168.70.135: icmp_seq=4 ttl=63 time=64.5 ms
64 bytes from 192.168.70.135: icmp_seq=5 ttl=63 time=87.0 ms
64 bytes from 192.168.70.135: icmp_seq=6 ttl=63 time=22.6 ms
64 bytes from 192.168.70.135: icmp_seq=7 ttl=63 time=35.9 ms
64 bytes from 192.168.70.135: icmp_seq=8 ttl=63 time=73.6 ms
64 bytes from 192.168.70.135: icmp_seq=9 ttl=63 time=9.55 ms
64 bytes from 192.168.70.135: icmp_seq=10 ttl=63 time=17.4 ms
64 bytes from 192.168.70.135: icmp_seq=11 ttl=63 time=25.4 ms
64 bytes from 192.168.70.135: icmp_seq=12 ttl=63 time=52.7 ms
^C
--- 192.168.70.135 ping statistics ---
12 packets transmitted, 12 received, 0% packet loss, time 11011ms
rtt min/avg/max/mdev = 9.555/38.573/87.065/24.059 ms
```

Note that if you ping the container directly, the `Round-Trip-Time (RTT)` is
much smaller:

```
ping -c 5 192.168.70.135
PING 192.168.70.135 (192.168.70.135) 56(84) bytes of data.
64 bytes from 192.168.70.135: icmp_seq=1 ttl=64 time=0.066 ms
64 bytes from 192.168.70.135: icmp_seq=2 ttl=64 time=0.060 ms
64 bytes from 192.168.70.135: icmp_seq=3 ttl=64 time=0.063 ms
64 bytes from 192.168.70.135: icmp_seq=4 ttl=64 time=0.051 ms
64 bytes from 192.168.70.135: icmp_seq=5 ttl=64 time=0.053 ms

--- 192.168.70.135 ping statistics ---
5 packets transmitted, 5 received, 0% packet loss, time 4089ms
rtt min/avg/max/mdev = 0.051/0.058/0.066/0.010 ms
```

**It is the proof that the 1st traffic test went trough the whole OAI stack!**

"""


import geni.portal as portal
import geni.rspec.pg as rspec
import geni.urn as URN
import geni.rspec.igext as IG
import geni.rspec.emulab.pnext as PN

request = portal.context.makeRequestRSpec()

node = request.RawPC( "node" )
node.hardware_type = "d430"
node.disk_image = "urn:publicid:IDN+emulab.net+image+OAI2021FallWS:oai-cn5g-docker"

tour = IG.Tour()
tour.Description(IG.Tour.MARKDOWN, tourDescription)
tour.Instructions(IG.Tour.MARKDOWN, tourInstructions)
request.addTour(tour)

portal.context.printRequestRSpec()
