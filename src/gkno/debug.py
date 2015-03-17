#!/usr/bin/python

from __future__ import print_function

# Define a class used for debugging purposes.
class debug:
  def __init__(self):
    pass

  # Write out all input and outputs files and options from the workflow.
  def workflow(self, graph):
    print()
    print('Tasks in workflow:')
    print()
    for task in graph.workflow:
      print('task:', task)
      print('\tinputs:')
      for nodeID in graph.graph.predecessors(task):
        print('\t\t', graph.getArgumentAttribute(nodeID, task, 'longFormArgument'), graph.getGraphNodeAttribute(nodeID, 'values'))
      print('\toutputs:')
      for nodeID in graph.graph.successors(task):
        print('\t\t', graph.getArgumentAttribute(task, nodeID, 'longFormArgument'), graph.getGraphNodeAttribute(nodeID, 'values'))

  # Write out all input and output files from all task in the graph.
  def allTasks(self, graph):
    print()
    print('All tasks in pipeline (not ordered by workflow):')
    print()
    for task in graph.getNodes('task'):
      print('task:', task)
      print('\tinputs:')
      for nodeID in graph.graph.predecessors(task):
        print('\t\t', graph.getArgumentAttribute(nodeID, task, 'longFormArgument'), graph.getGraphNodeAttribute(nodeID, 'values'))
      print('\toutputs:')
      for nodeID in graph.graph.successors(task):
        print('\t\t', graph.getArgumentAttribute(task, nodeID, 'longFormArgument'), graph.getGraphNodeAttribute(nodeID, 'values'))
