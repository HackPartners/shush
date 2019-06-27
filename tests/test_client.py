from unittest import mock

import shush


SHUSH_CLIENT_PARAMS = {
    "project_id": "solar-system",
    "bucket_location": "mars-west2",
    "keyring_location": "jupiter-east1",
}


@mock.patch("shush.Client.gcs_client")
@mock.patch("shush.Client.kms_client")
def test_initialize_creates_key_ring(kms_client, gcs_client):
    key_ring_id = "shush-secrets"
    project_id = SHUSH_CLIENT_PARAMS["project_id"]
    location_id = SHUSH_CLIENT_PARAMS["keyring_location"]

    # Instantiate a new shush client and initialize.
    shush.Client(**SHUSH_CLIENT_PARAMS).initialize()

    # Prepare KMS parameters as in KMS API documentation.
    parent = kms_client.location_path(project_id, location_id)

    keyring = {'name': kms_client.key_ring_path(
        project_id, location_id, key_ring_id,
    )}

    # Check KMS method was called once with appropriate parameters.
    # https://github.com/GoogleCloudPlatform/python-docs-samples/blob/950d97a9e783165731c52c3688b743e2f3032209/kms/api-client/snippets.py#L17-L38
    kms_client.create_key_ring.\
        assert_called_once_with(parent, "shush-secrets", keyring)


@mock.patch("shush.Client.gcs_client")
@mock.patch("shush.Client.kms_client")
def test_initialize_creates_bucket(kms_client, gcs_client):
    project_id = SHUSH_CLIENT_PARAMS["project_id"]
    location_id = SHUSH_CLIENT_PARAMS["bucket_location"]
    bucket_name = f"shush-secrets-{project_id}"

    # Instantiate a new shush client and initialize.
    shush.Client(**SHUSH_CLIENT_PARAMS).initialize()

    # Prepare bucket parameter as in API reference.
    bucket = gcs_client.bucket(bucket_name)
    bucket.storage_class = "REGIONAL"

    # Check correct method was called once with appropriate parameters.
    # https://googleapis.github.io/google-cloud-python/latest/storage/buckets.html#google.cloud.storage.bucket.Bucket.create
    bucket.create.assert_called_once_with(
        project=project_id, location=location_id,
    )
