# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Host', fields ['address']
        db.delete_unique(u'tomato_host', ['address'])


        # Changing field 'Organization.totalUsage'
        db.alter_column(u'tomato_organization', 'totalUsage_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.SET_NULL, to=orm['tomato.UsageStatistics']))

        # Changing field 'UDP_Endpoint.element'
        db.alter_column('tomato_udp_endpoint', 'element_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostElement'], null=True, on_delete=models.SET_NULL))

        # Changing field 'Connection.connectionElement2'
        db.alter_column(u'tomato_connection', 'connectionElement2_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.SET_NULL, to=orm['tomato.HostElement']))

        # Changing field 'Connection.connectionElement1'
        db.alter_column(u'tomato_connection', 'connectionElement1_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.SET_NULL, to=orm['tomato.HostElement']))

        # Changing field 'Connection.totalUsage'
        db.alter_column(u'tomato_connection', 'totalUsage_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.SET_NULL, to=orm['tomato.UsageStatistics']))

        # Changing field 'Connection.connection2'
        db.alter_column(u'tomato_connection', 'connection2_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.SET_NULL, to=orm['tomato.HostConnection']))

        # Changing field 'Connection.connection1'
        db.alter_column(u'tomato_connection', 'connection1_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.SET_NULL, to=orm['tomato.HostConnection']))

        # Changing field 'OpenVZ.profile'
        db.alter_column('tomato_openvz', 'profile_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Profile'], null=True, on_delete=models.SET_NULL))

        # Changing field 'OpenVZ.site'
        db.alter_column('tomato_openvz', 'site_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Site'], null=True, on_delete=models.SET_NULL))

        # Changing field 'OpenVZ.element'
        db.alter_column('tomato_openvz', 'element_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostElement'], null=True, on_delete=models.SET_NULL))

        # Changing field 'OpenVZ.template'
        db.alter_column('tomato_openvz', 'template_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Template'], null=True, on_delete=models.SET_NULL))

        # Changing field 'OpenVZ_Interface.element'
        db.alter_column('tomato_openvz_interface', 'element_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostElement'], null=True, on_delete=models.SET_NULL))

        # Changing field 'Host.totalUsage'
        db.alter_column(u'tomato_host', 'totalUsage_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.SET_NULL, to=orm['tomato.UsageStatistics']))

        # Changing field 'User.quota'
        db.alter_column('tomato_user', 'quota_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.PROTECT, to=orm['tomato.Quota']))

        # Changing field 'User.totalUsage'
        db.alter_column('tomato_user', 'totalUsage_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, on_delete=models.PROTECT, to=orm['tomato.UsageStatistics']))

        # Changing field 'HostElement.usageStatistics'
        db.alter_column(u'tomato_hostelement', 'usageStatistics_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.SET_NULL, to=orm['tomato.UsageStatistics']))

        # Changing field 'HostConnection.usageStatistics'
        db.alter_column(u'tomato_hostconnection', 'usageStatistics_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.SET_NULL, to=orm['tomato.UsageStatistics']))

        # Changing field 'External_Network_Endpoint.element'
        db.alter_column('tomato_external_network_endpoint', 'element_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostElement'], null=True, on_delete=models.SET_NULL))

        # Changing field 'Repy_Interface.element'
        db.alter_column('tomato_repy_interface', 'element_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostElement'], null=True, on_delete=models.SET_NULL))

        # Changing field 'Tinc_Endpoint.element'
        db.alter_column('tomato_tinc_endpoint', 'element_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostElement'], null=True, on_delete=models.SET_NULL))

        # Changing field 'Topology.totalUsage'
        db.alter_column(u'tomato_topology', 'totalUsage_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.SET_NULL, to=orm['tomato.UsageStatistics']))

        # Changing field 'KVMQM.profile'
        db.alter_column('tomato_kvmqm', 'profile_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Profile'], null=True, on_delete=models.SET_NULL))

        # Changing field 'KVMQM.site'
        db.alter_column('tomato_kvmqm', 'site_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Site'], null=True, on_delete=models.SET_NULL))

        # Changing field 'KVMQM.element'
        db.alter_column('tomato_kvmqm', 'element_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostElement'], null=True, on_delete=models.SET_NULL))

        # Changing field 'KVMQM.template'
        db.alter_column('tomato_kvmqm', 'template_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Template'], null=True, on_delete=models.SET_NULL))

        # Changing field 'KVMQM_Interface.element'
        db.alter_column('tomato_kvmqm_interface', 'element_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostElement'], null=True, on_delete=models.SET_NULL))

        # Changing field 'Element.totalUsage'
        db.alter_column(u'tomato_element', 'totalUsage_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, on_delete=models.SET_NULL, to=orm['tomato.UsageStatistics']))

        # Changing field 'Element.connection'
        db.alter_column(u'tomato_element', 'connection_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.SET_NULL, to=orm['tomato.Connection']))

        # Changing field 'Repy.profile'
        db.alter_column('tomato_repy', 'profile_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Profile'], null=True, on_delete=models.SET_NULL))

        # Changing field 'Repy.site'
        db.alter_column('tomato_repy', 'site_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Site'], null=True, on_delete=models.SET_NULL))

        # Changing field 'Repy.element'
        db.alter_column('tomato_repy', 'element_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostElement'], null=True, on_delete=models.SET_NULL))

        # Changing field 'Repy.template'
        db.alter_column('tomato_repy', 'template_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Template'], null=True, on_delete=models.SET_NULL))

        # Changing field 'Quota.monthly'
        db.alter_column(u'tomato_quota', 'monthly_id', self.gf('django.db.models.fields.related.ForeignKey')(on_delete=models.PROTECT, to=orm['tomato.Usage']))

        # Changing field 'Quota.used'
        db.alter_column(u'tomato_quota', 'used_id', self.gf('django.db.models.fields.related.ForeignKey')(on_delete=models.PROTECT, to=orm['tomato.Usage']))

        # Changing field 'UsageRecord.usage'
        db.alter_column(u'tomato_usagerecord', 'usage_id', self.gf('django.db.models.fields.related.ForeignKey')(on_delete=models.PROTECT, to=orm['tomato.Usage']))

    def backwards(self, orm):

        # Changing field 'Organization.totalUsage'
        db.alter_column(u'tomato_organization', 'totalUsage_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, to=orm['tomato.UsageStatistics']))

        # Changing field 'UDP_Endpoint.element'
        db.alter_column('tomato_udp_endpoint', 'element_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostElement'], null=True))

        # Changing field 'Connection.connectionElement2'
        db.alter_column(u'tomato_connection', 'connectionElement2_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['tomato.HostElement']))

        # Changing field 'Connection.connectionElement1'
        db.alter_column(u'tomato_connection', 'connectionElement1_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['tomato.HostElement']))

        # Changing field 'Connection.totalUsage'
        db.alter_column(u'tomato_connection', 'totalUsage_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, to=orm['tomato.UsageStatistics']))

        # Changing field 'Connection.connection2'
        db.alter_column(u'tomato_connection', 'connection2_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['tomato.HostConnection']))

        # Changing field 'Connection.connection1'
        db.alter_column(u'tomato_connection', 'connection1_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['tomato.HostConnection']))

        # Changing field 'OpenVZ.profile'
        db.alter_column('tomato_openvz', 'profile_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Profile'], null=True))

        # Changing field 'OpenVZ.site'
        db.alter_column('tomato_openvz', 'site_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Site'], null=True))

        # Changing field 'OpenVZ.element'
        db.alter_column('tomato_openvz', 'element_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostElement'], null=True))

        # Changing field 'OpenVZ.template'
        db.alter_column('tomato_openvz', 'template_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Template'], null=True))

        # Changing field 'OpenVZ_Interface.element'
        db.alter_column('tomato_openvz_interface', 'element_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostElement'], null=True))

        # Changing field 'Host.totalUsage'
        db.alter_column(u'tomato_host', 'totalUsage_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, to=orm['tomato.UsageStatistics']))
        # Adding unique constraint on 'Host', fields ['address']
        db.create_unique(u'tomato_host', ['address'])


        # Changing field 'User.quota'
        db.alter_column('tomato_user', 'quota_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, to=orm['tomato.Quota']))

        # Changing field 'User.totalUsage'
        db.alter_column('tomato_user', 'totalUsage_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, to=orm['tomato.UsageStatistics']))

        # Changing field 'HostElement.usageStatistics'
        db.alter_column(u'tomato_hostelement', 'usageStatistics_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, to=orm['tomato.UsageStatistics']))

        # Changing field 'HostConnection.usageStatistics'
        db.alter_column(u'tomato_hostconnection', 'usageStatistics_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, to=orm['tomato.UsageStatistics']))

        # Changing field 'External_Network_Endpoint.element'
        db.alter_column('tomato_external_network_endpoint', 'element_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostElement'], null=True))

        # Changing field 'Repy_Interface.element'
        db.alter_column('tomato_repy_interface', 'element_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostElement'], null=True))

        # Changing field 'Tinc_Endpoint.element'
        db.alter_column('tomato_tinc_endpoint', 'element_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostElement'], null=True))

        # Changing field 'Topology.totalUsage'
        db.alter_column(u'tomato_topology', 'totalUsage_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, to=orm['tomato.UsageStatistics']))

        # Changing field 'KVMQM.profile'
        db.alter_column('tomato_kvmqm', 'profile_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Profile'], null=True))

        # Changing field 'KVMQM.site'
        db.alter_column('tomato_kvmqm', 'site_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Site'], null=True))

        # Changing field 'KVMQM.element'
        db.alter_column('tomato_kvmqm', 'element_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostElement'], null=True))

        # Changing field 'KVMQM.template'
        db.alter_column('tomato_kvmqm', 'template_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Template'], null=True))

        # Changing field 'KVMQM_Interface.element'
        db.alter_column('tomato_kvmqm_interface', 'element_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostElement'], null=True))

        # Changing field 'Element.totalUsage'
        db.alter_column(u'tomato_element', 'totalUsage_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, to=orm['tomato.UsageStatistics']))

        # Changing field 'Element.connection'
        db.alter_column(u'tomato_element', 'connection_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['tomato.Connection']))

        # Changing field 'Repy.profile'
        db.alter_column('tomato_repy', 'profile_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Profile'], null=True))

        # Changing field 'Repy.site'
        db.alter_column('tomato_repy', 'site_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Site'], null=True))

        # Changing field 'Repy.element'
        db.alter_column('tomato_repy', 'element_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostElement'], null=True))

        # Changing field 'Repy.template'
        db.alter_column('tomato_repy', 'template_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Template'], null=True))

        # Changing field 'Quota.monthly'
        db.alter_column(u'tomato_quota', 'monthly_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Usage']))

        # Changing field 'Quota.used'
        db.alter_column(u'tomato_quota', 'used_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Usage']))

        # Changing field 'UsageRecord.usage'
        db.alter_column(u'tomato_usagerecord', 'usage_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.Usage']))

    models = {
        u'tomato.connection': {
            'Meta': {'object_name': 'Connection'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'connection1': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['tomato.HostConnection']"}),
            'connection2': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['tomato.HostConnection']"}),
            'connectionElement1': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['tomato.HostElement']"}),
            'connectionElement2': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['tomato.HostElement']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'permissions': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Permissions']"}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'topology': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'connections'", 'to': u"orm['tomato.Topology']"}),
            'totalUsage': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['tomato.UsageStatistics']"})
        },
        u'tomato.element': {
            'Meta': {'object_name': 'Element'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'elements'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['tomato.Connection']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'null': 'True', 'to': u"orm['tomato.Element']"}),
            'permissions': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Permissions']"}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'topology': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'elements'", 'to': u"orm['tomato.Topology']"}),
            'totalUsage': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['tomato.UsageStatistics']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'tomato.external_network': {
            'Meta': {'object_name': 'External_Network', '_ormbases': [u'tomato.Element']},
            u'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'}),
            'network': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Network']", 'null': 'True'})
        },
        'tomato.external_network_endpoint': {
            'Meta': {'object_name': 'External_Network_Endpoint', '_ormbases': [u'tomato.Element']},
            'element': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tomato.HostElement']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            u'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'}),
            'network': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.NetworkInstance']", 'null': 'True'})
        },
        u'tomato.host': {
            'Meta': {'ordering': "['site', 'name']", 'object_name': 'Host'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts'", 'to': u"orm['tomato.Site']"}),
            'totalUsage': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['tomato.UsageStatistics']"})
        },
        u'tomato.hostconnection': {
            'Meta': {'unique_together': "(('host', 'num'),)", 'object_name': 'HostConnection'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'connections'", 'to': u"orm['tomato.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num': ('django.db.models.fields.IntegerField', [], {}),
            'topology_connection': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'host_connections'", 'null': 'True', 'to': u"orm['tomato.Connection']"}),
            'topology_element': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'host_connections'", 'null': 'True', 'to': u"orm['tomato.Element']"}),
            'usageStatistics': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['tomato.UsageStatistics']"})
        },
        u'tomato.hostelement': {
            'Meta': {'unique_together': "(('host', 'num'),)", 'object_name': 'HostElement'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'elements'", 'to': u"orm['tomato.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num': ('django.db.models.fields.IntegerField', [], {}),
            'topology_connection': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'host_elements'", 'null': 'True', 'to': u"orm['tomato.Connection']"}),
            'topology_element': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'host_elements'", 'null': 'True', 'to': u"orm['tomato.Element']"}),
            'usageStatistics': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['tomato.UsageStatistics']"})
        },
        'tomato.kvmqm': {
            'Meta': {'object_name': 'KVMQM'},
            'element': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tomato.HostElement']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            u'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'}),
            'next_sync': ('django.db.models.fields.FloatField', [], {'default': '0', 'db_index': 'True'}),
            'profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Profile']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'rextfv_last_started': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tomato.Site']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Template']", 'null': 'True', 'on_delete': 'models.SET_NULL'})
        },
        'tomato.kvmqm_interface': {
            'Meta': {'object_name': 'KVMQM_Interface'},
            'element': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tomato.HostElement']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            u'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'tomato.linkmeasurement': {
            'Meta': {'unique_together': "(('siteA', 'siteB', 'type', 'end'),)", 'object_name': 'LinkMeasurement'},
            'begin': ('django.db.models.fields.FloatField', [], {}),
            'delayAvg': ('django.db.models.fields.FloatField', [], {}),
            'delayStddev': ('django.db.models.fields.FloatField', [], {}),
            'end': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loss': ('django.db.models.fields.FloatField', [], {}),
            'measurements': ('django.db.models.fields.IntegerField', [], {}),
            'siteA': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['tomato.Site']"}),
            'siteB': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['tomato.Site']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'db_index': 'True'})
        },
        'tomato.network': {
            'Meta': {'object_name': 'Network', '_ormbases': [u'tomato.Resource']},
            'kind': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'preference': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Resource']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.networkinstance': {
            'Meta': {'unique_together': "(('host', 'bridge'),)", 'object_name': 'NetworkInstance', 'db_table': "'tomato_network_instance'", '_ormbases': [u'tomato.Resource']},
            'bridge': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'networks'", 'to': u"orm['tomato.Host']"}),
            'network': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'instances'", 'to': "orm['tomato.Network']"}),
            u'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Resource']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.openvz': {
            'Meta': {'object_name': 'OpenVZ'},
            'element': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tomato.HostElement']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            u'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'}),
            'next_sync': ('django.db.models.fields.FloatField', [], {'default': '0', 'db_index': 'True'}),
            'profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Profile']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'rextfv_last_started': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tomato.Site']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Template']", 'null': 'True', 'on_delete': 'models.SET_NULL'})
        },
        'tomato.openvz_interface': {
            'Meta': {'object_name': 'OpenVZ_Interface'},
            'element': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tomato.HostElement']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            u'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'tomato.organization': {
            'Meta': {'object_name': 'Organization'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'totalUsage': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['tomato.UsageStatistics']"})
        },
        'tomato.permissionentry': {
            'Meta': {'unique_together': "(('user', 'set'),)", 'object_name': 'PermissionEntry'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'set': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'entries'", 'to': "orm['tomato.Permissions']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.User']"})
        },
        'tomato.permissions': {
            'Meta': {'object_name': 'Permissions'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'tomato.profile': {
            'Meta': {'object_name': 'Profile', '_ormbases': [u'tomato.Resource']},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'preference': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Resource']", 'unique': 'True', 'primary_key': 'True'}),
            'tech': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'tomato.quota': {
            'Meta': {'object_name': 'Quota'},
            'continous_factor': ('django.db.models.fields.FloatField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'monthly': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'on_delete': 'models.PROTECT', 'to': u"orm['tomato.Usage']"}),
            'used': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'on_delete': 'models.PROTECT', 'to': u"orm['tomato.Usage']"}),
            'used_time': ('django.db.models.fields.FloatField', [], {})
        },
        'tomato.repy': {
            'Meta': {'object_name': 'Repy'},
            'element': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tomato.HostElement']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            u'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'}),
            'next_sync': ('django.db.models.fields.FloatField', [], {'default': '0', 'db_index': 'True'}),
            'profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Profile']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'rextfv_last_started': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tomato.Site']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Template']", 'null': 'True', 'on_delete': 'models.SET_NULL'})
        },
        'tomato.repy_interface': {
            'Meta': {'object_name': 'Repy_Interface'},
            'element': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tomato.HostElement']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            u'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'tomato.resource': {
            'Meta': {'object_name': 'Resource'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'tomato.site': {
            'Meta': {'object_name': 'Site'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sites'", 'to': u"orm['tomato.Organization']"})
        },
        'tomato.template': {
            'Meta': {'object_name': 'Template', '_ormbases': [u'tomato.Resource']},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'preference': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Resource']", 'unique': 'True', 'primary_key': 'True'}),
            'tech': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'tomato.templateonhost': {
            'Meta': {'unique_together': "[('host', 'template')]", 'object_name': 'TemplateOnHost'},
            'date': ('django.db.models.fields.FloatField', [], {}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'templates'", 'to': u"orm['tomato.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ready': ('django.db.models.fields.BooleanField', [], {}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts'", 'to': "orm['tomato.Template']"})
        },
        'tomato.tinc_endpoint': {
            'Meta': {'object_name': 'Tinc_Endpoint', '_ormbases': [u'tomato.Element']},
            'element': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tomato.HostElement']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            u'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.tinc_vpn': {
            'Meta': {'object_name': 'Tinc_VPN', '_ormbases': [u'tomato.Element']},
            u'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'tomato.topology': {
            'Meta': {'ordering': "['-id']", 'object_name': 'Topology'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'permissions': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Permissions']"}),
            'timeout': ('django.db.models.fields.FloatField', [], {}),
            'timeout_step': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'totalUsage': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['tomato.UsageStatistics']"})
        },
        'tomato.udp_endpoint': {
            'Meta': {'object_name': 'UDP_Endpoint', '_ormbases': [u'tomato.Element']},
            'element': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tomato.HostElement']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            u'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'tomato.usage': {
            'Meta': {'object_name': 'Usage'},
            'cputime': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'diskspace': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'memory': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'traffic': ('django.db.models.fields.FloatField', [], {'default': '0.0'})
        },
        u'tomato.usagerecord': {
            'Meta': {'unique_together': "(('statistics', 'type', 'end'),)", 'object_name': 'UsageRecord'},
            'begin': ('django.db.models.fields.FloatField', [], {}),
            'end': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'measurements': ('django.db.models.fields.IntegerField', [], {}),
            'statistics': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'records'", 'to': u"orm['tomato.UsageStatistics']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'db_index': 'True'}),
            'usage': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'on_delete': 'models.PROTECT', 'to': u"orm['tomato.Usage']"})
        },
        u'tomato.usagestatistics': {
            'Meta': {'object_name': 'UsageStatistics'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'tomato.user': {
            'Meta': {'ordering': "['name', 'origin']", 'unique_together': "(('name', 'origin'),)", 'object_name': 'User'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_login': ('django.db.models.fields.FloatField', [], {'default': '1406190789.363121'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'users'", 'to': u"orm['tomato.Organization']"}),
            'origin': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'password_time': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'quota': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'null': 'True', 'on_delete': 'models.PROTECT', 'to': u"orm['tomato.Quota']"}),
            'totalUsage': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'on_delete': 'models.PROTECT', 'to': u"orm['tomato.UsageStatistics']"})
        }
    }

    complete_apps = ['tomato']