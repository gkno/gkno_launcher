
from __future__ import print_function

import json
import multiprocessing
import os
import subprocess
import sys
import tarfile
import urllib

##################################################################
# IMPORTANT: To add a new built-in tool, create a subclass
#   of GknoTool with the proper git info as well as build/update
#   steps. After that, add an instance of your new class
#   to the 'toolList' at the bottom of this script.
#   
#   gkno's 'admin mode' will use this list to know which 
#   tools to include in its build/update steps.
##################################################################

# Base class for all built-in gkno tools
class GknoTool(object):

  # Initialize defaults 
  def __init__(self):

    # Tool's display name. Should be unique across all built-in's
    self.name = ""

    # Tool's root install directory (probably same as self.name)
    # This should be the directory used when adding the tool as a submodule
    #   So 'git submodule add ... tools/X' means this installDir = "X"
    self.installDir = ""

    # Default output destinations
    self.out = sys.stdout
    self.err = sys.stderr

    # Default environment variables
    self.environ = os.environ

  # Define the build (e.g. compile) steps needed for the tool. 
  # Returns True/False for success/failure.
  # * If there is no build step needed (e.g. the tool is script-
  #   based and needs no compiling), simply return True.
  #
  # When this method is entered, the 'current working directory' 
  # is the tool's root directory.
  def doBuild(self):
    assert False
    return False

  # Define the update (e.g. recompile) steps needed for the tool. 
  # Returns True/False for success/failure.
  # * If there is no update step needed, simply return True.
  #
  # In many cases, the build & update operations share steps.
  # Feel free to have these methods call each other in any
  # manner that works for your tool's own build system.
  #
  # When this method is entered, the 'current working directory' 
  # is the tool's root directory.
  def doUpdate(self):
    assert False
    return False

  # External entry point for build step.
  # Sets output destination & calls subclass implementation
  def build(self, out=sys.stdout, err=sys.stderr):
    self.out = out
    self.err = err
    return self.doBuild()

  # External entry point for update step.
  # Sets output destination & calls subclass implementation
  def update(self, out=sys.stdout, err=sys.stderr):
    self.out = out
    self.err = err
    return self.doUpdate()

  # --------------------------------------------
  # OS/shell utility helper methods
  # --------------------------------------------

  # Convenience method for running "system" calls with easier syntax (no array syntax in calling code)
  # Uses the output destinations (stdout/stderr) set by earlier external caller
  # Converts command exit status to True/False (under assumption of common practice that exit status of 0 is success)
  def runCommand(self, command):
    p = subprocess.Popen(command.split(), env=self.environ, stdout=self.out, stderr=self.err)
    p.wait()
    status = p.returncode
    return status == 0

  # Similar to our runCommand() method, except the command is executed through the shell
  # Uses the output destinations (stdout/stderr) set by earlier external caller
  # Converts command exit status to True/False (under assumption of common practice that exit status of 0 is success)
  def runShellCommand(self, command):
     p = subprocess.Popen(command.split(), env=self.environ, stdout=self.out, stderr=self.err, shell=True)
     p.wait()
     status = p.returncode
     return status == 0

  # Creates directory if it doesn't already exist
  def ensureMakeDir(self, directory, mode=0777):
    if not os.path.exists(directory):
      os.makedirs(directory, mode)

  # --------------------------------------------
  # Build-system helper methods
  # --------------------------------------------

  def ant(self, optionString=""):
    return self.runCommand("ant " + optionString)

  def antClean(self):
    return self.runCommand("ant clean")

  def cmake(self, optionString=""):
    return self.runCommand("cmake " + optionString)

  def make(self, optionString=""):
    return self.runCommand("make -j" + str(multiprocessing.cpu_count()) + " " + optionString)

  def makeClean(self):
    return self.runCommand("make clean")

###############################################################

# bamtools
class BamTools(GknoTool):
  def __init__(self):
    super(BamTools, self).__init__()
    self.name       = "bamtools"
    self.installDir = "bamtools"

  # $ mkdir build
  # $ cd build  
  # $ cmake .. 
  # $ make -j N 
  def doBuild(self):
    buildDir = os.getcwd() + "/build/"
    self.ensureMakeDir(buildDir)
    os.chdir(buildDir)
    if not self.cmake(".."):
      return False
    return self.make()

  # Same as doBuild()
  def doUpdate(self):
    return self.doBuild()

# bamUtil
class BamUtil(GknoTool):
  def __init__(self):
    super(BamUtil, self).__init__()
    self.name       = "bamUtil"
    self.installDir = "bamUtil"

  # $ make -j N   
  def doBuild(self):
#    if not self.makeClean(): 
#      return False 
    return self.make()

  # $ make -j N   
  def doUpdate(self):
    return self.make()

# NCBI BLAST
class Blast(GknoTool):
  def __init__(self):
    super(Blast, self).__init__()
    self.name       = "blast"
    self.installDir = "blast"

  def doBuild(self):

    # Read contents of 'targets.json'.
    blastSettings = {}
    targetsFile = open("targets.json")
    try:
      blastSettings = json.load(targetsFile)
    except:
      return False

    # Determine proper URL depending on environment.
    key = 'linux_32'
    if sys.platform == 'darwin':
      key = 'macosx'
    else:
      if sys.maxsize > 2**32:
        key='linux_64'
    url = blastSettings[key]

    # Download tarball, extract contents, then erase tarball.
    try:
      filename, headers = urllib.urlretrieve(url) 
      tar = tarfile.open(filename)
      tar.extractall()
      tar.close()
      os.remove(filename)
    except:
      return False

    # If we get here, return success.
    return True
   
  def doUpdate(self):

    # If nothing built yet, force build
    filesList = os.listdir( os.getcwd() )
    blastFiles = []
    for f in filesList:
      if f.startswith('.') or f == 'targets.json':
        continue
      else:
        blastFiles.append(f)
    if len(blastFiles) == 0 :
      return self.doBuild()

    # TODO: determine if update needed for existing install
    return True

# FastQValidator
class FastQValidator(GknoTool):
  def __init__(self):
    super(FastQValidator, self).__init__()
    self.name       = "fastQValidator"
    self.installDir = "fastQValidator"

  # $ make -j N   
  def doBuild(self):
#    if not self.makeClean(): 
#      return False 
    return self.make()

  # $ make -j N   
  def doUpdate(self):
    return self.make()

# freebayes
class Freebayes(GknoTool):
  def __init__(self):
    super(Freebayes, self).__init__()
    self.name       = "freebayes"
    self.installDir = "freebayes"

  # $ make -j N   
  def doBuild(self):
#    if not self.makeClean(): 
#      return False 
    return self.make()

  # $ make -j N   
  def doUpdate(self):
    if not self.makeClean(): 
      return False 
    return self.make()

# gatk
class Gatk(GknoTool):
  def __init__(self):
    super(Gatk, self).__init__()
    self.name       = "gatk"
    self.installDir = "gatk"

  # N.B. - We're just going to require scala up front. Letting GATK compile 
  # scala failed on at least one machine (StackOverflowException). Providing 
  # it beforehand skirts this issue. Once we can trust GATK's build to succeed, 
  # we may remove this prerequisite and just let GATK build normally.

  # $ ant clean
  # $ ant -Dcompile.scala.by.default=false
  def doBuild(self):
    if not self.antClean():
      return False
    return self.doUpdate()

  # $ ant -Dcompile.scala.by.default=false
  def doUpdate(self):
    return self.ant()

# Jellyfish
class Jellyfish(GknoTool):
  def __init__(self):
    super(Jellyfish, self).__init__()
    self.name       = "jellyfish"
    self.installDir = "Jellyfish"

  def doBuild(self):

    # Install Yaggo.
    # Clones the repo, and installs the ruby libs & binary needed by Jellyfish build.
    if not self.runCommand("git clone https://github.com/gmarcais/yaggo.git") : return False
    os.chdir("yaggo")
    if not self.runCommand("ruby setup.rb config --prefix=. --siterubyver=./lib") : return False
    if not self.runCommand("ruby setup.rb setup") : return False
    if not self.runCommand("ruby setup.rb install --prefix=.") : return False
    if not self.runCommand("chmod 755 bin/yaggo") : return False
    self.environ["RUBYLIB"] = os.getcwd()+"/lib"
    os.chdir("..")

    # Install Jellyfish - using autotools & make.
    self.environ["YAGGO"] = os.getcwd()+"/yaggo/bin/yaggo"
    if not self.runCommand("autoreconf -i") : return False
    if not self.runCommand("./configure --prefix="+os.getcwd()) : return False
    if not self.make() : return False
    return True

  # TODO: implement me
  def doUpdate(self):
    os.chdir("yaggo")
    self.environ["RUBYLIB"] = os.getcwd()+"/lib"
    os.chdir("..")

    self.environ["YAGGO"] = os.getcwd()+"/yaggo/bin/yaggo"
    if not self.runCommand("autoreconf -i") : return False
    if not self.runCommand("./configure --prefix="+os.getcwd()) : return False
    if not self.make() : return False
    return True
    #return self.make()

# libStatGen
class LibStatGen(GknoTool):
  def __init__(self):
    super(LibStatGen, self).__init__()
    self.name       = "libStatGen"
    self.installDir = "libStatGen"

  # $ make -j N  
  def doBuild(self):    
#    if not self.makeClean():
#      return False
    return self.doUpdate()

  # $ make -j N
  def doUpdate(self):
    return self.make()

# mosaik
class Mosaik(GknoTool):
  def __init__(self):
    super(Mosaik, self).__init__()
    self.name       = "mosaik"
    self.installDir = "MOSAIK"
    self.getPlatformType()

  # $ cd src
  # $ make clean
  # $ make -j N
  def doBuild(self):
    os.chdir("src")
    if not self.makeClean():
      return False
    return self.make()
  
  # $ cd src
  # $ make -j N
  def doUpdate(self):
    os.chdir("src") 
    if not self.makeClean():
      return False
    return self.make()

  # Mosaik has a platform-specific environment 
  # variable we need to set.
  def getPlatformType(self):
    pl='linux'
    if sys.platform == 'darwin':
      pl='macosx'
      if sys.maxsize > 2**32:
        pl='macosx64'
    self.environ["BLD_PLATFORM"] = pl

# Mutatrix
class Mutatrix(GknoTool):
  def __init__(self):
    super(Mutatrix, self).__init__()
    self.name       = "mutatrix"
    self.installDir = "mutatrix"

  # $ make -j N  
  def doBuild(self):
#    if not self.makeClean():
#      return False
    return self.doUpdate()

  # $ make -j N
  def doUpdate(self):
    return self.make()

# ogap
class Ogap(GknoTool):
  def __init__(self):
    super(Ogap, self).__init__()
    self.name       = "ogap"
    self.installDir = "ogap"

  # $ make -j N  
  def doBuild(self):    
#    if not self.makeClean():
#      return False
    return self.doUpdate()

  # $ make -j N
  def doUpdate(self):
    return self.make()

# picard 
class Picard(GknoTool):
  def __init__(self):
    super(Picard, self).__init__()
    self.name       = "picard"
    self.installDir = "picard"

  # $ ant clean
  # $ ant sam-jar
  # $ ant -lib lib/ant package-commands
  def doBuild(self):
    if not self.antClean():
      return False
    return self.doUpdate()

  # $ ant sam-jar
  # $ ant -lib lib/ant package-commands
  def doUpdate(self):
    if not self.ant("sam-jar"):
      return False
    return self.ant("-lib lib/ant package-commands")

# premo
class Premo(GknoTool):
  def __init__(self):
    super(Premo, self).__init__()
    self.name       = "premo"
    self.installDir = "premo"

  # $ mkdir build
  # $ cd build 
  # $ cmake .. 
  # $ make -j N
  def doBuild(self):
    buildDir = os.getcwd() + "/build/"
    self.ensureMakeDir(buildDir)
    os.chdir(buildDir)
    if not self.cmake(".."):
      return False
    return self.make()

  # Same as doBuild()
  def doUpdate(self):
    return self.doBuild()

# Rufus
class Rufus(GknoTool):
  def __init__(self):
    super(Rufus, self).__init__()
    self.name       = "Rufus"
    self.installDir = "Rufus"

  # $ make clean
  # $ make -j N
  def doBuild(self):
    if not self.makeClean():
      return False
    return self.make()

  # $ make -j N
  def doUpdate(self):
    return self.make()

# samtools
class SamTools(GknoTool):
  def __init__(self):
    super(SamTools, self).__init__()
    self.name       = "samtools"
    self.installDir = "samtools"
 
  # $ make clean
  # $ make -j N
  def doBuild(self):
    if not self.makeClean():
      return False
    return self.make()

  # $ make -j N
  def doUpdate(self):
    return self.make()

# Scissors,
class Scissors(GknoTool):
  def __init__(self):
    super(Scissors, self).__init__()
    self.name       = "scissors"
    self.installDir = "scissors"

  # $ cd src
  # $ make clean
  # $ make -j N
  def doBuild(self):
    os.chdir("src")
    if not self.makeClean():
      return False
    return self.make()
  
  # $ cd src
  # $ make -j N
  def doUpdate(self):
    os.chdir("src") 
    if not self.makeClean():
      return False
    return self.make()

# Seqan (only building MASON for now)
class Seqan(GknoTool):
  def __init__(self):
    super(Seqan, self).__init__()
    self.name       = "seqan"
    self.installDir = "seqan"

  # mkdir build/Release
  # cd build/Release
  # cmake ../.. 
  # make mason
  def doBuild(self):
    self.ensureMakeDir(os.getcwd() + "/build/Release")
    os.chdir("build/Release")
    if not self.cmake("../.. -DCMAKE_BUILD_TYPE=Release"): return False
    if not self.make("mason"): return False
    os.chdir("../..")
    return True
  
  # TODO: check this
  def doUpdate(self):
    return self.doBuild()

# tabix (& bgzip)
class Tabix(GknoTool):
  def __init__(self):
    super(Tabix, self).__init__()
    self.name       = "tabix"
    self.installDir = "tabix"
 
  # $ make clean
  # $ make -j N
  def doBuild(self):
    if not self.makeClean():
      return False
    return self.make()

  # $ make -j N
  def doUpdate(self):
    return self.make()

# Tangram
class Tangram(GknoTool):
  def __init__(self):
    super(Tangram, self).__init__()
    self.name       = "tangram"
    self.installDir = "Tangram/src"

  # $ make -j N  
  def doBuild(self):    
#    if not self.makeClean():
#      return False
    return self.doUpdate()

  # $ make -j N
  def doUpdate(self):
    return self.make()

# vcflib
class VcfLib(GknoTool):
  def __init__(self):
    super(VcfLib, self).__init__()
    self.name       = "vcflib"
    self.installDir = "vcflib"

  # $ make -j N  
  def doBuild(self):    
#    if not self.makeClean():
#      return False
    return self.doUpdate()

  # $ make -j N
  def doUpdate(self):
    return self.make()

##############################################################
# Add any new built-in gkno tools to the list below.

# These tools are listed in alphabetical order with the
# exception of bamUtil.  This requires that libStatGen is
# already compiled and so follows it in the list.  Please
# ensure that this order is not modified.
##############################################################

List = [ 
        BamTools(),
        Blast(),
        Freebayes(),
        Gatk(),
        Jellyfish(),
        LibStatGen(), BamUtil(), FastQValidator(), # <-- Keep this order
        Mosaik(),
        Mutatrix(),
        Ogap(),
        Picard(),
        Premo(),
        Rufus(),
        SamTools(), 
        Scissors(),
        Seqan(),       
        Tabix(),
        Tangram(),
        VcfLib()
       ]

