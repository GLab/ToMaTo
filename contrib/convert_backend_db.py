#!/usr/bin/env python

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
old = client.tomato
core = client.tomato_backend_core
debug = client.tommato_backend_debug
users = client.tomato_backend_users

for table in ["host", "host_element", "host_connection", "element", "connection", "link_statistics", "template", "network", "network_instance", "profile"]:
	core[table].drop()
	for obj in old[table].find():
		for field in ["total_usage", "usage_statistics", "dump_last_fetch", "permissions"]:
			if field in obj:
				del obj[field]
		core[table].insert_one(obj)
	print "%d %ss converted" % (core[table].count(), table)

core.site.drop()
for obj in old.site.find():
	obj["organization"] = old.organization.find_one({"_id": obj["organization"]})["name"]
	core.site.insert_one(obj)
print "%d sites converted" % core.site.count()

core.topology.drop()
for obj in old.topology.find():
	if "total_usage" in obj:
		del obj["total_usage"]
	perms = []
	for perm in obj["permissions"]:
		user = old.user.find_one({"_id": perm["user"]})
		if not user:
			continue
		perm["user"] = user["name"]
		perms.append(perm)
	obj["permissions"] = perms
	core.topology.insert_one(obj)
print "%d topologies converted" % core.topology.count()

for table in ["user", "organization"]:
	users[table].drop()
	for obj in old[table].find():
		if "total_usage" in obj:
			del obj["total_usage"]
		users[table].insert_one(obj)
	print "%d %ss converted" % (users[table].count(), table)


# not converting error dumps, makes no sense
# not converting accounting data, too complicated for now