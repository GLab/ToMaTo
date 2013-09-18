#!/usr/bin/python
import json

modules = ['apt_get'] #it will pick the first of these modules where module.need()==True
def find_module():
	for mod in modules:
		modi = __import__(mod)
		if modi.need():
			return modi
	return None

def get_urls(pacs_json,module):
	paclist = pacs_json['paclist']
	urls={}
	ident=''

	inf = module.get_urls(paclist)
	ident= module.ident()

	return {
		'urls':inf['urls'],
		'order':inf['order'],
		'ident':ident,
		'pacs_json':pacs_json
	}

def install(pacs_json,module):
	pacs = pacs_json['order']
	ident = ''

	for i in pacs:
		module.install('packages/'+i)
	ident=module.ident()

	return {
		'ident':ident,
		'pacs_json':pacs_json
	}


#expects a json object, containing an array called 'paclist' in pacs.json
json_data=open('pacs.json','r')
pacs_json=json.load(json_data)
json_data.close()

module = find_module()

result={}
if pacs_json['mode']=='get_urls':
	result = get_urls(pacs_json,module)
if pacs_json['mode']=='install':
	result = install(pacs_json,module)

json_out=open('result.json','w+')
json.dump(result,json_out)
json_out.close()

