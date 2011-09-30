top="""
{
  "connectors": {
    "\u0427\u0443\u0436\u0434\u0438 \u0415\u0437\u0438\u0446\u0438": {
      "connections": {
        "\ufeaa\ufead\ufbfe\ufeb2 \ufeed.eth0": {
          "interface": "\ufeaa\ufead\ufbfe\ufeb2 \ufeed.eth0", 
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
        "\u5916\u56fd\u8a9e\u306e\u5b66\u7fd2\u3068\u6559\u6388.eth0": {
          "interface": "\u5916\u56fd\u8a9e\u306e\u5b66\u7fd2\u3068\u6559\u6388.eth0", 
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
        "\u0e40\u0e23\u0e35\u0e22\u0e19\u0e41\u0e25\u0e30\u0e2a\u0e2d\u0e19\u0e20\u0e32\u0e29\u0e32.eth0": {
          "interface": "\u0e40\u0e23\u0e35\u0e22\u0e19\u0e41\u0e25\u0e30\u0e2a\u0e2d\u0e19\u0e20\u0e32\u0e29\u0e32.eth0", 
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
        }
      }, 
      "attrs": {
        "external_access": false, 
        "state": "started", 
        "type": "switch", 
        "name": "\u0427\u0443\u0436\u0434\u0438 \u0415\u0437\u0438\u0446\u0438", 
        "_pos": "289,216"
      }
    }
  }, 
  "attrs": {
    "owner": "admin@test", 
    "state": "started", 
    "name": "Unicode_Test"
  }, 
  "devices": {
    "\ufeaa\ufead\ufbfe\ufeb2 \ufeed": {
      "interfaces": {
        "eth0": {
          "attrs": {
            "name": "eth0"
          }
        }
      }, 
      "attrs": {
        "name": "\ufeaa\ufead\ufbfe\ufeb2 \ufeed", 
        "args": "ip=10.0.0.2", 
        "hostgroup": null, 
        "_pos": "289,317", 
        "state": "started", 
        "template": "pingable_node-0.1", 
        "type": "prog"
      }
    }, 
    "\u0e40\u0e23\u0e35\u0e22\u0e19\u0e41\u0e25\u0e30\u0e2a\u0e2d\u0e19\u0e20\u0e32\u0e29\u0e32": {
      "interfaces": {
        "eth0": {
          "attrs": {
            "name": "eth0"
          }
        }
      }, 
      "attrs": {
        "name": "\u0e40\u0e23\u0e35\u0e22\u0e19\u0e41\u0e25\u0e30\u0e2a\u0e2d\u0e19\u0e20\u0e32\u0e29\u0e32", 
        "hostgroup": null, 
        "_pos": "192,128", 
        "state": "started", 
        "template": null, 
        "type": "kvm"
      }
    }, 
    "\u5916\u56fd\u8a9e\u306e\u5b66\u7fd2\u3068\u6559\u6388": {
      "interfaces": {
        "eth0": {
          "attrs": {
            "use_dhcp": false, 
            "ip6address": "fd01:ab1a:b1ab:0:3::1/64", 
            "name": "eth0", 
            "ip4address": "10.0.0.3/24"
          }
        }
      }, 
      "attrs": {
        "_notes": "\u5916\u56fd\u8a9e\u306e\u5b66\u7fd2\u3068\u6559\u6388", 
        "name": "\u5916\u56fd\u8a9e\u306e\u5b66\u7fd2\u3068\u6559\u6388", 
        "state": "started", 
        "hostgroup": null, 
        "_pos": "392,130", 
        "gateway6": null, 
        "gateway4": null, 
        "root_password": "glabroot", 
        "template": null, 
        "type": "openvz"
      }
    }
  }, 
  "permissions": {
    "admin@test": "owner"
  }
}
"""