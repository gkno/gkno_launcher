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
  def plot(self, graphToDraw, filename):

    # Loop over the nodes and change task nodes to rectangles.
    for taskNodeID in pipelineGraph.getNodes(graphToDraw, 'task'):
      predecessorNodeIDs = []
      successorNodeIDs   = []
      for predecessor in graphToDraw.predecessors(taskNodeID): predecessorNodeIDs.append(predecessor)
      for successor in graphToDraw.successors(taskNodeID): successorNodeIDs.append(successor)

      graphToDraw.remove_node(taskNodeID)
      graphToDraw.add_node(taskNodeID, shape = 'rectangle', style = 'filled')
      for nodeID in predecessorNodeIDs: graphToDraw.add_edge(nodeID, taskNodeID)
      for nodeID in successorNodeIDs: graphToDraw.add_edge(taskNodeID, nodeID)
    nx.write_dot(graphToDraw, filename)
