import shush

client = shush.Client(
    project_id="solar-system",
    bucket_location="mars-west2",
    keyring_location="jupiter-east1",
)

# client.initialize()

client.write_secret("abc_api_key", b"s5TmXcIS9L41hkRdOmg4SpDcd3m5l6Yg")
client.write_secret("xkcd_password", b"correct horse battery staple")
# client.write_secret("top_secret", open("my.secret", "rb"))

print(client.list_secrets())
print(client.read_secret("xkcd_password"))

client.destroy("abc_api_key")
client.destroy("xkcd_password")
print(client.list_secrets())
