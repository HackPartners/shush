from io import BufferedReader
from os.path import basename
from typing import BinaryIO
from typing import List, Optional

from google.auth.credentials import Credentials
from google.cloud import kms_v1
from google.cloud import storage
from google.cloud.kms_v1 import enums
from google.cloud.storage.blob import Blob
from google.cloud.storage.bucket import Bucket


class Client:

    @property
    def kms_key_path(self) -> str:
        """Return fully-qualified crypto_key_path string for shush key."""
        return self.kms_client.crypto_key_path_path(
            self.project_id,
            self.keyring_location,
            self.KEYRING_NAME,
            self.KEY_NAME,
        )

    @property
    def bucket_name(self) -> str:
        variables = {"bucket_location": self.bucket_location, "project_id": self.project_id}
        return self.bucket_name_template.format(**variables)

    @property
    def bucket(self) -> Bucket:
        # Raises google.cloud.storage.exceptions.NotFound if not found.
        return self.gcs_client.get_bucket(self.bucket_name)

    def __init__(
        self,
        project_id: str,
        bucket_location: str,
        keyring_location: str,
        credentials: Optional[Credentials] = None,
        bucket_name_template: str = "{bucket_location}-shush-secrets-{project_id}",
    ):
        self.KEY_NAME = "default"
        self.KEYRING_NAME = "shush-keyring"

        self.project_id = project_id
        self.bucket_location = bucket_location
        self.keyring_location = keyring_location
        self.credentials = credentials
        self.bucket_name_template = bucket_name_template

        self.gcs_client = storage.Client(
            project=project_id,
            credentials=credentials,
        )
        self.kms_client = kms_v1.KeyManagementServiceClient(
            credentials=credentials,
        )

    # @todo: needs some work on half-init, or re-init.
    def initialize(self) -> None:
        # Step 1: Create Google Cloud KMS keyring
        parent = self.kms_client.location_path(
            self.project_id, self.keyring_location,
        )

        keyring_name = self.kms_client.key_ring_path(
            self.project_id, self.keyring_location, self.KEYRING_NAME,
        )

        keyring = {"name": keyring_name}
        self.kms_client.create_key_ring(parent, self.KEYRING_NAME, keyring)

        # Step 2: Create Google Cloud KMS default shush key
        purpose = enums.CryptoKey.CryptoKeyPurpose.ENCRYPT_DECRYPT

        crypto_key = {'purpose': purpose}
        self.kms_client.create_crypto_key(
            keyring_name,
            self.KEY_NAME,
            crypto_key,
        )

        # Step 3: Create Google Cloud Storage bucket
        bucket = self.gcs_client.bucket(self.bucket_name)
        bucket.storage_class = "REGIONAL"

        bucket.create(project=self.project_id, location=self.bucket_location)

    def _get_secret_path(self, name: str) -> str:
        """Get the bucket relative GCS path to a secret"""
        return f"{self.keyring_location}/{self.KEY_NAME}/{name}"

    def _get_secret_blob(self, name: str) -> Blob:
        """Get the GCS blob object for a specific secret"""
        path = self._get_secret_path(name)
        blob = self.bucket.get_blob(path)

        if blob is None:
            raise ValueError(f"Secret blob \"{path}\" not found.")

        return blob

    def list_secrets(self) -> List[str]:
        blobs = self.bucket.list_blobs(prefix=self._get_secret_path(""))
        return list(map(lambda b: basename(b.name), blobs))

    def read_secret(self, secret_name: str) -> bytes:
        ciphertext = self._get_secret_blob(secret_name).download_as_string()
        return self.kms_client.decrypt(self.kms_key_path, ciphertext).plaintext

    def write_secret(self, name: str, plaintext: bytes) -> None:
        kms_response = self.kms_client.encrypt(self.kms_key_path, plaintext)
        blob = self.bucket.blob(self._get_secret_path(name))
        blob.upload_from_string(kms_response.ciphertext)

    def write_secret_from_file(self, name: str, plainfile: BinaryIO) -> None:
        """Usage: write_secret_from_file("secret", open("private", "rb"))"""
        # https://docs.python.org/3/library/io.html#binary-i-o
        # io.BufferedReader means that the file was opened in binary mode.
        if not isinstance(plainfile, BufferedReader):
            raise ValueError(f"Type {type(plainfile)} is not BufferedReader.")

        kms_max_plaintext_size = 64 * 1024  # Must be up to 64 kibibytes.
        plaintext = plainfile.read(kms_max_plaintext_size + 1)

        if len(plaintext) > kms_max_plaintext_size:
            raise ValueError(f"Secret size must be less than 64 KiB.")
        return self.write_secret(name, plaintext)

    def destroy_secret(self, secret_name: str) -> None:
        self._get_secret_blob(secret_name).delete()
