#!/bin/bash

COV=$1
MAX1=$2
MAX=$(($MAX1 + 1))
BIN=0

# Define a temporary file name based on the input.
TEMP=$1".temp"
TEMPBINS=$TEMP"_bin.txt"

# Parse the autosome and get the top $MAX coverage values.
for i in {1..22}
do
  TEMPFILE=$TEMP"_"$i".txt"
  TEMPFILEB=$TEMP"_"$i".txt.tmp"
  grep -P "^$i\t" $COV | head -n $MAX | tail -n $MAX1 | cut -f 3 > $TEMPFILE

  # Add chromosome if file is not empty, else delete the file.
  if [ -s $TEMPFILE ]
  then
    echo $i | cat - $TEMPFILE > $TEMPFILEB
    mv $TEMPFILEB $TEMPFILE

    # Add the bins.
    if [[ $BIN == 0 ]]
    then
      echo "bin" > $TEMPBINS
      grep -P "^$i\t" $COV | head -n $MAX | tail -n $MAX1 | cut -f 2 >> $TEMPBINS
      BIN=1
    fi
  else
    rm -f $TEMPFILE
  fi
done

# Include the sex chromosomes.
TEMPFILE=$TEMP"_X.txt"
TEMPFILEB=$TEMP"_X.txt.tmp"
grep -P "^X\t" $COV | head -n $MAX | tail -n $MAX1 | cut -f 3 > $TEMPFILE
if [ -s $TEMPFILE ]
then
  echo X | cat - $TEMPFILE >> $TEMPFILEB
  mv $TEMPFILEB $TEMPFILE
else
  rm -f $TEMPFILE
fi

TEMPFILE=$TEMP"_Y.txt"
TEMPFILEB=$TEMP"_Y.txt.tmp"
grep -P "^Y\t" $COV | head -n $MAX | tail -n $MAX1 | cut -f 3 > $TEMPFILE
if [ -s $TEMPFILE ]
then
  echo Y | cat - $TEMPFILE >> $TEMPFILEB
  mv $TEMPFILEB $TEMPFILE
else
  rm -f $TEMPFILE
fi

# Paste all the columns together.
command="paste $TEMPBINS"
for i in {1..22}
do
  if [ -f $TEMP"_"$i".txt" ]
  then
    command="$command "$TEMP"_"$i".txt"
  fi
done
if [ -f $TEMP"_X.txt" ]
then
  command="$command "$TEMP"_X.txt"
fi
if [ -f $TEMP"_Y.txt" ]
then
  command="$command "$TEMP"_Y.txt"
fi
$command

# Delete the temporary files.
for i in {1..22}
do
  TEMPFILE=$TEMP"_"$i".txt"
  rm -f $TEMPFILE
done
TEMPFILE=$TEMP"_X.txt"
rm -f $TEMPFILE
TEMPFILE=$TEMP"_Y.txt"
rm -f $TEMPFILE
rm -f $TEMPBINS
