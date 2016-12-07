import lib.newcmd.virsh
import sys
from lib.constants import ActionName, StateName, TypeName

print str(sys.argv)
command = sys.argv[1]
args = "1"
if sys.argv.__len__() >= 3 :
	args = sys.argv[2]


vir = lib.newcmd.virsh.virsh(TypeName.KVM)

if command == "start":
	vir.vm_start(int(args))
if command == "prepare":
	vir.vm_prepare(int(args))
if command == "stop":
	vir.vm_stop(int(args), bool(sys.argv[3]))
if command == "destroy":
	vir.vm_destroy(int(args))
if command == "status":
	print vir.getVMs()
if command == "set":
	i = 3
	attrs = {}
	while i < sys.argv.__len__():
		if str(sys.argv[i]) == "usbtablet":
			if str(sys.argv[i+1]) == "False":
				attrs[str(sys.argv[i])] = False
			else:
				attrs[str(sys.argv[i])] = True
			i += 2
		else:
			attrs[str(sys.argv[i])] = str(sys.argv[i+1])
			i += 2
	vir.set_Attributes(int(args), attrs)

#vir.vm_prepare(1)

