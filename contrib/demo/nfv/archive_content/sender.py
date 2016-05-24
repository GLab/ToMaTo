#!/usr/bin/python

import socket, thread, time, sys, random,math,getopt,json
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
PORT_RECEIVER= 5001
PORT_COMPRESSOR = 5001

sockets_out = []

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

bandwidth = 100000 #byte/s
packet_size = 1400 #byte
receiver_port = PORT_RECEIVER


try:
    opts, args = getopt.getopt(sys.argv[1:], "hb:r:")
except getopt.GetoptError:
    print 'sender.py -b <bandwidth (kbyte/s)> -r <ip:port-receiver>'
    sys.exit(2)

print "opts: %d" % opts.__len__()
print "argv: %s" % sys.argv
print "opts: %s" % opts
for opt, arg in opts:
    print "opt: %s arg: %s" % (opt,arg)
    if opt == '-h':
        print 'sender.py -b <bandwidth (kbyte/s)>'
        sys.exit()
    if opt == "-b":
        bandwidth = int(arg)*1000
        print "bandwidth set to %d" % bandwidth
    if opt == "-r":
        receiver_ip, receiver_port = arg.split(":")
        print "Receiver: %s:%s" % (receiver_ip, receiver_port)




def create_message(packet_size):
    msg = ""
    c = 1
    while (sys.getsizeof(msg) < packet_size):
        msg += ("%d" % math.pow(2,c)).encode("base64","strict")
        c += 1
    #msg.encode("base64","strict")
    return msg

init_sleeptimer = 0
sleeptimer = 0

sock.sendto("ping",(receiver_ip, 5005))
sock.sendto("ping",(compressor_ip, 5005))

while True:
    t_start = datetime.now()
    send_data = 0

    while send_data < bandwidth:

        payload = create_message(min(packet_size,(bandwidth-send_data)))
        msg = "%d|%d|%s" % (0,bandwidth,payload)
        send_data += sys.getsizeof(msg)
        sock.sendto(msg,(receiver_ip, int(receiver_port)))
        if init_sleeptimer > 0:
            time.sleep((init_sleeptimer/(bandwidth/packet_size))*0.8)

    t_end = datetime.now()
    t_elapsed = t_end - t_start
    if init_sleeptimer == 0 & t_elapsed.seconds < 1:
        init_sleeptimer = 1.0 - (t_elapsed.microseconds * math.pow(10,-6))
    if t_elapsed.seconds < 1:
        sleeptimer = 1.0 - (t_elapsed.microseconds * math.pow(10,-6))
    else:
        print "Could not deliver requested bandwidth. Please try setting a lower bandwidth"
    print "Send %d kbyte/s" % (bandwidth/1000)

    time.sleep(sleeptimer)


