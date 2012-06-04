#!/bin/bash

# rawdel.sh, a photo workflow script to delete raw files when the jpg has been removed
# By Alex Forbes
#
# I frequently shoot in RAW+JPG mode and when downloading from the camera I like to separate 
# the raw and jpg files into separate directories. I then go through the jpg directory and 
# delete the rejects. It is a pain to have to manually delete the corresponding raw files as 
# well, so I wrote a script to do it for me.
#
# It simply removes RAW files from a directory when the corresponding JPG file has been removed.

# Set these
rawextn="CR2"	# raw file extension (Canon is CR2)
rawdir="./RAW"	# directory where raw files reside
jpgdir="./JPG"	# directory where jpg files reside
				# rawdir and jpgdir can be the same

rawdir="."
jpgdir="."

# Working variables, leave as-is
list=""			# list of files that have been deleted
rawlist=""		# the list of raw files that we will delete
filecount=""	# number of files we will delete

# Operate on each raw file
for f in $(ls -1 $rawdir/*.$rawextn); do 
	# Corresponding JPG file is:
	jpgfile=$(basename $f | sed "s/\.$rawextn$/.JPG/")

	# If this JPG file doesn't exist
	if [ ! -f $jpgdir/$jpgfile ]; then
		# Add to our list of files that have been deleted
		list=$(echo -e "${jpgfile} ${list}")
	fi
done

# Convert jpg filenames back to corresponding raw filenames
rawlist=$(echo ${list} | sed 's/\.JPG$/.CR2/g')
filecount=$(echo -e ${rawlist}| awk 'END{print NF}')

if [ $filecount == 0 ]; then
	echo "No files to delete"
	exit 0
fi

echo -e "About to remove $filecount files:\n${rawlist}"
read -p "Continue? [Y/N] " prompt
 
if [[ $prompt = "Y" || $prompt = "y" ]]; then
	# Delete all files in the list
	for f in ${rawlist}; do
		rm -v $rawdir/$f
	done
	exit 0
else
	echo -e "\nAborted."
	exit 1
fi

 