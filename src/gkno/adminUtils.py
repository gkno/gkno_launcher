#!/usr/bin/python

from __future__ import print_function
import sys


import conf

# Use file: gkno/conf/user_settings.json
#   to track resource usage, anything else?

class adminUtils:

    def __init__(self):
        self.resourceModes = [ "add-resource", "remove-resource" ]
        self.allModes      = self.resourceModes + [ "build", "update" ]
        self.isRequested   = False
        self.mode          = ""
        self.resourceName  = ""
        self.sourcePath    = ""

    def build(self):

        print("Building...", file = sys.stdout)

        # create 'conf/user_settings.json' if does not exist

        # for each tool in conf.tools 
        #    git initialize
        #    git pull
        #    status = tool.build()

        # for each resource in conf.resources
        #    if resource.isDefault
        #       self.addResource(resource.name)

        # 

        return 0

    def update(self):
        
        print("Updating...", file = sys.stdout)

        # 'git pull origin master'

        # for each tool in conf.tools
        #   git pull
        #   status = tool.build()

        # for each resource in user settings
        #   git pull

        return 0;

    def addResource(self, resourceName):

        print("Adding resource...", file = sys.stdout)

        # if resourceName already in userSettingsFile
        #    print 'gkno already exists' message # FIXME: what if it's not *actually* there
        #    return 0  # not failure
        #
        # for each resource in conf.resources:
        #    if resourceName == resource.name:
        #      git initialize, pull
        #      add to userSettingsFile
        #      if all ok, return 0

        # FIXME: remove later, only here temporarily
        return 0

        # Resource unknown
        return 1

    def removeResource(self):
        
        print("Removing resource...", file = sys.stdout)

        # for each resource in conf.resources:
        #    if self.resourceName == resource.name:
        #      git remote rm stuff
        #      local rm -rf cleanup
        #      if all ok, return 0

        # FIXME: remove later, only here temporarily
        return 0
    
        # Resource unknown
        return 1

    def printInvalidMode(self):
        print("Invalid mode", file = sys.stdout)
        # FIXME: implement me!
        pass

    def run(self, sourcePath):

        print("Running...", file = sys.stdout)

        # Sanity check
        if not self.isRequested: 
            # FIXME: raise error
            return 1

        # Store gkno source path for convenience
        self.sourcePath = sourcePath

        # Run requested admin operation
        if   self.mode == 'build'           : return self.build()
        elif self.mode == 'update'          : return self.update()
        elif self.mode == 'add-resource'    : return self.addResource(self.resourceName)
        elif self.mode == 'remove-resource' : return self.removeResource()
        else:
            self.printInvalidMode()
            return 1

