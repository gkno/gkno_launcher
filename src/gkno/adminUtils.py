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
    self.isRequested  = False
    self.isVerbose    = False
    self.mode         = ""
    self.sourcePath   = sourcePath 
    self.userSettings = {}

    # Import user settings from file, initializing defaults if it doesn't exist
    self.importUserSettings()

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
        er = errors()
        er.gknoAlreadyBuilt()
        er.terminate()
    else:
      self.requireBuilt()
      
    # Run the requested operation
    if   self.mode == "build"  : self.build()
    elif self.mode == "update" : self.update()
    else:
    
      # Check command line for organism and/or release name
      possibleResourceAlias, hasReleaseArg, releaseName = self.getResourceArgs(commandLine)

      # Resolve any alias used
      resourceName = self.resolveAlias(possibleResourceAlias)
      if resource == "" :
        er = errors()
        er.requestedUnknownResource(possibleResourceAlias)
        er.terminate()

      # Add/remove requested resource/release 
      if   self.mode == "add-resource"    : self.addResource(resourceName, hasReleaseArg, releaseName)
      elif self.mode == "remove-resource" : self.removeResource(resourceName, hasReleaseArg, releaseName)
      elif self.mode == "update-resource" : self.updateResource(resourceName)

    # If admin mode ran successfully, update our user settings file
    self.exportUserSettings()

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

    # Cache other common directory paths
    resourcesDir = self.sourcePath + "/resources/"
    toolsDir     = self.sourcePath + "/tools/"

    # Make sure submodules are intialized & up-to-date
    os.chdir(self.sourcePath)
    print("Initializing component data...", end="", file=sys.stdout)
    status = self.runCommand("git submodule update --init --recursive")
    if status == 0:
      print("done.", file=sys.stdout)
    else:
      pass # FIXME: git submodule update error

    # Build all built-in tools
    print("Building tools: ", file=sys.stdout)
    for tool in conf.tools:
      print("\t" + tool.name + "...", end="", file=sys.stdout)
      os.chdir(toolsDir + tool.installDir)
      status = tool.build()
      if status == 0: 
        print("done.", file=sys.stdout)
      else:
        pass # FIXME: tool build error
    print("\n", file=sys.stdout)

    # Fetch all default resources (current releases only)
    print("Fetching default resources:", file=sys.stdout)
    for resource in conf.resources:
      if resource.isDefault:
        print("\t" + resource.name + "...", end="", file=sys.stdout)
        self.addResource(resource.name)
        print("done.", file=sys.stdout)
    print("\n", file=sys.stdout)
     
    # Clean up & mark built status
    os.chdir(originalWorkingDir)
    self.userSettings["isBuilt"] = True

  # "gkno update"
  #
  # Updating gkno consists of ensuring that all git submodules are up-to-date, 
  # updating (possibly rebuilding) tools, and checking tracked resources for 
  # new releases.
  def update(self):

    # Update main gkno repo
    print("Updating gkno...", end="", file=sys.stdout)
    status = self.runCommand("git pull origin master")
    if status == 0:
      print("done.", file=sys.stdout)
    else:
      pass # FIXME: git update error

    # Make sure submodules are intialized & up-to-date
    print("Updating component data...", end="", file=sys.stdout)
    os.chdir(self.sourcePath)
    status = self.runCommand("git submodule update --init --recursive")
    if status == 0:
      print("done.", file=sys.stdout)
    else:
      pass # FIXME: git submodule update error

    # Update all built-in tools 
    print("Checking tools: ", file=sys.stdout)
    for tool in conf.tools:
      print("\t" + tool.name + "...", end="", file=sys.stdout)
      os.chdir(toolsDir + tool.installDir)
      tool.update()
      if status == 0: 
        print("done.", file=sys.stdout)
      else:
        pass # FIXME: tool update error
    print("\n", file=sys.stdout)

    # List any resources with new updates
    print("Checking resources...", file=sys.stdout)
    updates = self.getUpdatableResources()
    print("done.", file=sys.stdout)
    print("\n", file=sys.stdout)

    if len(updates) != 0:
      self.listUpdatableResources(updates)
      print("\n", file=sys.stdout)
    
  # "gkno add-resource [organism] [options]"
  #
  # Depending on input parameters, either lists available resources/releases or 
  # fetches the requested resource/release. 
  def addResource(self, resourceName, hasReleaseArg=False, releaseName=""):

    # If no organism name provided, list all available organisms
    # ("gkno add-resource")
    if resourceName == "":
      self.listAddableResources()
      return

    # Otherwise, make sure that gkno actually knows about this organism
    else:
      found = False
      for resource in conf.resources:
        if resource.name == resourceName:
          found = True
          break
      if not found:
        # FIXME: attempting to add unknown resource
        return

    # If no release mentioned at all, fetch the current release for requested organism
    # ("gkno add-resource X")
    if not hasReleaseArg:
      self.addCurrentRelease(resourceName)
      return

    # If "--release" was entered without a release name, list all available releases for specified organism
    # ("gkno add-resource X --release")
    if releaseName == "":
      self.listAddableReleases(resourceName)

    # Otherwise, fetch requested release for requested organism
    # (i.e. "gkno add-resource X --release Y")
    else:
      self.addRelease(resourceName, releaseName)

  # "gkno remove-resource [organism] [options]"
  #
  # Depending on input parameters, either lists removable resources/releases or 
  # removes the requested resource/release. 
  def removeResource(self, resourceName, hasReleaseArg=False, releaseName=""):

    # If no organism name provided, list all organisms we have data for
    # ("gkno remove-resource")
    if resourceName == "":
      self.listRemovableResources()
      return

    # Otherwise, make sure that gkno actually knows about this organism
    else:
      found = False
      for resource in conf.resources:
        if resource.name == resourceName:
          found = True
          break
      if not found:
        # FIXME: attempting to remove unknown resource
        return

    # If no release mentioned at all, remove all releases for requested organism
    # ("gkno remove-resource X")
    if not hasReleaseArg:
      self.removeAllReleases(resourceName)
      return

    # If "--release" was entered without a release name, list all of our releases for specified organism
    # ("gkno remove-resource X --release")
    if releaseName == "":
      self.listRemovableReleases(resourceName)

    # Otherwise, remove only the requested release for requested organism
    # (i.e. "gkno remove-resource X --release Y")
    else:
      self.removeRelease(resourceName, releaseName)

  # "gkno update-resource <organism>"
  #
  # Functionally equivalent to the "gkno add-resource X" operation, 
  # but provided as a command-line convenience.
  def updateResource(self, resourceName):
    self.addCurrentRelease(resourceName)

  # -------------------------------------------
  # Resource helper methods
  # -------------------------------------------

  # Adds a resource's "current" release
  def addCurrentRelease(self, resourceName):

    # Fetch the name resource's "current" release
    currentReleaseName = self.getCurrentReleaseName(resourceName)
    if currentReleaseName == "":
      # FIXME: no current release available for resource
      return

    # Add named release
    self.addRelease(resourceName, currentReleaseName)

    # Make a symlink-ed directory "current" that points to release's directory
    currentDir = self.sourcePath + "/resources/" + resourceName + "/current"
    releaseDir = self.sourcePath + "/resources/" + resourceName + "/" + currentReleaseName
    os.symlink(releaseDir, currentDir)
    
    # Update settings
    self.userSettings["resources"][resourceName]["isTracking"] = True
    self.userSettings["resources"][resourceName]["current"]    = currentReleaseName

  # Add a named release for a named resource
  def addRelease(self, resourceName, releaseName):

    # If this is the first release for a requested organism resource, initialize its settings
    if resourceName not in self.userSettings["resources"]:
      self.userSettings["resources"][resourceName] = {}
      self.userSettings["resources"][resourceName]["current"]    = ""
      self.userSettings["resources"][resourceName]["isTracking"] = False
      self.userSettings["resources"][resourceName]["releases"]   = []

    # Make sure we don't already have this release
    if releaseName in self.userSettings["resources"][resourceName]["releases"]:
      # FIXME: warn: already added this release
      return 

    # Move into resource's directory
    os.chdir(self.sourcePath + "/resources/" + resourceName)

    # Get URL for release's tarball
    tarballURL = self.getUrlForRelease(resourceName, releaseName)
    if tarballURL == "":
      #FIXME: no URL for this resource/release
      return

    # Download release tarball
    filename, headers = urllib.urlretrieve(tarballURL) 

    # Extract files from tarball
    # N.B. - tarball should be set up so that all of its contents are 
    #        in a parent directory whose name matches its 'releaseName'
    tar = tarfile.open(filename)
    tar.extractall()
    tar.close()

    # Delete tarball
    os.remove(filename)

    # Add release to our settings for this resource
    self.userSettings["resources"][resourceName]["releases"].append(releaseName)

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
    for releaseName in self.userSettings["resources"][resourceName]["releases"]:
      self.removeRelease(resourceName, releaseName)

  # Removes a named release for a named resource
  def removeRelease(self, resourceName, releaseName):

    # Delete release directory (and all of its contents)
    shutil.rmtree(self.sourcePath + "/resources/" + resourceName + "/" + releaseName)
    
    # Remove release from settings
    self.settings["resources"][resourceName]["releases"].remove(releaseName)

    # If this was the last release for an organism, remove its entry for settings
    if len(self.settings["resources"][resourceName]["releases"]) == 0:
      self.settings["resources"].remove(resourceName)

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
    targetFile = open(self.sourcePath + "/resources/" + resourceName + "/targets.json")
    try: 
      return json.load(targetFile)
    except:
      er = errors()
      er.error = True
      exc_type, exc_value, exc_traceback = sys.exc_info()
      er.jsonOpenError("\t", exc_value)
      er.terminate()

  # -------------------------------------------
  # Resource listing methods
  # -------------------------------------------

  # Print a list of all genomes that we have no data for
  def listAddableResources(self):
    print("List all genomes that we can add", file = sys.stdout)
    # FIXME: implement
    
    allResourceNames = []
    for resource in conf.resources:
      allResourceNames.append(resource.name)

  # Print a list of all releases available for named resource
  def listAddableReleases(self, resourceName):
    print("List all releases for", resourceName, "that we can add", sep=" ", file = sys.stdout)
    # FIXME: implement

  # Print a list of all genomes we have data for
  def listRemovableResources(self):
    print("List all genomes that we can remove", file = sys.stdout)
    # FIXME: implement

  # Print a list of all releases we have for named resource
  def listRemovableReleases(self, resourceName):
    print("List all releases for", resourceName, "that we can remove", sep=" ", file = sys.stdout)
    # FIXME: implement

  # Print a list of all updatable resources/releases
  # @param updates => dictionary { resourceName : newReleaseName }
  def listUpdatableResources(self, updates):
    print("List all releases for", resourceName, "that we can remove", sep=" ", file = sys.stdout)
    # FIXME: implement

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
        er = errors()
        er.error = True
        exc_type, exc_value, exc_traceback = sys.exc_info()
        er.jsonOpenError("\t", exc_value)
        er.terminate()
  
  # Write settings to file in JSON format
  def exportUserSettings(self):
    filehandle = open(self.userSettingsFilename(), 'w')
    json.dump(self.userSettings, filehandle, indent = 2)
    filehandle.close()

  # Returns True if gkno has been 'built'
  def isBuilt(self):
    return self.userSettingsFileExists() and self.userSettings["isBuilt"]

  # Checks gkno's 'built' status. Prints error message if 'gkno build' has not 
  # been run.
  def requireBuilt(self):
    if not self.isBuilt():
      er = errors()
      er.gknoNotBuilt()
      er.terminate()
  
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
        er = errors()
        er.invalidResourceArgs(self.mode)
        er.terminate()
      resourceName = commandLine[0].lower()
      commandLine.pop(0)
      
      # Handle any additional args
      while ( len(commandLine) != 0 ):
        argument = commandLine.pop(0)

        # All of our args must start with '-'
        if not argument.startswith("-"):
          er = errors()
          er.invalidResourceArgs(self.mode)
          er.terminate()

        # If arg is '--release' 
        if argument == "--release":

          # "update-resource" does not recognize '--release' arg
          if self.mode == "update-resource":
            er = errors()
            er.invalidResourceArgs(self.mode)
            er.terminate()

          # Otherwise, set flag & see if a release name exists
          hasReleaseArg = True
          try: 
            releaseName = commandLine.pop(0).lower()
          except: 
            releaseName = ""

        # If arg is '--verbose' or '-vb', ignore it (we've already set our verbose-ness).
        if argument == "--verbose" or argument == "-vb":
          continue

        # If arg is ( ADD ANY NEW ARG HANDLING HERE )

        # If argument unrecognized
        else:
          er = errors()
          er.invalidResourceArgs(self.mode)
          er.terminate()
          
    # Return parsed results 
    return (resourceName, hasReleaseArg, releaseName)

  # Resolves resource alias
  #
  # If input is a normal resource name, just return it.
  # If input is an alias, return resource's actual name.
  # If input is not recognized, return empty string.
  def resolveAlias(self, possibleAlias) :
    for resource in conf.resources:
      if (possibleAlias == resource.name) or (possibleAlias in resource.aliases):
        return resource.name
    return ""        

  # Convenience method for running "system" calls. 
  # Adds the option to run in 'quiet' mode and suppress all output.
  def runCommand(self, command, quiet=False):                             # Final FIXME: change this to quiet=True
    if quiet:
      return subprocess.call(command.split(), stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))
    else:
      return subprocess.call(command.split(), stdout=sys.stdout, stderr=sys.stderr)

