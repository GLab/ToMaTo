#!/usr/bin/env python
import sys, os, tempfile, shutil, pwd, grp
import repy, namespace, exception_hierarchy, tracebackrepy, virtual_namespace

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
    (uname, gname) = options.runas.split(":")
    options.runas_uid = pwd.getpwnam(uname).pw_uid
    options.runas_gid = grp.getgrnam(gname).gr_gid
    return options

class ExceptionValue(namespace.ValueProcessor):
    def check(self, val):
        if not isinstance(val, Exception):
            raise RepyArgumentError("Invalid type %s" % type(val))
    def copy(self, val):
        return val
    
def build_context(quiet):
    import traceback, emultap, emulstruct, time
    starttime = time.time()
    for call in set(namespace.USERCONTEXT_WRAPPER_INFO.keys())-set(['exitall', 'createlock', 'getruntime', 'randombytes', 'createthread', 'sleep', 'log', 'getthreadname', 'createvirtualnamespace', 'getresources']):
        del namespace.USERCONTEXT_WRAPPER_INFO[call]
    namespace.USERCONTEXT_WRAPPER_INFO.update({
        'print_exc': {
            'func': traceback.print_exc,
            'args': [ExceptionValue()],
            'return': None,
        },
        'getruntime': {
            'func' : lambda :time.time() - starttime,
            'args' : [],
            'return' : namespace.Float()
        },
        'time': {
            'func' : time.time,
            'args' : [],
            'return' : namespace.Float()
        },
    })
    namespace.USERCONTEXT_WRAPPER_INFO.update(emultap.METHODS)
    namespace.USERCONTEXT_WRAPPER_INFO.update(emulstruct.METHODS)
    if quiet:
        namespace.USERCONTEXT_WRAPPER_INFO.update({
            'log': {
                'func': lambda s: None,
                'args': [namespace.NonCopiedVarArgs()],
                'return': None,
            },
            'print_exc': {
                'func': lambda s: None,
                'args': [],
                'return': None,
            },
        })
    
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
            sys.exit(1)
        raise
    
def drop_privileges(uid, gid):
    if os.getuid() != 0:
        return #nothing to drop
    os.setgid(gid)
    os.setuid(uid)
    
def main(options):
    #prepare network interfaces
    if options.verbose: print >>sys.stderr, "Preparing networking interfaces %s" % options.interface
    prepare_interfaces(options.interface)

    #move file to tmp dir and chown it to executing user
    if options.verbose: print >>sys.stderr, "Reading program from %s" % options.program
    with open(options.program) as fp:
      usercode = fp.read()
    
    #build usercontext
    if options.verbose: print >>sys.stderr, "Building script context"
    import time, nonportable
    nonportable.getruntime = time.time #change getruntime to time.time to gain preformance
    build_context(options.quiet)
    
    #change directory to directory of safe_check.py
    os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
    
    #drop privileges
    if not options.runasroot:
        if options.verbose: print >>sys.stderr, "Dropping privileges (%s)" % options.runas
        drop_privileges(options.runas_uid, options.runas_gid)
    else:
        if options.verbose: print >>sys.stderr, "Not dropping privileges !!!"      
        
    #run script
    try:
        if options.verbose: print >>sys.stderr, "Checking script %s" % options.program
        namespace = virtual_namespace.VirtualNamespace(usercode, options.program)
        usercode = None # allow the (potentially large) code string to be garbage collected
        if options.verbose: print >>sys.stderr, "Initializing resource restrictions %s" % options.resources
        repy.initialize_nanny(options.resources)
        if options.verbose: print >>sys.stderr, "Running script %s, arguments = %s" % (options.program, options.arguments)
        context = repy.get_safe_context(options.arguments)
        repy.execute_namespace_until_completion(namespace, context)
    except KeyboardInterrupt:
        return
    except SystemExit:
        pass
    except:
        tracebackrepy.handle_exception()
    try:
        import time
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        return
        
if __name__ == "__main__":
    main(parse_args())
