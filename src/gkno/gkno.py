from __future__ import print_function
import os.path
import subprocess
import sys

import commandLine
from commandLine import *

import files
from files import *

import tools
from tools import *

import pipelines
from pipelines import *

__author__ = "Alistair Ward"
__version__ = "0.01"
__date__ = "June 2012"

def main():

  # Define a command line options, get the first command line argument
  # and proceed as required.
  cl = commandLine()

  # Print gkno title and version to the screen.
  cl.printInformation(__version__, __date__)

  # Define the source path of all the gkno machinery.
  sourcePath = os.path.abspath(sys.argv[0])[0:os.path.abspath(sys.argv[0]).rfind('/src/gkno/gkno.py')]

  # Define a tools object.  This stores all information specific to individual
  # tools.
  tl = tools()

  # Generate a class for handling files.
  io = files()

  # Each of the tools available to gkno should have a config file to
  # describe its operation, purpose etc.  These are contained in
  # config_files/tools.  Find all of the config file and create a hash
  # table with all available tools.
  io.getJsonFiles(sourcePath + '/config_files/')

  # Read the tool json files into data structures in the tools class.
  io.getToolDescriptions(tl, sourcePath + '/config_files/tools')

  # Define a pipeline object.  Even if a single tool is all that is required,
  # some of the routines in the pipelines.py are still used.  A single tool
  # is essentially treated as a pipeline with a single element.
  pl = pipeline()
  mode = cl.getMode(tl)

  # If a pipeline is being run, check that configuration files
  # exist for the selected pipeline.  This should be in directory
  # config_files and have the name <$ARGV[1]>.json.
  if mode == 'pipe':
    io.getPipelineConfigurationFile(sourcePath + "/config_files/pipes")

    # Get the json information for the selected pipeline.
    io.phoneHomeID = io.getPipelineDescription(pl)

    # Print information about the pipeline to screen.
    pl.printPipelineInformation(tl)

  # If an individual tool is being run, modify the command line to be as expected
  # by the command line routines.
  else:
    tool = mode

    # Set the pipeline information to a single tool.
    io.phoneHomeID = pl.setupIndividualTool(tool)

    # Reset the command line to be compatible with that expected by the pipeline
    # routines.
    cl.resetCommandLine(tool)

  # For each of the tools, parse the allowed command line options
  # and populate options with their default values.
  tl.setupToolOptions(cl, pl)
  pl.setupPipelineOptions(tl)

  # Parse command line options and override any variables with these
  # values.
  cl.parseCommandLine(tl, pl, io)

  # Check all of the options for each tool and determine if the values are
  # linked to any other tool.  If so, set the values as necessary.  Also,
  # check that all required input files are set anc check the input and
  # output file extensions and paths.
  if mode == 'pipe': pl.toolLinkage(cl, tl)

  # Check that all required files and parameters have been set.
  cl.checkParameters(tl, pl)

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

  # Generate scripts to run the selected pipeline.
  io.generateMakefile(tl, pl, sourcePath);

  # Having established the mode of operation and checked that the command lines are
  # valid etc., ping the website to log use of gkno.
  io.phoneHome(sourcePath)

  # Execute the generated script unless the execute flag has been unset.
  if pl.options['--execute'] == True:
    print(file = sys.stdout)
    print("Executing make...\n", file = sys.stdout)
    success = subprocess.call(["make"])
    if success == 0: print("\ngkno completed tasks successfully.", file = sys.stdout)
    else: print("\ngkno failed to complete successfully.  Check operation and repair.", file = sys.stderr)

if __name__ == "__main__":
  main()
