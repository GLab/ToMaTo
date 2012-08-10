# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Connection'
        db.create_table('tomato_connection', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('owner', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=20)),
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

        # Adding model 'KVM'
        db.create_table('tomato_kvm', (
            ('element_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Element'], unique=True, primary_key=True)),
            ('template', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Resource'], null=True)),
        ))
        db.send_create_signal('tomato', ['KVM'])

        # Adding model 'KVM_Interface'
        db.create_table('tomato_kvm_interface', (
            ('element_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Element'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['KVM_Interface'])

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

        # Adding model 'LXC'
        db.create_table('tomato_lxc', (
            ('element_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Element'], unique=True, primary_key=True)),
            ('template', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Resource'], null=True)),
        ))
        db.send_create_signal('tomato', ['LXC'])

        # Adding model 'LXC_Interface'
        db.create_table('tomato_lxc_interface', (
            ('element_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Element'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['LXC_Interface'])

        # Adding model 'Bridge'
        db.create_table('tomato_bridge', (
            ('connection_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Connection'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['Bridge'])

        # Adding model 'Template'
        db.create_table('tomato_template', (
            ('resource_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Resource'], unique=True, primary_key=True)),
            ('tech', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('tomato', ['Template'])


    def backwards(self, orm):
        
        # Deleting model 'Connection'
        db.delete_table('tomato_connection')

        # Deleting model 'Element'
        db.delete_table('tomato_element')

        # Deleting model 'Resource'
        db.delete_table('tomato_resource')

        # Deleting model 'KVM'
        db.delete_table('tomato_kvm')

        # Deleting model 'KVM_Interface'
        db.delete_table('tomato_kvm_interface')

        # Deleting model 'OpenVZ'
        db.delete_table('tomato_openvz')

        # Deleting model 'OpenVZ_Interface'
        db.delete_table('tomato_openvz_interface')

        # Deleting model 'LXC'
        db.delete_table('tomato_lxc')

        # Deleting model 'LXC_Interface'
        db.delete_table('tomato_lxc_interface')

        # Deleting model 'Bridge'
        db.delete_table('tomato_bridge')

        # Deleting model 'Template'
        db.delete_table('tomato_template')


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
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'tomato.element': {
            'Meta': {'object_name': 'Element'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'elements'", 'null': 'True', 'to': "orm['tomato.Connection']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'null': 'True', 'to': "orm['tomato.Element']"}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'tomato.kvm': {
            'Meta': {'object_name': 'KVM', '_ormbases': ['tomato.Element']},
            'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Resource']", 'null': 'True'})
        },
        'tomato.kvm_interface': {
            'Meta': {'object_name': 'KVM_Interface', '_ormbases': ['tomato.Element']},
            'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.lxc': {
            'Meta': {'object_name': 'LXC', '_ormbases': ['tomato.Element']},
            'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Resource']", 'null': 'True'})
        },
        'tomato.lxc_interface': {
            'Meta': {'object_name': 'LXC_Interface', '_ormbases': ['tomato.Element']},
            'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
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
        'tomato.resource': {
            'Meta': {'object_name': 'Resource'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'tomato.template': {
            'Meta': {'object_name': 'Template', '_ormbases': ['tomato.Resource']},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Resource']", 'unique': 'True', 'primary_key': 'True'}),
            'tech': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        }
    }

    complete_apps = ['tomato']
