#!/usr/bin/python
# -*- coding: utf-8 -*-

""" 
A munin plugin that prints age in seconds of last apt-get update
"""
import sys
import argparse
from time import time, strftime
import os 
from types import StringTypes, TupleType, DictType, ListType, BooleanType
from subprocess import PIPE, Popen, CalledProcessError

def getEnv(name, default=None, cast=None):
    """
        function to get Environmentvars, cast them and setting defaults if they aren't
        getEnv('USER', default='nouser') # 'HomerS'
        getEnv('WINDOWID', cast=int) # 44040201
    """
    try:
        var = os.environ[name]
        if cast is not None:
            var = cast(var)
    except KeyError:
        # environment does not have this var
        var = default
    except:
        # now probably the cast went wrong
        print >> sys.stderr, "for environment variable %r, %r is no valid value"%(name, var)
        var = default
    return var


def Property(func):
    return property(**func())

def ageOfAptLists():
    """
    (if it exists (it is deleted after apt-get clean))
    /var/lib/apt/lists/*Packages are interesting too, 
    interesting files is /var/cache/apt/pkgcache.bin
    but it is deleted with a apt-get clean.
    So check whether it exists, if not take date from *Packages file.
    """
    lastRun = None
    try:
        lastRun = os.stat("/var/cache/apt/pkgcache.bin").st_mtime
    except:
        pass
    if not lastRun:
        # get latest modify time of a package file
        timeL = []
        packageListsDir = "/var/lib/apt/lists"
        files=os.listdir(packageListsDir)
        packageFileL = [ file for file in files if file.endswith('Packages')]
        for packageFile in packageFileL:
            timeL.append(os.stat(os.path.join(packageListsDir, packageFile)).st_mtime)
        lastRun = max(timeL)

    age = time() - lastRun 
    return age

class Munin(object):

    def __init__(self, commandLineArgs=None):
        self.commandLineArgs = commandLineArgs
        self.argParser = self._argParser()
        self.executionMatrix = { 
            'config': self.config,
            'run'   : self.run,
            'autoconf' : self.autoconf,
        }

    def execute(self):
        self.args = self.argParser.parse_args(self.commandLineArgs)
        self.executionMatrix[self.args.command]()

    def run(self):
        print "uptime.value %.1f" % (ageOfAptLists()/3600.)

    def config(self):
        print """
graph_title Age of last apt-get update or repository package file
graph_args --base 1000 -l 0 
graph_scale no
graph_vlabel age of package-lists in hours
graph_category debian
uptime.label age
uptime.draw AREA
uptime.warning -1:74
uptime.critical -24:170
        """

    def autoconf(self):
        """ checks wheter it is run on a debian machine"""
        try:
            p = Popen(["/usr/bin/lsb_release", "-is"], stderr=PIPE, stdout=PIPE)
            out,err = p.communicate()
        except:
            print 'no'
        # use this regex, if this module works with other linux distributions like ubuntu or mint 
        regex = re.compile(r"Debian")
        m = re.match(regex, out)
        if m:
            print 'yes'
        else:
            print 'no'

    def _argParser(self):
        parser = argparse.ArgumentParser(description="Show some statistics "\
                            "about debian packages installed on system by archive",
                           ) 
        parser.set_defaults(command='run', debug=True, nocache=True)

        parser.add_argument('--nocache', '-n', default=False, action='store_true',
                            help='do not use a cache file')
        helpCommand = """
            config ..... writes munin config
            run ........ munin run (writes values)
            autoconf ... writes 'yes'
        """
        parser.add_argument('command', nargs='?', 
                            choices=['config', 'run', 'autoconf', 'drun'],
                            help='mode munin wants to use. "run" is default' + helpCommand)
        return parser

if __name__=='__main__':
    muninPlugin = Munin()
    muninPlugin.execute()
    # import IPython; IPython.embed()
