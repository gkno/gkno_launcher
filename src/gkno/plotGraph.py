#!/bin/bash/python

from __future__ import print_function
import networkx as nx

import graph as gr
import plotErrors as er

import os
import subprocess
import sys

# Define the plotting class.
class plotGraph():
  def __init__(self):

    # Define the errors.
    self.errors = er.plotErrors()

    # Keep track of the requested plots.
    self.isFullPlot    = False
    self.isReducedPlot = False

    # Store the filenames.
    self.plotFilename        = None
    self.reducedPlotFilename = None
    self.fullPlotFilename    = None

    # Define the text font.
    self.fontName   = 'montserrat'

    # Define styles and colours for option nodes.
    self.optionNodeFillColour = 'white'
    self.optionNodeFontColour = 'black'
    self.optionNodeShape      = 'rectangle'
    self.optionNodeStyle      = 'filled, rounded'

    # Define styles and colours for task nodes.
    self.taskNodeColour     = '#0E77A6'
    self.taskNodeFillColour = 'white'
    self.taskNodeFontColour = '#5A5A5A'
    self.taskNodeShape      = 'circle'
    self.taskNodeStyle      = 'filled'
    self.taskNodeWidth      = '4'

    # Define file node styles and colours.
    self.fileNodeColour     = '#F97308'
    self.fileNodeFillColour = 'white'
    self.fileNodeFontColour = '#5A5A5A'
    self.fileNodeShape      = 'oval'
    self.fileNodeStyle      = 'filled'
    self.fileNodeWidth      = '2.5'

  # Determine if a plot was requested and if so, the plot type. Ensure that the filename(s) are
  # set.
  def isPlotRequired(self, arguments, gkno):

    # Check if a plot was requested. Firs, check to see if a full plot was requested.
    option = 'GKNO-DRAW-FULL-PIPELINE'
    if gkno.options[option].longFormArgument in arguments or gkno.options[option].shortFormArgument in arguments:
      self.isFullPlot   = True
      self.plotFilename = arguments[gkno.options[option].longFormArgument][0]

    # Then check if a reduced plot was requested.
    option = 'GKNO-DRAW-REDUCED-PIPELINE'
    if gkno.options[option].longFormArgument in arguments or gkno.options[option].shortFormArgument in arguments:
      self.isReducedPlot = True
      self.plotFilename  = arguments[gkno.options[option].longFormArgument][0]

    # Finally, check if both plots were requested.
    option = 'GKNO-DRAW-PIPELINE'
    if gkno.options[option].longFormArgument in arguments or gkno.options[option].shortFormArgument in arguments:
      self.isFullPlot    = True
      self.isReducedPlot = True
      self.plotFilename  = arguments[gkno.options[option].longFormArgument][0]

    # If no plot was requested, return.
    if not self.isFullPlot and not self.isReducedPlot: return

    # Check that a filename was provided.
    if not self.plotFilename: self.errors.noFilename()

    # If both a full and reduced plot are being produced, append '-full' and '-reduced' to the filenames
    # and ensure that all filenames end with the extension '.dot'.
    if self.plotFilename.endswith('.dot'): self.plotFilename = self.plotFilename.rsplit('.dot', 1)[0]
    if self.isFullPlot and self.isReducedPlot:
      self.fullPlotFilename    = str(self.plotFilename + '-full.dot')
      self.reducedPlotFilename = str(self.plotFilename + '-reduced.dot')
    else:
      self.fullPlotFilename    = str(self.plotFilename + '.dot')
      self.reducedPlotFilename = str(self.plotFilename + '.dot')
    
  # Plot a dot file. Either the option, file or all nodes are plotted (gkno specific
  # nodes are removed).
  def plot(self, superpipeline, graph, filename, isReduced):

    # Generate a copy of the graph to manipulate and draw.
    graphToDraw = graph.graph.copy()

    # Remove all option nodes.
    for optionNodeId in gr.pipelineGraph.CM_getNodes(graphToDraw, 'option'):
      if isReduced: graphToDraw.remove_node(optionNodeId)
      else:
        graphToDraw.node[optionNodeId]["label"]     = optionNodeId.rsplit('.', 1)[-1]
        graphToDraw.node[optionNodeId]["shape"]     = self.optionNodeShape
        graphToDraw.node[optionNodeId]["style"]     = self.optionNodeStyle
        graphToDraw.node[optionNodeId]["fillcolor"] = self.optionNodeFillColour
        graphToDraw.node[optionNodeId]["fontname"]  = self.fontName
        graphToDraw.node[optionNodeId]["fontcolor"] = self.optionNodeFontColour

    # Loop over file nodes. If the node has predecessors and successors, leave it in the graph. If it has only
    # predecessors or successors, check if it is listed as a node to be kept in the graph.
    for fileNodeId in gr.pipelineGraph.CM_getNodes(graphToDraw, 'file'):

      # If a reduced plot is requested, check if this node can be removed by checking all of the tool arguments
      # associated with the node for the includeInReducedPlot variable set to False.
      isIncluded = True
      if isReduced:
        arguments = []
        for task in graphToDraw.predecessors(fileNodeId):
          arguments.append((task, graph.getArgumentAttribute(task, fileNodeId, 'longFormArgument')))
        for task in graphToDraw.successors(fileNodeId):
          arguments.append((task, graph.getArgumentAttribute(fileNodeId, task, 'longFormArgument')))

        for task, longFormArgument in arguments:
          tool     = graph.getGraphNodeAttribute(task, 'tool')
          toolData = superpipeline.toolConfigurationData[tool]
          if not toolData.getArgumentAttribute(longFormArgument, 'includeInReducedPlot'):
            isIncluded = False
            break

      # If this node is not required, remove it.
      if isReduced and not isIncluded: graphToDraw.remove_node(fileNodeId)
 
      # Otherwise, update the nodes attributes for plotting.
      else:
        predecessorNodeIds = graphToDraw.predecessors(fileNodeId)
        successorNodeIds   = graphToDraw.successors(fileNodeId)
        extension          = 'NA'
        for predecessorNodeId in predecessorNodeIds:
          try: extension = gr.pipelineGraph.CM_getArgumentAttribute(graphToDraw, predecessorNodeId, fileNodeId, 'extensions')[0]
          except: extension = 'NA'
          if extension != 'NA': break
        if extension == 'NA':
          for successorNodeId in successorNodeIds:
            try: extension = gr.pipelineGraph.CM_getArgumentAttribute(graphToDraw, fileNodeId, successorNodeId, 'extensions')[0]
            except: extension = 'NA'
            if extension != 'NA': break
  
        # Modify the file node.
        graphToDraw.node[fileNodeId]["label"] = extension.rsplit('.', 1)[-1]

    # Loop over the nodes and add names, styles etc and mark those node to be removed.
    for taskNodeId in gr.pipelineGraph.CM_getNodes(graphToDraw, 'task'):

      # Remove the address from the task name.
      taskNodeName = taskNodeId.rsplit('.', 1)[-1]

      # Mark if nodes should be removed or not.
      if gr.pipelineGraph.CM_getGraphNodeAttribute(graphToDraw, taskNodeId, 'includeInReducedPlot'): graphToDraw.node[taskNodeId]["include"] = True
      elif isReduced: graphToDraw.node[taskNodeId]["include"] = False

      # Define the name of the new node.
      taskName = taskNodeId.rsplit('.', 1)[-1]

      # Modify node attributes.
      graphToDraw.node[taskNodeId]["color"]     = self.taskNodeColour
      graphToDraw.node[taskNodeId]["style"]     = self.taskNodeStyle
      graphToDraw.node[taskNodeId]["shape"]     = self.taskNodeShape
      graphToDraw.node[taskNodeId]["label"]     = taskName
      graphToDraw.node[taskNodeId]["fillcolor"] = self.taskNodeFillColour
      graphToDraw.node[taskNodeId]["fontcolor"] = self.taskNodeFontColour
      graphToDraw.node[taskNodeId]["fontname"]  = self.fontName
      graphToDraw.node[taskNodeId]["penwidth"]  = self.taskNodeWidth

    # Remove nodes marked for removal, handling edges that are left dangling.
    if isReduced: self.removeNodes(graphToDraw)

    # Remove any orphaned nodes.
    for nodeId in graphToDraw.nodes():
      if not graphToDraw.predecessors(nodeId) and not graphToDraw.successors(nodeId): graphToDraw.remove_node(nodeId)

    # Loop over the nodes and add names, styles etc for file nodes.
    for nodeId in gr.pipelineGraph.CM_getNodes(graphToDraw, 'file'):
      graphToDraw.node[nodeId]["color"]     = self.fileNodeColour
      graphToDraw.node[nodeId]["shape"]     = self.fileNodeShape
      graphToDraw.node[nodeId]["style"]     = self.fileNodeStyle
      graphToDraw.node[nodeId]["fillcolor"] = self.fileNodeFillColour
      graphToDraw.node[nodeId]["fontname"]  = self.fontName
      graphToDraw.node[nodeId]["fontcolor"] = self.fileNodeFontColour
      graphToDraw.node[nodeId]["penwidth"]  = self.fileNodeWidth

    # Draw the graph from left to right, rather than default top to bottom.
    graphToDraw.graph.setdefault('graph', {})['rankdir'] = 'LR'

    # Draw the graph.
    nx.write_dot(graphToDraw, filename)
    self.convertToPng(filename)

  # Remove marked nodes. When removing a node, check all edges coming in and out of the node and
  # connect the previous task to the next task.
  def removeNodes(self, graphToDraw):
    nodesToCheck  = []
    nodesToDelete = []

    # Loop over the task nodes.
    for taskNodeId in gr.pipelineGraph.CM_getNodes(graphToDraw, 'task'):

      # Only process nodes to be removed.
      if not graphToDraw.node[taskNodeId]['include']:

        # Get all the predecessors and identify any previous tasks that produce files that pass through the
        # node being deleted.
        sources      = []
        predecessors = graphToDraw.predecessors(taskNodeId)
        for predecessorNodeId in predecessors:
          for previousTask in graphToDraw.predecessors(predecessorNodeId):
            if graphToDraw.node[previousTask]['include']: sources.append(predecessorNodeId)

        # Now move along the successors and see if any created files get passed to tasks that are kept.
        targets    = []
        successors = graphToDraw.successors(taskNodeId)
        while successors:
          successorNodeId = successors.pop(0)
          for nodeId in graphToDraw.successors(successorNodeId):

            # If the task node is a node being kept, mark this node as a target and move on.
            if graphToDraw.node[nodeId]['include']: targets.append(nodeId)

            # If the task node is being removed, add its successors to the successors list to determine if
            # a task can be reached that is being kept.
            else:
              for nextSuccessor in graphToDraw.successors(nodeId): successors.append(nextSuccessor)

          # Store the file node for later.
          nodesToCheck.append(successorNodeId)

        # If there are no source or target nodes, no edges are required. Otherwise, join the sources to the
        # targets.
        for source in  sources:
          for target in targets: graphToDraw.add_edge(source, target)

        # Mark the node for deletion.
        nodesToDelete.append(taskNodeId)

    # Delete the task nodes.
    for taskNodeId in nodesToDelete: graphToDraw.remove_node(taskNodeId)

    # Loop over all the nodes that were successors to removed task nodes.
    for nodeId in nodesToCheck:

      # Check if the node is still in the graph.
      if nodeId in graphToDraw:

        # If the node has no predecessors, then the file node isn't flowing from a previous task, but will 
        # be shown in the plot as a unique node feeding into a task being kept in the plot. This gives the
        # false impression that the file is supplied, rather than having been generated by a task that has
        # been removed from the graph. This node should be deleted.
        if not graphToDraw.predecessors(nodeId): graphToDraw.remove_node(nodeId)

    # Finally, step through the graph and remove nodes marked 'NA'. These are files created from stubs that
    # are not passed to other tools, so just clutter the plot.
    for nodeId in gr.pipelineGraph.CM_getNodes(graphToDraw, 'file'):
      if graphToDraw.node[nodeId]['label'] == 'NA': graphToDraw.remove_node(nodeId)

  # Convert the .dot plots to png.
  def convertToPng(self, filename):

    # Define the command to execute.
    execute = 'dot -Tpng -Gsize=9.5,16/! ' + filename + ' -o ' + filename + '.png'
    success = subprocess.call(execute.split())

    # Delete the original dot file.
    execute = 'rm -f ' + filename
    success = subprocess.call(execute.split())
