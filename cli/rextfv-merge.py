#!/usr/bin/python
import sys, os, tarfile, random, shutil, glob


autoexecfilename='auto_exec.*'
statusdirname='exec_status'
tmpdir = '/tmp'

progname="rextfv-merge v0.1"

print progname
print ''

#map arguments
args = sys.argv[1:]
infiles = []
outfile = ''
curmode = 1
for arg in args:
	if arg=="-i":
		curmode = 1
	else:
		if arg=="-o":
			curmode = 0
		else:
			if curmode==1:
				infiles.append(arg)
			else:
				outfile=arg
				curmode=1

#create working dir
workingdir = str(random.randint(10000,99999))
while os.path.isdir(os.path.join(tmpdir,'rextfv_merge_'+workingdir)):
	workingdir = str(random.randint(10000,99999))
workingdir = os.path.join(tmpdir,'rextfv_merge_'+workingdir)
os.makedirs(workingdir)


#create directory structure in working dir
#  extract archives
#  create autoexec script
f = open(os.path.join(workingdir,'auto_exec.sh'),'w+')
f.write('#!/bin/bash\n')
f.write('echo This file was created by '+progname+'\n')
for i in range(0,len(infiles)):
	print  '('+str(i+1)+'/'+str(len(infiles))+') processing '+infiles[i]
	targetdir = os.path.join(workingdir,str(i))
	os.makedirs(targetdir)
	t = tarfile.open(infiles[i])
	t.extractall(path=targetdir)
	t.close()

	f.write('echo ""\n')
	f.write('echo "Starting auto-exec of '+infiles[i]+'"\necho "#########################################################"\n')
	if glob.glob(os.path.join(targetdir,autoexecfilename)):
		if not os.path.exists(os.path.join(targetdir,statusdirname)):
			print '                 will be auto-executed.'
			f.write('ln -s $nlxtp_dir/'+statusdirname+' $nlxtp_dir/'+str(i)+'/'+statusdirname+'\n')
			f.write('cd $nlxtp_dir/'+str(i)+'\n')
			f.write('chmod +x $nlxtp_dir/'+str(i)+'/'+autoexecfilename+'\n')
			f.write('nlxtp_dir=$nlxtp_dir/'+str(i)+' $(find $nlxtp_dir/'+str(i)+'/'+autoexecfilename+' -type f)\n')
		else:
			print '                 will not be auto-executed (status path exists).'
			f.write('echo found status path. aborting...\n')
	else:
		print '                 will not be auto-executed (no auto-exec script).'
		f.write('echo found no autoexec script. aborting...\n')
	print ''

f.write('echo ""\necho done.\n')
f.close()

print 'creating output file: '+outfile
t = tarfile.open(outfile,'w:gz')
t.add(workingdir,arcname="")
t.close()

shutil.rmtree(workingdir)
