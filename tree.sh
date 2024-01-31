#!/bin/bash

# Check if a directory is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <directory>"
    exit 1
fi

DIRECTORY=$1

# Check if the provided directory exists
if [ ! -d "$DIRECTORY" ]; then
    echo "Error: Directory '$DIRECTORY' does not exist."
    exit 1
fi

# Function to display files and subdirectories in a tree view
display_tree() {
    find "$1" -print | awk -F/ '
    {
        for(i=1; i<NF; i++) {
            printf("|   ");
        }
        print "-- "$NF
    }' | sed 's/-- $//'
}

# Call the function with the provided directory
display_tree "$DIRECTORY"
