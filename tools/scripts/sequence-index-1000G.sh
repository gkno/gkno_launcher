#!/bin/bash

TYPE=$1
INDEX=$2
MERGE=$3
FASTQ_DIR=$4
#FASTQ_DIR="$(pwd)"/"$(basename $4)"

## FUNCTIONS

# Function for initial contents of a json file.
write_initial_align_file()
{
  local type=$1
  local filename="$1_end_reads.json"

  echo '{' > $filename
  echo '  "arguments" : [' >> $filename
  echo '    "--fastq",' >> $filename
  if [[ $type == 'paired' ]]
  then
    echo '    "--fastq2",' >> $filename
  fi
  echo '    "--out",' >> $filename
  echo '    "--sample",' >> $filename
  echo '    "--center",' >> $filename
  echo '    "--sequencing-technology",' >> $filename
  echo '    "--read-group",' >> $filename
  echo '    "--library",' >> $filename
  echo '    "--platform-name"' >> $filename
  echo '  ],' >> $filename
  echo '  "values" : {' >> $filename
}

# Write the run specific information to the json file.
write_data_to_align_file()
{
  local filename="$1_end_reads.json"
  local sample=$2
  local centre=$3
  local sequencing_technology=$4
  local read_group=$5
  local library=$6
  local lane=$7
  local id=$8
  local fastq=$9
  local fastq2=${10}

  # Define the output filename.
  local output=`echo "$fastq" | cut -d '.' -f 1`
  if [[ $1 == 'paired' ]]
  then
    output=${output%?}
    output=${output%?}
  fi
  output="$output.$1.mkb"

  if [[ $id == 0 ]]
  then
    echo -e "    \"$id\" : [" >> $filename
  else
    echo -e ",\n    \"$id\" : [" >> $filename
  fi
  echo -e "      \"$FASTQ_DIR/$fastq\"," >> $filename
  if [[ $1 == 'paired' ]]
  then
    echo -e "      \"$FASTQ_DIR/$fastq2\"," >> $filename
  fi
  echo -e "      \"$output\"," >> $filename
  echo -e "      \"$sample\"," >> $filename
  echo -e "      \"$centre\"," >> $filename
  echo -e "      \"$sequencing_technology\"," >> $filename
  echo -e "      \"$read_group\"," >> $filename
  echo -e "      \"$library\"," >> $filename
  echo -e "      \"$lane\"" >> $filename
  echo -e "    ]\c" >> $filename
}

# Finish writing the align json file.
write_end_align_file()
{
  filename=$1
  echo >> $filename
  echo '  }' >> $filename
  echo '}' >> $filename
}

# Write the initial information to the merge sample input json files.
write_initial_merge_file()
{
  local filename="sample.merge.json"

  echo '{' > $filename
  echo '  "arguments" : [' >> $filename
  echo '    "--bam-list",' >> $filename
  echo '    "--out"' >> $filename
  echo '  ],' >> $filename
  echo '  "values" : {' >> $filename
}

# Write sample specific information to the merge file.
write_merge_file()
{
  local sample=$1
  local id=$2
  local total_number=$3
  local filename="sample.merge.json"

  echo "    \"$id\" : [" >> $filename
  echo "      \"${PWD}/$sample.1000G.bam_list.json\"," >> $filename
  echo "      \"$sample.merged.bam\"" >> $filename
  if [[ $id == $total_number ]]
  then
    echo "    ]" >> $filename
  else
    echo "    ]," >> $filename
  fi
}

write_end_merge_file()
{
  local filename="sample.merge.json"

  echo "  }" >> $filename
  echo "}" >> $filename
}

# Check that the fastq file(s) exist.
check_fastq()
{
  local fastq1=$1
  local fastq2=$2
  local file1="$FASTQ_DIR/$fastq1"
  local file2="$FASTQ_DIR/$fastq2"

  if [[ ! -f $file1 ]]
  then
    echo "Missing fastq file: $file1" 1>&2
    rm -f ./single_end_reads.json
    rm -f ./paired_end_reads.json
    exit 1
  fi
  if [[ $fastq2 != '' ]]
  then
    if [[ ! -f $file2 ]]
    then
      echo "Missing fastq file: $file2" 1>&2
      rm -f ./single_end_reads.json
      rm -f ./paired_end_reads.json
      exit 1
    fi
  fi
}

## END OF FUNCTIONS


# Check that the requested analysis is for single-end, paired end reads or both.
if [[ $TYPE != "s" ]] && [[ $TYPE != "p" ]] && [[ $TYPE != "b" ]]
then
  echo -e "Usage: 1000G_script.sh <analysis type> <sequence index file> <merge samples>" 1>&2
  echo -e "\tanalysis type:" 1>&2
  echo -e "\t\t's' - single end reads only," 1>&2
  echo -e "\t\t'p' - paired end reads only," 1>&2
  echo -e "\t\t'b' - both single and paired end read." 1>&2
  exit 1
fi

# Check that the index file exists.
if [[ ! -f $INDEX ]]
then
  echo -e "Usage: 1000G_script.sh <analysis type> <sequence index file> <merge samples>" 1>&2
  echo -e "\tIndex file does not exist." 1>&2
  exit 1
fi

# Check if merge is set to 'true' or 'false'.
if [[ $MERGE != 'True' ]] && [[ $MERGE != 'False' ]]
then
  echo -e "Usage: 1000G_script.sh <analysis type> <sequence index file> <merge samples>" 1>&2
  echo -e "\tThe merge samples option must be set to 'True' or 'False'" 1>&2
  echo -e "\tCurrent value is: $MERGE" 1>&2
  exit 1
fi

# Check that no files of the form *.bam_list.json exist.
if [[ $MERGE == 'True' ]]
then
  ls *.1000G.bam_list.json > /dev/null 2> /dev/null
  if [[ $? == 0 ]]
  then
    echo "ERROR"
    echo
    echo "When executed, there can exist no files of the form *.1000G.bam_list.json"
    echo "in the current directory.  Please move or remove those files from"
    echo "this directory before proceeding."
    exit 1
  fi
fi

# Set the directory for the fastq files.
if [[ $FASTQ_DIR == '' ]]
then
  FASTQ_DIR="${PWD}/fastq"
fi

# Define some variables.
NO_SINGLE_READS=0
NO_PAIRED_READS=0
SINGLE_COUNT=0
PAIRED_COUNT=0
unset SAMPLE_LIST

# Open json files for the single and paired end reads as necessary.
if [[ $TYPE != 'p' ]]
then
  write_initial_align_file 'single'
fi

if [[ $TYPE != 's' ]]
then
  write_initial_align_file 'paired'
fi

# Parse the sequence index file.
while read line
do
  FASTQ=`echo "$line" | cut -f 1 | cut -d '/' -f 4`
  FASTQ2=`echo "$line" | cut -f 20 | cut -d '/' -f 4`
  SAMPLE=`echo "$line" | cut -f 10`
  CENTRE=`echo "$line" | cut -f 6`
  READ_GROUP=`echo "$line" | cut -f 3`
  LIBRARY=`echo "$line" | cut -f 15`
  LANE=`echo "$line" | cut -f 14`
  TECH=`echo "$line" | cut -f 13`
  LIBRARY_TYPE=`echo "$line" | cut -f 20`
  if [[ $LIBRARY_TYPE == '' ]]
  then
    LIBRARY_TYPE='SINGLE'
  else
    LIBRARY_TYPE='PAIRED'
  fi

  # Handle the single end reads.
  if [[ $LIBRARY_TYPE == 'SINGLE' ]] && [[ $TYPE != 'p' ]]
  then
    write_data_to_align_file 'single' "$SAMPLE" "$CENTRE" "$TECH" "$READ_GROUP" "$LIBRARY" "$LANE" "$NO_SINGLE_READS" "$FASTQ"
    if [[ $MERGE == 'True' ]]
    then
      if [ ! -f $SAMPLE.1000G.bam_list.json ]
      then
        echo '{' >> $SAMPLE.1000G.bam_list.json
        echo -e "  \"filename list\" : [\c" >> $SAMPLE.1000G.bam_list.json
      fi
      NO_LINES=`wc -l $SAMPLE.1000G.bam_list.json | cut -d " " -f 1`
      if [[ $NO_LINES == 1 ]]
      then
        echo -e "\n    \""${PWD}"/"$READ_GROUP".single.sorted.recal.bam\"\c" >> $SAMPLE.1000G.bam_list.json
      else
        echo -e ",\n    \""${PWD}"/"$READ_GROUP".single.sorted.recal.bam\"\c" >> $SAMPLE.1000G.bam_list.json
      fi
    fi
    NO_SINGLE_READS=$(($NO_SINGLE_READS + 1))

    # Check that the fastq file exists.
    check_fastq $FASTQ

    # Add the sample to the list of processed samples.
    SAMPLE_LIST=("${SAMPLE_LIST[@]}" "$SAMPLE")
  fi

  # Handle the paired end reads.  Only handle paired end reads if the name
  # ends with 'xxx_1.fastq.gz' to avoid double inclusion.
  if [[ $LIBRARY_TYPE == 'PAIRED' ]] && [[ $TYPE != 's' ]]
  then
    WHICH_READ=`echo "$FASTQ" | cut -d '.' -f 1`
    if [[ $WHICH_READ == *_1 ]]
    then
      write_data_to_align_file 'paired' "$SAMPLE" "$CENTRE" "$TECH" "$READ_GROUP" "$LIBRARY" "$LANE" "$NO_PAIRED_READS" "$FASTQ" "$FASTQ2"
      if [[ $MERGE == 'True' ]]
      then
	if [ ! -f $SAMPLE.1000G.bam_list.json ]
        then
	  echo '{' >> $SAMPLE.1000G.bam_list.json
	  echo -e "  \"filename list\" : [\c" >> $SAMPLE.1000G.bam_list.json
	fi
	NO_LINES=`wc -l $SAMPLE.1000G.bam_list.json | cut -d " " -f 1`
        if [[ $NO_LINES == 1 ]]
        then
          echo -e "\n    \""${PWD}"/"$READ_GROUP".paired.sorted.recal.bam\"\c" >> $SAMPLE.1000G.bam_list.json
        else
          echo -e ",\n    \""${PWD}"/"$READ_GROUP".paired.sorted.recal.bam\"\c" >> $SAMPLE.1000G.bam_list.json
        fi
      fi
      NO_PAIRED_READS=$(($NO_PAIRED_READS + 1))

      # Check that the fastq file exists.
      check_fastq $FASTQ $FASTQ2
  
      # Add the sample to the list of processed samples.
      SAMPLE_LIST=("${SAMPLE_LIST[@]}" "$SAMPLE")
    fi
  fi

done < $INDEX

# Find all of the unique samples in the sample_list.
for sample in ${SAMPLE_LIST[@]}
do
  echo $sample
done | sort | uniq > temp_samples.txt

SAMPLE_ID=0
NO_SAMPLES=`wc -l temp_samples.txt | cut -d ' ' -f 1`
NO_SAMPLES=$(($NO_SAMPLES - 1))
if [[ $MERGE == "True" ]]
then
  write_initial_merge_file
  while read sample
  do
    write_merge_file $sample $SAMPLE_ID $NO_SAMPLES
    SAMPLE_ID=$(($SAMPLE_ID + 1))
  done < temp_samples.txt
  write_end_merge_file
fi
rm -f temp_samples.txt

#
for file in *.bam_list.json
do
  echo -e "\n  ]" >> $file
  echo -e "}" >> $file
done

# Finish writing the json files, or delete if nothing was addded to them.
if [[ $NO_SINGLE_READS == 0 ]]
then
  rm -f ./single_end_reads.json
else
  write_end_align_file 'single_end_reads.json'
fi

if [[ $NO_PAIRED_READS == 0 ]]
then
  rm -f ./paired_end_reads.json
else
  write_end_align_file 'paired_end_reads.json'
fi
