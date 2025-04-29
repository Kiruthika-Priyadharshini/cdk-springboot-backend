# Welcome to your CDK Python project!

This is a blank project for CDK development with Python.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project. The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory. To create the virtualenv, it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on macOS and Linux:

```
$ python -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example, other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Steps to Push ECR Images to AWS

Follow these steps to push the Docker images for `user-service` and `order-service` to AWS Elastic Container Registry (ECR):

1. **Authenticate Docker with ECR**:
   ```
   aws ecr get-login-password --region <REGION> | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com
   ```
   Replace `<ACCOUNT_ID>` with your AWS account ID and `<REGION>` with your desired AWS region.

2. **Create ECR Repositories** (if not already created):
   ```
   aws ecr create-repository --repository-name user-service
   aws ecr create-repository --repository-name order-service
   ```

3. **Build the Docker Images**:
   ```
   docker build -t user-service ./path/to/user-service
   docker build -t order-service ./path/to/order-service
   ```

4. **Tag the Docker Images**:
   ```
   docker tag user-service:latest <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/user-service:latest
   docker tag order-service:latest <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/order-service:latest
   ```

5. **Push the Docker Images to ECR**:
   ```
   docker push <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/user-service:latest
   docker push <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/order-service:latest
   ```

6. **Verify the Images in ECR**:
   ```
   aws ecr describe-images --repository-name user-service
   aws ecr describe-images --repository-name order-service
   ```

Once the images are pushed, the ECS services in your CDK stack will automatically pull the images from ECR during deployment.

## Steps to Deploy the CDK Stack to AWS ECS

1. **Bootstrap the CDK Environment** (if not already done):
   ```
   cdk bootstrap aws://<ACCOUNT_ID>/<REGION>
   ```
   Replace `<ACCOUNT_ID>` with your AWS account ID and `<REGION>` with your desired AWS region (e.g., `us-east-1`).

2. **Synthesize the CloudFormation Template**:
   ```
   cdk synth
   ```

3. **Deploy the CDK Stack**:
   ```
   cdk deploy
   ```

   This will deploy the ECS cluster, services, and other resources defined in your CDK stack.

4. **Destroy the CDK Stack**:
   ```
   cdk destroy
   ```

   This will remove all resources defined in your stack from your AWS account. Ensure you no longer need the resources before running this command, as it will delete them permanently.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation
 * `cdk destroy`     destroy all resources created by the stack

Enjoy!
