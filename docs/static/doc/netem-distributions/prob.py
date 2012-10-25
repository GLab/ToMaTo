#!/usr/bin/env python

counts = {}
vals = 0.0
resolution = 10.0

try:
  while(True):
    val = float(raw_input())
    val = round(val*resolution)
    counts[val] = counts.get(val, 0.0) + 1.0
    vals += 1.0
except EOFError:
    for i in range(0, int(100.0*resolution)):
      print "%s %s" % (i/resolution, (counts.get(i-1, 0.0)+2.0*counts.get(i, 0.0)+counts.get(i+1, 0.0))/4.0/vals*resolution)
