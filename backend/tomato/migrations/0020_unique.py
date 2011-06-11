# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding unique constraint on 'Permission', fields ['user', 'topology']
        db.create_unique('tomato_permission', ['user', 'topology_id'])

        # Adding unique constraint on 'Device', fields ['name', 'topology']
        db.create_unique('tomato_device', ['name', 'topology_id'])

        # Adding unique constraint on 'Connection', fields ['connector', 'interface']
        db.create_unique('tomato_connection', ['connector_id', 'interface_id'])

        # Adding unique constraint on 'Connector', fields ['name', 'topology']
        db.create_unique('tomato_connector', ['name', 'topology_id'])

        # Adding unique constraint on 'Interface', fields ['device', 'name']
        db.create_unique('tomato_interface', ['device_id', 'name'])

        # Adding unique constraint on 'PhysicalLink', fields ['dst_group', 'src_group']
        db.create_unique('tomato_physicallink', ['dst_group', 'src_group'])

        # Adding unique constraint on 'Template', fields ['type', 'name']
        db.create_unique('tomato_template', ['type', 'name'])

        # Adding unique constraint on 'ExternalNetwork', fields ['type', 'group']
        db.create_unique('tomato_externalnetwork', ['type', 'group'])
    
    
    def backwards(self, orm):
        
        # Removing unique constraint on 'Permission', fields ['user', 'topology']
        db.delete_unique('tomato_permission', ['user', 'topology_id'])

        # Removing unique constraint on 'Device', fields ['name', 'topology']
        db.delete_unique('tomato_device', ['name', 'topology_id'])

        # Removing unique constraint on 'Connection', fields ['connector', 'interface']
        db.delete_unique('tomato_connection', ['connector_id', 'interface_id'])

        # Removing unique constraint on 'Connector', fields ['name', 'topology']
        db.delete_unique('tomato_connector', ['name', 'topology_id'])

        # Removing unique constraint on 'Interface', fields ['device', 'name']
        db.delete_unique('tomato_interface', ['device_id', 'name'])

        # Removing unique constraint on 'PhysicalLink', fields ['dst_group', 'src_group']
        db.delete_unique('tomato_physicallink', ['dst_group', 'src_group'])

        # Removing unique constraint on 'Template', fields ['type', 'name']
        db.delete_unique('tomato_template', ['type', 'name'])

        # Removing unique constraint on 'ExternalNetwork', fields ['type', 'group']
        db.delete_unique('tomato_externalnetwork', ['type', 'group'])
    
    
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
            'Meta': {'unique_together': "(('group', 'type'),)", 'object_name': 'ExternalNetwork'},
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
            'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
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
            'Meta': {'unique_together': "(('topology', 'user'),)", 'object_name': 'Permission'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '30'})
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
        'tomato.template': {
            'Meta': {'unique_together': "(('name', 'type'),)", 'object_name': 'Template'},
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
            'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
            'date_usage': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'owner': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'task': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'})
        }
    }
    
    complete_apps = ['tomato']
