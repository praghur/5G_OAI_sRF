#!/usr/bin/python

"""
A single compute node with an image that includes docker, docker-compose,
tshark, oai-cn5g-fed v1.2.1, and docker images for all of the OAI 5G core
network functions.

For use by OAI Fall 2021 Workshop RAN Lab sessions. Instructions located at:

https://gitlab.flux.utah.edu/powderrenewpublic/oai_fall_2021_workshop

"""

import geni.portal as portal
import geni.rspec.pg as rspec
import geni.urn as URN
import geni.rspec.emulab.pnext as PN

request = portal.context.makeRequestRSpec()

node = request.RawPC( "node" )
node.hardware_type = "d430"
node.disk_image = "urn:publicid:IDN+emulab.net+image+OAI2021FallWS:oai-cn5g-docker"

portal.context.printRequestRSpec()
