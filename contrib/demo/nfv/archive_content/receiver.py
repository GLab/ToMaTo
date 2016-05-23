#!/usr/bin/python

from __future__ import division
import socket, thread, time, sys, random, math
from datetime import datetime
import json

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


SO_BINDTODEVICE = 25

PORT_SENDER = 5000
PORT_RECEIVER= 5001
PORT_COMPRESSOR = 5001

sockets_out = []

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(None)
sock.bind(("0.0.0.0",PORT_RECEIVER))

bandwidth_measured = 0.0

t_start = datetime.now()
t_bandwidth_low_detected = 0
data_rcvd = 0


sock.sendto("ping",(sender_ip, 5005))
sock.sendto("ping",(compressor_ip, 5005))

while True:
    (msg, src) = sock.recvfrom(65536)
    msg_size = sys.getsizeof(msg)
    data_rcvd += msg_size

    t_received = datetime.now()
    t_elapsed = t_received - t_start

    if t_elapsed.seconds >= 1:
        bandwidth_measured = data_rcvd
        data_rcvd = 0
        t_start = datetime.now()
        compressed, bandwidth_source, msg = msg.split("|",2)
        print "Bandwidth: %d / %d (kbyte/s)    Compressed: %s" % (int(bandwidth_measured)/1000,int(bandwidth_source)/1000,compressed)
        if (int(bandwidth_source)*0.9 > bandwidth_measured):
            if int(compressed) == 0:

                if t_bandwidth_low_detected == 0:
                    t_bandwidth_low_detected = datetime.now()
                    print "Too low Bandwidth detected"
                else:
                    t_bandwidth_low_duration = datetime.now() - t_bandwidth_low_detected
                    if t_bandwidth_low_duration.seconds > 5:
                        print "Too low Bandwidth detected for more than 5 seconds. Sending message"
                        msg = ("%s|%s|%s|%s|%s|%s" % (sender_ip,receiver_ip,compressor_ip,sender_mac,receiver_mac,compressor_mac))
                        sock.sendto(msg,(controller_ip, 5003))
        else:
            t_bandwidth_low_detected = 0



