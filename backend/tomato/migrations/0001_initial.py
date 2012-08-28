# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'User'
        db.create_table('tomato_user', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('origin', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('attrs', self.gf('tomato.lib.db.JSONField')()),
        ))
        db.send_create_signal('tomato', ['User'])

        # Adding model 'Permissions'
        db.create_table('tomato_permissions', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('tomato', ['Permissions'])

        # Adding model 'PermissionEntry'
        db.create_table('tomato_permissionentry', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('set', self.gf('django.db.models.fields.related.ForeignKey')(related_name='entries', to=orm['tomato.Permissions'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.User'])),
            ('role', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('tomato', ['PermissionEntry'])

        # Adding unique constraint on 'PermissionEntry', fields ['user', 'set']
        db.create_unique('tomato_permissionentry', ['user_id', 'set_id'])

        # Adding model 'Topology'
        db.create_table('tomato_topology', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('permissions', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Permissions'])),
            ('attrs', self.gf('tomato.lib.db.JSONField')()),
        ))
        db.send_create_signal('tomato', ['Topology'])

        # Adding model 'Site'
        db.create_table('tomato_site', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=10)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('tomato', ['Site'])

        # Adding model 'Host'
        db.create_table('tomato_host', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('address', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(related_name='hosts', to=orm['tomato.Site'])),
            ('attrs', self.gf('tomato.lib.db.JSONField')()),
        ))
        db.send_create_signal('tomato', ['Host'])

        # Adding model 'HostElement'
        db.create_table('tomato_hostelement', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('host', self.gf('django.db.models.fields.related.ForeignKey')(related_name='elements', to=orm['tomato.Host'])),
            ('num', self.gf('django.db.models.fields.IntegerField')()),
            ('attrs', self.gf('tomato.lib.db.JSONField')()),
        ))
        db.send_create_signal('tomato', ['HostElement'])

        # Adding unique constraint on 'HostElement', fields ['host', 'num']
        db.create_unique('tomato_hostelement', ['host_id', 'num'])

        # Adding model 'HostConnection'
        db.create_table('tomato_hostconnection', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('host', self.gf('django.db.models.fields.related.ForeignKey')(related_name='connections', to=orm['tomato.Host'])),
            ('num', self.gf('django.db.models.fields.IntegerField')()),
            ('attrs', self.gf('tomato.lib.db.JSONField')()),
        ))
        db.send_create_signal('tomato', ['HostConnection'])

        # Adding unique constraint on 'HostConnection', fields ['host', 'num']
        db.create_unique('tomato_hostconnection', ['host_id', 'num'])

        # Adding model 'UsageStatistics'
        db.create_table('tomato_usagestatistics', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('attrs', self.gf('tomato.lib.db.JSONField')()),
        ))
        db.send_create_signal('tomato', ['UsageStatistics'])

        # Adding model 'UsageRecord'
        db.create_table('tomato_usagerecord', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('statistics', self.gf('django.db.models.fields.related.ForeignKey')(related_name='records', to=orm['tomato.UsageStatistics'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('begin', self.gf('django.db.models.fields.DateTimeField')()),
            ('end', self.gf('django.db.models.fields.DateTimeField')()),
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
            ('topology', self.gf('django.db.models.fields.related.ForeignKey')(related_name='connections', to=orm['tomato.Topology'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('permissions', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Permissions'])),
            ('usageStatistics', self.gf('django.db.models.fields.related.OneToOneField')(related_name='connection', unique=True, null=True, to=orm['tomato.UsageStatistics'])),
            ('attrs', self.gf('tomato.lib.db.JSONField')()),
        ))
        db.send_create_signal('tomato', ['Connection'])

        # Adding model 'Element'
        db.create_table('tomato_element', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('topology', self.gf('django.db.models.fields.related.ForeignKey')(related_name='elements', to=orm['tomato.Topology'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='children', null=True, to=orm['tomato.Element'])),
            ('connection', self.gf('django.db.models.fields.related.ForeignKey')(related_name='elements', null=True, to=orm['tomato.Connection'])),
            ('permissions', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Permissions'])),
            ('usageStatistics', self.gf('django.db.models.fields.related.OneToOneField')(related_name='element', unique=True, null=True, to=orm['tomato.UsageStatistics'])),
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

        # Adding model 'Network'
        db.create_table('tomato_network', (
            ('resource_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tomato.Resource'], unique=True, primary_key=True)),
            ('kind', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('bridge', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('preference', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('tomato', ['Network'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'ResourceInstance', fields ['num', 'type']
        db.delete_unique('tomato_resourceinstance', ['num', 'type'])

        # Removing unique constraint on 'HostConnection', fields ['host', 'num']
        db.delete_unique('tomato_hostconnection', ['host_id', 'num'])

        # Removing unique constraint on 'HostElement', fields ['host', 'num']
        db.delete_unique('tomato_hostelement', ['host_id', 'num'])

        # Removing unique constraint on 'PermissionEntry', fields ['user', 'set']
        db.delete_unique('tomato_permissionentry', ['user_id', 'set_id'])

        # Deleting model 'User'
        db.delete_table('tomato_user')

        # Deleting model 'Permissions'
        db.delete_table('tomato_permissions')

        # Deleting model 'PermissionEntry'
        db.delete_table('tomato_permissionentry')

        # Deleting model 'Topology'
        db.delete_table('tomato_topology')

        # Deleting model 'Site'
        db.delete_table('tomato_site')

        # Deleting model 'Host'
        db.delete_table('tomato_host')

        # Deleting model 'HostElement'
        db.delete_table('tomato_hostelement')

        # Deleting model 'HostConnection'
        db.delete_table('tomato_hostconnection')

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

        # Deleting model 'Network'
        db.delete_table('tomato_network')


    models = {
        'tomato.connection': {
            'Meta': {'object_name': 'Connection'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'permissions': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Permissions']"}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'topology': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'connections'", 'to': "orm['tomato.Topology']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'usageStatistics': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'connection'", 'unique': 'True', 'null': 'True', 'to': "orm['tomato.UsageStatistics']"})
        },
        'tomato.element': {
            'Meta': {'object_name': 'Element'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'elements'", 'null': 'True', 'to': "orm['tomato.Connection']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'null': 'True', 'to': "orm['tomato.Element']"}),
            'permissions': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Permissions']"}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'topology': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'elements'", 'to': "orm['tomato.Topology']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'usageStatistics': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'element'", 'unique': 'True', 'null': 'True', 'to': "orm['tomato.UsageStatistics']"})
        },
        'tomato.host': {
            'Meta': {'object_name': 'Host'},
            'address': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts'", 'to': "orm['tomato.Site']"})
        },
        'tomato.hostconnection': {
            'Meta': {'unique_together': "(('host', 'num'),)", 'object_name': 'HostConnection'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'connections'", 'to': "orm['tomato.Host']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num': ('django.db.models.fields.IntegerField', [], {})
        },
        'tomato.hostelement': {
            'Meta': {'unique_together': "(('host', 'num'),)", 'object_name': 'HostElement'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'elements'", 'to': "orm['tomato.Host']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num': ('django.db.models.fields.IntegerField', [], {})
        },
        'tomato.network': {
            'Meta': {'object_name': 'Network', '_ormbases': ['tomato.Resource']},
            'bridge': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'kind': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'preference': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Resource']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.permissionentry': {
            'Meta': {'unique_together': "(('user', 'set'),)", 'object_name': 'PermissionEntry'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'set': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'entries'", 'to': "orm['tomato.Permissions']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.User']"})
        },
        'tomato.permissions': {
            'Meta': {'object_name': 'Permissions'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
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
        'tomato.site': {
            'Meta': {'object_name': 'Site'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'})
        },
        'tomato.template': {
            'Meta': {'object_name': 'Template', '_ormbases': ['tomato.Resource']},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'preference': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Resource']", 'unique': 'True', 'primary_key': 'True'}),
            'tech': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'tomato.topology': {
            'Meta': {'object_name': 'Topology'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'permissions': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Permissions']"})
        },
        'tomato.usagerecord': {
            'Meta': {'object_name': 'UsageRecord'},
            'begin': ('django.db.models.fields.DateTimeField', [], {}),
            'cputime': ('django.db.models.fields.FloatField', [], {}),
            'diskspace': ('django.db.models.fields.FloatField', [], {}),
            'end': ('django.db.models.fields.DateTimeField', [], {}),
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'tomato.user': {
            'Meta': {'object_name': 'User'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'origin': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['tomato']
