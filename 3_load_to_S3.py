import boto3
import os


def load_csv_to_s3(local_csv_path, bucket_name, s3_prefix):
    s3 = boto3.client('s3')
    for root, dirs, files in os.walk(local_csv_path):
        for file_name in files:
            local_file_path = os.path.join(root, file_name)
            s3_key = os.path.join(s3_prefix, file_name)

            try:
                s3.upload_file(local_file_path, bucket_name, s3_key)
                print(f"File {local_file_path} uploaded to S3: {bucket_name}/{s3_key}")
            except Exception as e:
                print(f"Error uploading {local_file_path} to S3: {e}")


if __name__ == "__main__":
    local_csv_path = 'twitter_trend_output'
    s3_bucket_name = 'TwitterTrendData'
    s3_prefix = 'TwitterTrendData/'
    load_csv_to_s3(local_csv_path, s3_bucket_name, s3_prefix)