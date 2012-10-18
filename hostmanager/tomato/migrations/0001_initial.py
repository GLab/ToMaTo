# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'UsageStatistics'
        db.create_table('tomato_usagestatistics', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('begin', self.gf('django.db.models.fields.FloatField')()),
            ('attrs', self.gf('tomato.lib.db.JSONField')()),
        ))
        db.send_create_signal('tomato', ['UsageStatistics'])

        # Adding model 'UsageRecord'
        db.create_table('tomato_usagerecord', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('statistics', self.gf('django.db.models.fields.related.ForeignKey')(related_name='records', to=orm['tomato.UsageStatistics'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('begin', self.gf('django.db.models.fields.FloatField')()),
            ('end', self.gf('django.db.models.fields.FloatField')()),
            ('measurements', self.gf('django.db.models.fields.IntegerField')()),
            ('memory', self.gf('django.db.models.fields.FloatField')()),
            ('diskspace', self.gf('django.db.models.fields.FloatField')()),
            ('traffic', self.gf('django.db.models.fields.FloatField')()),
            ('cputime', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('tomato', ['UsageRecord'])

        # Adding model 'Connection'
        db.create_table('tomato_connection', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('owner', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('usageStatistics', self.gf('django.db.models.fields.related.OneToOneField')(related_name='connection', unique=True, null=True, to=orm['tomato.UsageStatistics'])),
            ('attrs', self.gf('tomato.lib.db.JSONField')()),
        ))
        db.send_create_signal('tomato', ['Connection'])

        # Adding model 'Element'
        db.create_table('tomato_element', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('owner', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='children', null=True, to=orm['tomato.Element'])),
            ('connection', self.gf('django.db.models.fields.related.ForeignKey')(related_name='elements', null=True, to=orm['tomato.Connection'])),
            ('usageStatistics', self.gf('django.db.models.fields.related.OneToOneField')(related_name='element', unique=True, null=True, to=orm['tomato.UsageStatistics'])),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('attrs', self.gf('tomato.lib.db.JSONField')()),
        ))
        db.send_create_signal('tomato', ['Element'])

        # Adding model 'Resource'
        db.create_table('tomato_resource', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('attrs', self.gf('tomato.lib.db.JSONField')()),
        ))
        db.send_create_signal('tomato', ['Resource'])

        # Adding model 'ResourceInstance'
        db.create_table('tomato_resourceinstance', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('num', self.gf('django.db.models.fields.IntegerField')()),
            ('ownerElement', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Element'], null=True)),
            ('ownerConnection', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Connection'], null=True)),
            ('attrs', self.gf('tomato.lib.db.JSONField')()),
        ))
        db.send_create_signal('tomato', ['ResourceInstance'])

        # Adding unique constraint on 'ResourceInstance', fields ['num', 'type']
        db.create_unique('tomato_resourceinstance', ['num', 'type'])

        # Adding model 'Template'
        db.create_table('tomato_template', (
            ('resource_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Resource'], unique=True, primary_key=True)),
            ('tech', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('preference', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('tomato', ['Template'])

        # Adding model 'KVMQM'
        db.create_table('tomato_kvmqm', (
            ('element_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Element'], unique=True, primary_key=True)),
            ('template', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Template'], null=True)),
        ))
        db.send_create_signal('tomato', ['KVMQM'])

        # Adding model 'KVMQM_Interface'
        db.create_table('tomato_kvm_interface', (
            ('element_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Element'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['KVMQM_Interface'])

        # Adding model 'OpenVZ'
        db.create_table('tomato_openvz', (
            ('element_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Element'], unique=True, primary_key=True)),
            ('template', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Resource'], null=True)),
        ))
        db.send_create_signal('tomato', ['OpenVZ'])

        # Adding model 'OpenVZ_Interface'
        db.create_table('tomato_openvz_interface', (
            ('element_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Element'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['OpenVZ_Interface'])

        # Adding model 'Repy'
        db.create_table('tomato_repy', (
            ('element_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Element'], unique=True, primary_key=True)),
            ('template', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Template'], null=True)),
        ))
        db.send_create_signal('tomato', ['Repy'])

        # Adding model 'Repy_Interface'
        db.create_table('tomato_repy_interface', (
            ('element_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Element'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['Repy_Interface'])

        # Adding model 'Network'
        db.create_table('tomato_network', (
            ('resource_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Resource'], unique=True, primary_key=True)),
            ('kind', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('bridge', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20)),
            ('preference', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('tomato', ['Network'])

        # Adding model 'External_Network'
        db.create_table('tomato_external_network', (
            ('element_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Element'], unique=True, primary_key=True)),
            ('network', self.gf('django.db.models.fields.related.ForeignKey')(related_name='instances', null=True, to=orm['tomato.Network'])),
        ))
        db.send_create_signal('tomato', ['External_Network'])

        # Adding model 'UDP_Tunnel'
        db.create_table('tomato_udp_tunnel', (
            ('element_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Element'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['UDP_Tunnel'])

        # Adding model 'Tinc'
        db.create_table('tomato_tinc', (
            ('element_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Element'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['Tinc'])

        # Adding model 'Bridge'
        db.create_table('tomato_bridge', (
            ('connection_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Connection'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['Bridge'])

        # Adding model 'Fixed_Bridge'
        db.create_table('tomato_fixed_bridge', (
            ('connection_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Connection'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['Fixed_Bridge'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'ResourceInstance', fields ['num', 'type']
        db.delete_unique('tomato_resourceinstance', ['num', 'type'])

        # Deleting model 'UsageStatistics'
        db.delete_table('tomato_usagestatistics')

        # Deleting model 'UsageRecord'
        db.delete_table('tomato_usagerecord')

        # Deleting model 'Connection'
        db.delete_table('tomato_connection')

        # Deleting model 'Element'
        db.delete_table('tomato_element')

        # Deleting model 'Resource'
        db.delete_table('tomato_resource')

        # Deleting model 'ResourceInstance'
        db.delete_table('tomato_resourceinstance')

        # Deleting model 'Template'
        db.delete_table('tomato_template')

        # Deleting model 'KVMQM'
        db.delete_table('tomato_kvmqm')

        # Deleting model 'KVMQM_Interface'
        db.delete_table('tomato_kvm_interface')

        # Deleting model 'OpenVZ'
        db.delete_table('tomato_openvz')

        # Deleting model 'OpenVZ_Interface'
        db.delete_table('tomato_openvz_interface')

        # Deleting model 'Repy'
        db.delete_table('tomato_repy')

        # Deleting model 'Repy_Interface'
        db.delete_table('tomato_repy_interface')

        # Deleting model 'Network'
        db.delete_table('tomato_network')

        # Deleting model 'External_Network'
        db.delete_table('tomato_external_network')

        # Deleting model 'UDP_Tunnel'
        db.delete_table('tomato_udp_tunnel')

        # Deleting model 'Tinc'
        db.delete_table('tomato_tinc')

        # Deleting model 'Bridge'
        db.delete_table('tomato_bridge')

        # Deleting model 'Fixed_Bridge'
        db.delete_table('tomato_fixed_bridge')


    models = {
        'tomato.bridge': {
            'Meta': {'object_name': 'Bridge', '_ormbases': ['tomato.Connection']},
            'connection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connection']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.connection': {
            'Meta': {'object_name': 'Connection'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'usageStatistics': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'connection'", 'unique': 'True', 'null': 'True', 'to': "orm['tomato.UsageStatistics']"})
        },
        'tomato.element': {
            'Meta': {'object_name': 'Element'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'elements'", 'null': 'True', 'to': "orm['tomato.Connection']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'null': 'True', 'to': "orm['tomato.Element']"}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'usageStatistics': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'element'", 'unique': 'True', 'null': 'True', 'to': "orm['tomato.UsageStatistics']"})
        },
        'tomato.external_network': {
            'Meta': {'object_name': 'External_Network', '_ormbases': ['tomato.Element']},
            'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'}),
            'network': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'instances'", 'null': 'True', 'to': "orm['tomato.Network']"})
        },
        'tomato.fixed_bridge': {
            'Meta': {'object_name': 'Fixed_Bridge', '_ormbases': ['tomato.Connection']},
            'connection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connection']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.kvmqm': {
            'Meta': {'object_name': 'KVMQM', '_ormbases': ['tomato.Element']},
            'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Template']", 'null': 'True'})
        },
        'tomato.kvmqm_interface': {
            'Meta': {'object_name': 'KVMQM_Interface', 'db_table': "'tomato_kvm_interface'", '_ormbases': ['tomato.Element']},
            'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.network': {
            'Meta': {'object_name': 'Network', '_ormbases': ['tomato.Resource']},
            'bridge': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'kind': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'preference': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Resource']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.openvz': {
            'Meta': {'object_name': 'OpenVZ', '_ormbases': ['tomato.Element']},
            'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Resource']", 'null': 'True'})
        },
        'tomato.openvz_interface': {
            'Meta': {'object_name': 'OpenVZ_Interface', '_ormbases': ['tomato.Element']},
            'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.repy': {
            'Meta': {'object_name': 'Repy', '_ormbases': ['tomato.Element']},
            'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Template']", 'null': 'True'})
        },
        'tomato.repy_interface': {
            'Meta': {'object_name': 'Repy_Interface', '_ormbases': ['tomato.Element']},
            'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.resource': {
            'Meta': {'object_name': 'Resource'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'tomato.resourceinstance': {
            'Meta': {'unique_together': "(('num', 'type'),)", 'object_name': 'ResourceInstance'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num': ('django.db.models.fields.IntegerField', [], {}),
            'ownerConnection': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Connection']", 'null': 'True'}),
            'ownerElement': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Element']", 'null': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'tomato.template': {
            'Meta': {'object_name': 'Template', '_ormbases': ['tomato.Resource']},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'preference': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Resource']", 'unique': 'True', 'primary_key': 'True'}),
            'tech': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'tomato.tinc': {
            'Meta': {'object_name': 'Tinc', '_ormbases': ['tomato.Element']},
            'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.udp_tunnel': {
            'Meta': {'object_name': 'UDP_Tunnel', '_ormbases': ['tomato.Element']},
            'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.usagerecord': {
            'Meta': {'object_name': 'UsageRecord'},
            'begin': ('django.db.models.fields.FloatField', [], {}),
            'cputime': ('django.db.models.fields.FloatField', [], {}),
            'diskspace': ('django.db.models.fields.FloatField', [], {}),
            'end': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'measurements': ('django.db.models.fields.IntegerField', [], {}),
            'memory': ('django.db.models.fields.FloatField', [], {}),
            'statistics': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'records'", 'to': "orm['tomato.UsageStatistics']"}),
            'traffic': ('django.db.models.fields.FloatField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'tomato.usagestatistics': {
            'Meta': {'object_name': 'UsageStatistics'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'begin': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['tomato']
