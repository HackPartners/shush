from google.auth import credentials
from google.cloud import kms_v1
from google.cloud import storage


class Client:

    @property
    def gcs_client(self):
        if self._gcs_client is None:
            self._gcs_client = storage.Client(
                project=self.project_id,
                credentials=self.credentials,
            )
        return self._gcs_client

    @property
    def kms_client(self):
        if self._kms_client is None:
            self._kms_client = kms_v1.KeyManagementServiceClient(
                credentials=self.credentials,
            )
        return self._kms_client

    def __init__(
        self,
        project_id: str,
        bucket_location: str,
        keyring_location: str,
        # Can I type it like this instead of using Any?
        credentials: credentials.Credentials = None,
    ) -> None:

        self._gcs_client = None
        self._kms_client = None

        self.project_id = project_id
        self.bucket_location = bucket_location
        self.keyring_location = keyring_location
        self.credentials = credentials

    def initialize(self) -> None:
        # Step 1: Create Google Cloud KMS keyring
        parent = self.kms_client.location_path(
            self.project_id, self.keyring_location,
        )

        keyring_name = self.kms_client.key_ring_path(
            self.project_id, self.keyring_location, "shush-secrets",
        )

        self.kms_client.create_key_ring(
            parent, "shush-secrets", {'name': keyring_name}
        )

        # Step 2: Create Google Cloud Storage bucket
        bucket_name = f"shush-secrets-{self.project_id}"
        bucket = self.gcs_client.bucket(bucket_name)
        bucket.storage_class = "REGIONAL"

        bucket.create(project=self.project_id, location=self.bucket_location)
