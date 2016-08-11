#!/bin/bash

INPUT=/dev/stdin
if [ $# == 0 ]; then
  OUTPUT=/dev/stdout
elif [ $# == 1 ]; then
  OUTPUT=$1
else
  echo "Unknown arguments on command line"
  exit 1
fi

more -f $INPUT | cut -f 9 | cut -d ';' -f 5 | cut -d '"' -f 2 | sort | uniq > $OUTPUT
