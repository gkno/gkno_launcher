#!/bin/bash

VCF=$1

zcat $VCF \
| cut -f -8
