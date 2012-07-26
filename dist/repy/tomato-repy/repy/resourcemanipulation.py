"""
   Author: Justin Cappos

   Start Date: 7 Dec 2010   (Derived from restrictions.py and nmresourcemath.py)

   Description:

   This class handles resource specifications.   It used to handle 
   restricting access to functions, but that has been removed in favor of
   security layers.
   This module is supposed to be readable and obviously correct.  

   This is only supposed to specify what resources are assigned to a vessel.
   It does not cover tracking resource use over time, etc. 
"""


# this provides information about the valid resource names, required 
# resources, etc.
import resource_constants


class ResourceParseError(Exception):
  """This exception is thrown if the resource file is invalid"""

class ResourceMathError(Exception):
  """A resource dictionary is missing elements or negative"""



# be sure no resources are negative...
def _assert_resourcedict_doesnt_have_negative_resources(newdict):
  for resource in newdict:
    if type(newdict[resource]) != set and newdict[resource] < 0.0:
      raise ResourceMathError("Insufficient quantity: Resource '"+resource+"' has a negative quantity")



# Helper method to ensure that the given resource dict has all of the resources
# listed as required in nanny.py. -Brent
def _assert_resourcedict_has_required_resources(newdict):
  for resource in resource_constants.must_assign_resources:
    if resource not in newdict:
      raise ResourceMathError("Missing required resource: '"+resource+"'")







############################ Parsing and I/O #############################

""" 
The resource file format consists of lines that look like this:
 
Comment Lines: 
# This is a comment


Resource quantities: what the program is allowed to utilize
Usage: resource resourcename limit
Example:
resource CPU 0.1			# Can have %10 CPU utilization
resource memory 33554432		# Can have 32 MB of memory
resource outsockets 1			# Can initiate one outgoing comm
resource insocket 2			# Can listen for 2 incoming comms
resource messport 2023 			# Can use messageport 2023 
resource messport 2043 			# Can use messageport 2043 

"""



def read_resourcedict_from_file(filename):
  """
    <Purpose>
        Reads resource information from a file, returning a dict

    <Arguments>
        filename: the name of the file to read resource information from.

    <Exceptions>
        ResourceParseError: if the file does not have the correct format

        IOError: if the file cannot be opened.
   
    <Side Effects>
        None

    <Returns>
        A dictionary with the resource information.   Resources that are
        not specified, but are required will be set to 0.0
  """

  filedata = open(filename).read()

  return parse_resourcedict_from_string(filedata)




# This is a braindead parser.   It's supposed to be readable and obviously 
# correct, not "clever"
def parse_resourcedict_from_string(resourcestring):
  """
    <Purpose>
        Reads resource information from a file, returning a dict

    <Arguments>
        resourcestring: the string of data to parse

    <Exceptions>
        ResourceParseError: if the file does not have the correct format

        IOError: if the file cannot be opened.
   
    <Side Effects>
        None

    <Returns>
        A dictionary with the resource information.   Resources that are
        not specified, but are required will be set to 0.0
  """


  returned_resource_dict = {}

  # I must create an empty set for any resource types that are sets.
  # (these are things like messports, etc.)
  for resourcename in resource_constants.individual_item_resources:
    returned_resource_dict[resourcename] = set()


  # ensure we don't have problems with windows style newlines... (only LF)
  lfresourcestring = resourcestring.replace('\r\n','\n')

  for line in lfresourcestring.split('\n'):

    # let's get rid of whitespace...
    cleanline = line.strip()

    # remove any comments
    noncommentline = cleanline.split('#')[0]

    # the items are all separated by spaces
    tokenlist = noncommentline.split()

    if len(tokenlist) == 0:
      # This was a blank or comment line
      continue
    
    linetypestring = tokenlist[0]
 
    # should be either a resource or a call line
    if linetypestring != 'resource' and linetypestring != 'call':
      raise ResourceParseError("Line '"+line+"' not understood.")
    


    if linetypestring == 'resource':

      ####### Okay, it's a resource.  It must have two other tokens!
      if len(tokenlist) != 3:
        raise ResourceParseError("Line '"+line+"' has wrong number of items")

      # the other tokens are the resource and the resource value
      knownresourcename = tokenlist[1]
      resourcevaluestring = tokenlist[2]

      # and the second token must be a known resource
      if knownresourcename not in resource_constants.known_resources:
        raise ResourceParseError("Line '"+line+"' has an unknown resource '"+knownresourcename+"'")

      # and the last item should be a valid float
      try:
        resourcevalue = float(resourcevaluestring)
      except ValueError:
        raise ResourceParseError("Line '"+line+"' has an invalid resource value '"+resourcevaluestring+"'")

      # if it's an individual_item_resource, then there can be a list of 
      # different values for the resource (like ports)
      if knownresourcename in resource_constants.individual_item_resources:

        # I'm implicitly ignoring duplicates in the file.   Is that wise?
        returned_resource_dict[knownresourcename].add(resourcevalue)
        continue

      # other resources should not have been previously assigned
      if knownresourcename in returned_resource_dict:
        raise ResourceParseError("Line '"+line+"' has a duplicate resource rule for '"+knownresourcename+"'")

        
      # Finally, we assign it to the table
      returned_resource_dict[knownresourcename] = resourcevalue
      
      # Let's do the next line!
      continue




    elif linetypestring == 'call':

      # it was a call...   I'm going to ignore these because these are obsolete
      # This may be an error later
      continue

    else:
      raise ResourceParseError("Internal error for '"+line+"'")


  # make sure that if there are required resources, they are defined
  _assert_resourcedict_has_required_resources(returned_resource_dict)

  # give any remaining resources an entry with 0.0 as the value.   This fills
  # out the table (preventing key errors later).   It won't prevent divide by
  # zero for rate based resources though.

  for resource in resource_constants.known_resources:
    if resource not in returned_resource_dict:
      returned_resource_dict[resource] = 0.0


  return returned_resource_dict











def write_resourcedict_to_file(resourcedict, filename):
  """
    <Purpose>
        Writes out a resource dictionary to disk...

    <Arguments>
        resourcedict: the dictionary to write out
        filename: the file to write it to

    <Exceptions>
        IOError: if the filename cannot be opened or is invalid.
   
    <Side Effects>
        Creates a file

    <Returns>
        None
  """

  outfo = open(filename,"w")
  for resource in resourcedict:
    if type(resourcedict[resource]) == set:
      for item in resourcedict[resource]:
        print >> outfo, "resource "+resource+" "+str(item)
    else:
      print >> outfo, "resource "+resource+" "+str(resourcedict[resource])

  outfo.close()





############################ Math #############################


  

# Take two sets of resources and add them...
def add_resourcedicts(dict1, dict2):
  """
    <Purpose>
        Takes two resource dicts and returns the sum

    <Arguments>
        dict1,dict2: the resource dictionaries

    <Exceptions>
        ResourceMathError: if a resource dict is invalid
   
    <Side Effects>
        None

    <Returns>
        The new resource dictionary
  """

  # check arguments
  _assert_resourcedict_doesnt_have_negative_resources(dict1)
  _assert_resourcedict_doesnt_have_negative_resources(dict2)
  _assert_resourcedict_has_required_resources(dict1)
  _assert_resourcedict_has_required_resources(dict2)


  retdict = dict1.copy()

  # let's iterate through the second dictionary and add if appropriate.   If
  # dict2 doesn't have the key, it doesn't matter.
  for resource in dict2:

    # if this is a set, then get the union
    if type(retdict[resource]) == set:
      retdict[resource] = retdict[resource].union(dict2[resource])
      continue

    # empty if not preexisting
    if resource not in retdict:
      retdict[resource] = 0.0

    if type(retdict[resource]) != float:
      raise ResourceMathError("Resource dictionary contain an element of unknown type '"+str(type(retdict[resource]))+"'")

    # ... and add this item to what we have.   This is okay for sets or floats
    retdict[resource] = retdict[resource] + dict2[resource]

  
  # these should be impossible to trigger
  _assert_resourcedict_has_required_resources(retdict)
  _assert_resourcedict_doesnt_have_negative_resources(retdict)
  return retdict



# remove one quantity of resources from the other. (be sure to check if the
# resulting resources are negative if appropriate)
def subtract_resourcedicts(dict1, dict2):
  """
    <Purpose>
        Takes resource dict1 and subtracts resource dict2 from it.   An 
        exception is raised if the resulting resource dict is not positive.

    <Arguments>
        dict1: a resource dict
        dict2: a resource dict to remove from dict1

    <Exceptions>
        ResourceMathError: if the result would be negative or a resource dict
        is malformed
   
    <Side Effects>
        None

    <Returns>
        The new resource dictionary
  """
  # check arguments
  _assert_resourcedict_doesnt_have_negative_resources(dict1)
  _assert_resourcedict_doesnt_have_negative_resources(dict2)
  _assert_resourcedict_has_required_resources(dict1)
  _assert_resourcedict_has_required_resources(dict2)


  retdict = dict1.copy()

  # then look at resourcefile1
  for resource in dict2:

    # empty if not preexisting
    if resource not in retdict:
      retdict[resource] = 0.0

    # ... if it's a float, we can just subtract...
    if type(retdict[resource]) == float:
      retdict[resource] = retdict[resource] - dict2[resource]

    # otherwise we need to be sure we're only subtracting items that exist
    elif type(retdict[resource]) == set:
      if not retdict[resource].issuperset(dict2[resource]):
        raise ResourceMathError('Subtracted resource dictionary does not contain all elements')

      # use the set subtraction
      retdict[resource] = retdict[resource] - dict2[resource]

    # otherwise, WTF is this?
    else:
      raise ResourceMathError("Resource dictionary contain an element of unknown type '"+str(type(retdict[resource]))+"'")
       

  # this may be negative, but should have all of the required resources
  _assert_resourcedict_doesnt_have_negative_resources(retdict)
  _assert_resourcedict_has_required_resources(retdict)
  return retdict




