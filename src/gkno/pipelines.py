#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import dataChecking
from dataChecking import checkDataType

import errors
from errors import *

import helpClass
from helpClass import *

import json
import os
import sys

class pipeline:
  def __init__(self):
    self.additionalFileDependencies = {}
    self.arguments                  = {}
    self.argumentInformation        = {}
    self.constructFilenames         = {}
    self.deleteFiles                = {}
    self.description                = ''
    self.errors                     = errors()
    self.hasInternalLoop            = False
    self.instances                  = {}
    self.isPipeline                 = False
    self.linkage                    = {}
    self.pipelineName               = ''
    self.shortForms                 = {}
    self.taskToTool                 = {}
    self.toolArgumentLinks          = {}
    self.toolsOutputtingToStream    = []
    self.workflow                   = []

    # Define the fields that are allowed for each argument in the linkage section of the
    # configuration file.  The Boolean value describes if the field is required or not.
    self.allowedLinkageFields                          = {}
    self.allowedLinkageFields['link to this task']     = True
    self.allowedLinkageFields['link to this argument'] = True
    self.allowedLinkageFields['json block']            = False
    self.allowedLinkageFields['extension']             = False

    # Define the allowed fields that can appear for each task in the 'additional dependencies' section.
    self.allowedDependenciesFields                = {}
    self.allowedDependenciesFields['task output'] = False

    # Define the fields that are allowed for each argument in the construct filenames section
    # of the configuration file.  The Boolean value describes if the field is required or not.
    self.allowedConstructFields                                    = {}
    self.allowedConstructFields['filename root']                   = True
    self.allowedConstructFields['filename root text']              = False
    self.allowedConstructFields['get root from task']              = False
    self.allowedConstructFields['get root from argument']          = False
    self.allowedConstructFields['remove input extension']          = False
    self.allowedConstructFields['additional text']                 = False
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

    # Check if the 'additional dependencies' section exists.  This defines files on which a tool
    # depends that are not explicitly supplied in a command line argument.
    if 'additional dependencies' in data: self.checkAdditionalDependencies(data['additional dependencies'], argumentInformation, verbose)

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
                  self.errors.missingRootInformationInConstruct(verbose, task, argument, 'remove input extension', self.pipelineFile)
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

        # Linked arguments can take more than one value.  In this case, the linkedTask and linkedArgument
        # may be lists.  If the linkedTask is a list, the linkedArgument must also be a list.  Store the
        # values and then check that they are valid.
        #
        # First deal with the case that 'link to this task' is a list, but the 'link to this argument' is not.
        linkedTaskList     = []
        linkedArgumentList = []
        if isinstance(linkedTask, list) and not isinstance(linkedArgument, list):
          self.errors.linkedTaskArgumentIsNotAList(verbose, task, argument, self.pipelineFile)
          self.errors.terminate()

        # Then deal with the case that 'link to this argument' is a list, but the 'link to this task' is not.
        elif isinstance(linkedArgument, list) and not isinstance(linkedTask, list):
          self.errors.linkedTaskArgumentIsNotAList(verbose, task, argument, self.pipelineFile)
          self.errors.terminate()

        # Next if both are lists,
        elif isinstance(linkedTask, list):
          if len(linkedTask) != len(linkedArgument):
            self.errors.linkedTaskArgumentIsNotAList(verbose, task, argument, self.pipelineFile)
            self.errors.terminate()

          for counter, value in enumerate(linkedTask):
            linkedTaskList.append(linkedTask[counter])
            linkedArgumentList.append(linkedArgument[counter])

        # And finally, if neither are lists.
        else:
          linkedTaskList.append(linkedTask)
          linkedArgumentList.append(linkedArgument)

        # Now check that all the values are valid.
        for counter, value in enumerate(linkedTaskList):
          linkedTask     = linkedTaskList[counter]
          linkedArgument = linkedArgumentList[counter]
          if linkedTask not in self.workflow:
            self.errors.invalidLinkedTask(verbose, task, argument, linkedTask, self.pipelineFile)
            self.errors.terminate()

          linkedTool     = self.taskToTool[linkedTask]
          if linkedArgument not in argumentInformation[linkedTool]:
            self.errors.invalidLinkedArgument(verbose, task, argument, linkedTask, linkedArgument, self.pipelineFile)
            self.errors.terminate()

      self.linkage[task] = linkage[task]
    self.jsonSections.remove('linkage')

  # Check the contents of the 'additional dependencies' section,
  def checkAdditionalDependencies(self, data, argumentInformation, verbose):

    # Check that the section is a dictionary.
    if not isinstance(data, dict):
      self.errors.pipelineSectionIsNotADictionary(verbose, 'additional dependencies', self.pipelineFile)
      self.errors.terminate()

    # Now loop over the tasks, checking that they are valid.
    for task in data:
      if task not in self.workflow:
        self.errors.taskNotInWorkflow(verbose, 'additional dependencies', task, self.pipelineFile)
        self.errors.terminate()

      for field in data[task]:

        # If the dependency comes from a previous task output, check that the task and
        # argument exist.
        if field == 'task output':
          if not isinstance(data[task][field], dict):
            text = 'additional dependencies -> ' + task + ' -> ' + field
            self.errors.pipelineSectionIsNotADictionary(verbose, text, self.pipelineFile)
            self.errors.terminate()

          for linkedTask in data[task][field]:
            if linkedTask not in self.workflow:
              self.errors.unknownTaskInAdditionalDepedenciesTaskOutput(verbose, task, linkedTask, self.pipelineFile)
              self.errors.terminate()

            # Check that the linkedTask is a list of arguments.
            if not isinstance(data[task][field][linkedTask], list):
              text = 'additional dependencies -> ' + task + ' -> ' + field + ' -> ' + linkedTask
              self.errors.pipelineSectionIsNotAList(verbose, text, self.pipelineFile)
              self.errors.terminate()

        # If the dependency is any additional files created by a tool.
        elif field == 'additional files from task':

          # Check that a list of valid tasks is supplied.
          if not isinstance(data[task][field], list):
            text = 'additional dependencies -> ' + task + ' -> ' + field
            self.errors.pipelineSectionIsNotAList(verbose, text, self.pipelineFile)
            self.errors.terminate()

          for linkedTask in data[task][field]:
            if linkedTask not in self.workflow:
              text = 'additional dependencies -> ' + task + ' -> ' + field
              self.errors.taskNotInWorkflow(verbose, text, linkedTask, self.pipelineFile)
              self.errors.terminate()

            if task not in self.additionalFileDependencies: self.additionalFileDependencies[task] = []
            self.additionalFileDependencies[task].append(linkedTask)

        else:
          self.errors.unrecognisedFieldInAdditionalDependencies(verbose, task, field, self.allowedDependenciesFields, self.pipelineFile)
          self.errors.terminate()

    self.jsonSections.remove('additional dependencies')

  # The arguments section is required and contains all the arguments allowed for the pipeline.
  def checkArguments(self, data, verbose):
    if 'arguments' not in data:
      text = 'This provides details of all the allowable command line arguments including which tasks in the ' + \
      'pipeline they are associated with.'
      self.errors.missingPipelineSection(verbose, 'arguments', text, self.pipelineFile)
      self.errors.terminate()

    for argument in data['arguments']:
      self.argumentInformation[argument] = data['arguments'][argument]

      # Check that a description of the argument is supplied.
      if 'description' not in self.argumentInformation[argument]:
        self.errors.pipelineArgumentMissingDescription(verbose, argument, self.pipelineFile)
        self.errors.terminate()

      # Check that the expected data type is included.
      if 'description' not in self.argumentInformation[argument]:
        self.errors.pipelineArgumentMissingType(verbose, argument, self.pipelineFile)
        self.errors.terminate()

      # Set the short form argument.
      if 'short form argument' in self.argumentInformation[argument]:
        shortForm                  = self.argumentInformation[argument]['short form argument']
        self.shortForms[shortForm] = argument
      else:
        self.errors.pipelineArgumentMissingShortForm(verbose, argument, self.pipelineFile)
        self.errors.terminate()

      # Check that the task and argument that this argument is linked to is defined.
      if 'link to this task' not in self.argumentInformation[argument]:
        self.errors.pipelineArgumentMissingInformation(verbose, argument, 'link to this task', self.pipelineFile)
        self.errors.terminate()

      # Check that the task being linked to exists in the workflow.
      else:
        linkedTask = self.argumentInformation[argument]['link to this task']
        if linkedTask not in self.workflow:
          self.errors.invalidLinkedTaskInArguments(verbose, linkedTask, self.pipelineFile)
          self.errors.terminate()

      if 'link to this argument' not in self.argumentInformation[argument]:
        self.errors.pipelineArgumentMissingInformation(verbose, argument, 'link to this argument', self.pipelineFile)
        self.errors.terminate()

      # If the 'required' field is provided, check that the value is a Boolean.
      if 'required' in self.argumentInformation[argument]:
        value = self.argumentInformation[argument]['required']
        if value == 'true' or value == 'True' or value == True: self.argumentInformation[argument]['required'] = True
        elif value == 'false' or value == 'False' or value == False: self.argumentInformation[argument]['required'] = False
        else:
          text = 'arguments -> ' + argument + ' -> required'
          self.errors.differentDataTypeInConfig(verbose, self.pipelineFile, '', text, type(self.argumentInformation[argument]['required']), bool)
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
