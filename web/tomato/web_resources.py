__author__ = 't-gerhard'

import json, urllib2
from urlparse import urljoin
from settings import default_executable_archives_list_url
from .lib.reference_library import techs

def web_resources():
	return {
		'executable_archives': executable_archives()
	}


def executable_archives():
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

		entry['default_archive'] = urljoin(url, default_archive['default_archive'])

		entry['alternatives'] = {k: dict() for k in techs()}
		for alternative in default_archive.get('alternatives', []):
			assert 'templates' in alternative
			assert 'archive' in alternative
			for template in alternative['templates']:
				alt_entry = {
					'url': urljoin(url, alternative['archive'])
				}
				alt_entry['description'] = alternative.get('description', None)
				if ':' in template:
					tech, template_name = template.split(':')
					entry['alternatives'][tech][template_name] = alt_entry
				else:
					for tech in techs():
						entry['alternatives'][tech][template] = alt_entry

		default_archive_list.append(entry)

	return default_archive_list