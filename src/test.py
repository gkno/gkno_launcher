#!/bin/python

from __future__ import print_function
import networkx as nx

import pipelineAttributes
from pipelineAttributes import *

import toolAttributes
from toolAttributes import *

__author__  = "Alistair Ward"
__version__ = "0.000"
__date__    = "August 2013"

def main():
  pipe    = pipelineConfiguration()
  success = pipe.readConfiguration('configs/config.json')
  if not success:
    print('Failed to open', pipe.jsonError)
    exit(1)
  pipelineGraph = nx.DiGraph()
  pipe.validateConfigurationData('configs/config.json') #TODO Check that all fields are present and correct.
  pipe.addNodesAndEdges(pipelineGraph)

  # Generate the workflow.
  workflow = pipe.generateWorkflow(pipelineGraph)

  # Populate the nodes with necessary information.  Return a list of all of the tools used by the
  # pipelines.
  requiredTools = pipe.getRequiredTools(pipelineGraph)

  # Open all of the configuration files for the tools required by the pipeline and provide an
  # error for any tools that do not have configuration files.
  toolObjects = {} # Create an array of tool objects.
  for tool in requiredTools:

    #FIXME Determining the location and name of the tool configuration file is a GKNO
    # specific task.  This is a hack for testing.
    toolFilename = tool
    if tool == 'bamtools-index': toolFilename = 'configs/bamtools.json'
    if tool == 'bamtools-sort': toolFilename = 'configs/bamtools.json'
    if tool == 'mosaik-build-reference': toolFilename = 'configs/mosaik.json'
    if tool == 'mosaik-build-fastq': toolFilename = 'configs/mosaik.json'
    if tool == 'mosaik-aligner': toolFilename = 'configs/mosaik.json'
    if tool == 'mosaik-jump': toolFilename = 'configs/mosaik.json'
    if tool == 'freebayes': toolFilename = 'configs/freebayes.json'

    toolObjects[tool] = toolConfiguration() # Generate a toolAttributes object for this tool.
    success           = toolObjects[tool].readConfiguration(toolFilename)
    if not success:
      print('Failed to open:', toolFilename, toolObjects[tool].jsonError)
      exit(1)

    # Ensure that the tool configuration file is well constructed.
    toolObjects[tool].getConfigurationData(tool)

  # Loop over the task in the graph and perform necessary operations.
  for task in workflow:
    associatedTool = pipelineGraph.node[task]['attributes'].tool

    # Check that all the required nodes are defined for the tool.  If some data is required by
    # the tool, it's source must either be the command line or a different tool in the pipeline.
    # All pipeline command line arguments and tool outputs are specified in the pipeline
    # configuration file, so if the connections do not already exist in the graph, then the
    # pipeline cannot function.
    requiredArguments = toolObjects[associatedTool].getRequiredArguments()
    missingEdges      = pipe.checkRequiredTaskConnections(pipelineGraph, task, requiredArguments)
    if len(missingEdges) != 0:
      print('missing required edges for task:', task, missingEdges)

if __name__ == '__main__':
  main()
