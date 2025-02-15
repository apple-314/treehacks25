# import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import time
from PIL import Image
import requests
from io import BytesIO
import face_recognition
import numpy as np

def format_info(about, experiences, education):
    about_lines = ["------------", about, ""]

    experience_lines = []
    for exp in experiences:
        experience_lines.append("--------------")
        for l in exp:
            experience_lines.append(l)
        experience_lines.append("")

    education_lines = []
    for edu in education:
        education_lines.append("--------------")
        for l in edu:
            education_lines.append(l)
        education_lines.append("")

    about_s = "\n".join(about_lines)[:-1]
    experience_s = "\n".join(experience_lines)[:-1]
    educaiton_s = "\n".join(education_lines)[:-1]
    return about_s, experience_s, educaiton_s

def get_info(client, link):
    client.get(link)
    time.sleep(1)

    soup = str(BeautifulSoup(client.page_source , "lxml"))

    with open("out.txt", "w") as f:
        f.write(soup)


    # -----
    # ABOUT
    # -----

    about = ""
    about_start = '''<span aria-hidden="true"><!-- -->About'''
    s = soup.find(about_start) + len(about_start)
    if (s != -1):
        about_item = soup.find('''aria-hidden="true">''', s)
        about_end = soup.find("</span>", about_item)
        about = soup[about_item+19:about_end].replace("amp;", "").replace("<!-- -->", "").replace("<br/>", "\n")

    # -----------
    # EXPERIENCES
    # -----------

    exp_start = '''<span aria-hidden="true"><!-- -->Experience'''
    item_start = '''<div class="display-flex align-items-center mr1 t-bold">'''
    field_start = '''aria-hidden="true">'''
    exp_end = '''</section>'''

    s = soup.find(exp_start) + len(exp_start)
    fields = [m.start() for m in re.finditer(field_start, soup)]
    fields.append(100000000)
    items = [m.start() for m in re.finditer(item_start, soup)]
    e = soup.find(exp_end, s)

    cur_item = 0
    done = False

    experiences = []

    if s != -1:
        for i in range(len(items) - 1):
            if (items[i] < s or items[i] > e):
                continue
                
            cur_experience = []

            for j in range(len(fields)):
                if (fields[j] < items[i] or fields[j] > items[i+1] or fields[j] > e):
                    continue

                field_end = soup.find("</span>", fields[j])
                processed_field = soup[fields[j]+19:field_end].replace("amp;", "").replace("<!-- -->", "").replace("<br/>", "\n")
                cur_experience.append(processed_field)

            experiences.append(cur_experience)

    # -----------
    # EDUCATION
    # -----------

    edu_start = '''<span aria-hidden="true"><!-- -->Education'''
    item_start = '''<div class="display-flex align-items-center mr1 hoverable-link-text t-bold">'''
    field_start = '''aria-hidden="true">'''
    edu_end = '''</section>'''

    s = soup.find(edu_start) + len(edu_start)
    fields = [m.start() for m in re.finditer(field_start, soup)]
    fields.append(100000000)
    items = [m.start() for m in re.finditer(item_start, soup)]
    e = soup.find(edu_end, s)

    cur_item = 0
    done = False

    education = []

    if s != -1:
        for i in range(len(items) - 1):
            if (items[i] < s or items[i] > e):
                continue
                
            cur_edu = []

            for j in range(len(fields)):
                if (fields[j] < items[i] or fields[j] > items[i+1] or fields[j] > e):
                    continue

                field_end = soup.find("</span>", fields[j])
                processed_field = soup[fields[j]+19:field_end].replace("amp;", "").replace("<!-- -->", "").replace("<br/>", "\n")
                cur_edu.append(processed_field)

            education.append(cur_edu)

    return about, experiences, education

def scrape(fn, ln, headless = True, log = False):
    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--disable-gpu')

    client = webdriver.Chrome(options=options)

    liat = "AQEDAVZo6gAFBmSCAAABlEAQG4YAAAGVLCXhPlYAv0yz1MRZNE6ZbykySX83XA5fgvAc9IPI-bixNWy5VFBuYTK0LcxnrORHE2bf44ByN-ZIeBcIRDEf4eDAvvEYPSQ4D2vrrP5aK3llXXcznU-Gi7rN"

    fr_image = face_recognition.load_image_file(f"../imgs/{fn}{ln}.png")
    fr_face_encoding = face_recognition.face_encodings(fr_image)[0]

    known_face_encodings = [
        fr_face_encoding
    ]

    known_face_names = [
        f"{fn} {ln}"
    ]

    fn = fn.lower()
    ln = ln.lower()
    all_profiles = []
    pfps = []

    client.get("https://www.linkedin.com/")
    client.add_cookie({"name": "li_at", "value": liat})
    client.refresh()

    detected_link = None

    begin2 = time.time()

    if log:
        print("LOG: accessed search")

    for page in range(1, 10):
        SEARCH_URL = f"https://www.linkedin.com/search/results/people/?firstName={fn}&lastName={ln}&origin=GLOBAL_SEARCH_HEADER&page={page}"

        client.get(SEARCH_URL)

        soup = str(BeautifulSoup(client.page_source , "lxml"))
        
        # starts = [m.start() for m in re.finditer('vSWaujnrxAZrXrdBiXgHxMuBIweBeLKqlvmY', soup)]  # this changes
        starts = [m.start() for m in re.finditer('data-chameleon-result-urn="urn:li:member:', soup)]  # this changes
        
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
            # print(profiles[-1])

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
                    if log:
                        print("LOG: found person")
                    about, experiences, education = get_info(client, pf)
                    return orig_img, pf, about, experiences, education

# img, link = scrape("James", "Chen")
# img, link, about, experiences, education = scrape("James", "Chen", headless=False)

# s = format_info(about, experiences, education)
# print(s)

# input()
# img.show()