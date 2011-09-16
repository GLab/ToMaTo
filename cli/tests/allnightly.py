import all, time

if __name__ == "__main__":
	runs = 100
	succeeded = 0
	failed = 0
	for n in xrange(1, runs+1):
		start = time.time()
		print "-" * 50
		print "Test run %d" % n
		print "-" * 50
		if all.run(False):
			succeeded += 1
		else:
			failed += 1
		min = (time.time()-start)/60.0
		print "-" * 50
		print "Test run %d finished in %.1f min" % (n, min) 
		print "Statistics: %d succeeded, %d failed" % (succeeded, failed)
		print "-" * 50
		if n != runs:
			time.sleep(10)
