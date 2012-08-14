#!/usr/bin/python

from __future__ import print_function
import os.path
import getpass
import subprocess
import sys

import commandLine
from commandLine import *

import files
from files import *

import helpClass
from helpClass import *

import tools
from tools import *

import pipelines
from pipelines import *

__author__ = "Alistair Ward"
__version__ = "0.04"
__date__ = "August 2012"

def main():

  # Define a tools object.  This stores all information specific to individual
  # tools.
  tl = tools()

  # Define a command line options, get the first command line argument
  # and proceed as required.
  cl = commandLine(tl)

  # Define a pipeline object.  Even if a single tool is all that is required,
  # some of the routines in the pipelines.py are still used.  A single tool
  # is essentially treated as a pipeline with a single element.
  pl = pipeline()

  # Define the source path of all the gkno machinery.
  sourcePath = os.path.abspath(sys.argv[0])[0:os.path.abspath(sys.argv[0]).rfind('/src/gkno/gkno.py')]

  # Generate a class for handling files.
  io = files()

  # Define a help class.  This provides usage information for the user.
  gknoHelp = helpClass()

  # Check if help has been requested.  If so, print out usage information for
  # the tool or pipeline as requested.
  cl.getMode(io, gknoHelp, tl, pl)

  # Check if help has been requested on the command line.  Search for the '--help'
  # or '-h' arguments on the command line.
  cl.checkForHelp(gknoHelp, pl)

  # Each of the tools available to gkno should have a config file to
  # describe its operation, purpose etc.  These are contained in
  # config_files/tools.  Find all of the config file and create a hash
  # table with all available tools.
  io.getJsonFiles(sourcePath + '/config_files/')

  # Print gkno title and version to the screen.
  if not gknoHelp.printHelp: gknoHelp.printHeader(__version__, __date__)

  # If a pipeline is being run, check that configuration files
  # exist for the selected pipeline.  This should be in directory
  # config_files and have the name <$ARGV[1]>.json.  If the file
  # exists, parse the json file.
  if pl.isPipeline:
    io.getPipelineConfigurationFile(gknoHelp, pl, sourcePath + "/config_files/pipes")

    # If a spcific pipeline has been specified and the pipeline exists, read in
    # the json file.
    if (not gknoHelp.printHelp) or (gknoHelp.printHelp and gknoHelp.specificPipelineHelp and not gknoHelp.unknownPipeline):
      io.phoneHomeID = io.getPipelineDescription(tl ,pl, True)

  # If gkno is being run in tool mode, the pl object still exists and is used.
  # Set the pl.information structure up to reflect a pipeline containing a
  # single tool.
  else: io.phoneHomeID = pl.setupIndividualTool(tl.tool, not gknoHelp.printHelp)

  # Read the tool json files into data structures in the tools class.
  #verbose = False if gknoHelp.printHelp else True
  io.getToolDescriptions(tl, pl, sourcePath + '/config_files/tools', not gknoHelp.printHelp)
  tl.checkForRequiredFields()

  # If a single tool is being run, check that it is a valid tool.
  if not pl.isPipeline: tl.checkTool(gknoHelp)
  pl.addPipelineSpecificOptions(tl)

  # If help was requested or there were problems (e.g. the tool name or pipeline
  # name did not exist), print out the required usage information.
  if gknoHelp.printHelp: gknoHelp.printUsage(io, tl, pl, __version__, __date__, sourcePath)

  # Print information about the pipeline to screen.
  if pl.isPipeline: pl.printPipelineInformation(tl)

  # For each of the tools in the pipeline, or the single tool if in tool mode,
  # parse the configuration file and put all of the allowed command line
  # arguments into a data structure along with defaults, exptected data types
  # etc.  Then parse the command line.
  tl.setupToolOptions(cl, pl)
  pl.setupPipelineOptions(tl)

  # Parse the command line.  Anything set by the user will overide configuration
  # file defaults or linkages.
  if pl.isPipeline: cl.parsePipelineCommandLine(gknoHelp, io, tl, pl)
  else: cl.parseToolCommandLine(gknoHelp, io, tl, pl, sys.argv, tl.tool, tl.tool, True)

  # Loop over each of the tools in turn and set all of the parameters.  Each
  # task in turn may depend on parameters/outputs of previous tasks and so
  # handling in each task in the order it appears in the pipeline is necessary.
  if tl.toolArguments['pipeline']['--verbose']:
    print('Setting up all parameters for task...', file = sys.stdout)
    sys.stdout.flush()
  for task in pl.information['workflow']:
    tool = pl.information['tools'][task]
    if tl.toolArguments['pipeline']['--verbose']:
      print("\t", task, ' (', tool, ')...', sep = '', file = sys.stdout)
      sys.stdout.flush()

    # Check all of the options for each tool and determine if the values are
    # linked to any other tool.  If so, set the values as necessary.  Also,
    # check that all required input files are set anc check the input and
    # output file extensions and paths.
    if pl.isPipeline: pl.toolLinkage(cl, tl, task, tool)

    # Check all input and output files.  If there are instructions on how to construct
    # filenames, construct them.
    tl.constructFilenames(pl, task, tool)

    # For all files, check that a path has been given.  If a path is set, leave the file
    # as is.  If no path has been set, check if the file is an input, output or resource
    # file and use the --input-path, --output-path and --resource-path values
    # respectively.
    cl.setPaths(tl, pl, task, tool)

    # Check that all required files and parameters have been set.
    cl.checkParameters(tl, pl, gknoHelp, task, tool)
    if tl.toolArguments['pipeline']['--verbose']:
      print(file = sys.stdout)
      sys.stdout.flush()

  # Parse through all of the selected options and for those options referring
  # to input/output files, check that the extensions are correct, that the
  # paths are included and that the strings containing the output files and
  # the dependent files for each tool are populated.
  tl.determineDependencies(cl, pl)

  # There may be files that are required by the tool to run (e.g. files to
  # appear in the dependency list) that are not listed in the input arguments.
  # Those listed with arguments have already been included in the dependency
  # string for each tool in cl.checkParameters, now check for others.
  #
  # Similarly, each tool produces output files.  These are listed in the
  # Makefile in order to ensure that tools are only run if their outputs
  # don't already exist.
  tl.determineAdditionalFiles(pl)

  # In the course of executing the pipeline, some of the intermediate files
  # generated along the way should be deleted.  The pipeline configuration
  # file segment 'delete files' identifies which files should be deleted and
  # when in the pipeline they can be removed.
  pl.determineFilesToDelete(tl)

  # The list of files to be produced by the script is all of the files created
  # by each individual task in the pipeline.  However, if some of the files
  # are deleted along the way, the final list of files should not include these
  # deleted files.
  pl.determineFinalOutputs(tl)

  # The pipeline allows for tools to be outputted to the stream rather than to
  # an output file.  This allows tools to be joined together by pipes rather
  # than forcing the generation of all intermediate files.  The tasks that
  # output to the stream are listed in the pipeline configuration file, so check
  # if there are any and if so, check that the tools allow outputting to the
  # stream.
  pl.determinePiping(tl)

  # The basic order of the Makefile is to start with the final tool and write
  # out the rules to build the final output file.  If the prerequisites for this
  # task do not exist, then make will search for the rule to make the files.  The
  # Makefile proceeds in this manner all the way to the first task.  If any of the
  # tasks are piped together, then these need to be output in order, not reverse
  # order.
  if pl.isPiped: pl.determineToolWriteOrder()

  # Generate scripts to run the selected pipeline.
  io.generateMakefile(tl, pl, sourcePath)

  # Having established the mode of operation and checked that the command lines are
  # valid etc., ping the website to log use of gkno.
  io.phoneHome(sourcePath)

  # Execute the generated script unless the execute flag has been unset.
  if (tl.toolArguments['pipeline']['--execute'] == True) or (tl.toolArguments['pipeline']['--execute'] == 'True'):
    print("Executing make...\n", file = sys.stdout)
    success = subprocess.call(["make"])
    if success == 0: print("\ngkno completed tasks successfully.", file = sys.stdout)
    else: print("\ngkno failed to complete successfully.  Check operation and repair.", file = sys.stderr)

if __name__ == "__main__":
  main()
