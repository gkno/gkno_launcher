
from __future__ import print_function

import distutils.version
import os
import re
import subprocess
import sys

##################################################################
# IMPORTANT: To add a new dependency, create a subclass
#   of GknoDependency with a command to get its version number
#   from the command line.
#   
#   To update an existing dependency (e.g. a new tool needs a 
#   newer version), then update the list at the bottom. NEVER
#   reduce the minimum version number, as you may break another
#   tool.
# 
#   gkno's 'admin mode' will use this list to check dependencies
#   at build time.
##################################################################

# Base class for all gkno dependencies
class GknoDependency(object):

  # Initialize defaults 
  def __init__(self, versionString):

    # Dependency's display name. Should be unique.
    self.name = ""

    # Version command to run ("foo --version"). 
    self.command = ""

    # Our minimum req'd version
    if versionString == "": versionString = "0.0.0"
    self.minimumVersion = distutils.version.LooseVersion(versionString)

    # Initialized to None, but should be set (if found), by subclass
    # (used for error reporting in case of incompatible version)
    self.currentVersion = None

    # Catch stdout & stderr from version commands. Different tools print
    # their version information to different destinations. Thus we catch 
    # both so that extractCurrentVersion() can access either.
    self.outdata = ""
    self.errdata = ""

    # For error reporting:
    self.isMissing = False
    self.isUnknownVersion = False

  # Checks the tool for existence & acceptable version number 
  # Returns True/False for success/failure.
  def check(self, out=sys.stdout, err=sys.stderr):
    
    # If command fails
    if not self.checkOutput(self.command):
      self.isMissing = True
      return False

    # Attempt to extract 'current version'
    if not self.extractCurrentVersion():
      self.isUnknownVersion = True
      return False

    # Compare version numbers & return compatibility
    return self.currentVersion >= self.minimumVersion

  # ** Override in subclasses if needed **
  #
  # Extract the version string from @command's output.
  #
  # On method entry, the command's STDOUT & STDERR output are stored in
  # self.outdata & self.errdata, respectively. Parse these values as 
  # needed to extract the version number and set it in self.currentVersion
  # 
  # Return True/False for parsing success or failure
  def extractCurrentVersion(self):
    assert False
    return False

  # --------------------------------------------
  # OS/shell utility helper methods
  # --------------------------------------------

  # Convenience method for running "system" calls with easier syntax (no array syntax in calling code)
  # Uses the output destinations (stdout/stderr) set by earlier external caller
  # Converts command exit status to True/False (under assumption of common practice that exit status of 0 is success)
  def runCommand(self, command):
    status = subprocess.call(command.split(), stdout=self.out, stderr=self.err)
    return status == 0

  # Convenience method for running "system" calls with easier syntax (no array syntax in calling code)
  # Sets our self.outdata & self.errdata with results from command
  # Returns True if command returned 0, else False
  def checkOutput(self, command):
    try:
      p = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      (self.outdata, self.errdata) = p.communicate()
      return p.returncode == 0
    except OSError:
      return False

  # --------------------------------------------
  # Parsing helper methods
  # --------------------------------------------
  def extractNormalVersionNumber(self, query):
    m = re.search(r'\d+(\.\d+)*', query)
    if m:
      self.currentVersion = distutils.version.LooseVersion(m.group(0))
      return True
    else: 
      return False

###############################################################

# ant
class Ant(GknoDependency):
  def __init__(self, versionString=""):
    super(Ant, self).__init__(versionString)
    self.name    = "ant"
    self.command = "ant -version"

  def extractCurrentVersion(self):
    return self.extractNormalVersionNumber(self.outdata)

# cmake
class Cmake(GknoDependency):
  def __init__(self, versionString=""):
    super(Cmake, self).__init__(versionString)
    self.name    = "cmake"
    self.command = "cmake --version"

  def extractCurrentVersion(self):
  
    # Try to extract normal version, like other tools, returning False on complete failure.
    # But we're not done yet, so don't simply return the result of extraction.
    if not self.extractNormalVersionNumber(self.outdata):
      return False
 
    # Cmake versions 2.6.x have a different version output format (2.6-patch x)
    # After the initial 'extractNormalVersionNumber', our currentVersion will be 2.6,
    # but the patch number is not yet set. So we need to tease it out.
    if ("patch" in self.outdata) and (self.currentVersion == distutils.version.LooseVersion("2.6")):
      m = re.search(r'patch\s+(\d+)', self.outdata)
      if m: 
        patchNumber = m.group(1)   
      else:
        return False 

      versionString = "2.6."+patchNumber
      self.currentVersion = distutils.version.LooseVersion(versionString)

    # We should be OK by here
    return True

# gcc
class Gcc(GknoDependency):
  def __init__(self, versionString=""):
    super(Gcc, self).__init__(versionString)
    self.name    = "gcc"
    self.command = "gcc --version"

  def extractCurrentVersion(self):
    return self.extractNormalVersionNumber(self.outdata)

# git
class Git(GknoDependency):
  def __init__(self, versionString=""):
    super(Git, self).__init__(versionString)
    self.name    = "git"
    self.command = "git --version"

  def extractCurrentVersion(self):
    return self.extractNormalVersionNumber(self.outdata)

# g++
class Gplusplus(GknoDependency):
  def __init__(self, versionString=""):
    super(Gplusplus, self).__init__(versionString)
    self.name    = "g++"
    self.command = "g++ --version"

  def extractCurrentVersion(self):
    return self.extractNormalVersionNumber(self.outdata)

# java
class Java(GknoDependency):
  def __init__(self, versionString=""):
    super(Java, self).__init__(versionString)
    self.name    = "java"
    self.command = "java -version"

  def extractCurrentVersion(self):
    return self.extractNormalVersionNumber(self.errdata)  # STDERR

# javac
class Javac(GknoDependency):
  def __init__(self, versionString=""):
    super(Javac, self).__init__(versionString)
    self.name    = "javac"
    self.command = "javac -version"

  def extractCurrentVersion(self):
    return self.extractNormalVersionNumber(self.errdata)  # STDERR

# make
class Make(GknoDependency):
  def __init__(self, versionString=""):
    super(Make, self).__init__(versionString)
    self.name    = "make"
    self.command = "make --version"

  def extractCurrentVersion(self):
    return self.extractNormalVersionNumber(self.outdata)

# python
class Python(GknoDependency):
  def __init__(self, versionString=""):
    super(Python, self).__init__(versionString)
    self.name    = "python"
    self.command = "python --version"

  def extractCurrentVersion(self):
    return self.extractNormalVersionNumber(self.errdata)  # STDERR

# scala
class Scala(GknoDependency):
  def __init__(self, versionString=""):
    super(Scala, self).__init__(versionString)
    self.name    = "scala"
    self.command = "scala -version"

  def extractCurrentVersion(self):
    return self.extractNormalVersionNumber(self.outdata)

# scalac
class Scalac(GknoDependency):
  def __init__(self, versionString=""):
    super(Scalac, self).__init__(versionString)
    self.name    = "scalac"
    self.command = "scalac -version"

  def extractCurrentVersion(self):
    return self.extractNormalVersionNumber(self.errdata)  # STDERR

##############################################################
# Add any new dependencies to the list below.
#
# Place minimum version number in the constructor.
##############################################################

List = [ 
        Ant("1.7.1"),
        Cmake("2.6.4"),
        Gcc("4.0"),
        Git("1.7"),
        Gplusplus("4.0"),
        Java("1.6"),
        Javac("1.6"),
        Make("3.80"),
        Python("2.6")
        #Scala("2.7.7"),
        #Scalac("2.7.7")
       ]

