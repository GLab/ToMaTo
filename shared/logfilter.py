import json, sys, re

def buildFilterEq(key, value):
  return lambda d: key in d and str(d[key]) == value

def buildFilterGt(key, value):
  return lambda d: key in d and str(d[key]) > value

def buildFilterLt(key, value):
  return lambda d: key in d and str(d[key]) < value

def buildFilterRe(key, value):
  return lambda d: key in d and re.match(value, str(d[key]))

def buildFilters(args):
  filters = []
  for arg in args:
    if "=" in arg:
      key, value = arg.split("=", 1)
      filters.append(buildFilterEq(key, value))
    elif ">" in arg:
      key, value = arg.split(">", 1)
      filters.append(buildFilterGt(key, value))
    elif "<" in arg:
      key, value = arg.split("<", 1)
      filters.append(buildFilterLt(key, value))
    elif "~" in arg:
      key, value = arg.split("~", 1)
      filters.append(buildFilterRe(key, value))
  return filters
      

def filterLogs(logs, filters):
  for line in logs:
    data = json.loads(line)
    match = True
    for f in filters:
      if not f(data):
        match = False
        break
    if match:
      print line.strip()

if __name__ == "__main__":
  filters = buildFilters(sys.argv[1:])
  filterLogs(sys.stdin, filters)