#!/usr/bin/perl -w

package commandLine;

use strict;
use Getopt::Long;

# Check the first entry on the command line is valid.
sub getMode {
  my $rTools = $_[0];
  my $mode;

  # If a mode of operation has not been defined, show the gkno
  # launcher usage information.
  if (! defined $ARGV[0]) {usage($rTools);}

  # If a pipeline has been selected set the mode to pipe
  if ($ARGV[0] eq "pipe") {
    $mode = "pipe";

  # If a non-existent tool has been selected, show the launcher
  # usage information.
  } else {
    if (! defined $rTools->{$ARGV[0]}) {
      usage($rTools);
    } else {
      $mode = "tool";
    }
  }

  return $mode;
}

# Loop over each tool in the pipeline and set up a hash of hashes.
# For each too, the set of allowed options along with default values
# if defined.
sub setupToolOptions {
  my $rPipe  = $_[0];
  my $rTools = $_[1];
  my %toolOptions;
  my %allOptions;

  foreach my $tool (@{$rPipe->{"workflow"}}) {
    $tool =~ s/"//g;
    my $toolInfo = json::evaluateString($rTools->{$tool});
    my $options  = json::evaluateString($toolInfo->{"options"});
    foreach my $option (keys %{$options}) {
      my $optionDescription = json::evaluateString($options->{$option});
      (my $default = $optionDescription->{"default"}) =~ s/"//g;
      if (exists $optionDescription->{"alternative"}) {
        (my $alternative = $optionDescription->{"alternative"}) =~ s/"//g;
        $toolOptions{$alternative} = "link:$option";
      }
      $toolOptions{$option} = $default;
    }
    $allOptions{$tool} = {%toolOptions};
    %toolOptions = ();
  }

  return \%allOptions;
}

# Parse the command line.
sub parseCommandLine {
  my $rTools      = $_[0];
  my $rPipe       = $_[1];
  my $toolOptions = $_[2];
  my $error  = 0;
  my $option;
  my $optionString;
  my %definedOptions;

  # Loop through the command line arguments, omitting the 'pipe' and the
  # pipeline name.  For each argument, check that it is valid and pass
  # the string into a hash.
  for (my $i = 2; $i < scalar(@ARGV); $i++) {

    # Check if the argument contains a '='.  If not, the next argument is
    # the string associated with this tool.
    if ($ARGV[$i] =~ /=/) {
      $option       = (split(/=/, $ARGV[$i]))[0];
      $optionString = (split(/=/, $ARGV[$i]))[1];
    } else {

      # If an '=' sign was not included the next argument should be the string
      # for this tool.  If the next argument begins with a '-', the string is
      # missing, so throw an exception.
      $option = $ARGV[$i];
      if (!defined $ARGV[$i + 1]) {
        print STDERR "ERROR: No string included for option $ARGV[$i]\n";
        $error = 1;
      } else {
        $optionString = $ARGV[$i + 1];
        $i++;
      }
    }

    # Strip off leading '-' or '--'.
    $option =~ s/^--//;
    $option =~ s/^-//;
    if (! defined $toolOptions->{$option}) {
      print STDERR "ERROR: Unknown option - ", $option, "\n";
      $error = 1;
    } else {
      $definedOptions{$option} = $optionString;
    }
  }

  # If there were errors on the command line, terminate the script.
  if ($error == 1) {
    print STDERR "ERROR: Ensure that the command line is correctly constructed.\n";
    print STDERR "\n\tAllowable inputs for pipeline $ARGV[1]:\n";
    foreach my $key (keys %{$toolOptions}) {print STDERR "\t\t$key\n";}
    exit(1);
  }

  return \%definedOptions;
}

# Parse the command line options for individual tools and ensure that
# they are valid.
sub toolCommands {
  my $exePath     = $_[0];
  my $toolOptions = $_[1];
  my $setOptions  = $_[2];
  my $rTools      = $_[3];
  my $error       = 0;
  my %toolError;
  my $configError = 0;
  my ($key, $value);
  my @userOptions = ();

  print STDOUT "Checking command line options...\n";
  foreach my $tool (keys %{$toolOptions}) {
    print STDOUT "\t$tool...\n";

    # Set the error status for the tool to zero.
    $toolError{$tool} = 0;

    # Compare the inputted options with the allowed options.  If the option
    # does not exist or has the wrong type (e.g. a string where an integer
    # is expected), the script will fail with an error.
    #@userOptions = split(/\s+/, $toolOptions->{$tool});
    if (defined $setOptions->{$tool}) {@userOptions = split(/\s+/, $setOptions->{$tool});}
    for (my $i = 0; $i < scalar(@userOptions); $i++) {
      my $option = $userOptions[$i];
      if ($option =~ /^-/) {

        if (!exists $toolOptions->{$tool}->{$option}) {
          print STDERR "\t\tERROR: Option $option is not a valid input for $tool\n";
          $error            = 1;
          $toolError{$tool} = 1;
        } else {

          # Check if this option is the alternative form.  If so, change the $option
          # variable to the primary (long form_ option.
          if ($toolOptions->{$tool}->{$option} =~ /^link:(.+)/) {$option = $1;}

          # If the option requires an argument, set the argument as the next
          # entry in userOptions.
          my $toolInfo          = json::evaluateString($rTools->{$tool});
          my $tempOptions       = json::evaluateString($toolInfo->{"options"});
          my $optionDescription = json::evaluateString($tempOptions->{$option});
          (my $type             = $optionDescription->{"type"}) =~ s/"//g;
          if ($type ne "flag") {
            print STDOUT "\t\tModified value of '$option' from $toolOptions->{$tool}->{$option} to ";
            $toolOptions->{$tool}->{$option} = $userOptions[$i + 1];
            print STDOUT "$toolOptions->{$tool}->{$option}\n";
            $i++;
          } else {
            $value = "flag";
            print STDOUT "\t\tSet flag '$option' to true\n";
          }
        }
      }
    }

    # Reset the user options.
    @userOptions = ();
  }

  # If there were command line errors, terminate the script.
  if ($error == 1) {
    print STDERR "\nERROR: Please correct the command line options (see individual error messages above).\n";
    foreach my $tool (keys %{$toolOptions}) {
      if ($toolError{$tool} == 1) {
        my $toolInfo = json::evaluateString($rTools->{$tool});
        my $toolHelp = $exePath . "/" . $toolInfo->{"path"} . "/" . $tool . " " . $toolInfo->{"help"};
        $toolHelp =~ s/"//g;
        print STDERR "\nType '$toolHelp' to see available parameters for '$tool'\n";
      }
    }
    exit(1);
  }
  if ($configError == 1) {
    print STDERR "ERROR: Please check configuration file for repeated command line definitions.\n";
    exit(1);
  }
}

# Print usage information.
sub usage {
  my $rTools = $_[0];

  print STDERR ("gkno usage: ./gkno mode [options]\n\n");
  print STDERR ("mode:\n");
  print STDERR ("\tpipe:\t\tany of the pipes available in gkno (gkno pipe help for details)\n\n");

  # Print out a list of available tools.
  foreach my $tool (sort keys %{$rTools}) {

    # Get the tool description.
    my $rHash = json::evaluateString($rTools->{$tool});
    (my $description = $rHash->{"description"}) =~ s/"//g;
    print STDERR "\t$tool:\t$description\n";
  }
  exit(1);
}

# Print usage information for pipelines:
sub pipelineUsage() {
  print STDERR "gkno pipeline usage: ./gkno pipe <pipeline name> [options]\n\n";
  print STDERR "./gkno pipe <pipeline name> --help for additional pipeline help.\n";
  exit(1);
}

# Command line.
sub pipelineCommands {
  my $rPipe = $_[0];

  # Get the allowed command line arguments from the configuration file.
  if (defined $rPipe->{"options"}) {
    print "Parsing command line options...\n";
    my $rOptions = json::evaluateString($rPipe->{"options"});
    foreach my $option (keys %{$rOptions}) {
      print "$option\n";
    }
  }
}

1;
