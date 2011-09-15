import all

if __name__ == "__main__":
	runs = 50
	succeeded = 0
	failed = 0
	for n in xrange(0, runs):
		print "-" * 50
		print "Test run %d" % (n+1)
		print "-" * 50
		if all.run(False):
			succeeded += 1
		else:
			failed += 1
	print "%d succeeded, %d failed" % (succeeded, failed)	