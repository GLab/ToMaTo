
from south.db import db
from django.db import models
from glabnetman.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Deleting model 'dhcpddevice'
        db.delete_table('glabnetman_dhcpddevice')
        
    
    
    def backwards(self, orm):
        
        # Adding model 'dhcpddevice'
        db.create_table('glabnetman_dhcpddevice', (
            ('subnet', orm['glabnetman.dhcpddevice:subnet']),
            ('device_ptr', orm['glabnetman.dhcpddevice:device_ptr']),
            ('netmask', orm['glabnetman.dhcpddevice:netmask']),
            ('range', orm['glabnetman.dhcpddevice:range']),
            ('nameserver', orm['glabnetman.dhcpddevice:nameserver']),
            ('gateway', orm['glabnetman.dhcpddevice:gateway']),
        ))
        db.send_create_signal('glabnetman', ['dhcpddevice'])
        
    
    
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
        'glabnetman.template': {
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '12'})
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
