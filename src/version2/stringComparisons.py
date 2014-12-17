#!/bin/bash/python

from __future__ import print_function
from difflib import SequenceMatcher

import json
import os
import sys

def rankListByString(inputList, queryString):

  # Loop over the list and store the value with it's match score.
  scores = []
  for listString in inputList: scores.append((int( 1000 * SequenceMatcher(None, listString.lower(), queryString.lower()).ratio()), listString))

  # Generate the ranked list.
  rankedList = []
  for score, listString in sorted(scores): rankedList.append(listString)
  rankedList.reverse()

  # Return the ranked list.
  return rankedList
