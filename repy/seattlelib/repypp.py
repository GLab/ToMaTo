#!/usr/bin/env python

""" 
Author: Justin Cappos
 
Start Date: August 7, 2008

Purpose: A preprocessor for repy.  It includes dependent files as needed.
This is used to help the programmer avoid the need to use import.   They
can instead use "include X" which works somewhat like "from X import *".
However, include must be the first character on the line (no indentation!)

If a.py contains:

def foo():
  pass

and b.py contains:

include a.py
def bar():
  pass

then after inclusion the file will look like:

#begin include a.py
def foo():
  pass
#end include a.py
def bar():
  pass
   
Note:You can change a.py and then rerun the inclusion on the preprocessed 
output file and it will update a.py

Note: Doesn't correctly support recursion currently...

"""


usestring = """repypp.py infile outfile

preprocesses infile and includes content from the current directory.  Output is
written to outfile.   Outfile and infile must be distinct.
"""



import sys


def processfiledata(stringlist):
  # walk through the list and strip out any previously included data.   Also
  # note any included files and return a list of the names
  
  includelist = []
  outdata = []
 
  included_section = None
  for line in stringlist:
    # it's an include line... pretty simple to handle, just add the rest of the
    # line to the includelist after stripping off whitespace
    if line.startswith('include '):
      includelist.append(line[len('include '):].strip())
      outdata.append(line)
      continue

    # Am I inside of an included file?
    if not included_section:

      # add the file to the include list...
      if line.startswith('#begin include '):
        thisitem = line[len('#begin include '):]
        includelist.append(thisitem.strip())
        included_section = thisitem.strip()
        # don't strip here.   We want the newline, etc. to be written out
        outdata.append('include '+thisitem)
        continue

      # shouldn't see this if I'm not in an included section
      if line.startswith('#end include '):
        raise ValueError, "Found an #end include outside of an included section"
   
      # a normal line.  Let's append
      outdata.append(line)
      continue

    else:
      # I'm in an included section...

      # this might be my end include...
      if line.startswith('#end include '):
        if included_section == line[len('#end include '):].strip():
          # it's me!   Let's leave the included section
          included_section = None
          continue
        else:
          # it's okay, this may be a nested include section 
          continue
        
        # nothing to do.   I don't include data inside the included section
        continue
    
  #Append a newline to outdata to ensure included files end 
  #with an unindented blank line
  outdata.append("\n")
    
  return (includelist, outdata)
  

# 
def processfile(filename):

  # I'm going to read in all the file contents and put them into a dict keyed 
  # by name
  filedatadict = {}
  
  # start with a "todo" list of just the file mentioned...
  files_to_read = [filename]
  while files_to_read != []:

    # figure out which file to read...
    thisfilename = files_to_read.pop()

    if thisfilename in filedatadict:
      # I've already loaded it
      continue

    # read it in
    try:
      fileobj = file(thisfilename)
      filedata = fileobj.readlines()
      fileobj.close()
    except:
      print "Error opening source file '"+thisfilename+"'"
      sys.exit(1)

    # parse the contents...
    (includelist, parsedfiledata) = processfiledata(filedata)
    
    # add me to the dictionary
    filedatadict[thisfilename] = parsedfiledata
    
    # add unknown files to the list
    for thisfilename in includelist:  
      if thisfilename not in files_to_read:
        files_to_read.append(thisfilename)
    
  # at this point I've built a dictionary of all of the files I'll need to 
  # include.   I now need to walk through the starting file and actually 
  # include the data.

  # I think this is likely to be easiest to do recursively.   
  (filedata,includedfiles) =  recursive_build_outdata(filename, [], filedatadict)

  return filedata



def recursive_build_outdata(filename, includedfiles,filedict):
  retdata = []

  for line in filedict[filename]:
    if line.startswith('include '):
      includename = line[len('include '):]

      # already added, so note that and move on...
      if includename.strip() in includedfiles:
        retdata.append("#begin include "+includename)
        retdata.append("#already included "+includename)
        retdata.append("#end include "+includename)
        continue
      
      # Let's do the inclusion
      includedfiles.append(includename.strip())

      # get the filedata and use their included files as our own...
      (filedata, includedfiles) = recursive_build_outdata(includename.strip(), includedfiles, filedict)

      retdata.append("#begin include "+includename)
      # add whatever they gave me
      retdata = retdata + filedata
      retdata.append("#end include "+includename)

    else:
      # it's a normal line, just include
      retdata.append(line)

  return retdata, includedfiles
      
    



def main():
  
  if len(sys.argv)!= 3:
    print "Invalid number of arguments"
    print usestring
    sys.exit(1)


  # we don't support this (yet)
  if sys.argv[1] == sys.argv[2]:
    print "The infile and outfile must be different files"
    sys.exit(1)

  # get the outgoing file object
  try:
    outfileobj = file(sys.argv[2],'w')
  except:
    print "Error opening out file '"+sys.argv[2]+"'"
    sys.exit(1)



  # strip out any previously included files
  outfiledata = processfile(sys.argv[1])

  outfileobj.writelines(outfiledata)
  

if __name__ == '__main__':
  main()
