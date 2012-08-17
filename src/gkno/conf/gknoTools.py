
###############################################################
# IMPORTANT: To add a new built-in tool, create a subclass
#   of GknoTool with the proper git info as well as build
#   steps. After that, add an instance of your new class
#   to the 'toolList' at the bottom of this script.
#   
#   gkno's 'admin mode' will use this list to know which 
#   tools to include in its build/update steps.
###############################################################

# Base class for all built-in gkno tools
class GknoTool:

  # Initialize defaults (e.g. "master" branch from all git repos
  # unless otherwise specified.)
  def __init__(self):
    self.name       = ""
    self.gitBranch  = "master"
    self.gitUrl     = ""
    self.installDir = ""

  # Define the build steps needed for the tool.
  # Return exit status of zero if successful, non-zero if failed.
  #
  # When building, you can assume that the current directory
  # is the root directory for your tool's repo.
  # FIXME: ^^^^^^^^^^^^^^^^^
  #        IS THIS CORRECT??
  # 
  # If there is no build step needed (e.g. the tool is script-
  # based and needs no compiling), you may simply return zero.
  def build(self):

    # FIXME: print error, tool did not define build step
    return 1

###############################################################

# bamtools
class BamTools(GknoTool):
  
  def __init__(self):
    self.name       = "bamtools"
    self.gitUrl     = "git://github.com/gkno/bamtools.git"
    self.installDir = "bamtools"

  def build(self):
    #"mkdir build",
    #"cd build",
    #"cmake ..",
    #"make"
    return 0

# freebayes
class Freebayes(GknoTool):
  
  def __init__(self):
    self.name       = "freebayes"
    self.gitUrl     = "git://github.com/gkno/freebayes.git"
    self.installDir = "freebayes"

  def build(self):
    return 0

# gatk
class Gatk(GknoTool):

  def __init__(self):
    self.name       = "gatk"
    self.gitUrl     = "git://github.com/broadgsa/gatk.git"
    self.installDir = "gatk"

  def build(self):
    return 0

# mosaik
class Mosaik(GknoTool):

  def __init__(self):
    self.name       = "MOSAIK"
    self.gitUrl     = "git://github.com/gkno/MOSAIK.git"
    self.installDir = "MOSAIK"

  def build(self):
    # "cd src",
    # "make"
    return 0

# picard #FIXME: <-------------

# premo
class Premo(GknoTool):

  def __init__(self):
    self.name       = "premo"
    self.gitUrl     = "git://github.com/gkno/premo.git"
    self.installDir = "premo"

  def build(self):
    #"mkdir build",
    #"cd build",
    #"cmake ..",
    #"make"
    return 0

##############################################################
# Add any new built-in gkno tools to the list below.
##############################################################

List = [ 
        BamTools(),
        Freebayes(),
        Gatk(),
        Mosaik(),
        #Picard(),
        Premo()
       ]

