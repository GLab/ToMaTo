# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
	
	def forwards(self, orm):
		
		# Adding field 'OpenVZDevice.vmid'
		db.add_column('tomato_openvzdevice', 'vmid', self.gf('django.db.models.fields.PositiveIntegerField')(null=True), keep_default=False)

		# Adding field 'OpenVZDevice.template'
		db.add_column('tomato_openvzdevice', 'template', self.gf('django.db.models.fields.CharField')(max_length=255, null=True), keep_default=False)

		# Adding field 'OpenVZDevice.vnc_port'
		db.add_column('tomato_openvzdevice', 'vnc_port', self.gf('django.db.models.fields.PositiveIntegerField')(null=True), keep_default=False)

		# Adding field 'Connection.bridge_id'
		db.add_column('tomato_connection', 'bridge_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True), keep_default=False)

		# Adding field 'TincConnection.tinc_port'
		db.add_column('tomato_tincconnection', 'tinc_port', self.gf('django.db.models.fields.PositiveIntegerField')(null=True), keep_default=False)

		# Adding field 'Device.hostgroup'
		db.add_column('tomato_device', 'hostgroup', self.gf('django.db.models.fields.CharField')(max_length=20, null=True), keep_default=False)

		# Adding field 'KVMDevice.vmid'
		db.add_column('tomato_kvmdevice', 'vmid', self.gf('django.db.models.fields.PositiveIntegerField')(null=True), keep_default=False)

		# Adding field 'KVMDevice.template'
		db.add_column('tomato_kvmdevice', 'template', self.gf('django.db.models.fields.CharField')(max_length=255, null=True), keep_default=False)

		# Adding field 'KVMDevice.vnc_port'
		db.add_column('tomato_kvmdevice', 'vnc_port', self.gf('django.db.models.fields.PositiveIntegerField')(null=True), keep_default=False)

		# Adding field 'Topology.task'
		db.add_column('tomato_topology', 'task', self.gf('django.db.models.fields.CharField')(max_length=250, null=True), keep_default=False)

		# Adding field 'Topology.date_usage'
		db.add_column('tomato_topology', 'date_usage', self.gf('django.db.models.fields.DateTimeField')(null=True), keep_default=False)

		# Adding field 'ExternalNetworkConnector.network_group'
		db.add_column('tomato_externalnetworkconnector', 'network_group', self.gf('django.db.models.fields.CharField')(max_length=20, null=True), keep_default=False)

		# Adding field 'ExternalNetworkConnector.network_type'
		db.add_column('tomato_externalnetworkconnector', 'network_type', self.gf('django.db.models.fields.CharField')(default='internet', max_length=20), keep_default=False)
	
		# Adding field 'Device.attrs'
		db.add_column('tomato_device', 'attrs', self.gf('tomato.lib.db.JSONField')(default={}), keep_default=False)

		# Adding field 'Connection.attrs'
		db.add_column('tomato_connection', 'attrs', self.gf('tomato.lib.db.JSONField')(default={}), keep_default=False)

		# Adding field 'Connector.attrs'
		db.add_column('tomato_connector', 'attrs', self.gf('tomato.lib.db.JSONField')(default={}), keep_default=False)

		# Adding field 'Interface.attrs'
		db.add_column('tomato_interface', 'attrs', self.gf('tomato.lib.db.JSONField')(default={}), keep_default=False)

		# Adding field 'Host.attrs'
		db.add_column('tomato_host', 'attrs', self.gf('tomato.lib.db.JSONField')(default={}), keep_default=False)

		# Adding field 'Topology.attrs'
		db.add_column('tomato_topology', 'attrs', self.gf('tomato.lib.db.JSONField')(default={}), keep_default=False)
	
	def backwards(self, orm):
		
		# Deleting field 'OpenVZDevice.vmid'
		db.delete_column('tomato_openvzdevice', 'vmid')

		# Deleting field 'OpenVZDevice.template'
		db.delete_column('tomato_openvzdevice', 'template')

		# Deleting field 'OpenVZDevice.vnc_port'
		db.delete_column('tomato_openvzdevice', 'vnc_port')

		# Deleting field 'Connection.bridge_id'
		db.delete_column('tomato_connection', 'bridge_id')

		# Deleting field 'TincConnection.tinc_port'
		db.delete_column('tomato_tincconnection', 'tinc_port')

		# Deleting field 'Device.hostgroup'
		db.delete_column('tomato_device', 'hostgroup')

		# Deleting field 'KVMDevice.vmid'
		db.delete_column('tomato_kvmdevice', 'vmid')

		# Deleting field 'KVMDevice.template'
		db.delete_column('tomato_kvmdevice', 'template')

		# Deleting field 'KVMDevice.vnc_port'
		db.delete_column('tomato_kvmdevice', 'vnc_port')

		# Deleting field 'Topology.task'
		db.delete_column('tomato_topology', 'task')

		# Deleting field 'Topology.date_usage'
		db.delete_column('tomato_topology', 'date_usage')

		# Deleting field 'ExternalNetworkConnector.network_group'
		db.delete_column('tomato_externalnetworkconnector', 'network_group')

		# Deleting field 'ExternalNetworkConnector.network_type'
		db.delete_column('tomato_externalnetworkconnector', 'network_type')

		# Deleting field 'Device.attrs'
		db.delete_column('tomato_device', 'attrs')

		# Deleting field 'Connection.attrs'
		db.delete_column('tomato_connection', 'attrs')

		# Deleting field 'Connector.attrs'
		db.delete_column('tomato_connector', 'attrs')

		# Deleting field 'Interface.attrs'
		db.delete_column('tomato_interface', 'attrs')

		# Deleting field 'Host.attrs'
		db.delete_column('tomato_host', 'attrs')

		# Deleting field 'Topology.attrs'
		db.delete_column('tomato_topology', 'attrs')
	
	
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
