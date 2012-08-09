# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Element'
        db.create_table('tomato_element', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('owner', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='children', null=True, to=orm['tomato.Element'])),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('attrs', self.gf('tomato.lib.db.JSONField')()),
        ))
        db.send_create_signal('tomato', ['Element'])

        # Adding model 'OpenVZ'
        db.create_table('tomato_openvz', (
            ('element_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Element'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['OpenVZ'])

        # Adding model 'KVM'
        db.create_table('tomato_kvm', (
            ('element_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Element'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['KVM'])

        # Adding model 'Resource'
        db.create_table('tomato_resource', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('attrs', self.gf('tomato.lib.db.JSONField')()),
        ))
        db.send_create_signal('tomato', ['Resource'])

        # Adding model 'Template'
        db.create_table('tomato_template', (
            ('resource_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Resource'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('tomato', ['Template'])


    def backwards(self, orm):
        
        # Deleting model 'Element'
        db.delete_table('tomato_element')

        # Deleting model 'OpenVZ'
        db.delete_table('tomato_openvz')

        # Deleting model 'KVM'
        db.delete_table('tomato_kvm')

        # Deleting model 'Resource'
        db.delete_table('tomato_resource')

        # Deleting model 'Template'
        db.delete_table('tomato_template')


    models = {
        'tomato.element': {
            'Meta': {'object_name': 'Element'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'null': 'True', 'to': "orm['tomato.Element']"}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'tomato.kvm': {
            'Meta': {'object_name': 'KVM', '_ormbases': ['tomato.Element']},
            'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.openvz': {
            'Meta': {'object_name': 'OpenVZ', '_ormbases': ['tomato.Element']},
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
            'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Resource']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['tomato']
