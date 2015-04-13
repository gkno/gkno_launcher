#!/usr/bin/python

from __future__ import print_function

import os.path
import getpass
import shutil
import subprocess
import sys

class testHarness:
  def __init__(self, errorCode):

    # Define the error code.
    self.errorCode = errorCode

    # Define the executable.
    self.executable = '../gkno'

    # Define devnull.
    self.devnull = open(os.devnull, 'w')

    # Initialise the number of test successes and failures.
    self.successes = 0
    self.failures  = []

  # Print the test results.
  def printResults(self):
    noTests = self.successes + len(self.failures)
    print('    Number of tests: ', noTests, file = sys.stdout)
    if noTests > 0:
      print('    Successes:       ', self.successes, file = sys.stdout)
      print('    Failures:        ', len(self.failures), file = sys.stdout)

    # Print out the names of the failed test pipelines.
    if self.failures:
      print(file = sys.stdout)
      print('    ===========================================', file = sys.stdout)
      print('    The following pipelines failed their tests:', file = sys.stdout)
      print('    ===========================================', file = sys.stdout)
      for pipeline in self.failures: print('      ', pipeline, file = sys.stdout)

# Test harness for gkno. Runs over a host of malformed configuration files and checks
# that all errors are handled. In addition, all pipelines are executed using the 'test'
# parameter set using files in the tutorial resources bundle.
def main():
  print(file = sys.stdout)
  print('============================', file = sys.stdout)
  print('Executing gkno test harness.', file = sys.stdout)
  print('============================', file = sys.stdout)

  # Get a list of all files/directories that should not be deleted.
  keep, copyFiles = getRequiredFiles()

  # Test all of the included pipelines.
  testPipelines(keep, copyFiles)

  # Check that help messages can be requested.
  testCommands(0, 'gkno help errors', helpCommands(), keep)

  # Test all of the predefined pipeline configuration files. These fall into a range of
  # different test cases.
  testErrorCase(2, 'admin errors', keep)
  testErrorCase(3, 'command line errors', keep)
  testErrorCase(4, 'file handling errors', keep)
  testErrorCase(5, 'general configuration file errors', keep)
  testErrorCase(6, 'tool configuration file errors', keep)
  testErrorCase(7, 'pipeline configuration file errors', keep)
  testErrorCase(8, 'graph construction errors', keep)
  testErrorCase(9, 'argument errors', keep)
  testCommands(10, 'malformed command line errors', userCommands(), keep)
  testErrorCase(10, 'data consistency errors', keep)
  testErrorCase(11, 'help request errors', keep)
  testErrorCase(12, 'plotting graph errors', keep)
  testErrorCase(13, 'makefile generation errors', keep)

# Read the keep-files.txt file and store a list of files/directories that should not be deleted.
# In addition, read the copy-files.txt file and determine the files that need to be copied to the
# test harness before each task. Ensure that these files exist prior to executing the tests.
def getRequiredFiles():
  filehandle   = open('keep-list.txt')
  isTerminate  = False
  keep         = []
  resourcePath = os.path.abspath(os.getcwd() + '/../resources/tutorial/current') + '/'
  for line in filehandle.readlines(): keep.append(line.rstrip('\n'))

  filehandle = open('copy-files.txt')
  copy       = {}
  for line in filehandle.readlines():
    task  = line.split(':')[0].replace('"', '').replace(' ', '')
    files = line.split(':')[1].rstrip('\n').split(',')

    # Store the filenames.
    copy[task] = []
    for filename in files:
      updatedFilename = str(resourcePath + filename.replace('"', '').replace(' ', ''))
      if not os.path.isfile(updatedFilename): isTerminate = True
      else: copy[task].append(updatedFilename)

  # Terminate if not all the files exist.
  if isTerminate:
    print('Ensure all files in copy-files.txt are in the resources directory.')
    exit(1)

  return keep, copy

# Loop over all of the pipelines included with gkno and check that they all execute when provided
# with the test parameter set.
def testPipelines(keep, copy):

  # Define a test class.
  harness = testHarness(0)

  # Print to screen the tests being performed.
  print(file = sys.stdout)
  print('Testing defined pipelines...', file = sys.stdout)
  sys.stdout.flush()

  # Loop over all defined pipelines.
  for filename in os.listdir('../config_files/pipes'):
    if filename.endswith('.json') and not filename.endswith('parameter-sets.json'):
      pipeline = filename.rsplit('.json')[0]
      print('\t', pipeline, '...', sep = '', end = '', file = sys.stdout)
      sys.stdout.flush()

      # Copy across any necessary files.
      copyFiles(copy, pipeline)

      # Execute the command.
      command  = harness.executable + ' ' + pipeline + ' -ps test'
      success  = subprocess.call(command.split(), stdout = harness.devnull, stderr = harness.devnull)
      if success == harness.errorCode:
        harness.successes += 1
        print('succeeded.', file = sys.stdout)
        sys.stdout.flush()
      else:
        harness.failures.append(str(pipeline + '. Command: '  + command))
        print('failed.', file = sys.stdout)
        sys.stdout.flush()

      # Delete created files.
      deleteFiles(keep)

  # Print the results.
  harness.printResults()

# Copy across necessary files.
def copyFiles(copy, pipeline):
  if pipeline in copy:
    for filename in copy[pipeline]: shutil.copy(filename, '.')

# Check help messages.
def testCommands(code, text, commands, keep):

  # Get the gkno executable.
  harness = testHarness(code)

  # Print to screen the tests being performed.
  print(file = sys.stdout)
  print('Testing \'' + text + '\'...', end = '', file = sys.stdout)
  sys.stdout.flush()

  # Loop over all the commands and test them.
  for name, command, code in commands:
    success = subprocess.call(command.split(), stdout = harness.devnull, stderr = harness.devnull)
    if success == code: harness.successes += 1
    else: harness.failures.append(str(name + '. Command: ' + command))

    # Delete created files.
    deleteFiles(keep)

  # Print the results.
  print('complete.', file = sys.stdout)
  sys.stdout.flush()
  harness.printResults()

# Check all instances of error and ensure that gkno terminates with the correct error code.
def testErrorCase(code, text, keep):

  # Define a test class.
  harness = testHarness(code)
  path    = './' + text.replace(' ', '-')

  # Print to screen the tests being performed.
  print(file = sys.stdout)
  print('Testing \'' + text + '\'...', end = '', file = sys.stdout)
  sys.stdout.flush()

  # Loop over all the malformed configuration files.
  for filename in os.listdir(path):
    pipeline = filename.rsplit('.json')[0]
    command  = harness.executable + ' ' + pipeline + ' -cp ' + path
    success  = subprocess.call(command.split(), stdout = harness.devnull, stderr = harness.devnull)
    if success == harness.errorCode: harness.successes += 1
    else: harness.failures.append(str(pipeline + '. Command: '  + command))

    # Delete created files.
    deleteFiles(keep)

  # Print the results.
  print('complete.', file = sys.stdout)
  sys.stdout.flush()
  harness.printResults()

# Get commands for testing gkno help.
def helpCommands():

  # Define a test class.
  executable = testHarness(0).executable

  # Build a list of commands to test.
  commands = [
               ('top-level', executable, 0),
               ('categories (long form)', executable + ' --categories', 0),
               ('categories (short form)', executable + ' -cat', 0),
               ('specific category', executable + ' -cat test', 0),
               ('all pipelines (long form)', executable + ' --all-pipelines', 0),
               ('all pipelines (short form)', executable + ' -api', 0),
               ('pipeline (long form)', executable + ' freebayes --help', 0),
               ('pipeline (short form)', executable + ' freebayes -h', 0)
             ]

  return commands

# Get command lines that include errors or incomplete information.
def userCommands():

  # Define a test class.
  executable = testHarness(0).executable

  # Perform the tests using this pipeline.
  pipeline = 'freebayes'
  initial  = executable + ' ' + pipeline

  # Build a list of commands to test.
  commands = [
               ('no arguments', initial, 10),
               ('invalid long form argument', initial + ' --ins', 3),
               ('invalid short form argument', initial + ' -ins', 3),
               ('invalid extension', initial + ' -r ref.f', 10),
               ('repeated argument', initial + ' -i a.bam -r ref.fa -r ref2.fa', 10)
             ]

  return commands

# Delete all created files.
def deleteFiles(keep):
  for filename in os.listdir('.'):
    if filename not in keep and not filename.startswith('.'):
      if os.path.isfile(filename): os.remove(filename)
      elif os.path.isdir(filename): shutil.rmtree(filename)

if __name__ == "__main__":
  main()
