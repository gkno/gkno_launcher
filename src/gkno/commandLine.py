#!/usr/bin/python

from __future__ import print_function
import sys

import gknoErrors
from gknoErrors import *

import files
from files import *

class commandLine:

  # Constructor.
  def __init__(self):
    self.arguments          = {}
    self.argumentDictionary = {}
    self.argumentList       = []
    self.argumentsToNodes   = []
    self.errors             = gknoErrors()
    self.linkedArguments    = {}
    self.mode               = 'help'
    self.uniqueArguments    = {}

  # If an admin operation has been requested, check which admin mode is required.
  def isAdminMode(self, adminModes):
    try:
      if sys.argv[1] in adminModes: return True
    except: return False

  # Check if a mode has been defined.  The mode is either 'pipe', 'run-test' or
  # a tool name.  If nothing is set, then no mode is chosen and the general help
  # message will be displayed.
  def setMode(self, isAdmin):
    isPipeline = False

    try: argument = sys.argv[1]
    except: return False

    # If help is requested, a mode isn't set.
    if isAdmin: self.mode = 'admin'
    elif argument == '-h' or argument == '--help': self.mode = 'help'
    elif argument == 'pipe':
      self.mode  = 'pipeline'
      isPipeline = True
    elif argument == 'run-test':
      self.mode = 'test'
      isPipeline = True
    else: self.mode = 'tool'

    return isPipeline

  # If gkno is being run in pipeline mode, get the name of the pipeline.
  def getPipelineName(self, isPipeline):
    if isPipeline:
      try: return sys.argv[2]
      except: return None

    # If running in tool mode, return the name of the tool.
    else:
      try: return sys.argv[1]
      except: return None

  # Check to see if the verbose argument is set.
  def checkVerbose(self, graph, config, admin):
    for count, argument in enumerate(sys.argv[1:]):
      if argument == '--verbose' or argument == '-vb':
        try: value = sys.argv[count + 2]
        except: value = ''

        # Check the supplied value.
        if value == 'false' or value == 'False': isVerbose = False
        elif value == 'true' or value == 'True':
          isVerbose       = True
          admin.isVerbose = True
        else:
          # TODO ERROR
          print('ERROR GETTING VERBOSE - commands.checkVerbose')
          self.errors.terminate()

        # Update the 'GKNO-VERBOSE' node.
        config.nodeMethods.addValuesToGraphNode(graph, 'GKNO-VERBOSE', [isVerbose], 'replace')

        return isVerbose

    return True

  # Parse through the command line and put all of the arguments into a list.
  def getCommandLineArguments(self, graph, config, gknoConfig, tool, isPipeline, verbose):
    count = 1
    while True:
      try: argument = sys.argv[count]
      except: break

      # The command line will include an instruction on whether to run a pipe or the name of the
      # tool.  Ignore this argument.
      if argument != tool and argument != 'pipe' and argument != 'run-test':

        # Check the next argument on the command line.  If it does not begin with a '-', then this
        # is assumed to be a value that goes with the current arguments.  Add the pair to the list
        # of arguments as a tuple.
        try: nextArgument = sys.argv[count + 1]
        except: nextArgument = '-'
  
        # If arguments for a task within the pipeline are being set on the command line, all of the
        # task specific arguments must be contained within square brackets.  If the nextArgument is
        # identified as beginning with a square bracket, find the end of the task specific commands.
        if nextArgument.startswith('['): count, nextArgument = self.checkForTaskCommands(count, nextArgument)
  
        # Check if the argument is a gkno specific argument.
        pipelineArgument = gknoConfig.checkPipelineArgument(graph, config, argument)
        if pipelineArgument != None:
          if pipelineArgument not in self.argumentDictionary: self.argumentDictionary[pipelineArgument] = []
          if nextArgument.startswith('-'): self.argumentDictionary[pipelineArgument].append('')
          else:
            self.argumentDictionary[pipelineArgument].append(nextArgument)
            count += 1

        else:

          # Check if the next argument starts with a '-'.  If so, the next argument on the command line
          # is not a value to accompany this argument, but is a new argument.  This is either because
          # the current argument is a flag or the argument is the name of a task within the pipeline.
          # If the argument is the name of a task in the workflow, the next entry on the command line
          # should be the value for this argument.
          if nextArgument.startswith('-'):
    
            # Check if the argument is the name of a task.
            task = ''
            if argument.startswith('-'): task = argument[1:]
            if argument.startswith('--'): task = argument[2:]
    
            isTask = False
            if task in graph.nodes(data = False):
    
              # The task is a node in the pipeline, but check that the node is a task node.
              if config.nodeMethods.getGraphNodeAttribute(graph, task, 'nodeType') == 'task':
    
                if argument not in self.argumentDictionary: self.argumentDictionary[argument] = []
                self.argumentDictionary[argument].append(nextArgument)
                count += 1
                isTask = True
    
            # Deal with arguments that are not the names of tasks.
            if not isTask:
  
              # If a pipeline is being run, check the arguments against those allowed by the
              # pipeline confuguration file.
              if isPipeline: longForm = config.pipeline.getLongFormArgument(graph, argument)
  
              # If gkno is being run in tool mode, check the arguments against those allowed by
              # the tool.
              else: longForm = config.tools.getLongFormArgument(tool, argument)
  
              # Update the argumentDictionary.
              if longForm not in self.argumentDictionary: self.argumentDictionary[longForm] = []
              self.argumentDictionary[longForm].append('')
    
          else:
            if isPipeline: longForm = config.pipeline.getLongFormArgument(graph, argument)
            else: longForm = config.tools.getLongFormArgument(tool, argument)
  
            # Update the argumentDictionary.
            if longForm not in self.argumentDictionary: self.argumentDictionary[longForm] = []
            self.argumentDictionary[longForm].append(nextArgument)
            count += 1
      count += 1

  # Check for arguments for tasks within the pipeline.
  def checkForTaskCommands(self, count, nextArgument):
  
    # First check if nextArgument ends with a ']'.  If there is only a single command in the
    # square brackets, the command is a flag and no spaces are included, this woule be the case.
    if nextArgument.endswith(']'):
      nextArgument = nextArgument[1:len(nextArgument) - 1]
  
    else:
      taskArgumentCounter = 2
      while True:
        try: buildTaskArguments = sys.argv[count + taskArgumentCounter]
        except: self.errors.hasError = True
    
        # If the square brackets aren't closed, terminate.
        if self.errors.hasError:
          self.errors.unterminatedTaskSpecificOptions(verbose, argument)
          self.errors.terminate()
    
        nextArgument += ' ' + buildTaskArguments
        if not buildTaskArguments.endswith(']'): taskArgumentCounter += 1
        else:
         count += taskArgumentCounter - 1
    
         # Strip off the square brackets.
         nextArgument = nextArgument[1:len(nextArgument) - 1]
         break

    return count, nextArgument

  # Check if an instance was defined and return the instance name.  If no instance was requested,
  # return 'default'.
  def getInstanceName(self):
    if '--instance' in self.argumentDictionary:

      # If multiple instances were specified, fail.
      if len(self.argumentDictionary['--instance']) != 1:
        # TODO SORT ERRORS
        print('Multiple instances specified on the command line.')
        self.errors.terminate()

      return self.argumentDictionary['--instance'][0]

    else: return 'default'

  # Check for lists of input files and add any to the argumentDictionary structure.
  def checkForInputLists(self, config):
    for argument in self.argumentDictionary:
      filename = './' + self.argumentDictionary[argument][0]

      # Read in all of the files, check that they end with the correct extension and
      # add to the argumentDictionary.
      try: filenames = [filename.strip() for filename in open(filename)]
      except:
        print('failed to open ', filename)
        self.errors.terminate()

      # Get the argument that is to be used for these filenames.
      extension = config.tools.getArgumentData(tool, argument, '')
      for filename in filenames:
        print(filename)
    exit(0)

  # Attach the values supplied on the command line to the nodes.
  def attachPipelineArgumentsToNodes(self, graph, config, gknoConfig):
    for argument in self.argumentDictionary:

      # The argument supplied can either be an argument defined in the pipeline configuration
      # file, or the name of a task in the pipeline.  First check to see if the argument is
      # defined in the pipeline configuration, then if it is a task and if neither, fail.
      nodeID = config.pipeline.isArgumentAPipelineArgument(argument)
      if nodeID == None:

        # Check if this argument is a gkno argument defined in the gkno configuration file.  If
        # so, there exists a 'floating' node in the graph for this argument.
        nodeID = gknoConfig.getNodeForGknoArgument(graph, config, argument)

        if nodeID == None:
          taskArgument = argument            
          if taskArgument.startswith('--'): taskArgument = argument[2:len(argument)]
          if taskArgument.startswith('-'): taskArgument = argument[1:len(argument)]
          if taskArgument in graph.nodes(data = False): nodeID = taskArgument

      # If the command line argument does not correspond to a node, fail.
      if nodeID == None:
        #TODO DAEL WITH ERROR
        print('unknown command:', argument)
      else:

        # TODO Deal with multiple runs and parallel execution loops.
        hasMultipleRuns      = False
        hasParallelExecution = False
        if hasMultipleRuns or hasParallelExecution:
          print('Not yet handled multiple runs or parallel execution.')

        # Handle command line arguments that correspond to a data node first.  Deal with arguments
        # pointing to a task node afterwards.
        if not config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'nodeType') == 'task':

          #TODO ASSUMING THAT CREATING ADDITIONAL NODES FOR ARGUMENTS POINTING TO NODES WITH PREDECESSORS
          # WORKED, IMPLEMENT HERE ASWELL.
          config.nodeMethods.addValuesToGraphNode(graph, nodeID, self.argumentDictionary[argument], write = 'replace')

        # Now deal with arguments pointing to task nodes.
        else:

          # Join together all of the arguments for this task into a string.
          argumentString = self.argumentDictionary[argument].pop(0)
          for argumentList in self.argumentDictionary[argument]: argumentString += ' ' + argumentList
          taskArguments = argumentString.split(' ')
          while True:
  
            # Get the first entry in the list.  Terminate the loop if there is nothing left in the list.
            try: taskArgument = taskArguments.pop(0)
            except: break
  
            # Get the next value in the list if one exists.
            try: nextTaskArgument = taskArguments[0]
            except: nextTaskArgument = '-'

            # Ensure that we are using the long form argument.
            task           = nodeID
            associatedTool = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
            longForm       = config.tools.getLongFormArgument(associatedTool, taskArgument)
            shortForm      = config.tools.getArgumentData(associatedTool, longForm, 'short form argument')
            isFilenameStub = config.tools.getArgumentData(associatedTool, longForm, 'is filename stub')

            # Determine if this is a flag or a value. If the argument is a flag, the next argument on the
            # command line will be a '-'
            if nextTaskArgument.startswith('-'): value = ['set']
            else: value = [taskArguments.pop(0)]

            # If there is no node available for this task argument, create the node and add the edge.
            sourceNodeIDs = config.nodeMethods.getNodeForTaskArgument(graph, nodeID, longForm)
            if not sourceNodeIDs:
              sourceNodeID  = 'OPTION_' + str(config.nodeMethods.optionNodeID)
              attributes    = config.nodeMethods.buildNodeFromToolConfiguration(config.tools, associatedTool, longForm)
              graph.add_node(sourceNodeID, attributes = attributes)
              config.nodeMethods.addValuesToGraphNode(graph, sourceNodeID, value, write = 'replace')
              config.edgeMethods.addEdge(graph, config.nodeMethods, config.tools, sourceNodeID, task, longForm)
              config.nodeMethods.optionNodeID += 1

            # If there are already nodes for this task argument, determine how to proceed.
            else:

              # Check if this argument defines a file/files. If so, all of the possible source nodes must be
              # referencing a file.
              isFile = config.nodeMethods.getGraphNodeAttribute(graph, sourceNodeIDs[0], 'isFile')

              # For option nodes not corresponding to files, check that there is only a single source node
              # and set its value.
              if not isFile:
                if len(sourceNodeIDs) == 1:
                  config.nodeMethods.addValuesToGraphNode(graph, sourceNodeIDs[0], value, write = 'replace')
                  config.edgeMethods.addEdge(graph, config.nodeMethods, config.tools, sourceNodeIDs[0], task, longForm)
                else:
                  #TODO ERROR
                  print('MULTIPLE SOURCE NODES FOR NON FILE NODE. - attachPipelineArgumentsToNodes')
                  self.errors.terminate()

              # Option nodes dealing with files are a little more complex.
              else:
                #TODO LOOK INTO THIS.
                # If the node is connected to a file node, check if the file node has already been created.  If
                # it has, determine if the file node has any predecessors.  If so, generate a new input node for 
                # this task that will exist alongside the original node - in effect creating two nodes that both
                # feed into the task using the same argument.  The reason for this is that it does not make sense
                # to modify options that act backwards in the pipeline.  For example, the output of a sorting
                # routine is a file node that feed into a variant calling task (as directed in the pipeline
                # configuration file). In addition, tha command line might have input bam files defined to feed 
                # directly into the variant calling task node.  It doesn't make sense to add these files to the
                # node that has been merged with the sort routine since these input bam files have no connection to
                # tasks prior to the variant calling.  This is clearly only allowed for options where multiple values
                # are permitted (there will now be two nodes associated with the same argument, so this argument must
                # allow multiple definitions.)
  
                # It is possible that a new node has already been created, in which case sourceNodeIDs will have
                # multiple values.  Check if any of them are files and have no predecssors.  If there is one such
                # node, add values to this.  If not, create a new node.
                availableNodeIDs = []
                for sourceNodeID in sourceNodeIDs:
                  if config.nodeMethods.getGraphNodeAttribute(graph, sourceNodeID, 'isFile'):
                    fileNodeID = sourceNodeID + '_FILE'
                    if fileNodeID in graph.nodes(data = False):
                      if not graph.predecessors(fileNodeID): availableNodeIDs.append(sourceNodeID)
  
                # No nodes were found with no predecessors, so a new node should be created.
                if not availableNodeIDs:
                  attributes   = config.nodeMethods.buildNodeFromToolConfiguration(config.tools, associatedTool, longForm)
                  sourceNodeID = config.nodeMethods.buildOptionNode(graph, config.tools, task, associatedTool, longForm, attributes)
                  config.nodeMethods.addValuesToGraphNode(graph, sourceNodeID, value, write = 'replace')
                  config.edgeMethods.addEdge(graph, config.nodeMethods, config.tools, sourceNodeID, task, longForm)
  
                # A node was found with no predecssors, so add values to this node.
                elif len(availableNodeIDs) == 1:
                  sourceNodeID = availableNodeIDs[0]
                  config.nodeMethods.addValuesToGraphNode(graph, sourceNodeID, value, write = 'append', iteration = 1)
                  config.edgeMethods.addEdge(graph, config.nodeMethods, config.tools, sourceNodeID, task, longForm)
  
                # Multiple previous nodes were found. This should not have occured, so gkno canno proceed.
                else:
                  #TODO ERROR
                  print('too many available nodes, attachPipelineArgumentsToNodes - commandLine.py')
                  self.errors.terminate()
  
              # Check if this option defines a file.  If so, create a file node for this option.
              if config.tools.getArgumentData(associatedTool, longForm, 'input'):
                config.nodeMethods.buildTaskFileNodes(graph, config.tools, sourceNodeID, task, longForm, shortForm, 'input')
              elif config.tools.getArgumentData(associatedTool, longForm, 'output'):
                config.nodeMethods.buildTaskFileNodes(graph, config.tools, sourceNodeID, task, longForm, shortForm, 'output')

  # Attach the tool arguments to the graph nodes.
  def attachToolArgumentsToNodes(self, graph, config, gknoConfig):

    # Define the argumentValues structure. The argumentDictionary structure is parsed and
    # the values for each argument are stored in argumentValues. After all entries in
    # argumentDictionary have been processed, the values are added to the graph nodes.
    # The reason for this is that the same argument may appear on the command line multiple
    # times and these should all be collated before being assigned to the node.
    argumentValues = {}

    # Get the task node.
    task = config.nodeMethods.getNodes(graph, 'task')[0]

    # Parse the command line arguments.
    for argument in self.argumentDictionary:
      isGknoArgument = False

      # Get the nodeID of the option node for this argument.
      try: nodeID = config.nodeMethods.getNodeForTaskArgument(graph, task, argument)[0]

      # If no nodes were found, the argument must be a gkno specific argument or not have
      # been created in the graph yet,
      except:

        # See if this is a gkno specific argument.
        nodeID = gknoConfig.getNodeForGknoArgument(graph, config, argument)

        # If not, this is an argument that hasn't yet had a node created. Before creating a new node,
        # check to see if this is an input list. If so, determine which argument the values in the list
        # refer to and add the values to the relevant node.
        if not nodeID:

          # If this is a list of arguments, get the argument to use for the values.
          if config.tools.getArgumentData(task, argument, 'list of input files'):
            assignedArgument = config.tools.getArgumentData(task, argument, 'apply by repeating this argument')
            try: nodeID = config.nodeMethods.getNodeForTaskArgument(graph, task, assignedArgument)[0]
            except:
              #TODO
              print("NODE DOESN'T EXIST. CREATE - attachToolArgumentsToNodes")
              self.errors.terminate()

            # Parse the list and modify the value in argumentDictionary from the list to the files
            # in the list.
            filename = './' + self.argumentDictionary[argument][0]
            names    = [name.strip() for name in open(filename)]
            values   = []
            for name in names: values.append(name)
            self.argumentDictionary[argument] = values
          
          # The node doesn't exist.
          else:
            nodeID     = 'OPTION_' + str(config.nodeMethods.optionNodeID)
            attributes = config.nodeMethods.buildNodeFromToolConfiguration(config.tools, task, argument)
            graph.add_node(nodeID, attributes = attributes)
            config.edgeMethods.addEdge(graph, config.nodeMethods, config.tools, nodeID, task, argument)
            config.nodeMethods.optionNodeID += 1

        else: isGknoArgument = True

      # Check if the argument is a flag. If so, the value needs to be set to 'set'.
      if isGknoArgument:
        if config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'dataType') == 'flag': self.argumentDictionary[argument] = ['set']
      else:
        if config.tools.getArgumentData(task, argument, 'data type') == 'flag': self.argumentDictionary[argument] = ['set']

      if nodeID not in argumentValues: argumentValues[nodeID] = self.argumentDictionary[argument]
      else:
        for value in self.argumentDictionary[argument]: argumentValues[nodeID].append(value)
      
    for nodeID in argumentValues: config.nodeMethods.addValuesToGraphNode(graph, nodeID, argumentValues[nodeID], write = 'replace')

  # Assign values to the file nodes using the option nodes.
  def mirrorFileNodeValues(self, graph, config, workflow):
    for task in workflow:
      fileNodeIDs = config.nodeMethods.getPredecessorFileNodes(graph, task)
      for fileNodeID in fileNodeIDs:
        optionNodeID = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)
        values       = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'values')
        config.nodeMethods.replaceGraphNodeValues(graph, fileNodeID, values)

      # Now deal with output files.
      fileNodeIDs = config.nodeMethods.getSuccessorFileNodes(graph, task)
      for fileNodeID in fileNodeIDs:
        optionNodeID = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)
        values       = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'values')
        config.nodeMethods.replaceGraphNodeValues(graph, fileNodeID, values)
























  # Parse through all of the commands stored in the argumentList and check that they are all valid.
  # If they are, put them in a new structure that groups all of the arguments with their respective
  # task.  This structure is returned.
  def assignArgumentsToTasks(self):#, tool, shortForms, isPipeline, pipelineArguments, pipeArguments, pipeShortForms, workflow, verbose):
    task = tool if not isPipeline else ''

    # Parse through the list of arguments supplied on the command line and determine which task in
    # the pipeline they belong to.  Modify the argumentList to include the task as well as the
    # argument and value.  This routine does not check that the arguments are valid or correctly
    # formed: those checks are performed in the parseCommandLine routine.
    for argument, value in self.argumentList:
      argumentName = ''
      if argument in pipeArguments or argument in pipeShortForms:
        argumentName = pipeShortForms[argument] if argument in pipeShortForms else argument
        taskLink     = pipeArguments[argumentName]['link to this task']
        argumentLink = pipeArguments[argumentName]['link to this argument'] if 'link to this argument' in pipeArguments[argumentName] else 'pipeline'

        # Do not add 'pipeline' arguments to the new structure.
        if argumentLink != 'pipeline':
          if taskLink not in self.linkedArguments: self.linkedArguments[taskLink] = []
          self.linkedArguments[taskLink].append(('pipeline', argumentName, argumentLink, value))

        # Add pipeline arguments to their own structure.
        else:
          shortForm = pipeArguments[argumentName]['short form argument']
          dataType  = pipeArguments[argumentName]['type']
          value     = self.checkDataType(task, 'pipeline', argumentName, shortForm, '', '', value, dataType, verbose)
          if dataType == 'flag': pipelineArguments[argumentName] = 'set'
          else: pipelineArguments[argumentName] = value

      # If a pipeline is being run, the name of a task in the workflow is an allowed command line
      # argument.  If this is the case, there may be multiple arguments supplied for that specific
      # task, so place all of these in the modifiedList.
      elif isPipeline:
        if argument.startswith('-'): task = argument[1:]
        if argument.startswith('--'): task = argument[2:]
        if task in workflow:
          taskArguments = value.split(' ')
          while True:

            # Get the first entry in the list.  Terminate the loop if there is nothing left in the list.
            try: taskArgument = taskArguments.pop(0)
            except: break

            # Get the next value in the list if one exists.
            try: nextTaskArgument = taskArguments[0]
            except: nextTaskArgument = '-'

            if nextTaskArgument.startswith('-'):
              if task not in self.linkedArguments: self.linkedArguments[task] = []
              self.linkedArguments[task].append(('pipeline task', taskArgument, taskArgument, ''))
            else:
              if task not in self.linkedArguments: self.linkedArguments[task] = []
              self.linkedArguments[task].append(('pipeline task', taskArgument, taskArgument, nextTaskArgument))
              taskArguments.pop(0)

        # If gkno is being run in the pipe mode, the allowed options (pipeline argument or pipeline task)
        # have also been covered.  Any other command line arguments are unrecognised.
        else:
          self.errors.unknownArgument(verbose, argument)
          self.errors.terminate()

      # If a single tool is being run, the argument must be for this tool (again, checks on the
      # validity of the argument are checked later).
      elif not isPipeline:
        argumentName = shortForms[task][argument] if argument in shortForms[task] else argument
        if task not in self.linkedArguments: self.linkedArguments[task] = []
        self.linkedArguments[task].append(('tool', argumentName, argumentName, value))

      # If gkno is being run as a tool, the only allowed options (a general pipeline argument such
      # as --verbose, or a tool argument) have been covered.  If gkno is being run in the pipe mode,
      # the allowed options (pipeline argument or pipeline task) have also been covered.  Any other
      # command line arguments are unrecognised.
      else:
        self.errors.unknownArgument(verbose, argument)
        self.errors.terminate()

  # All of the arguments on the command line have been added to the linkedArguments structure.  In
  # this structure, each task in the pipeline has all of the arguments associated with it stored
  # with their given values along with the argument in the form understood by the tool the task points
  # to.  Now parse through all of these and check that the values supplied are valid.
  def parseCommandLine(self, tool, arguments, shortForms, isPipeline, workflow, pipeArguments, pipeShortForms, taskToTool, verbose):

    # Initialise the self.arguments structure.  This will hold all of the commands ready for building
    # command lines in the final scripts.
    if isPipeline:
      for task in workflow: self.arguments[task] = {}
    else:
      task                 = tool
      taskToTool[task]     = task
      self.arguments[task] = {}

    # Parse through all of the supplied arguments and values, task by task.
    for task in self.linkedArguments:

      # Get the name of the tool that the argument is for.  Note that in a pipeline, the workflow
      # is a list of unique tasks.  Each task is associated with a tool.
      tool = taskToTool[task]

      # Parse through all of the arguments for this task.
      for argumentType, pipeArgument, argument, value in self.linkedArguments[task]:

        # Check that the argument is valid for the tool it is intended.
        if argument not in arguments[tool]:
          self.errors.unknownArgument(verbose, argument)
          self.errors.terminate()

        # Get the expected data type associated with the argument.
        dataType = arguments[tool][argument]['type']

        # Get the short form of the argument.
        pipeShortForm = ''
        shortForm     = ''
        if argumentType == 'pipeline': pipeShortForm = pipeArguments[pipeArgument]['short form argument']
        shortForm = arguments[tool][argument]['short form argument'] if 'short form argument' in arguments[tool][argument] else ''

        # Check that a value was supplied for the argument if it is not a flag.  If there is an
        # error, determine if the argument was defined as a pipeline argument, or as a direct
        # argument for the tool.  The error message needs to reflect the argument inputted by the
        # usself.errors.
        if dataType != 'flag' and value == '':
          self.errors.missingArgumentValue(verbose, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, dataType)
          self.errors.terminate()

        # If the argument is a flag and it was supplied with an argument, terminate.
        if dataType == 'flag' and value != '':
          self.errors.flagGivenValue(verbose, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value)
          self.errors.terminate()

        # If the argument is not a flag, check that the data type given is consistent with expectation.
        if dataType != 'flag':
          value = self.checkDataType(task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value, dataType, verbose)

          # Check if this command line argument has already been seen.  Some arguments can have multiple
          # values and so can appear on the command line multiple times (for example the --bam command in
          # freebayes can be set multiple times to allow multiple BAM files to be read in).  If this is
          # allowed, the argument definition should include the 'allow multiple definitions' in its 
          # information.
          if argument in self.arguments[task]:
            if argument in arguments[tool]:
              if 'allow multiple definitions' not in arguments[tool][argument]:
                self.errors.multipleDefinitionsForSameArgument(verbose, task, argument, shortForm)
                self.errors.terminate()
              else: self.arguments[task][argument].append(value)
            else: exit('haven\'t handled yet, command line: 312')
          else:
            self.arguments[task][argument] = []
            self.arguments[task][argument].append(value)

        # If the argument is a flag, mark this flag as set.
        else:
          if argument in self.arguments[task]:
            self.errors.multipleDefinitionsForFlag(verbose, task, argument, shortForm)
            self.errors.terminate()
          else:
            self.arguments[task][argument] = []
            self.arguments[task][argument].append('set')

  # Check that the argument has the correct data type.
  def checkDataType(self, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value, dataType, verbose):

    # If the argument expects a Boolean, check that the given value is either 'true', 'True', 'false' or
    # 'False'.
    if dataType == 'bool':
  
      # Ensure that a valid argument has been provided.
      if (value == 'true') or (value == 'True'): value = True
      elif (value == 'false') or (value == 'False'): value = False
      else:
        self.errors.incorrectBooleanValue(verbose, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value)
        self.errors.terminate()
  
    # If the argument demands a string, check that a value is provided.
    elif dataType == 'string':
      if value == '':
        self.errors.missingArgumentValue(verbose, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, dataType)
        self.errors.terminate()

    # If the argument demands an integer, check that the supplied value is an integself.errors.
    elif (dataType == 'integer'):
      try: value = int(value)
      except: self.errors.incorrectDataType(verbose, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value, dataType)
      if self.errors.hasError: self.errors.terminate()

    # If the argument demands a floating point...
    elif dataType == 'float':
      try: value = float(value)
      except: self.errors.incorrectDataType(verbose, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value, dataType)
      if self.errors.hasError: self.errors.terminate()

    # If a value was provided to a flag...
    elif dataType == 'flag':
      if value != '':
        self.errors.flagGivenValue(verbose, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value)
        self.errors.terminate()

    return value
