#!/bin/bash
set -e

echo "Installing Git LFS..."
apt-get update && apt-get install -y git-lfs
git lfs install
git lfs pull

echo "Installing Python dependencies..."
pip install -r requirements.txt
