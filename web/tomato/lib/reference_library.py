__author__ = 't-gerhard'

from django.core.urlresolvers import reverse

def tech_to_label(tech):
	if tech == "kvmqm":
		return "KVM"
	if tech == "openvz":
		return "OpenVZ"
	if tech == "repy":
		return "Repy"
	return tech

def techs():
	return ['kvmqm', 'openvz', 'repy']

def entity_to_label(entity):
	if entity == 'topology':
		return "Topology"
	if entity == 'host':
		return "Host"
	if entity == 'site':
		return "Site"
	if entity == 'organization':
		return "Organization"
	if entity == 'account':
		return "User Account"
	if entity == 'template':
		return "Template"
	if entity == 'profile':
		return "Device Profile"


def reference_config():
	return {
		'topology': ('id'),
		'host': ('name'),
		'site': ('name'),
		'organization': ('name'),
		'account': ('name'),
		'template': ('id'),
		'profile': ('id')
	}

def resolve_reference(api, ref):
	obj_type, obj_id = (ref[0], ref[1])

	if obj_type == "topology":
		ref_link = reverse("tomato.topology.info", kwargs={"id": obj_id})
		try:
			topology_info = api.topology_info(obj_id)
			return ref_link, "View Topology '%s'" % topology_info["name"]
		except:
			return ref_link, "View Topology [%s]" % obj_id

	if obj_type == "host":
		ref_link = reverse("tomato.admin.host.info", kwargs={"name": obj_id})
		return ref_link, "View Host '%s'" % obj_id

	if obj_type == "site":
		ref_link = reverse("tomato.admin.site.info", kwargs={"name": obj_id})
		try:
			site_info = api.site_info(obj_id)
			return ref_link, "View Site '%s'" % site_info['label']
		except:
			return ref_link, "View Site '%s'" % obj_id

	if obj_type == "organization":
		ref_link = reverse("tomato.admin.organization.info", kwargs={"name": obj_id})
		try:
			organization_info = api.organization_info(obj_id)
			return ref_link, "View Organization '%s'" % organization_info['label']
		except:
			return ref_link, "View Organization '%s'" % obj_id

	if obj_type == "account":
		ref_link = reverse("tomato.account.info", kwargs={"id": obj_id})
		try:
			account_info = api.account_info(obj_id)
			return ref_link, "View User Account '%s'" % account_info['realname']
		except:
			return ref_link, "View User Account '%s'" % obj_id

	if obj_type == "profile":
		ref_link = reverse("tomato.profile.info", kwargs={"res_id": obj_id})
		try:
			profile_info = api.profile_info(obj_id)
			return ref_link, "View %s Device Profile '%s'" % (tech_to_label(profile_info['tech']), profile_info['label'])
		except:
			return ref_link, "View Device Profile '%s'" % obj_id

	if obj_type == "template":
		ref_link = reverse("tomato.template.info", kwargs={"res_id": obj_id})
		try:
			template_info = api.template_info(obj_id)
			return ref_link, "View %s Template '%s'" % (tech_to_label(template_info['tech']), template_info['label'])
		except:
			return ref_link, "View Template '%s'" % obj_id

	if obj_type == "errorgroup":
		ref_link = reverse("tomato.dumpmanager.group_info", kwargs={"group_id": obj_id})
		try:
			errorgroup_info = api.errorgroup_info(obj_id)
			return ref_link, "View Error group '%s'" % errorgroup_info['description']
		except:
			return ref_link, "View Error group '%s'" % obj_id

	return "", "%s %s" % (obj_type, obj_id)