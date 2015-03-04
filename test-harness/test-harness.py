#!/usr/bin/python

from __future__ import print_function

import os.path
import getpass
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

  # Test all of the included pipelines.
  testPipelines()

  # Check that help messages can be requested.
  testCommands(0, 'gkno help errors', helpCommands())

  # Test all of the predefined pipeline configuration files. These fall into a range of
  # different test cases.
  testErrorCase(2, 'admin errors')
  testErrorCase(3, 'command line errors')
  testErrorCase(4, 'file handling errors')
  testErrorCase(5, 'general configuration file errors')
  testErrorCase(6, 'tool configuration file errors')
  testErrorCase(7, 'pipeline configuration file errors')
  testErrorCase(8, 'graph construction errors')
  testErrorCase(9, 'argument errors')
  testCommands(10, 'malformed command line errors', userCommands())
  testErrorCase(10, 'data consistency errors')
  testErrorCase(11, 'help request errors')
  testErrorCase(12, 'plotting graph errors')
  testErrorCase(13, 'makefile generation errors')

# Loop over all of the pipelines included with gkno and check that they all execute when provided
# with the test parameter set.
def testPipelines():

  # Define a test class.
  harness = testHarness(0)

  # Print to screen the tests being performed.
  print(file = sys.stdout)
  print('Testing defined pipelines...', end = '', file = sys.stdout)
  sys.stdout.flush()

  # Loop over all defined pipelines.
  for filename in os.listdir('../config_files/pipes'):
    if filename.endswith('.json') and not filename.endswith('parameter-sets.json'):
      pipeline = filename.rsplit('.json')[0]
      command  = harness.executable + ' ' + pipeline + ' -ps test'
      success  = subprocess.call(command.split(), stdout = harness.devnull, stderr = harness.devnull)
      if success == harness.errorCode: harness.successes += 1
      else: harness.failures.append(str(pipeline + '. Command:'  + command))

  # Print the results.
  print('complete.', file = sys.stdout)
  sys.stdout.flush()
  harness.printResults()

# Check help messages.
def testCommands(code, text, commands):

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

  # Print the results.
  print('complete.', file = sys.stdout)
  sys.stdout.flush()
  harness.printResults()

# Check all instances of error and ensure that gkno terminates with the correct error code.
def testErrorCase(code, text):

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
    else: harness.failures.append(str(pipeline + '. Command:'  + command))

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
               ('pipeline (long form)', executable + ' call --help', 0),
               ('pipeline (short form)', executable + ' call -h', 0)
             ]

  return commands

# Get command lines that include errors or incomplete information.
def userCommands():

  # Define a test class.
  executable = testHarness(0).executable

  # Perform the tests using this pipeline.
  pipeline = 'call-population'
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

if __name__ == "__main__":
  main()
