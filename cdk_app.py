from constructs import Construct
from aws_cdk import (
    App, 
    Duration,
    Stack,
    aws_iam,
    aws_events,
    aws_events_targets,
    aws_lambda
)

class CloudWatchEmptyLogGroupPurgeTask(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        with open('index.py') as code_file:
            code = code_file.read()

        lambda_function = aws_lambda.Function(self, 'LambdaFunction',
            code = aws_lambda.Code.from_inline(code),
            handler = 'index.lambda_handler',
            runtime = aws_lambda.Runtime.PYTHON_3_9,
            architecture = aws_lambda.Architecture.ARM_64,
            description = 'Purges expired empty log groups from CloudWatch',
            function_name = 'cloudwatch-empty-log-group-purge-task',
            timeout = Duration.minutes(15),
            reserved_concurrent_executions = 1
        )

        iam_policy_statement = aws_iam.PolicyStatement(
            actions = [
                'logs:DeleteLogStream',
                'logs:DescribeLogGroups',
                'logs:DescribeLogStreams',
                'logs:GetLogEvents'
            ],
            resources = [
                'arn:aws:logs:*'
            ]
        )

        iam_policy = aws_iam.Policy(self, 'CloudwatchLogsPolicy', 
            statements = [iam_policy_statement]
        )

        lambda_function.role.attach_inline_policy(iam_policy)

        cron = aws_events.Rule(self, 'CronJob',
            rule_name = 'cloudwatch-empty-log-group-purge-cron',
            schedule = aws_events.Schedule.cron(hour='11', minute='21'),
            description = 'Triggers the daily purge of expired empty log groups from CloudWatch'
        )

        cron.add_target(aws_events_targets.LambdaFunction(lambda_function))


app = App()

CloudWatchEmptyLogGroupPurgeTask(app, 'cloudwatch-empty-log-group-purge-task')

app.synth()
