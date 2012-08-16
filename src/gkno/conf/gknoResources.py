
###############################################################
# IMPORTANT: To make a new resource repository available to
#   gkno, create a subclass of GknoResource with the proper 
#   git info. After that, add an instance of your new class 
#   to the 'resourceList' at the bottom of this script.
#   
#   gkno's 'admin mode' will use this list to know which 
#   resources are available
###############################################################

# Base class for all gkno resources
class GknoResource:

  # Initialize defaults (e.g. "master" branch from all git repos
  # unless otherwise specified.)
  def __init__(self):
    self.name       = ""
    self.gitBranch  = "master"
    self.gitUrl     = ""
    self.installDir = ""
    self.isDefault  = False # set this to True if resource should be available after initial build

###############################################################

# ecoli
class EColi(GknoResource):
  
  def __init__(self):
    self.name       = "ecoli"
    self.gitUrl     = "git://github.com/gkno/resources-ecoli.git"
    self.installDir = "e.coli"

# human
class Human(GknoResource):
  
  def __init__(self):
    self.name       = "human"
    self.gitUrl     = "git://github.com/gkno/resources-human.git"
    self.installDir = "human"

# mouse
class Mouse(GknoResource):
  
  def __init__(self):
    self.name       = "mouse"
    self.gitUrl     = "git://github.com/gkno/resources-mouse.git"
    self.installDir = "mouse"

# test
class Test(GknoResource):
  
  def __init__(self):
    self.name       = "test"
    self.gitUrl     = "git://github.com/gkno/resources-test.git"
    self.installDir = "test"
    self.isDefault  = True

# yeast
class Yeast(GknoResource):
  
  def __init__(self):
    self.name       = "yeast"
    self.gitUrl     = "git://github.com/gkno/resources-yeast.git"
    self.installDir = "yeast"

##############################################################
# Add any new gkno resource repos to the list below.
##############################################################

List = [ 
        #EColi(),
        #Human(),
        #Mouse(),
        Test(),
        #Yeast()
       ] 
