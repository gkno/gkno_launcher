from __future__ import print_function
import json
import os.path
import sys

__author__ = "alistair ward"
__version__ = "version 0.01"
__date__ = "may 2012"

def main():

  # Define the source path of all the gkno machinery.
  filename = os.path.abspath(sys.argv[1])

  # The name of the tool for which parameters are required is the third
  # argument in the command line.
  tool     = sys.argv[2]

  # Open the json file
  jsonData = open(filename)
  data     = json.load(jsonData)
  command  = ""
  for parameter in data['parameters'][tool]:
    command += str(parameter) + ' ' + str(data['parameters'][tool][parameter]) + ' '

  print(command)

if __name__ == "__main__":
  main()
