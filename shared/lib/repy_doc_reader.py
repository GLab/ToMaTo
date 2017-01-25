def read_repy_doc(filename):
	with open(self.getPath(), "r") as f:
		script = f.read()
	if script[:3] == '"""':
		if '"""' in script[3:]:
			self.repy_doc = script[3:].split('"""', 1)[0].strip()
