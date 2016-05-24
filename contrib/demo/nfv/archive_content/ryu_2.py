# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
An OpenFlow 1.0 L2 learning switch implementation.
"""
import struct, socket, json
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import addrconv
from ryu.ofproto import ofproto_v1_0
from ryu.ofproto import ofproto_v1_0_parser
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import udp
from ryu.lib.packet import arp
from threading import Thread
#from ryu.lib.packet import ether_types


class SimpleSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]
    thread_started = 0

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch, self).__init__(*args, **kwargs)
        self.mac_to_port = {}



    def ipv4_to_int(self,ip):
        """
        Converts human readable IPv4 string to int type representation.
        :param str ip: IPv4 address string w.x.y.z
        :returns: unsigned int of form w << 24 | x << 16 | y << 8 | z
        """
        return struct.unpack("!I", addrconv.ipv4.text_to_bin(ip))[0]

    def add_flow(self, datapath, in_port, dst, actions):
        ofproto = datapath.ofproto

        match = datapath.ofproto_parser.OFPMatch(
            in_port=in_port, dl_dst=haddr_to_bin(dst))

        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, cookie=0,
            command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            priority=ofproto.OFP_DEFAULT_PRIORITY,
            flags=ofproto.OFPFF_SEND_FLOW_REM, actions=actions)
        datapath.send_msg(mod)


    def correct_arp(self, datapath, dst, src, out_port):
        ofproto = datapath.ofproto

        if src in self.mac_to_port[datapath.id]:
            in_port = self.mac_to_port[datapath.id][src]
        else:
            print ("CA: Could not find matching port for %s" % src)
            return

        match = datapath.ofproto_parser.OFPMatch(
            in_port=in_port, dl_src=haddr_to_bin(src), dl_dst=haddr_to_bin(dst), dl_type=2054
        )
        actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, command=ofproto.OFPFC_ADD,
            cookie=0, idle_timeout=0, hard_timeout=0,
            priority=65535,
            flags=ofproto.OFPFF_SEND_FLOW_REM,
            actions=actions)
        self.logger.info("Saving ARP entry from %s to %s", src, dst)
        datapath.send_msg(mod)

    def listen_for_commands(self, datapath):
        ofproto = datapath.ofproto
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(None)
        sock.bind(("0.0.0.0",5003))

        while True:
            (msg, src) = sock.recvfrom(65536)
            src_ip, dst_ip,nf_ip, src_mac, dst_mac,nf_mac = msg.split("|",6)

            print ("LFC: Received message: Src: %s / %s Dst: %s / %s NF: %s / %s" % (src_ip,src_mac,dst_ip, dst_mac, nf_ip, nf_mac))

            print ("LFC: Saving ARP routes:")
            if dst_mac in self.mac_to_port[datapath.id]:
                out_port = self.mac_to_port[datapath.id][dst_mac]
            else:
                print ("CA: Could not find matching port for %s" % dst_mac)
                out_port = ofproto.OFPP_FLOOD
            self.correct_arp(datapath,dst_mac,src_mac,out_port)
            self.correct_arp(datapath,dst_mac,nf_mac,out_port)

            if nf_mac in self.mac_to_port[datapath.id]:
                out_port = self.mac_to_port[datapath.id][nf_mac]
            else:
                print ("CA: Could not find matching port for %s" % nf_mac)
                out_port = ofproto.OFPP_FLOOD
            self.correct_arp(datapath,nf_mac,src_mac,out_port)
            self.correct_arp(datapath,nf_mac,dst_mac,out_port)

            if src_mac in self.mac_to_port[datapath.id]:
                out_port = self.mac_to_port[datapath.id][src_mac]
            else:
                print ("CA: Could not find matching port for %s" % src_mac)
                out_port = ofproto.OFPP_FLOOD
            self.correct_arp(datapath,src_mac,dst_mac,out_port)
            self.correct_arp(datapath,src_mac,nf_mac,out_port)

            if src_mac in self.mac_to_port[datapath.id]:
                in_port = self.mac_to_port[datapath.id][src_mac]
            else:
                print ("LFC: Could not find matching port for %s" % src_mac)

            match = datapath.ofproto_parser.OFPMatch(
                in_port=in_port, dl_type=2048,
                nw_src=self.ipv4_to_int(src_ip), nw_dst=self.ipv4_to_int(dst_ip), nw_proto=17,
                tp_dst=5001
            )

            if nf_mac in self.mac_to_port[datapath.id]:
                out_port = self.mac_to_port[datapath.id][nf_mac]
            else:
                out_port = ofproto.OFPP_FLOOD
                print ("LFC: Could not find matching port for %s" % nf_mac)

            actions = [ofproto_v1_0_parser.OFPActionSetNwDst(self.ipv4_to_int(nf_ip)),
                           ofproto_v1_0_parser.OFPActionSetDlDst(haddr_to_bin(nf_mac)),
                           ofproto_v1_0_parser.OFPActionSetNwSrc(self.ipv4_to_int(dst_ip)),
                           ofproto_v1_0_parser.OFPActionSetDlSrc(haddr_to_bin(dst_mac)),
                           datapath.ofproto_parser.OFPActionOutput(out_port)]
            self.logger.info("LFC: Rerouting from %s to %s Origin: %s", dst_ip, nf_ip, src_ip)
            mod = datapath.ofproto_parser.OFPFlowMod(
                datapath=datapath, match=match, command=ofproto.OFPFC_ADD,
                cookie=0, idle_timeout=0, hard_timeout=0,
                priority=65000,
                flags=ofproto.OFPFF_SEND_FLOW_REM,
                actions=actions)
            datapath.send_msg(mod)

            #Rewriting Source IP and Mac on packages from "Network Function" to Receiver
            if nf_mac in self.mac_to_port[datapath.id]:
                in_port = self.mac_to_port[datapath.id][nf_mac]
            else:
                print ("LFC: Could not find matching port for %s" % nf_mac)

            match = datapath.ofproto_parser.OFPMatch(
                in_port=in_port, dl_type=2048,
                nw_src=self.ipv4_to_int(nf_ip), nw_dst=self.ipv4_to_int(dst_ip), nw_proto=17,
                tp_dst=5001
            )

            if dst_mac in self.mac_to_port[datapath.id]:
                    out_port = self.mac_to_port[datapath.id][dst_mac]
            else:
                out_port = ofproto.OFPP_FLOOD
                print ("LFC: Could not find matching port for %s" % dst_mac)

            actions = [ofproto_v1_0_parser.OFPActionSetNwSrc(self.ipv4_to_int(src_ip)),
                       ofproto_v1_0_parser.OFPActionSetDlSrc(haddr_to_bin(src_mac)),
                       datapath.ofproto_parser.OFPActionOutput(out_port)]
            self.logger.info("LFC: Changing Src Field from %s to %s Target: %s", nf_ip, src_ip, dst_ip)
            mod = datapath.ofproto_parser.OFPFlowMod(
                datapath=datapath, match=match, command=ofproto.OFPFC_ADD,
                cookie=0, idle_timeout=0, hard_timeout=0,
                priority=65000,
                flags=ofproto.OFPFF_SEND_FLOW_REM,
                actions=actions)
            datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto

        #print "open config"
        with open("config.json") as f:
            config = json.load(f)

        sender_ip = config["sender"]["ip"]
        sender_mac = config["sender"]["mac"]
        sender_router_port = config["sender"]["router_if"]

        receiver_ip = config["receiver"]["ip"]
        receiver_mac = config["receiver"]["mac"]
        receiver_router_port = config["receiver"]["router_if"]

        compressor_ip = config["compressor"]["ip"]
        compressor_mac = config["compressor"]["mac"]
        compressor_router_port = config["compressor"]["router_if"]

        controller_ip = config["controller"]["ip"]
        controller_mac = config["controller"]["mac"]
        controller_router_port = config["controller"]["router_if"]
        #print "config loaded"

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        ip = pkt.get_protocol(ipv4.ipv4)
        udp_ = pkt.get_protocol(udp.udp)
        arp_ = pkt.get_protocol(arp.arp)
        #if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            #return
        dst = eth.dst
        src = eth.src
        dst_ip = "10.0.0.0"
        src_ip = "10.0.0.0"
        #print ("Ether: %s" % eth.ethertype)
        #if ip is not None:
        #    print ("ip proto: %s" % ip.proto)
        #    if udp_ is not None:
        #        print ("UDP proto: %s" % udp_.dst_port)
        #    dst_ip = ip.dst
        #    src_ip = ip.src
        #if arp_ is not None:
        #    print ("ARP: %s" % arp_.proto)



        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        self.logger.info("packet in %s %s %s %s %s %s", dpid, src, dst, msg.in_port, dst_ip, src_ip)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = msg.in_port

        #self.mac_to_port[dpid][sender_mac] = sender_router_port
        #self.mac_to_port[dpid][receiver_mac] = receiver_router_port
        #self.mac_to_port[dpid][compressor_mac] = compressor_router_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            self.add_flow(datapath,msg.in_port,dst,actions)
        if arp_ is not None:
            self.correct_arp(datapath,dst, src,out_port)
        #if ip is not None:
            #if ip.proto == 17:
                #if udp_.dst_port == 5001:
                    #self.logger.info("adding flow %s %s %s %s", msg.in_port, dst, dst_ip,src_ip)
                    #self.test_flow_entry(datapath, msg.in_port, dst,src,dst_ip,src_ip, actions, out_port)

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD
        actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port,
            actions=actions, data=data)
        datapath.send_msg(out)

        if self.thread_started == 0:
            t = Thread(target=self.listen_for_commands, args=(datapath,))
            t.start()
            self.thread_started = 1

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def _port_status_handler(self, ev):
        msg = ev.msg
        reason = msg.reason
        port_no = msg.desc.port_no

        ofproto = msg.datapath.ofproto
        if reason == ofproto.OFPPR_ADD:
            self.logger.info("port added %s", port_no)
        elif reason == ofproto.OFPPR_DELETE:
            self.logger.info("port deleted %s", port_no)
        elif reason == ofproto.OFPPR_MODIFY:
            self.logger.info("port modified %s", port_no)
        else:
            self.logger.info("Illeagal port state %s %s", port_no, reason)