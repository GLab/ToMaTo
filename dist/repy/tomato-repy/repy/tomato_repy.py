#!/usr/bin/env python
import sys, os

def parse_args():
    try:
       from arggparse import ArgumentParser as Parser
       argparser = True
    except:
       from optparse import OptionParser as Parser
       argparser = False
    parser = Parser(description="ToMaTo Repy Client")
    if argparser:
       addArg = parser.add_argument
    else:
       addArg = parser.add_option
    addArg('--program', '-p', help="a repy file to execute")
    addArg('--interface', '-i', action="append", help="a networking interface to expose to the repy program")
    addArg('--resources', '-r', help="path of the resource file")
    addArg('--quiet', '-q', default=False, action="store_true", help="disable all output methods")
    addArg('--verbose', '-v', default=False, action="store_true", help="enable debugging output")
    addArg('--runasroot', default=False, action="store_true", help="run script as root and do not drop privileges")
    addArg('--runas', default="nobody:nogroup", help="run script as a specific user:group")
    if argparser:    
        addArg("arguments", nargs="*", help="arguments for the repy program")
	options = parser.parse_args()
    else:
        (options, args) = parser.parse_args()
        options.arguments = args
    if not options.program:
       raise Exception("Program needed")
    if not options.resources:
       options.resources = os.path.dirname(os.path.realpath(sys.argv[0]))+"/default.resources"
    if not options.interface:
       options.interface=[]
    return options

def build_context(quiet):
    import repy
    context = {}
    context["echo"] = lambda s: sys.stdout.write(str(s) + "\n")
    import traceback
    context["print_exc"] = traceback.print_exc
    if quiet:
        context["echo"] = lambda s: None
        context["print_exc"] = lambda s: None
    import emulmisc
    context["randombytes"] = emulmisc.randombytes
    context["getruntime"] = emulmisc.getruntime
    context["exitall"] = emulmisc.exitall
    context["createlock"] = emulmisc.createlock
    context["getthreadname"] = emulmisc.getthreadname
    context["getlasterror"] = emulmisc.getlasterror
    import emultimer
    context["createthread"] = emultimer.createthread
    context["sleep"] = emultimer.sleep
    import emultap
    context["tuntap_read"] = emultap.device_read
    context["tuntap_read_any"] = emultap.device_read_any
    context["tuntap_send"] = emultap.device_send
    context["tuntap_list"] = emultap.device_list
    context["tuntap_info"] = emultap.device_info
    import emulstruct
    context["struct"] = emulstruct.struct
    return repy.prepare_usercontext({}, context)
    
def prepare_interfaces(interfaces):
    try:
        import emultap
        for iface in interfaces:
            parts = iface.split(",")
            name = parts[0]
            options = {"alias": name, "mtu": emultap.DEFAULT_MTU, "mode": "tap"}
            for opt in parts[1:]:
               (key, value) = opt.split("=")
               options[key]=value
            options["mtu"] = int(options["mtu"])
            if options["mode"] == "raw":
                emultap.device_open(name, **options)
            else:
                options["mode"] = {"tap": emultap.IFF_TAP | emultap.IFF_NO_PI, "tun": emultap.IFF_TUN | emultap.IFF_NO_PI, 
                  "tap+pi": emultap.IFF_TAP, "tun+pi": emultap.IFF_TUN}.get(options["mode"], emultap.IFF_TAP | emultap.IFF_NO_PI)
                emultap.device_create(name, **options)
    except IOError:
        if os.getuid() != 0:
            print >>sys.stderr, "Error: root privileges are needed to setup networking devices"
            sys.exit(-1)
        raise
    
def drop_privileges(user_group):
    if os.getuid() != 0:
        return #nothing to drop
    import pwd, grp
    (uname, gname) = user_group.split(":")
    running_uid = pwd.getpwnam(uname).pw_uid
    running_gid = grp.getgrnam(gname).gr_gid
    os.setgid(running_gid)
    os.setuid(running_uid)
    
def main(options):
    #prepare network interfaces
    if options.verbose: print >>sys.stderr, "Preparing networking interfaces %s" % options.interface
    prepare_interfaces(options.interface)

    #read program code
    if options.verbose: print >>sys.stderr, "Reading program from %s" % options.program
    import repy
    code = repy.read_file(options.program)
    
    #build usercontext
    if options.verbose: print >>sys.stderr, "Building script context"
    usercontext = build_context(options.quiet)
    
    #change directory to directory of safe_check.py
    os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
    
    #drop privileges
    if not options.runasroot:
        if options.verbose: print >>sys.stderr, "Dropping privileges (%s)" % options.runas
        drop_privileges(options.runas)
    else:
        if options.verbose: print >>sys.stderr, "Not dropping privileges !!!"      
        
    #run script
    try:
        if options.verbose: print >>sys.stderr, "Running script %s, arguments = %s" % (options.program, options.arguments)
        repy.run_file(options.resources, options.program, options.arguments, usercontext, usercode=code)
    except KeyboardInterrupt:
        return
    except SystemExit:
        pass
    except:
        import tracebackrepy
        tracebackrepy.handle_exception()
    try:
        import time
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        return
        
if __name__ == "__main__":
    main(parse_args())
