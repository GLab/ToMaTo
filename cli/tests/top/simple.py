top="""
{
  "devices": {
    "kvm1": {
      "interfaces": {
        "eth2": {
          "attrs": {
            "name": "eth2"
          }
        }, 
        "eth1": {
          "attrs": {
            "name": "eth1"
          }
        }, 
        "eth0": {
          "attrs": {
            "name": "eth0"
          }
        }
      }, 
      "attrs": {
        "name": "kvm1", 
        "pos": "324.63314014775955,198.04655380292638", 
        "gateway6": "fd01:ab1a:b1ab:1:2:FFFF:FFFF:FFFF", 
        "gateway4": "10.1.2.254", 
        "template": "", 
        "type": "kvm"
      }
    }, 
    "openvz1": {
      "interfaces": {
        "eth1": {
          "attrs": {
            "use_dhcp": "False", 
            "ip6address": "fd01:ab1a:b1ab:1:1::1/80", 
            "name": "eth1", 
            "ip4address": "10.1.1.1/24"
          }
        }, 
        "eth0": {
          "attrs": {
            "use_dhcp": "False", 
            "ip6address": "fd01:ab1a:b1ab:0:1::1/64", 
            "name": "eth0", 
            "ip4address": "10.0.0.1/24"
          }
        }
      }, 
      "attrs": {
        "name": "openvz1", 
        "gateway4": "10.1.1.254", 
        "pos": "239.43011233356827,364.5779393802325", 
        "gateway6": "fd01:ab1a:b1ab:1:1:FFFF:FFFF:FFFF", 
        "root_password": "glabroot", 
        "template": "", 
        "type": "openvz"
      }
    }, 
    "openvz2": {
      "interfaces": {
        "eth1": {
          "attrs": {
            "use_dhcp": "False", 
            "ip6address": "fd01:ab1a:b1ab:2:1::1/64", 
            "name": "eth1", 
            "ip4address": "10.2.0.1/24"
          }
        }, 
        "eth0": {
          "attrs": {
            "use_dhcp": "False", 
            "ip6address": "fd01:ab1a:b1ab:0:2::1/64", 
            "name": "eth0", 
            "ip4address": "10.0.0.2/24"
          }
        }
      }, 
      "attrs": {
        "name": "openvz2", 
        "pos": "415.3253309652951,361.69189514413586", 
        "root_password": "glabroot", 
        "template": "", 
        "type": "openvz"
      }
    },
    "prog1": {
      "interfaces": {
        "eth0": {
          "attrs": {
            "name": "eth0"
          }
        }
      }, 
      "attrs": {
        "args": "ip=10.0.0.3", 
        "name": "prog1", 
        "pos": "330,460", 
        "template": "pingable_node-0.1", 
        "type": "prog"
      }
    }
  }, 
  "connectors": {
    "switch1": {
      "connections": {
        "openvz1.eth0": {
          "attrs": {
            "interface": "openvz1.eth0", 
            "delay": "20", 
            "bandwidth": "10000",
            "lossratio": "0.0"
          }
        }, 
        "openvz2.eth0": {
          "attrs": {
            "interface": "openvz2.eth0", 
            "latency": "0",
            "bandwidth": "10000",
            "lossratio": "0.0"
          }
        },
		"prog1.eth0": {
		  "attrs": {
			"interface": "prog1.eth0", 
			"latency": "0",
			"bandwidth": "10000",
			"lossratio": "0.0"
		  }
		}
      }, 
      "attrs": {
        "type": "switch", 
        "name": "switch1", 
        "pos": "330.21751983360576,362.3420810476748"
      }
    }, 
    "router1": {
      "connections": {
        "kvm1.eth0": {
          "attrs": {
  		    "interface": "kvm1.eth0", 
            "gateway6": "fd01:ab1a:b1ab:1:2:FFFF:FFFF:FFFF/80", 
            "gateway4": "10.1.2.254/24", 
            "latency": "0",
            "bandwidth": "10000",
            "gateway4": "10.1.2.254/24",
            "lossratio": "0.0"
          }
        }, 
        "openvz1.eth1": {
          "attrs": {
		    "interface": "openvz1.eth1", 
            "gateway6": "fd01:ab1a:b1ab:1:1:FFFF:FFFF:FFFF/80", 
            "gateway4": "10.1.1.254/24", 
            "bandwidth": "1000", 
            "latency": "0",
            "lossratio": "0.0"
          }
        }
      }, 
      "attrs": {
        "type": "router", 
        "name": "router1", 
        "pos": "283.62906210229033,282.87548737394656"
      }
    }, 
    "hub1": {
      "connections": {
        "kvm1.eth2": {
          "attrs": {
		    "interface": "kvm1.eth2", 
            "latency": "0",
            "bandwidth": "10000",
            "lossratio": "0.0"
          }
        }, 
        "openvz2.eth1": {
          "attrs": {
		    "interface": "openvz2.eth1", 
            "capture": "True", 
            "latency": "0",
            "bandwidth": "10000",
            "lossratio": "0.5"
          }
        }
      }, 
      "attrs": {
        "type": "hub", 
        "name": "hub1", 
        "pos": "371.7312219132281,279.2482063903265"
      }
    }, 
    "internet": {
      "connections": {
        "kvm1.eth1": {
          "attrs": {
		    "interface": "kvm1.eth1" 
          }
        }
      }, 
      "attrs": {
        "name": "internet", 
        "network_group": "", 
        "pos": "321.7498714530068,96.27027741727849", 
        "type": "external", 
        "network_type": "internet"
      }
    }
  }, 
  "attrs": {
    "name": "Topology_1"
  }
}
"""