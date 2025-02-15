import requests

# Define the API endpoint
url = "http://127.0.0.1:8000/get_context/"

# Define query parameters
params = {"first_name": "Sai", "last_name": "Konkimalla"}

# Send the GET request
response = requests.get(url, params=params)

# Handle the response
if response.status_code == 200:
    data = response.json()
    print(f"Received context: \nAbout:\n{data['about']}\n\nExperiences:\n{data['experiences']}\n\nEducation:\n{data['education']}")
else:
    print(f"Failed to fetch context. Status code: {response.status_code}")