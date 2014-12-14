#!/bin/bash/python

from __future__ import print_function
from difflib import SequenceMatcher

import json
import os
import sys

def findClosestPipelines(pipelines, pipeline):
  pipelineMatches = []

  # Compare the given pipeline to the available pipelines.
  for task in pipelines:
    if SequenceMatcher(None, task, pipeline).ratio() > 0.8: pipelineMatches.append(task)

  return pipelineMatches
