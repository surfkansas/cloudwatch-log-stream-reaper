# CloudWatch Log Stream Reaper

This Lambda function solves a problem with CloudWatch log retention. When setting log retention, the individual log messages are deleted. However, the log *streams* are not deleted when they are empty. This isn't an issue for log streams that re-use a stream. However, for services that create new log streams per container instance (such as Lambda or Fargate), you can run into issues with a myriad of empty log streams.

This function runs daily using an Event Bridge schedule (configured at 10:13 UTC in the CDK deployment) and it deletes any log streams that meet the following criteria:

* Retention days specified on the log group
* Last Event Timestamp and Last Injested Timestamp on the steam are 2 days older than calculated retention time
* Log stream is empty

If all of these criteria are met, the log stream will be deleted.

When run, the processor will run until all relevant log streams are removed, or until it times out at 15 minutes. If added to an account that has a lot of historical empty log streams, it may take several runs to complete the cleanup.

The tool is deployed via the AWS CDK v2. To install, do the following:

* Install the AWS CDK v2 (if not installed)
* Set your local console environment to point to the account you wish to deploy to (such as by use of `AWS_PROFILE` environment variable)
* Install the CDK components from `requirements.txt` into your local virtual environment
* Run the following command to deploy: `cdk deploy`