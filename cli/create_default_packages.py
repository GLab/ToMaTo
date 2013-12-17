from getpackages import create_package
import tomato, lib
import argparse, getpass, os

def get_all_linux_openvz_templates(conn):
	res = []
	templs = conn.resource_list('template')
	for templ in templs:
		if templ['attrs']['tech'] == 'openvz' and templ['attrs']['subtype'] == 'linux':
			res.append(templ['attrs']['name'])
	return res

def get_connection_from_params():
	parser = argparse.ArgumentParser(description="ToMaTo XML-RPC Client", add_help=False)
	parser.add_argument('--help', action='help')
	parser.add_argument("--hostname" , "-h", required=True, help="the host of the server")
	parser.add_argument("--port", "-p", default=8000, help="the port of the server")
	parser.add_argument("--ssl", "-s", action="store_true", default=False, help="whether to use ssl")
	parser.add_argument("--client_cert", required=False, default=None, help="path of the ssl certificate")
	parser.add_argument("--username", "-U", help="the username to use for login")
	parser.add_argument("--password", "-P", help="the password to use for login")
	options = parser.parse_args()
	
	if not options.username and not options.client_cert:
		options.username=raw_input("Username: ")
	if not options.password and not options.client_cert:
		options.password=getpass.getpass("Password: ")
		
	return tomato.getConnection(options.hostname, options.port, options.ssl, options.username, options.password, options.client_cert)




templates = ['ubuntu-10.04_x86', 'debian-6.0_x86', 'debian-6.0_x86_64', 'debian-7.0_x86', 'debian-7.0_x86_64', 'ubuntu-12.04_x86', 'ubuntu-12.04_x86_64', 'ubuntu-10.04_x86_64']
packages = [
		{'name':'python', 'packets':['python']},
		{'name':'openjdk6-jre','packets':['openjdk-6-jre']},
		{'name':'iperf','packets':['iperf']}
	]

output_dir =os.path.expanduser('~')
print "saving result to "+output_dir

conn = get_connection_from_params()

for p in packages:
	print "_____________________________________"
	print "building "+p['name']
	print ""
	create_package(conn,templates,'openvz',os.path.join(output_dir,'install_'+p['name']+'.tar.gz'),p['packets'],site='ukl')
	print ""