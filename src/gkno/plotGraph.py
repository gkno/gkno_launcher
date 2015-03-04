#!/bin/bash/python

from __future__ import print_function
import networkx as nx

import graph as gr
import plotErrors as er

import os
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
    for optionNodeID in gr.pipelineGraph.CM_getNodes(graphToDraw, 'option'):
      if isReduced: graphToDraw.remove_node(optionNodeID)
      else:
        graphToDraw.node[optionNodeID]["label"]     = optionNodeID.rsplit('.', 1)[-1]
        graphToDraw.node[optionNodeID]["shape"]     = 'rectangle'
        graphToDraw.node[optionNodeID]["style"]     = 'filled, rounded'
        graphToDraw.node[optionNodeID]["fillcolor"] = '#6E915F'
        graphToDraw.node[optionNodeID]["fontname"]  = 'montserrat'
        graphToDraw.node[optionNodeID]["fontcolor"] = 'white'

    # Loop over file nodes. If the node has predecessors and successors, leave it in the graph. If it has only
    # predecessors or successors, check if it is listed as a node to be kept in the graph.
    for fileNodeID in gr.pipelineGraph.CM_getNodes(graphToDraw, 'file'):

      # If a reduced plot is requested, check if this node can be removed by checking all of the tool arguments
      # associated with the node for the includeInReducedPlot variable set to False.
      isIncluded = True
      if isReduced:
        arguments = []
        for task in graphToDraw.predecessors(fileNodeID):
          arguments.append((task, graph.getArgumentAttribute(task, fileNodeID, 'longFormArgument')))
        for task in graphToDraw.successors(fileNodeID):
          arguments.append((task, graph.getArgumentAttribute(fileNodeID, task, 'longFormArgument')))

        for task, longFormArgument in arguments:
          tool     = graph.getGraphNodeAttribute(task, 'tool')
          toolData = superpipeline.toolConfigurationData[tool]
          if not toolData.getArgumentAttribute(longFormArgument, 'includeInReducedPlot'):
            isIncluded = False
            break

      # If this node is not required, remove it.
      if isReduced and not isIncluded: graphToDraw.remove_node(fileNodeID)
 
      # Otherwise, update the nodes attributes for plotting.
      else:
        predecessorNodeIDs = graphToDraw.predecessors(fileNodeID)
        successorNodeIDs   = graphToDraw.successors(fileNodeID)
        extension          = 'NA'
        for predecessorNodeID in predecessorNodeIDs:
          try: extension = gr.pipelineGraph.CM_getArgumentAttribute(graphToDraw, predecessorNodeID, fileNodeID, 'extensions')[0]
          except: extension = 'NA'
          if extension != 'NA': break
        if extension == 'NA':
          for successorNodeID in successorNodeIDs:
            try: extension = gr.pipelineGraph.CM_getArgumentAttribute(graphToDraw, fileNodeID, successorNodeID, 'extensions')[0]
            except: extension = 'NA'
            if extension != 'NA': break
  
        # Modify the file node.
        graphToDraw.node[fileNodeID]["label"] = extension.rsplit('.', 1)[-1]

    # Loop over the nodes and add names, styles etc and mark those node to be removed.
    for taskNodeID in gr.pipelineGraph.CM_getNodes(graphToDraw, 'task'):

      # Remove the address from the task name.
      taskNodeName = taskNodeID.rsplit('.', 1)[-1]

      # Mark if nodes should be removed or not.
      if gr.pipelineGraph.CM_getGraphNodeAttribute(graphToDraw, taskNodeID, 'includeInReducedPlot'): graphToDraw.node[taskNodeID]["include"] = True
      elif isReduced: graphToDraw.node[taskNodeID]["include"] = False

      # Define the name of the new node.
      taskName = taskNodeID.rsplit('.', 1)[-1]

      # Modify node attributes.
      graphToDraw.node[taskNodeID]["style"]     = 'filled'
      graphToDraw.node[taskNodeID]["shape"]     = 'doublecircle'
      graphToDraw.node[taskNodeID]["label"]     = taskName
      graphToDraw.node[taskNodeID]["fillcolor"] = '#005422'
      graphToDraw.node[taskNodeID]["fontname"]  = 'montserrat'
      graphToDraw.node[taskNodeID]["fontcolor"] = 'white'

    # Remove nodes marked for removal, handling edges that are left dangling.
    if isReduced: self.removeNodes(graphToDraw)

    # Remove any orphaned nodes.
    for nodeID in graphToDraw.nodes():
      if not graphToDraw.predecessors(nodeID) and not graphToDraw.successors(nodeID): graphToDraw.remove_node(nodeID)

    # Loop over the nodes and add names, styles etc for file nodes.
    for nodeID in gr.pipelineGraph.CM_getNodes(graphToDraw, 'file'):
      graphToDraw.node[nodeID]["shape"]     = 'circle'
      graphToDraw.node[nodeID]["style"]     = 'filled'
      graphToDraw.node[nodeID]["fillcolor"] = '#6E915F'
      graphToDraw.node[nodeID]["fontname"]  = 'montserrat'
      graphToDraw.node[nodeID]["fontcolor"] = 'white'

    # Draw the graph from left to right, rather than default top to bottom.
    graphToDraw.graph.setdefault('graph', {})['rankdir'] = 'LR'

    # Draw the graph.
    nx.write_dot(graphToDraw, filename)

  # Remove marked nodes. When removing a node, check all edges coming in and out of the node and
  # connect the previous task to the next task.
  def removeNodes(self, graphToDraw):
    nodesToCheck  = []
    nodesToDelete = []

    # Loop over the task nodes.
    for taskNodeID in gr.pipelineGraph.CM_getNodes(graphToDraw, 'task'):

      # Only process nodes to be removed.
      if not graphToDraw.node[taskNodeID]['include']:

        # Get all the predecessors and identify any previous tasks that produce files that pass through the
        # node being deleted.
        sources      = []
        predecessors = graphToDraw.predecessors(taskNodeID)
        for predecessorNodeID in predecessors:
          for previousTask in graphToDraw.predecessors(predecessorNodeID):
            if graphToDraw.node[previousTask]['include']: sources.append(predecessorNodeID)

        # Now move along the successors and see if any created files get passed to tasks that are kept.
        targets    = []
        successors = graphToDraw.successors(taskNodeID)
        while successors:
          successorNodeID = successors.pop(0)
          for nodeID in graphToDraw.successors(successorNodeID):

            # If the task node is a node being kept, mark this node as a target and move on.
            if graphToDraw.node[nodeID]['include']: targets.append(nodeID)

            # If the task node is being removed, add its successors to the successors list to determine if
            # a task can be reached that is being kept.
            else:
              for nextSuccessor in graphToDraw.successors(nodeID): successors.append(nextSuccessor)

          # Store the file node for later.
          nodesToCheck.append(successorNodeID)

        # If there are no source or target nodes, no edges are required. Otherwise, join the sources to the
        # targets.
        for source in  sources:
          for target in targets: graphToDraw.add_edge(source, target)

        # Mark the node for deletion.
        nodesToDelete.append(taskNodeID)

    # Delete the task nodes.
    for taskNodeID in nodesToDelete: graphToDraw.remove_node(taskNodeID)

    # Loop over all the nodes that were successors to removed task nodes.
    for nodeID in nodesToCheck:

      # Check if the node is still in the graph.
      if nodeID in graphToDraw:

        # If the node has no predecessors, then the file node isn't flowing from a previous task, but will 
        # be shown in the plot as a unique node feeding into a task being kept in the plot. This gives the
        # false impression that the file is supplied, rather than having been generated by a task that has
        # been removed from the graph. This node should be deleted.
        if not graphToDraw.predecessors(nodeID): graphToDraw.remove_node(nodeID)

    # Finally, step through the graph and remove nodes marked 'NA'. These are files created from stubs that
    # are not passed to other tools, so just clutter the plot.
    for nodeID in gr.pipelineGraph.CM_getNodes(graphToDraw, 'file'):
      if graphToDraw.node[nodeID]['label'] == 'NA': graphToDraw.remove_node(nodeID)