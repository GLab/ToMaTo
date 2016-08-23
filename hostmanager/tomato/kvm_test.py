import lib.newcmd.virsh_lib
import sys

print str(sys.argv)
command = sys.argv[1]
args = sys.argv[2]

vir = lib.newcmd.virsh_lib.virsh()

if command == "start":
	vir.vm_start(int(args))
if command == "create":
	vir.vm_prepare(int(args))
if command == "stop":
	vir.vm_stop(int(args), bool(sys.argv[3]))
if command == "destroy":
	vir.vm_destroy(int(args))

#vir.vm_prepare(1)

