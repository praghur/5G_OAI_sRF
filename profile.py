#!/usr/bin/python

tourDescription = """
### MERIF 2023: Teaching 5G with POWDER

This profile is for an educational tutorial session during MERIF 2023. It
deploys a single compute node with an image that includes docker,
docker-compose, tshark, oai-cn5g-fed v1.4.0, and docker images for all of the
OAI 5G core network functions. It also includes source code and a prebuilt
version of the OAI RAN stack (gNB, nrUE, RF simulator). We will show how
profiles like this one can be used in the classroom to explore 5G networks.
While this session won't be a hands-on exercice, attendees will be able to try
it out for themselves after the session, and use it as a starting point for
teaching 5G concepts in their own classrooms. The description and instructions
for this activity can be found
[here](https://gitlab.flux.utah.edu/powderrenewpublic/merif2023/-/blob/main/content/teaching-5g-oai.md).
"""

tourInstructions = """

Note: After you instantiate an experiment, you have to wait until the POWDER
portal shows your experiment status in green as "Your experiment is ready"
before proceeding.


"""


import geni.portal as portal
import geni.rspec.pg as rspec
import geni.urn as URN
import geni.rspec.igext as IG
import geni.rspec.emulab.pnext as PN
import geni.rspec.emulab as emulab

request = portal.context.makeRequestRSpec()

node = request.RawPC( "node" )
node.hardware_type = "d430"
node.disk_image = "urn:publicid:IDN+emulab.net+image+mww2023:oai-cn5g-rfsim"
node.startVNC()

tour = IG.Tour()
tour.Description(IG.Tour.MARKDOWN, tourDescription)
tour.Instructions(IG.Tour.MARKDOWN, tourInstructions)
request.addTour(tour)

portal.context.printRequestRSpec()
