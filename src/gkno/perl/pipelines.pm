#!/usr/bin/perl -w

package pipelines;

use strict;
use File::Find;
no strict "refs";

# If a pipeline is being run, search for the corresponding config file.
sub getPipelineConfig {
  my $path = $_[0];
  my $jsonFile;

  # If the pipeline name was not given, throw an error.
  if (! defined $ARGV[1]) {commandLine::pipelineUsage();}

  my $pipelineConfig = "$path/config_files/pipes/" . $ARGV[1] . ".json";
  if (! -f $pipelineConfig) {
    print STDERR "ERROR: Unable to find pipeline configuration file: $pipelineConfig\n";
    print STDERR "ERROR: Available pipelines:\n";

    # Find all the available json files and give a list of the available
    # pipelines.
    $jsonFile = find(\&jsonFileSearch, "$path/config_files/pipes");
    print $jsonFile, "\n";
    exit(1);
  }

  return $pipelineConfig;
}

# Search a directory for json files.
sub jsonFileSearch {
  chomp;
  if ($_ =~ /\.json$/) {
    print STDERR "\t$_\n";
  }
}

# Print to screen information about the selected pipeline.
sub information {
  my $time   = $_[0];
  my $rPipe  = $_[1];
  my $rTools = $_[2];

  print "\n=================================\n";
  print "  Boston College gkno pipeline\n";
  print "  $time\n";
  print "=================================\n\n";
  print "Executing pipeline: $ARGV[1]\n\n";
  print "Workflow:\n";
  foreach my $element (@{$rPipe->{"workflow"}}) {
    (my $tool        = $element) =~ s/"//g;
    my $rToolInfo    = json::evaluateString($rTools->{$tool});
    (my $description = $rToolInfo->{"description"}) =~ s/"//g;
    print "\t$tool\t$description\n";
  }
  print "\n";
}

# Check that the input files for each component are consistent with
# the output file of the previous component.
sub checkFlowConsistency {
  my $rPipe    = $_[0];
  my $rTools   = $_[1];
  my ($rToolInfo, $toolA, $toolB, $toolAInputFormat, $toolAOutputFormat, $toolBInputFormat, $toolBOutputFormat);
  my @workflow = @{$rPipe->{"workflow"}};
  my $failed   = 0;

  print "\nChecking flow consistency...\n";

  # For each tool, the relevant configuration file (json) entry is
  # evaluated.
  ($toolA = (split(/,/, $workflow[0]))[0]) =~ s/"//g;
  $rToolInfo         = json::evaluateString($rTools->{$toolA});
  ($toolAInputFormat  = $rToolInfo->{"input format"}) =~ s/"//g;
  ($toolAOutputFormat = $rToolInfo->{"output format"}) =~ s/"//g;
  foreach my $i (1..$#workflow) {
    ($toolB = (split(/,/, $workflow[$i]))[0]) =~ s/"//g;
    $rToolInfo         = json::evaluateString($rTools->{$toolB});
    ($toolBInputFormat  = $rToolInfo->{"input format"}) =~ s/"//g;
    ($toolBOutputFormat = $rToolInfo->{"output format"}) =~ s/"//g;
    print "\t$toolA -> $toolB... ";
    if ($toolAOutputFormat eq $toolBInputFormat) {
      print "ok.\n";
    } else {
      print "failed.\n";
      $failed = 1;
    }

    # Now iterate the tools, so the tool that was second (toolB) is now
    # first and the new toolB will be taken from the workflow.
    $toolA             = $toolB;
    $toolAInputFormat  = $toolBInputFormat;
    $toolAOutputFormat = $toolBOutputFormat;
  }

  # If an inconsistency was found, terminate the program.
  if ($failed != 0) {
    print "ERROR: Pipeline workflow is inconsistent with file formats.\n";
    exit(1);
  }
}

# Look for options for each of the tools specified in the pipeline config
# file.
sub updateOptions {
  my $toolOptions = $_[0];
  my $rTools      = $_[1];
  my $rPipe       = $_[2];
  my $error       = 0;

  print STDOUT "Checking pipeline configuration for additional parameters...\n";
  foreach my $tool (@{$rPipe->{"workflow"}}) {
    print STDOUT "\t$tool...\n";
    my $bob = json::evaluateString($rPipe->{"parameters"});
    if (exists $bob->{$tool}) {
      my $options = json::evaluateString($bob->{$tool});
      foreach my $option (keys %{$options}) {
        (my $value = $options->{$option}) =~ s/"//g;

        # Check that the configuration file includes a valid option for
        # this tool.
        if (!exists $toolOptions->{$tool}->{$option}) {
          print STDERR "\t\tERROR: Pipeline configuration file contains an invalid option for $tool ($option)\n";
          $error = 1;
        } else {
          $toolOptions->{$tool}->{$option} = $value;
        }
      }
    }
  }
  print STDOUT "\n";

  # If there were errors with the parameters in the configuration file,
  # terminate the program.
  if ($error == 1) {
    print STDERR "ERROR: Correct the pipeline configuration file.\n";
    exit(1);
  }
}

# The set of tools and the associated parameters are set
# in the config file, so build up the scripts to run the
# pipeline.
sub generateMakefile {
  my $exePath     = $_[0];
  my $rPipe       = $_[1];
  my $rTools      = $_[2];
  my $toolOptions = $_[3];
  my $error = 0;
  my $dependencyList;
  my %outputOptions;
  my $outputFiles;

  # Open a script file.
  open(my $makeFilehandle, ">Makefile");

  print STDOUT "\nGenerating Makefile...\n";
  print $makeFilehandle "### Makefile for pipeline\n\n";
  print $makeFilehandle "TOOL_BIN=$exePath\n";
  print $makeFilehandle "RESOURCES=$exePath/resources\n\n";

  # Loop over each tool in the work flow and generate the command lines
  # for each.  Work in reverse order building up the dependencies.
  for my $i (reverse 0..$#{$rPipe->{"workflow"}}) {
    (my $tool         = ${$rPipe->{"workflow"}}[$i]) =~ s/"//g;
    my $toolVariables = json::evaluateString($rTools->{$tool});
    my $options       = json::evaluateString($toolVariables->{"options"});

    # Loop over all of the options for this tool.  Determine which files
    # are required to list as dependencies in the Makefile.
    $dependencyList   = extractDependencies($makeFilehandle, $toolVariables, $toolOptions, $tool, $dependencyList);

    # Determine the output file(s).  If the output is a stub, find the names
    # of all of the output files.
    $outputFiles = findOutputFiles($makeFilehandle, $toolOptions, $options, $tool, $outputFiles);
  }

  # Having established all the dependencies and the output files for each
  # tool, write out the commands for the Makefile.
  print $makeFilehandle "./PHONY: all\n";
  print $makeFilehandle "all:";
  for my $i (reverse 0..$#{$rPipe->{"workflow"}}) {
    (my $tool         = ${$rPipe->{"workflow"}}[$i]) =~ s/"//g;
    foreach my $output (@{$outputFiles->{$tool}}) {print $makeFilehandle " $output";}
  }
  print $makeFilehandle "\n\n";
  for my $i (reverse 0..$#{$rPipe->{"workflow"}}) {
    (my $tool         = ${$rPipe->{"workflow"}}[$i]) =~ s/"//g;
    my $toolVariables = json::evaluateString($rTools->{$tool});
    my $pathVariable  = writeInitialInformation($makeFilehandle, $toolVariables, $tool);
    my $options       = json::evaluateString($toolVariables->{"options"});
    generateCommand($makeFilehandle, $outputFiles, $dependencyList, $toolVariables, $pathVariable, $tool, $toolOptions, $error);
  }

  # Close the Makefile.
  close($makeFilehandle);

  # If there were any undefined files, terminate the program.
  if ($error != 0) {
    print STDERR "ERROR: Please define the necessary files.\n";
    exit(1);
  }
  print "\n";
}

# Write initial information to the Makefile.
sub writeInitialInformation {
  my $makeFilehandle = $_[0];
  my $toolVariables  = $_[1];
  my $tool           = $_[2];

  print STDOUT "\t$tool...\n";
  print $makeFilehandle "### Information for $tool\n";
  (my $path        = $toolVariables->{"path"}) =~ s/"//g;
  my $pathVariable = uc($tool . "_PATH");
  print $makeFilehandle "$pathVariable=\$(TOOL_BIN)/$path\n";

  return $pathVariable;
}

# Extract the files that the tool is dependent on.
sub extractDependencies {
  my $makeFilehandle = $_[0];
  my $toolVariables  = $_[1];
  my $toolOptions    = $_[2];
  my $tool           = $_[3];
  my $dependencyList = $_[4];

  if (exists $toolVariables->{"dependencies"}) {
    my @dependencies = @{$toolVariables->{"dependencies"}};
    foreach my $value (@dependencies) {
      $value =~ s/"//g;
      my $options = json::evaluateString($toolVariables->{"options"});
      foreach my $option (keys %{$options}) {
        my $titleString = json::evaluateString($options->{$option});
        (my $title = $titleString->{"title"}) =~ s/"//g;
        if (! exists $dependencyList->{$tool}) {$dependencyList->{$tool} = "";}
        if ($title eq $value) {$dependencyList->{$tool} = $dependencyList->{$tool} . " " . $toolOptions->{$tool}->{$option};}
      }
    }
  }

  return $dependencyList;
}

# Search through all the options and find all the output files.  If
# the defined output is just a stub, find the full names of all of the
# output files.
sub findOutputFiles {
  my $makeFilehandle = $_[0];
  my $toolOptions    = $_[1];
  my $options        = $_[2];
  my $tool           = $_[3];
  my $outputFiles    = $_[4];

  foreach my $option (keys %{$options}) {
    my $optionInfo  = json::evaluateString($options->{$option});
    (my $title = $optionInfo->{"title"}) =~ s/"//g;
    if ($title eq "OUTPUT") {
      my $stub = 0;
    
      # Check if the stub variable is set to true (if included in the configuration
      # file).
      if (exists $optionInfo->{"stub"}) {if ($optionInfo->{"stub"} =~ /true/) {$stub = 1;}}
      if ($stub == 0) {
        if (! exists $outputFiles->{$tool}) {$outputFiles->{$tool} = ();}
        push(@{$outputFiles->{$tool}}, $toolOptions->{$tool}->{$option});
      } else {

        # If the output is a stub, make sure that all of the output names to be
        # produced are included in a list.
        if (! exists $optionInfo->{"outputs"}) {
          print STDERR "ERROR: Output name for '$tool' is a stub, but the output names to be produced are not included.\n";
          print STDERR "ERROR: Ensure that the configuration file contains a list under the '$option' option called \"outputs\".\n";
          exit(1);
        } else {
          foreach my $name (@{$optionInfo->{"outputs"}}) {
            $name =~ s/"//g;
            my $outputFile = $toolOptions->{$tool}->{$option} . $name;
            if (! exists $outputFiles->{$tool}) {$outputFiles->{$tool} = ();}
            push(@{$outputFiles->{$tool}}, $outputFile);
          }
        }
      }
    }
  }

  return $outputFiles;
}

sub generateCommand {
  my $makeFilehandle = $_[0];
  my $outputFiles    = $_[1];
  my $dependencyList = $_[2];
  my $toolVariables  = $_[3];
  my $pathVariable   = $_[4];
  my $tool           = $_[5];
  my $toolOptions    = $_[6];
  my $error          = $_[7];

  # Print out the output file and the list of dependencies.
  for my $i (0..$#{$outputFiles->{$tool}}) {
    if ($i != 0) {print $makeFilehandle " ";}
    print $makeFilehandle $outputFiles->{$tool}->[$i];
  }
  print $makeFilehandle ":$dependencyList->{$tool}\n\t";

  # Print out the command line.
  if (exists $toolVariables->{"precommand"}) {
    (my $precommand = $toolVariables->{"precommand"}) =~ s/"//g;
    print $makeFilehandle "$precommand ";
  }
  print $makeFilehandle "\$($pathVariable)/$tool";
  if (exists $toolVariables->{"modifier"}) {
    (my $modifier = $toolVariables->{"modifier"}) =~ s/"//g;
    print $makeFilehandle " $modifier";
  }

  # Include all of the set options.
  foreach my $option (keys %{$toolOptions->{$tool}}) {

    # Check the value of the option.  If it is silent, do not
    # print it out.
    if ($toolOptions->{$tool}->{$option} eq "user input") {
      print STDERR "\t\tERROR: Required option '$option' is unset for tool '$tool'\n";
      $error = 1;
    } elsif ($toolOptions->{$tool}->{$option} ne "silent" && $toolOptions->{$tool}->{$option} !~ /^link:/) {
      print $makeFilehandle " \\\n\t$option $toolOptions->{$tool}->{$option}";
    }
  }
  print $makeFilehandle "\n\n";

  return $error;
}

1;
