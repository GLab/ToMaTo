#!/usr/bin/python
import subprocess

def need(): #is this module able to handle packages for the current template?
	return True #TODO: this is a stub

def ident(): #identity of module for debugging.
	return 'apt_get'

def get_urls(packagelist):	#returns list of packages to install and their urls
							#{'urls':[],'order':[]
							#important: in the returned object, order and urls must be in the same order!
	urlList=[]
	order=[]
	proc_update = subprocess.call(['apt-get','update'])
	proc = subprocess.Popen(['apt-get','install','--print-uris','-y','-qq']+packagelist,stdout=subprocess.PIPE)
	for line in iter(proc.stdout.readline,''):
		l = line.split()
		urlList.append(l[0])
		order.append(l[1])
	return { 'urls':urlList, 'order':order}

def install(filename): #installs a package located at filename
	proc = subprocess.call(['dpkg','-i',filename])
