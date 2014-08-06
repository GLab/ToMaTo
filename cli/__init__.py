# Remove all traces of backend from environment to allow import of hostmanager 
import sys
for mod in sys.modules.keys():
	if mod.startswith("backend") or mod.startswith("django") or mod.startswith("hostmanager"):
		del sys.modules[mod]