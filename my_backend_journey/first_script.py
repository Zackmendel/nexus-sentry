import requests

# 1. We act as the Client sending a GET request
# This is a free public API for testing
url = "https://jsonplaceholder.typicode.com/posts/1"
response = requests.get(url)

# 2. Inspect the Response
print(f"Status Code: {response.status_code}") # Should be 200
print("Data Received:")
print(response.json()) # This prints the JSON body
print(response.headers)

