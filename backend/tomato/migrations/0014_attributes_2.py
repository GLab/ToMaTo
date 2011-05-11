# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):
	
	def forwards(self, orm):
		for obj in orm.Host.objects.all():
			attrs = orm.AttributeSet()
			attrs.save()
			obj.attributes = attrs
			attrs.attributeentry_set.add(orm.AttributeEntry(name="port_start", value=obj.port_range_start, attribute_set=attrs))
			attrs.attributeentry_set.add(orm.AttributeEntry(name="port_count", value=obj.port_range_count, attribute_set=attrs))
			attrs.attributeentry_set.add(orm.AttributeEntry(name="vmid_start", value=obj.vmid_range_start, attribute_set=attrs))
			attrs.attributeentry_set.add(orm.AttributeEntry(name="vmid_count", value=obj.vmid_range_count, attribute_set=attrs))
			attrs.attributeentry_set.add(orm.AttributeEntry(name="bridge_start", value=obj.bridge_range_start, attribute_set=attrs))
			attrs.attributeentry_set.add(orm.AttributeEntry(name="bridge_count", value=obj.bridge_range_count, attribute_set=attrs))
			attrs.attributeentry_set.add(orm.AttributeEntry(name="hostserver_port", value=obj.hostserver_port, attribute_set=attrs))
			attrs.attributeentry_set.add(orm.AttributeEntry(name="hostserver_basedir", value=obj.hostserver_basedir, attribute_set=attrs))
			attrs.attributeentry_set.add(orm.AttributeEntry(name="hostserver_secret_key", value=obj.hostserver_secret_key, attribute_set=attrs))
			obj.save()
		for obj in orm.Topology.objects.all():
			attrs = orm.AttributeSet()
			attrs.save()
			obj.attributes = attrs
			attrs.attributeentry_set.add(orm.AttributeEntry(name="date_created", value=obj.date_created, attribute_set=attrs))
			attrs.attributeentry_set.add(orm.AttributeEntry(name="date_modified", value=obj.date_modified, attribute_set=attrs))
			attrs.attributeentry_set.add(orm.AttributeEntry(name="date_usage", value=obj.date_usage, attribute_set=attrs))
			attrs.attributeentry_set.add(orm.AttributeEntry(name="task", value=obj.task, attribute_set=attrs))
			if obj.resources:
				for r in obj.resources.resourceentry_set.all():
					attrs.attributeentry_set.add(orm.AttributeEntry(name="resources_%s" % r.type, value=r.value, attribute_set=attrs))
			obj.save()
		for obj in orm.Device.objects.all():
			attrs = orm.AttributeSet()
			attrs.save()
			obj.attributes = attrs
			attrs.attributeentry_set.add(orm.AttributeEntry(name="pos", value=obj.pos, attribute_set=attrs))
			attrs.attributeentry_set.add(orm.AttributeEntry(name="hostgroup", value=obj.hostgroup, attribute_set=attrs))
			if obj.resources:
				for r in obj.resources.resourceentry_set.all():
					attrs.attributeentry_set.add(orm.AttributeEntry(name="resources_%s" % r.type, value=r.value, attribute_set=attrs))
			obj.save()
		for obj in orm.Interface.objects.all():
			attrs = orm.AttributeSet()
			attrs.save()
			obj.attributes = attrs
			obj.save() 
		for obj in orm.Connector.objects.all():
			attrs = orm.AttributeSet()
			attrs.save()
			obj.attributes = attrs
			attrs.attributeentry_set.add(orm.AttributeEntry(name="pos", value=obj.pos, attribute_set=attrs))
			if obj.resources:
				for r in obj.resources.resourceentry_set.all():
					attrs.attributeentry_set.add(orm.AttributeEntry(name="resources_%s" % r.type, value=r.value, attribute_set=attrs))
			obj.save()
		for obj in orm.Connection.objects.all():
			attrs = orm.AttributeSet()
			attrs.save()
			obj.attributes = attrs
			if obj.bridge_id:
				attrs.attributeentry_set.add(orm.AttributeEntry(name="bridge_id", value=obj.bridge_id, attribute_set=attrs))
			obj.save() 
		for obj in orm.EmulatedConnection.objects.all():
			if obj.delay:
				obj.attributes.attributeentry_set.add(orm.AttributeEntry(name="delay", value=obj.delay, attribute_set=obj.attributes))
			if obj.bandwidth:
				obj.attributes.attributeentry_set.add(orm.AttributeEntry(name="bandwidth", value=obj.bandwidth, attribute_set=obj.attributes))
			if obj.lossratio:
				obj.attributes.attributeentry_set.add(orm.AttributeEntry(name="lossratio", value=obj.lossratio, attribute_set=obj.attributes))
			if obj.capture:
				obj.attributes.attributeentry_set.add(orm.AttributeEntry(name="capture", value=obj.capture, attribute_set=obj.attributes))
			obj.save()
		for obj in orm.KVMDevice.objects.all():
			if obj.kvm_id:
				obj.attributes.attributeentry_set.add(orm.AttributeEntry(name="vmid", value=obj.kvm_id, attribute_set=obj.attributes))
			if obj.template:
				obj.attributes.attributeentry_set.add(orm.AttributeEntry(name="template", value=obj.template, attribute_set=obj.attributes))
			if obj.vnc_port:
				obj.attributes.attributeentry_set.add(orm.AttributeEntry(name="vnc_port", value=obj.vnc_port, attribute_set=obj.attributes))
			obj.save()
		for obj in orm.OpenVZDevice.objects.all():
			if obj.openvz_id:
				obj.attributes.attributeentry_set.add(orm.AttributeEntry(name="vmid", value=obj.openvz_id, attribute_set=obj.attributes))
			if obj.template:
				obj.attributes.attributeentry_set.add(orm.AttributeEntry(name="template", value=obj.template, attribute_set=obj.attributes))
			if obj.vnc_port:
				obj.attributes.attributeentry_set.add(orm.AttributeEntry(name="vnc_port", value=obj.vnc_port, attribute_set=obj.attributes))
			if obj.gateway:
				obj.attributes.attributeentry_set.add(orm.AttributeEntry(name="gateway", value=obj.gateway, attribute_set=obj.attributes))
			obj.save()
		for obj in orm.ConfiguredInterface.objects.all():
			if obj.use_dhcp:
				obj.attributes.attributeentry_set.add(orm.AttributeEntry(name="use_dhcp", value=obj.use_dhcp, attribute_set=obj.attributes))
			if obj.ip4address:
				obj.attributes.attributeentry_set.add(orm.AttributeEntry(name="ip4address", value=obj.ip4address, attribute_set=obj.attributes))
			obj.save()
		for obj in orm.SpecialFeatureConnector.objects.all():
			if obj.feature_group:
				obj.attributes.attributeentry_set.add(orm.AttributeEntry(name="feature_group", value=obj.feature_group, attribute_set=obj.attributes))
			if obj.feature_type:
				obj.attributes.attributeentry_set.add(orm.AttributeEntry(name="feature_type", value=obj.feature_type, attribute_set=obj.attributes))
			obj.save()
		for obj in orm.TincConnection.objects.all():
			if obj.tinc_port:
				obj.attributes.attributeentry_set.add(orm.AttributeEntry(name="tinc_port", value=obj.tinc_port, attribute_set=obj.attributes))
			if obj.gateway:
				obj.attributes.attributeentry_set.add(orm.AttributeEntry(name="gateway", value=obj.gateway, attribute_set=obj.attributes))
			obj.save()
		
			
	
	def backwards(self, orm):
		raise Exception("not implemented")
	
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
			'interface_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Interface']", 'unique': 'True', 'primary_key': 'True'}),
			'ip4address': ('django.db.models.fields.CharField', [], {'max_length': '18', 'null': 'True'}),
			'use_dhcp': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
		},
		'tomato.connection': {
			'Meta': {'object_name': 'Connection'},
			'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']", 'null': 'True'}),
			'bridge_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
			'connector': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Connector']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'interface': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Interface']", 'unique': 'True'})
		},
		'tomato.connector': {
			'Meta': {'object_name': 'Connector'},
			'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']", 'null': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
			'pos': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
			'resources': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.ResourceSet']", 'null': 'True'}),
			'state': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '10'}),
			'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
		},
		'tomato.device': {
			'Meta': {'object_name': 'Device'},
			'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']", 'null': 'True'}),
			'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Host']", 'null': 'True'}),
			'hostgroup': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
			'pos': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
			'resources': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.ResourceSet']", 'null': 'True'}),
			'state': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '10'}),
			'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
		},
		'tomato.emulatedconnection': {
			'Meta': {'object_name': 'EmulatedConnection', '_ormbases': ['tomato.Connection']},
			'bandwidth': ('django.db.models.fields.IntegerField', [], {'default': '10000', 'null': 'True'}),
			'capture': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
			'connection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connection']", 'unique': 'True', 'primary_key': 'True'}),
			'delay': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
			'lossratio': ('django.db.models.fields.FloatField', [], {'null': 'True'})
		},
		'tomato.error': {
			'Meta': {'object_name': 'Error'},
			'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
			'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
		},
		'tomato.host': {
			'Meta': {'object_name': 'Host'},
			'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']", 'null': 'True'}),
			'bridge_range_count': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1000'}),
			'bridge_range_start': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1000'}),
			'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
			'group': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
			'hostserver_basedir': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
			'hostserver_port': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
			'hostserver_secret_key': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
			'port_range_count': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1000'}),
			'port_range_start': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '7000'}),
			'vmid_range_count': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '200'}),
			'vmid_range_start': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1000'})
		},
		'tomato.interface': {
			'Meta': {'object_name': 'Interface'},
			'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']", 'null': 'True'}),
			'device': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Device']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '5'})
		},
		'tomato.kvmdevice': {
			'Meta': {'object_name': 'KVMDevice', '_ormbases': ['tomato.Device']},
			'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Device']", 'unique': 'True', 'primary_key': 'True'}),
			'kvm_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
			'template': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
			'vnc_port': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
		},
		'tomato.openvzdevice': {
			'Meta': {'object_name': 'OpenVZDevice', '_ormbases': ['tomato.Device']},
			'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Device']", 'unique': 'True', 'primary_key': 'True'}),
			'gateway': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
			'openvz_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
			'root_password': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
			'template': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
			'vnc_port': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
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
		'tomato.resourceentry': {
			'Meta': {'object_name': 'ResourceEntry'},
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'resource_set': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.ResourceSet']"}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
			'value': ('django.db.models.fields.BigIntegerField', [], {})
		},
		'tomato.resourceset': {
			'Meta': {'object_name': 'ResourceSet'},
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
		},
		'tomato.specialfeature': {
			'Meta': {'object_name': 'SpecialFeature'},
			'bridge': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
			'feature_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.SpecialFeatureGroup']"}),
			'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Host']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
		},
		'tomato.specialfeatureconnector': {
			'Meta': {'object_name': 'SpecialFeatureConnector', '_ormbases': ['tomato.Connector']},
			'connector_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connector']", 'unique': 'True', 'primary_key': 'True'}),
			'feature_group': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
			'feature_type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
			'used_feature_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.SpecialFeatureGroup']", 'null': 'True'})
		},
		'tomato.specialfeaturegroup': {
			'Meta': {'object_name': 'SpecialFeatureGroup'},
			'avoid_duplicates': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
			'feature_type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
			'group_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'max_devices': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
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
			'gateway': ('django.db.models.fields.CharField', [], {'max_length': '18', 'null': 'True'}),
			'tinc_port': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
		},
		'tomato.tincconnector': {
			'Meta': {'object_name': 'TincConnector', '_ormbases': ['tomato.Connector']},
			'connector_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connector']", 'unique': 'True', 'primary_key': 'True'})
		},
		'tomato.topology': {
			'Meta': {'object_name': 'Topology'},
			'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']", 'null': 'True'}),
			'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
			'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
			'date_usage': ('django.db.models.fields.DateTimeField', [], {}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
			'owner': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
			'resources': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.ResourceSet']", 'null': 'True'}),
			'task': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
		}
	}
	
	complete_apps = ['tomato']
