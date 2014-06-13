#!/bin/bash

FASTQ_PATH=$1
OUTPUT=$2
MATE1_SUFFIX=$3
MATE2_SUFFIX=$4

# Set the suffixes, if not provided.
if [[ $MATE1_SUFFIX == '' ]]
then
  MATE1_SUFFIX="_1"
fi

if [[ $MATE2_SUFFIX == '' ]]
then
  MATE2_SUFFIX=${MATE1_SUFFIX/1/2}
fi

# Set up the output file.
echo '{' > $OUTPUT
echo '  "arguments" : [' >> $OUTPUT
echo '    "--fastq",' >>  $OUTPUT
echo '    "--fastq2",' >>  $OUTPUT
echo '    "--sample-name",' >> $OUTPUT
echo '    "--read-group-id"' >> $OUTPUT
echo '  ],' >> $OUTPUT
echo '  "values" : [' >> $OUTPUT

FIRST_VALUE=0
# Loop over all files in the given path.
for MATE1 in $FASTQ_PATH/*
do
  if [[ $MATE1 == *$MATE1_SUFFIX.fq || $MATE1 == *$MATE1_SUFFIX.fq.gz || $MATE1 == *$MATE1_SUFFIX.fastq || $MATE1 == *$MATE1_SUFFIX.fastq.gz ]]
  then
    MATE2=${MATE1/$MATE1_SUFFIX/$MATE2_SUFFIX}
    MATE1=$(readlink -f $MATE1)
    MATE2=$(readlink -f $MATE2)

    # If this is not the first set of values, close the previous entry.
    if [[ $FIRST_VALUE != 0 ]]
    then
      echo '    ],' >> $OUTPUT
    else
      FIRST_VALUE=1
    fi

    # If the second mate can't be found, terminate. 
    if [ ! -f $MATE2 ]
    then
      echo 'Unable to locate file: $MATE2' 1>&2
      exit 1
    fi

    # Write the fastq files to the output.
    echo '    [' >> $OUTPUT
    echo '      "'$MATE1'",' >> $OUTPUT
    echo '      "'$MATE2'",' >> $OUTPUT
    echo '      "'${MATE1/$MATE1_SUFFIX/}'",' >> $OUTPUT
    echo '      "'${MATE1/$MATE1_SUFFIX/}'"' >> $OUTPUT
  fi
done

# Finish the output file.
echo '    ]' >> $OUTPUT
echo '  ]' >> $OUTPUT
echo '}' >> $OUTPUT
