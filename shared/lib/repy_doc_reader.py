def read_repy_doc(filename):
	with open(filename, "r") as f:
		script = f.read()
	if script[:3] == '"""':
		if '"""' in script[3:]:
			return script[3:].split('"""', 1)[0].strip()
