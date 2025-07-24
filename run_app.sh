#!/bin/bash
set -e

COMPOSE_FILE="docker-compose.yml"

cleanup() {
    echo "--- Tearing down environment ---"
    docker compose -f $COMPOSE_FILE down --remove-orphans --volumes
}
trap cleanup SIGINT 

docker compose -f $COMPOSE_FILE up -d --build localstack

S3_READY=false
for i in {1..24}; do
    if curl -s --fail http://localhost:4566/_localstack/health | grep -q '"s3": "available"'; then
        S3_READY=true
        echo "--- S3 is ready ---"
        break
    fi
    echo "Waiting for S3... (attempt $i of 24)"
    sleep 5
done

if [ "$S3_READY" = false ]; then
    echo "FATAL: LocalStack S3 service did not become healthy." >&2
    exit 1
fi

echo "--- S3 is ready. Applying Terraform to create the bucket. ---"
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
terraform init -input=false
terraform apply -auto-approve -input=false -no-color

echo ""
echo "Application is running"
echo "API is available at http://localhost:5000"
echo "Press Ctrl+C to stop"

docker compose -f $COMPOSE_FILE up --build app