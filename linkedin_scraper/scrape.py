# import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re
import time
from PIL import Image
import requests
from io import BytesIO
import face_recognition
import numpy as np

#create a session
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')

client = webdriver.Chrome(options=options)

liat = "AQEDAVZo6gAFBmSCAAABlEAQG4YAAAGUZByfhlYAn8M_eKmWyJ3hQxrW7yGvY7ZXkI25-JTfGDKNz-Qtorud1a8sD32QcGBb2t74ZNlc_YqtOaMSJ1Lq2O_hiW4dueUo_OBzjGbcHKnpxwTZ5MXFzEBN"

sai_image = face_recognition.load_image_file("sai.png")
sai_face_encoding = face_recognition.face_encodings(sai_image)[0]

james_image = face_recognition.load_image_file("james.png")
james_face_encoding = face_recognition.face_encodings(james_image)[0]

known_face_encodings = [
    sai_face_encoding,
    james_face_encoding
]
known_face_names = [
    "Sai Konkimalla",
    "James Chen"
]

begin = time.time()

fn = "james"
ln = "chen"
all_profiles = []
pfps = []

client.get("https://www.linkedin.com/")
client.add_cookie({"name": "li_at", "value": liat})
client.refresh()

detected_link = None

begin2 = time.time()

for page in range(1, 10):
    SEARCH_URL = f"https://www.linkedin.com/search/results/people/?firstName={fn}&lastName={ln}&origin=GLOBAL_SEARCH_HEADER&page={page}"

    client.get(SEARCH_URL)

    soup = str(BeautifulSoup(client.page_source , "lxml"))
    
    # starts = [m.start() for m in re.finditer('vSWaujnrxAZrXrdBiXgHxMuBIweBeLKqlvmY', soup)]  # this changes
    starts = [m.start() for m in re.finditer('JeSqqbWzFiqyizxycCHmniVoBOKUNXaTE', soup)]  # this changes
    
    if len(starts) == 0:
        break

    profiles = []

    starts.append(len(soup))
    for i in range(len(starts) - 1):
        s1 = soup.find("https://www.linkedin.com/in/", starts[i])
        e1 = soup.find("?", s1)
        pf = soup[s1:e1]

        s2 = soup.find("https://media.licdn.com/dms/image/", e1, starts[i+1])
        if s2 == -1:
            continue
        e2 = soup.find("\"", s2)
        pfp = soup[s2:e2].replace("amp;", "")

        profiles.append([pf, pfp])
        print(profiles[-1])

        response = requests.get(pfp)
        orig_img = Image.open(BytesIO(response.content)).convert("RGB")
        img = np.array(orig_img)

        face_locations = face_recognition.face_locations(img)
        face_encodings = face_recognition.face_encodings(img, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]

            if name != "Unknown":
                # print(f"** {pf} **")
                # print(time.time() - begin)
                # print(time.time() - begin2)
                # orig_img.show()
                # input()
                detected_link = pf
                break

        if detected_link != None:
            break

    if detected_link != None:
        break

