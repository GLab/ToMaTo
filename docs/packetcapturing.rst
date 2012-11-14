Packet Capturing
================

Packet capturing can help to trace packages through the network and analyze communication streams.

ToMaTo capabilities
-------------------

ToMaTo supports capturing of packets on connections on Tinc-based connectors. The capturing can be enabled in the graphical editor in the properties panels of the connections. The captured packets are saved to a rotating set of files holding at most 50 MB of data. The capture files can be downloaded by clicking the "download capture" button in the control panel of the connection.

The timestamp in the capture files do not exactly correspond with the time of sending the packet in the virtual machine since the scheduling might introduce a delay. However the timestamp is guaranteed to be between the time of sending and the time of the forwarding to the connection.

Also note that timestamps from different hosts might have a certain offset, depending on how good the clocks of the hosts are synchronized. In the German-Lab testbed currently no actions are taken to synchronize the clocks among the hosts.


Analysis programs
-----------------

ToMaTo generates capture files in the `pcap format <http://en.wikipedia.org/wiki/Pcap>`_. When downloaded from the hosts multiple capture files are packed into a tar.gz archive.

The capture files created by ToMaTo can be used by a lot different programs:

* `Wireshark <http://www.wireshark.org>`_ - a graphical pcap explorer an analysis tool
* `Cloudshark <http://www.cloudshark.org>`_ - a web-based pcp explorer with a similar UI to Wireshark
* `tcpreplay <http://tcpreplay.synfin.net/>`_ - a Linux tool to replay pcap files