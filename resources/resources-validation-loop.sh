#!/bin/bash

# Define the path to the 'resources' folder
resources_folder="."

# Check if the 'resources' folder exists
if [ ! -d "$resources_folder" ]; then
    echo "The 'resources' folder does not exist at the specified path: $resources_folder"
    exit 1
fi

# Navigate to the 'resources' folder
cd "$resources_folder"

# Find all PNG files and run pngcrush on each
find . -type f -name '*.png' -exec pngcrush -n -q {} \;

echo "pngcrush has been executed on all PNG files in the 'resources' folder."