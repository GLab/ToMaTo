# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Deleting model 'OpenVZDevice'
        db.delete_table('tomato_openvzdevice')

        # Deleting model 'TincConnection'
        db.delete_table('tomato_tincconnection')

        # Deleting model 'EmulatedConnection'
        db.delete_table('tomato_emulatedconnection')

        # Deleting model 'KVMDevice'
        db.delete_table('tomato_kvmdevice')

        # Deleting model 'TincConnector'
        db.delete_table('tomato_tincconnector')

        # Deleting model 'ConfiguredInterface'
        db.delete_table('tomato_configuredinterface')
    
    
    def backwards(self, orm):
        
        # Adding model 'OpenVZDevice'
        db.create_table('tomato_openvzdevice', (
            ('device_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Device'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['OpenVZDevice'])

        # Adding model 'TincConnection'
        db.create_table('tomato_tincconnection', (
            ('emulatedconnection_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.EmulatedConnection'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['TincConnection'])

        # Adding model 'EmulatedConnection'
        db.create_table('tomato_emulatedconnection', (
            ('connection_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Connection'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['EmulatedConnection'])

        # Adding model 'KVMDevice'
        db.create_table('tomato_kvmdevice', (
            ('device_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Device'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['KVMDevice'])

        # Adding model 'TincConnector'
        db.create_table('tomato_tincconnector', (
            ('connector_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Connector'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['TincConnector'])

        # Adding model 'ConfiguredInterface'
        db.create_table('tomato_configuredinterface', (
            ('interface_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Interface'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['ConfiguredInterface'])
    
    
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
        'tomato.topology': {
            'Meta': {'object_name': 'Topology'},
            'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'owner': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        }
    }
    
    complete_apps = ['tomato']
