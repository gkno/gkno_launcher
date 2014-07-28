#!/bin/bash/python

from __future__ import print_function
import networkx as nx

import gknoErrors
from gknoErrors import *

import os
import sys

# Define the plotting class.
class drawGraph():
  def __init__(self):
    self.errors = gknoErrors()

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

  # Draw the pipeline graph.
  def drawPipeline(self, graph, config):
    filename = config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-DRAW-PIPELINE', 'values')[1][0]
    if filename == '': self.errors.noDrawFileProvided(graph, config)

    # If the filename does not have the '.dot' extension, add it.
    if not filename.endswith('.dot'): filename += '.dot'
    self.drawDot(graph, config, filename, nodes = 'file')

  # Plot a dot file. Either the option, file or all nodes are plotted (gkno specific
  # nodes are removed).
  def drawDot(self, graph, config, filename, nodes = 'all'):
    graphToDraw = graph.copy()

    # Define a dictionary for containing mapping information for the nodes.  This will
    # map the current node names into new ones.
    mapping = {}

    # Get the required nodes for plotting.
    fileNodeIDs   = config.nodeMethods.getNodes(graphToDraw, 'file')
    optionNodeIDs = config.nodeMethods.getNodes(graphToDraw, 'option')
    gknoNodeIDs   = config.nodeMethods.getNodes(graphToDraw, 'general')
    if nodes == 'file':
      for nodeID in optionNodeIDs: config.nodeMethods.setGraphNodeAttribute(graphToDraw, nodeID, 'isMarkedForRemoval', True)

      # Find the first file associated with the file node.
      for nodeID in fileNodeIDs:
        try: newNodeID = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values')[1][0]
        except: newNodeID = nodeID

        # Remove the path from the file.
        if '/' in newNodeID: newNodeID = newNodeID.split('/')[-1]

        # Rename the node.
        if nodeID != newNodeID: config.nodeMethods.renameNode(graphToDraw, config.tools, nodeID, newNodeID, allowNullArgument = True)

    # Modify option nodes.
    elif nodes == 'option':
      for nodeID in fileNodeIDs: config.nodeMethods.setGraphNodeAttribute(graphToDraw, nodeID, 'isMarkedForRemoval', True)

    elif nodes != 'all':
      print('Do not know which nodes to plot - graphPlot')
      self.errors.terminate()

    # Mark gkno specific nodes for removal.
    for nodeID in gknoNodeIDs: config.nodeMethods.setGraphNodeAttribute(graphToDraw, nodeID, 'isMarkedForRemoval', True)
    graphToDraw.remove_node('gkno')
    config.nodeMethods.purgeNodeMarkedForRemoval(graphToDraw)

    # Get all of the categories associated with tools in the pipeline.
    categories = {}
    colourID   = 0
    for nodeID in graphToDraw:

      # Modify task nodes to include colour labels based on the category.
      if config.nodeMethods.getGraphNodeAttribute(graphToDraw, nodeID, 'nodeType') == 'task':
        tool     = config.nodeMethods.getGraphNodeAttribute(graphToDraw, nodeID, 'tool')
        category = config.tools.getGeneralAttribute(tool, 'category')

        # Associate this category with a colour.
        if category not in categories:
          categories[category] = colourID
          colourID += 1

        # Modify the colour of the node.
        del graphToDraw.node[nodeID]['attributes']
        graphToDraw.add_node(nodeID, shape = 'rectangle', style = 'filled', fillcolor = self.colours[categories[category]])

      # Modify option nodes.
      elif config.nodeMethods.getGraphNodeAttribute(graphToDraw, nodeID, 'nodeType') == 'option':
        del graphToDraw.node[nodeID]['attributes']

      # Modify file nodes.
      elif config.nodeMethods.getGraphNodeAttribute(graphToDraw, nodeID, 'nodeType') == 'file':

        # Get the file extension.
        extension = nodeID.split('.')[-1]
        graphToDraw.add_node(nodeID, label = extension)
        del graphToDraw.node[nodeID]['attributes']

    # Modify the edges so that the command line argument is displayed in the graph plot.
    for nodeID in graphToDraw:
      successorNodeIDs = graphToDraw.successors(nodeID)
      for successorNodeID in successorNodeIDs:

        # If the long form argument is 'None', replace the value with 'dependency'. This edge does not represent a
        # typical argument, but the task is dependent on the file. It may be that the file may be evaluated using a
        # defined command or something else, but the edge should be shown to fully represent dependencies.
        argument = config.edgeMethods.getEdgeAttribute(graphToDraw, nodeID, successorNodeID, 'longFormArgument')
        if argument == None: longFormArgument = '"dependency"'
        else: longFormArgument = '"' + argument + '"'
        graphToDraw.remove_edge(nodeID, successorNodeID)
        #graphToDraw.add_edge(nodeID, successorNodeID, label = longFormArgument)
        graphToDraw.add_edge(nodeID, successorNodeID)

    # Add category nodes.
    firstTask          = config.pipeline.workflow[0]
    predecessorNodeIDs = graphToDraw.predecessors(firstTask)
    firstNodeID        = predecessorNodeIDs[0] if predecessorNodeIDs else firstTask
    for category in categories:
      name = 'CAT_' + str(category)
      graphToDraw.add_node(name, shape = 'rectangle', style = 'filled', fillcolor = self.colours[categories[category]], label = category)
      graphToDraw.add_edge(name, firstNodeID, style = 'invis')

    # Map the new node names.
    graphToDraw = nx.relabel_nodes(graphToDraw, {})
    nx.write_dot(graphToDraw, filename)
