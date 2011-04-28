# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Deleting model 'ResourceEntry'
        db.delete_table('tomato_resourceentry')

        # Deleting model 'ResourceSet'
        db.delete_table('tomato_resourceset')

        # Deleting field 'Connection.bridge_id'
        db.delete_column('tomato_connection', 'bridge_id')

        # Changing field 'Connection.attributes'
        db.alter_column('tomato_connection', 'attributes_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.AttributeSet']))

        # Deleting field 'Connector.pos'
        db.delete_column('tomato_connector', 'pos')

        # Deleting field 'Connector.resources'
        db.delete_column('tomato_connector', 'resources_id')

        # Changing field 'Connector.attributes'
        db.alter_column('tomato_connector', 'attributes_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.AttributeSet']))

        # Deleting field 'Topology.task'
        db.delete_column('tomato_topology', 'task')

        # Deleting field 'Topology.date_usage'
        db.delete_column('tomato_topology', 'date_usage')

        # Deleting field 'Topology.date_modified'
        db.delete_column('tomato_topology', 'date_modified')

        # Deleting field 'Topology.date_created'
        db.delete_column('tomato_topology', 'date_created')

        # Deleting field 'Topology.resources'
        db.delete_column('tomato_topology', 'resources_id')

        # Changing field 'Topology.attributes'
        db.alter_column('tomato_topology', 'attributes_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.AttributeSet']))

        # Deleting field 'Host.bridge_range_count'
        db.delete_column('tomato_host', 'bridge_range_count')

        # Deleting field 'Host.hostserver_basedir'
        db.delete_column('tomato_host', 'hostserver_basedir')

        # Deleting field 'Host.bridge_range_start'
        db.delete_column('tomato_host', 'bridge_range_start')

        # Deleting field 'Host.hostserver_secret_key'
        db.delete_column('tomato_host', 'hostserver_secret_key')

        # Deleting field 'Host.port_range_start'
        db.delete_column('tomato_host', 'port_range_start')

        # Deleting field 'Host.vmid_range_count'
        db.delete_column('tomato_host', 'vmid_range_count')

        # Deleting field 'Host.port_range_count'
        db.delete_column('tomato_host', 'port_range_count')

        # Deleting field 'Host.hostserver_port'
        db.delete_column('tomato_host', 'hostserver_port')

        # Deleting field 'Host.vmid_range_start'
        db.delete_column('tomato_host', 'vmid_range_start')

        # Changing field 'Host.attributes'
        db.alter_column('tomato_host', 'attributes_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.AttributeSet']))

        # Deleting field 'ConfiguredInterface.use_dhcp'
        db.delete_column('tomato_configuredinterface', 'use_dhcp')

        # Deleting field 'ConfiguredInterface.ip4address'
        db.delete_column('tomato_configuredinterface', 'ip4address')

        # Deleting field 'TincConnection.tinc_port'
        db.delete_column('tomato_tincconnection', 'tinc_port')

        # Deleting field 'TincConnection.gateway'
        db.delete_column('tomato_tincconnection', 'gateway')

        # Deleting field 'SpecialFeatureConnector.feature_group'
        db.delete_column('tomato_specialfeatureconnector', 'feature_group')

        # Deleting field 'SpecialFeatureConnector.feature_type'
        db.delete_column('tomato_specialfeatureconnector', 'feature_type')

        # Changing field 'Interface.attributes'
        db.alter_column('tomato_interface', 'attributes_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.AttributeSet']))

        # Deleting field 'OpenVZDevice.vnc_port'
        db.delete_column('tomato_openvzdevice', 'vnc_port')

        # Deleting field 'OpenVZDevice.openvz_id'
        db.delete_column('tomato_openvzdevice', 'openvz_id')

        # Deleting field 'OpenVZDevice.root_password'
        db.delete_column('tomato_openvzdevice', 'root_password')

        # Deleting field 'OpenVZDevice.template'
        db.delete_column('tomato_openvzdevice', 'template')

        # Deleting field 'OpenVZDevice.gateway'
        db.delete_column('tomato_openvzdevice', 'gateway')

        # Deleting field 'KVMDevice.vnc_port'
        db.delete_column('tomato_kvmdevice', 'vnc_port')

        # Deleting field 'KVMDevice.template'
        db.delete_column('tomato_kvmdevice', 'template')

        # Deleting field 'KVMDevice.kvm_id'
        db.delete_column('tomato_kvmdevice', 'kvm_id')

        # Deleting field 'EmulatedConnection.delay'
        db.delete_column('tomato_emulatedconnection', 'delay')

        # Deleting field 'EmulatedConnection.capture'
        db.delete_column('tomato_emulatedconnection', 'capture')

        # Deleting field 'EmulatedConnection.bandwidth'
        db.delete_column('tomato_emulatedconnection', 'bandwidth')

        # Deleting field 'EmulatedConnection.lossratio'
        db.delete_column('tomato_emulatedconnection', 'lossratio')

        # Deleting field 'Device.pos'
        db.delete_column('tomato_device', 'pos')

        # Deleting field 'Device.hostgroup'
        db.delete_column('tomato_device', 'hostgroup')

        # Deleting field 'Device.resources'
        db.delete_column('tomato_device', 'resources_id')

        # Changing field 'Device.attributes'
        db.alter_column('tomato_device', 'attributes_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.AttributeSet']))
    
    
    def backwards(self, orm):
        
        # Adding model 'ResourceEntry'
        db.create_table('tomato_resourceentry', (
            ('resource_set', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.ResourceSet'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.BigIntegerField')()),
        ))
        db.send_create_signal('tomato', ['ResourceEntry'])

        # Adding model 'ResourceSet'
        db.create_table('tomato_resourceset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('tomato', ['ResourceSet'])

        # Adding field 'Connection.bridge_id'
        db.add_column('tomato_connection', 'bridge_id', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Changing field 'Connection.attributes'
        db.alter_column('tomato_connection', 'attributes_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.AttributeSet'], null=True))

        # Adding field 'Connector.pos'
        db.add_column('tomato_connector', 'pos', self.gf('django.db.models.fields.CharField')(max_length=10, null=True), keep_default=False)

        # Adding field 'Connector.resources'
        db.add_column('tomato_connector', 'resources', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.ResourceSet'], null=True), keep_default=False)

        # Changing field 'Connector.attributes'
        db.alter_column('tomato_connector', 'attributes_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.AttributeSet'], null=True))

        # Adding field 'Topology.task'
        db.add_column('tomato_topology', 'task', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True), keep_default=False)

        # Adding field 'Topology.date_usage'
        db.add_column('tomato_topology', 'date_usage', self.gf('django.db.models.fields.DateTimeField')(default=datetime.date(2011, 3, 30)), keep_default=False)

        # Adding field 'Topology.date_modified'
        db.add_column('tomato_topology', 'date_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, default=datetime.date(2011, 3, 30), blank=True), keep_default=False)

        # Adding field 'Topology.date_created'
        db.add_column('tomato_topology', 'date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, default=datetime.date(2011, 3, 30), blank=True), keep_default=False)

        # Adding field 'Topology.resources'
        db.add_column('tomato_topology', 'resources', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.ResourceSet'], null=True), keep_default=False)

        # Changing field 'Topology.attributes'
        db.alter_column('tomato_topology', 'attributes_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.AttributeSet'], null=True))

        # Adding field 'Host.bridge_range_count'
        db.add_column('tomato_host', 'bridge_range_count', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1000), keep_default=False)

        # Adding field 'Host.hostserver_basedir'
        db.add_column('tomato_host', 'hostserver_basedir', self.gf('django.db.models.fields.CharField')(max_length=100, null=True), keep_default=False)

        # Adding field 'Host.bridge_range_start'
        db.add_column('tomato_host', 'bridge_range_start', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1000), keep_default=False)

        # Adding field 'Host.hostserver_secret_key'
        db.add_column('tomato_host', 'hostserver_secret_key', self.gf('django.db.models.fields.CharField')(max_length=100, null=True), keep_default=False)

        # Adding field 'Host.port_range_start'
        db.add_column('tomato_host', 'port_range_start', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=7000), keep_default=False)

        # Adding field 'Host.vmid_range_count'
        db.add_column('tomato_host', 'vmid_range_count', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=200), keep_default=False)

        # Adding field 'Host.port_range_count'
        db.add_column('tomato_host', 'port_range_count', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1000), keep_default=False)

        # Adding field 'Host.hostserver_port'
        db.add_column('tomato_host', 'hostserver_port', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True), keep_default=False)

        # Adding field 'Host.vmid_range_start'
        db.add_column('tomato_host', 'vmid_range_start', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1000), keep_default=False)

        # Changing field 'Host.attributes'
        db.alter_column('tomato_host', 'attributes_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.AttributeSet'], null=True))

        # Adding field 'ConfiguredInterface.use_dhcp'
        db.add_column('tomato_configuredinterface', 'use_dhcp', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True), keep_default=False)

        # Adding field 'ConfiguredInterface.ip4address'
        db.add_column('tomato_configuredinterface', 'ip4address', self.gf('django.db.models.fields.CharField')(max_length=18, null=True), keep_default=False)

        # Adding field 'TincConnection.tinc_port'
        db.add_column('tomato_tincconnection', 'tinc_port', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'TincConnection.gateway'
        db.add_column('tomato_tincconnection', 'gateway', self.gf('django.db.models.fields.CharField')(max_length=18, null=True), keep_default=False)

        # Adding field 'SpecialFeatureConnector.feature_group'
        db.add_column('tomato_specialfeatureconnector', 'feature_group', self.gf('django.db.models.fields.CharField')(default='', max_length=50, blank=True), keep_default=False)

        # Adding field 'SpecialFeatureConnector.feature_type'
        db.add_column('tomato_specialfeatureconnector', 'feature_type', self.gf('django.db.models.fields.CharField')(default='', max_length=50), keep_default=False)

        # Changing field 'Interface.attributes'
        db.alter_column('tomato_interface', 'attributes_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.AttributeSet'], null=True))

        # Adding field 'OpenVZDevice.vnc_port'
        db.add_column('tomato_openvzdevice', 'vnc_port', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'OpenVZDevice.openvz_id'
        db.add_column('tomato_openvzdevice', 'openvz_id', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'OpenVZDevice.root_password'
        db.add_column('tomato_openvzdevice', 'root_password', self.gf('django.db.models.fields.CharField')(max_length=50, null=True), keep_default=False)

        # Adding field 'OpenVZDevice.template'
        db.add_column('tomato_openvzdevice', 'template', self.gf('django.db.models.fields.CharField')(default='', max_length=30), keep_default=False)

        # Adding field 'OpenVZDevice.gateway'
        db.add_column('tomato_openvzdevice', 'gateway', self.gf('django.db.models.fields.CharField')(max_length=15, null=True), keep_default=False)

        # Adding field 'KVMDevice.vnc_port'
        db.add_column('tomato_kvmdevice', 'vnc_port', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'KVMDevice.template'
        db.add_column('tomato_kvmdevice', 'template', self.gf('django.db.models.fields.CharField')(default='', max_length=30), keep_default=False)

        # Adding field 'KVMDevice.kvm_id'
        db.add_column('tomato_kvmdevice', 'kvm_id', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'EmulatedConnection.delay'
        db.add_column('tomato_emulatedconnection', 'delay', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'EmulatedConnection.capture'
        db.add_column('tomato_emulatedconnection', 'capture', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True), keep_default=False)

        # Adding field 'EmulatedConnection.bandwidth'
        db.add_column('tomato_emulatedconnection', 'bandwidth', self.gf('django.db.models.fields.IntegerField')(default=10000, null=True), keep_default=False)

        # Adding field 'EmulatedConnection.lossratio'
        db.add_column('tomato_emulatedconnection', 'lossratio', self.gf('django.db.models.fields.FloatField')(null=True), keep_default=False)

        # Adding field 'Device.pos'
        db.add_column('tomato_device', 'pos', self.gf('django.db.models.fields.CharField')(max_length=10, null=True), keep_default=False)

        # Adding field 'Device.hostgroup'
        db.add_column('tomato_device', 'hostgroup', self.gf('django.db.models.fields.CharField')(max_length=10, null=True), keep_default=False)

        # Adding field 'Device.resources'
        db.add_column('tomato_device', 'resources', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.ResourceSet'], null=True), keep_default=False)

        # Changing field 'Device.attributes'
        db.alter_column('tomato_device', 'attributes_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.AttributeSet'], null=True))
    
    
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
            'connector': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Connector']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interface': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Interface']", 'unique': 'True'})
        },
        'tomato.connector': {
            'Meta': {'object_name': 'Connector'},
            'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '10'}),
            'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'tomato.device': {
            'Meta': {'object_name': 'Device'},
            'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']"}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Host']", 'null': 'True'}),
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
        'tomato.host': {
            'Meta': {'object_name': 'Host'},
            'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']"}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        'tomato.interface': {
            'Meta': {'object_name': 'Interface'},
            'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']"}),
            'device': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Device']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '5'})
        },
        'tomato.kvmdevice': {
            'Meta': {'object_name': 'KVMDevice', '_ormbases': ['tomato.Device']},
            'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Device']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.openvzdevice': {
            'Meta': {'object_name': 'OpenVZDevice', '_ormbases': ['tomato.Device']},
            'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Device']", 'unique': 'True', 'primary_key': 'True'})
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
            'emulatedconnection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.EmulatedConnection']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.tincconnector': {
            'Meta': {'object_name': 'TincConnector', '_ormbases': ['tomato.Connector']},
            'connector_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connector']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.topology': {
            'Meta': {'object_name': 'Topology'},
            'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'owner': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        }
    }
    
    complete_apps = ['tomato']
