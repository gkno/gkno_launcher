#!/usr/bin/python

from __future__ import print_function
import os
import sys

class errors:
  def __init__(self):
    self.error = False;

  # If an unknown command line argument is given.
  def unknownToolArgument(self, pad, tool, argument):
    print(pad, 'ERROR: Argument \'', argument, '\' for tool \'', tool, '\' is not recognised.', sep = '', end = '', file = sys.stderr)
    print(' Please check command line.', sep = '', file = sys.stderr)
    sys.stderr.flush()
    self.error = True

  # If there is an unknown command line argument when running a pipeline (e.g.
  # it is not a pipeline argument, nor is it a tool name within the pipeline).
  def unknownPipelineArgument(self, pad, argument):
    print(pad, 'ERROR: Argument \'', argument, '\' is neither a pipeline argument or a tool name.', sep = '', end = '', file = sys.stderr)
    print(' Please check command line.', sep = '', file = sys.stderr)
    sys.stderr.flush()
    self.error = True

  # If a required field in a tool configuration file is missing.
  def missingFieldForTool(self, pad, task, argument, field, value):
    print(pad, 'ERROR: Required field \'', field, '\' in configuration file for \'', task, '\' argument ', sep = '', end = '', file = sys.stderr)
    print('\'', argument, '\' is ', sep = '', end = '', file = sys.stderr)
    if value == '': print('missing.', sep = '', file = sys.stderr)
    else: print('invalid (value: \'', value, '\')', sep = '', file = sys.stderr)
    self.error = True

  # If the command line argument is a tool name, a list of tool specific commands must
  # follow (in quotation marks).  If not, then there is an error.
  def commandLineToolError(self, pad, pipelineName, tool):
    print(pad, 'ERROR: Commands for tool \'', tool, '\' expected in the form:', sep = '', file = sys.stderr)
    print(pad, "\tgkno pipe ", pipelineName, ' [options] -', tool, ' "[tool options]"', sep = '', file = sys.stderr)
    self.error = True

  # When parsing the command line for a pipeline, if any of the pipeline arguments (as
  # specified in the pipeline configuration file) point to a tool that is not in the
  # pipeline, fail.
  def associatedToolNotInPipeline(self, text, tool, argument):
    print(text, 'ERROR: Pipeline argument \'', argument, '\' is associated with a tool that is not ', sep = '', end = '', file = sys.stderr)
    print('part of the pipeline (\'', tool, '\')', sep = '', file = sys.stderr)
    self.error = True

  # The pipeline configuration file contains an argument that points to a constituent
  # tool, however the tool argument it points to is invalid.
  def incorrectArgumentInPipelineConfigurationFile(self, pad, tool, argument, linkedArgument):
    print(pad, 'ERROR: The pipeline configuration file \'arguments\' block defines \'', argument, '\'', sep = '', end = '', file = sys.stderr)
    print(' as linked to \'', linkedArgument, '\' in tool \'', tool, '\'', sep = '', end = '', file = sys.stderr)
    print(pad, 'ERROR: This argument (\'', linkedArgument, '\') does not exist for this tool.', sep = '', end = '', file = sys.stderr)
    print('  Please check the pipeline configuration file.', sep = '', file = sys.stderr)
    self.error = True

  def invalidOption(self, newLine, pad, text, option, tool):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: Invalid option (', option, ') in the \'', text, '\' section of the pipeline ', sep = '', end = '', file = sys.stderr)
    print('configuration file for tool \'', tool, '\'.', sep = '', file = sys.stderr)
    self.error = True

  # The tool configuration file has multiple input files designated for use as output
  # filename constructors.
  def multipleFilenameConstructors(self, pad, task, tool, argumentA, argumentB):
    print(pad, 'ERROR: Task \'', task, '\' (tool \'', tool, '\')\' has multiple input files designated ', sep = '', end = '', file = sys.stderr)
    print('as filename generators: \'', argumentA, '\' and \'', argumentB, '\'.', sep = '', file = sys.stderr)
    self.error = True

  # If an output filename is to be constructed from an input filename and the specific
  # input argument to use was not specified and there are multiple inputs to the task,
  # gkno cannot determine which argument to use.
  def unknownFilenameConstructor(self, newLine, pad, task, tool, argument):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: Filename for output argument \'', argument, '\' in task \'', task, sep = '', end = '', file = sys.stderr)
    print(' (\'', tool, '\')\' cannot be determined.', sep = '', file = sys.stderr)
    print(pad, 'ERROR: Either no or multiple input files exist and none are designated for use in filename creation.', sep = '', file = sys.stderr)
    self.error = True

  # The input file used for constructing an output file is blank.
  def noInputFilenameForFilenameConstruction(self, pad, task, tool, outputFile):
    print(pad, 'ERROR: Constructing output filename \'', outputFile, '\' in task \'', task, sep = '', end = '', file = sys.stderr)
    print(' (\'', tool, '\')\' failed.', sep = '', file = sys.stderr)
    print(pad, 'ERROR: Input filename used in the construction is blank.', sep = '', file = sys.stderr)
    self.error = True

  # The pipeline configuration file may contain a block describing how to construct the
  # name of an output file.  In this description, the 'additional text from variables'
  # block may appear describing the tool and argument from which to take a variable.  If
  # these are missing, the filename cannot be constructed.
  def noDescriptionOfVariable(self, pad, tool, argument, text):
    print(pad, 'ERROR: Unable to construct filename for \'', tool, '\' argument \'', argument, '\'.', sep = '', end = '', file = sys.stderr)
    print(pad, 'ERROR: Variable \'', text, '\' appearing in the \'order\' list needs to be described.', sep = '', end = '', file = sys.stderr)
    print(pad, 'ERROR: See documentation and ensure that the configuration file is well constructed.', sep = '', end = '', file = sys.stderr)
    print(file = sys.stderr)
    self.error = True

  # Same as above, except the description is present, but either the tool or argument
  # is not.
  def missingVariableForFilenameConstruction(self, pad, tool, argument, text):
    print(pad, 'ERROR: Unable to construct filename for \'', tool, '\' argument \'', argument, '\'.', sep = '', end = '', file = sys.stderr)
    print(pad, 'ERROR: Either the \'tool\' or \'argument\' fields are missing for \'', text, '\'.', sep = '', end = '', file = sys.stderr)
    print(file = sys.stderr)
    self.error = True

  # As above, but all of the information is present, but the variable to which the json
  # file points to does not exist.
  def nonExistentToolOrArgumentInConstruction(self, pad, tool, argument, text, addTool, addArgument, toolError):
    print(pad, 'ERROR: Unable to construct filename for \'', tool, '\' argument \'', argument, '\'.', sep = '', end = '', file = sys.stderr)
    print(pad, 'ERROR: Variable \'', text, '\' comes from \'', addTool, '\' argument \'', addArgument, '\'.', sep = '', end = '', file = sys.stderr)
    if toolError: print(pad, 'ERROR: This tool (\'', addTool, '\') does not exist.', sep = '', end = '', file = sys.stderr)
    else: print(pad, 'ERROR: This argument (\'', addArgument, '\') does not exist.', sep = '', end = '', file = sys.stderr)
    print(file = sys.stderr)
    self.error = True

  # A required value is not given.
  def missingRequiredValue(self, newLine, pad, task, tool, argument):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: Argument \'', argument, '\' for tool \'', task, ' (', tool, ')\' is required and not set.', sep = '', file = sys.stderr)
    self.error = True

  # If a command line argument is given a value with the wrong data type, throw an error.
  def incorrectDataType(self, newLine, pad, tool, argument, value, dataType):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: Argument \'', argument, '\' in tool \'', tool, '\' expects a value of data type \'', sep = '', end = '', file = sys.stderr)
    print(dataType, '\'.  Given \'', value, '\'', sep = '', file = sys.stderr)
    self.error = True

  # If the data type specified in the configuration file is unknown, throw an error.
  def unknownDataType(self, newLine, pad, tool, argument, dataType):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: Unknown data type \'', dataType, '\' for option \'', argument, '\' in the \'', tool, sep = '', end = '', file = sys.stderr)
    print('\' configuration file.', file = sys.stderr)
    self.error = True

  # Terminate the script after errors have been found.
  def terminate(self):
    print(file = sys.stderr)
    print('================================================================================================', file = sys.stderr)
    print('  TERMINATED: Errors found in running gkno.  See specific error messages above for resolution.', file = sys.stderr)
    print('================================================================================================', file = sys.stderr)
    exit(1)








  # If no pipeline name is supplied.
  def missingPipelineName(self):
    print("ERROR: Pipeline mode was selected, but no pipeline name was supplied.", file = sys.stderr)
    self.error = True

  # Missing pipeline json configuration file.
  def missingPipelineJsonFile(self, jsonFile):
    print("ERROR: Unable to find pipeline configuration file: ", jsonFile, sep = "", file = sys.stderr)

  # If a json configuration file is malformed, terminate the script with an error.
  def jsonOpenError(self, text, error):
    print(text, "ERROR: json file is malformed: '", error, "'.", sep = '', file = sys.stderr)

  def unknownTool(self, task, tool):
    print("\tERROR: Tool name '", task, "' is associated with tool '", tool, "' but this tool", sep = "", end = "", file = sys.stderr)
    print(" is not available in the gkno package.", file = sys.stderr)
    self.error = True

  # If the pipeline configuration contains an option that is not in the tool
  # configuration file, there is an error in the linkage section of the pipeline
  # configuration file.
  def invalidToolName(self, pad, text, tool):
    print(pad, 'ERROR: Invalid tool name \'', tool, '\' in the \'', text, '\' section of the pipeline ', sep = '', end = '', file = sys.stderr)
    print('configuration file.', sep = '', file = sys.stderr)
    self.error = True

  # If an expected json block is missing from the file.
  def missingJsonEntry(self, value, tool):
    print("\t\tERROR: The json file for tool '", tool, "' is missing the entry '", value, "'.", sep = '', file = sys.stderr)
    self.error = True

  # A tool name in the pipeline configuration file is not associated
  # with an actual tool name.
  def unknownToolName(self, task):
    print("\t\tERROR: Tool name '", task, "' in the pipeline configuration is not associated", sep = "", end = "", file = sys.stderr)
    print(" with a tool available to gkno.", file = sys.stderr)
    print("\t\tERROR: Check that the tool appears in the workflow names block of the configuration file.", sep = "", file = sys.stderr)
    self.error = True

  # Each tool name appearing in the pipeline configuration file is required
  # to be unique to avoid ambiguous linkages.  If repeated names are discovered
  # give an error and terminate.
  def repeatedTool(self, task):
    print("\t\tERROR: tool name '", task, "' appears multiple times in the pipeline configuration file.", sep = "", file = sys.stderr)
    print("\t\tERROR: Ensure that all tool names are unique.", file = sys.stderr)
    self.error = True

  # Unknown command in the tools dependency list.
  def unknownArgumentInDependency(self, task, tool, argument):
    print(file = sys.stderr)
    print("\t\tERROR: Unknown argument '", argument, "' in the dependency 'arguments' for tool '", sep = '', end = '', file = sys.stderr)
    print(task, " (", tool, ")'", sep = '', file = sys.stderr)
    self.error = True

  # Error for a missing required component in a json tool option.
  def toolArgumentsError(self, text, tool, option):
    print("\t\tERROR: The '", text, "' value is not present in the tool configuration file for '", option, sep = "", end = "", file = sys.stderr)
    print("' in '", tool, "'", sep = "", file = sys.stderr)
    self.error = True

  # When parsing the pipeline configuration file, there are a list of commands that
  # are either pipeline specific or associated with a contained tool.  If the 'tool'
  # value is not present in the file, throw an error.
  def optionAssociationError(self, pad, text, option, tool):
    print(pad, 'ERROR: Value \'', text, '\' is missing for option \'', option, '\' in the \'', tool, sep = '', end = '', file = sys.stderr)
    print('\' configuration file.', file = sys.stderr)
    self.error = True

  # If a configuration file contains a default value for a flag and it isn't 'set' or 'unset',
  # throw an error.
  def unknownFlagDefault(self, task, option, value):
    print("\t\tERROR: Configuration file entry for '", task, "' flag '", option, "' should be 'set', ", sep = "", end = "", file = sys.stderr)
    print(" 'unset' or not provided.", sep = "", file = sys.stderr)
    self.error = True

  # If a value is assigned to a flag on the command line, terminate the script.
  def assignedValueToFlag(self, tool, argument):
    print("\tERROR: A value was assigned to the flag '", argument, "' in the tool '", tool, "'.", sep = "", file = sys.stderr)
    self.error = True

  # Fail if an unknown option is specified on the command line.
  def unknownOption(self, startText, tool, argument):
    print(startText, "ERROR: Unknown command line argument '", argument, "' for tool '", tool, "'", sep = "", file = sys.stderr)
    self.error = True

  # For output files designated as stubs, a list of the output extensions
  # is required.  Fail if these are missing.
  def stubNoOutputs(self, tool, option):
    print("ERROR: Output name for '", tool, "' is a stub, but the output names to be produced are not included.", sep = "", file = sys.stderr)
    print("ERROR: Ensure that the configuration file contains a list under the '", option, sep = "", end = "", file = sys.stderr)
    print("' option called \"outputs\".", file = sys.stderr)
    exit(1)

  # When building up the list of dependent files, inputs that are stubs need to have
  # the dependent files constructed.  For this to be possible the 'outputs' value
  # needs to be present in the configuration file. Terminate if it is not.
  def missingStubOutputsDependency(self, task, tool, option):
    print("\t\tERROR: Input '", option, "' to tool '", task, " (", tool, ")' is a stub.", sep = "", file = sys.stderr)
    print("\t\tERROR: A list of file extensions is required in the configuration file to determine dependent files.", sep = "", file = sys.stderr)
    print("\t\tERROR: Ensure the configuration file contains the value 'outputs' listing the extensions.", file = sys.stderr)
    self.error = True

  # If a file has an unexpected extension, flag the problem.
  def extensionError(self, option, filename, extension):
    print("\t\tERROR: File '", filename, "' does not end with the expected extension '", extension, "'", sep = "", end = "", file = sys.stderr)
    print(" (option: '", option, "')", sep = "", file = sys.stderr)
    self.error = True

  # The additional files section of the configuration file contains an unknown file
  # type.
  def unknownDependencyOrOutput(self, task, fileType):
    print("\t\tERROR: Unknown file type '", fileType, "' in the 'additional files' section of the pipeline", sep = '', file = sys.stderr)
    print("\t\tERROR: configuration file for tool '", task, "'.", sep = '', file = sys.stderr)

  # If the input file for the first tool in the pipeline is unset, terminate the script.
  def inputFileError(self, tool, option):
    print("\t\tERROR: Required input '", option, "' to the tool '", tool, "' is not specified.", sep = "", file = sys.stderr)
    self.error = True

  # If a required input file is not defined and the pipeline has a command line argument
  # for that input file, print out the pipeline argument that needs to be set before
  # terminating.
  def pipelineOption(self, tool, option, altOption):
    if altOption == '': print("\t\tERROR: This can be set on the command line using '", option, "'.", sep = "", file = sys.stderr)
    else: print("\t\tERROR: This can be set on the command line using '", option, " (", altOption, ")'.", sep = "", file = sys.stderr)

  def unsetRequiredVariable(self, task, tool, option):
    print("\t\tERROR: Required variable '", option, "' in tool '", task, " (", tool, ")' is unset.", sep = "", file = sys.stderr)
    self.error = True

  # If a file on which a tool is dependent is not defined, the script should fail with
  # an error message.
  def missingDependentFile(self, task, tool, option, isHidden):
    print("\t\tERROR: Tool '", task, " (", tool, ")' requires '", option, "' to be set in order to run.", sep = '', file = sys.stderr)
    if isHidden:
      print("\t\tERROR: This is a hidden option (i.e. is not set on the command line).", file = sys.stderr)
      print("\t\tERROR: Ensure that the pipeline configuration file links a file to this option.", file = sys.stderr)

  # If a tools input is linked to the output of another tool and its output is
  # a stub, then the configuration file must contain reference to the required
  # extension (e.g. which of the output files to use).  If this isn't provided,
  # the script should fail.
  def missingExtension(self, task, tool, option, inputToolName, inputTool):
    print("\t\tERROR: Input to tool '", task, " (", tool, ")' is defined by the output from '", sep = "", end = "", file = sys.stderr)
    print(inputToolName, " (", inputTool, ")' which is a stub.", sep = "", file = sys.stderr)
    print("\t\tERROR: Ensure the linkage section of the pipeline configuration file contains 'extension'", sep = "", file = sys.stderr)
    print("\t\tERROR: defining which of the files to use.", file = sys.stderr)
    self.error = True

  # If the input is from a previous tools output and this output is a stub, fail
  # if the requested extension is not one of the extensions specified in the
  # tools configuration file.
  def invalidStubExtension(self, task, tool, option, inputToolName, inputTool, extension):
    print("\t\tERROR: Input to tool '", task, " (", tool, ")' is defined by the output from '", sep = "", end = "", file = sys.stderr)
    print(inputToolName, " (", inputTool, ")' which is a stub.", sep = "", file = sys.stderr)
    print("\t\tERROR: The requested extension '", extension, "' is not valid.", sep = "", file = sys.stderr)
    self.error = True

  # If an incorrect command line for a tool is provided, the command line to get
  # help on the allowable arguments for that tool is printed to screen.  If the
  # help command is not provided for the tool, this cannot be printed out.
  def noHelpForTool(self, tool):
    print("ERROR: The argument for help for tool '", tool, "' is not present in the configuration file.", sep = "", file = sys.stderr)
    self.error = True

  # If an additional task is requested for one of the tools and the task is unknown
  # terminate.
  def unknownTask(self, task, tasks):
    print("\t\tERROR: Unknown additional task requested in pipeline configuration file: '", task, sep = "", end = "", file = sys.stderr)
    print("'.  Allowed tasks are:", sep = "", file = sys.stderr)
    for allowedTask in tasks:
      print("\t\t\t", allowedTask, ": ", tasks[allowedTask], sep = "", file = sys.stderr)

    self.terminate()

  # If the number of files for the rename task is incorrect, fail.
  def fileCountError(self, task, filename):
    print("\t\tERROR: The rename task requires a single input and output file for tool '", task, "'", sep = "", file = sys.stderr)
    os.remove(filename)
    self.terminate()

  # If the output from a tool is not defined by a command line argument, but the
  # configuration file contains a reference to the command line argument that
  # should be used to generate the file name and this reference is missing, fail.
  # If a requested command is not defined, throw an error.
  def missingCommand(self, task, tool, command):
    print("\tERROR: The output file for tool '", task, " (", tool, ")' requires command '", sep = "", end = "", file = sys.stderr)
    print(command, "'.", sep = "", file = sys.stderr)
    print("\tERROR: This command is not defined.", file = sys.stderr)
    self.error = True

  # For tools where the option order is important, each option must be provided
  # with an ID.  If this is not present for any of the parameters, fail.
  def missingOrderID(self, task, tool, option):
    print("\t\tERROR: The option order for tool '", task, " (", tool, ")' is important", sep = "", file = sys.stderr)
    print("\t\tERROR: Option '", option, "' does not have the 'order' parameter defined", sep = "", file = sys.stderr)
    self.error = True

  # If the position in the order of the command line arguments has already been defined,
  # fail.
  def optionIDExists(self, task, tool, option):
    print("\t\tERROR: The option order for tool '", task, " (", tool, ")' is important", sep = "", file = sys.stderr)
    print("\t\tERROR: Option '", option, "' has a non-unique value of the 'order' parameter", sep = "", file = sys.stderr)
    self.error = True

  # If the order list of arguments is missing a number, print a warning to the screen, but
  # do not terminate.  For example, if a tool has two arguments and the ids given in the
  # configuration file are 1 and 3, check that there isn't supposed to be an option 2.
  def orderWarning(self, task, tool, order):
    print("\t\tWARNING: Tool '", task, " (", tool, ")' has ordered arguments and '", order, "' is missing", sep = "", file = sys.stderr)

  # If the tool configuration file contains a dependency type that is unknown, throw
  # an error.
  def unknownDependencyType(self, text, dependencyType):
    print(text, "ERROR: Unknown format for dependencies '", dependencyType, "'.  Check documentation for allowed types.", sep = '', file = sys.stderr)
    self.error = True

  # List the allowed inputs.
  def allowableInputs(self, pl, tl):
    print("\nThe following tools can have parameters modified:", file = sys.stderr)
    for task in tl.toolArguments.keys():
      tool = pl.information['tools'][task]
      print("\t--", task, ":\t\"", task, " (", tool, ") specific options\"", sep = "", file = sys.stderr)
    print("\nPipeline specific options:", file = sys.stderr)
    for option in pl.information['arguments']:
      print("\t", option, sep = "", end = "", file = sys.stderr)
      if 'alternative' in pl.information['arguments'][option]:
        print(" (", pl.information['arguments'][option]['alternative'], ")", sep = "", end = "", file = sys.stderr)
      if 'description' in pl.information['arguments'][option]:
        print(":\t", pl.information['arguments'][option]['description'], sep = '', end = '', file = sys.stderr)
      print(file = sys.stderr)
