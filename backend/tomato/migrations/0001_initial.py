# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Error'
        db.create_table('tomato_error', (
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('message', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('tomato', ['Error'])

        # Adding model 'HostGroup'
        db.create_table('tomato_hostgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal('tomato', ['HostGroup'])

        # Adding model 'Host'
        db.create_table('tomato_host', (
            ('bridge_range_count', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1000)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostGroup'])),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('bridge_range_start', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1000)),
            ('port_range_start', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=7000)),
            ('vmid_range_count', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=200)),
            ('port_range_count', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1000)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('vmid_range_start', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1000)),
        ))
        db.send_create_signal('tomato', ['Host'])

        # Adding model 'Template'
        db.create_table('tomato_template', (
            ('default', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=12)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('download_url', self.gf('django.db.models.fields.CharField')(default='', max_length=255)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('tomato', ['Template'])

        # Adding model 'PhysicalLink'
        db.create_table('tomato_physicallink', (
            ('loss', self.gf('django.db.models.fields.FloatField')()),
            ('dst_group', self.gf('django.db.models.fields.related.ForeignKey')(related_name='reverselink', to=orm['tomato.HostGroup'])),
            ('src_group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostGroup'])),
            ('delay_avg', self.gf('django.db.models.fields.FloatField')()),
            ('delay_stddev', self.gf('django.db.models.fields.FloatField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('tomato', ['PhysicalLink'])

        # Adding model 'SpecialFeature'
        db.create_table('tomato_specialfeature', (
            ('bridge', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('host', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Host'])),
            ('feature_group', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('feature_type', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('tomato', ['SpecialFeature'])

        # Adding model 'Resources'
        db.create_table('tomato_resources', (
            ('ports', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('disk', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('special', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('memory', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('tomato', ['Resources'])

        # Adding model 'Topology'
        db.create_table('tomato_topology', (
            ('task', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('date_usage', self.gf('django.db.models.fields.DateTimeField')()),
            ('date_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('owner', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('resources', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Resources'], null=True)),
        ))
        db.send_create_signal('tomato', ['Topology'])

        # Adding model 'Permission'
        db.create_table('tomato_permission', (
            ('user', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('role', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('topology', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Topology'])),
        ))
        db.send_create_signal('tomato', ['Permission'])

        # Adding model 'Device'
        db.create_table('tomato_device', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('pos', self.gf('django.db.models.fields.CharField')(max_length=10, null=True)),
            ('hostgroup', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostGroup'], null=True)),
            ('state', self.gf('django.db.models.fields.CharField')(default='created', max_length=10)),
            ('host', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Host'], null=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('resources', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Resources'], null=True)),
            ('topology', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Topology'])),
        ))
        db.send_create_signal('tomato', ['Device'])

        # Adding model 'Interface'
        db.create_table('tomato_interface', (
            ('device', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Device'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=5)),
        ))
        db.send_create_signal('tomato', ['Interface'])

        # Adding model 'Connector'
        db.create_table('tomato_connector', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('pos', self.gf('django.db.models.fields.CharField')(max_length=10, null=True)),
            ('state', self.gf('django.db.models.fields.CharField')(default='created', max_length=10)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('resources', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Resources'], null=True)),
            ('topology', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Topology'])),
        ))
        db.send_create_signal('tomato', ['Connector'])

        # Adding model 'Connection'
        db.create_table('tomato_connection', (
            ('connector', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Connector'])),
            ('interface', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Interface'], unique=True)),
            ('bridge_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('tomato', ['Connection'])

        # Adding model 'EmulatedConnection'
        db.create_table('tomato_emulatedconnection', (
            ('delay', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('capture', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('bandwidth', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('connection_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Connection'], unique=True, primary_key=True)),
            ('lossratio', self.gf('django.db.models.fields.FloatField')(null=True)),
        ))
        db.send_create_signal('tomato', ['EmulatedConnection'])

        # Adding model 'KVMDevice'
        db.create_table('tomato_kvmdevice', (
            ('device_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Device'], unique=True, primary_key=True)),
            ('template', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('kvm_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('vnc_port', self.gf('django.db.models.fields.IntegerField')(null=True)),
        ))
        db.send_create_signal('tomato', ['KVMDevice'])

        # Adding model 'OpenVZDevice'
        db.create_table('tomato_openvzdevice', (
            ('device_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Device'], unique=True, primary_key=True)),
            ('vnc_port', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('openvz_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('root_password', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('template', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('gateway', self.gf('django.db.models.fields.CharField')(max_length=15, null=True)),
        ))
        db.send_create_signal('tomato', ['OpenVZDevice'])

        # Adding model 'ConfiguredInterface'
        db.create_table('tomato_configuredinterface', (
            ('use_dhcp', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('ip4address', self.gf('django.db.models.fields.CharField')(max_length=18, null=True)),
            ('interface_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Interface'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['ConfiguredInterface'])

        # Adding model 'TincConnector'
        db.create_table('tomato_tincconnector', (
            ('connector_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Connector'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['TincConnector'])

        # Adding model 'TincConnection'
        db.create_table('tomato_tincconnection', (
            ('tinc_port', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('emulatedconnection_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.EmulatedConnection'], unique=True, primary_key=True)),
            ('gateway', self.gf('django.db.models.fields.CharField')(max_length=18, null=True)),
        ))
        db.send_create_signal('tomato', ['TincConnection'])

        # Adding model 'SpecialFeatureConnector'
        db.create_table('tomato_specialfeatureconnector', (
            ('feature_group', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('feature_type', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('connector_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Connector'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['SpecialFeatureConnector'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Error'
        db.delete_table('tomato_error')

        # Deleting model 'HostGroup'
        db.delete_table('tomato_hostgroup')

        # Deleting model 'Host'
        db.delete_table('tomato_host')

        # Deleting model 'Template'
        db.delete_table('tomato_template')

        # Deleting model 'PhysicalLink'
        db.delete_table('tomato_physicallink')

        # Deleting model 'SpecialFeature'
        db.delete_table('tomato_specialfeature')

        # Deleting model 'Resources'
        db.delete_table('tomato_resources')

        # Deleting model 'Topology'
        db.delete_table('tomato_topology')

        # Deleting model 'Permission'
        db.delete_table('tomato_permission')

        # Deleting model 'Device'
        db.delete_table('tomato_device')

        # Deleting model 'Interface'
        db.delete_table('tomato_interface')

        # Deleting model 'Connector'
        db.delete_table('tomato_connector')

        # Deleting model 'Connection'
        db.delete_table('tomato_connection')

        # Deleting model 'EmulatedConnection'
        db.delete_table('tomato_emulatedconnection')

        # Deleting model 'KVMDevice'
        db.delete_table('tomato_kvmdevice')

        # Deleting model 'OpenVZDevice'
        db.delete_table('tomato_openvzdevice')

        # Deleting model 'ConfiguredInterface'
        db.delete_table('tomato_configuredinterface')

        # Deleting model 'TincConnector'
        db.delete_table('tomato_tincconnector')

        # Deleting model 'TincConnection'
        db.delete_table('tomato_tincconnection')

        # Deleting model 'SpecialFeatureConnector'
        db.delete_table('tomato_specialfeatureconnector')
    
    
    models = {
        'tomato.configuredinterface': {
            'Meta': {'object_name': 'ConfiguredInterface', '_ormbases': ['tomato.Interface']},
            'interface_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Interface']", 'unique': 'True', 'primary_key': 'True'}),
            'ip4address': ('django.db.models.fields.CharField', [], {'max_length': '18', 'null': 'True'}),
            'use_dhcp': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'tomato.connection': {
            'Meta': {'object_name': 'Connection'},
            'bridge_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'connector': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Connector']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interface': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Interface']", 'unique': 'True'})
        },
        'tomato.connector': {
            'Meta': {'object_name': 'Connector'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'pos': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'resources': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Resources']", 'null': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '10'}),
            'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'tomato.device': {
            'Meta': {'object_name': 'Device'},
            'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Host']", 'null': 'True'}),
            'hostgroup': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.HostGroup']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'pos': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'resources': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Resources']", 'null': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '10'}),
            'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'tomato.emulatedconnection': {
            'Meta': {'object_name': 'EmulatedConnection', '_ormbases': ['tomato.Connection']},
            'bandwidth': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
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
            'bridge_range_count': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1000'}),
            'bridge_range_start': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1000'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.HostGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'port_range_count': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1000'}),
            'port_range_start': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '7000'}),
            'vmid_range_count': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '200'}),
            'vmid_range_start': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1000'})
        },
        'tomato.hostgroup': {
            'Meta': {'object_name': 'HostGroup'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'tomato.interface': {
            'Meta': {'object_name': 'Interface'},
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
            'dst_group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reverselink'", 'to': "orm['tomato.HostGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loss': ('django.db.models.fields.FloatField', [], {}),
            'src_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.HostGroup']"})
        },
        'tomato.resources': {
            'Meta': {'object_name': 'Resources'},
            'disk': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'memory': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'ports': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'special': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'tomato.specialfeature': {
            'Meta': {'object_name': 'SpecialFeature'},
            'bridge': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'feature_group': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'feature_type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Host']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'tomato.specialfeatureconnector': {
            'Meta': {'object_name': 'SpecialFeatureConnector', '_ormbases': ['tomato.Connector']},
            'connector_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connector']", 'unique': 'True', 'primary_key': 'True'}),
            'feature_group': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'feature_type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
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
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'date_usage': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'owner': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'resources': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Resources']", 'null': 'True'}),
            'task': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        }
    }
    
    complete_apps = ['tomato']
