# Remove all traces of hostmanager from environment to allow import of backend 
import sys
for mod in sys.modules.keys():
	if mod.startswith("hostmanager") or mod.startswith("django") or mod.startswith("cli"):
		del sys.modules[mod]