# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):
	
	def forwards(self, orm):
		for obj in orm.Host.objects.all():
			obj.attrs = {}
			for attr in obj.attributes.attributeentry_set.all():
				if attr.name in ["vmid_start", "vmid_count", "port_start", "port_count", "bridge_start", "bridge_count"]:
					obj.attrs[attr.name] = int(attr.value)
				else:
					obj.attrs[attr.name] = attr.value
			obj.save()
		for obj in orm.Topology.objects.all():
			obj.attrs = {}
			for attr in obj.attributes.attributeentry_set.all():
				if attr.name == "task":
					obj.task = attr.value
				elif attr.name == "date_usage":
					obj.date_usage = attr.value
				else:
					obj.attrs[attr.name] = attr.value
			obj.save()
		for obj in orm.OpenVZDevice.objects.all():
			obj.attrs = {}
			for attr in obj.attributes.attributeentry_set.all():
				if attr.name == "vmid":
					obj.vmid = int(attr.value)
				elif attr.name == "template":
					obj.template = attr.value
				elif attr.name == "vnc_port":
					obj.vnc_port = attr.value
				elif attr.name == "hostgroup":
					obj.hostgroup = attr.value
				else:
					obj.attrs[attr.name] = attr.value
			obj.save()
		for obj in orm.KVMDevice.objects.all():
			obj.attrs = {}
			for attr in obj.attributes.attributeentry_set.all():
				if attr.name == "vmid":
					obj.vmid = int(attr.value)
				elif attr.name == "template":
					obj.template = attr.value
				elif attr.name == "vnc_port":
					obj.vnc_port = attr.value
				elif attr.name == "hostgroup":
					obj.hostgroup = attr.value
				else:
					obj.attrs[attr.name] = attr.value
			obj.save()
		for obj in orm.Connection.objects.all():
			obj.attrs = {}
			for attr in obj.attributes.attributeentry_set.all():
				if attr.name == "bridge_id":
					obj.bridge_id = int(attr.value)
				else:
					obj.attrs[attr.name] = attr.value
			obj.save()
		for obj in orm.TincConnection.objects.all():
			for attr in obj.attributes.attributeentry_set.all():
				if attr.name == "tinc_port":
					obj.tinc_port = int(attr.value)
			obj.save()
		for obj in orm.TincConnector.objects.all():
			obj.attrs = {}
			for attr in obj.attributes.attributeentry_set.all():
				obj.attrs[attr.name] = attr.value
			obj.save()
		for obj in orm.ExternalNetworkConnector.objects.all():
			obj.attrs = {}
			for attr in obj.attributes.attributeentry_set.all():
				if attr.name == "network_group":
					obj.network_group = attr.value
				if attr.name == "network_type":
					obj.network_type = attr.value
				else:
					obj.attrs[attr.name] = attr.value
			obj.save()
		for obj in orm.Interface.objects.all():
			obj.attrs = {}
			for attr in obj.attributes.attributeentry_set.all():
				obj.attrs[attr.name] = attr.value
			obj.save()
	
	
	def backwards(self, orm):
		"Write your backwards methods here."
	
	models = {
		'tomato.attributeentry': {
			'Meta': {'object_name': 'AttributeEntry'},
			'attribute_set': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
			'value': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'})
		},
		'tomato.attributeset': {
			'Meta': {'object_name': 'AttributeSet'},
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
		},
		'tomato.configuredinterface': {
			'Meta': {'object_name': 'ConfiguredInterface', '_ormbases': ['tomato.Interface']},
			'interface_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Interface']", 'unique': 'True', 'primary_key': 'True'})
		},
		'tomato.connection': {
			'Meta': {'object_name': 'Connection'},
			'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']"}),
			'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
			'bridge_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
			'connector': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Connector']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'interface': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Interface']", 'unique': 'True'})
		},
		'tomato.connector': {
			'Meta': {'object_name': 'Connector'},
			'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']"}),
			'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
			'state': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '10'}),
			'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
		},
		'tomato.device': {
			'Meta': {'object_name': 'Device'},
			'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']"}),
			'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
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
			'connection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connection']", 'unique': 'True', 'primary_key': 'True'})
		},
		'tomato.error': {
			'Meta': {'object_name': 'Error'},
			'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
			'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
		},
		'tomato.externalnetwork': {
			'Meta': {'object_name': 'ExternalNetwork'},
			'avoid_duplicates': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
			'group': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'max_devices': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
		},
		'tomato.externalnetworkbridge': {
			'Meta': {'object_name': 'ExternalNetworkBridge'},
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
			'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']"}),
			'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
			'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
			'group': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
		},
		'tomato.interface': {
			'Meta': {'object_name': 'Interface'},
			'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']"}),
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
			'vnc_port': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'})
		},
		'tomato.openvzdevice': {
			'Meta': {'object_name': 'OpenVZDevice', '_ormbases': ['tomato.Device']},
			'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Device']", 'unique': 'True', 'primary_key': 'True'}),
			'template': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
			'vmid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
			'vnc_port': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'})
		},
		'tomato.permission': {
			'Meta': {'object_name': 'Permission'},
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'role': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
			'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
			'user': ('django.db.models.fields.CharField', [], {'max_length': '30'})
		},
		'tomato.physicallink': {
			'Meta': {'object_name': 'PhysicalLink'},
			'delay_avg': ('django.db.models.fields.FloatField', [], {}),
			'delay_stddev': ('django.db.models.fields.FloatField', [], {}),
			'dst_group': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'loss': ('django.db.models.fields.FloatField', [], {}),
			'src_group': ('django.db.models.fields.CharField', [], {'max_length': '10'})
		},
		'tomato.template': {
			'Meta': {'object_name': 'Template'},
			'default': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
			'download_url': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '12'})
		},
		'tomato.tincconnection': {
			'Meta': {'object_name': 'TincConnection', '_ormbases': ['tomato.EmulatedConnection']},
			'emulatedconnection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.EmulatedConnection']", 'unique': 'True', 'primary_key': 'True'}),
			'tinc_port': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'})
		},
		'tomato.tincconnector': {
			'Meta': {'object_name': 'TincConnector', '_ormbases': ['tomato.Connector']},
			'connector_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connector']", 'unique': 'True', 'primary_key': 'True'})
		},
		'tomato.topology': {
			'Meta': {'object_name': 'Topology'},
			'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']"}),
			'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
			'date_usage': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
			'owner': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
			'task': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'})
		}
	}
	
	complete_apps = ['tomato']
