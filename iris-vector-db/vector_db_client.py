import requests
import json
import time
from datetime import datetime

# Define the server URL
SERVER_URL = "http://127.0.0.1:8000/receive"

# JSON data to send (converted to a string)
# data_list = [
#     {
#         "type": "Experience",
#         "title": "Software Engineer",
#         "description": "Developed scalable web applications.",
#         "name": "JamesChen",
#         "msg_type": "LinkedIn"
#     },
#     {
#         "type": "Experience",
#         "title": "Data Scientist",
#         "description": "Built machine learning models for predictions.",
#         "name": "JamesChen",
#         "msg_type": "LinkedIn"
#     },
#     {
#         "type": "Experience",
#         "title": "DevOps Engineer",
#         "description": "Automated CI/CD pipelines for deployments.",
#         "name": "JamesChen",
#         "msg_type": "LinkedIn"
#     },
#     {
#         "type": "Experience",
#         "title": "Backend Developer",
#         "description": "Designed and optimized REST APIs.",
#         "name": "JamesChen",
#         "msg_type": "LinkedIn"
#     },
#     {
#         "type": "Experience",
#         "title": "Full Stack Developer",
#         "description": "Worked on frontend and backend technologies.",
#         "name": "JamesChen",
#         "msg_type": "LinkedIn"
#     },
#     {
#         "type": "Experience",
#         "title": "Cloud Engineer",
#         "description": "Managed cloud infrastructure using AWS.",
#         "name": "JamesChen",
#         "msg_type": "LinkedIn"
#     },
#     {
#         "type": "Experience",
#         "title": "AI Engineer",
#         "description": "Implemented deep learning algorithms for AI applications.",
#         "name": "JamesChen",
#         "msg_type": "LinkedIn"
#     },
#     {
#         "type": "Experience",
#         "title": "Security Engineer",
#         "description": "Developed security policies and penetration testing.",
#         "name": "JamesChen",
#         "msg_type": "LinkedIn"
#     },
#     {
#         "type": "Experience",
#         "title": "Embedded Systems Engineer",
#         "description": "Built firmware for IoT devices.",
#         "name": "JamesChen",
#         "msg_type": "LinkedIn"
#     },
#     {
#         "type": "Experience",
#         "title": "Game Developer",
#         "description": "Designed and developed engaging games.",
#         "name": "JamesChen",
#         "msg_type": "LinkedIn"
#     },
#     {
#         "type": "Experience",
#         "title": "Mobile Developer",
#         "description": "Created mobile apps for Android and iOS.",
#         "name": "JamesChen",
#         "msg_type": "LinkedIn"
#     },
#     {
#         "type": "Experience",
#         "title": "Machine Learning Engineer",
#         "description": "Developed and deployed ML models into production.",
#         "name": "JamesChen",
#         "msg_type": "LinkedIn"
#     },
#     {
#         "type": "Experience",
#         "title": "Site Reliability Engineer",
#         "description": "Ensured high availability and reliability of systems.",
#         "name": "JamesChen",
#         "msg_type": "LinkedIn"
#     },
#     {
#         "type": "Experience",
#         "title": "Business Analyst",
#         "description": "Analyzed market trends to optimize business processes.",
#         "name": "JamesChen",
#         "msg_type": "LinkedIn"
#     },
#     {
#         "type": "Experience",
#         "title": "Cybersecurity Analyst",
#         "description": "Monitored and responded to security threats.",
#         "name": "JamesChen",
#         "msg_type": "LinkedIn"
#     },
#     {
#         "type": "Experience",
#         "title": "Blockchain Developer",
#         "description": "Developed smart contracts and decentralized apps.",
#         "name": "JamesChen",
#         "msg_type": "LinkedIn"
#     },
#     {
#         "type": "Experience",
#         "title": "Frontend Developer",
#         "description": "Designed user interfaces using modern frameworks.",
#         "name": "JamesChen",
#         "msg_type": "LinkedIn"
#     },
#     {
#         "type": "Experience",
#         "title": "Database Administrator",
#         "description": "Managed and optimized database performance.",
#         "name": "JamesChen",
#         "msg_type": "LinkedIn"
#     },
#     {
#         "type": "Experience",
#         "title": "Network Engineer",
#         "description": "Configured and maintained network infrastructures.",
#         "name": "JamesChen",
#         "msg_type": "LinkedIn"
#     },
#     {
#         "type": "Experience",
#         "title": "Software Architect",
#         "description": "Designed high-level software architecture for scalability.",
#         "name": "JamesChen",
#         "msg_type": "LinkedIn"
#     }
# ]

# for data_dict in data_list:
#     json_string = json.dumps(data_dict)  # Convert dictionary to JSON string

#     # Send POST request with raw JSON string
#     response = requests.post(SERVER_URL, data=json_string)

#     # Print server response
#     print("Server Response:", response.json())
#     time.sleep(5)


data_dict = {
    "conv_id" : 1,
    "time_stamp" : str(datetime.now().replace(microsecond=0)),
    "transcript" : "dssdf"
}

json_string = json.dumps(data_dict)  # Convert dictionary to JSON string

# Send POST request with raw JSON string
response = requests.post(SERVER_URL, data=json_string)

# Print server response
print("Server Response:", response.json())
time.sleep(5)