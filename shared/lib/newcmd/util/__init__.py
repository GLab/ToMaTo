from cmd import CommandError, run, spawn, spawnDaemon
from daemon import Daemon
from locks import LockMatrix
from misc import removeControlChars, escape, identifier, randomPassword