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

# def get_info(client, link):
#     client.get(link)
#     client.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#     WebDriverWait(client, 10).until(
#         EC.presence_of_element_located((By.TAG_NAME, "body"))  # Adjust the condition based on required elements
#     )
#     time.sleep(3)
#     soup = str(BeautifulSoup(client.page_source , "lxml"))
#     print(soup)
#     input()

def get_info(client, link):
    """
    Loads the LinkedIn profile at 'link', waits for key elements to load,
    clicks any "see more" buttons to expand hidden sections, and scrolls
    incrementally to ensure dynamic content is loaded. Returns the full HTML.
    """
    client.get(link)
    
    # Wait for the profile's top card to be present (adjust XPath if needed)
    WebDriverWait(client, 15).until(
        EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "pv-top-card")]'))
    )
    time.sleep(2)
    
    # Click any "see more" buttons that are immediately visible
    try:
        see_more_buttons = client.find_elements(By.XPATH, '//button[contains(@aria-label, "see more")]')
        for btn in see_more_buttons:
            try:
                client.execute_script("arguments[0].click();", btn)
                time.sleep(1)
            except Exception as e:
                print(f"Error clicking 'see more' button: {e}")
    except Exception as e:
        print(f"Error finding 'see more' buttons: {e}")
    
    # Incrementally scroll to the bottom to load lazy-loaded content
    scroll_pause_time = 2
    last_height = client.execute_script("return document.body.scrollHeight")
    while True:
        client.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        
        # Optionally, try clicking any new "see more" buttons during scroll
        try:
            see_more_buttons = client.find_elements(By.XPATH, '//button[contains(@aria-label, "see more")]')
            for btn in see_more_buttons:
                try:
                    client.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
                except Exception as e:
                    print(f"Error clicking 'see more' button during scroll: {e}")
        except Exception as e:
            print(f"Error during scroll while searching for buttons: {e}")
        
        new_height = client.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Allow any final dynamic content to load
    time.sleep(2)
    soup = str(BeautifulSoup(client.page_source , "lxml"))
    print(soup)
    input()

def scrape(fn, ln):
    options = Options()
    # options.add_argument('--headless')
    options.add_argument('--disable-gpu')

    client = webdriver.Chrome(options=options)

    liat = "AQEDAVZo6gAFBmSCAAABlEAQG4YAAAGVLCXhPlYAv0yz1MRZNE6ZbykySX83XA5fgvAc9IPI-bixNWy5VFBuYTK0LcxnrORHE2bf44ByN-ZIeBcIRDEf4eDAvvEYPSQ4D2vrrP5aK3llXXcznU-Gi7rN"

    fr_image = face_recognition.load_image_file(f"{fn}{ln}.png")
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
                    get_info(client, pf)
                    return orig_img, pf

# img, link = scrape("James", "Chen")
img, link = scrape("Kaival", "Shah")
# print(f"\n\n{link}")
# img.show()