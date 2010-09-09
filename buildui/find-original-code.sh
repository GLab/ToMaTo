#!/bin/bash
#Import revision: 5dfe202fc1741cf8f62c5a167524aa1c7c750bd6

echo Step 1: Find all lines that somehow stem from the origin
find . -name *.java | while read i; do git blame -M10 -C10 -w -c $i; done | fgrep 5dfe202f | cut -d\) -f2- > step1.txt
wc -l < step1.txt

echo Step 2: Remove all comments and license headers
grep -v '^[ ]*//' < step1.txt | grep -v '^[ /]*[*]' | grep -v '^[ ]*#' > step2.txt
wc -l < step2.txt

echo Step 3: Remove all empty and very short lines
grep -E "[[:alnum:]]{3,}" < step2.txt > step3.txt
wc -l < step3.txt 

echo Step 4: Remove duplicate lines
sed 's/ //g;s/\t//g' < step3.txt | sort | uniq > step4.txt
wc -l < step4.txt 

echo Step 5: Compressed size
lzma < step4.txt | wc -c

rm step*.txt
