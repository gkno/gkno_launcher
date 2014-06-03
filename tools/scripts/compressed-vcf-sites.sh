#!/bin/bash

VCF=$1
SITES=$2

zcat $VCF \
| cut -f -8 \
| gzip > $SITES
