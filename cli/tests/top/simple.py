top="""
{
  "connectors": {
    "hub1": {
      "connections": {
        "kvm1.eth2": {
          "interface": "kvm1.eth2", 
          "attrs": {
            "lossratio_to": 50.0, 
            "bandwidth_from": 10000.0, 
            "delay_from": 0.0, 
            "capture_to_file": false, 
            "lossratio_from": 50.0, 
            "gateway6": null, 
            "gateway4": null, 
            "capture_filter": "", 
            "bandwidth_to": 10000.0, 
            "delay_to": 0.0, 
            "capture_via_net": false
          }
        }, 
        "prog3.eth0": {
          "interface": "prog3.eth0", 
          "attrs": {
            "delay": 0.0, 
            "lossratio": 0.0, 
            "capture_to_file": false, 
            "bandwidth": 10000.0, 
            "gateway6": null, 
            "gateway4": null, 
            "capture_filter": "", 
            "capture_via_net": false
          }
        }, 
        "openvz2.eth1": {
          "interface": "openvz2.eth1", 
          "attrs": {
            "lossratio_to": 0.0, 
            "bandwidth_from": 10000.0, 
            "delay_from": 0.0, 
            "capture_to_file": false, 
            "lossratio_from": 0.0, 
            "gateway6": null, 
            "gateway4": null, 
            "capture_filter": "", 
            "bandwidth_to": 10000.0, 
            "delay_to": 0.0, 
            "capture_via_net": false
          }
        }
      }, 
      "attrs": {
        "external_access": false, 
        "state": "created", 
        "type": "hub", 
        "name": "hub1", 
        "_pos": "371.7312219132281,279.2482063903265"
      }
    }, 
    "router1": {
      "connections": {
        "kvm1.eth0": {
          "interface": "kvm1.eth0", 
          "attrs": {
            "lossratio_to": 0.0, 
            "bandwidth_from": 10000.0, 
            "delay_from": 0.0, 
            "capture_to_file": false, 
            "lossratio_from": 0.0, 
            "gateway6": "fd01:ab1a:b1ab:1:2:FFFF:FFFF:FFFF/80", 
            "gateway4": "10.1.2.254/24", 
            "capture_filter": "", 
            "bandwidth_to": 10000.0, 
            "delay_to": 0.0, 
            "capture_via_net": false
          }
        }, 
        "prog2.eth0": {
          "interface": "prog2.eth0", 
          "attrs": {
            "delay": 0.0, 
            "lossratio": 0.0, 
            "capture_to_file": false, 
            "bandwidth": 10000.0, 
            "gateway6": "fd01:ab1a:b1ab:1:3:FFFF:FFFF:FFFF/80", 
            "gateway4": "10.1.3.254/24", 
            "capture_filter": "", 
            "capture_via_net": false
          }
        }, 
        "openvz1.eth1": {
          "interface": "openvz1.eth1", 
          "attrs": {
            "lossratio_to": 0.0, 
            "bandwidth_from": 1000.0, 
            "delay_from": 0.0, 
            "capture_to_file": false, 
            "lossratio_from": 0.0, 
            "gateway6": "fd01:ab1a:b1ab:1:1:FFFF:FFFF:FFFF/80", 
            "gateway4": "10.1.1.254/24", 
            "capture_filter": "", 
            "bandwidth_to": 1000.0, 
            "delay_to": 0.0, 
            "capture_via_net": false
          }
        }
      }, 
      "attrs": {
        "external_access": false, 
        "state": "created", 
        "type": "router", 
        "name": "router1", 
        "_pos": "283.62906210229033,282.87548737394656"
      }
    }, 
    "switch1": {
      "connections": {
        "prog1.eth0": {
          "interface": "prog1.eth0", 
          "attrs": {
            "lossratio_to": 0.0, 
            "bandwidth_from": 10000.0, 
            "delay_from": 0.0, 
            "capture_to_file": false, 
            "lossratio_from": 0.0, 
            "gateway6": null, 
            "gateway4": null, 
            "capture_filter": "", 
            "bandwidth_to": 10000.0, 
            "delay_to": 0.0, 
            "capture_via_net": false
          }
        }, 
        "openvz1.eth0": {
          "interface": "openvz1.eth0", 
          "attrs": {
            "lossratio_to": 0.0, 
            "bandwidth_from": 10000.0, 
            "delay_from": 20.0, 
            "capture_to_file": false, 
            "lossratio_from": 0.0, 
            "gateway6": null, 
            "gateway4": null, 
            "capture_filter": "", 
            "bandwidth_to": 10000.0, 
            "delay_to": 20.0, 
            "capture_via_net": false
          }
        }, 
        "openvz2.eth0": {
          "interface": "openvz2.eth0", 
          "attrs": {
            "lossratio_to": 0.0, 
            "bandwidth_from": 10000.0, 
            "delay_from": 0.0, 
            "capture_to_file": false, 
            "lossratio_from": 0.0, 
            "gateway6": null, 
            "gateway4": null, 
            "capture_filter": "", 
            "bandwidth_to": 10000.0, 
            "delay_to": 0.0, 
            "capture_via_net": false
          }
        }
      }, 
      "attrs": {
        "external_access": false, 
        "state": "created", 
        "type": "switch", 
        "name": "switch1", 
        "_pos": "330.21751983360576,362.3420810476748"
      }
    }, 
    "internet": {
      "connections": {
        "kvm1.eth1": {
          "interface": "kvm1.eth1", 
          "attrs": {}
        }
      }, 
      "attrs": {
        "name": "internet", 
        "network_group": "", 
        "_pos": "321.7498714530068,96.27027741727849", 
        "state": "created", 
        "type": "external", 
        "network_type": "internet"
      }
    }
  }, 
  "attrs": {
    "owner": "admin@test", 
    "state": "created", 
    "name": "Topology_1"
  }, 
  "devices": {
    "prog1": {
      "interfaces": {
        "eth0": {
          "attrs": {
            "name": "eth0"
          }
        }
      }, 
      "attrs": {
        "name": "prog1", 
        "args": "ip=10.0.0.3", 
        "hostgroup": null, 
        "_pos": "330,460", 
        "state": "created", 
        "template": "pingable_node-0.1", 
        "type": "prog"
      }
    }, 
    "prog3": {
      "interfaces": {
        "eth0": {
          "attrs": {
            "name": "eth0"
          }
        }
      }, 
      "attrs": {
        "name": "prog3", 
        "args": "ip=10.2.0.2", 
        "hostgroup": null, 
        "_pos": "470,232", 
        "state": "created", 
        "template": "pingable_node-0.1", 
        "type": "prog"
      }
    }, 
    "prog2": {
      "interfaces": {
        "eth0": {
          "attrs": {
            "name": "eth0"
          }
        }
      }, 
      "attrs": {
        "name": "prog2", 
        "args": "ip=10.1.3.1", 
        "hostgroup": null, 
        "_pos": "189,234", 
        "state": "created", 
        "template": "pingable_node-0.1", 
        "type": "prog"
      }
    }, 
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
        "hostgroup": null, 
        "_pos": "324.63314014775955,198.04655380292638", 
        "state": "created", 
        "template": "debian-5.0_glab_x86", 
        "type": "kvm"
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
        "state": "created", 
        "hostgroup": null, 
        "_pos": "415.3253309652951,361.69189514413586", 
        "gateway6": null, 
        "gateway4": null, 
        "root_password": "glabroot", 
        "template": "debian-5.0_glab_x86", 
        "type": "openvz"
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
        "state": "created", 
        "hostgroup": null, 
        "_pos": "239.43011233356827,364.5779393802325", 
        "gateway6": "fd01:ab1a:b1ab:1:1:FFFF:FFFF:FFFF", 
        "gateway4": "10.1.1.254", 
        "root_password": "glabroot", 
        "template": "debian-5.0_glab_x86", 
        "type": "openvz"
      }
    }
  }, 
  "permissions": {
    "admin@test": "owner"
  }
}
"""