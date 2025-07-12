#!/bin/bash
echo "Building the test Docker image"
docker build -t my-book-api-test -f Dockerfile.test .

echo "Running tests in the container"
docker run --rm my-book-api-test
