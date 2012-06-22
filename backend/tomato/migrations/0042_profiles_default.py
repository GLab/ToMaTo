# encoding: utf-8
import datetime, json
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        orm.DeviceProfile.objects.create(type="openvz", name="S", default=False, restricted=False, attrs=json.dumps({"ram": 128, "disk": 2500}))
        orm.DeviceProfile.objects.create(type="openvz", name="M", default=True, restricted=False, attrs=json.dumps({"ram": 256, "disk": 5000}))
        orm.DeviceProfile.objects.create(type="openvz", name="L", default=False, restricted=False, attrs=json.dumps({"ram": 512, "disk": 10000}))
        orm.DeviceProfile.objects.create(type="openvz", name="XL", default=False, restricted=True, attrs=json.dumps({"ram": 1024, "disk": 25000}))
        orm.DeviceProfile.objects.create(type="kvm", name="S", default=False, restricted=False, attrs=json.dumps({"ram": 128, "cpus": 1, "disk": 2500}))
        orm.DeviceProfile.objects.create(type="kvm", name="M", default=True, restricted=False, attrs=json.dumps({"ram": 256, "cpus": 1, "disk": 5000}))
        orm.DeviceProfile.objects.create(type="kvm", name="L", default=False, restricted=False, attrs=json.dumps({"ram": 512, "cpus": 1, "disk": 10000}))
        orm.DeviceProfile.objects.create(type="kvm", name="XL", default=False, restricted=True, attrs=json.dumps({"ram": 1024, "cpus": 2, "disk": 25000}))
        orm.DeviceProfile.objects.create(type="prog", name="default", default=True, restricted=False, attrs=json.dumps({}))


    def backwards(self, orm):
        "Write your backwards methods here."


    models = {
        'tomato.configuredinterface': {
            'Meta': {'ordering': "['name']", 'object_name': 'ConfiguredInterface', '_ormbases': ['tomato.Interface']},
            'interface_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Interface']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.connection': {
            'Meta': {'unique_together': "(('connector', 'interface'),)", 'object_name': 'Connection'},
            'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
            'connector': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Connector']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interface': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Interface']", 'unique': 'True'})
        },
        'tomato.connector': {
            'Meta': {'ordering': "['name']", 'unique_together': "(('topology', 'name'),)", 'object_name': 'Connector'},
            'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '10'}),
            'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'tomato.device': {
            'Meta': {'ordering': "['name']", 'unique_together': "(('topology', 'name'),)", 'object_name': 'Device'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Host']", 'null': 'True'}),
            'hostgroup': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.DeviceProfile']", 'null': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '10'}),
            'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'tomato.deviceprofile': {
            'Meta': {'ordering': "['type', 'name']", 'unique_together': "(('name', 'type'),)", 'object_name': 'DeviceProfile', 'db_table': "'device_profile'"},
            'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'restricted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '12'})
        },
        'tomato.emulatedconnection': {
            'Meta': {'object_name': 'EmulatedConnection', '_ormbases': ['tomato.Connection']},
            'connection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connection']", 'unique': 'True', 'primary_key': 'True'}),
            'ifb_id': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['tomato.ResourceEntry']"}),
            'live_capture_port': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['tomato.ResourceEntry']"})
        },
        'tomato.error': {
            'Meta': {'ordering': "['-date_last']", 'object_name': 'Error'},
            'date_first': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_last': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'occurrences': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'error'", 'max_length': '20'})
        },
        'tomato.externalnetwork': {
            'Meta': {'ordering': "['type', 'group']", 'unique_together': "(('group', 'type'),)", 'object_name': 'ExternalNetwork'},
            'avoid_duplicates': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'group': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_devices': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'tomato.externalnetworkbridge': {
            'Meta': {'ordering': "['host', 'bridge']", 'unique_together': "(('host', 'bridge'),)", 'object_name': 'ExternalNetworkBridge'},
            'bridge': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Host']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'network': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.ExternalNetwork']"})
        },
        'tomato.externalnetworkconnector': {
            'Meta': {'ordering': "['name']", 'object_name': 'ExternalNetworkConnector', '_ormbases': ['tomato.Connector']},
            'connector_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connector']", 'unique': 'True', 'primary_key': 'True'}),
            'network_group': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'network_type': ('django.db.models.fields.CharField', [], {'default': "'internet'", 'max_length': '20'}),
            'used_network': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.ExternalNetwork']", 'null': 'True'})
        },
        'tomato.host': {
            'Meta': {'ordering': "['group', 'name']", 'object_name': 'Host'},
            'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'group': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        'tomato.interface': {
            'Meta': {'ordering': "['name']", 'unique_together': "(('device', 'name'),)", 'object_name': 'Interface'},
            'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
            'device': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Device']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'tomato.kvmdevice': {
            'Meta': {'ordering': "['name']", 'object_name': 'KVMDevice', '_ormbases': ['tomato.Device']},
            'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Device']", 'unique': 'True', 'primary_key': 'True'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'vmid': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['tomato.ResourceEntry']"}),
            'vnc_port': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['tomato.ResourceEntry']"})
        },
        'tomato.openvzdevice': {
            'Meta': {'ordering': "['name']", 'object_name': 'OpenVZDevice', '_ormbases': ['tomato.Device']},
            'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Device']", 'unique': 'True', 'primary_key': 'True'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'vmid': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['tomato.ResourceEntry']"}),
            'vnc_port': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['tomato.ResourceEntry']"})
        },
        'tomato.permission': {
            'Meta': {'ordering': "['role', 'user']", 'unique_together': "(('topology', 'user'),)", 'object_name': 'Permission'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.User']"})
        },
        'tomato.physicallink': {
            'Meta': {'ordering': "['src_group', 'dst_group']", 'unique_together': "(('src_group', 'dst_group'),)", 'object_name': 'PhysicalLink'},
            'delay_avg': ('django.db.models.fields.FloatField', [], {}),
            'delay_stddev': ('django.db.models.fields.FloatField', [], {}),
            'dst_group': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loss': ('django.db.models.fields.FloatField', [], {}),
            'src_group': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'tomato.progdevice': {
            'Meta': {'ordering': "['name']", 'object_name': 'ProgDevice', '_ormbases': ['tomato.Device']},
            'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Device']", 'unique': 'True', 'primary_key': 'True'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'vnc_port': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['tomato.ResourceEntry']"})
        },
        'tomato.resourceentry': {
            'Meta': {'unique_together': "(('pool', 'num'), ('owner_type', 'owner_id', 'slot'))", 'object_name': 'ResourceEntry'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num': ('django.db.models.fields.IntegerField', [], {}),
            'owner_id': ('django.db.models.fields.IntegerField', [], {}),
            'owner_type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'pool': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.ResourcePool']"}),
            'slot': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'tomato.resourcepool': {
            'Meta': {'unique_together': "(('host', 'type'),)", 'object_name': 'ResourcePool'},
            'first_num': ('django.db.models.fields.IntegerField', [], {}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Host']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_count': ('django.db.models.fields.IntegerField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'tomato.template': {
            'Meta': {'ordering': "['type', 'name']", 'unique_together': "(('name', 'type'),)", 'object_name': 'Template'},
            'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '12'})
        },
        'tomato.tincconnection': {
            'Meta': {'object_name': 'TincConnection', '_ormbases': ['tomato.EmulatedConnection']},
            'bridge_id': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['tomato.ResourceEntry']"}),
            'emulatedconnection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.EmulatedConnection']", 'unique': 'True', 'primary_key': 'True'}),
            'tinc_port': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['tomato.ResourceEntry']"})
        },
        'tomato.tincconnector': {
            'Meta': {'ordering': "['name']", 'object_name': 'TincConnector', '_ormbases': ['tomato.Connector']},
            'connector_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connector']", 'unique': 'True', 'primary_key': 'True'}),
            'external_access_port': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['tomato.ResourceEntry']"}),
            'mode': ('django.db.models.fields.CharField', [], {'default': "'switch'", 'max_length': '10'})
        },
        'tomato.topology': {
            'Meta': {'ordering': "['-id']", 'object_name': 'Topology'},
            'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
            'date_usage': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.User']"}),
            'task': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'})
        },
        'tomato.user': {
            'Meta': {'ordering': "['name', 'origin']", 'unique_together': "(('name', 'origin'),)", 'object_name': 'User'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_user': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'origin': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'password_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        }
    }

    complete_apps = ['tomato']
