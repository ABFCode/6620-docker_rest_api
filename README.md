## Prerequisites

- [Docker Desktop Official Website](https://www.docker.com/products/docker-desktop)

---

## How to Run

To build the Docker image and run the API server, follow these steps:

1.  **Clone the repository:**

    ```sh
    git clone https://github.com/ABFCode/6620-docker_rest_api
    cd 6620-docker_rest_api
    ```

2.  **Make the script executable**

    ```sh
    chmod +x run_app.sh
    ```

3.  **Run the script:**
    ```sh
    ./run_app.sh
    ```

The API will now be running at `http://localhost:5000`.

---

## Run the Tests

1.  **Make the test script executable**

    ```sh
    chmod +x run_tests.sh
    ```

2.  **Run the script:**
    ```sh
    ./run_tests.sh
    ```

---

https://stackoverflow.com/questions/40336918/how-to-write-a-file-or-data-to-an-s3-object-using-boto3

https://dev.to/aws-builders/how-to-list-contents-of-s3-bucket-using-boto3-python-47mm

https://stackoverflow.com/questions/40995251/reading-a-json-file-from-s3-using-python-boto3

https://github.com/localstack-samples/localstack-terraform-samples

AI/LLM USAGE:
CLAUDE/CHATGPT 

Prompts - Starting Prompts: 
1. What is wrong with my current use of these two classes (run_tests.sh)/(docker-compose.test.yml) Having issues with credentials and exiting early

2. I think trying to run terraform in side our dockercomposetest is difficulk we should move into a more run_tests.sh focused method where we : Start LocalStack - This provides a local AWS environment that mimics S3
Wait for LocalStack to be ready - It takes time to boot up
Run Terraform - This creates the S3 bucket in LocalStack
Run the tests - pytest runs against the Flask app, which connects to LocalStack's S3. Is that better/possible?

3. Issue with workflows (main.yaml) 
./run_tests.sh: line 9: docker-compose: command not found