
import os, shutil

def remove(path, recursive=False):
	if recursive and os.path.isdir(path):
		shutil.rmtree(path)
	else:
		os.remove(path)

def copy(src, dst):
	shutil.copy(src, dst)

def getSize(path):
	op = os.path
	return sum((sum(map(op.getsize, filter(op.isfile, (op.join(p, f) for f in fs)))) for p, ds, fs in os.walk(path)))