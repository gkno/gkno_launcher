
import os
import multiprocessing
import subprocess
import sys

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

  # Define the build (e.g. compile) steps needed for the tool. 
  # Return exit status of 0 if successful, non-zero if failed.
  # * If there is no build step needed (e.g. the tool is script-
  #   based and needs no compiling), simply return zero.
  #
  # When this method is entered, the 'current working directory' 
  # is the tool's root directory.
  def build(self):
    assert False
    return 1

  # Define the update (e.g. recompile) steps needed for the tool. 
  # Return exit status of 0 if successful, non-zero if failed.
  # * If there is no update step needed, simply return zero.
  #
  # In many cases, the build & update operations share steps.
  # Feel free to have these methods call each other in any
  # manner that works for your tool's own build system.
  #
  # When this method is entered, the 'current working directory' 
  # is the tool's root directory.
  def update(self):
    assert False
    return 1

  # --------------------------------------------
  # OS/shell utility helper methods
  # --------------------------------------------

  # Run external command, suppressing output by default
  def runCommand(self, command, quiet=False):   # FIXME: <-- change quiet=True
    if quiet:
      return subprocess.call(command.split(), stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))
    else:
      return subprocess.call(command.split(), stdout=sys.stdout, stderr=sys.stderr)

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
  def build(self):
    buildDir = os.getcwd() + "/build/"
    self.ensureMakeDir(buildDir)
    os.chdir(buildDir)   
    self.cmake("..")
    self.make()
    return 0

  # Same as build()
  def update(self):
    return self.build()

# freebayes
class Freebayes(GknoTool):
  def __init__(self):
    super(Freebayes, self).__init__()
    self.name       = "freebayes"
    self.installDir = "freebayes"

  # $ make clean 
  # $ make -j N   
  def build(self):
    self.makeClean()
    return self.update()

  # $ make -j N   
  def update(self):
    self.make()
    return 0

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
  def build(self):
    self.antClean()
    return self.update()

  # $ ant -Dcompile.scala.by.default=false
  def update(self):
    self.ant("-Dcompile.scala.by.default=false")
    return 0

# mosaik
class Mosaik(GknoTool):
  def __init__(self):
    super(Mosaik, self).__init__()
    self.name       = "MOSAIK"
    self.installDir = "MOSAIK"

  # $ cd src
  # # make clean
  # $ make -j N
  def build(self):
    os.chdir("src") 
    self.makeClean()                   
    self.make()
    return 0 
  
  # $ cd src
  # $ make -j N
  def update(self):
    os.chdir("src")                    
    self.make()
    return 0

# ogap
class Ogap(GknoTool):
  def __init__(self):
    super(Ogap, self).__init__()
    self.name       = "ogap"
    self.installDir = "ogap"

  # $ make clean
  # $ make -j N  
  def build(self):     
    self.makeClean()
    return self.update()

  # $ make -j N
  def update(self):
    self.make()
    return 0

# picard 
class Picard(GknoTool):
  def __init__(self):
    super(Picard, self).__init__()
    self.name       = "picard"
    self.installDir = "picard"

  # $ ant clean
  # $ ant sam-jar
  # $ ant -lib lib/ant package-commands
  def build(self):
    self.antClean()  
    return self.update()

  # $ ant sam-jar
  # $ ant -lib lib/ant package-commands
  def update(self):
    self.ant("sam-jar")
    self.ant("-lib lib/ant package-commands")
    return 0

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
  def build(self):
    buildDir = os.getcwd() + "/build/"
    self.ensureMakeDir(buildDir)
    os.chdir(buildDir)  
    self.cmake("..")
    self.make()          
    return 0

  # Same as build()
  def update(self):
    return self.build()

# samtools
class SamTools(GknoTool):
  def __init__(self):
    super(SamTools, self).__init__()
    self.name       = "samtools"
    self.installDir = "samtools"
 
  # $ make clean
  # $ make -j N
  def build(self) :
    self.makeClean()
    self.make()
    return 0

  # $ make -j N
  def update(self) :
    self.make()
    return 0

##############################################################
# Add any new built-in gkno tools to the list below.
##############################################################

List = [ 
        BamTools(),
        Freebayes(),
        Gatk(),
        Mosaik(),
        Ogap(),
        Picard(),
        Premo(),
        SamTools()
       ]

