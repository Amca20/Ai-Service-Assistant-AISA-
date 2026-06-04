# 🤖 AI Service Assistant (AISA) - Smart Biometric Kiosk

An intelligent, multi-modal visitor management system engineered to automate conventional front-desk registration processes within academic institutions and administrative environments[cite: 4]. Developed under the Faculty of Artificial Intelligence and Cyber Security (FAIX), UTeM, AISA replaces traditional paper-based logbooks with a seamless, contactless, and voice-guided experience driven by computer vision and generative AI[cite: 4].

---

## 📌 Project Overview & Objectives

Traditional visitor logging suffers from administrative bottlenecks, legible handwriting issues, and lack of real-time tracking[cite: 4]. AISA addresses these security gaps and operational inefficiencies by merging automated facial verification with natural language intent extraction to provide zero-touch data entry[cite: 4].

### 🎯 Core Objectives:
* **Voice-Based Registration:** Build an intuitive speech-to-text processing engine to log visit details hands-free[cite: 4].
* **Biometric Face Tracking:** Deploy real-time face detection and recognition to securely audit and log visitor arrivals and departures[cite: 4].
* **Centralized Administration:** Provide a comprehensive administrative web dashboard for real-time facility monitoring, visual trend analytics, and logs management[cite: 4].
* **Instant Communication:** Automate staff notifications by immediately dispatching arrival details and visitor photos to the requested hosts[cite: 4].

---

## 🛠️ System Architecture & Workflow

AISA is built on a robust three-tier client-server architecture designed for high throughput, low latency, and fluid modular interaction[cite: 4].

```text
  [Visitor Kiosk Terminal] ──► [Flask Backend Orchestrator] ──► [Relational Database]
             │                            │                            │
             ▼                            ▼                            ▼
   (Web Speech API)              (Google Gemini API)           (Facial Encodings)

```

### 🔄 End-to-End Processing Steps:

1. **Visitor Detection:** The kiosk high-definition camera automatically detects an approaching visitor.


2. **Voice Capture:** The kiosk triggers voice recording upon a keyword command ("Hello") or manual start, capturing unstructured speech inputs.


3. **Speech-to-Text Conversion:** Spoken words are transcribed in real-time on the client side using the browser's Web Speech API.


4. **Entity Extraction (NLP):** The backend passes the transcript to the Google Gemini AI API, parsing the sentence into structured JSON fields (`name`, `matric_number`, `host_name`, `reason`).


5. **Facial Encoding:** The system captures a snapshot, computes a 128-dimensional biometric face vector using deep metric learning, and searches for identity matches.


6. **Room Occupancy Check:** A secondary camera monitors the lecturer's office to dynamically analyze real-time availability via face counting algorithms.


7. **Database Logging & Notification:** The structured log is securely committed, and a non-blocking threaded email notification is immediately dispatched to the host.



---

## 🧠 Technical Stack & Dependencies

| Component | Technology / Library | Purpose & Justification |
| --- | --- | --- |
| **Web Server Backend** | Python / Flask Framework | Lightweight, modular routing hub perfect for multi-modal integrations.

 |
| **Computer Vision Core** | OpenCV & `face_recognition` | Performs face detection and 128-D vector embedding calculation (dlib-based).

 |
| **Natural Language Parsing** | Google Gemini API (`gemini-flash-latest`) | High-speed, accurate structured entity extraction through structured prompting.

 |
| **Client-Side Senses** | HTML5, CSS3, JavaScript (Web Speech) | Provides interactive web kiosk rendering and offline speech transcription.

 |
| **Database & Mail** | SQLite, SQLAlchemy ORM, Flask-Mail | Secure storage for metrics and threaded SMTP delivery models.

 |

---

## 📊 Performance Analytics & Testing Results

AISA underwent rigorous unit, integration, and functional testing under indoor conditions, achieving high operational reliability:

* **Face Detection Accuracy:** Exceeds **98%** under optimal lighting conditions.


* **Registration Speed:** Full workflow completes within **2.5 minutes**, reflecting an **80% processing time reduction** compared to manual logging.


* **Administrative Load:** Reduces active front-desk management utilization by **67%**, allowing streamlined data exporting directly to CSV format.



---

## 👥 Project Contributors (Group 29)

This intelligent system was engineered as a final Workshop 2 project for the SEMESTER 1 2025/2026 session:

* **Muhammad Amsyar Bin Hazalan** (B032310492)


* **Danish Bin Mohd Rafid** (B032310427)


* **Sakthivell A/L Kannan** (B032410309)


* **Boon Shoung A/L Kok Hoe** (B032410931)



### 🎓 Project Supervisor:

* **Professor Madya Ts. Dr. Siti Azirah Binti Asmai**


---

## 🗂️ Project Repository Materials

* `app.py` — Main Flask orchestration script coordinating API endpoints, video streams, and AI pipelines.


* `templates/` — UI templates for the interactive `index.html` kiosk and `admin.html` dashboard panels.


* `instance/database.db` — Active relational database instance containing log definitions and configurations.


* `static/captures/` — Directory mapping timestamped visitor image assets for email notification logs.



```

