import hashlib, os

def removeControlChars(s):
    #allow TAB=9, LF=10, CR=13
    controlChars = "".join(map(chr, range(0,9)+range(11,13)+range(14,32)))
    return s.translate(None, controlChars)

def escape(s):
    return repr(unicode(s).encode("utf-8"))

def identifier(s, allowed="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_.", subst="_"):
    ret=""
    for ch in s:
        if ch in allowed:
            ret += ch
        elif subst:
            ret += subst
    return ret

def randomPassword():
    return hashlib.md5(os.urandom(8)).hexdigest()
