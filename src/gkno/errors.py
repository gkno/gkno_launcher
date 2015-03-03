#!/usr/bin/python

from __future__ import print_function
from errno import errorcode

import inspect
from inspect import currentframe, getframeinfo

import os
import sys

class errors:

  # Initialise.
  def __init__(self):
    pass

  # Format the error message and write to screen.
  def writeFormattedText(self, text, errorType):
    firstLine = True
    secondLine = False
    maxLength = 93 - 5
    print(file = sys.stderr)
    for line in text:
      textList = []
      while len(line) > maxLength:
        index = line.rfind(' ', 0, maxLength)
        if index == -1:
          index = line.find(' ', 0, len(line))
          if index == -1:
            textList.append(line)
            line = ''
          else:
            textList.append(line[0:index])
            line = line[index + 1:len(line)]
        else:
          textList.append(line[0:index])
          line = line[index + 1:len(line)]

      if line != '' and line != ' ': textList.append(line)
      line = textList.pop(0)
      while line.startswith(' '): line = line[1:]

      if firstLine and errorType == 'error': print('ERROR:   %-*s' % (1, line), file = sys.stderr)
      elif firstLine and errorType == 'warning': print('WARNING: %-*s' % (1, line), file = sys.stderr)
      elif secondLine:
        print('DETAILS: %-*s' % (1, line), file = sys.stderr)
        secondLine = False
      else: print('         %-*s' % (1, line), file = sys.stderr)
      for line in textList:
        while line.startswith(' '): line = line[1:]
        if secondLine: print('DETAILS: %-*s' % (1, line), file = sys.stderr)
        else: print('         %-*s' % (1, line), file = sys.stderr)

      if firstLine:
        print(file = sys.stderr)
        firstLine = False
        secondLine = True

  ##################
  # Terminate gkno #
  ##################
  def terminate(self, errorCode):
    print(file=sys.stderr)
    print('================================================================================================', file=sys.stderr)
    print('  TERMINATED: Errors found in running gkno.  See specific error messages above for resolution.', file=sys.stderr)
    print('================================================================================================', file=sys.stderr)
    errcode = int(errorCode)
    sys.exit(errcode)
