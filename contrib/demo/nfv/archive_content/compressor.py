#!/usr/bin/python

from __future__ import division
import socket, thread, time, sys, random, math
import StringIO
import gzip
import json

from datetime import datetime

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
PORT_RECEIVER = 5001
PORT_COMPRESSOR = 5001


sockets_out = []

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(None)
sock.bind(("0.0.0.0", PORT_COMPRESSOR))

sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_out.settimeout(None)

bandwidth_measured = 0.0

t_start = datetime.now()
data_rcvd = 0
output_data = 0
message_uc = ""


sock.sendto("ping",(sender_ip, 5005))
sock.sendto("ping",(receiver_ip, 5005))

while True:
    (msg, src) = sock.recvfrom(65536)
    ip = src[0]
    msg_c = msg

    compressed, bandwidth_source, msg = msg.split("|")

    if not int(compressed):
        msg_c = msg.encode("zlib")
        msg_c = "%d|%d|%s" % (1,int(bandwidth_source),msg_c)
        output_data += sys.getsizeof(msg_c)
    else:
        print "msg already compressed"
    #msg_uc = msg_c.decode("zlib")

    sock_out.sendto(msg_c,(ip,PORT_RECEIVER))

    t_received = datetime.now()
    t_elapsed = t_received - t_start

    if t_elapsed.seconds >= 1:
        print ("Input bandwidth: %s Output bandwidth: %s" % (int(bandwidth_source)/1000,output_data/1000))
        output_data = 0
        t_start = datetime.now()


