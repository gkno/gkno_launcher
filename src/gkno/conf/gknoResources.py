
###############################################################
# IMPORTANT: To make a new resource available to gkno, create 
#   a subclass of GknoResource with the proper info. Then, add 
#   an instance of your new class to 'List' at the bottom of 
#   this script. 
#
#   gkno's 'admin mode' will use this list to know which 
#   resources are available.
###############################################################

# Base class for all gkno resources
class GknoResource(object):
  def __init__(self):

    # Resource's display name. Should be unique across all built-in's
    self.name = ""

    # Resource's root install directory (probably same as self.name)
    # This should be the directory used when adding the resource as a submodule
    #   So 'git submodule add ... resources/X' means this installDir = "X"
    self.installDir = ""
    
    # Set this to True if the resource should be available immediately after initial build.
    # N.B. - gkno only supports adding the 'current' release of a default resource.
    self.isDefault = False 

    # Add any additional aliases (like 'human' for homo_sapiens)
    # We'll do a case-insensitive compare, so don't bother listing case variations.
    self.aliases = []    

###############################################################

# for tutorials
class Tutorial(GknoResource):
  def __init__(self):
    super(Tutorial, self).__init__()
    self.name       = "tutorial"
    self.installDir = "tutorial"
    self.isDefault  = True

###############################################################

class CaenorhabditisElegans(GknoResource):
  def __init__(self):
    super(CaenorhabditisElegans, self).__init__()
    self.name       = "caenorhabditis_elegans"
    self.installDir = "caenorhabditis_elegans"
    self.aliases    = ["c.elegans"]

class EscherichiaColi(GknoResource):
  def __init__(self):
    super(EscherichiaColi, self).__init__()
    self.name       = "escherichia_coli"
    self.installDir = "escherichia_coli"
    self.aliases    = ["e.coli"]

class HomoSapiens(GknoResource):  
  def __init__(self):
    super(HomoSapiens, self).__init__()
    self.name       = "homo_sapiens"
    self.installDir = "homo_sapiens"
    self.aliases    = ["h.sapiens", "human"]

class MusMusculus(GknoResource):
  def __init__(self):
    super(MusMusculus, self).__init__()
    self.name       = "mus_musculus"
    self.installDir = "mus_musculus"
    self.aliases    = ["m.musculus", "mouse"]

class ToxoplasmaGondii(GknoResource):
  def __init__(self):
    super(ToxoplasmaGondii, self).__init__()
    self.name       = "toxoplasma_gondii"
    self.installDir = "toxoplasma_gondii"
    self.aliases    = ["t.gondii", "toxoplasma"]

##############################################################
# Add any new gkno resource instances to the list below.
##############################################################

List = [ Tutorial(),
        #CaenorhabditisElegans(),
        #EscherichiaColi(),
        HomoSapiens(),
        #MusMusculus(),
        #ToxoplasmaGondii()
       ] 
