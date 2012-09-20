#!/usr/bin/python

from __future__ import print_function

import json
import os
import os.path
import shutil
import subprocess
import sys
import tarfile
import urllib

import conf
import errors
from errors import *

class adminUtils:
  def __init__(self, sourcePath):

    # Command line modes
    self.resourceModes = [ "add-resource", "remove-resource", "update-resource" ]
    self.allModes      = [ "build", "update" ] + self.resourceModes

    # Setup help/usage descriptions
    self.modeDescriptions = {}
    self.modeDescriptions["build"]           = "Initialize gkno. This step is required to run any other operations."
    self.modeDescriptions["update"]          = "Update gkno itself, its internal tools, and any tracked organism resources."
    self.modeDescriptions["add-resource"]    = "Download resource data for an organism and track it for updated releases."
    self.modeDescriptions["remove-resource"] = "Delete resource data for an organism and stop tracking it."
    self.modeDescriptions["update-resource"] = "Update resource data for an organism."

    # General data members
    self.error        = errors()
    self.isRequested  = False
    self.isVerbose    = False
    self.mode         = ""
    self.userSettings = { }

    # Commonly used path names
    self.sourcePath    = sourcePath 
    self.resourcesPath = sourcePath + "/resources/"
    self.toolsPath     = sourcePath + "/tools/"
    self.logsPath      = sourcePath + "/logs/"
    
    # Import user settings from file (or initialize defaults if file doesn't exist)
    self.importUserSettings()

    # Make sure our common directories exist
    self.ensureMakeDir(self.resourcesPath)
    self.ensureMakeDir(self.toolsPath)
    self.ensureMakeDir(self.logsPath)

  # -------------------------------------------
  # Main entry point for running admin mode
  # -------------------------------------------

  # Verify built status on entry, run requested mode, 
  # and export user settings to file on successful exit.
  def run(self, commandLine):

    # Sanity check
    assert self.mode in self.allModes

    # Check that requested admin operation is compatible with our "built" status
    if self.mode == "build":
      if self.isBuilt():
        self.error.gknoAlreadyBuilt()
        return True
    else:
      if not self.isBuilt():
        self.error.gknoNotBuilt()
        return False
      
    # Run the requested operation
    success = False
    if   self.mode == "build" : success = self.build()
    elif self.mode == "update": success = self.update()
    else:
    
      # Check command line for organism and/or release name, then resolve any potential alias.
      possibleResourceAlias, hasReleaseArg, releaseName = self.getResourceArgs(commandLine)
      resolvedOk, resourceName = self.resolveAlias(possibleResourceAlias)
      if not resolvedOk:
        self.error.requestedUnknownResource(possibleResourceAlias)
        return False

      # Add/remove/update as requested
      if   self.mode == "add-resource"   : success = self.addResource(resourceName, hasReleaseArg, releaseName)
      elif self.mode == "remove-resource": success = self.removeResource(resourceName, hasReleaseArg, releaseName)
      elif self.mode == "update-resource": success = self.updateResource(resourceName)

    # If admin mode ran successfully, update our user settings file
    if success:
      self.exportUserSettings()

    # Return success/failure
    return success

  # -------------------------------------------
  # Admin mode main operations
  # -------------------------------------------

  # "gkno build"
  #
  # Building gkno consists of ensuring that all git submodules are up-to-date, 
  # building (compiling) all tools, and fetching all default resources.
  #  
  # If the build succeeds, then gkno's 'built' status is set to True.
  def build(self):

    # Cache our starting working directory since we're going to move around
    originalWorkingDir = os.getcwd()

    # Check requirements (attempt to access 3rd party dependencies/tools)
    print("Checking dependencies...", end="", file=sys.stdout)
    sys.stdout.flush()
    if self.checkDependencies():
      print("done.", file=sys.stdout)
    else:
      return False  # error message displayed in subroutine

    # Make sure submodules are intialized & up-to-date
    print("Initializing component data...", end="", file=sys.stdout)
    sys.stdout.flush()
    if self.gitSubmoduleUpdate():
      print("done.", file=sys.stdout)
    else:
      self.error.gitSubmoduleUpdateFailed(dest=sys.stdout)
      return False

    # Build all tools
    print("Building tools: ", file=sys.stdout)
    for tool in conf.tools:
      print("  "+tool.name+"...", end="", file=sys.stdout)
      sys.stdout.flush()
      if self.buildTool(tool):
        print("done.", file=sys.stdout)
      else:
        self.error.toolBuildFailed(tool.name, dest=sys.stdout)
        return False

    # Fetch all default resources (current releases only)
    print("Fetching default resources:", file=sys.stdout)
    for resource in conf.resources:
      if resource.isDefault:
        print("  "+resource.name+":", file=sys.stdout)
        sys.stdout.flush()
        if not self.addCurrentRelease(resource.name, "    "):
          self.error.resourceFetchFailed(resource.name, dest=sys.stdout)
          return False

    # If we get here - clean up, mark built status, and return success
    os.chdir(originalWorkingDir)
    self.userSettings["isBuilt"] = True
    return True

  # "gkno update"
  #
  # Updating gkno consists of ensuring that all git submodules are up-to-date, 
  # updating (possibly rebuilding) tools, and checking tracked resources for 
  # new releases.
  def update(self):

    # Update main gkno repo
    print("Updating gkno...", end="", file=sys.stdout)
    sys.stdout.flush()
    if self.gitUpdate():
      print("done.", file=sys.stdout)
    else:
      self.error.gitUpdateFailed(dest=sys.stdout)
      return False

    # Make sure submodules are intialized & up-to-date
    print("Initializing component data...", end="", file=sys.stdout)
    sys.stdout.flush()
    if self.gitSubmoduleUpdate():
      print("done.", file=sys.stdout)
    else:
      self.error.gitSubmoduleUpdateFailed(dest=sys.stdout)
      return False

    # Update all built-in tools 
    print("Checking tools: ", file=sys.stdout)
    for tool in conf.tools:
      print("  "+tool.name+"...", end="", file=sys.stdout)
      sys.stdout.flush()
      if self.updateTool(tool):
        print("done.", file=sys.stdout)
      else:
        self.error.toolUpdateFailed(tool.name, dest=sys.stdout)
        return False

    # Check resources for new updates
    print("Checking resources...", file=sys.stdout)
    sys.stdout.flush()
    updates = self.getUpdatableResources()
    print("done.", file=sys.stdout)

    # List any 'updatable' resources
    if len(updates) != 0:
      self.listUpdatableResources(updates)
      print("", file=sys.stdout)

    # Return success
    return True
    
  # "gkno add-resource [organism] [options]"
  #
  # Depending on input parameters, either lists available resources/releases or 
  # fetches the requested resource/release. 
  def addResource(self, resourceName, hasReleaseArg=False, releaseName=""):

    # If no organism name provided, list all available organisms
    # ("gkno add-resource")
    if resourceName == "":
      self.listAddableResources()
      return True

    # Otherwise, make sure that gkno actually knows about this organism
    else:
      found = False
      for resource in conf.resources:
        if resource.name == resourceName:
          found = True
          break
      if not found:
        self.error.requestedUnknownResource(resourceName)
        return False

    # If no release mentioned at all, fetch the current release for requested organism
    # ("gkno add-resource X")
    if not hasReleaseArg:
      print("Fetching current release for "+resourceName+":", file=sys.stdout)
      sys.stdout.flush()
      return self.addCurrentRelease(resourceName, "  ")

    # If "--release" was entered without a release name, list all available releases for specified organism
    # ("gkno add-resource X --release")
    if releaseName == "":
      self.listAddableReleases(resourceName)
      return True

    # Otherwise, fetch requested release for requested organism
    # ("gkno add-resource X --release Y")
    else:
      print("Fetching release "+releaseName+" for "+resourceName+":", file=sys.stdout)
      sys.stdout.flush()
      return self.addRelease(resourceName, releaseName, "  ")

  # "gkno remove-resource [organism] [options]"
  #
  # Depending on input parameters, either lists removable resources/releases or 
  # removes the requested resource/release. 
  def removeResource(self, resourceName, hasReleaseArg=False, releaseName=""):

    # If no organism name provided, list all organisms we have data for
    # ("gkno remove-resource")
    if resourceName == "":
      self.listRemovableResources()
      return True

    # Otherwise, make sure that gkno actually knows about this organism
    else:
      found = False
      for resource in conf.resources:
        if resource.name == resourceName:
          found = True
          break
      if not found:
        self.error.requestedUnknownResource(resourceName)
        return False

    # If no release mentioned at all, remove all releases for requested organism
    # ("gkno remove-resource X")
    if not hasReleaseArg:
      print("Removing all releases for "+resourceName+"...", end="", file=sys.stdout)
      sys.stdout.flush()
      success = self.removeAllReleases(resourceName)
      if success:
        print("done.", file=sys.stdout)
      else:
        pass
        #FIXME: error message
      return success

    # If "--release" was entered without a release name, list all of our releases for specified organism
    # ("gkno remove-resource X --release")
    if releaseName == "":
      self.listRemovableReleases(resourceName)
      return True

    # Otherwise, remove only the requested release for requested organism
    # ("gkno remove-resource X --release Y")
    else:
      print("Removing release "+releaseName+" for "+resourceName+"...", end="", file=sys.stdout)
      sys.stdout.flush()
      success = self.removeRelease(resourceName, releaseName)
      if success:
        print("done.", file=sys.stdout)
      else:
        pass
        #FIXME: error message
      return success

  # "gkno update-resource <organism>"
  #
  # Functionally equivalent to the "gkno add-resource X" operation, 
  # but provided as a command-line convenience.
  def updateResource(self, resourceName):

    # If no organism name provided, list all organisms we can update
    # ("gkno update-resource")
    if resourceName == "":
      updates = self.getUpdatableResources()
      self.listUpdatableResources(updates)
      return True

    # Otherwise, add the current release for this organism
    # ("gkno update-resource <organism>")
    else:
      print("Updating "+resourceName+":", file=sys.stdout)
      sys.stdout.flush()
      return self.addCurrentRelease(resourceName, "  ")

  # -------------------------------------------
  # Build/update helper methods
  # -------------------------------------------

  def buildTool(self, tool):
    stub = "build_" + tool.name
    outFilename = self.logsPath + stub + ".out"
    errFilename = self.logsPath + stub + ".err"
    out = sys.stdout
    err = sys.stderr
    if not self.isVerbose:
      out = open(outFilename, 'w')
      err = open(errFilename, 'w')
    os.chdir(self.toolsPath + tool.installDir)
    success = tool.build(out, err)
    if not self.isVerbose:
      out.close()
      err.close()
      if success: 
        os.remove(outFilename)
        os.remove(errFilename)
    return success

  def updateTool(self, tool):
    stub = "update_" + tool.name
    outFilename = self.logsPath + stub + ".out"
    errFilename = self.logsPath + stub + ".err"
    out = sys.stdout
    err = sys.stderr
    if not self.isVerbose:
      out = open(outFilename, 'w')
      err = open(errFilename, 'w')
    os.chdir(self.toolsPath + tool.installDir)
    success = tool.update(out, err)
    if not self.isVerbose:
      out.close()
      err.close()
      if success: 
        os.remove(outFilename)
        os.remove(errFilename)
    return success

  def gitSubmoduleUpdate(self):
    outFilename = self.logsPath + "submodule_update.out"
    errFilename = self.logsPath + "submodule_update.err"
    out = sys.stdout
    err = sys.stderr
    if not self.isVerbose:
      out = open(outFilename, 'w')
      err = open(errFilename, 'w')
    os.chdir(self.sourcePath)
    success = self.runCommand("git submodule update --init --recursive", out, err)
    if not self.isVerbose:
      out.close()
      err.close()
      if success:
        os.remove(outFilename)
        os.remove(errFilename)
    return success

  def gitUpdate(self):
    outFilename = self.logsPath + "gkno_update.out"
    errFilename = self.logsPath + "gkno_update.err"
    out = sys.stdout
    err = sys.stderr
    if not self.isVerbose:
      out = open(outFilename, 'w')
      err = open(errFilename, 'w')
    os.chdir(self.sourcePath)
    success = self.runCommand("git pull origin master", out, err)
    if not self.isVerbose:
      out.close()
      err.close()
      if success:
        os.remove(outFilename)
        os.remove(errFilename)
    return success

  def checkDependencies(self):
    
    # Initialize our error lists
    missing      = []
    incompatible = []
    unknown      = []
    
    # For each dependency
    allChecksPassed = True
    for dependency in conf.dependencies:

      # If check failed, store in respective list 
      if not dependency.check():
        if   dependency.isMissing:        missing.append(dependency)
        elif dependency.isUnknownVersion: unknown.append(dependency)
        else:                             incompatible.append(dependency)
        allChecksPassed = False
        
    # Return success if all checks passed
    if allChecksPassed:
      return True

    #------------------------------------------------------------------------
    # Failed
    #------------------------------------------------------------------------

    # Print helpful message 
    print("failed.", file=sys.stdout)
    sys.stdout.flush()
    print("", file=sys.stdout)
    
    if len(missing) > 0:
      print("    Missing:", file=sys.stdout)
      for dep in missing:
        print("        ",dep.name, sep="", file=sys.stdout)
      print("", file=sys.stdout)
    if len(incompatible) > 0:
      print("    Not up-to-date:", file=sys.stdout)
      for dep in incompatible:
        print("        ", dep.name, 
              "    minimum version: ", dep.minimumVersion, 
              "    found version: "  , dep.currentVersion, sep="", file=sys.stdout)
      print("", file=sys.stdout)
    if len(missing) > 0 or len(incompatible) > 0:
      print("", file=sys.stdout)
      print("gkno (and its components) require a few 3rd-party utilities", file=sys.stdout)
      print("to either build or run properly.  To obtain/update the utilities ", file=sys.stdout)
      print("listed above, check your system's package manager or search the ", file=sys.stdout)
      print("web for download instructions.", file=sys.stdout)
      print("", file=sys.stdout)

    # ODD CASE
    if len(unknown) > 0:
      print("----------------------------------------", file=sys.stdout)
      print("The following utilities have version numbers that could not be ", file=sys.stdout)
      print("determined by gkno:", file=sys.stdout)
      for dep in unknown:
        print("        ",dep.name, sep="", file=sys.stdout)
      print("", file=sys.stdout)
      print("This indicates a likely bug or as-yet-unseen oddity.", file=sys.stdout)
      print("Please contact the gkno development team to report this issue.  Thanks.", file=sys.stdout)
      print("", file=sys.stdout)
      print("----------------------------------------", file=sys.stdout)

    # Return failure
    return False

  # -------------------------------------------
  # Release helper methods
  # -------------------------------------------

  # Adds a resource's "current" release
  def addCurrentRelease(self, resourceName, outputIndent=""):

    # Fetch the name resource's "current" release
    currentReleaseName = self.getCurrentReleaseName(resourceName)
    if currentReleaseName == "":
      self.error.noCurrentReleaseAvailable(resourceName)
      return False

    # Add named release
    if not self.addRelease(resourceName, currentReleaseName, outputIndent):
      return False

    # Make a symlink-ed directory "current" that points to release's directory
    currentDir = self.resourcesPath + resourceName + "/current"
    releaseDir = self.resourcesPath + resourceName + "/" + currentReleaseName
    os.symlink(releaseDir, currentDir)
    
    # Update settings & return success
    self.userSettings["resources"][resourceName]["isTracking"] = True
    self.userSettings["resources"][resourceName]["current"]    = currentReleaseName
    return True

  # Add a named release for a named resource
  def addRelease(self, resourceName, releaseName, outputIndent=""):

    # If this is the first release for a requested organism resource, initialize its settings
    if resourceName not in self.userSettings["resources"]:
      self.userSettings["resources"][resourceName] = {}
      self.userSettings["resources"][resourceName]["current"]    = ""
      self.userSettings["resources"][resourceName]["isTracking"] = False
      self.userSettings["resources"][resourceName]["releases"]   = []

    # Make sure we don't already have this release
    if releaseName in self.userSettings["resources"][resourceName]["releases"]:
      self.error.resourceAlreadyAdded(resourceName)
      return False

    # Move into resource's directory
    os.chdir(self.resourcesPath + resourceName)

    # Get URL for release's tarball
    tarballUrl = self.getUrlForRelease(resourceName, releaseName)
    if tarballUrl == "":
      self.error.noReleaseUrlFound(resourceName, releaseName)
      return False

    # Download release tarball
    print(outputIndent+"Downloading files...  0%", end="", file=sys.stdout)
    sys.stdout.flush()
    try:
      filename, headers = urllib.urlretrieve(tarballUrl, reporthook=downloadProgress) 
    except IOError:
      self.error.urlRetrieveFailed(tarballUrl)
      return False
    print("", file=sys.stdout)
  
    # Extract files from tarball
    # N.B. - tarball should be set up so that all of its contents are 
    #        in a parent directory whose name matches its 'releaseName'
    print(outputIndent+"Unpacking files...", end="", file=sys.stdout)
    sys.stdout.flush()
    try:
      tar = tarfile.open(filename)
      tar.extractall()
      tar.close()
    except tarfile.TarError:
      self.error.extractTarballFailed(filename)
      return False
    print("done.", file=sys.stdout)

    # Delete tarball
    os.remove(filename)

    # Add release to our settings for this resource & return success
    self.userSettings["resources"][resourceName]["releases"].append(releaseName)
    return True

  # Returns a dictionary of all tracked genomes with new 'current' releases
  # { resourceName : newReleaseName }
  def getUpdatableResources(self):
    updates = {}  
    for resourceName in self.userSettings["resources"]:
      if self.userSettings["resources"][resourceName]["isTracking"]:
        localCurrentReleaseName = self.userSettings["resources"][resourceName]["current"]
        newCurrentReleaseName   = self.getCurrentReleaseName(resourceName)
        if localCurrentReleaseName != newCurrentReleaseName:
          updates[resourceName] = newCurrentReleaseName
    return updates

  # Removes all releases for a named resource
  def removeAllReleases(self, resourceName):
    allRemovedOk = True
    for releaseName in self.userSettings["resources"][resourceName]["releases"]:
      if not self.removeRelease(resourceName, releaseName):
        allRemovedOk = False
    return allRemovedOk

  # Removes a named release for a named resource
  def removeRelease(self, resourceName, releaseName):

    # Delete release directory (and all of its contents)
    shutil.rmtree(self.resourcesPath + resourceName + "/" + releaseName)
    
    # Remove release from settings
    self.settings["resources"][resourceName]["releases"].remove(releaseName)

    # If this was the last release for an organism, remove its entry for settings
    if len(self.settings["resources"][resourceName]["releases"]) == 0:
      self.settings["resources"].remove(resourceName)

    # Return success (any possible failures here?)
    return True

  # -------------------------------------------
  # Resource target file methods
  # -------------------------------------------

  # Return the name of a resource's "current" release
  def getCurrentReleaseName(self, resourceName):
    targetSettings = self.readTargetsFile(resourceName)
    return targetSettings["current"]

  # Return the URL for a resource's named release ("" if not found)
  def getUrlForRelease(self, resourceName, releaseName):
    targetSettings = self.readTargetsFile(resourceName)
    for targetInfo in targetSettings["targets"]:
      if targetInfo["name"] == releaseName:
        return targetInfo["url"]
    return ""

  # Fetch & return resource's target data (JSON)
  def readTargetsFile(self, resourceName):
    targetFile = open(self.resourcesPath + resourceName + "/targets.json")
    try: 
      return json.load(targetFile)
    except:
      exc_type, exc_value, exc_traceback = sys.exc_info()
      self.error.jsonOpenError(True, 1, exc_value, targetFile)
      self.error.terminate()

  # -------------------------------------------
  # Resource listing methods
  # -------------------------------------------

  # Print a list of all genomes that we have no data for
  def listAddableResources(self):

    # Print header
    print("The following organism resources are available. (Aliases in parentheses)", file=sys.stdout)
    print("Add using: 'gkno add-resource <organism>'", file=sys.stdout)
    print("", file=sys.stdout)

    # Lookup all possible resource names (& store corresponding aliases)
    allResources = {}
    for resource in conf.resources:
      allResources[resource.name] = resource.aliases

    # Lookup all user's resources
    userResourceNames = []
    for name in self.userSettings["resources"].keys():
      userResourceNames.append(name)

    # Determine padding based on longest resource name
    maxNameLength = 0
    for name in allResources.keys():
      currentNameLength = len(name)
      if currentNameLength > maxNameLength:
        maxNameLength = currentNameLength
    maxNameLength += 4

    # Print resource list
    allResourceNames = allResources.keys()
    allResourceNames.sort()
    for name in allResourceNames:
      print("    ", sep="", end="", file=sys.stdout)
      if name in userResourceNames:
        print("* ", sep="", end="", file=sys.stdout)
      else:
        print("  ", sep="", end="", file=sys.stdout)
      print(name, end="", file=sys.stdout)
      print(" "*(maxNameLength-len(name)), end="", file=sys.stdout)
      aliases = allResources[name]
      numAliases = len(aliases)
      if numAliases > 0:
        print("(", end="", file=sys.stdout)
        i = 1
        for alias in aliases:
          if i < numAliases:
            print(alias+", ", end="", file=sys.stdout)
          else:
            print(alias, end="", file=sys.stdout)
          i += 1
        print(")", end="")
      print("", file=sys.stdout)
    print("", file=sys.stdout)

    # Print footer
    print("Resources preceded by a '*' have already been added.", file=sys.stdout)
    print("", file=sys.stdout)

  # Print a list of all releases available for named resource
  def listAddableReleases(self, resourceName):

    # Print header
    print("The following releases are available for "+resourceName+".", file=sys.stdout)
    print("Add using: 'gkno add-resource "+resourceName+" --release <name>'", file=sys.stdout)
    print("", file=sys.stdout)

    # Lookup all possible releases for resource
    targetSettings = self.readTargetsFile(resourceName)
    allReleaseNames = []
    for target in targetSettings["targets"]:
      allReleaseNames.append(target["name"])

    # Lookup all user's releases for resource
    userReleaseNames = []
    if resourceName in self.userSettings["resources"]:
      for releaseName in self.userSettings["resources"][resourceName]["releases"]:
        userReleaseNames.append(releaseName)

    # Print release list
    for name in allReleaseNames:
      print("    ", sep="", end="", file=sys.stdout)
      if name in userReleaseNames:
        print("* ", sep="", end="", file=sys.stdout)
      else:
        print("  ", sep="", end="", file=sys.stdout)
      print(name, file=sys.stdout)
    print("", file=sys.stdout)

    # Print footer
    print("Releases preceded by a '*' have already been added.", file=sys.stdout)
    print("", file=sys.stdout)

  # Print a list of all genomes we have data for
  def listRemovableResources(self):

    # Print header
    print("The following organism resources can be removed. (Aliases in parentheses)", file=sys.stdout)
    print("Remove using: 'gkno remove-resource <organism>'", file=sys.stdout)
    print("", file=sys.stdout)

    # Lookup all possible resource names (& store corresponding aliases)
    allResources = {}
    for resource in conf.resources:
      allResources[resource.name] = resource.aliases
  
    # Determine padding based on longest removable resource name
    maxNameLength = 0
    removableResourceNames = self.userSettings["resources"].keys()
    for name in removableResourceNames:
      currentNameLength = len(name)
      if currentNameLength > maxNameLength:
        maxNameLength = currentNameLength
    maxNameLength += 4

    # Print resource list
    removableResourceNames.sort()
    for name in removableResourceNames:
      print("    "+name, end="", file=sys.stdout)
      print(" "*(maxNameLength-len(name)), end="", file=sys.stdout)
      aliases = allResources[name]
      numAliases = len(aliases)
      if numAliases > 0:
        print("(", end="", file=sys.stdout)
        i = 1
        for alias in aliases:
          if i < numAliases:
            print(alias+", ", end="", file=sys.stdout)
          else:
            print(alias, end="", file=sys.stdout)
          i += 1
        print(")", end="")
      print("", file=sys.stdout)
    print("", file=sys.stdout)

  # Print a list of all releases we have for named resource
  def listRemovableReleases(self, resourceName):

    # Print header
    print("The following releases can be removed for "+resourceName+".", file=sys.stdout)
    print("Remove using: 'gkno remove-resource "+resourceName+" --release <name>'", file=sys.stdout)
    print("", file=sys.stdout)

    # Print release list
    if resourceName in self.userSettings["resources"]:
      allReleaseNames = self.userSettings["resources"][resourceName]["releases"]
      allReleaseNames.sort()
      for name in allReleaseNames:
        print("    "+name, file=sys.stdout)
    print("", file=sys.stdout)

  # Print a list of all updatable resources
  def listUpdatableResources(self, updates):

    # Print header
    print("The following organisms have new releases available. (Aliases in parentheses)", file=sys.stdout)
    print("Update using: 'gkno update-resource <organism>'", file=sys.stdout)
    print("", file=sys.stdout)

    # Lookup all possible resource names (& store corresponding aliases)
    allResources = {}
    for resource in conf.resources:
      allResources[resource.name] = resource.aliases

    # Determine padding based on longest updatable resource name
    maxNameLength = 0
    updatableResourceNames = updates.keys()
    for name in updatableResourceNames:
      currentNameLength = len(name)
      if currentNameLength > maxNameLength:
        maxNameLength = currentNameLength
    maxNameLength += 4

    # Print resource list
    updatableResourceNames.sort()
    for name in updatableResourceNames:
      print("    "+name, end="", file=sys.stdout)
      print(" "*(maxNameLength-len(name)), end="", file=sys.stdout)
      aliases = allResources[name]
      numAliases = len(aliases)
      if numAliases > 0:
        print("(", end="", file=sys.stdout)
        i = 1
        for alias in aliases:
          if i < numAliases:
            print(alias+", ", end="", file=sys.stdout)
          else:
            print(alias, end="", file=sys.stdout)
          i += 1
        print(")", end="")
      print("", file=sys.stdout)
    print("", file=sys.stdout)

  # -------------------------------------------
  # Settings file & build status methods
  # -------------------------------------------

  # Import settings data from file, or 
  # initialize settings object if the file has not been created yet
  def importUserSettings(self):
    if not self.userSettingsFileExists():
      self.userSettings["resources"] = {}
      self.userSettings["isBuilt"]   = False
    else:
      settingsFile = open(self.userSettingsFilename())
      try: 
        self.userSettings = json.load(settingsFile)
      except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        self.error.jsonOpenError(True, 1, exc_value, settingsFile)
        self.error.terminate()
  
  # Write settings to file in JSON format
  def exportUserSettings(self):
    filehandle = open(self.userSettingsFilename(), 'w')
    json.dump(self.userSettings, filehandle, indent = 2)
    filehandle.close()

  # Returns True if gkno has been 'built'
  def isBuilt(self):
    return self.userSettingsFileExists() and self.userSettings["isBuilt"]
  
  # Returns path to user settings file.
  # This file lists our 'built' status and all tracked resources.
  def userSettingsFilename(self):
    return self.sourcePath + "/src/gkno/conf/user_settings.json"

  # Returns True if the settings file exists on disk
  def userSettingsFileExists(self):
    return os.path.exists( self.userSettingsFilename() )

  # -------------------------------------------
  # Other utility methods
  # -------------------------------------------

  # Creates directory if it doesn't already exist
  def ensureMakeDir(self, directory, mode=0777):
    if not os.path.exists(directory):
      os.makedirs(directory, mode)

  # Parse command line arguments
  # "gkno mode" values have already been removed
  def getResourceArgs(self, commandLine):

    # Set defaults
    resourceName  = ""
    hasReleaseArg = False
    releaseName   = ""  

    # If any args provided 
    if len(commandLine) > 0:
      
      # We require the first one to be a bare-word resource name
      if commandLine[0].startswith("-"):
        self.error.invalidResourceArgs(self.mode)
        self.error.terminate()
      resourceName = commandLine[0].lower()
      commandLine.pop(0)
      
      # Handle any additional args
      while ( len(commandLine) != 0 ):
        argument = commandLine.pop(0)

        # All of our args must start with '-'
        if not argument.startswith("-"):
          self.error.invalidResourceArgs(self.mode)
          self.error.terminate()

        # If arg is '--release' 
        if argument == "--release":

          # "update-resource" does not recognize '--release' arg
          if self.mode == "update-resource":
            self.error.invalidResourceArgs(self.mode)
            self.error.terminate()

          # Otherwise, set flag & see if a release name exists
          hasReleaseArg = True
          try: 
            releaseName = commandLine.pop(0).lower()
          except: 
            releaseName = ""

        # If arg is '--verbose' or '-vb', ignore it (we've already set our verbose-ness).
        elif argument == "--verbose" or argument == "-vb":
          continue

        # If arg is ( ADD ANY NEW ARG HANDLING HERE )

        # If argument unrecognized
        else:
          self.error.invalidResourceArgs(self.mode)
          self.error.terminate()
          
    # Return parsed results 
    return (resourceName, hasReleaseArg, releaseName)

  # Resolves resource alias
  #
  # If input is a normal resource name, just return it.
  # If input is an alias, return resource's actual name.
  # If input is not recognized, return empty string.
  def resolveAlias(self, possibleAlias) :
    if possibleAlias == "":
      return (True, "")
    for resource in conf.resources:
      if (possibleAlias == resource.name) or (possibleAlias in resource.aliases):
        return (True, resource.name)
    return (False, "")

  # Convenience method for running "system" calls with easier syntax (no array syntax in calling code)
  # Adds the option to direct stdout/stderr to any file objects (defaults to normal stdout/stderr)
  # Converts command exit status to True/False (under assumption of common practice that exit status of 0 is success)
  def runCommand(self, command, out=sys.stdout, err=sys.stderr):
    status = subprocess.call(command.split(), stdout=out, stderr=err)
    return status == 0

  # Convenience method for runCommand(), where all output (stdout/stderr) is suppressed
  def runSilentCommand(self, command):
    return self.runCommand(command, out=open(os.devnull, 'w'), err=open(os.devnull, 'w'))

def downloadProgress(count, blockSize, totalSize):
    percent = int(count*blockSize*100/totalSize)
    sys.stdout.write("\b\b\b%2d%%" % percent)
    sys.stdout.flush()
