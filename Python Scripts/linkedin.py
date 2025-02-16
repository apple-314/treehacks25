from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import face_recognition
import re
import requests
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup
import time
import os

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

    # ---
    # IMG
    # ---

    pfp_start = '''pv-top-card__non-self-photo-wrapper ml0'''
    s = soup.find(pfp_start) + len(pfp_start)
    pfp_s = soup.find("https://media.licdn.com", s)
    pfp_e = soup.find("\"", pfp_s)
    pfp = soup[pfp_s:pfp_e].replace("amp;", "").replace("<!-- -->", "").replace("<br/>", "\n")

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

    return pfp, about, experiences, education

async def scrape(fn, ln, file, headless = True, log = False):
    print("Scraping...")
    print(fn)
    print(ln)
    print(file)
    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--disable-gpu')

    client = webdriver.Chrome(options=options)

    liat = "AQEDAVZo6gAFBmSCAAABlEAQG4YAAAGVLCXhPlYAv0yz1MRZNE6ZbykySX83XA5fgvAc9IPI-bixNWy5VFBuYTK0LcxnrORHE2bf44ByN-ZIeBcIRDEf4eDAvvEYPSQ4D2vrrP5aK3llXXcznU-Gi7rN"

    print("Loading face image...")
    fr_image = np.ascontiguousarray(face_recognition.load_image_file(f"{file}"))
    fr_face_encoding = face_recognition.face_encodings(fr_image)
    if len(fr_face_encoding) == 0:
        print("No face found in screenshot!")
        client.quit()
        return None, None, None, None, None
    fr_face_encoding = fr_face_encoding[0]

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

    print("Accessing LinkedIn...")
    client.get("https://www.linkedin.com/")
    client.add_cookie({"name": "li_at", "value": liat})
    client.refresh()

    detected_link = None

    begin2 = time.time()

    if log:
        print("LOG: accessed search")

    for page in range(1, 10):
        SEARCH_URL = f"https://www.linkedin.com/search/results/people/?firstName={fn}&lastName={ln}&origin=GLOBAL_SEARCH_HEADER&page={page}"
        print(f"Searching page {page}...")
        client.get(SEARCH_URL)

        soup = str(BeautifulSoup(client.page_source , "lxml"))
        
        starts = [m.start() for m in re.finditer('data-chameleon-result-urn="urn:li:member:', soup)]
        
        if len(starts) == 0:
            print(f"No results found on page {page}")
            break

        profiles = []

        starts.append(len(soup))
        for i in range(len(starts) - 1):
            s1 = soup.find("https://www.linkedin.com/in/", starts[i])
            e1 = soup.find("?", s1)
            pf = soup[s1:e1]
            print(f"Found profile: {pf}")

            s2 = soup.find("https://media.licdn.com/dms/image/", e1, starts[i+1])
            if s2 == -1:
                print("No profile picture found")
                continue
            e2 = soup.find("\"", s2)
            pfp = soup[s2:e2].replace("amp;", "")

            profiles.append([pf, pfp])
            print("Downloading profile picture...")
            response = requests.get(pfp)
            orig_img = Image.open(BytesIO(response.content)).convert("RGB")
            img = np.array(orig_img)

            print("Running face recognition...")
            face_locations = face_recognition.face_locations(img)
            if len(face_locations) == 0:
                print("No face found in profile picture")
                continue
                
            face_encodings = face_recognition.face_encodings(img, face_locations)

            face_names = []
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"

                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
                    print(f"Found matching face: {name}")

                if name != "Unknown":
                    print("Getting profile info...")
                    pfp, about, experiences, education = get_info(client, pf)
                    client.quit()
                    return pfp, pf, about, experiences, education
    
    print("No matching profile found")
    client.quit()
    return None, None, None, None, None

def update_db(db, fn, ln, about, experiences, education):
    API_KEY = os.getenv("GROQ_API_KEY")
    ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    a, b, c = format_info(about, experiences, education)
    prompt = f"Summarize this person's interest in at most 5 words. ONLY include a list of interests, nothing else. DON'T SAY ANYTHING BEFORE THE INTERESTS!! JUST THE LIST!! THIS MEANS YOUR FINAL RESPONSE SHOULD BE AT MOST 5 WORDS!! Don't include any special characters in your final response (commas ok).\n\nBio:\n{a}\n\nExperiences:\n{b}\n\nEducation:\n{c}\n\n"
    print(prompt)

    data = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
    }

    response = requests.post(ENDPOINT, headers=headers, json=data)
    json_response = response.json()
    interests = json_response["choices"][0]["message"]["content"]

    db.delete_table(f"{fn}{ln}", "LinkedIn")

    for item in about:
        data_dict = {"type": "bio", "description": "\n".join(item)}
        db.write_data_dict(f"{fn}{ln}", "LinkedIn", data_dict)

    for item in experiences:
        data_dict = {"type": "exp", "description": "\n".join(item)}
        db.write_data_dict(f"{fn}{ln}", "LinkedIn", data_dict)

    for item in education:
        data_dict = {"type": "edu", "description": "\n".join(item)}
        db.write_data_dict(f"{fn}{ln}", "LinkedIn", data_dict)

    data_dict = {"type": "interests", "description": interests}
    db.write_data_dict(f"{fn}{ln}", "LinkedIn", data_dict)

    data_dict = {"type": "pfp", "description": pfp}
    db.write_data_dict(f"{fn}{ln}", "LinkedIn", data_dict)