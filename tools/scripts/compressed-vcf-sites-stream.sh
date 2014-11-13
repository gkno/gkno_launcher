#!/bin/bash

VCF=$1

if [[ "$(uname)" == "Darwin" ]]
then
  gzcat $VCF | cut -f -8
else
  zcat $VCF | cut -f -8
fi
