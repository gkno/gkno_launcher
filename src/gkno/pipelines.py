#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import errors
from errors import *

import helpClass
from helpClass import *

import json
import os
import sys

class pipeline:
  def __init__(self):
    self.errors                  = errors()
    self.toolArgumentLinks       = {}
    self.arguments               = {}
    self.argumentInformation     = {}
    self.constructFilenames      = {}
    self.deleteFiles             = {}
    self.description             = ''
    self.hasInternalLoop         = False
    self.instances               = {}
    self.isPipeline              = False
    self.linkage                 = {}
    self.pipelineName            = ''
    self.shortForms              = {}
    self.taskToTool              = {}
    self.toolsOutputtingToStream = []
    self.workflow                = []

    # Define the fields that are allowed for each argument in the linkage section of the
    # configuration file.  The Boolean value describes if the field is required or not.
    self.allowedLinkageFields                          = {}
    self.allowedLinkageFields['link to this task']     = True
    self.allowedLinkageFields['link to this argument'] = True
    self.allowedLinkageFields['json block']            = False
    self.allowedLinkageFields['extension']             = False

    # Define the fields that are allowed for each argument in the construct filenames section
    # of the configuration file.  The Boolean value describes if the field is required or not.
    self.allowedConstructFields                                    = {}
    self.allowedConstructFields['filename root']                   = True
    self.allowedConstructFields['filename root text']              = False
    self.allowedConstructFields['get root from task']              = False
    self.allowedConstructFields['get root from argument']          = False
    self.allowedConstructFields['remove input extension']          = False
    self.allowedConstructFields['additional text from parameters'] = False
    self.allowedConstructFields['output extension']                = False

  # Check that the pipeline configuration file exists.
  def checkPipelineExists(self, gknoHelp, pipelineFiles):
    if self.pipelineName + '.json' not in pipelineFiles.keys():
      if (gknoHelp.specificPipelineHelp) or (not gknoHelp.printHelp):
        gknoHelp.specificPipelineHelp = False
        gknoHelp.unknownPipeline      = True
        gknoHelp.pipelineHelp         = True
        gknoHelp.printHelp            = True

      return False
    else: return True

  # Parse through the pipeline configuration file and check that all necessary fields are
  # available and valid.  Store all of the data in data structures for later use.
  def checkConfigurationFile(self, gknoHelp, data, pipelineFiles, availableTools, argumentInformation, verbose):
    length = len(self.pipelineName + 'Executing pipeline: ') + 4
    text   = '=' * length

    # Put all of the sections of the json file into a list.  As each of the allowed sections
    # is checked, remove it from the list.  At the end of this routine, check if there are 
    # any values left in the list.  If so, these are entries unrecognised by gkno and an error
    # can be thrown.
    self.jsonSections = data.keys()

    # Check that the pipeline description is available.
    self.checkDescription(data, verbose)

    # Check that a workflow exists and that it is a list.
    self.checkWorkflow(data, verbose)

    # If an internal loop is defined for the pipeline, perform the necessary checks to ensure
    # that everything is valid and consistent.
    internalLoopTasks = self.checkInternalLoop(data, availableTools, verbose)

    # Check that there is a 'tools' section and that there is a named tool for each of the tasks.
    self.checkTools(data, availableTools, verbose)

    # If there are tools outputting to the stream, check that section is a list and that each element
    # in the list, is present in the workflow.
    self.checkToolsOutputtingToStream(data, verbose)

    # If the construct self.pipelineNames section is included, check that it is a dictionary of key/value pairs,
    # where all of the keys are the names of tasks.
    self.checkConstructFilenames(data, argumentInformation, verbose)

    # The linkage section describing how different tools are linked together in the pipeline is a
    # dictionary containing tasks in the workflow as keys.  Check that these are all valid tasks.
    if 'linkage' in data: self.checkLinkageSection(data['linkage'], argumentInformation, verbose)

    # The arguments section is required and contains all the arguments allowed for the pipeline.
    self.checkArguments(data, verbose)

    # If the section 'delete files' is present.  If so, check that it is a dictionary whose keys are
    # tasks present in the workflow.
    if 'delete files' in data: self.checkDeleteFiles(argumentInformation, data['delete files'], verbose)

    # If there are instances associated with the pipeline, ensure that this is a dictionary.
    self.checkInstances(data, verbose)

    # Check to see if the list 'jsonSections' is now empty.  If not, throw an error indicating
    # the unknown sections.
    if len(self.jsonSections) > 0:
      self.errors.unknownSectionsInPipelineConfig(True, self.jsonSections, self.pipelineFile)
      self.errors.terminate()

    return internalLoopTasks

  # Check that the pipeline description is available.
  def checkDescription(self, data, verbose):
    Tab = 1 if verbose else 0

    if 'description' not in data:
      text = 'A textual description of the pipeline for the help messages is required information.'
      self.errors.missingPipelineSection(verbose, 'description', text, self.pipelineFile)
      self.errors.terminate()

    self.description = data['description']
    self.jsonSections.remove('description')

  # Check that a workflow exists and that it is a list.
  def checkWorkflow(self, data, verbose):
    if 'workflow' not in data:
      text = 'This provides an ordered list of unique tasks to be performed.'
      self.errors.missingPipelineSection(verbose, 'workflow', text, self.pipelineFile)
      self.errors.terminate()

    if type(data['workflow']) != list:
      self.errors.pipelineSectionIsNotAList(verbose, 'workflow', self.pipelineFile)
      self.errors.terminate()

    # Check that all of the tasks in the workflow have unique names.
    tasks = []
    for task in data['workflow']:
      if task in tasks:
        self.errors.multipleTasksWithSameName(verbose, task, self.pipelineFile)
        self.errors.terminate()
      tasks.append(task)

    self.workflow = data['workflow']
    self.jsonSections.remove('workflow')

  # TODO Check that all aspects of the internal loop are checked.
  # Check that the internal loop information is valid.
  def checkInternalLoop(self, data, availableTools, verbose):
    internalLoopTasks = []
    if 'internal loop' in data:

      # First ensure that the 'internal loop' definition is a list and all of the tasks contained
      # in the list are defined in the workflow.
      if not isinstance(data['internal loop'], list):
        self.errors.pipelineSectionIsNotAList(verbose, 'internal loop', self.pipelineFile)
        self.errors.terminate()

      for task in data['internal loop']:
        if task not in self.workflow:
          self.errors.taskNotInWorkflow(verbose, 'internal loop', task, self.pipelineFile)
          self.errors.terminate()

      self.hasInternalLoop   = True
      internalLoopTasks = data['internal loop']
      self.jsonSections.remove('internal loop')

    return internalLoopTasks

  # Check that there is a 'tools' section and that there is a named tool for each of the tasks.
  def checkTools(self, data, availableTools, verbose):
    if 'tools' not in data:
      text = 'This defines which tools are associated with each task in the pipeline.'
      self.errors.missingPipelineSection(verbose, 'tools', text, self.pipelineFile)
      self.errors.terminate()

    if type(data['tools']) != dict:
      self.errors.pipelineSectionIsNotADictionary(verbose, 'tools', self.pipelineFile)
      self.errors.terminate()

    self.taskToTool = data['tools']
    for task in self.taskToTool:
      if task not in self.workflow:
        self.errors.taskNotInWorkflow(verbose, 'tools', task, self.pipelineFile)
        self.errors.terminate()

      if self.taskToTool[task] not in availableTools:
        self.errors.taskAssociatedWithNonExistentTool(verbose, task, self.taskToTool[task], self.pipelineFile)
        self.errors.terminate()

    self.jsonSections.remove('tools')

  # If there are tools outputting to the stream, check that section is a list and that each element
  # in the list, is present in the workflow.
  def checkToolsOutputtingToStream(self, data, verbose):
    if 'tools outputting to stream' in data:
      if type(data['tools outputting to stream']) != list:
        self.errors.pipelineSectionIsNotAList(verbose, 'tools outputting to stream', self.pipelineFile)
        self.errors.terminate()

      for task in data['tools outputting to stream']:
        if task not in self.workflow:
          self.errors.taskNotInWorkflow(verbose, 'tools outputting to stream', task, self.pipelineFile)
          self.errors.terminate()

      self.toolsOutputtingToStream = data['tools outputting to stream']
      self.jsonSections.remove('tools outputting to stream')

  # If the construct self.pipelineNames section is included, check that it is a dictionary of key/value pairs,
  # where all of the keys are the names of tasks.
  def checkConstructFilenames(self, data, argumentInformation, verbose):
    if 'construct filenames' in data:

      # Chech that the "construct filenames" section is a dictionary.
      if type(data['construct filenames']) != dict:
        self.errors.pipelineSectionIsNotADictionary(verbose, 'construct filenames', self.pipelineFile)
        self.errors.terminate()

      # Parse over each task included in the section.
      for task in data['construct filenames']:

        # Check that the task is valid.
        if task not in self.workflow:
          self.errors.taskNotInWorkflow(verbose, 'construct filenames', task, self.pipelineFile)
          self.errors.terminate()

        # Store the information about this task.
        self.constructFilenames[task] = data['construct filenames'][task]
      
        # For each argument, check that the argument exists and that the necessary information is present.
        tool = self.taskToTool[task]
        for argument in data['construct filenames'][task]:

          # Check that the argument is valid for the current task.
          if argument not in argumentInformation[tool]:
            self.errors.invalidArgumentInConstruct(verbose, task, argument, self.pipelineFile)
            self.errors.terminate()

          # Check for required fields.
          for field in self.allowedConstructFields:
            required = self.allowedConstructFields[field]
            if required and field not in data['construct filenames'][task][argument]:
              self.errors.missingFieldInConstruct(verbose, task, argument, field, self.pipelineFile)
              self.errors.terminate()

          # Check the contained information.
          for field in data['construct filenames'][task][argument]:

            # Check for unknown fields.
            if field not in self.allowedConstructFields:
              self.errors.unknownFieldInConstruct(verbose, task, argument, field, self.allowedConstructFields, self.pipelineFile)
              self.errors.terminate()

            # For each field, check that the data types are correct and that any additional fields required
            # are present (for example, if "filename root" is set to "from argument", the "get root from task"
            # and "get root from argument fields" must be present).
            # If the field is 'filename root', check that the value is valid.  This can take one of the following:
            #   a) from argument
            if field == 'filename root':
              allowedRootFields = []
              allowedRootFields.append('from argument')
              allowedRootFields.append('from text')

              # For 'from argument',
              if data['construct filenames'][task][argument][field] == 'from argument':
                if 'get root from task' not in data['construct filenames'][task][argument]:
                  text = 'get root from task'
                  self.errors.missingRootInformationInConstruct(verbose, task, argument, text, self.pipelineFile)
                  self.errors.terminate()
                if 'get root from argument' not in data['construct filenames'][task][argument]:
                  text = 'get root from argument'
                  self.errors.missingRootInformationInConstruct(verbose, task, argument, text, self.pipelineFile)
                  self.errors.terminate()
                if 'remove input extension' not in data['construct filenames'][task][argument]:
                  text = 'remove input extension'
                  self.errors.missingRootInformationInConstruct(verbose, task, argument, self.pipelineFile)
                  self.errors.terminate()

                # If the necessary fields are present, check that they are valid.
                linkedTask     = data['construct filenames'][task][argument]['get root from task']
                linkedArgument = data['construct filenames'][task][argument]['get root from argument']
                if linkedTask not in self.workflow:
                  text = task + ' -> ' + argument + ' -> get root from task -> ' + linkedTask
                  self.errors.taskNotInWorkflow(verbose, 'construct filenames', text, self.pipelineFile)
                  self.errors.terminate()

                linkedTool = self.taskToTool[linkedTask]
                if linkedArgument not in argumentInformation[linkedTool]:
                  self.errors.invalidRootArgumentInConstruct(verbose, task, argument, linkedArgument, self.pipelineFile)
                  self.errors.terminate()

                # Check that the remove input extension is a Boolean.
                if type(data['construct filenames'][task][argument]['remove input extension']) != bool:
                  value = data['construct filenames'][task][argument]['remove input extension']
                  self.errors.invalidRootDataTypeInConstruct(verbose, task, argument, value, self.pipelineFile)
                  self.errors.terminate()

              # If the "filename root" field takes the value "from text", the field "filename root text" must
              # be present and contain the text to use as the filename root.
              elif data['construct filenames'][task][argument][field] == 'from text':
                if 'filename root text' not in data['construct filenames'][task][argument]:
                  self.errors.filenameRootTextMissing(verbose, task, argument, self.pipelineFile)
                  self.errors.terminate()

              # If the "filename root" field takes an unknown value.
              else:
                value = data['construct filenames'][task][argument][field]
                self.errors.unknownRootValue(verbose, task, argument, value, allowedRootFields, self.pipelineFile)
                self.errors.terminate()

            # If the field 'additional text from parameters' exists, check the contents of this section.
            elif field == 'additional text from parameters':
              additionalText = []
              if type(data['construct filenames'][task][argument][field]) != dict:
                self.errors.additionalTextInConstructNotADict(verbose, task, argument, self.pipelineFile)
                self.errors.terminate()

              if 'order' not in data['construct filenames'][task][argument][field]:
                self.errors.orderMissingInAdditionalTextInConstruct(verbose, task, argument, self.pipelineFile)
                self.errors.terminate()

              if type(data['construct filenames'][task][argument][field]['order']) != list:
                self.errors.additionalTextOrderInConstructNotAList(verbose, task, argument, self.pipelineFile)
                self.errors.terminate()

              # Get the names of all the pieces of text that will be added to the filename.
              for name in data['construct filenames'][task][argument][field]['order']: additionalText.append(name)

              # Each field in the order section, must be defined with a link to an argument.  Check that they
              # are and check the data types.
              for additional in additionalText:
                if additional not in data['construct filenames'][task][argument][field] and additional != 'filename root':
                  self.errors.missingTextDefinitionInConstruct(verbose, task, argument, additional, self.pipelineFile)
                  self.errors.terminate()

                # If the value of additional is 'filename root', check that the accompanying value is valid.  This field
                # can take one of the following values:
                #   a) from argument
                elif additional != 'filename root':
                  if 'get parameter from task' not in data['construct filenames'][task][argument][field][additional]:
                    text = 'get parameter from task'
                    self.errors.missingFieldInTextDefinitionInConstruct(verbose, task, argument, additional, text, self.pipelineFile)
                    self.errors.terminate()
                  else:
                    if data['construct filenames'][task][argument][field][additional]['get parameter from task'] not in self.workflow:
                      text        = 'construct filenames -> ' + task + ' -> ' + argument + ' -> additional text from parameters -> ' + additional
                      invalidTask = data['construct filenames'][task][argument][field][additional]['get parameter from task']
                      self.errors.taskNotInWorkflow(verbose, text, invalidTask, self.pipelineFile)
                      self.errors.terminate()
                  if 'get parameter from argument' not in data['construct filenames'][task][argument][field][additional]:
                    text = 'get parameter from argument'
                    self.errors.missingFieldInTextDefinitionInConstruct(verbose, task, argument, additional, text, self.pipelineFile)
                    self.errors.terminate()
                  else:
                    linkedTask     = data['construct filenames'][task][argument][field][additional]['get parameter from task']
                    linkedArgument = data['construct filenames'][task][argument][field][additional]['get parameter from argument']
                    linkedTool     = self.taskToTool[linkedTask]
                    if linkedArgument not in argumentInformation[linkedTool]:
                      self.errors.invalidArgumentInConstructAdditional(verbose, task, argument, additional, linkedTask, linkedArgument, self.pipelineFile)
                      self.errors.terminate()

                  # Check that the 'remove extension' field is also present and is a Boolean.
                  if 'remove extension' not in data['construct filenames'][task][argument][field][additional]:
                    text = 'remove extension'
                    self.errors.missingFieldInTextDefinitionInConstruct(verbose, task, argument, additional, text, self.pipelineFile)
                    self.errors.terminate()
                  if type(data['construct filenames'][task][argument][field][additional]['remove extension']) != bool:
                    value = data['construct filenames'][task][argument][field][additional]['remove extension']
                    self.errors.invalidAdditionalDataTypeInConstruct(verbose, task, argument, additional, value, self.pipelineFile)
                    self.errors.terminate()

              # Check that no fields are defined that are not included in the ordself.errors.
              for additional in data['construct filenames'][task][argument][field]:
                if additional not in additionalText and additional != 'order' and additional != 'separator':
                  self.errors.definedTextNotInOrderInConstruct(verbose, task, argument, additional, self.pipelineFile)
                  self.errors.terminate()

      self.jsonSections.remove('construct filenames')

  # Check the contents of the linkage section of the configuration file.
  def checkLinkageSection(self, linkage, argumentInformation, verbose):
    if type(linkage) != dict:
      self.errors.pipelineSectionIsNotADictionary(False, 'linkage', self.pipelineFile)
      self.errors.terminate()

    for task in linkage:
      if task not in self.workflow:
        self.errors.taskNotInWorkflow(verbose, 'linkage', task, self.pipelineFile)
        self.errors.terminate()

      # Check that the argument is a valid argument for this task.  Also, check that each argument has the 
      #'link to this task' and 'link to this argument' values set, and check that they point to real tool arguments.
      for argument in linkage[task]:
  
        # Check for required fields.
        for field in self.allowedLinkageFields:
          required = self.allowedLinkageFields[field]
          if required and field not in linkage[task][argument]:
            self.errors.missingFieldInLinkage(verbose, task, argument, field, self.pipelineFile)
            self.errors.terminate()

        tool = self.taskToTool[task]

        # If the argument is 'json parameteres', check that the 'link to this task', 'link to this
        # argument' and 'json block' fields are present and valid.
        if argument == 'json parameters':
          if 'json block' not in linkage[task][argument]:
            self.errors.missingFieldInLinkage(verbose, task, argument, 'json block', self.pipelineFile)
            self.errors.terminate()

          linkedTask     = linkage[task][argument]['link to this task']
          linkedArgument = linkage[task][argument]['link to this argument']
          if linkedTask not in self.workflow:
            self.errors.invalidLinkedTask(verbose, task, argument, linkedTask, self.pipelineFile)
            self.errors.terminate()
          linkedTool = self.taskToTool[task]
          if linkedArgument not in argumentInformation[linkedTool]:
            self.errors.invalidLinkedArgument(verbose, task, argument, linkedTask, linkedArgument, self.pipelineFile)
            self.errors.terminate()

        elif argument not in argumentInformation[tool]:
          self.errors.invalidArgumentInLinkage(verbose, task, argument, self.pipelineFile)
          self.errors.terminate()

        # Loop over the fields for this argument.  The only allowed fields are 'link to this task', 'link
        # to this argument' and 'json block'.  If anything else is observed, terminate.
        for field in linkage[task][argument]:
          if field not in self.allowedLinkageFields:
            self.errors.unknownFieldInLinkage(verbose, task, argument, field, self.allowedLinkageFields, self.pipelineFile)
            self.errors.terminate()

        # Check that the task and argument to which this argument is linked, exists.
        linkedTask     = linkage[task][argument]['link to this task']
        linkedArgument = linkage[task][argument]['link to this argument']
        if linkedTask not in self.workflow:
          self.errors.invalidLinkedTask(verbose, task, argument, linkedTask, self.pipelineFile)
          self.errors.terminate()

        linkedTool     = self.taskToTool[linkedTask]
        if linkedArgument not in argumentInformation[linkedTool]:
          self.errors.invalidLinkedArgument(verbose, task, argument, linkedTask, linkedArgument, self.pipelineFile)
          self.errors.terminate()

      self.linkage[task] = linkage[task]
    self.jsonSections.remove('linkage')

  # The arguments section is required and contains all the arguments allowed for the pipeline.
  def checkArguments(self, data, verbose):
    if 'arguments' not in data:
      text = 'This provides details of all the allowable command line arguments including which tasks in the ' + \
      'pipeline they are associated with.'
      self.errors.missingPipelineSection(verbose, 'arguments', text, self.pipelineFile)
      self.errors.terminate()

    for argument in data['arguments']:
      self.argumentInformation[argument] = data['arguments'][argument]
      if 'short form argument' in self.argumentInformation[argument]:
        shortForm                  = self.argumentInformation[argument]['short form argument']
        self.shortForms[shortForm] = argument

      # Check that the task and argument that this argument is linked to is defined.
      if 'link to this task' not in self.argumentInformation[argument]:
        self.errors.pipelineArgumentMissingInformation(verbose, argument, 'link to this task', self.pipelineFile)
        self.errors.terminate()

      if 'link to this argument' not in self.argumentInformation[argument]:
        self.errors.pipelineArgumentMissingInformation(verbose, argument, 'link to this argument', self.pipelineFile)
        self.errors.terminate()

    self.jsonSections.remove('arguments')

  # If the section 'delete files' is present.  If so, check that it is a dictionary whose keys are
  # tasks present in the workflow.
  def checkDeleteFiles(self, argumentInformation, data, verbose):
    required = []
    required.append('output extension')
    required.append('delete after task')

    if type(data) != dict:
      self.errors.pipelineSectionIsNotADictionary(verbose, 'delete files', self.pipelineFile)
      self.errors.terminate()

    # Check that the contents are tasks in the pipeline workflow.
    for task in data:
      if task not in self.workflow:
        self.errors.taskNotInWorkflow(verbose, 'delete files', task, self.pipelineFile)
        self.errors.terminate()

      # Check that for each task, there are defined valid arguments for the tool as well
      # as which task need to be completed prior to file deletion.  This task must also
      # be valid.
      tool                   = self.taskToTool[task]
      self.deleteFiles[task] = []
      for argument in data[task]:
        if argument not in argumentInformation[tool]:
          self.errors.unknownArgumentInDeleteFiles(verbose, task, tool, argument, self.pipelineFile)
          self.errors.terminate()

        # Check for unknown fields.
        for field in data[task][argument]:
          if field not in required:
            self.errors.unknownFieldInDeleteFiles(verbose, task, argument, field, self.pipelineFile)
            self.errors.terminate()

        # Ensure the delete after task field is present.
        if 'delete after task' not in data[task][argument]:
          self.errors.deleteAfterTaskMissing(verbose, task, argument, self.pipelineFile)
          self.errors.terminate()

        # If the output extensions fiels exists, check that it is a list and then find out how
        # many files are to be deleted.
        if 'output extension' in data[task][argument]:
          if type(data[task][argument]['output extension']) != list:
            self.errors.outputExtensionNotAListInDeleteFiles(verbose, task, argument, self.pipelineFile)
            self.errors.terminate()

          # Now ensure that the 'delete after task' field is also a list with the same
          # number of elements.

          if type(data[task][argument]['delete after task']) != list:
            self.errors.deleteAfterTaskNotAList(verbose, task, argument, self.pipelineFile)
            self.errors.terminate()

          if len(data[task][argument]['output extension']) != len(data[task][argument]['delete after task']):
            self.errors.listsDifferentSizeInDeleteFiles(verbose, task, argument, self.pipelineFile)
            self.errors.terminate()

          for deleteAfterTask, extension in zip(data[task][argument]['delete after task'], data[task][argument]['output extension']):
            if deleteAfterTask not in self.workflow:
              text = 'delete files -> ' + task + ' -> ' + argument + ' -> delete after task'
              self.errors.taskNotInWorkflow(verbose, text, deleteAfterTask, self.pipelineFile)
              self.errors.terminate()

            # Check that the extension is allowed for this tool.
            allowedExtension = argumentInformation[tool][argument]['extension']
            if allowedExtension == 'stub':
              correct = False
              for extensionValue in argumentInformation[tool][argument]['outputs']:
                if extension == extensionValue:
                  correct = True
                  break
              if not correct:
                self.errors.invalidExtensionInDeleteFiles(verbose, task, argument, extension, self.pipelineFile)
                self.errors.terminate()
            else:
              if allowedExtension != extension:
                self.errors.invalidExtensionInDeleteFiles(verbose, task, argument, extension, self.pipelineFile)
                self.errors.terminate()
            self.deleteFiles[task].append((argument, deleteAfterTask, extension))

        # If the 'output extension' field is not present, then there only needs to be the
        # 'delete after task'.  This is for the case that the output argument produces a
        # single file and so a list of output extensions is not required.
        else:
          deleteAfterTask = data[task][argument]['delete after task']
          if deleteAfterTask not in self.workflow:
            text = 'delete files -> ' + task + ' -> ' + argument + ' -> delete after task'
            self.errors.taskNotInWorkflow(verbose, text, deleteAfterTask, self.pipelineFile)
            self.errors.terminate()
          self.deleteFiles[task].append((argument, deleteAfterTask, ''))
          
    self.jsonSections.remove('delete files')

  # If there are instances associated with the pipeline, ensure that this is a dictionary.
  def checkInstances(self, data, verbose):
    if 'instances' not in data:
      text = 'A section containing instance information is required.  If no instance is requested, the \'default\' instance ' + \
      'is used (this need not set any parameters).'
      self.errors.missingPipelineSection(verbose, 'instances', text, self.pipelineFile)
      self.errors.terminate()
    else: instances = data['instances']

    if type(instances) != dict:
      self.errors.pipelineSectionIsNotADictionary(verbose, 'instances', self.pipelineFile)
      self.errors.terminate()

    # Check that each instance has a unique name and contains a description.
    for instance in instances:
      if 'description' not in instances[instance]:
        self.errors.noInstanceDescription(verbose, instance, self.pipelineFile)
        self.errors.terminate()

    self.instances = instances
    self.jsonSections.remove('instances')

  # Set up a dictionary that links the pipeline command line argument with the tool to which it points.
  # If there is a problem with one of the arguments for a specific tool, this dictionary allows quick
  # look up of the pipeline argument that is used to set it.
  def setArgumentLinks(self):
    for argument in self.argumentInformation: 
      linkedTask = self.argumentInformation[argument]['link to this task'] 
      if linkedTask != 'pipeline': 
        linkedArgument = self.argumentInformation[argument]['link to this argument'] 
        if linkedTask not in self.toolArgumentLinks: self.toolArgumentLinks[linkedTask] = {} 

        # Find the short form of the argument.
        shortForm = self.argumentInformation[argument]['short form argument'] if 'short form argument' in self.argumentInformation[argument] else ''
        self.toolArgumentLinks[linkedTask][linkedArgument] = argument, shortForm

  # After the json file has been parsed into the self.information structure, add some
  # pipeline specific values.
  def addPipelineSpecificOptions(self):

    # The verbose arguments allows the user to request that information is or is not
    # written to the screen as the pipeline runs.
    self.argumentInformation['--verbose']                        = {}
    self.argumentInformation['--verbose']['description']         = 'Boolean to determine if verbose information should be output.  Default: True'
    self.argumentInformation['--verbose']['link to this task']   = 'pipeline'
    self.argumentInformation['--verbose']['short form argument'] = '-vb'
    self.argumentInformation['--verbose']['type']                = 'bool'
    self.argumentInformation['--verbose']['default']             = True
    self.shortForms['-vb']                                       = '--verbose'
    self.arguments['--verbose']                                  = True

    self.argumentInformation['--input-path']                        = {}
    self.argumentInformation['--input-path']['description']         = 'Path for input files if not defined.  Default: current directory'
    self.argumentInformation['--input-path']['link to this task']   = 'pipeline'
    self.argumentInformation['--input-path']['short form argument'] = '-ip'
    self.argumentInformation['--input-path']['type']                = 'string'
    self.argumentInformation['--input-path']['default']             = '$(PWD)'
    self.shortForms['-ip']                                          = '--input-path'
    self.arguments['--input-path']                                  = '$(PWD)'

    self.argumentInformation['--output-path']                        = {}
    self.argumentInformation['--output-path']['description']         = 'Path for output files if not defined.  Default: current directory'
    self.argumentInformation['--output-path']['link to this task']   = 'pipeline'
    self.argumentInformation['--output-path']['short form argument'] = '-op'
    self.argumentInformation['--output-path']['type']                = 'string'
    self.argumentInformation['--output-path']['default']             = '$(PWD)'
    self.shortForms['-op']                                           = '--output-path'
    self.arguments['--output-path']                                  = '$(PWD)'

    self.argumentInformation['--execute']                        = {}
    self.argumentInformation['--execute']['description']         = 'Boolean to determine if the Makefile should be executed.  Default: True'
    self.argumentInformation['--execute']['link to this task']   = 'pipeline'
    self.argumentInformation['--execute']['short form argument'] = '-ex'
    self.argumentInformation['--execute']['type']                = 'bool'
    self.argumentInformation['--execute']['default']             = True
    self.shortForms['-ex']                                       = '--execute'
    self.arguments['--execute']                                  = True

    self.argumentInformation['--export-instance']                        = {}
    self.argumentInformation['--export-instance']['description']         = 'Export instance information to a new configuration file of this name.'
    self.argumentInformation['--export-instance']['link to this task']   = 'pipeline'
    self.argumentInformation['--export-instance']['short form argument'] = '-ei'
    self.argumentInformation['--export-instance']['type']                = 'string'
    self.argumentInformation['--export-instance']['default']             = ''
    self.shortForms['-ei']                                               = '--export-instance'
    self.arguments['--export-instance']                                  = ''

    self.argumentInformation['--multiple-runs']                        = {}
    self.argumentInformation['--multiple-runs']['description']         = 'Run the pipeline multiple times using the inputs defined in this file.'
    self.argumentInformation['--multiple-runs']['link to this task']   = 'pipeline'
    self.argumentInformation['--multiple-runs']['short form argument'] = '-mr'
    self.argumentInformation['--multiple-runs']['type']                = 'string'
    self.argumentInformation['--multiple-runs']['default']             = ''
    self.shortForms['-mr']                                             = '--multiple-runs'
    self.arguments['--multiple-runs']                                  = ''

    self.argumentInformation['--internal-loop']                        = {}
    self.argumentInformation['--internal-loop']['description']         = 'Loop over a subsection of the pipeline.'
    self.argumentInformation['--internal-loop']['link to this task']   = 'pipeline'
    self.argumentInformation['--internal-loop']['short form argument'] = '-il'
    self.argumentInformation['--internal-loop']['type']                = 'string'
    self.argumentInformation['--internal-loop']['default']             = ''
    self.shortForms['-il']                                             = '--internal-loop'
    self.arguments['--internal-loop']                                  = ''

    self.argumentInformation['--number-jobs']                        = {}
    self.argumentInformation['--number-jobs']['description']         = 'The number of parallel jobs to be used (only valid in conjunction with ' + \
    'the --internal-loop option).'
    self.argumentInformation['--number-jobs']['link to this task']   = 'pipeline'
    self.argumentInformation['--number-jobs']['short form argument'] = '-nj'
    self.argumentInformation['--number-jobs']['type']                = 'integer'
    self.argumentInformation['--number-jobs']['default']             = '1'
    self.shortForms['-nj']                                             = '--number-jobs'
    self.arguments['--number-jobs']                                  = ''

    self.argumentInformation['--task-stdout']                        = {}
    self.argumentInformation['--task-stdout']['description']         = 'Generate a stdout and stderr for each task.'
    self.argumentInformation['--task-stdout']['link to this task']   = 'pipeline'
    self.argumentInformation['--task-stdout']['short form argument'] = '-ts'
    self.argumentInformation['--task-stdout']['type']                = 'bool'
    self.argumentInformation['--task-stdout']['default']             = False
    self.shortForms['-ts']                                           = '--task-stdout'
    self.arguments['--task-stdout']                                  = False

    self.argumentInformation['--instance']                        = {}
    self.argumentInformation['--instance']['description']         = 'Generate a stdout and stderr for each task.'
    self.argumentInformation['--instance']['link to this task']   = 'pipeline'
    self.argumentInformation['--instance']['short form argument'] = '-is'
    self.argumentInformation['--instance']['type']                = 'string'
    self.argumentInformation['--instance']['default']             = ''
    self.shortForms['-is']                                        = '--instance'
    self.arguments['--instance']                                  = ''

  # Modify pipeline information to handle an individual tool.
  def setupIndividualTool(self, tool, verbose):
    self.workflow.append(tool)
    text = '=' * (len(tool) + 20)
    if verbose:
      print(text, file = sys.stdout)
      print('Executing tool: ', tool, sep = '', file = sys.stdout)
      print(text, file = sys.stdout)
      print(file = sys.stdout)

    return 'tools/' + tool

  # Use the 'linkage' section of the pipeline configuration file to set all
  # parameters that depend on other tools.
  def toolLinkage(self, task, tool, argumentInformation, arguments, usingInternalLoop, iTasks, numberOfIterations, verbose):

    # Work through each argument in turn and identify all of the input and output files.
    # For non-input/output files, just check for links to other tools.
    hasLinkageInformation = True if len(self.linkage.keys()) != 0 else False
    if hasLinkageInformation: 
      taskLinkage = True if task in self.linkage else False
      if taskLinkage:

        # Link together parameters.
        for argument in self.linkage[task]:

          # Check if this argument is linked to any other commands.
          argumentLinkage = True if argument in self.linkage[task] else False
          if argumentLinkage:
            targetTask     = self.linkage[task][argument]['link to this task']
            targetArgument = self.linkage[task][argument]['link to this argument']

            # For tasks that are not part of the internal loop (i.e. they are only run once),
            # set up linkage.
            if targetTask not in iTasks or not usingInternalLoop:
              targetValue = []
              if targetArgument in arguments[targetTask][0]: targetValue.append(deepcopy(arguments[targetTask][0][targetArgument]))
              else: targetValue.append([])

            # If the task is in the internal loop, this task will have multiple iterations with different
            # input files that can be run in parallel.
            else:
              targetValue = []
              if targetTask in arguments:
                for iteration in arguments[targetTask]:
                  targetValue.append(deepcopy(iteration[targetArgument]))
              else:
                for counter in range(0, numberOfIterations): targetValue.append([])

            # If an extension needs to be added to the values, add it here.
            if 'extension' in self.linkage[task][argument]:
              if len(targetValue) != 0:
                for counterA, iteration in enumerate(targetValue):
                  for counterB, value in enumerate(iteration): targetValue[counterA][counterB] += deepcopy(self.linkage[task][argument]['extension'])

            # Now update the arguments to include the linked arguments.  There are four possible cases:
            # 1. Both the task in question and the targetTask are not in the internal loop,
            # 2. They both are,
            # 3. The task is and the targetTask isn't,
            # 4. The task isn't and the targetTask isn't.
            #
            # Handle each case individually.
            #
            # If neither of the tasks are in the internal loop, there is only one set of parameters
            # associated with each task, so the zeroth iteration can be used for both.
            if (task not in iTasks and targetTask not in iTasks) or not usingInternalLoop:
              arguments[task][0][argument] = deepcopy(targetValue[0])

            # If both tasks are in the internal loop, then both have n sets of parameters for the
            # n interation in the internal loop.  This means that the nth value in the targetTask
            # argument can be mapped to the nth value in the current task.
            elif task in iTasks and targetTask in iTasks:
              for counter in range(0, numberOfIterations): arguments[task][counter][argument] = deepcopy(targetValue[counter])

            # If the task is in the internal loop, but the targetTask isn't, then this means that all
            # of the n iterations of parameters for this task take the same value from the target.  This
            # means that the zeroth iteration of the target can be mapped to all n iterations for the
            # task.
            elif task in iTasks and targetTask not in iTasks:
              for counter in range(0, numberOfIterations): arguments[task][counter][argument] = deepcopy(targetValue[0])

            # Finally, if the task is not in the internal loop, but the targetTask is, then this is the
            # first task occuring outside of the internal loop.  If this task is linked to a targetTask
            # within the loop, then it is taking the outputs from all n iterations of the targetTask.
            # This means that the argument being populated must be capable of receiving multiple
            # values.  This is checked and if so, the argument is populated with all of the outputs from
            # the n iterations of the targetTask.
            elif task not in iTasks and targetTask in iTasks:
              for counter in range(0, numberOfIterations):
                for value in targetValue[counter]: arguments[task][0][argument].append(value)
