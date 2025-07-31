import json
import os
import urllib.parse
import boto3
import time

# Initialize AWS clients
s3_client = boto3.client('s3')
transcribe_client = boto3.client('transcribe')

def lambda_handler(event, context):
    """
    AWS Lambda function to transcribe audio files uploaded to S3.

    This function is triggered by an S3 PutObject event.
    It starts an AWS Transcribe job for the uploaded audio file
    and saves the transcription (JSON) to a specified S3 output path.
    """
    print(f"Received event: {json.dumps(event)}")

    # 1. Extract information from the S3 event
    try:
        # Get the bucket name and object key from the S3 event
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        object_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
        print(f"Processing file: s3://{bucket_name}/{object_key}")
    except KeyError as e:
        print(f"Error extracting S3 event data: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid S3 event structure.')
        }

    # Ensure the object key starts with 'StaticAudio/' as expected
    if not object_key.startswith('StaticAudio/'):
        print(f"Skipping file {object_key} as it's not in the 'StaticAudio/' prefix.")
        return {
            'statusCode': 200,
            'body': json.dumps('File not in expected prefix, skipping transcription.')
        }

    # Determine the username from the object key (e.g., StaticAudio/username/audio.mp3)
    # Split the key by '/' and get the second part
    parts = object_key.split('/')
    if len(parts) < 3:
        print(f"Object key {object_key} does not contain a username folder. Skipping.")
        return {
            'statusCode': 200,
            'body': json.dumps('No username folder found in object key, skipping transcription.')
        }
    username = parts[1] # This assumes the structure is StaticAudio/username/filename.ext

    # Define the output path for the transcription
    # It will be s3://g7-static-files/StaticTranscription/{username}/audio_filename.json
    audio_filename_without_ext = os.path.splitext(os.path.basename(object_key))[0]
    transcription_output_key = f"StaticTranscription/{username}/{audio_filename_without_ext}.json"

    # 2. Start the AWS Transcribe job
    # Generate a unique job name (Transcribe job names must be unique)
    # Using timestamp and a portion of the object key for uniqueness
    # Replace spaces with hyphens to satisfy the regex pattern for job names
    job_name = f"transcription-job-{int(time.time())}-{audio_filename_without_ext[:50]}".replace(' ', '-')
    media_format = object_key.split('.')[-1].lower() # Extract file extension for media format

    # Check for supported media formats
    supported_formats = ['flac', 'mp3', 'mp4', 'wav', 'amr', 'webm', 'ogg']
    if media_format not in supported_formats:
        print(f"Unsupported media format: {media_format}. Supported formats are: {', '.join(supported_formats)}")
        return {
            'statusCode': 400,
            'body': json.dumps(f"Unsupported media format: {media_format}")
        }

    try:
        # Define transcription settings
        transcription_settings = {
            'LanguageCode': 'en-US',  # You can change this to your audio's language
            'MediaFormat': media_format,
            'Media': {
                'MediaFileUri': f"s3://{bucket_name}/{object_key}"
            },
            'OutputBucketName': bucket_name, # Output to the same bucket
            'OutputKey': transcription_output_key # Specify the full output key
        }

        # If you want to enable speaker labeling, set 'ShowSpeakerLabels': True
        # and provide a 'MaxSpeakerLabels' value between 2 and 10.
        # Otherwise, do not include these settings to avoid BadRequestException.
        # For now, we are removing MaxSpeakerLabels as ShowSpeakerLabels is False by default.
        # If you later set ShowSpeakerLabels to True, you must re-add MaxSpeakerLabels.
        if transcription_settings.get('ShowSpeakerLabels', False):
            # Example if you wanted speaker labels:
            # transcription_settings['Settings'] = {
            #     'ShowSpeakerLabels': True,
            #     'MaxSpeakerLabels': 2 # Example, adjust as needed (2-10)
            # }
            pass # No action needed if ShowSpeakerLabels is False or not present

        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            **transcription_settings # Unpack the dictionary into arguments
        )
        print(f"Started transcription job: {job_name} for s3://{bucket_name}/{object_key}")

        # --- IMPORTANT NOTE ON LONG AUDIO FILES ---
        # For very long audio files (e.g., > 5 minutes), the Lambda function
        # might time out (max 15 minutes execution).
        # A more robust solution for production would be:
        # 1. This Lambda starts the job and exits.
        # 2. Configure AWS Transcribe to send a notification (e.g., to SNS)
        #    when the job completes.
        # 3. Another Lambda function is triggered by that SNS notification
        #    to fetch the transcription result and save it.
        # For simplicity and demonstration, this example includes polling.
        # Be aware of the 15-minute Lambda timeout.

        # 3. Poll for transcription job completion (for shorter audio files)
        max_attempts = 60 # Check every 10 seconds for up to 10 minutes
        for attempt in range(max_attempts):
            status_response = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
            job_status = status_response['TranscriptionJob']['TranscriptionJobStatus']
            print(f"Transcription job {job_name} status: {job_status}")

            if job_status == 'COMPLETED':
                print(f"Transcription job {job_name} completed.")
                # The transcription is automatically saved to the specified OutputKey by Transcribe
                print(f"Transcription saved to: s3://{bucket_name}/{transcription_output_key}")
                return {
                    'statusCode': 200,
                    'body': json.dumps(f'Transcription job {job_name} completed and saved to S3.')
                }
            elif job_status == 'FAILED':
                failure_reason = status_response['TranscriptionJob'].get('FailureReason', 'Unknown reason')
                print(f"Transcription job {job_name} failed: {failure_reason}")
                return {
                    'statusCode': 500,
                    'body': json.dumps(f'Transcription job {job_name} failed: {failure_reason}')
                }
            time.sleep(10) # Wait 10 seconds before checking again

        print(f"Transcription job {job_name} did not complete within the allowed time.")
        return {
            'statusCode': 504,
            'body': json.dumps(f'Transcription job {job_name} timed out.')
        }

    except Exception as e:
        print(f"Error during transcription process: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error transcribing audio: {str(e)}')
        }
