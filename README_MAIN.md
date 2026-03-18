# Smart Waste Sorter

A full-stack robotic application that uses computer vision and machine learning to automatically sort waste items using a Dobot Magician robot arm. The system connects to a DroidCam video stream, performs real-time waste classification, and controls the robot arm to sort items into appropriate bins.
## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Application Workflow](#application-workflow)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Known Limitations](#known-limitations)
- [Contributors](#contributions)

---

## Overview

The Smart Waste Sorter is an automated waste sorting system that combines:

- Computer Vision: Real-time camera feed from DroidCam (phone camera)
- Machine Learning: YOLOv8 classification model for waste type detection
- Robotics: Dobot Magician robotic arm for automated sorting
- Full-Stack Web Application: Next.js frontend with FastAPI backend

### What It Does

1. Captures images from a DroidCam video stream
2. Classifies waste items using a trained YOLOv8 model (12 waste categories)
3. Automatically controls a Dobot Magician robot arm to sort items into appropriate bins
4. Provides real-time feedback through a web interface

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  User Interface                                      │   │
│  │  - Camera preview (MJPEG stream)                     │   │
│  │  - "Capture & Send" button                           │   │
│  │  - Prediction results display                        │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP API
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              BACKEND (FastAPI - Python)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Snapshot    │  │  Camera      │  │  Dobot       │       │
│  │  Service     │  │  Service     │  │  Service     │       │
│  │  (Frame      │  │  (ML         │  │  (Robot      │       │
│  │  Extraction) │  │  Inference)  │  │  Control)    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└────────────┬──────────────────┬──────────────────┬──────────┘
             │                  │                  │
             ▼                  ▼                  ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │  DroidCam    │  │  YOLOv8      │  │  Dobot       │
    │  (Phone      │  │  Model       │  │  Magician    │
    │  Camera)     │  │  (best.pt)   │  │  (USB)       │
    └──────────────┘  └──────────────┘  └──────────────┘
```

### Components

**Frontend (Next.js)**
- React-based web interface
- Real-time MJPEG camera preview
- Image capture and upload
- Results display

**Backend (FastAPI)**
- Snapshot Service: Extracts frames from DroidCam MJPEG stream
- Camera Service: Processes images, runs ML inference
- Dobot Service: Controls robot arm movements and sorting

**External Systems**
- DroidCam: Phone camera streaming via WiFi (MJPEG)
- YOLOv8 Model: Pre-trained classification model
- Dobot Magician: Robotic arm with gripper end effector

---

## Application Workflow

### Detailed Step-by-Step

**Phase 1: Image Capture**
1. User clicks "Capture & Send" button
2. Frontend validates camera is connected and IP address is provided
3. Frontend shows status: "Pausing preview..."
4. Frontend pauses MJPEG preview stream (sets previewPaused = true)
5. 250ms delay to allow DroidCam to free the connection
6. Frontend shows status: "Capturing frame from camera..."
7. Frontend calls /api/snapshot?ip={ip} endpoint
8. Backend connects to DroidCam MJPEG stream (http://{ip}:4747/video)
9. Backend extracts first JPEG frame
10. Backend returns JPEG blob with enhanced error handling:
    - Invalid IP: Clear error message with format example
    - Connection errors: Troubleshooting hints (check camera, network, app)
    - Timeout errors: Suggests camera may be busy
    - Stream errors: Indicates corrupted stream

**Phase 2: Image Processing & ML Inference**
1. Frontend shows status: "Uploading image to server..."
2. Frontend creates FormData with captured image blob
3. Frontend shows status: "Processing image..."
4. POST request to /api/capture endpoint
5. Backend validation steps:
   - Validates file size (default max: 10MB, configurable via MAX_FILE_SIZE env var)
   - Validates file is not empty
   - Returns clear error if file too large or empty
6. Backend decodes image (PIL Image, RGB format) with error handling:
   - Returns user-friendly error if image format is invalid
7. Backend sanitizes filename:
   - Removes directory traversal attempts
   - Removes invalid filesystem characters
   - Limits filename length to 255 characters
8. Image saved to backend/frames/ with sanitized timestamp filename
9. Frontend shows status: "Running ML inference..."
10. YOLOv8 model loaded (cached after first load, lazy loading)
11. Model inference runs on image with enhanced error handling:
    - FileNotFoundError: Clear message if model missing
    - RuntimeError: Indicates model corruption or incompatibility
12. Top-1 prediction and confidence extracted

**Phase 3: Robot Sorting**
1. Prediction class name mapped to bin position (paper, plastic, cardboard, biological, trash)
2. Dobot service auto-connects if needed
3. Robot executes sorting sequence:
   - Move above pickup position
   - Descend to pickup height
   - Close gripper (pick item)
   - Lift item
   - Move above target bin
   - Descend to bin height
   - Open gripper (place item)
   - Lift up
   - Return to home position
4. Robot operation status captured (success or error message)

**Phase 4: Response & Display**
1. Backend builds JSON response with:
   - Success status
   - Saved filename
   - Prediction class
   - Confidence score (0.0-1.0)
   - Robot action status (includes error message if robot failed)
2. Frontend receives response and formats display:
   - Success: "Image processed successfully! Saved as: {filename} | Prediction: {class} ({confidence}%) | Robot: {status}"
   - Error: "Processing failed: {error} | Tip: {troubleshooting_hint}"
3. Error messages include context-specific troubleshooting hints:
   - File size errors: Suggests using smaller image
   - Image format errors: Suggests valid formats
   - Model errors: Suggests checking model configuration
   - Disk errors: Suggests checking space and permissions
4. Preview stream resumes automatically (previewPaused = false)

---

## Tech Stack

### Frontend
- Next.js 16.3 (React framework)
- TypeScript
- Tailwind CSS
- shadcn/ui components

### Backend
- FastAPI (Python web framework)
- Uvicorn (ASGI server)
- Pillow (Image processing)
- Ultralytics YOLOv8 (ML model)
- httpx (Async HTTP client)

### ML/AI
- YOLOv8 classification model
- PyTorch (via Ultralytics)
- 12 waste categories: battery, biological, brown-glass, cardboard, clothes, green-glass, metal, paper, plastic, shoes, trash, white-glass

### Robotics
- Dobot Magician robotic arm
- Dobot SDK (Windows DLL + Python wrapper)
- USB/Serial connection

### Camera
- DroidCam (phone camera streaming)
- MJPEG stream over WiFi

---

## Getting Started

### Prerequisites

- **Python 3.12** — This project targets 3.12. Other versions are not recommended (e.g. 3.14 has httpx/httpcore issues). [python.org](https://www.python.org/downloads/) — 64-bit on Windows.
- **Node.js 18+** — [nodejs.org](https://nodejs.org/) or `winget install OpenJS.NodeJS.LTS` / `brew install node`.

Robot + camera: Dobot Magician (USB), DroidCam, and **Windows**. On Mac/Linux you can run the app and ML; robot control is Windows-only.

### Installation

#### 1. Project folder that contains `backend/`, `frontend/`, and `requirements.txt`...

```bash
cd <project-folder>
```

#### 2. Backend (venv + deps)

**Windows:**

```bash
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Mac / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Dobot SDK (Windows only)

**Mac/Linux users:** Robot control requires Windows in this project.

The Dobot Magician SDK files are included in this repository at `backend/dobot_magician/`. The original SDK from Dobot has been modified to work correctly with this project.

**SDK Modifications:**

The original SDK's load() function used relative paths that failed when the script was run from different directories. The included version has been modified with the following changes:

**Original SDK issues:**
- Used "./DobotDll.dll" (relative path), which only worked when running from the SDK directory
- Used CDLL with RTLD_GLOBAL flag, which is Linux/Mac-specific and caused issues on Windows
- Could not load the DLL from any working directory

**Modifications made:**

1. Added import at the top:
   ```python
   from pathlib import Path
   ```

2. Modified the load() function to use absolute paths:
   ```python
   def load():
       dll_path = str(Path(__file__).resolve().parent / "DobotDll.dll")
       print("Loading Dobot DLL from:", dll_path)
       if platform.system() == "Windows":
           print("您用的dll是64位，为了顺利运行，请保证您的python环境也是64位")
           print("python环境是：",platform.architecture())
           from ctypes import WinDLL
           return WinDLL(dll_path)
       elif platform.system() == "Darwin":
           dylib_path = str(Path(__file__).resolve().parent / "libDobotDll.dylib")
           return CDLL(dylib_path)
       elif platform.system() == "Linux":
           return CDLL("libDobotDll.so")
   ```

**What these changes accomplish:**
- Absolute path resolution: Uses Path(__file__).resolve().parent to find the DLL relative to the script's location, regardless of working directory
- Windows-specific loading: Uses WinDLL instead of CDLL on Windows (more appropriate for Windows DLLs)
- Removed RTLD_GLOBAL: This flag is Linux/Mac-specific and not needed on Windows
- macOS path fix: Also uses absolute path for macOS dylib

The SDK files in `backend/dobot_magician/` are ready to use and do not require any additional setup.

#### 4. Frontend

```bash
cd frontend
npm install
```

#### 5. ML Model

The trained YOLOv8 model is included in the repository at `backend/models/best.pt`. The model is ready to use and does not require additional setup.

### Running the Application

**Terminal 1 — Backend**

**Windows:**

```bash
cd <project-folder>\backend
python main.py
```

**Mac / Linux:**

```bash
cd <project-folder>/backend
python3 main.py
```

**Optional env vars:** `YOLO_MODEL_PATH`, `YOLO_DEVICE` (cpu/cuda), `MAX_FILE_SIZE`, `FASTAPI_URL`. Defaults work.

→ `http://localhost:8000`

**Terminal 2 — Frontend**

```bash
cd <project-folder>\frontend
npm run dev
```

**Mac / Linux:**

```bash
cd <project-folder>/frontend
npm run dev
```

→ `http://localhost:3000`

#### Connect DroidCam

1. Start DroidCam app on the phone
2. Note the IP address (e.g., `192.168.0.105`)
3. Ensure phone and computer are on the same WiFi network
4. In the web interface, enter the IP and click "Connect Camera"

#### Test the System

1. Open `http://localhost:3000`
2. Enter DroidCam IP and connect
3. Place a waste item in the pickup area
4. Click "Capture & Send"
5. Watch the robot sort the item

---

## Project Structure

```
<project-directory>/
├── frontend/                       # Next.js frontend application
│   ├── app/                       # Next.js App Router
│   │   ├── api/                   # API routes (proxies to FastAPI)
│   │   │   ├── capture/route.ts  # Image upload proxy
│   │   │   └── snapshot/route.ts # Frame extraction proxy
│   │   ├── page.tsx               # Main page
│   │   └── layout.tsx
│   │
│   ├── components/                 # React components
│   │   ├── sorter/
│   │   │   └── CameraFeed.tsx     # MJPEG preview component
│   │   └── ui/                    # shadcn/ui components
│   │       └── demo.tsx           # Main control panel
│   │
│   ├── lib/
│   │   └── sorter/
│   │       └── capture.ts         # Frame capture utility
│   │
│   ├── public/                     # Static assets
│   ├── package.json               # Frontend dependencies
│   ├── next.config.ts             # Next.js configuration
│   └── tsconfig.json              # TypeScript configuration
│
├── requirements.txt                 # Python dependencies (backend + training)
│
├── backend/                        # FastAPI backend
│   ├── main.py                    # FastAPI app entry point
│   │
│   ├── services/
│   │   ├── camera_service.py      # ML inference & image processing
│   │   ├── snapshot_service.py    # DroidCam frame extraction
│   │   ├── dobot_service.py       # Robot control
│   │
│   ├── models/
│   │   ├── best.onnx              # YOLOv8 model .onnx
│   │   └── best.pt                # YOLOv8 model .pt
│   │
│   ├── utils/
│   │   └── image_utils.py         # Image conversion utilities
│   │
│   ├── frames/                    # Saved captured frames
│   │
│   ├── dobot_magician/            # Dobot SDK files (modified version included)
│   │   ├── DobotDll.dll
│   │   ├── DobotDllType.py        # Modified to use absolute paths
│   │   ├── DobotControl.py
│   │   └── ...                    # remaining SDK files
│
├── docs/                          # Additional documentation
├── training/                      # ML model training scripts
│   └── inspect_model.py          # Model inspection utility
└── README.md                      # This file
```

---

## Known Limitations

### Current Limitations


1. **Automatic sorting without manual confirmation**  
   There is no option for the user to approve or decline the predicted class before the robot moves.

2. **Limited error recovery**  
   If the robot fails mid-sequence, there is no automatic retry logic or structured recovery workflow.

3. **Single camera / stream limitation**  
   DroidCam Free only allows one connection to stream at a time, so the preview must pause when capturing a frame.

4. **Windows-only robot integration**  
   The Dobot SDK only supports Windows, so the full system (with robot control) is tied to Windows.

5. **Manual coordinate calibration required**  
   Bin and pickup positions must be manually calibrated for each physical setup using the calibration guide.

### Future Improvements

Planned or potential improvements:

- **Confirmation mode**  
  Allow the user to accept/decline the prediction before robot moves.

- **Better error recovery and logging**  
  Add structured retry logic, clearer robot error codes, and persistent logs for troubleshooting.

- **Better camera hardware**  
  Support additional camera sources or multiple streams beyond a single DroidCam connection.

- **Cross-platform robot abstraction**  
  Introduce an abstraction layer so that other robot arms or cross-platform SDKs can be integrated more easily in the future.

---

## Additional Documentation

- Coordinate Calibration: See `docs/COORDINATE_ADJUSTMENT_GUIDE.md` for robot setup instructions
- Dataset information: See `docs/DATASET_INFO.md`
- Dobot SDK: See https://www.dobot-robots.com/service/download-center for SDK documentation and files


## Contributors  

The given work is contributed and supported by **[Atilla](https://github.com/Atilla888) 
and 

This project is part of a university course (Applied Robotics).


