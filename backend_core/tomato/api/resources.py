# -*- coding: utf-8 -*-
# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from ..lib.cache import cached, invalidates

def _getTemplate(id_):
	res = Template.objects.get(id=id_)
	UserError.check(res, code=UserError.ENTITY_DOES_NOT_EXIST, message="Template does not exist", data={"id": id_})
	return res

def _getNetwork(id_):
	res = Network.objects.get(id=id_)
	UserError.check(res, code=UserError.ENTITY_DOES_NOT_EXIST, message="Network does not exist", data={"id": id_})
	return res

def _getNetworkInstance(id_):
	res = NetworkInstance.objects.get(id=id_)
	UserError.check(res, code=UserError.ENTITY_DOES_NOT_EXIST, message="Network instance does not exist", data={"id": id_})
	return res

def _getProfile(id_):
	res = Profile.objects.get(id=id_)
	UserError.check(res, code=UserError.ENTITY_DOES_NOT_EXIST, message="Profile does not exist", data={"id": id_})
	return res

@cached(timeout=6*3600, autoupdate=True)
def template_list(tech=None):
	"""
	Retrieves information about all resources.

	Parameter *tech*:
	  If *tech* is set, only resources with a matching tech will be returned.

	Return value:
	  A list with information entries of all matching templates. Each list
	  entry contains exactly the same information as returned by
	  :py:func:`template_info`. If no resource matches, the list is empty.
	"""
	res = Template.objects(tech=tech) if tech else Template.objects()
	return [r.info() for r in res]

@invalidates(template_list)
def template_create(tech, name, attrs=None):
	"""
	Creates a template of given tech and name, configuring it with the given attributes.

	Parameter *tech*:
	  The parameter *tech* must be a string identifying one of the supported
	  template techs.

	Parameter *name*:
	  The parameter *name* must be a string giving a name for the template.

	Parameter *attrs*:
	  The attributes of the template can be given as the parameter *attrs*.
	  This parameter must be a dict of attributes if given. Attributes can
	  later be changed using :py:func:`template_modify`.

	Return value:
	  The return value of this method is the info dict of the new template as
	  returned by :py:func:`resource_info`.
	"""
	if not attrs: attrs = {}
	attrs = dict(attrs)
	attrs.update(name=name, tech=tech)
	res = Template.create(attrs)
	return res.info()

@invalidates(template_list)
def template_modify(id, attrs):
	"""
	Modifies a template, configuring it with the given attributes.

	Parameter *tech*:
	  The parameter *tech* must be a string identifying one of the supported
	  template techs.

	Parameter *name*:
	  The parameter *name* must be a string giving a name for the template.

	Parameter *attrs*:
	  The attributes of the template can be given as the parameter *attrs*.
	  This parameter must be a dict of attributes.

	Return value:
	  The return value of this method is the info dict of the resource as
	  returned by :py:func:`template_info`. This info dict will reflect all
	  attribute changes.

	Exceptions:
	  If the given template does not exist an exception *template does not
	  exist* is raised.
	"""
	res = _getTemplate(id)
	res.modify(attrs)
	return res.info()


@invalidates(template_list)
def template_remove(id):
	"""
	Removes a template.

	Parameter *tech*:
	  The parameter *tech* must be a string identifying one of the supported
	  template techs.

	Parameter *name*:
	  The parameter *name* must be a string giving a name for the template.

	Return value:
	  The return value of this method is ``None``.

	Exceptions:
	  If the given template does not exist an exception *template does not
	  exist* is raised.
	"""
	res = _getTemplate(id)
	res.remove()
	return {}

def template_id(tech, name):
	"""
	translate tech and name to a template id
	"""
	return Template.objects.get(tech=tech, name=name).id

def template_info(id, include_torrent_data=False): #@ReservedAssignment
	"""
	Retrieves information about a template.

	Parameter *tech*:
	  The parameter *tech* must be a string identifying one of the supported
	  template techs.

	Parameter *name*:
	  The parameter *name* must be a string giving a name for the template.

	Parameter *include_torrent_data*:
	  boolean
	  if true, the return value includes the base64-encoded torrent file.
	  This may throw an error when a user without access to it tries to access a restricted template.

	Return value:
	  The return value of this method is a dict containing information
	  about this template.

	Exceptions:
	  If the given template does not exist an exception *template does not
	  exist* is raised.
	"""
	res = _getTemplate(id)
	return res.info(include_torrent_data=include_torrent_data)

@cached(timeout=6*3600, autoupdate=True)
def profile_list(tech=None):
	"""
	Retrieves information about all resources.

	Parameter *tech*:
	  If *tech* is set, only resources with a matching tech will be returned.

	Return value:
	  A list with information entries of all matching profiles. Each list
	  entry contains exactly the same information as returned by
	  :py:func:`profile_info`. If no resource matches, the list is empty.
	"""
	res = Profile.objects(tech=tech) if tech else Profile.objects()
	return [r.info() for r in res]


@invalidates(profile_list)
def profile_create(tech, name, attrs=None):
	"""
	Creates a profile of given tech and name, configuring it with the given attributes.

	Parameter *tech*:
	  The parameter *tech* must be a string identifying one of the supported
	  profile techs.

	Parameter *name*:
	  The parameter *name* must be a string giving a name for the profile.

	Parameter *attrs*:
	  The attributes of the profile can be given as the parameter *attrs*.
	  This parameter must be a dict of attributes if given. Attributes can
	  later be changed using :py:func:`profile_modify`.

	Return value:
	  The return value of this method is the info dict of the new profile as
	  returned by :py:func:`resource_info`.
	"""
	if not attrs: attrs = {}
	attrs = dict(attrs)
	attrs.update(name=name, tech=tech)
	res = Profile.create(attrs)
	return res.info()


@invalidates(profile_list)
def profile_modify(id, attrs):
	"""
	Modifies a profile, configuring it with the given attributes.

	Parameter *tech*:
	  The parameter *tech* must be a string identifying one of the supported
	  profile techs.

	Parameter *name*:
	  The parameter *name* must be a string giving a name for the profile.

	Parameter *attrs*:
	  The attributes of the profile can be given as the parameter *attrs*.
	  This parameter must be a dict of attributes.

	Return value:
	  The return value of this method is the info dict of the resource as
	  returned by :py:func:`profile_info`. This info dict will reflect all
	  attribute changes.

	Exceptions:
	  If the given profile does not exist an exception *profile does not
	  exist* is raised.
	"""
	res = _getProfile(id)
	res.modify(attrs)
	return res.info()


@invalidates(profile_list)
def profile_remove(id):
	"""
	Removes a profile.

	Parameter *tech*:
	  The parameter *tech* must be a string identifying one of the supported
	  profile techs.

	Parameter *name*:
	  The parameter *name* must be a string giving a name for the profile.

	Return value:
	  The return value of this method is ``None``.

	Exceptions:
	  If the given profile does not exist an exception *profile does not
	  exist* is raised.
	"""
	res = _getProfile(id)
	res.remove()
	return {}

def profile_id(tech, name):
	"""
	translate tech and name to a template id
	"""
	return Profile.objects.get(tech=tech, name=name).id

def profile_info(id):
	"""
	Retrieves information about a profile.

	Parameter *tech*:
	  The parameter *tech* must be a string identifying one of the supported
	  profile techs.

	Parameter *name*:
	  The parameter *name* must be a string giving a name for the profile.

	Return value:
	  The return value of this method is a dict containing information
	  about this profile.

	Exceptions:
	  If the given profile does not exist an exception *profile does not
	  exist* is raised.
	"""
	res = _getProfile(id)
	return res.info()


@cached(timeout=6*3600, autoupdate=True)
def network_list():
	"""
	Retrieves information about all resources.

	Return value:
	  A list with information entries of all matching networks. Each list
	  entry contains exactly the same information as returned by
	  :py:func:`network_info`. If no resource matches, the list is empty.
	"""
	res = Network.objects()
	return [r.info() for r in res]


@invalidates(network_list)
def network_create(kind, attrs=None):
	"""
	Creates a network of given tech and name, configuring it with the given attributes.

	Parameter *kind*:
	  The parameter *kind* must be a string identifying the kind of the network.

	Parameter *attrs*:
	  The attributes of the network can be given as the parameter *attrs*.
	  This parameter must be a dict of attributes if given. Attributes can
	  later be changed using :py:func:`network_modify`.

	Return value:
	  The return value of this method is the info dict of the new network as
	  returned by :py:func:`resource_info`.
	"""
	if not attrs: attrs = {}
	attrs = dict(attrs)
	attrs.update(kind=kind)
	res = Network.create(attrs)
	return res.info()


@invalidates(network_list)
def network_modify(id, attrs):
	"""
	Modifies a network, configuring it with the given attributes.

	Parameter *kind*:
	  The parameter *kind* must be a string identifying the kind of the network.

	Parameter *attrs*:
	  The attributes of the network can be given as the parameter *attrs*.
	  This parameter must be a dict of attributes.

	Return value:
	  The return value of this method is the info dict of the resource as
	  returned by :py:func:`network_info`. This info dict will reflect all
	  attribute changes.

	Exceptions:
	  If the given network does not exist an exception *network does not
	  exist* is raised.
	"""
	res = _getNetwork(id)
	res.modify(attrs)
	return res.info()


@invalidates(network_list)
def network_remove(id):
	"""
	Removes a network.

	Parameter *kind*:
	  The parameter *kind* must be a string identifying the kind of the network.

	Return value:
	  The return value of this method is ``None``.

	Exceptions:
	  If the given network does not exist an exception *network does not
	  exist* is raised.
	"""
	res = _getNetwork(id)
	res.remove()
	return {}


def network_info(id): #@ReservedAssignment
	"""
	Retrieves information about a network.

	Parameter *kind*:
	  The parameter *kind* must be a string identifying the kind of the network.

	Return value:
	  The return value of this method is a dict containing information
	  about this network.

	Exceptions:
	  If the given network does not exist an exception *network does not
	  exist* is raised.
	"""
	res = _getNetwork(id)
	return res.info()


@cached(timeout=6*3600, autoupdate=True)
def network_instance_list(network=None, host=None):
	"""
	Retrieves information about all resources.

	Parameter *kind*:
	  If *kind* is set, only resources with a matching kind will be returned.

	Return value:
	  A list with information entries of all matching network_instances. Each list
	  entry contains exactly the same information as returned by
	  :py:func:`network_instance_info`. If no resource matches, the list is empty.
	"""
	res = NetworkInstance.objects
	if network:
		res = res.filter(network=_getNetwork(network))
	if host:
		res = res.filter(hosT=_getHost(host))
	return [r.info() for r in res]


@invalidates(network_instance_list)
def network_instance_create(network, host, attrs=None):
	"""
	Creates a network_instance of given kind and host, configuring it with the given attributes.

	Parameter *kind*:
	  The parameter *kind* must be a string identifying one of the supported
	  network_instance kinds.

	Parameter *host*:
	  The parameter *host* must be a string giving a host for the network_instance.

	Parameter *attrs*:
	  The attributes of the network_instance can be given as the parameter *attrs*.
	  This parameter must be a dict of attributes if given. Attributes can
	  later be changed using :py:func:`network_instance_modify`.

	Return value:
	  The return value of this method is the info dict of the new network_instance as
	  returned by :py:func:`resource_info`.
	"""
	if not attrs: attrs = {}
	attrs = dict(attrs)
	attrs.update(host=host, network=network)
	res = NetworkInstance.create(attrs)
	return res.info()


@invalidates(network_instance_list)
def network_instance_modify(id, attrs):
	"""
	Modifies a network_instance, configuring it with the given attributes.

	Parameter *kind*:
	  The parameter *kind* must be a string identifying one of the supported
	  network_instance kinds.

	Parameter *host*:
	  The parameter *host* must be a string giving a host for the network_instance.

	Parameter *attrs*:
	  The attributes of the network_instance can be given as the parameter *attrs*.
	  This parameter must be a dict of attributes.

	Return value:
	  The return value of this method is the info dict of the resource as
	  returned by :py:func:`network_instance_info`. This info dict will reflect all
	  attribute changes.

	Exceptions:
	  If the given network_instance does not exist an exception *network_instance does not
	  exist* is raised.
	"""
	res = _getNetworkInstance(id)
	res.modify(attrs)
	return res.info()


@invalidates(network_instance_list)
def network_instance_remove(id):
	"""
	Removes a network_instance.

	Parameter *kind*:
	  The parameter *kind* must be a string identifying one of the supported
	  network_instance kinds.

	Parameter *host*:
	  The parameter *host* must be a string giving a host for the network_instance.

	Return value:
	  The return value of this method is ``None``.

	Exceptions:
	  If the given network_instance does not exist an exception *network_instance does not
	  exist* is raised.
	"""
	getCurrentUserInfo().check_may_remove_technical_resources()
	res = _getNetworkInstance(id)
	res.remove()
	return {}


def network_instance_info(id):
	"""
	Retrieves information about a network_instance.

	Parameter *kind*:
	  The parameter *kind* must be a string identifying one of the supported
	  network_instance kinds.

	Parameter *host*:
	  The parameter *host* must be a string giving a host for the network_instance.

	Return value:
	  The return value of this method is a dict containing information
	  about this network_instance.

	Exceptions:
	  If the given network_instance does not exist an exception *network_instance does not
	  exist* is raised.
	"""
	res = _getNetworkInstance(id)
	return res.info()


from ..resources.network import Network, NetworkInstance
from ..resources.profile import Profile
from ..resources.template import Template
from .host import _getHost
from ..lib.error import UserError
