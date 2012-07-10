#!/usr/bin/perl -w

package json;

use strict;

# Parse a json file and return the contents in perl
# data structures.
sub fileToString {
  $json::openFilename = $_[0];
  $json::openFile     = $_[1];
  my $string    = "";
  my $newString = "";
  my $line;
  my $character;

  while(<$json::openFile>) {
    chomp;
    if (length($_) != 0) {$string = $string . $_;}
  }

  # Remove all whitespace characters from the string, unless they are
  # contained within double quotes.
  my $inQuotes = 0;
  for (my $position = 0; $position < length($string); $position++) {
    $character = substr($string, $position, 1);

    # If the character is a '"', flip inQuotes (0/1).
    if ($character eq '"') {
     ($inQuotes == 0) ? ($inQuotes = 1) : ($inQuotes = 0);
     $newString = $newString . $character;

    # Character is a whitespace charater.  If inQuotes = 0, remove this
    # character.
    } elsif ($character =~ /\s/) {
      if ($inQuotes == 1) {$newString = $newString . $character};

    # Character is anything else and so should be kept.
    } else {$newString = $newString . $character;}
  }

  # Trim the leading '{' and trailing '}'.
  #if ($newString =~ /^\{/) {$newString = substr($newString, 1);}
  #if ($newString =~ /\}$/) {$newString = substr($newString, 0, length($newString) - 1);}

  return $newString;
}

# Take a json string and break it up into its key/value pairs and
# store in a dictionary.  If the value is an object or an array, set
# the value to a hash or a list.
sub evaluateString {
  my $string   = $_[0];
  my $complete = 0;
  my $indexA;
  my $indexB;
  my $key;
  my $noOpenObjects;
  my $offset;
  my %hash;

  $indexA = index($string, ':');
  ($key   = substr($string, 0, $indexA)) =~ s/"//g;
  $string = substr($string, $indexA + 1);

  # If the key begins with a '{', then the string is an object and may have
  # multiple entries to evaluate.  If, however, the key does not begin with
  # a '{', then this is a simple key/value pair.
  if (substr($key, 0, 1) ne '{') {
    $hash{$key} = $string;
    $complete   = 1;
  } else {
    $key = substr($key, 1);
    while ($complete == 0) {

      # Determine if the value is an object or a scalar.
      if (substr($string, 0, 1) eq '{') {

        # The value is an object itself.  There will be no attempt in this
        # iteration to evaluate the object, but just add the string as the
        # value.  The end of the object needs to be found first, accounting
        # for the fact that this object may contain more nested objects.
        $noOpenObjects = 1;
        $offset        = 1;

        while($noOpenObjects > 0) {
          $indexA = index($string, '{', $offset);
          $indexB = index($string, '}', $offset);

          # No object block termination.
          if ($indexB == -1) {
            print STDERR "ERROR: Malformed json file.  No termination of key $key.\n";
            exit(1);

          # If an object is closed, decrement the noOpenObjects and set the
          # offset to $indexB, the position of the closing character.
          } elsif ($indexA == -1 || ($indexB < $indexA) ) {
            $offset = $indexB + 1;
            $noOpenObjects -= 1;

          # Another object is nested in this object.  Keep searching through the
          # string to find the end of the current object.
          } else {
            $noOpenObjects += 1;
            $offset = $indexA + 1;
          }
        }

        # When the above loop is complete, the variable offset defines the
        # position of the end of the value.
        $hash{$key} = substr($string, 0, $offset);
        $string     = substr($string, $offset);

        # If the next character in the string is a comma, there are more key/value
        # pairs to evaluate.  Trim off the comma and continue.
        if (substr($string, 0, 1) eq ',') {
          $string = substr($string, 1);
          $indexA = index($string, ':');
          ($key   = substr($string, 0, $indexA)) =~ s/"//g;
          $string = substr($string, $indexA + 1);

        # If the next character is the objects closing character, the object has
        # been successfully parsed.
        } elsif (substr($string, 0, 1) eq '}') {
          $complete   = 1;

        # Unknown character.  The object should either have more pairs and so a
        # comma should be observed, or the block should be finished and the
        # string have zero length.  Anything else suggests a malformed json file.
        } else {
          print STDERR "ERROR: Malformed json file.  No termination of key $key.\n";
          exit(1);
        }

      # The value is a list.  Currently, it is not permitted to have nested lists.
      } elsif (substr($string, 0, 1) eq '[') {
        $indexA = index($string, '[', 1);
        $indexB = index($string, ']', 1);

        # If the list is never closed, throw an error.
        if ($indexB == -1) {
          print STDERR "ERROR: A list is not properly terminated.  Check json file.";
          exit(1);

        # If another list is opened before this list is complete, terminate with
        # an error.
        } elsif ($indexA != -1 && ($indexA < $indexB)) {
          print STDERR "ERROR: Currently nested loops are not permitted.\n";
          print STDERR "Remove nested lists from file\n";
          exit(1);

        # Parse the list.
        } else {
          my $list = [];
          foreach my $element (split(/,/, substr($string, 1, $indexB - 1))) {
            push(@{$list}, "$element");
          }
          $string     = substr($string, $indexB + 1);
          $hash{$key} = $list;

          # If the next character in the string is a comma, there are more key/value
          # pairs to evaluate.  Trim off the comma and continue.
          if (substr($string, 0, 1) eq ',') {
            $string = substr($string, 1);
            $indexA = index($string, ':');
            ($key   = substr($string, 0, $indexA)) =~ s/"//g;
            $string = substr($string, $indexA + 1);

          # If the next character is the objects closing character, the object has
          # been successfully parsed.
          } elsif (substr($string, 0, 1) eq '}') {
            $complete   = 1;

          # Unknown character.  The object should either have more pairs and so a
          # comma should be observed, or the block should be finished and the
          # string have zero length.  Anything else suggests a malformed json file.
          } else {
            print STDERR "ERROR: Malformed json file.  No termination of key $key.\n";
            exit(1);
          }
        }

      # The object contains no nested objects, so just parse out the key/vaiue
      # pairs.
      } else {

        # Find the end of the value.  This will either be a ',' indicating
        # that there are more pairs to parse, or a '}', indiciating that all
        # of the pairs in the object have been parsed,
        $indexA = index($string, '}');
        $indexB = index($string, ',');

        # No termination to object block.  Throw an error.
        if ($indexA == -1) {
          print STDERR "ERROR: Malformed json file.  No termination of key $key.\n";
          exit(1);

        # This is the last/only pair in the object block.
        } elsif ($indexB == -1 || $indexA < $indexB) {
          $hash{$key} = substr($string, 0, $indexA);
          $string     = substr($string, $indexA + 1);
          $complete   = 1;

        # There are more pairs in this object.
        } elsif ($indexB < $indexA) {
          $hash{$key} = substr($string, 0, $indexB);
          $string     = substr($string, $indexB + 1);
          $indexA     = index($string, ':');
          ($key       = substr($string, 0, $indexA)) =~ s/"//g;
          $string = substr($string, $indexA + 1);
        }
      }
    }
  }

  return \%hash;
}

sub error {
  print STDERR "ERROR: $_[0]\n";
  exit(1);
}

1;
