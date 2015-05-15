#!/bin/bash/python

from __future__ import print_function

import pipelineConfigurationErrors as errors
import toolConfiguration as tc

import json
import os
import sys

# Define a class to deal with including commands for pipeline values.
class evaluateCommands:
  def __init__(self):

    # Store a list of node ids whose values need to be updated.
    self.updateValues = []

  # If any pipeline configuration nodes are given commands to evaluate, check the validity of the instructions
  # and implement them.
  def checkCommands(self, graph, superpipeline):

    # Loop over all of the pipelines in the superpipeline.
    for tier in superpipeline.pipelinesByTier:

      # Loop over all of the pipelines in the tier and get the configuration file data.
      for pipeline in superpipeline.pipelinesByTier[tier]:
        data = superpipeline.getPipelineData(pipeline)

        # Loop over all of the unique and shared configuration nodes foe the pipeline.
        self.checkCommand(graph, data.uniqueNodeAttributes, 'unique')
        self.checkCommand(graph, data.sharedNodeAttributes, 'shared')

  # Check the command set for the node and add to the graph.
  def checkCommand(self, graph, nodeIds, nodeType):

    # Loop over all of the requesed configuration file nodes.
    for configNodeId in nodeIds:
      evaluateCommand = nodeIds[configNodeId].evaluateCommand
      if evaluateCommand:
  
        # Get the command to be applied instead of a value.
        command = self.getCommand(evaluateCommand)
  
        # Get the graph node id for the unique configuration node.
        #TODO ERROR
        if configNodeId not in graph.configurationFileToGraphNodeId: print('ERROR - evaluateCommand.checkCommands - node not present', nodeType, configNodeId); exit(1)

        # Check the validity of the instructions regarding including values from nodes within the pipeline and return
        # a list of nodes which the instructions require.
        connectedNodeIds = self.getValues(graph, evaluateCommand, configNodeId, command)
  
        # Loop over the associated graph nodes.
        for nodeId in graph.configurationFileToGraphNodeId[configNodeId]:
  
          # If the graph node has no values, add the command. In addition, store the graph node id in the updateValues
          # list. After all file names have been constructed, these commands will be revisited to check if any values
          # need to be added to the commands. Including the command in the graph node will ensure that gkno will not
          # terminate due to the required values being missing for these nodes.
          graph.setGraphNodeAttribute(nodeId, 'values', [str(command)])
          graph.setGraphNodeAttribute(nodeId, 'isCommandToEvaluate', True)
          if 'add values' in evaluateCommand: self.updateValues.append((nodeId, evaluateCommand['add values']))
          else: self.updateValues.append((nodeId, None))

          # Get an initialised set of argument attributes to add to the edge.
          edgeAttributes            = tc.argumentAttributes()
          edgeAttributes.isLinkOnly = True

          # Add edges from all connected nodes to the task associated with the unique node.
          if nodeType == 'unique':
            task = nodeIds[configNodeId].task
            for connectedNode in connectedNodeIds: graph.graph.add_edge(connectedNode, task, attributes = edgeAttributes)

          # Add edges from all connected nodes to all tasks in the shared configuration node.
          elif nodeType == 'shared':
            for sharingNode in nodeIds[configNodeId].nodes:
              task = sharingNode['task']
              for connectedNode in connectedNodeIds: graph.graph.add_edge(connectedNode, task, attributes = edgeAttributes)

  # Check that the 'command' field appears in the evaluate command information and return
  # the value.
  def getCommand(self, data):

    # Terminate if the 'command' field is not present.
    #TODO ERROR
    if 'command' not in data: print('ERROR - evaluateCommands.getCommand'); exit(1)

    return str('$(' + data['command'] + ')')

  # Parse the instructions on values to be added to the command, check their validity and apply.
  def getValues(self, graph, data, nodeId, command):
    nodeIds = []

    # If there are values to be added, they must be included as a list.
    if 'add values' in data:

      #TODO ERROR
      if not isinstance(data['add values'], list): print('ERROR - evaluateCommands.getValues - list'); exit(1)

      # Loop over the list of values to add.
      for instructions in data['add values']:

        # If there are values to be used, the fields 'id' and 'nodeId' must be present.
        #TODO ERROR
        if 'id' not in instructions: print('ERROR - evaluateCommands.getValues - id', nodeId); exit(1)
        if 'node id' not in instructions: print('ERROR - evaluateCommands.getValues - nodeId', nodeId); exit(1)

        # The nodeId field must point to a node in the graph and additionally, must have values associated
        # with it, but only a single value
        #TODO ERROR
        if instructions['node id'] not in graph.graph.nodes(): print('ERROR - evaluateCommands.getValues - node not in graph', nodeId); exit(1)
  
        # The id is a string that appears in the command and should be replaced by the specified value.
        # If the id is not present in the command, then the instructions are not well formed.
        # TODO ERROR
        if instructions['id'] not in command: print('ERROR - evaluateCommands.getValues - id not in command'); exit(1)

        # If all of the above checks were successful, the command to evaluate is well formed and values can be added
        # when the values have been populated. Add the node id included in the instructions to nodeIds.
        nodeIds.append(instructions['node id'])

    # Return the nodeIds associated with the instructions.
    return nodeIds

  # Loop over all nodes that have values that are commands to evaluate and include values from other nodes, if
  # necessary.
  def addValues(self, graph):

    # Loop over all nodes whose values have been defined as commands to evaluate at run time.
    for nodeId, data in self.updateValues:
      values = graph.getGraphNodeAttribute(nodeId, 'values')

      # Only add values if there are instructions to do so.
      for instructions in data:
        associatedNodeId = instructions['node id']
        associatedValues = graph.getGraphNodeAttribute(associatedNodeId, 'values')
        textId           = instructions['id']

        # If the number of values for the current node is different to the number of values for the associated node,
        # terminate. For every value in the node being modified, there must be a value in the associated node.
        # TODO ERROR
        if len(associatedValues) != len(values): print('ERROR - evaluateCommands.addValues'); exit(1)

        # Loop over all values for the node.
        updatedValues = []
        for value, associatedValue in zip(values, associatedValues):
          updatedValues.append(str(value.replace(textId, associatedValue)))
          
      # Replace the values for the node with the updated values.
      graph.setGraphNodeAttribute(nodeId, 'values', updatedValues)
