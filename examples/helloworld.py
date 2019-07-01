# NB: This is just some example code to showcase shush's usage.
# This file should not be ran as a script - it will not work!
import shush


# Create a Shush client.
client = shush.Client(
    project_id="solar-system",
    bucket_location="mars-west2",
    keyring_location="jupiter-east1",
)

# Create shush bucket, keyring, and key.
client.initialize()

# Write some shush secrets (directly from byte strings).
client.write_secret("abc_api_key", b"s5TmXcIS9L41hkRdOmg4SpDcd3m5l6Yg")
client.write_secret("xkcd_password", b"correct horse battery staple")

# Write a shush secret from a file object (read in binary mode).
client.write_secret_from_file("top_secret", open("my.secret", "rb"))

# Read all secrets (client location specific).
# Delete each secret after reading.
for secret in client.list_secrets():
    print(client.read_secret(secret))
    client.destroy_secret(secret)
