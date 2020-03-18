# -*- coding: utf-8 -*-
import boto3
import time


def disable_compute_environment(client, arn, attempts=3):
    attempt = 1
    success = False
    while attempt <= attempts:
        try:
            client.update_compute_environment(
                computeEnvironment=arn,
                state="DISABLED",
                computeResources={
                    'minvCpus': 0
                }
            )
            success = True
            time.sleep(3)
            break
        except:
            attempt += 1
            time.sleep(3)
    return success


def enable_compute_environment(client, arn, cpus, attempts=3):
    attempt = 1
    success = False
    while attempt <= attempts:
        try:
            client.update_compute_environment(
                computeEnvironment=arn,
                state="ENABLED",
                computeResources={
                    'minvCpus': cpus,
                    'desiredvCpus': cpus
                }
            )
            success = True
            time.sleep(3)
            break
        except:
            attempt += 1
            time.sleep(3)
    return success


def handler(event, context):
    client = boto3.client('batch')
    active_statuses = ['SUBMITTED', 'PENDING', 'RUNNABLE', 'STARTING', 'RUNNING']
    job_queues = client.describe_job_queues()['jobQueues']
    compute_environments = []
    for queue in job_queues:
        jobs = [client.list_jobs(jobQueue=queue['jobQueueArn'], jobStatus=status)["jobSummaryList"] for status in active_statuses]
        if not any(jobs):
            compute_environments.extend([i["computeEnvironment"] for i in queue["computeEnvironmentOrder"]])
    if compute_environments:
        compute_environments_to_reset = [
            i for i in client.describe_compute_environments()['computeEnvironments']
            if i['computeEnvironmentArn'] in compute_environments
            and i['computeResources']['minvCpus'] != i['computeResources']['desiredvCpus']
        ]
        for env in compute_environments_to_reset:
            print("Resetting\n", env)
            success = disable_compute_environment(
                client=client,
                arn=env['computeEnvironmentArn']
            )
            assert success, "Could not successfully disable {0}".format(env['computeEnvironmentArn'])
            success = enable_compute_environment(
                client=client,
                arn=env['computeEnvironmentArn'],
                cpus=env['computeResources']['minvCpus']
            )
            assert success, "Could not successfully enable {0}".format(env['computeEnvironmentArn'])
    print("Finished successfully!")
    return
