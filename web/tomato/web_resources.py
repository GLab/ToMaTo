__author__ = 't-gerhard'

import json, urllib2
from urlparse import urljoin

from lib.settings import get_settings, Config
import settings as config_module
settings = get_settings(config_module)

from django.shortcuts import render
import time
from .lib import wrap_rpc
from .lib.reference_library import techs
from .lib.exceptionhandling import wrap_and_handle_current_exception

def web_resources():
	return {
		'executable_archives': executable_archives(),
		'custom_element_icons': custom_element_icons()
	}

def custom_element_icons(ignore_errors=True):
	url = settings.get_web_resource_location(Config.WEB_RESOURCE_CUSTOM_ELEMENT_ICONS)
	try:
		icon_setting_list = json.load(urllib2.urlopen(url))
		for l in icon_setting_list:
			l["url"] = urljoin(url, l["url"])
		return icon_setting_list
	except:
		if ignore_errors:
			return ()
		else:
			raise


def executable_archives(split_alternatives=True, ignore_errors=True):
	default_executable_archives_list_url = settings.get_web_resource_location(Config.WEB_RESOURCE_DEFAULT_EXECUTABLE_ARCHIVE_LIST)
	try:
		default_archive_list = []
		default_archive_list_imported = json.load(urllib2.urlopen(default_executable_archives_list_url))
		for default_archive_listentry in default_archive_list_imported:
			assert 'name' in default_archive_listentry
			assert 'url' in default_archive_listentry
			entry = {
				'name': default_archive_listentry['name'],
				'label': default_archive_listentry.get('label', default_archive_listentry['name'])
			}
			url = urljoin(default_executable_archives_list_url, default_archive_listentry['url'])
			default_archive = json.load(urllib2.urlopen(url))
			assert 'default_archive' in default_archive

			if 'icon' in default_archive:
				entry['icon'] = urljoin(url, default_archive['icon'])
			else:
				entry['icon'] = None

			entry['description'] = default_archive.get('description', None)
			entry['creation_date'] = default_archive.get('creation_date', None)
			if entry['creation_date']:
				entry['creation_date'] = time.mktime(time.strptime(entry['creation_date'], '%Y-%m-%d'))

			entry['default_archive'] = urljoin(url, default_archive['default_archive'])

			if split_alternatives:
				entry['alternatives'] = {k: dict() for k in techs()}
			else:
				entry['alternatives'] = []

			for alternative in default_archive.get('alternatives', []):
				assert 'templates' in alternative
				assert 'archive' in alternative
				alt_entry = {
					'url': urljoin(url, alternative['archive']),
					'creation_date': alternative.get('creation_date', None)
				}
				alt_entry['description'] = alternative.get('description', None)
				if alt_entry['creation_date']:
					alt_entry['creation_date'] = time.mktime(time.strptime(alt_entry['creation_date'], '%Y-%m-%d'))
				else:
					alt_entry['creation_date'] = entry['creation_date']

				if split_alternatives:
					for template in alternative['templates']:
							if ':' in template:
								tech, template_name = template.split(':')
								entry['alternatives'][tech][template_name] = alt_entry
							else:
								for tech in techs():
									entry['alternatives'][tech][template] = alt_entry
				else:
					alt_entry['templates'] = alternative['templates']
					entry['alternatives'].append(alt_entry)


			default_archive_list.append(entry)

		return default_archive_list
	except:
		if ignore_errors:
			return ()
		else:
			raise


@wrap_rpc
def executable_archive_list(api, request):
	default_executable_archives_list_url = settings.get_web_resource_location(Config.WEB_RESOURCE_DEFAULT_EXECUTABLE_ARCHIVE_LIST)
	archives = executable_archives(False, True)
	for archive in archives:
		archive['alternatives'] = len(archive['alternatives'])
	return render(request, 'web_resources/default_executable_archive_list.html', {'archive_list': archives, 'default_executable_archives_list_url': default_executable_archives_list_url})

@wrap_rpc
def custom_element_icon_list(api, request):
	url = settings.get_web_resource_location(Config.WEB_RESOURCE_CUSTOM_ELEMENT_ICONS)
	icons = custom_element_icons(True)
	return render(request, 'web_resources/custom_element_icons_list.html', {'icon_list': icons, 'index_url': url})

@wrap_rpc
def executable_archive_info(api, request, name):
	archives = executable_archives(False, True)

	# find archive corresponding to name
	archive = None
	for archive_ in archives:
		if archive_['name'] == name:
			archive = archive_
	if not archive:
		return  # fixme: return 404

	# build template dict for later usage
	template_list = api.template_list()
	template_dict = {k: dict() for k in techs()}
	for template in template_list:
		template_dict[template['type']][template['name']] = template

	# convert template list into better format
	alt_list_new = []
	for alternative in archive['alternatives']:
		templates_described = []
		for template in alternative['templates']:
			if ':' in template:
				type, template_name = template.split(':')
				templates_described.append((type, template_name))
			else:
				for tech in techs():
					templates_described.append((tech, template))
		alternative['templates'] = []
		for type, name in templates_described:
			template = template_dict.get(type, {}).get(name, None)
			if template:
				alternative['templates'].append({
					'id': template['id'],
					'name': name,
					'label': template['label'] if template['label'] else name,
					'type': type
				})

	default_executable_archives_list_url = settings.get_web_resource_location(Config.WEB_RESOURCE_DEFAULT_EXECUTABLE_ARCHIVE_LIST)
	return render(request, 'web_resources/default_executable_archive_info.html', {'archive': archive, 'default_executable_archives_list_url': default_executable_archives_list_url})