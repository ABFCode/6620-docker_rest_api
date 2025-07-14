#!/bin/bash
set -e

COMPOSE_FILE="docker-compose.test.yml"

cleanup() {
    echo "--- Tearing down test environment ---"
    exit_code=$?
    docker-compose -f $COMPOSE_FILE down --remove-orphans
    exit $exit_code
}
trap cleanup EXIT

docker compose -f $COMPOSE_FILE up -d localstack

S3_READY=false
for i in {1..24}; do
    if curl -s http://localhost:4566/_localstack/health | grep -q '"s3": "available"'; then
        S3_READY=true
        break
    fi
    sleep 5
done

if [ "$S3_READY" = false ]; then
    echo "FATAL: LocalStack S3 service did not become healthy." >&2
    exit 1
fi

export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
terraform init -input=false
terraform apply -auto-approve -input=false -no-color

if ! docker-compose -f $COMPOSE_FILE exec localstack awslocal s3 ls | grep -q "my-books"; then
    echo "FATAL: Terraform did not create the 'my-books' bucket." >&2
    exit 1
fi

docker-compose -f $COMPOSE_FILE up --build --exit-code-from tests tests