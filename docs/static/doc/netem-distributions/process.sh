#!/bin/bash
for i in plain uniform normal pareto paretonormal; do
  rm $i.data
  fgrep icmp_seq < $i.raw | awk '{ print $7 }' | cut -d = -f 2 | sort -n | ./prob.py > $i.data
done
gnuplot graph.gnpl
