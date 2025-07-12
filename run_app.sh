#!/bin/bash
echo "Building the API Docker image"
docker build -t my-book-app -f Dockerfile.app .

echo "Running the API container"
docker run -p 5000:5000 --rm my-book-app