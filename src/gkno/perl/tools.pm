#!/usr/bin/perl -w

package tools;

use strict;

# Find the current date and time.
sub findTime {
  my @months = qw(Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec);
  my @days   = qw(Sun Mon Tue Wed Thu Fri Sat);
  my ($second, $minute, $hour, $dayofmonth, $month, $year, $dayofweek, $dayofyear, $daylightsavings);
  my $time;

  ($second, $minute, $hour, $dayofmonth, $month, $year, $dayofweek, $dayofyear, $daylightsavings) = localtime();
  $year += 1900;
  $time = sprintf("%02d%s%02d%s%02d%s", $hour, ":", $minute, ":", $second, " on $days[$dayofweek], $months[$month] $dayofmonth, $year");
  $month += 1;

  return ($time, $dayofmonth, $month, $year);
}

# Search a directory for json files and return a reference
# to a list.
sub getJsonFiles {
  my $dir = $_[0];
  my @jsonFiles;

  opendir DIR, $dir or die "cannot open dir $dir: $!";
  my @files = readdir DIR;
  closedir DIR;

  foreach my $file (@files) {
    if ($file =~ /\.json/) {push(@jsonFiles, $file);}
  }

  return \@jsonFiles;
}

# From the list of json files, popluate a hash table with the names
# and descriptions of the tools.
sub getToolDescriptions {
  my $sourcePath = $_[0];
  my $toolFiles  = $_[1];
  my %tools;

  foreach my $tool (@{$toolFiles}) {

    # Open the json file and get the tool description.
    my $fileHandle;
    my $file = "$sourcePath/config_files/tools/$tool";
    open($fileHandle, "<$file");
    my $string = json::fileToString($tool, $fileHandle);
    my $rTool  = json::evaluateString($string);
    close($fileHandle);

    # Get the information on the executables.
    $string  = $rTool->{"executables"};
    my $rExe = json::evaluateString($string);

    foreach my $exe (keys %{$rExe}) {
      $tools{$exe} = $rExe->{$exe};
    }
  }

  return \%tools;
}

1;
