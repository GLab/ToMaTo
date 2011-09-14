# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from tomato import hosts
from tomato.hosts import resources
from tomato import models as m

class Migration(DataMigration):
	
	def forwards(self, orm):
		for host in hosts.getAll():
			for type in resources.TYPES:
				resources.createPool(host, type, host.getAttribute("%s_start" % type), host.getAttribute("%s_count" % type))
				host.deleteAttribute("%s_start" % type)
				host.deleteAttribute("%s_count" % type)
		for obj in m.EmulatedConnection.objects.all():
			if obj.getAttribute("capture_port"):
				host = obj.interface.device.host
				obj.live_capture_port = resources.take(host, "port", obj, obj.LIVE_CAPTURE_PORT_SLOT, obj.getAttribute("capture_port"))
				obj.deleteAttribute("capture_port")
			if not obj.getAttribute("ifb_id") is None:
				host = obj.interface.device.host
				obj.ifb_id = resources.take(host, "ifb", obj, obj.IFB_ID_SLOT, obj.getAttribute("ifb_id"))
				obj.deleteAttribute("ifb_id")
		for obj in m.TincConnector.objects.all():
			if obj.getAttribute("external_access_port"):
				port = obj.getAttribute("external_access_port")
				obj.deleteAttribute("external_access_port")
				cname = obj.getAttribute("external_access_con")
				obj.deleteAttribute("external_access_con")
				con = obj.topology.interfacesGet(cname).connection
				host = con.interface.device.host
				obj.external_access_port = resources.take(host, "port", obj, obj.EXTERNAL_ACCESS_PORT_SLOT, port)
		for obj in orm.TincConnection.objects.all():
			host = obj.interface.device.host
			if obj.tinc_port and host:
				pool = orm.ResourcePool.objects.get(host=host, type="port")
				obj.tinc_port_ref = orm.ResourceEntry.objects.create(pool=pool, owner_type="c", owner_id=obj.id, slot="tinc", num=obj.tinc_port)
			if obj.bridge_id and host:
				pool = orm.ResourcePool.objects.get(host=host, type="bridge")
				obj.bridge_id_ref = orm.ResourceEntry.objects.create(pool=pool, owner_type="c", owner_id=obj.id, slot="b", num=obj.bridge_id)
		for obj in orm.KVMDevice.objects.all():
			if obj.vmid and obj.host:
				pool = orm.ResourcePool.objects.get(host=host, type="vmid")
				obj.vmid_ref = orm.ResourceEntry.objects.create(pool=pool, owner_type="D", owner_id=obj.id, slot="vmid", num=obj.vmid)
			if obj.vnc_port and obj.host:
				pool = orm.ResourcePool.objects.get(host=host, type="port")
				obj.vnc_port_ref = orm.ResourceEntry.objects.create(pool=pool, owner_type="D", owner_id=obj.id, slot="vnc", num=obj.vnc_port)
		for obj in orm.OpenVZDevice.objects.all():
			if obj.vmid and obj.host:
				pool = orm.ResourcePool.objects.get(host=host, type="vmid")
				obj.vmid_ref = orm.ResourceEntry.objects.create(pool=pool, owner_type="D", owner_id=obj.id, slot="vmid", num=obj.vmid)
			if obj.vnc_port and obj.host:
				pool = orm.ResourcePool.objects.get(host=host, type="port")
				obj.vnc_port_ref = orm.ResourceEntry.objects.create(pool=pool, owner_type="D", owner_id=obj.id, slot="vnc", num=obj.vnc_port)
		for obj in orm.ProgDevice.objects.all():
			if obj.vnc_port and obj.host:
				pool = orm.ResourcePool.objects.get(host=host, type="port")
				obj.vnc_port_ref = orm.ResourceEntry.objects.create(pool=pool, owner_type="D", owner_id=obj.id, slot="vnc", num=obj.vnc_port)
	
	def backwards(self, orm):
		raise Exception("not implemented")
	
	models = {
		'tomato.configuredinterface': {
			'Meta': {'object_name': 'ConfiguredInterface', '_ormbases': ['tomato.Interface']},
			'interface_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Interface']", 'unique': 'True', 'primary_key': 'True'})
		},
		'tomato.connection': {
			'Meta': {'unique_together': "(('connector', 'interface'),)", 'object_name': 'Connection'},
			'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
			'bridge_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
			'connector': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Connector']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'interface': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Interface']", 'unique': 'True'})
		},
		'tomato.connector': {
			'Meta': {'unique_together': "(('topology', 'name'),)", 'object_name': 'Connector'},
			'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
			'state': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '10'}),
			'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
		},
		'tomato.device': {
			'Meta': {'unique_together': "(('topology', 'name'),)", 'object_name': 'Device'},
			'attrs': ('tomato.lib.db.JSONField', [], {}),
			'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Host']", 'null': 'True'}),
			'hostgroup': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
			'state': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '10'}),
			'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
		},
		'tomato.emulatedconnection': {
			'Meta': {'object_name': 'EmulatedConnection', '_ormbases': ['tomato.Connection']},
			'connection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connection']", 'unique': 'True', 'primary_key': 'True'}),
			'ifb_id': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['tomato.ResourceEntry']"}),
			'live_capture_port': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['tomato.ResourceEntry']"})
		},
		'tomato.error': {
			'Meta': {'object_name': 'Error'},
			'date_first': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
			'date_last': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
			'occurrences': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
			'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
			'type': ('django.db.models.fields.CharField', [], {'default': "'error'", 'max_length': '20'})
		},
		'tomato.externalnetwork': {
			'Meta': {'unique_together': "(('group', 'type'),)", 'object_name': 'ExternalNetwork'},
			'avoid_duplicates': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
			'group': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'max_devices': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
		},
		'tomato.externalnetworkbridge': {
			'Meta': {'unique_together': "(('host', 'bridge'),)", 'object_name': 'ExternalNetworkBridge'},
			'bridge': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
			'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Host']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'network': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.ExternalNetwork']"})
		},
		'tomato.externalnetworkconnector': {
			'Meta': {'object_name': 'ExternalNetworkConnector', '_ormbases': ['tomato.Connector']},
			'connector_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connector']", 'unique': 'True', 'primary_key': 'True'}),
			'network_group': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
			'network_type': ('django.db.models.fields.CharField', [], {'default': "'internet'", 'max_length': '20'}),
			'used_network': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.ExternalNetwork']", 'null': 'True'})
		},
		'tomato.host': {
			'Meta': {'object_name': 'Host'},
			'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
			'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
			'group': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
		},
		'tomato.interface': {
			'Meta': {'unique_together': "(('device', 'name'),)", 'object_name': 'Interface'},
			'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
			'device': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Device']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '5'})
		},
		'tomato.kvmdevice': {
			'Meta': {'object_name': 'KVMDevice', '_ormbases': ['tomato.Device']},
			'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Device']", 'unique': 'True', 'primary_key': 'True'}),
			'template': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
			'vmid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
			'vmid_ref': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['tomato.ResourceEntry']"}),
			'vnc_port': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
			'vnc_port_ref': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['tomato.ResourceEntry']"})
		},
		'tomato.openvzdevice': {
			'Meta': {'object_name': 'OpenVZDevice', '_ormbases': ['tomato.Device']},
			'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Device']", 'unique': 'True', 'primary_key': 'True'}),
			'template': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
			'vmid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
			'vmid_ref': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['tomato.ResourceEntry']"}),
			'vnc_port': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
			'vnc_port_ref': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['tomato.ResourceEntry']"})
		},
		'tomato.permission': {
			'Meta': {'unique_together': "(('topology', 'user'),)", 'object_name': 'Permission'},
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'role': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
			'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
			'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.User']"})
		},
		'tomato.physicallink': {
			'Meta': {'unique_together': "(('src_group', 'dst_group'),)", 'object_name': 'PhysicalLink'},
			'delay_avg': ('django.db.models.fields.FloatField', [], {}),
			'delay_stddev': ('django.db.models.fields.FloatField', [], {}),
			'dst_group': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'loss': ('django.db.models.fields.FloatField', [], {}),
			'src_group': ('django.db.models.fields.CharField', [], {'max_length': '10'})
		},
		'tomato.progdevice': {
			'Meta': {'object_name': 'ProgDevice', '_ormbases': ['tomato.Device']},
			'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Device']", 'unique': 'True', 'primary_key': 'True'}),
			'template': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
			'vnc_port': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
			'vnc_port_ref': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['tomato.ResourceEntry']"})
		},
		'tomato.resourceentry': {
			'Meta': {'unique_together': "(('pool', 'num'), ('owner_type', 'owner_id', 'slot'))", 'object_name': 'ResourceEntry'},
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'num': ('django.db.models.fields.IntegerField', [], {}),
			'owner_id': ('django.db.models.fields.IntegerField', [], {}),
			'owner_type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
			'pool': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.ResourcePool']"}),
			'slot': ('django.db.models.fields.CharField', [], {'max_length': '10'})
		},
		'tomato.resourcepool': {
			'Meta': {'unique_together': "(('host', 'type'),)", 'object_name': 'ResourcePool'},
			'first_num': ('django.db.models.fields.IntegerField', [], {}),
			'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Host']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'num_count': ('django.db.models.fields.IntegerField', [], {}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
		},
		'tomato.template': {
			'Meta': {'unique_together': "(('name', 'type'),)", 'object_name': 'Template'},
			'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
			'default': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '12'})
		},
		'tomato.tincconnection': {
			'Meta': {'object_name': 'TincConnection', '_ormbases': ['tomato.EmulatedConnection']},
			'bridge_id_ref': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['tomato.ResourceEntry']"}),
			'emulatedconnection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.EmulatedConnection']", 'unique': 'True', 'primary_key': 'True'}),
			'tinc_port': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
			'tinc_port_ref': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['tomato.ResourceEntry']"})
		},
		'tomato.tincconnector': {
			'Meta': {'object_name': 'TincConnector', '_ormbases': ['tomato.Connector']},
			'connector_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connector']", 'unique': 'True', 'primary_key': 'True'}),
			'external_access_port': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['tomato.ResourceEntry']"})
		},
		'tomato.topology': {
			'Meta': {'object_name': 'Topology'},
			'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
			'date_usage': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
			'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.User']"}),
			'task': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'})
		},
		'tomato.user': {
			'Meta': {'unique_together': "(('name', 'origin'),)", 'object_name': 'User'},
			'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'is_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
			'is_user': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
			'origin': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
			'password': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
			'password_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
		}
	}
	
	complete_apps = ['tomato']
