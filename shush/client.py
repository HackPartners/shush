# @todo: add checks to ensure shush has been initialized in all methods.
from typing import List, Optional

from google.auth.credentials import Credentials
from google.cloud import kms_v1
from google.cloud import storage
from google.cloud.kms_v1 import enums


class Client:

    def __init__(
        self,
        project_id: str,
        bucket_location: str,
        keyring_location: str,
        credentials: Optional[Credentials] = None,
    ):
        self.project_id = project_id
        self.bucket_location = bucket_location
        self.keyring_location = keyring_location
        self.credentials = credentials
        self.bucket_name = f"shush-secrets-{project_id}"

        self.gcs_client = storage.Client(
            project=project_id,
            credentials=credentials,
        )
        self.kms_client = kms_v1.KeyManagementServiceClient(
            credentials=credentials,
        )

    def initialize(self) -> None:
        # Step 1: Create Google Cloud KMS keyring
        parent = self.kms_client.location_path(
            self.project_id, self.keyring_location,
        )

        keyring_name = self.kms_client.key_ring_path(
            self.project_id, self.keyring_location, "shush-secrets",
        )

        keyring = {"name": keyring_name}
        self.kms_client.create_key_ring(parent, "shush-secrets", keyring)

        # Step 2: Create Google Cloud KMS "default" key
        purpose = enums.CryptoKey.CryptoKeyPurpose.ENCRYPT_DECRYPT

        crypto_key = {'purpose': purpose}
        self.kms_client.create_crypto_key(keyring_name, "default", crypto_key)

        # Step 3: Create Google Cloud Storage bucket
        bucket = self.gcs_client.bucket(self.bucket_name)
        bucket.storage_class = "REGIONAL"

        bucket.create(project=self.project_id, location=self.bucket_location)

    def write_secret(self, secret_name: str, secret_plaintext: bytes) -> None:
        # Step 1: Encrypt the plaintext using Google Cloud KMS
        name = self.kms_client.crypto_key_path_path(
            self.project_id,
            self.keyring_location,
            "shush-secrets",
            "default",
        )

        ciphertext = self.kms_client.encrypt(name, secret_plaintext).ciphertext

        # Step 2: Create and upload blob to Google Cloud Storage
        bucket = self.gcs_client.get_bucket(self.bucket_name)
        blob = bucket.blob(
            f"{self.keyring_location}/"
            f"default/{secret_name}.encrypted",
        )

        blob.upload_from_string(ciphertext)

    def read_secret(self, secret_name: str) -> bytes:
        # Step 1: Read encrypted blob from Google Cloud Storage
        bucket = self.gcs_client.get_bucket(self.bucket_name)
        blob = bucket.get_blob(
            f"{self.keyring_location}/"
            f"default/{secret_name}.encrypted",
        )

        if blob is None:
            raise ValueError(f"Could not find secret with name {secret_name}.")

        ciphertext = blob.download_as_string()

        # Step 2: Decrypt the ciphertext using Google Cloud KMS
        name = self.kms_client.crypto_key_path_path(
            self.project_id,
            self.keyring_location,
            "shush-secrets",
            "default",
        )

        return self.kms_client.decrypt(name, ciphertext).plaintext

    def destroy_secret(self, secret_name: str) -> None:
        bucket = self.gcs_client.get_bucket(self.bucket_name)
        blob = bucket.get_blob(
            f"{self.keyring_location}/"
            f"default/{secret_name}.encrypted",
        )

        if blob is None:
            raise ValueError(f"Could not find secret with name {secret_name}.")

        blob.delete()
