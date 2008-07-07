#!/usr/bin/env python

import sys, os, traceback
from optparse import OptionParser

def die(msg):
  print msg
  raise SystemExit(1)

option_parser = OptionParser()
option_parser.add_option('--install-root',default='/usr/local/graphite/',
  help="The base directory of the graphite installation, default: /usr/local/graphite/")
option_parser.add_option('--extjs',default='',
  help="Path to an ExtJS (http://www.extjs.com) installation, specifically the directory containing \"ext-all.js\"")

(options,args) = option_parser.parse_args()

install_root = options.install_root
if not install_root.endswith('/'):
  install_root += '/'


# Test for ExtJS
if not options.extjs:
  print "Please provide the full path to your ExtJS installation (the directory that contains \"ext-all.js\""
  print "If you do not have ExtJS installed, go to http://www.extjs.com and download the 2.x SDK"
  print "\nFor example: ./install.py --extjs=/usr/local/extjs\n"
  raise SystemExit(1)

ext_all = os.path.join(options.extjs,'ext-all.js')
if not os.path.isfile(ext_all):
  die("The path \"%s\" does not appear to contain the ExtJS SDK. The path you give should be the directory containing ext-all.js" % options.extjs)

# Simple python version test
major,minor = sys.version_info[:2]
py_version = sys.version.split()[0]
if major < 2 or (major == 2 and minor < 4):
  die("You are using python %s, but version 2.4 or greater is required" % py_version)
if major > 2:
  die("Python 3.x is not supported yet")

# Test for pycairo
try:
  import cairo
except:
  die("Unable to import the 'cairo' module, do you have pycairo installed for python %s?" % py_version)

# Test that pycairo has the PNG backend
try:
  surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 10, 10)
  del surface
except:
  die("Failed to create an ImageSurface with cairo, you probably need to recompile cairo with PNG support")

# Test for django
try:
  import django
except:
  die("Unable to import the 'django' module, do you have Django installed for python %s?" % py_version)

# Verify django version
if django.VERSION[0] == 0 and django.VERSION[1] < 95:
  version = '.'.join([str(v) for v in django.VERSION if v is not None])
  die("You have django version %s installed, but version 0.95 or greater is required" % version)

# Test for mod_python
try:
  import mod_python
except:
  die("Unable to import the 'mod_python' module, do you have mod_python installed for python %s?" % py_version)

# Test for pyparsing
try:
  import pyparsing
except:
  die("Unable to import the 'pyparsing' module, do you have pyparsing installed for python %s?" % py_version)

# Test for python-memcached
try:
  import memcache
except:
  print "[WARNING]"
  print "Unable to import the 'memcache' module, do you have python-memcached installed for python %s?" % py_version
  print "This feature is not required but greatly improves performance.\n"

# Test for sqlite
try:
  try:
    import sqlite3 #python 2.5+
  except:
    from pysqlite2 import dbapi2 #python 2.4
except:
  print "[WARNING]"
  print "Unable to import the sqlite module, do you have python-sqlite2 installed for python %s?" % py_version
  print "If you plan on using another database backend that Django supports (such as mysql or postgres)"
  print "then don't worry about this. However if you do not want to setup the database yourself, you will"
  print "need to install sqlite2 and python-sqlite2.\n"

# Test for python-ldap
try:
  import ldap
except:
  print "[wARNING]"
  print "Unable to import the 'ldap' module, do you have python-ldap installed for python %s?" % py_version
  print "Without python-ldap, you will not be able to use LDAP authentication in the graphite webapp.\n"

# Prompt before installing
print "Required dependencies are met, graphite will be installed into:"
print "  %s" % install_root
print "\nAnd will symlink your ExtJS installation from:"
print "  %s" % options.extjs
while True:
  answer = raw_input("\nOk to continue [y/n]?").lower().strip()
  if answer == 'y':
    break
  if answer == 'n':
    raise SystemExit(0)

# Verify permissions
if not os.path.isdir(install_root):
  try:
    os.makedirs(install_root)
  except OSError, e:
    print "Failed to created install directory \"%s\": %s" % (install_root,e.strerror)
    raise SystemExit(1)
else:
  if not os.access(install_root,os.R_OK|os.W_OK|os.X_OK):
    print "You do not have permission to install into \"%s\", you should use" % install_root
    print "a --install-root that you own, or run install.py as root."
    raise SystemExit(1)

# Perform the installation
print 'Installing graphite library package'
dir = os.getcwd()
os.chdir('lib/')
os.system("%s setup.py install" % sys.executable)
os.chdir(dir)
try:
  import graphite
except ImportError:
  die("Installation of graphite library package failed")

print 'Copying files...'
os.system("cp -rvf webapp/ %s" % install_root)
os.system("cp -rvf storage/ %s" % install_root)
os.system("cp -rvf carbon/ %s" % install_root)

print '\nCreating a symlink to %s\n' % options.extjs
extjs_dir = os.path.join(install_root,'webapp','content','js','extJS')
os.system("ln -s %s %s" % (options.extjs, extjs_dir))

#Setup local_settings.py
try:
  local_settings_py = os.path.join(install_root, 'webapp', 'web', 'local_settings.py')
  local_settings_example = os.path.join(install_root, 'webapp', 'web', 'local_settings.py.example')
  if not os.path.isfile(local_settings_py):
    print "Creating an example local_settings.py"
    os.system("mv %s %s" % (local_settings_example, local_settings_py))
  else:
    print "local_settings.py exists, leaving untouched"
    os.system("rm -f %s" % local_settings_example)
except:
  print "Error while inspecting local_settings.py (please report this as a bug!)"
  traceback.print_exc()
  print

#Install the carbon init script
inits_installed = False
for init_dir in ('/etc/init.d/','/etc/rc.d/init.d/'):
  if os.path.isdir(init_dir):
    print "Installing init scripts into %s" % init_dir
    inits_installed = True
    os.system("cp -f carbon/init-script.sh %s/carbon-agent.sh" % init_dir)
    break

if not inits_installed:
  print "[Warning] Could not find a suitable system init-script directory, please install \"carbon/init-script.sh\" manually."

print "The install process is complete, if this is a first-time installation"
print "you should run the following command to complete the remaining setup steps:\n"
print "%s post-install.py --install-root=%s" % (sys.executable, install_root)
