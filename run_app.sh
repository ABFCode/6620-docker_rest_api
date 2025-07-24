#!/bin/bash
set -e

COMPOSE_FILE="docker-compose.yml"

cleanup() {
    echo "--- Tearing down environment ---"
    docker compose -f $COMPOSE_FILE down --remove-orphans --volumes
}
trap cleanup EXIT

echo "--- Starting LocalStack in the background ---"
docker compose -f $COMPOSE_FILE up -d --build localstack

echo "--- Waiting for LocalStack services to be ready ---"
S3_READY=false
DYNAMO_READY=false
for i in {1..24}; do
    HEALTH=$(curl -s --fail http://localhost:4566/_localstack/health || echo "")
    if echo "$HEALTH" | grep -q '"s3": "available"'; then
        S3_READY=true
    fi
    if echo "$HEALTH" | grep -q '"dynamodb": "available"'; then
        DYNAMO_READY=true
    fi

    if [ "$S3_READY" = true ] && [ "$DYNAMO_READY" = true ]; then
        break
    fi
    echo "Waiting... S3 ready: $S3_READY, DynamoDB ready: $DYNAMO_READY"
    sleep 5
done

if [ "$S3_READY" = false ] || [ "$DYNAMO_READY" = false ]; then
    echo "FATAL: A LocalStack service did not become healthy." >&2
    exit 1
fi
echo "--- All services are ready ---"

echo "--- Applying Terraform to create resources ---"
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
terraform init -input=false
terraform apply -auto-approve -input=false -no-color

echo ""
echo "--- Starting the application ---"
echo "Application is running"
echo "API is available at http://localhost:5000"
echo "Press Ctrl+C to stop"

docker compose -f $COMPOSE_FILE up --build app