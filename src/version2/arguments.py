#!/bin/bash/python

from __future__ import print_function

import argumentErrors as err
import pipelineConfiguration as pc

import json
import os
import sys

# Define a class for handling all arguments and their relationship with the graph.
class arguments:
  def __init__(self):

    # Define error handling for file errors.
    self.errors = err.argumentErrors()

    # Store information for each argument.
    self.arguments = {}

  # Add arguments from pipeline configuration data to the object.
  def addPipelineArguments(self, data):

    # Loop over the arguments and add the argument information to the arguments data structure.
    for argument in data: self.arguments[argument] = data[argument]

  # Now that the graph is built, parse all of the arguments in the pipelines and associate them with
  # the graph nodes and vice versa.
  def assignNodesToArguments(self, graph, superpipeline):

    # Loop over all tiers of the superpipeline (except the top level as this has already been handled),
    # and add the arguments by path.
    for tier in range(1, len(superpipeline.pipelinesByTier) + 1):

      # Loop over the pipelines.
      for pipeline in superpipeline.pipelinesByTier[tier]:

        # Get the pipeline configuration data.
        pipelineData = superpipeline.pipelineConfigurationData[pipeline]
        for argument in pipelineData.longFormArguments:

          # Get the pipeline address.
          address = pipelineData.address

          # Get the node that this argument is associated with and the graph node associated with
          # the configuration node. There may be more than one graph node if this is a stub argument.
          configurationNodeID = pipelineData.longFormArguments[argument].nodeID
          nodeAddress         = address + '.' + configurationNodeID if address else configurationNodeID

          # Check that the node address is present in the graph.configurationFileToGraphNodeID dictionary. If
          # it isn't, then no node with this address has been observed in the superpipeline and so, there is
          # an error in the pipeline configuration file.
          try: graphNodeIDs = graph.configurationFileToGraphNodeID[nodeAddress]
          except: pipelineData.errors.invalidNodeInArgument(pipeline, argument, nodeAddress, pipelineData.longFormArguments[argument].category)

          # If this is not the top level pipeline, the argument requires the pipeline address. Define
          # the argument name for use in the data structures. The '--' of the argument is left intact
          # to ensure that the created name doesn't conflict with a configuration file node name.
          argumentAddress = str(address + '.' + argument) if address else str(argument)

          # If this is not the top level pipeline, add the argument to the list of available arguments.
          if tier != 1: self.arguments[str(argumentAddress)] = pipelineData.longFormArguments[argument]

          # Link the graph node IDs with the argument.
          for graphNodeID in graphNodeIDs:

            # Get the short form of the argument.
            shortFormArgument = pipelineData.longFormArguments[argument].shortFormArgument
            shortFormAddress  = str(address + '.' + shortFormArgument) if address else str(shortFormArgument)

            # Add the arguments to the graph node as well as the description of the argument.
            if not graph.getGraphNodeAttribute(graphNodeID, 'longFormArgument'):
              graph.setGraphNodeAttribute(graphNodeID, 'longFormArgument', str(argumentAddress))
              graph.setGraphNodeAttribute(graphNodeID, 'shortFormArgument', shortFormAddress)
              graph.setGraphNodeAttribute(graphNodeID, 'description', pipelineData.longFormArguments[argument].description)

            # If the argument had already been set, add this argument to the list of alternative arguments.
            else:
              alternativeArguments = graph.getGraphNodeAttribute(graphNodeID, 'alternativeArguments')
              alternativeArguments.append((str(argumentAddress), str(shortFormAddress)))
              graph.setGraphNodeAttribute(graphNodeID, 'alternativeArguments', alternativeArguments)

            # Link the argument with the graph node ID to which it points.
            self.arguments[str(argumentAddress)].graphNodeIDs.append(str(graphNodeID))

            # Check for predecessors or successors and find the data type for the argument.
            successors = graph.graph.successors(graphNodeID)
            if successors: self.arguments[str(argumentAddress)].dataType = graph.getArgumentAttribute(graphNodeID, successors[0], 'dataType')
            if not self.arguments[str(argumentAddress)].dataType:
              predecessors = graph.graph.predecessors(graphNodeID)
              if predecessors:
                self.arguments[str(argumentAddress)].dataType = graph.getArgumentAttribute(predecessors[0], graphNodeID, 'dataType')

  # If the main pipeline lists a tool whose arguments should be imported, check that the listed tool is
  # valid, that none of the arguments conflict with the pipeline and then add the arguments to the
  # allowed arguments.
  def importArguments(self, graph, superpipeline):

    # Get the name of the tool.
    task = superpipeline.pipelineConfigurationData[superpipeline.pipeline].importArgumentsFromTool
    if not task: return

    # Check if the named task is a pipeline, a tool or invalid and respond appropriately.
    if task in superpipeline.tasks: self.importToolArguments(task, graph, superpipeline)
    elif task in superpipeline.tiersByPipeline: self.importPipelineArguments(task, superpipeline)

    # The supplied task is invalid.
    else: self.errors.invalidImportTool(task)

  # Import arguments from a tool in the pipeline.
  def importToolArguments(self, task, graph, superpipeline):
    pipeline = superpipeline.pipeline

    # Loop over the pipeline arguments and check if any of them point to the tool whose arguments
    # are to be imported. Store which of the tool arguments are already set.
    setArguments              = []
    definedLongFormArguments  = []
    definedShortFormArguments = []
    for argument in self.arguments.keys():
      if '.' not in argument:

        # Store the long and short forms of the pipeline argument.
        definedLongFormArguments.append(str(argument))
        definedShortFormArguments.append(str(self.arguments[argument].shortFormArgument))

        # Check if the graph node is a predecessor or successor of the task whose arguments are being
        # imported. If so, identify the long and short forms of the arguments for the tool.
        for graphNodeID in self.arguments[argument].graphNodeIDs:
          if task in graph.graph.predecessors(graphNodeID):
            longFormArgument = graph.getArgumentAttribute(task, graphNodeID, 'longFormArgument')
            if longFormArgument not in setArguments: setArguments.append(longFormArgument)
          if task in graph.graph.successors(graphNodeID):
            longFormArgument = graph.getArgumentAttribute(graphNodeID, task, 'longFormArgument')
            if longFormArgument not in setArguments: setArguments.append(longFormArgument)

    # Get the tool whose arguments should be imported.
    tool      = superpipeline.tasks[task]
    arguments = superpipeline.getToolArguments(tool)

    # Identify the nodes that already exist for this tool, so that arguments can be attached to these nodes.
    toolArgumentNodes = self.getTaskNodes(graph, task)

    # Loop over all the tool arguments.
    for argument in arguments:
      isLongFormDefined  = False
      isShortFormDefined = False

      # If a pipeline argument is already linked to the tool argument, do not include this argument.
      if argument not in setArguments:
          
        # Find the node that the argument points to, if one exists.
        graphNodeID = toolArgumentNodes[argument] if argument in toolArgumentNodes else None

        # If this is an output file and the output file is passed on to another tool, do not offer
        # this as a command line argument. The description provided could be confusing, so if it is
        # required that this argument is set, a pipeline argument must be provided.
        if not (superpipeline.getToolArgumentAttribute(tool, argument, 'isOutput') and graph.graph.successors(graphNodeID)):

          # Check if the long form version of this argument conflicts with an argument already set.
          if argument in definedLongFormArguments: isLongFormDefined = True
  
          # Perform the same check for the short form version of the argument.
          shortFormArgument = superpipeline.getToolArgumentAttribute(tool, argument, 'shortFormArgument')
          if shortFormArgument in definedShortFormArguments: isShortFormDefined = True
  
          # If the long and short forms are already defined, this is likely because the tool whose arguments
          # are being imported has a standard argument that is also defined at the pipeline level (e.g. an
          # argument such as --region, -rg is standardised across all tools using a region). The resolution to
          # this is to either link the pipeline argument to the relevant node in the graph, or create a unique
          # node in the pipeline that can be addressed with a new argument.
          if isLongFormDefined and isShortFormDefined: self.errors.importedArgumentIsDefined(task, tool, pipeline, argument, shortFormArgument)
  
          # If the tool long or short form argument conflicts with a pipeline argument, advise that the pipeline
          # argument should be changed.
          if isLongFormDefined: self.errors.importedArgumentLongFormConflict(task, tool, pipeline, argument)
          if isShortFormDefined:
            pipelineArgument = superpipeline.pipelineConfigurationData[pipeline].shortFormArguments[shortFormArgument]
            self.errors.importedArgumentShortFormConflict(task, tool, pipeline, argument, shortFormArgument, pipelineArgument)
  
          # Create a pipelineArguments data structure for storing the argument information and add basic information.
          argumentAttributes = pc.pipelineArguments()
          argumentAttributes.dataType          = superpipeline.getToolArgumentAttribute(tool, argument, 'dataType')
          argumentAttributes.description       = superpipeline.getToolArgumentAttribute(tool, argument, 'description')
          argumentAttributes.isRequired        = superpipeline.getToolArgumentAttribute(tool, argument, 'isRequired')
          argumentAttributes.longFormArgument  = argument
          argumentAttributes.shortFormArgument = shortFormArgument
          argumentAttributes.graphNodeID       = graphNodeID
  
          # Set the category to which the tool belongs.
          argumentAttributes.category = superpipeline.getToolArgumentAttribute(tool, argument, 'category')
  
          # Add the argument to the pipeline arguments.
          self.arguments[argument] = argumentAttributes

  # Loop over all predecessor and successor nodes for a task and return a dictionary linking
  # tool arguments to graph nodes.
  def getTaskNodes(self, graph, task):
    nodes = {}
    for nodeID in graph.graph.predecessors(task): nodes[graph.getArgumentAttribute(nodeID, task, 'longFormArgument')] = nodeID
    for nodeID in graph.graph.successors(task): nodes[graph.getArgumentAttribute(task, nodeID, 'longFormArgument')] = nodeID

    # Return the dictionary.
    return nodes

  # Import arguments from a pipeline contained within the pipeline.
  def importPipelineArguments(self, pipeline, superpipeline):
    print('IMPORT ARGUMENTS FROM PIPELINE')
