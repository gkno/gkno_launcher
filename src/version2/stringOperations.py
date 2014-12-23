#!/bin/bash/python

from __future__ import print_function
from difflib import SequenceMatcher

import json
import os
import random
import string
import sys

# Given a list of values and a string, return a reordered list, ranked by similarity
# the string.
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

# Return a random string of length n.
def randomString(n):
  return ''.join(random.SystemRandom().choice(string.uppercase + string.digits) for _ in xrange(n))
