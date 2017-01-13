from django.core.urlresolvers import reverse

from constants import TypeName, TechName

from .exceptionhandling import deprecated
from .references import Reference

@deprecated("constants.Tech.ONSCREEN")
def tech_to_label(tech):
	return TechName.ONSCREEN.get(tech, tech)

@deprecated("constants.Type.ONSCREEN")
def type_to_label(type_):
	return TypeName.ONSCREEN.get(type_, type_)

@deprecated('new constant in constants.py')
def techs():
	return [TypeName.KVM, TypeName.KVMQM, TypeName.OPENVZ, TypeName.REPY]

@deprecated('Reference.ONSCREEN')
def entity_to_label(entity):
	return Reference.ONSCREEN[entity]

@deprecated('Reference.KEYS')
def reference_config():
	return Reference.KEYS


def resolve_reference(api, ref):
	"""
	use API and a reference to display a link to the respective object in a frontend.
	:param api:
	:param resolver: funtion that converts
	:param ref:
	:return: tuple: link url, link text
	"""
	obj_type, obj_id = (ref[0], ref[1])

	if obj_type == Reference.TOPOLOGY:
		ref_link = reverse("tomato.topology.info", kwargs={"id": obj_id})
		try:
			topology_info = api.topology_info(obj_id)
			return ref_link, "View Topology '%s'" % topology_info["name"]
		except:
			return ref_link, "View Topology [%s]" % obj_id

	if obj_type == Reference.HOST:
		ref_link = reverse("tomato.admin.host.info", kwargs={"name": obj_id})
		return ref_link, "View Host '%s'" % obj_id

	if obj_type == Reference.SITE:
		ref_link = reverse("tomato.admin.site.info", kwargs={"name": obj_id})
		try:
			site_info = api.site_info(obj_id)
			return ref_link, "View Site '%s'" % site_info['label']
		except:
			return ref_link, "View Site '%s'" % obj_id

	if obj_type == Reference.ORGANIZATION:
		ref_link = reverse("tomato.admin.organization.info", kwargs={"name": obj_id})
		try:
			organization_info = api.organization_info(obj_id)
			return ref_link, "View Organization '%s'" % organization_info['label']
		except:
			return ref_link, "View Organization '%s'" % obj_id

	if obj_type == Reference.ACCOUNT:
		ref_link = reverse("tomato.account.info", kwargs={"id": obj_id})
		try:
			account_info = api.account_info(obj_id)
			return ref_link, "View User Account '%s'" % account_info['realname']
		except:
			return ref_link, "View User Account '%s'" % obj_id

	if obj_type == Reference.PROFILE:
		ref_link = reverse("tomato.profile.info", kwargs={"res_id": obj_id})
		try:
			profile_info = api.profile_info(obj_id)
			return ref_link, "View %s Device Profile '%s'" % (TypeName.ONSCREEN.get(profile_info['tech'],profile_info['tech']), profile_info['label'])
		except:
			return ref_link, "View Device Profile '%s'" % obj_id

	if obj_type == Reference.TEMPLATE:
		ref_link = reverse("tomato.template.info", kwargs={"res_id": obj_id})
		try:
			template_info = api.template_info(obj_id)
			return ref_link, "View %s Template '%s'" % (TypeName.ONSCREEN.get(template_info['tech'],template_info['tech']), template_info['label'])
		except:
			return ref_link, "View Template '%s'" % obj_id

	if obj_type == Reference.ERRORGROUP:
		ref_link = reverse("tomato.dumpmanager.group_info", kwargs={"group_id": obj_id})
		try:
			errorgroup_info = api.errorgroup_info(obj_id)
			return ref_link, "View Error group '%s'" % errorgroup_info['description']
		except:
			return ref_link, "View Error group '%s'" % obj_id

	return "", "%s %s" % (obj_type, obj_id)
