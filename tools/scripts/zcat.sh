#!/bin/bash

if [[ "$(uname)" == "Darwin" ]]
then
  gzcat $1
else
  zcat $1
fi
