"""

Author: Armon Dadgar

Start Date: February 16th, 2009

Description:
Functions to reconstruct objects from their string representation.

"""
# Constants for the types, these are the supported object types
DERSERIALIZE_DICT = 1
DERSERIALIZE_LIST = 2
DERSERIALIZE_TUPLE = 3

# Convert a string, which either a boolean, None, floating point number,
# long, or int to a primitive, not string type
def deserialize_stringToPrimitive(inStr):
  try:
    # Check if it is None
    if inStr == "None":
      return None
      
    # Check if it is boolean
    if inStr == "True":
      return True
    elif inStr == "False":
      return False
    
    # Check if it is floating point
    if inStr.find(".") != -1:
      val = float(inStr)
  
    # It must be a long/int
    else:
      # It is a long if it has an L suffix
      if inStr[-1] == 'L':
        val = long(inStr)
      else:
        val = int(inStr)
  except:
    return inStr
  
  return val

# Returns an array with the index of the search char
def deserialize_findChar(char, str):
  indexes = []
  
  # Look for all starting braces
  location = 0
  first = True
  while first or index != -1:
    # Turn first off
    if first:
      first = False

    # Search for sub dictionaries
    index = str.find(char,location)

    # Add the index, update location
    if index != -1:
      indexes.append(index)
      location = index+1   
  
  return indexes
      
# Find sub-objects
def deserialize_findSubObjs(str):
  # Object types
  objectStarts = {"{":DERSERIALIZE_DICT,"[":DERSERIALIZE_LIST,"(":DERSERIALIZE_TUPLE}
  objectEnds = {"}":DERSERIALIZE_DICT,"]":DERSERIALIZE_LIST,")":DERSERIALIZE_TUPLE}
  
  # Location of the start and end braces
  startIndexes = []
  for (start, type) in objectStarts.items():
    startIndexes += deserialize_findChar(start, str)
  startIndexes.sort()
  
  # Check if any sub-dicts exist    
  if len(startIndexes) == 0:
    return []
  
  endIndexes = []
  for (end, type) in objectEnds.items():
    endIndexes += deserialize_findChar(end, str)          
  endIndexes.sort()
  
  # Partitions of the string
  partitions = []
  
  startindex = 0
  endindex = 0
  
  while True:    
    maxStartIndex = len(startIndexes) - 1
    
    if maxStartIndex == -1:
      break
      
    if maxStartIndex == startindex or endIndexes[endindex] < startIndexes[startindex+1]:
      partitions.append([startIndexes[startindex],endIndexes[endindex],startindex,objectStarts[str[startIndexes[startindex]]]])
      del startIndexes[startindex]
      del endIndexes[endindex]
      startindex = 0
      endindex = 0
    else:
      startindex += 1
  
  return partitions
  
# Returns an object from the string filler
def deserialize_partitionedObj(value, partitions):
  index = int(value.lstrip("#"))
  return partitions[index]

# Modifies the start and end indexes of all elements in the array
# by indexOffset if they are greater than the start index
def deserialize_indexOffsetAdjustment(array, start, indexOffset):
  index = 0
  
  while index < len(array):
    if array[index][0] > start:
      array[index][0] -= indexOffset
    if array[index][1] > start:
      array[index][1] -= indexOffset
    index += 1
    
# Removes all string objects from a larger string
def deserialize_removeStringObjects(strIn, partitions):
  # Get strings starting with a single quote
  substrings1 = deserialize_findChar("'",strIn)
  
  # Get strings starting with a double quote
  substrings2 = deserialize_findChar("\"",strIn)
  
  # Calculate the lengths
  num1 = len(substrings1)
  num2 = len(substrings2)    
  partitionIndex = len(partitions)
  
  # Actual top level strings
  substrings = []
  
  # Filter out strings inside other strings
  subIndex1 = 0
  subIndex2 = 0
  if num1 != 0 and num2 != 0:
    while True:
      # Get the indexes of both lists
      start1 = substrings1[subIndex1]
      start2 = substrings2[subIndex2]
    
      # If the start index of one is lower than the other, then 
      # remove all members until we reach the closing quote
      if start1<start2:
        # Get the index value of the closing quote
        endIncrement = substrings1[subIndex1+1]
      
        # While there are strings between the starting and closing quote, remove them
        while num2 != 0 and endIncrement > start2:
          del substrings2[subIndex2]
          num2 -= 1
          if num2 == subIndex2:
            break
          start2 = substrings2[subIndex2]
      
        # Add the current start and end to the list of substrings
        substrings.append([start1,endIncrement])
        subIndex1 += 2
        
      elif start2<start1:
        # Get the index value of the closing quote
        endIncrement = substrings2[subIndex2+1]
      
        # While there are strings between the starting and closing quote, remove them
        while num1 != 0 and endIncrement > start1:
          del substrings1[subIndex1]
          num1 -= 1
          if num1 == subIndex1:
            break
          start1 = substrings1[subIndex1]
      
        # Add the current start and end to the list of substrings
        substrings.append([start2,endIncrement])
        subIndex2 += 2
    
      # Break if we've hit the end of either list
      if subIndex1 >= num1 or subIndex2 >= num2:
        break
  
  # Add any remaining substrings, that were not nested
  while subIndex1+1 < num1:
    substrings.append([substrings1[subIndex1],substrings1[subIndex1+1]])
    subIndex1 += 2
  while subIndex2+1 < num2:
    substrings.append([subIndex2[subIndex2],subIndex2[subIndex2+1]])
    subIndex2 += 2
  
  # Cleanup
  substrings1 = None
  substrings2 = None
    
  # Remove every substring and store as an object
  for sub in substrings:
    # Get the info for the string
    (start,end) = sub
    
    # Extract the real string, store it
    actualstr = strIn[start+1:end] # Add one to the start to avoid including the single quotes
    partitions.append(actualstr)
    
    # Replace the string in the larger string with a filler
    addIn = "#"+str(partitionIndex)
    partitionIndex += 1
    strIn = strIn[0:start]+addIn+strIn[end+1:]
    
    # Modify the indexes of the existing strings
    indexOffset = 1+end-start
    indexOffset -= len(addIn)
    deserialize_indexOffsetAdjustment(substrings, start, indexOffset)
    
  return strIn  

# Removes all lists and dictionary objects from the string, begins deserializing
# objects from the innermost depth upward
def deserialize_removeObjects(strIn, partitions=[]):  
  # Find all the sub objects
  subObjs = deserialize_findSubObjs(strIn)
  
  # Get the current length of the partitions
  partitionIndex = len(partitions)
    
  # Determine maximum depth
  maxDepth = 0
  for obj in subObjs:
    maxDepth = max(maxDepth, obj[2])
  
  # Start at the lowest depth and work upward
  while maxDepth >= 0:
    for obj in subObjs:
      (start,end,depth,type) = obj
      if depth == maxDepth:
        # Switch deserialization method on type
        if type == DERSERIALIZE_DICT:
          realObj = deserialize_dictObj(strIn[start:end+1],partitions)
        elif type == DERSERIALIZE_LIST:
          realObj = deserialize_listObj(strIn[start:end+1],partitions)
        elif type == DERSERIALIZE_TUPLE:
          realObj = deserialize_tupleObj(strIn[start:end+1],partitions)
        
        # Store the real object
        partitions.append(realObj)
        
        # Replace the string representation of the object with a filler
        addIn = "#"+str(partitionIndex)
        partitionIndex += 1
        strIn = strIn[0:start]+addIn+strIn[end+1:]
        
        # Modify the indexes now that the string length has changed
        indexOffset = 1+end-start
        indexOffset -= len(addIn)
        deserialize_indexOffsetAdjustment(subObjs, start, indexOffset)
    
    # Go up to a higher depth        
    maxDepth -= 1
  
  return strIn
          
# Convert a string representation of a Dictionary back into a dictionary
def deserialize_dictObj(strDict, partitions):
  # Remove dict brackets
  strDict = strDict[1:len(strDict)-1]
    
  # Get key/value pairs by exploding on commas
  keyVals = strDict.split(", ")

  # Create new dictionary
  newDict = {}

  # Process each key/Value pair
  for pair in keyVals:
    (key, value) = pair.split(": ",1)
    
    # Convert key to primitive
    if (key[0] == "#"):
      key = deserialize_partitionedObj(key,partitions)
    else:
      key = deserialize_stringToPrimitive(key)
    
    # Convert value to primitive
    if (value[0] == "#"):
      value = deserialize_partitionedObj(value,partitions)
    else:
      value = deserialize_stringToPrimitive(value)
  
    # Add key/value pair
    newDict[key] = value

  return newDict

# Convert a string representation of a list back into a list
def deserialize_listObj(strList, partitions):
  # Remove list brackets
  strList = strList[1:len(strList)-1]

  # Get values by exploding on commas
  values = strList.split(", ")

  # Create new list
  newList = []

  # Process each value
  for value in values:
    # Check for a sub-object filler
    if (value[0] == "#"):
      value = deserialize_partitionedObj(value,partitions)

    # Else this is a primitive type
    else:
      value = deserialize_stringToPrimitive(value)

    # Store the element
    newList.append(value)

  return newList
      
# Convert a string representation of a tuple back into a tuple
def deserialize_tupleObj(strList, partitions):
  # Remove tuple brackets
  strList = strList[1:len(strList)-1]

  # Get values by exploding on commas
  values = strList.split(", ")

  # Create new tuple
  newTuple = ()

  # Process each value
  for value in values:
    # Check for a sub-object filler
    if (value[0] == "#"):
      value = deserialize_partitionedObj(value,partitions)
    
    # Else this is a primitive type
    else:
      value = deserialize_stringToPrimitive(value)
      
    # Store the element
    newTuple += (value,)

  return newTuple  

# Converts a string representation of a list or dictionary 
# back into the real object. This works with sub-lists, sub-dictionaries,
# as well as strings, longs, ints, floats, and bools
def deserialize(string):
  # Array of partitions
  partitions = []
  
  # If there is an error, try to give specific feedback
  # Remove the sub-strings
  try:
    string = deserialize_removeStringObjects(string, partitions)
  except:
    raise ValueError, "Complicated sub-strings failed to parse!"
  
  # Remove the sub-objects
  try:
    string = deserialize_removeObjects(string, partitions)
  except:
    raise ValueError, "Complicated sub-objects failed to parse!"
    
  # Retrieve the top level object
  try:
    root = deserialize_partitionedObj(string, partitions)
  except:
    raise ValueError, "Failed to retrieve top-level object!"
  
  return root
  
