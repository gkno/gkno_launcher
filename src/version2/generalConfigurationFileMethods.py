#!/bin/bash/python

from __future__ import print_function
import generalConfigurationFileErrors as er

import json
import os
import sys

# Check that the supplied value is a dictionary.
def checkIsDictionary(node, allowTermination):
  success = True
  if not isinstance(node, dict):
    #TODO ERROR
    if allowTermination: print('generalConfig.checkIsDictionary - 1'); exit(0) # nodeIsNotADictionary
    else: success = False

  return success

# Check that the supplied dictionary has an id field.
def checkForId(node, allowTermination):
  try: return node['id']
  except:
    if allowTermination: print('generalConfig.checkForId - 1'); exit(0)
    return False

# Check that the supplied dictionary has an id field.
def checkForLongFormArgument(node, allowTermination):
  try: return node['long form argument']
  except:
    if allowTermination: print('generalConfig.checkForLongFormArgument - 1'); exit(0)
    return False

# Check general attribute information.
def checkAttributes(data, allowedAttributes, attributes, allowTermination, helpInfo):
  success = True
  errors  = er.generalConfigurationFileErrors()

  # Keep track of the observed required values.
  observedAttributes = {}

  # Loop over all of the attributes in the configuration file.
  for attribute in data:

    # If the value is not in the allowedAttributes, it is not an allowed value and execution
    # should be terminate with an error.
    if attribute not in allowedAttributes:
      if allowTermination: errors.invalidAttribute(attribute, allowedAttributes, helpInfo)
      else: return False, None

    # Mark this values as having been observed,
    observedAttributes[attribute] = True

    # Check that the value given to the attribute is of the correct type. If the value is unicode,
    # convert to a string first.
    value = str(data[attribute]) if isinstance(data[attribute], unicode) else data[attribute]
    if allowedAttributes[attribute][0] != type(value):
      #TODO ERROR
      if allowTermination: print('generalConfig.checkAttributes - 2'); exit(0) # incorrectTypeInPipelineConfigurationFile
      else: return False, None

    # At this point, the attribute in the configuration file is allowed and of valid type. Check that 
    # the value itself is valid (if necessary) and store the value.
    #if allowedAttributes[attribute][2]: setattr(self, attribute, value)
    if allowedAttributes[attribute][2]: setAttribute(attributes, allowedAttributes[attribute][3], value)

  # Having parsed all of the general attributes attributes, check that all those that are required
  # are present.
  for attribute in allowedAttributes:
    if allowedAttributes[attribute][1] and attribute not in observedAttributes:
      if allowTermination: errors.missingAttribute(attribute, helpInfo)
      else: return False, None

  return True, attributes

# Set a value in the toolAttributes.
def setAttribute(attributes, attribute, value):
  try: test = getattr(attributes, attribute)

  # If the attribute can't be set, determine the source of the problem and provide an
  # error message.
  #TODO ERROR
  except: print('generalConfig.setAttributes - 1 ', attribute); exit(0) # invalidAttributeInSetAttribute

  # Set the attribute.
  setattr(attributes, attribute, value)

  return attributes
