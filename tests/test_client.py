import shutil
import tempfile
from os import path
from unittest import TestCase, mock

import shush


SHUSH_CLIENT_PARAMS = {
    "project_id": "solar-system",
    "bucket_location": "mars-west2",
    "keyring_location": "jupiter-east1",
}


class TestInitialise(TestCase):

    def setUp(self):
        # https://docs.python.org/3/library/unittest.mock.html#patch-methods-start-and-stop
        self.gcs_client = mock.patch("google.cloud.storage.Client").start()
        self.kms_client = mock.patch("google.cloud.kms_v1.KeyManagementServiceClient").start()

        # Various Google Cloud Platform parameters.
        self.key_ring_id = "shush-keyring"
        self.project_id = SHUSH_CLIENT_PARAMS["project_id"]

        # Create shush client for all tests.
        self.client = shush.Client(**SHUSH_CLIENT_PARAMS)
        self.client.initialize()

    def tearDown(self):
        # Undo all patches.
        mock.patch.stopall()

    def test_creates_key_ring(self):
        location_id = SHUSH_CLIENT_PARAMS["keyring_location"]

        # Prepare KMS parameters as in KMS API documentation.
        client = self.kms_client()
        parent = client.location_path(self.project_id, location_id)

        keyring_name = client.key_ring_path(self.project_id, location_id, self.key_ring_id)
        keyring = {"name": keyring_name}

        # Check KMS method was called once with appropriate parameters.
        # https://github.com/GoogleCloudPlatform/python-docs-samples/blob/950d97a9e783165731c52c3688b743e2f3032209/kms/api-client/snippets.py#L17-L38
        client.create_key_ring.\
            assert_called_once_with(parent, self.key_ring_id, keyring)

    def test_creates_default_crypto_key(self):
        location_id = SHUSH_CLIENT_PARAMS["keyring_location"]

        # Prepare KMS parameters as in KMS API documentation.
        client = self.kms_client()
        parent = client.key_ring_path(self.project_id, location_id, self.key_ring_id)

        from google.cloud.kms_v1 import enums
        purpose = enums.CryptoKey.CryptoKeyPurpose.ENCRYPT_DECRYPT
        crypto_key = {"purpose": purpose}

        # Check KMS method was called once with appropriate parameters.
        # https://github.com/GoogleCloudPlatform/python-docs-samples/blob/29e4cd6c236567ec35b7fb68ab78823a180b2594/kms/api-client/snippets.py#L41-L63
        client.create_crypto_key. \
            assert_called_once_with(parent, "default", crypto_key)

    def test_creates_bucket(self):
        location_id = SHUSH_CLIENT_PARAMS["bucket_location"]
        bucket_name = f"shush-secrets-{self.project_id}"

        # Prepare bucket parameter as in API reference.
        client = self.gcs_client()
        bucket = client.bucket(bucket_name)
        bucket.storage_class = "REGIONAL"

        # Check correct method was called once with appropriate parameters.
        # https://googleapis.github.io/google-cloud-python/latest/storage/buckets.html#google.cloud.storage.bucket.Bucket.create
        bucket.create.assert_called_once_with(
            project=self.project_id, location=location_id,
        )


class TestWriteSecretMethods(TestCase):

    def setUp(self):
        # https://docs.python.org/3/library/unittest.mock.html#patch-methods-start-and-stop
        mock.patch("google.cloud.storage.Client").start()
        mock.patch("google.cloud.kms_v1.KeyManagementServiceClient").start()

        # Create shush client for all tests.
        self.client = shush.Client(**SHUSH_CLIENT_PARAMS)

        # Create a temporary directory and file for testing.
        self.directory = tempfile.mkdtemp()
        self.secret_file = path.join(self.directory, "secret.tmp")

        f = open(self.secret_file, "w")
        f.write("correct horse battery staple")

    def tearDown(self):
        # Undo all patches.
        mock.patch.stopall()
        # Remove temporary directory.
        shutil.rmtree(self.directory)

    def test_opened_file_not_binary_raises_error(self):
        secret = open(self.secret_file, "r")
        with self.assertRaises(ValueError):
            self.client.write_secret_from_file("secret", secret)
