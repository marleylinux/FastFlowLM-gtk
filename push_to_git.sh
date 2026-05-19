#!/bin/bash

# FastFlowLM-gtk Git Push Script

cd /home/marley/FastFlowLM-gtk || exit

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    git remote add origin https://github.com/marleylinux/FastFlowLM-gtk
fi

# Add all files
git add .

# Commit changes
# Using a generic message or timestamp if no message is provided
git commit -m "Update: $(date)"

# Push to main
git push -u origin main
