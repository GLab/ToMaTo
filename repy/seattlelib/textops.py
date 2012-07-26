"""
<Program Name>
  textops.py

<Started>
  July 24, 2009

<Author>
  Conrad Meyer <cemeyer@u.washington.edu>

<Purpose>
  Provides text-processing utility functions loosely modelled after GNU
  coreutils.

  Currently supports a subset of the functionality of grep and wc.
"""




def textops_rawtexttolines(text, linedelimiter="\n"):
  """
  <Purpose>
    Converts raw text (a string) into lines that can be processed by the
    functions in this module.

  <Arguments>
    text:
            The text to convert into lines (basically, a sequence of strings).

    linedelimiter (optional, defaults to "\n"):
            The string denoting an EOL ("\n" on Unix, "\r\n" on Windows).

  <Exceptions>
    TypeError on bad parameters.

  <Side Effects>
    None.

  <Returns>
    A sequence of strings; each element is a line, with newlines removed.

  """

  lines = text.split(linedelimiter)
  if lines[len(lines)-1] == '':
    lines = lines[:-1]

  return lines




def textops_grep(match, lines, exclude=False, case_sensitive=True):
  """
  <Purpose>
    Return a subset of lines matching (or not matching) a given string.

  <Arguments>
    match:
            The string to match.
    
    lines:
            The lines to filter.

    exclude (optional, defaults to false):
            If false, include lines matching 'match'. If true, include lines
            not matching 'match'.

    case_sensitive (optional, defaults to true):
            If false, ignore case when comparing 'match' to the lines.

  <Exceptions>
    TypeError on bad parameters.

  <Side Effects>
    None.

  <Returns>
    A subset of the original lines.

  """
  
  if not case_sensitive:
    match = match.lower()

  result = []
  for line in lines:
    if not case_sensitive:
      mline = line.lower()
    else:
      mline = line

    if not exclude and mline.find(match) >= 0:
      result.append(line)
    elif exclude and mline.find(match) < 0:
      result.append(line)

  return result




def textops_cut(lines, delimiter="\t", characters=None, fields=None,
    complement=False, only_delimited=False, output_delimiter=None):
  """
  <Purpose>
    Perform the same operations as GNU coreutils' cut.

  <Arguments>
    lines:
            The lines to perform a cut on.

    delimiter (optional):
            Field delimiter. Defaults to "\t" (tab).

    characters (optional):
            Characters selector. Used to select some subset of characters
            in the lines. Should be a sequence argument. Caller must use one
            of characters or fields; not both.

            Note: unlike cut(1), we use zero-based indices.

    fields (optional):
            Fields selector. Used to select some subset of fields in the
            lines. Should be a sequence argument. Caller must use one
            of characters or fields; not both.

            Note: unlike cut(1), we use zero-based indices.

    complement (optional):
            Invert which characters or fields get selected. Defaults to False.

    only_delimited (optional):
            When selecting fields, only include lines containing the field
            delimiter.

    output_delimiter (optional):
            When selecting fields, join fields with this (defaults to the
            input delimiter).

  <Exceptions>
    TypeError on bad parameters.

  <Side Effects>
    None.

  <Returns>
    The filtered lines.

  """

  if (characters is None and fields is None) or \
      (characters is not None and fields is not None):
    raise TypeError("Exactly one of fields or characters must be specified.")

  if output_delimiter is None:
    output_delimiter = delimiter

  if characters is None:
    matched_fields = list(fields)
  else:
    matched_fields = list(characters)

  res_list = []
  for line in lines:
    if characters is not None:
      if complement:
        select_characters = list(range(0, len(line)))
        for character in matched_fields:
          select_characters = select_characters.remove(character)
      else:
        select_characters = matched_fields

      res_line = ""
      for character in select_characters:
        try:
          res_line += line[character]
        except IndexError:
          break

      res_list.append(res_line)

    else:
      split_line = line.split(delimiter)
      if len(split_line) == 1:
        if not only_delimited:
          res_list.append(line)
        continue

      if complement:
        select_fields = list(range(0, len(split_line)))
        for field in matched_fields:
          select_fields = select_fields.remove(field)
      else:
        select_fields = matched_fields

      split_res_line = []
      for field in select_fields:
        try:
          split_res_line.append(split_line[field])
        except IndexError:
          break

      res_list.append(output_delimiter.join(split_res_line))

  return res_list
