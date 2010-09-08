
from south.db import db
from django.db import models
from glabnetman.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Changing field 'TincConnection.tinc_port'
        # (to signature: django.db.models.fields.IntegerField(null=True))
        db.alter_column('glabnetman_tincconnection', 'tinc_port', orm['glabnetman.tincconnection:tinc_port'])
        
        # Changing field 'KVMDevice.vnc_port'
        # (to signature: django.db.models.fields.IntegerField(null=True))
        db.alter_column('glabnetman_kvmdevice', 'vnc_port', orm['glabnetman.kvmdevice:vnc_port'])
        
        # Changing field 'KVMDevice.kvm_id'
        # (to signature: django.db.models.fields.IntegerField(null=True))
        db.alter_column('glabnetman_kvmdevice', 'kvm_id', orm['glabnetman.kvmdevice:kvm_id'])
        
        # Changing field 'Connection.bridge_id'
        # (to signature: django.db.models.fields.IntegerField(null=True))
        db.alter_column('glabnetman_connection', 'bridge_id', orm['glabnetman.connection:bridge_id'])
        
        # Changing field 'OpenVZDevice.vnc_port'
        # (to signature: django.db.models.fields.IntegerField(null=True))
        db.alter_column('glabnetman_openvzdevice', 'vnc_port', orm['glabnetman.openvzdevice:vnc_port'])
        
        # Changing field 'OpenVZDevice.openvz_id'
        # (to signature: django.db.models.fields.IntegerField(null=True))
        db.alter_column('glabnetman_openvzdevice', 'openvz_id', orm['glabnetman.openvzdevice:openvz_id'])
        
    
    
    def backwards(self, orm):
        
        # Changing field 'TincConnection.tinc_port'
        # (to signature: django.db.models.fields.IntegerField())
        db.alter_column('glabnetman_tincconnection', 'tinc_port', orm['glabnetman.tincconnection:tinc_port'])
        
        # Changing field 'KVMDevice.vnc_port'
        # (to signature: django.db.models.fields.IntegerField())
        db.alter_column('glabnetman_kvmdevice', 'vnc_port', orm['glabnetman.kvmdevice:vnc_port'])
        
        # Changing field 'KVMDevice.kvm_id'
        # (to signature: django.db.models.fields.IntegerField())
        db.alter_column('glabnetman_kvmdevice', 'kvm_id', orm['glabnetman.kvmdevice:kvm_id'])
        
        # Changing field 'Connection.bridge_id'
        # (to signature: django.db.models.fields.IntegerField())
        db.alter_column('glabnetman_connection', 'bridge_id', orm['glabnetman.connection:bridge_id'])
        
        # Changing field 'OpenVZDevice.vnc_port'
        # (to signature: django.db.models.fields.IntegerField())
        db.alter_column('glabnetman_openvzdevice', 'vnc_port', orm['glabnetman.openvzdevice:vnc_port'])
        
        # Changing field 'OpenVZDevice.openvz_id'
        # (to signature: django.db.models.fields.IntegerField())
        db.alter_column('glabnetman_openvzdevice', 'openvz_id', orm['glabnetman.openvzdevice:openvz_id'])
        
    
    
    models = {
        'glabnetman.configuredinterface': {
            'gateway': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'interface_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['glabnetman.Interface']", 'unique': 'True', 'primary_key': 'True'}),
            'ip4address': ('django.db.models.fields.CharField', [], {'max_length': '18', 'null': 'True'}),
            'use_dhcp': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'glabnetman.connection': {
            'bridge_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
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
        'glabnetman.error': {
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'glabnetman.host': {
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['glabnetman.HostGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
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
            'kvm_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'vnc_port': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        },
        'glabnetman.openvzdevice': {
            'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['glabnetman.Device']", 'unique': 'True', 'primary_key': 'True'}),
            'openvz_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'root_password': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'vnc_port': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        },
        'glabnetman.permission': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['glabnetman.Topology']"}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'glabnetman.template': {
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '12'})
        },
        'glabnetman.tincconnection': {
            'emulatedconnection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['glabnetman.EmulatedConnection']", 'unique': 'True', 'primary_key': 'True'}),
            'gateway': ('django.db.models.fields.CharField', [], {'max_length': '18', 'null': 'True'}),
            'tinc_port': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
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
