from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import numpy as np
from scipy.io.wavfile import write
import whisper
import mss
import cv2
from bs4 import BeautifulSoup
import time
from datetime import datetime
import os
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

app = FastAPI()

accumulated_samples: List[float] = []

model = whisper.load_model("base")

name = ""

class AudioSamples(BaseModel):
    samples: List[float]

@app.post("/upload_samples")
async def upload_samples(data: AudioSamples):
    """
    Endpoint for streaming audio samples from Swift.
    The payload should be a JSON object like:
      { "samples": [0.02977, 0.03075, ...] }
    """
    global accumulated_samples
    accumulated_samples.extend(data.samples)
    return {
        "message": f"Received {len(data.samples)} samples. Total samples stored: {len(accumulated_samples)}."
    }

@app.post("/finalize")
async def finalize_audio():
    """
    Endpoint to finalize the audio stream.
    This converts all accumulated samples into a WAV file.
    """
    global accumulated_samples
    if not accumulated_samples:
        raise HTTPException(status_code=400, detail="No audio samples received.")

    # Convert the accumulated samples to a numpy array (float32)
    audio_data = np.array(accumulated_samples, dtype=np.float32)

    # Convert the float samples (assumed to be in -1.0 to 1.0) to 16-bit PCM values.
    audio_int16 = np.int16(audio_data * 32767)

    # Define the sample rate in Hz (adjust if needed)
    sample_rate = 44100
    output_file = "output.wav"

    # Write the audio data to a WAV file.
    write(output_file, sample_rate, audio_int16)

    # Transcribe the audio using Whisper
    try:
        result = model.transcribe(output_file)
        transcription = result["text"].strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        # Clear the accumulator after finalizing
        accumulated_samples.clear()

    print(transcription)
    return {"transcription": transcription}

def capture_single_screenshot():
    """Capture a single screenshot and save it with timestamp"""
    with mss.mss() as sct:
        # Capture the primary monitor's screen
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        # Convert to a NumPy array and change color format from BGRA to BGR
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        
        # Create timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        
        # Save the image
        cv2.imwrite(filename, frame)
        return filename

@app.post("/count_contacts")
async def count_contacts(data: str = Body(..., media_type="text/plain")):
    # Print the received string
    print(data)
    # Return a success message
    return JSONResponse(content={"message": "success"})

@app.post("/obtain_name")
async def obtain_name(data: str = Body(..., media_type="text/plain")):
    # Print the received string
    print("printing the received name string")
    print(data)
    global name
    name = data
    # Return a success message
    return JSONResponse(content={"message": "success", "name": data})

@app.post("/capture_gesture")
async def capture_gesture(data: dict):
    """
    Endpoint for capturing pinch gesture timestamps from Vision Pro.
    The payload should be a JSON object like:
    { "timestamp": "2025-02-15T10:30:45Z" }
    """
    print("Received gesture timestamp:", data["timestamp"])
    
    # Capture a screenshot
    screenshot_file = capture_single_screenshot()
    
    # Split the name into first and last name
    global name
    first_name = name.split()[0]
    last_name = name.split()[1] if len(name.split()) > 1 else ""
    orig_img, pf, about, experiences, education = await scrape(first_name, last_name, screenshot_file, headless=False)
    
    if pf is None:
        return {
            "message": f"Received timestamp: {data['timestamp']}. Total gestures captured: 1. No matching LinkedIn profile found.",
            "screenshot": screenshot_file
        }
        
    print("Profile found!")
    print(f"About: {about}")
    print(f"Experiences: {experiences}")
    print(f"Education: {education}")
    
    return {
        "message": f"Received timestamp: {data['timestamp']}. Total gestures captured: 1.",
        "screenshot": screenshot_file,
        "profile": {
            "name": first_name + " " + last_name,
            "about": about,
            "experiences": experiences,
            "education": education,
            "profile_url": pf
        }
    }

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

    # liat = "AQEDAVZo6gAFBmSCAAABlEAQG4YAAAGVLCXhPlYAv0yz1MRZNE6ZbykySX83XA5fgvAc9IPI-bixNWy5VFBuYTK0LcxnrORHE2bf44ByN-ZIeBcIRDEf4eDAvvEYPSQ4D2vrrP5aK3llXXcznU-Gi7rN"
    liat = "AQEDAVfBjbMCGjz2AAABlQ4Q3SgAAAGVMh1hKE4ApVIpMIJnh2ClzonkXaMz9pnqOS5B1krHwPYxnYanrv8mNe5mjHFbEZ__I9KaIDeFdQfwnUzXjtvWFl2qsF6a6-0kPKpskJiPIjbsy3T_08pW9hUC"

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
                    about, experiences, education = get_info(client, pf)
                    client.quit()
                    return orig_img, pf, about, experiences, education
    
    print("No matching profile found")
    client.quit()
    return None, None, None, None, None

@app.get("/get_profiles")
async def get_profiles():
    """
    Returns a JSON object containing profile information for specific individuals.
    """
    profiles = {
        "Sai Konkimalla": {
            "LinkedIn": {
                "bio": "I am an undergrad at Stanford studying math and computer science. I am passionate about mathematics, robotics, computer systems, parallel computing, and machine learning, and I am interested to work/research in the intersection of these fields.\n\nI would love to chat about any of topics above, so feel free to reach out! I am also actively looking for summer work/research opportunities in the above fields.",
                "experiences": [
                    "R&D Software and Robotics Intern\nReazon Holdings, inc.\nTokyo, Japan\nDeveloped software for teleoperated humanoid bartending robot",
                    "Guidance, Navigation, and Controls (GNC) and Embedded Systems Intern\nRaytheon · Internship\nTucson, Arizona, United States · On-site\nDesigned and verified functionality of GPS M-code receiver",
                    "Student Researcher, Applied Math\nUniversity of Arizona · Part-time\nTucson, Arizona, United States\nResearched physics-based reinforcement learning algorithms in energy environments",
                    "Lead Teaching Assistant\nRandom Math Inc. · Part-time\nRemote\nHelped high school students prepare for national math competitions (AMC 12/AIME)"
                ],
                "education": [
                    "Stanford University\nBachelor of Science - BS, Mathematics and Computer Science\nActivities and societies: Stanford University Mathematical Organization (SUMO), Stanford Math Tournament (SMT)",
                    "University of Arizona\nDual Enrollment, Mathematics\nSelected coursework: MATH 223: Vector Calculus, MATH 254: Differential Equations, and MATH 313: Linear Algebra"
                ]
            },
            "convos": [],
            "interests": "Math, Robotics, Computer Science",
            "img": "https://media.licdn.com/dms/image/v2/D4D03AQEPcYIdcOsMJA/profile-displayphoto-shrink_400_400/profile-displayphoto-shrink_400_400/0/1698282810114?e=1745452800&v=beta&t=UvqvxyAtsd009IzoR-2-MOY-vxWPmhDRTe-ky84gtGo"
        },
        "James Chen": {
            "LinkedIn": {
                "bio": "",
                "experiences": [
                    "Software Engineering Intern\nReazon Holdings, inc. · Internship\nTokyo, Japan",
                    "Undergraduate Researcher (NLP, LLMs, Conversational Agents)\nStanford University Department of Computer Science\nProfessor Monica Lam's Lab",
                    "First Place Grand Prize & Reazon Holdings Prize\nTreeHacks\nStanford University\nBaymax, Your Personal Healthcare Companion",
                    "Research Intern (Data Science Project)\nU.S. Naval Research Laboratory\nMonterey, California",
                    "Research Intern (Machine Learning Project)\nNASA Ames Research Center\nMountain View, California"
                ],
                "education": [
                    "Stanford University\nBachelor of Science - BS, Computer Science\nGPA: 4.07"
                ]
            },
            "convos": [],
            "interests": "Physics, English, Robotics",
            "img": "https://media.licdn.com/dms/image/v2/D4D03AQEPcYIdcOsMJA/profile-displayphoto-shrink_400_400/profile-displayphoto-shrink_400_400/0/1698282810114?e=1745452800&v=beta&t=UvqvxyAtsd009IzoR-2-MOY-vxWPmhDRTe-ky84gtGo"
        },
        "Kaival Shah": {
            "LinkedIn": {
                "bio": "Hey! I'm Kaival, a student at Northwestern University studying Applied Mathematics and Computer Science. I love design thinking and software that changes lives.\n• kaival@u.northwestern.edu\n• https://github.com/kaivalsshah",
                "experiences": [
                    "Resident Founder\nThe Garage at Northwestern University",
                    "Co-Founder\nStealth\nRestaurant deals & rewards; sold to Quill Payments, Inc.",
                    "Mathematical Biology Researcher @ Research Mentorship Program\nUC Santa Barbara\nOn-site\n• Selected as 1 among 77 students from 4,000+ applicants (~2% admit rate) to conduct graduate-level research at UC Santa Barbara\n• Optimized offspring resource distribution models for Gaussian survivorship functions, contributing to existing literature on concave, convex, and mixed-function survivorship curves\n• Applied nonlinear optimization techniques and probabilistic annealing algorithms to enhance the theoretical model\n• Conducted research under the guidance of Dr. Sakal at UC Santa Barbara's Department of Ecology, Evolution, and Marine Biology\n• Delineated resource distribution optimization techniques and biological underpinnings in a paper, poster, and Research Symposium talk",
                    "FRC Software Lead, FTC Mentor\nFIRST\nOn-site\n• Led team in Robot Java Object Oriented Programming workshops & development of an iOS robot scouting app with real-time match analysis, processing 1000+ data entries to foster a competitive advantage during alliance selection\n• Organized logistics using Gantt Charts and Notion Taskboards; encouraged regular check-ins, documentation, and test-driven programming lessons\n• Developed robot autonomous routines with spline trajectory generation, feedback, and odometry\n• Mentored middle school FIRST Tech Challenge teams, helping students foster a passion for engineering\n• Qualified for FIRST Robotics Challenge World Championships 2x, receiving school-wide recognition",
                    "Computational Physics Researcher\nPioneer Academics\nRemote\n• Collaborated with NYU Associate Professor of Physics Dr. Haas to model oscillatory chaos computationally\n• Developed dynamic models with multiple parameters using Python and advanced graphing techniques\n• Explored Monte Carlo simulations, numerical integration applications, and the Ising model to deepen understanding of computational physics methods\n• Documented research findings and model results in an extensive research paper"
                ],
                "education": [
                    "Northwestern University\nBachelor of Science - BS, Computer Science, Mathematics\nGrade: 4.0",
                    "UC Santa Barbara\nGrade: 4.0\nINT 93P: Presentation Techniques in Interdisciplinary University Research\nINT 93R: Introduction to Interdisciplinary University Research Techniques"
                ]
            },
            "convos": [],
            "interests": "Film Studies, Biology, Basket Weaving",
            "img": "https://media.licdn.com/dms/image/v2/D4D03AQEPcYIdcOsMJA/profile-displayphoto-shrink_400_400/profile-displayphoto-shrink_400_400/0/1698282810114?e=1745452800&v=beta&t=UvqvxyAtsd009IzoR-2-MOY-vxWPmhDRTe-ky84gtGo"
        }
    }
    return profiles
