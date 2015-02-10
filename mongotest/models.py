from mongoengine import *
import bson

class ExtDocument(object):
	def getFieldId(self, field):
		dat = self._data.get(field)
		if isinstance(dat, bson.DBRef):
			return dat._DBRef__id
		return dat.id

class BaseDocument(ExtDocument, Document):
	meta = {'abstract': True}

	def __setattr__(self, key, value):
		if key.startswith('_') or key in ['id'] or hasattr(self, key) or (key.startswith('get_') and key.endswith('_display')):
			Document.__setattr__(self, key, value)
		else:
			print "Warning: value set on untracked field: %s.%s = %r" % (self.__class__.__name__, key, value)

class Usage(EmbeddedDocument):
	memory = FloatField(default=0.0) #unit: bytes
	diskspace = FloatField(default=0.0) #unit: bytes
	traffic = FloatField(default=0.0) #unit: bytes
	cputime = FloatField(default=0.0) #unit: cpu seconds

class UsageRecord(EmbeddedDocument):
	begin = FloatField(required=True)
	end = FloatField(required=True)
	measurements = IntField(default=0)
	usage = EmbeddedDocumentField(Usage, required=True)
	meta = {
		'collection': 'usage_record',
		'ordering': ['type', 'end'],
		'indexes': [
			('type', 'end')
		]
	}

class UsageStatistics(BaseDocument):
	by5minutes = ListField(EmbeddedDocumentField(UsageRecord), db_field='5minutes')
	byHour = ListField(EmbeddedDocumentField(UsageRecord), db_field='hour')
	byDay = ListField(EmbeddedDocumentField(UsageRecord), db_field='day')
	byMonth = ListField(EmbeddedDocumentField(UsageRecord), db_field='month')
	byYear = ListField(EmbeddedDocumentField(UsageRecord), db_field='year')
	meta = {
		'collection': 'usage_statistics',
	}

class Quota(EmbeddedDocument):
	monthly = EmbeddedDocumentField(Usage, required=True)
	used = EmbeddedDocumentField(Usage, required=True)
	usedTime = FloatField(db_field='used_time', required=True)
	continousFactor = FloatField(db_field='continous_factor')

class Organization(BaseDocument):
	name = StringField(unique=True, required=True)
	totalUsage = ReferenceField(UsageStatistics, db_field='total_usage', required=True)
	label = StringField(required=True)
	homepageUrl = URLField(db_field='homepage_url')
	imageUrl = URLField(db_field='image_url')
	description = StringField()
	meta = {
		'ordering': ['name'],
		'indexes': [
			'name'
		]
	}
	@property
	def sites(self):
		return Site.objects(organization=self)
	@property
	def users(self):
		return User.objects(organization=self)

class Site(BaseDocument):
	name = StringField(unique=True, required=True)
	organization = ReferenceField(Organization, required=True)
	#hosts = ListField(ReferenceField('Host'))
	label = StringField(required=True)
	location = StringField()
	geolocation = GeoPointField()
	description = StringField()
	meta = {
		'ordering': ['organization', 'name'],
		'indexes': [
			'organization', 'name'
		]
	}
	@property
	def hosts(self):
		return Host.objects(site=self)

class User(BaseDocument):
	name = StringField(required=True, unique_with='origin')
	origin = StringField(required=True)
	organization = ReferenceField(Organization, required=True)
	password = StringField(required=True)
	passwordTime = FloatField(db_field='password_time', required=True)
	lastLogin = FloatField(db_field='last_login', required=True)
	totalUsage = ReferenceField(UsageStatistics, db_field='total_usage', required=True)
	quota = EmbeddedDocumentField(Quota, required=True)
	realname = StringField()
	email = EmailField()
	flags = ListField(StringField())
	meta = {
		'ordering': ['name'],
		'indexes': [
			'lastLogin', 'passwordTime', 'flags', 'organization', ('name', 'origin')
		]
	}
	@property
	def topologies(self):
		return Topology.objects(permissions__user=self)

class Permission(EmbeddedDocument):
	user = ReferenceField(User, required=True)
	role = StringField(choices=['owner', 'manager', 'user'], required=True)

class ErrorDump(EmbeddedDocument):
	source = StringField(required=True)
	dumpId = StringField(db_field='dump_id', required=True, unique=True)
	description = DictField(required=True)
	data = StringField()
	dataAvailable = BooleanField(default=False, db_field='data_available')
	type = StringField(required=True)
	softwareVersion = DictField(db_field='software_version')
	timestamp = FloatField(required=True)
	meta = {
		'ordering': ['+timestamp'],
		'indexes': [
			'dumpId'
		]
	}

class ErrorGroup(BaseDocument):
	groupId = StringField(db_field='group_id', required=True, unique=True)
	description = StringField(required=True)
	removedDumps = IntField(default=0, db_field='removed_dumps')
	dumps = ListField(EmbeddedDocumentField(ErrorDump))
	meta = {
		'collection': 'error_group',
		'ordering': ['groupId'],
		'indexes': [
			'groupId'
		]
	}

class Network(BaseDocument):
	kind = StringField(required=True)
	preference = IntField(default=0, required=True)
	restricted = BooleanField(default=False)
	meta = {
		'ordering': ['+preference', 'kind'],
		'indexes': [
			('kind', 'preference')
		]
	}
	@property
	def instances(self):
		return NetworkInstance.objects(network=self)

class Profile(BaseDocument):
	tech = StringField(required=True)
	name = StringField(required=True, unique_with='tech')
	preference = IntField(default=0, required=True)
	label = StringField()
	restricted = BooleanField(default=False)
	meta = {
		'ordering': ['tech', '+preference', 'name'],
		'indexes': [
			('tech', 'preference'), ('tech', 'name')
		]
	}

class Template(BaseDocument):
	tech = StringField(required=True)
	name = StringField(required=True, unique_with='tech')
	preference = IntField(default=0)
	label = StringField()
	restricted = BooleanField(default=False)
	subtype = StringField()
	torrentData = BinaryField(db_field='torrent_data')
	kblang = StringField(default='en-us')
	meta = {
		'ordering': ['tech', '+preference', 'name'],
		'indexes': [
			('tech', 'preference'), ('tech', 'name')
		]
	}
	@property
	def hosts(self):
		return Host.objects(templates__in=self)

class Host(BaseDocument):
	name = StringField(required=True, unique=True)
	address = StringField(required=True)
	rpcurl = StringField(required=True, unique=True)
	site = ReferenceField(Site, required=True)
	totalUsage = ReferenceField(UsageStatistics, db_field='total_usage', required=True)
	elementTypes = DictField(db_field='element_types', required=True)
	connectionTypes = DictField(db_field='connection_types', required=True)
	hostInfo = DictField(db_field='host_info', required=True)
	hostInfoTimestamp = FloatField(db_field='host_info_timestamp', required=True)
	accountingTimestamp = FloatField(db_field='accounting_timestamp', required=True)
	lastResourcesSync = FloatField(db_field='last_resource_sync', required=True)
	enabled = BooleanField(default=True)
	componentErrors = IntField(default=0, db_field='component_errors')
	problemAge = FloatField(db_field='problem_age')
	problemMailTime = FloatField(db_field='problem_mail_time')
	availability = FloatField(default=1.0)
	description = StringField()
	dumpLastFetch = FloatField(db_field='dump_last_fetch')
	templates = ListField(ReferenceField(Template))
	meta = {
		'ordering': ['site', 'name'],
		'indexes': [
			'name', 'site'
		]
	}
	@property
	def elements(self):
		return HostElement.objects(host=self)
	@property
	def connections(self):
		return HostConnection.objects(host=self)

STATE_OPTIONS=['default', 'created', 'prepared', 'started']

class HostObject(BaseDocument):
	host = ReferenceField(Host, required=True)
	num = IntField(unique_with='host', required=True)
	topologyElement = ReferenceField('Element', db_field='topology_element')
	topologyConnection = ReferenceField('Connection', db_field='topology_connection')
	usageStatistics = ReferenceField(UsageStatistics, db_field='usage_statistics', required=True)
	state = StringField(choices=STATE_OPTIONS, required=True)
	type = StringField(required=True)
	meta = {
		"abstract": True
	}

class HostElement(HostObject):
	connection = ReferenceField('HostConnection')
	parent = ReferenceField('self')
	meta = {
		'collection': 'host_element',
		'indexes': [
			('host', 'num')
		]
	}

class HostConnection(HostObject):
	elementFrom = ReferenceField(HostElement, db_field='element_from', required=True)
	elementTo = ReferenceField(HostElement, db_field='element_to', required=True)
	meta = {
		'collection': 'host_connection',
		'indexes': [
			('host', 'num')
		]
	}

class LinkMeasurement(BaseDocument):
	siteA = ReferenceField(Site, db_field='site_a', required=True)
	siteB = ReferenceField(Site, db_field='site_b', required=True)
	type = StringField(choices=["single", "5minutes", "hour", "day", "month", "year"], required=True)
	begin = FloatField(required=True)
	end = FloatField(required=True)
	measurements = IntField(required=True)
	loss = FloatField(required=True)
	delayAvg = FloatField(db_field='delay_avg', required=True)
	delayStddev = FloatField(db_field='delay_stddev', required=True)
	meta = {
		'collection': 'link_measurement',
		'ordering': ['siteA', 'siteB', 'type', 'end'],
		'indexes': [
			('siteA', 'siteB'), ('siteA', 'siteB', 'type', 'end')
		]
	}

class NetworkInstance(BaseDocument):
	network = ReferenceField(Network, required=True)
	host = ReferenceField(Host, required=True)
	bridge = StringField(required=True)
	meta = {
		'collection': 'network_instance',
		'ordering': ['network', 'host', 'bridge'],
		'indexes': [
			'network', 'host'
		]
	}

class Topology(BaseDocument):
	permissions = ListField(EmbeddedDocumentField(Permission))
	totalUsage = ReferenceField(UsageStatistics, db_field='total_usage', required=True)
	timeout = FloatField(required=True)
	timeoutStep = IntField(db_field='timeout_step', required=True)
	site = ReferenceField(Site)
	name = StringField()
	clientData = DictField(db_field='client_data')
	meta = {
		'ordering': ['name'],
		'indexes': [
			'name', ('timeout', 'timeoutStep')
		]
	}
	@property
	def elements(self):
		return Element.objects(topology=self)
	@property
	def connections(self):
		return Connection.objects(topology=self)

class Element(ExtDocument, DynamicDocument):
	topology = ReferenceField(Topology, required=True)
	state = StringField(choices=STATE_OPTIONS, required=True)
	parent = GenericReferenceField()
	connection = ReferenceField('Connection')
	permissions = ListField(EmbeddedDocumentField(Permission))
	totalUsage = ReferenceField(UsageStatistics, db_field='total_usage', required=True)
	hostElements = ListField(ReferenceField('HostElement'), db_field='host_elements')
	hostConnections = ListField(ReferenceField('HostConnection'), db_field='host_connections')
	clientData = DictField(db_field='client_data')
	meta = {
		'allow_inheritance': True,
		'indexes': [
			'topology', 'state', 'parent'
		]
	}
	@property
	def children(self):
		return Element.objects(parent=self)

class VMElement(Element):
	element = ReferenceField('HostElement')
	site = ReferenceField('Site')
	name = StringField()
	profile = ReferenceField('Profile')
	template = ReferenceField('Template')
	rextfvLastStarted = FloatField(default=0, db_field='rextfv_last_started')
	nextSync = FloatField(default=0, db_field='next_sync')
	lastSync = FloatField(default=0, db_field='last_sync')
	customTemplate = BooleanField(default=False, db_field='custom_template')

class VMInterface(Element):
	element = ReferenceField('HostElement')
	name = StringField(regex="^eth[0-9]+$")

class ExternalNetwork(Element):
	name = StringField()
	samenet = BooleanField(default=False)
	kind = StringField(default='internet')
	network = ReferenceField('Network')

class ExternalNetworkEndpoint(Element):
	element = ReferenceField('HostElement')
	name = StringField()
	kind = StringField(default='internet')
	network = ReferenceField('NetworkInstance')

class KVMQM(VMElement):
	pass

class KVMQM_Interface(VMInterface):
	pass

class OpenVZ(VMElement):
	rootpassword = StringField()
	hostname = StringField()

class OpenVZ_Interface(VMInterface):
	ip4address = StringField()
	ip6address = StringField()
	useDhcp = BooleanField(db_field='use_dhcp')

class Repy(VMElement):
	pass

class Repy_Interface(VMInterface):
	pass

class TincVPN(Element):
	name = StringField()
	mode = StringField(choices=['switch', 'hub'])

class TincEndpoint(Element):
	element = ReferenceField('HostElement')
	name = StringField()
	mode = StringField(choices=['switch', 'hub'])
	peers = ListField(DictField())

class UDPEndpoint(Element):
	element = ReferenceField('HostElement')
	name = StringField()
	connect = StringField()

class Connection(ExtDocument, DynamicDocument):
	topology = ReferenceField(Topology, required=True)
	state = StringField(choices=STATE_OPTIONS, required=True)
	permissions = ListField(EmbeddedDocumentField(Permission))
	totalUsage = ReferenceField(UsageStatistics, db_field='total_usage', required=True)
	elementFrom = ReferenceField('Element', db_field='element_from', required=True)
	elementTo = ReferenceField('Element', db_field='element_to', required=True)
	connectionFrom = ReferenceField('HostConnection', db_field='connection_from')
	connectionTo = ReferenceField('HostConnection', db_field='connection_to')
	connectionElementFrom = ReferenceField('HostElement', db_field='connection_element_from')
	connectionElementTo = ReferenceField('HostElement', db_field='connection_element_to')
	clientData = DictField(db_field='client_data')
	meta = {
		'allow_inheritance': True,
		'indexes': [
			'topology', 'state', 'elementFrom', 'elementTo'
		]
	}
