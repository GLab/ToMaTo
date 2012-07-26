#!/bin/bash
# Author: Armon Dadgar
# Convert's print statements using sed
# This will not work properly for instances using
# print redirection
#

if [ $# -eq 0 ]
then
    echo "Must provide a single argument to glob the files!"
    exit
fi

# These are the files to fix, passed to ls
FILE_GLOB=$1

# This is the sed command
SED_CMD="sed -e"

# This argument handles the trailing , to avoid a new-line
SED_ARG_NO_NEWL="s|print \(.*[^,]\),$|log(\1)|"

# This argument handles the normal print with a newline
SED_ARG_NEWL="s|print \(.*\)$|log(\1,'\\\n')|"

# This argument handles a print to just add a newline
SED_ARG_NOARG="s|print[ \t]*$|log('\\\n')|"

# This is the temporary suffix used while fixing
TMP_SUFFIX="tmp"

# This is the suffix used to backup the modified file
BACKUP_SUFFIX="bak"

# Get the files
FILES=`ls $FILE_GLOB`

# Handle each file
for FILE in $FILES
do
    echo "Fixing: $FILE"
    cat $FILE | $SED_CMD "${SED_ARG_NO_NEWL}" | $SED_CMD "${SED_ARG_NEWL}" | $SED_CMD "${SED_ARG_NOARG}" > "$FILE.$TMP_SUFFIX"
    mv $FILE "$FILE.$BACKUP_SUFFIX"
    mv "$FILE.$TMP_SUFFIX" $FILE
done

