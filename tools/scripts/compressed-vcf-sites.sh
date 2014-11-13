#!/bin/bash

VCF=$1
SITES=$2

if [[ "$(uname)" == "Darwin" ]]
then
  gzcat $VCF | cut -f -8 | gzip > $SITES
else
  zcat $VCF | cut -f -8 | gzip > $SITES
fi
