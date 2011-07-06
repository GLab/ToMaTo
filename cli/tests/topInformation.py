from lib.misc import *
import time, os, socket

def simpleTop_checkTopInformation(topId):
	#make sure topology is started
	task = top_action(topId, "start")
	waitForTask(task, assertSuccess=True)

	expected = {
		'finished_task': None,
		'capabilities': {
			'action': {
				'prepare': True,
				'stop': True, 
				'remove': True, 
				'start': True, 
				'renew': True, 
				'destroy': True
			},
			'modify': True,
			'permission_set': True
		},
		'connectors': {
			'switch1': {
				'connections': {
					'openvz1.eth0': {
						'interface': 'openvz1.eth0',
						'attrs': {
							'gateway6': None,
							'lossratio': 0.0,
							'bridge_id': None,
							'capture_to_file': False,
							'gateway4': None,
							'delay': 20,
							'bandwidth': 10000,
							'tinc_port': None,
							'capture_filter': '',
							'capture_via_net': False
						},
						'capabilities': {
							'action': {
								'download_capture': False
							},
							'other': {
								'live_capture': False
							},
							'configure': {
								'gateway6': False,
								'lossratio': True,
								'capture_to_file': True,
								'gateway4': False,
								'delay': True,
								'bandwidth': True,
								'capture_filter': True,
								'capture_via_net': True
							}
						}
					},
					'openvz2.eth0': {
						'interface': 'openvz2.eth0',
						'attrs': {
							'gateway6': None,
							'lossratio': 0.0,
							'bridge_id': None,
							'capture_to_file': False,
							'gateway4': None,
							'delay': 0,
							'bandwidth': 10000,
							'tinc_port': None,
							'capture_filter': '',
							'capture_via_net': False
						},
						'capabilities': {
							'action': {
								'download_capture': False
							},
							'other': {
								'live_capture': False
							},
							'configure': {
								'gateway6': False, 
								'lossratio': True, 
								'capture_to_file': True, 
								'gateway4': False, 
								'delay': True, 
								'bandwidth': True, 
								'capture_filter': True, 
								'capture_via_net': True
							}
						}
					}
				},
				'resources': None, 
				'attrs': {
					'state': 'started',
					'type': 'switch',
					'name': 'switch1', 
					'pos': None
				},
				'capabilities': {
					'action': {
						'start': False,
						'download_capture': True,
						'stop': True,
						'prepare': False,
						'destroy': False
					},
					'configure': {
						'pos': True
					}
				}
			}, 
			'router1': {
				'connections': {
					'kvm1.eth0': {
						'interface': 'kvm1.eth0',
						'attrs': {
							'gateway6': 'fd01:ab1a:b1ab:1:2:FFFF:FFFF:FFFF/80',
							'lossratio': 0.0,
							'bridge_id': None,
							'capture_to_file': False,
							'gateway4': '10.1.2.254/24',
							'delay': 0,
							'bandwidth': 10000,
							'tinc_port': None,
							'capture_filter': '',
							'capture_via_net': False
						},
						'capabilities': {
							'action': {
								'download_capture': False
							},
							'other': {
								'live_capture': False
							},
							'configure': {
								'gateway6': False,
								'lossratio': True,
								'capture_to_file': True,
								'gateway4': False,
								'delay': True,
								'bandwidth': True,
								'capture_filter': True,
								'capture_via_net': True
							}
						}
					},
					'openvz1.eth1': {
						'interface': 'openvz1.eth1',
						'attrs': {
							'gateway6': 'fd01:ab1a:b1ab:1:1:FFFF:FFFF:FFFF/80',
							'lossratio': 0.0,
							'bridge_id': None,
							'capture_to_file': False,
							'gateway4': '10.1.1.254/24',
							'delay': 0,
							'bandwidth': 1000,
							'tinc_port': None,
							'capture_filter': '',
							'capture_via_net': False
						},
						'capabilities': {
							'action': {
								'download_capture': False
							},
							'other': {
								'live_capture': False
							},
							'configure': {
								'gateway6': False,
								'lossratio': True, 
								'capture_to_file': True, 
								'gateway4': False, 
								'delay': True, 
								'bandwidth': True, 
								'capture_filter': True, 
								'capture_via_net': True
							}
						}
					}
				},
				'resources': None,
				'attrs': {
					'state': 'started', 
					'type': 'router', 
					'name': 'router1', 
					'pos': None
				},
				'capabilities': {
					'action': {
						'start': False,
						'download_capture': True,
						'stop': True,
						'prepare': False,
						'destroy': False
					},
					'configure': {
						'pos': True
					}
				}
			},
			'hub1': {
				'connections': {
					'kvm1.eth2': {
						'interface': 'kvm1.eth2',
						'attrs': {
							'gateway6': None,
							'lossratio': 0.0,
							'bridge_id': None,
							'capture_to_file': False,
							'gateway4': None,
							'delay': 0,
							'bandwidth': 10000,
							'tinc_port': None,
							'capture_filter': '',
							'capture_via_net': False
						},
						'capabilities': {
							'action': {
								'download_capture': False
							},
							'other': {
								'live_capture': False
							},
							'configure': {
								'gateway6': False, 
								'lossratio': True, 
								'capture_to_file': True, 
								'gateway4': False, 
								'delay': True, 
								'bandwidth': True, 
								'capture_filter': True, 
								'capture_via_net': True
							}
						}
					}, 
					'openvz2.eth1': {
						'interface': 'openvz2.eth1',
						'attrs': {
							'gateway6': None,
						 	'lossratio': 0.5, 
						 	'bridge_id': None, 
						 	'capture_to_file': False, 
						 	'gateway4': None, 
						 	'delay': 0, 
						 	'bandwidth': 10000, 
						 	'tinc_port': None, 
						 	'capture_filter': '', 
						 	'capture_via_net': False
						 }, 
						'capabilities': {
							'action': {
								'download_capture': False
							},
							'other': {
								'live_capture': False
							},
							'configure': {
								'gateway6': False,
								'lossratio': True,
								'capture_to_file': True,
								'gateway4': False,
								'delay': True,
								'bandwidth': True,
								'capture_filter': True,
								'capture_via_net': True
							}
						}
					}
				},
				'resources': None,
				'attrs': {
					'state': 'started',
					'type': 'hub',
					'name': 'hub1',
					'pos': None
				},
				'capabilities': {
					'action': {
						'start': False,
						'download_capture': True,
						'stop': True,
						'prepare': False,
						'destroy': False
					}, 
					'configure': {
						'pos': True
					}
				}
			},
			'internet': {
				'connections': {
					'kvm1.eth1': {
						'interface': 'kvm1.eth1',
						'attrs': {
							'bridge_id': None
						},
						'capabilities': {
							'action': {},
							'configure': {}
						}
					}
				},
				'resources': None,
				'attrs': {
					'name': 'internet',
					'network_group': None,
					'pos': None,
					'state': 'started',
					'used_network': {
						'max_devices': 0,
						'avoid_duplicates': False,
						'group': None,
						'type': 'internet',
					},
					'type': 'external',
					'network_type': 'internet'
				},
				'capabilities': {
					'action': {
						'start': False,
						'stop': True, 
						'prepare': False, 
						'destroy': False
					}, 
					'configure': {
						'network_group': False, 
						'pos': True, 
						'network_type': False
					}
				}
			}
		}, 
		'devices': {
			'kvm1': {
				'interfaces': {
					'eth2': {
						'attrs': {
							'name': 'eth2'
						},
						'capabilities': {
							'action': {},
							'configure': {}
						}
					},
					'eth1': {
						'attrs': {
							'name': 'eth1'
						},
						'capabilities': {
							'action': {}, 
							'configure': {}
						}
					},
					'eth0': {
						'attrs': {
							'name': 'eth0'
						},
						'capabilities': {
							'action': {},
							'configure': {}
						}
					}
				},
			 	'resources': None,
			 	'attrs': {
					'name': 'kvm1',
					'vnc_port': None, 
					'vmid': None, 
					'state': 'started', 
					'pos': None, 
					'host': None, 
					'template': None, 
					'type': 'kvm', 
					'vnc_password': None
				}, 
				'capabilities': {
					'action': {
						'prepare': False,
						'upload_image_use': False,
						'download_image': False,
						'stop': True,
						'send_keys': True,
						'start': False,
						'migrate': True,
						'upload_image_prepare': False,
						'destroy': False
					},
					'other': {
						'console': True
					},
					'configure': {
						'pos': True,
						'hostgroup': True,
						'template': False
					}
				}
			},
			'openvz1': {
				'interfaces': {
					'eth1': {
						'attrs': {
							'use_dhcp': 'False',
							'ip6address': 'fd01:ab1a:b1ab:1:1::1/80',
							'name': 'eth1',
							'ip4address': '10.1.1.1/24'
						}, 
						'capabilities': {
							'action': {},
							'configure': {
								'use_dhcp': True,
								'ip6address': True,
								'ip4address': True
							}
						}
					},
					'eth0': {
						'attrs': {
							'use_dhcp': 'False', 
							'ip6address': 'fd01:ab1a:b1ab:0:1::1/64', 
							'name': 'eth0', 
							'ip4address': '10.0.0.1/24'
						},
						'capabilities': {
							'action': {},
							'configure': {
								'use_dhcp': True,
								'ip6address': True,
								'ip4address': True
							}
						}
					}
				},
				'resources': None,
				'attrs': {
					'name': 'openvz1', 
					'vnc_port': None, 
					'vmid': None, 
					'pos': None, 
					'gateway6': 'fd01:ab1a:b1ab:1:1:FFFF:FFFF:FFFF', 
					'gateway4': '10.1.1.254', 
					'state': 'started', 
					'root_password': 'glabroot', 
					'template': None, 
					'host': None, 
					'type': 'openvz', 
					'vnc_password': None
				},
				'capabilities': {
					'action': {
						'execute': True, 
						'prepare': False, 
						'upload_image_use': False, 
						'download_image': False, 
						'stop': True, 
						'start': False, 
						'migrate': True, 
						'upload_image_prepare': False, 
						'destroy': False
					}, 
					'other': {
						'console': True
					},
					'configure': {
						'pos': True, 
						'hostgroup': True, 
						'gateway6': True, 
						'gateway4': True, 
						'root_password': True, 
						'template': False
					}
				}
			},
			'openvz2': {
				'interfaces': {
					'eth1': {
						'attrs': {
							'use_dhcp': 'False', 
							'ip6address': 'fd01:ab1a:b1ab:2:1::1/64', 
							'name': 'eth1', 
							'ip4address': '10.2.0.1/24'
						},
						'capabilities': {
							'action': {},
							'configure': {
								'use_dhcp': True, 
								'ip6address': True, 
								'ip4address': True
							}
						}
					},
					'eth0': {
						'attrs': {
							'use_dhcp': 'False', 
							'ip6address': 'fd01:ab1a:b1ab:0:2::1/64', 
							'name': 'eth0', 
							'ip4address': '10.0.0.2/24'
						},
						'capabilities': {
							'action': {}, 
							'configure': {
								'use_dhcp': True, 
								'ip6address': True, 
								'ip4address': True
							}
						}
					}
				},
				'resources': None,
				'attrs': {
					'name': 'openvz2', 
					'vnc_port': None, 
					'vmid': None, 
					'pos': None, 
					'gateway6': None, 
					'gateway4': None, 
					'state': 'started', 
					'root_password': 'glabroot', 
					'template': None, 
					'host': None, 
					'type': 'openvz', 
					'vnc_password': None
				},
				'capabilities': {
					'action': {
						'execute': True, 
						'prepare': False, 
						'upload_image_use': False, 
						'download_image': False, 
						'stop': True, 
						'start': False, 
						'migrate': True, 
						'upload_image_prepare': False, 
						'destroy': False
					},
					'other': {
						'console': True
					},
					'configure': {
						'pos': True, 
						'hostgroup': True, 
						'gateway6': True, 
						'gateway4': True, 
						'root_password': True, 
						'template': False
					}
				}
			}
		},
		'attrs': {
			'name': None,
			'destroy_timeout': None,
			'connector_count': 4,
			'state': 'started',
			'stop_timeout': None, 
			'device_count': 3, 
			'remove_timeout': None, 
			'owner': None
		}, 
		'id': None, 
		'resources': None, 
		'permissions': {}
	}
	real = top_info(topId)
	(res, msg) = is_superset (real, expected)
	assert res, "%s: real: %s, expected: %s" % (msg, real, expected)

if __name__ == "__main__":
	from tests.top.simple import top
	errors_remove()
	topId = top_create()
	try:
		print "creating topology..."
		top_modify(topId, jsonToMods(top), True)

		print "starting topology..."
		task = top_action(topId, "start")
		waitForTask(task, assertSuccess=True)

		print "testing topology information..."
		simpleTop_checkTopInformation(topId)

		print "destroying topology..."
		top_action(topId, "destroy", direct=True)
	except:
		import traceback
		traceback.print_exc()
		print "-" * 50
		errors_print()
		print "-" * 50
		print "Topology id is: %d" % topId
		raw_input("Press enter to remove topology")
	finally:
		top_action(topId, "remove", direct=True)
