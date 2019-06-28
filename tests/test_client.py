from unittest import mock

import shush


SHUSH_CLIENT_PARAMS = {
    "project_id": "solar-system",
    "bucket_location": "mars-west2",
    "keyring_location": "jupiter-east1",
}


@mock.patch("google.cloud.storage.Client")
@mock.patch("google.cloud.kms_v1.KeyManagementServiceClient")
def test_initialize_creates_key_ring(
    KeyManagementServiceClient,  # noqa: N803 to use CamelCase for class.
    CloudStorageClient,  # noqa: N803 to use CamelCase for class.
):
    key_ring_id = "shush-secrets"
    project_id = SHUSH_CLIENT_PARAMS["project_id"]
    location_id = SHUSH_CLIENT_PARAMS["keyring_location"]

    shush.Client(**SHUSH_CLIENT_PARAMS).initialize()

    # Prepare KMS parameters as in KMS API documentation.
    client = KeyManagementServiceClient()
    parent = client.location_path(project_id, location_id)

    keyring_name = client.key_ring_path(project_id, location_id, key_ring_id)
    keyring = {"name": keyring_name}

    # Check KMS method was called once with appropriate parameters.
    # https://github.com/GoogleCloudPlatform/python-docs-samples/blob/950d97a9e783165731c52c3688b743e2f3032209/kms/api-client/snippets.py#L17-L38
    client.create_key_ring.\
        assert_called_once_with(parent, "shush-secrets", keyring)


@mock.patch("google.cloud.storage.Client")
@mock.patch("google.cloud.kms_v1.KeyManagementServiceClient")
def test_initialize_creates_default_crypto_key(
    KeyManagementServiceClient,  # noqa: N803 to use CamelCase for class.
    CloudStorageClient,  # noqa: N803 to use CamelCase for class.
):
    key_ring_id = "shush-secrets"
    project_id = SHUSH_CLIENT_PARAMS["project_id"]
    location_id = SHUSH_CLIENT_PARAMS["keyring_location"]

    shush.Client(**SHUSH_CLIENT_PARAMS).initialize()

    # Prepare KMS parameters as in KMS API documentation.
    client = KeyManagementServiceClient()
    parent = client.key_ring_path(project_id, location_id, key_ring_id)

    from google.cloud.kms_v1 import enums
    purpose = enums.CryptoKey.CryptoKeyPurpose.ENCRYPT_DECRYPT
    crypto_key = {'purpose': purpose}

    # Check KMS method was called once with appropriate parameters.
    # https://github.com/GoogleCloudPlatform/python-docs-samples/blob/29e4cd6c236567ec35b7fb68ab78823a180b2594/kms/api-client/snippets.py#L41-L63
    client.create_crypto_key. \
        assert_called_once_with(parent, "default", crypto_key)


@mock.patch("google.cloud.storage.Client")
@mock.patch("google.cloud.kms_v1.KeyManagementServiceClient")
def test_initialize_creates_bucket(
    KeyManagementServiceClient,  # noqa: N803 to use CamelCase for class.
    CloudStorageClient,  # noqa: N803 to use CamelCase for class.
):
    project_id = SHUSH_CLIENT_PARAMS["project_id"]
    location_id = SHUSH_CLIENT_PARAMS["bucket_location"]
    bucket_name = f"shush-secrets-{project_id}"

    shush.Client(**SHUSH_CLIENT_PARAMS).initialize()

    # Prepare bucket parameter as in API reference.
    client = CloudStorageClient()
    bucket = client.bucket(bucket_name)
    bucket.storage_class = "REGIONAL"

    # Check correct method was called once with appropriate parameters.
    # https://googleapis.github.io/google-cloud-python/latest/storage/buckets.html#google.cloud.storage.bucket.Bucket.create
    bucket.create.assert_called_once_with(
        project=project_id, location=location_id,
    )
