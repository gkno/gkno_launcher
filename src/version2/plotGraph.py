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
    #for fileNodeID in pipelineGraph.CM_getNodes(graphToDraw, 'file'):

    # Loop over the nodes and change task nodes to rectangles.
    for taskNodeID in pipelineGraph.CM_getNodes(graphToDraw, 'task'):

      # If the node is not marked for inclusion in the plot, remove it.
      if not pipelineGraph.CM_getGraphNodeAttribute(graphToDraw, taskNodeID, 'includeInPlot') and isReduced: graphToDraw.remove_node(taskNodeID)

      # Otherwise, modify the node for plotting.
      else:
        predecessorNodeIDs = []
        successorNodeIDs   = []
        for predecessor in graphToDraw.predecessors(taskNodeID): predecessorNodeIDs.append(predecessor)
        for successor in graphToDraw.successors(taskNodeID): successorNodeIDs.append(successor)
  
        graphToDraw.remove_node(taskNodeID)
        graphToDraw.add_node(taskNodeID, shape = 'rectangle', style = 'filled')
        for nodeID in predecessorNodeIDs: graphToDraw.add_edge(nodeID, taskNodeID)
        for nodeID in successorNodeIDs: graphToDraw.add_edge(taskNodeID, nodeID)

    # Remove any orphaned nodes.
    for nodeID in graphToDraw.nodes():
      if not graphToDraw.predecessors(nodeID) and not graphToDraw.successors(nodeID): graphToDraw.remove_node(nodeID)

    # Draw the graph from left to right, rather than default top to bottom.
    graphToDraw.graph.setdefault('graph', {})['rankdir'] = 'LR'

    # Draw the graph.
    nx.write_dot(graphToDraw, filename)
