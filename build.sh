set -e

echo "Installing Git LFS..."
apt-get update && apt-get install -y git-lfs
git lfs install

echo "Fetching LFS files..."
git lfs fetch --all
git lfs checkout

echo "Checking ONNX model files sizes and head of one model:"
ls -lh "AI Models/models/buffalo_l/"
head -n 10 "AI Models/models/buffalo_l/1k3d68.onnx" || echo "File not found!"

echo "Installing Python dependencies..."
pip install -r requirements.txt
