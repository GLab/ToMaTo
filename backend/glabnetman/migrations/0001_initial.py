
from south.db import db
from django.db import models
from glabnetman.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Host'
        db.create_table('glabnetman_host', (
            ('id', orm['glabnetman.Host:id']),
            ('group', orm['glabnetman.Host:group']),
            ('name', orm['glabnetman.Host:name']),
            ('public_bridge', orm['glabnetman.Host:public_bridge']),
        ))
        db.send_create_signal('glabnetman', ['Host'])
        
        # Adding model 'TincConnector'
        db.create_table('glabnetman_tincconnector', (
            ('connector_ptr', orm['glabnetman.TincConnector:connector_ptr']),
        ))
        db.send_create_signal('glabnetman', ['TincConnector'])
        
        # Adding model 'TincConnection'
        db.create_table('glabnetman_tincconnection', (
            ('emulatedconnection_ptr', orm['glabnetman.TincConnection:emulatedconnection_ptr']),
            ('tinc_port', orm['glabnetman.TincConnection:tinc_port']),
            ('gateway_ip', orm['glabnetman.TincConnection:gateway_ip']),
            ('gateway_netmask', orm['glabnetman.TincConnection:gateway_netmask']),
        ))
        db.send_create_signal('glabnetman', ['TincConnection'])
        
        # Adding model 'Topology'
        db.create_table('glabnetman_topology', (
            ('id', orm['glabnetman.Topology:id']),
            ('name', orm['glabnetman.Topology:name']),
            ('owner', orm['glabnetman.Topology:owner']),
            ('date_created', orm['glabnetman.Topology:date_created']),
            ('date_modified', orm['glabnetman.Topology:date_modified']),
            ('task', orm['glabnetman.Topology:task']),
        ))
        db.send_create_signal('glabnetman', ['Topology'])
        
        # Adding model 'KVMDevice'
        db.create_table('glabnetman_kvmdevice', (
            ('device_ptr', orm['glabnetman.KVMDevice:device_ptr']),
            ('kvm_id', orm['glabnetman.KVMDevice:kvm_id']),
            ('template', orm['glabnetman.KVMDevice:template']),
            ('vnc_port', orm['glabnetman.KVMDevice:vnc_port']),
        ))
        db.send_create_signal('glabnetman', ['KVMDevice'])
        
        # Adding model 'Interface'
        db.create_table('glabnetman_interface', (
            ('id', orm['glabnetman.Interface:id']),
            ('name', orm['glabnetman.Interface:name']),
            ('device', orm['glabnetman.Interface:device']),
        ))
        db.send_create_signal('glabnetman', ['Interface'])
        
        # Adding model 'DhcpdDevice'
        db.create_table('glabnetman_dhcpddevice', (
            ('device_ptr', orm['glabnetman.DhcpdDevice:device_ptr']),
            ('subnet', orm['glabnetman.DhcpdDevice:subnet']),
            ('netmask', orm['glabnetman.DhcpdDevice:netmask']),
            ('range', orm['glabnetman.DhcpdDevice:range']),
            ('gateway', orm['glabnetman.DhcpdDevice:gateway']),
            ('nameserver', orm['glabnetman.DhcpdDevice:nameserver']),
        ))
        db.send_create_signal('glabnetman', ['DhcpdDevice'])
        
        # Adding model 'Connection'
        db.create_table('glabnetman_connection', (
            ('id', orm['glabnetman.Connection:id']),
            ('connector', orm['glabnetman.Connection:connector']),
            ('interface', orm['glabnetman.Connection:interface']),
            ('bridge_id', orm['glabnetman.Connection:bridge_id']),
            ('bridge_special_name', orm['glabnetman.Connection:bridge_special_name']),
        ))
        db.send_create_signal('glabnetman', ['Connection'])
        
        # Adding model 'ConfiguredInterface'
        db.create_table('glabnetman_configuredinterface', (
            ('interface_ptr', orm['glabnetman.ConfiguredInterface:interface_ptr']),
            ('use_dhcp', orm['glabnetman.ConfiguredInterface:use_dhcp']),
            ('ip4address', orm['glabnetman.ConfiguredInterface:ip4address']),
            ('ip4netmask', orm['glabnetman.ConfiguredInterface:ip4netmask']),
        ))
        db.send_create_signal('glabnetman', ['ConfiguredInterface'])
        
        # Adding model 'InternetConnector'
        db.create_table('glabnetman_internetconnector', (
            ('connector_ptr', orm['glabnetman.InternetConnector:connector_ptr']),
        ))
        db.send_create_signal('glabnetman', ['InternetConnector'])
        
        # Adding model 'OpenVZDevice'
        db.create_table('glabnetman_openvzdevice', (
            ('device_ptr', orm['glabnetman.OpenVZDevice:device_ptr']),
            ('openvz_id', orm['glabnetman.OpenVZDevice:openvz_id']),
            ('root_password', orm['glabnetman.OpenVZDevice:root_password']),
            ('template', orm['glabnetman.OpenVZDevice:template']),
            ('vnc_port', orm['glabnetman.OpenVZDevice:vnc_port']),
        ))
        db.send_create_signal('glabnetman', ['OpenVZDevice'])
        
        # Adding model 'Device'
        db.create_table('glabnetman_device', (
            ('id', orm['glabnetman.Device:id']),
            ('name', orm['glabnetman.Device:name']),
            ('topology', orm['glabnetman.Device:topology']),
            ('type', orm['glabnetman.Device:type']),
            ('state', orm['glabnetman.Device:state']),
            ('pos', orm['glabnetman.Device:pos']),
            ('host', orm['glabnetman.Device:host']),
            ('hostgroup', orm['glabnetman.Device:hostgroup']),
        ))
        db.send_create_signal('glabnetman', ['Device'])
        
        # Adding model 'Connector'
        db.create_table('glabnetman_connector', (
            ('id', orm['glabnetman.Connector:id']),
            ('name', orm['glabnetman.Connector:name']),
            ('topology', orm['glabnetman.Connector:topology']),
            ('type', orm['glabnetman.Connector:type']),
            ('state', orm['glabnetman.Connector:state']),
            ('pos', orm['glabnetman.Connector:pos']),
        ))
        db.send_create_signal('glabnetman', ['Connector'])
        
        # Adding model 'HostGroup'
        db.create_table('glabnetman_hostgroup', (
            ('id', orm['glabnetman.HostGroup:id']),
            ('name', orm['glabnetman.HostGroup:name']),
        ))
        db.send_create_signal('glabnetman', ['HostGroup'])
        
        # Adding model 'EmulatedConnection'
        db.create_table('glabnetman_emulatedconnection', (
            ('connection_ptr', orm['glabnetman.EmulatedConnection:connection_ptr']),
            ('delay', orm['glabnetman.EmulatedConnection:delay']),
            ('bandwidth', orm['glabnetman.EmulatedConnection:bandwidth']),
            ('lossratio', orm['glabnetman.EmulatedConnection:lossratio']),
        ))
        db.send_create_signal('glabnetman', ['EmulatedConnection'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Host'
        db.delete_table('glabnetman_host')
        
        # Deleting model 'TincConnector'
        db.delete_table('glabnetman_tincconnector')
        
        # Deleting model 'TincConnection'
        db.delete_table('glabnetman_tincconnection')
        
        # Deleting model 'Topology'
        db.delete_table('glabnetman_topology')
        
        # Deleting model 'KVMDevice'
        db.delete_table('glabnetman_kvmdevice')
        
        # Deleting model 'Interface'
        db.delete_table('glabnetman_interface')
        
        # Deleting model 'DhcpdDevice'
        db.delete_table('glabnetman_dhcpddevice')
        
        # Deleting model 'Connection'
        db.delete_table('glabnetman_connection')
        
        # Deleting model 'ConfiguredInterface'
        db.delete_table('glabnetman_configuredinterface')
        
        # Deleting model 'InternetConnector'
        db.delete_table('glabnetman_internetconnector')
        
        # Deleting model 'OpenVZDevice'
        db.delete_table('glabnetman_openvzdevice')
        
        # Deleting model 'Device'
        db.delete_table('glabnetman_device')
        
        # Deleting model 'Connector'
        db.delete_table('glabnetman_connector')
        
        # Deleting model 'HostGroup'
        db.delete_table('glabnetman_hostgroup')
        
        # Deleting model 'EmulatedConnection'
        db.delete_table('glabnetman_emulatedconnection')
        
    
    
    models = {
        'glabnetman.configuredinterface': {
            'interface_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['glabnetman.Interface']", 'unique': 'True', 'primary_key': 'True'}),
            'ip4address': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'ip4netmask': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'use_dhcp': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'glabnetman.connection': {
            'bridge_id': ('django.db.models.fields.IntegerField', [], {}),
            'bridge_special_name': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'connector': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['glabnetman.Connector']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interface': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['glabnetman.Interface']", 'unique': 'True'})
        },
        'glabnetman.connector': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'pos': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '10'}),
            'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['glabnetman.Topology']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'glabnetman.device': {
            'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['glabnetman.Host']"}),
            'hostgroup': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['glabnetman.HostGroup']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'pos': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '10'}),
            'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['glabnetman.Topology']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'glabnetman.dhcpddevice': {
            'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['glabnetman.Device']", 'unique': 'True', 'primary_key': 'True'}),
            'gateway': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'nameserver': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'netmask': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'range': ('django.db.models.fields.CharField', [], {'max_length': '31'}),
            'subnet': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        'glabnetman.emulatedconnection': {
            'bandwidth': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'connection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['glabnetman.Connection']", 'unique': 'True', 'primary_key': 'True'}),
            'delay': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'lossratio': ('django.db.models.fields.FloatField', [], {'null': 'True'})
        },
        'glabnetman.host': {
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['glabnetman.HostGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'public_bridge': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'glabnetman.hostgroup': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'glabnetman.interface': {
            'device': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['glabnetman.Device']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '5'})
        },
        'glabnetman.internetconnector': {
            'connector_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['glabnetman.Connector']", 'unique': 'True', 'primary_key': 'True'})
        },
        'glabnetman.kvmdevice': {
            'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['glabnetman.Device']", 'unique': 'True', 'primary_key': 'True'}),
            'kvm_id': ('django.db.models.fields.IntegerField', [], {}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'vnc_port': ('django.db.models.fields.IntegerField', [], {})
        },
        'glabnetman.openvzdevice': {
            'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['glabnetman.Device']", 'unique': 'True', 'primary_key': 'True'}),
            'openvz_id': ('django.db.models.fields.IntegerField', [], {}),
            'root_password': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'vnc_port': ('django.db.models.fields.IntegerField', [], {})
        },
        'glabnetman.tincconnection': {
            'emulatedconnection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['glabnetman.EmulatedConnection']", 'unique': 'True', 'primary_key': 'True'}),
            'gateway_ip': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'gateway_netmask': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'tinc_port': ('django.db.models.fields.IntegerField', [], {})
        },
        'glabnetman.tincconnector': {
            'connector_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['glabnetman.Connector']", 'unique': 'True', 'primary_key': 'True'})
        },
        'glabnetman.topology': {
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'owner': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'task': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        }
    }
    
    complete_apps = ['glabnetman']
