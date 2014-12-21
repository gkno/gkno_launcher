#!/bin/bash/python

from __future__ import print_function
import networkx as nx

import graph
from graph import *

import os
import sys

# Define the plotting class.
class plotGraph():
  def __init__(self):

    # Define a list of colours.
    self.colours = [ \
      'darkslategray1', \
      'deepskyblue', \
      'burlywood4', \
      'chocolate', \
      'darkgoldenrod', \
      'darkgoldenrod4', \
      'deepskyblue4', \
      'burlywood', \
      'darkkhaki', \
      'darkolivegreen2', \
      'darkolivegreen4' \
    ]

  # Plot a dot file. Either the option, file or all nodes are plotted (gkno specific
  # nodes are removed).
  def plot(self, superpipeline, graphToDraw, filename, isReduced):

    # Remove all option nodes.
    if isReduced:
      for optionNodeID in pipelineGraph.CM_getNodes(graphToDraw, 'option'): graphToDraw.remove_node(optionNodeID)

    # Loop over file nodes. If the node has predecessors and successors, leave it in the graph. If it has only
    # predecessors or successors, check if it is listed as a node to be kept in the graph.
    for fileNodeID in pipelineGraph.CM_getNodes(graphToDraw, 'file'):
      predecessorNodeIDs = graphToDraw.predecessors(fileNodeID)
      successorNodeIDs   = graphToDraw.successors(fileNodeID)
      extension          = 'NA'
      for predecessorNodeID in predecessorNodeIDs:
        try: extension = pipelineGraph.CM_getArgumentAttribute(graphToDraw, predecessorNodeID, fileNodeID, 'extensions')[0]
        except: extension = 'NA'
        if extension != 'NA': break
      if extension == 'NA':
        for successorNodeID in successorNodeIDs:
          try: extension = pipelineGraph.CM_getArgumentAttribute(graphToDraw, fileNodeID, successorNodeID, 'extensions')[0]
          except: extension = 'NA'
          if extension != 'NA': break

      # Modify the file node.
      graphToDraw.node[fileNodeID]["label"] = extension

    # Loop over the nodes and add names, styles etc and mark those node to be removed.
    for taskNodeID in pipelineGraph.CM_getNodes(graphToDraw, 'task'):

      # Remove the address from the task name.
      taskNodeName = taskNodeID.rsplit('.', 1)[-1]

      # Mark if nodes should be removed or not.
      if pipelineGraph.CM_getGraphNodeAttribute(graphToDraw, taskNodeID, 'includeInPlot'): graphToDraw.node[taskNodeID]["include"] = True
      elif isReduced: graphToDraw.node[taskNodeID]["include"] = False

      # Define the name of the new node.
      taskName = taskNodeID.rsplit('.', 1)[-1]

      # Modify node attributes.
      graphToDraw.node[taskNodeID]["style"]     = 'filled'
      graphToDraw.node[taskNodeID]["shape"]     = 'doublecircle'
      graphToDraw.node[taskNodeID]["label"]     = taskName
      graphToDraw.node[taskNodeID]["fillcolor"] = '#2d8fc1'
      graphToDraw.node[taskNodeID]["fontname"]  = 'montserrat'
      graphToDraw.node[taskNodeID]["fontcolor"] = 'white'

    # Remove nodes marked for removal, handling edges that are left dangling.
    if isReduced: self.removeNodes(graphToDraw)

    # Remove any orphaned nodes.
    for nodeID in graphToDraw.nodes():
      if not graphToDraw.predecessors(nodeID) and not graphToDraw.successors(nodeID): graphToDraw.remove_node(nodeID)

    # Loop over the nodes and add names, styles etc for file nodes.
    for nodeID in pipelineGraph.CM_getNodes(graphToDraw, 'file'):
      graphToDraw.node[nodeID]["shape"]     = 'circle'
      graphToDraw.node[nodeID]["style"]     = 'filled'
      graphToDraw.node[nodeID]["fillcolor"] = '#123d53'
      graphToDraw.node[nodeID]["fontname"]  = 'montserrat'
      graphToDraw.node[nodeID]["fontcolor"] = 'white'

    # Draw the graph from left to right, rather than default top to bottom.
    graphToDraw.graph.setdefault('graph', {})['rankdir'] = 'LR'

    # Draw the graph.
    nx.write_dot(graphToDraw, filename)

  # Remove marked nodes. When removing a node, check all edges coming in and out of the node and
  # connect the previous task to the next task.
  def removeNodes(self, graphToDraw):
    nodesToCheck = []

    # Loop over the task nodes.
    for taskNodeID in pipelineGraph.CM_getNodes(graphToDraw, 'task'):

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

        # Delete the node.
        graphToDraw.remove_node(taskNodeID)

        # If there are no source or target nodes, no edges are required. Otherwise, join the sources to the
        # targets.
        for source in  sources:
          for target in targets: graphToDraw.add_edge(source, target)

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
    for nodeID in pipelineGraph.CM_getNodes(graphToDraw, 'file'):
      if graphToDraw.node[nodeID]['label'] == 'NA': graphToDraw.remove_node(nodeID)
