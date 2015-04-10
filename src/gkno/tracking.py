#!/usr/bin/python

from __future__ import print_function
import os
import sys

import subprocess
from subprocess import PIPE

# Ping the website with usage information.
def phoneHome(sourcePath, pipeline):

  # Indicate that tracking of the run is being taken.
  print("Logging gkno usage with ID: ", pipeline, "...", sep = '', end = '', file = sys.stdout)

  # Track the pipeline.
  executable = sourcePath + '/src/gkno/ga.sh'
  subprocess.call([executable, pipeline], stdout=PIPE, stderr=PIPE)

  print('complete.')
  sys.stdout.flush()
