# 🖐️ HandPoint

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV" />
  <img src="https://img.shields.io/badge/MediaPipe-Hand%20Tracking-00979D?style=for-the-badge&logo=google&logoColor=white" alt="MediaPipe" />
  <img src="https://img.shields.io/badge/Status-Active%20Development-success?style=for-the-badge" alt="Status" />
</p>

> **A real-time computer vision virtual mouse built with Python, OpenCV, MediaPipe, and PyAutoGUI.**

**HandPoint** transforms your standard webcam into a touchless controller. By tracking hand landmarks in real-time, it seamlessly maps physical hand gestures to operating system mouse events—allowing you to navigate, click, and scroll without touching a physical device.
 
---

## 🌟 Key Highlights

* 🖱️ **Smooth Cursor Tracking:** Uses an exponential smoothing algorithm to eliminate jitter and track your index finger fluidly.
* 🎯 **Dynamic Palm Calibration:** Automatically measures your palm size during initial startup to normalize gesture distances regardless of camera depth.
* 🔒 **Hysteresis & Intent Hold:** State-machine architecture prevents accidental clicks and double-triggering.
* 📜 **Natural Scroll Mode:** Simply open your palm and move vertically to scroll through pages.
* 📊 **Live Diagnostic HUD:** On-screen display showing active modes, real-time FPS, gesture states, and tracking bounds.

---

## 🔄 System Architecture

HandPoint processes incoming frame buffers sequentially through a multi-stage pipeline:

```text
  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐
  │  Webcam Feed │ ──> │ OpenCV Frame │ ──> │ MediaPipe Processing │
  └──────────────┘     └──────────────┘     └──────────────────────┘
                                                       │
                                                       ▼
  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐
  │ Mouse Event  │ <── │ PyAutoGUI    │ <── │ Hand Landmarks (21x) │
  │ Execution    │     │ Automation   │     └──────────────────────┘
  └──────────────┘     └──────────────┘                │
                                                       ▼
                                            ┌──────────────────────┐
                                            │ Gesture State-Engine │
                                            │ (Pinch, Open, Move)  │
                                            └──────────────────────┘

```
 
## 🎮 Gesture Interaction Guide

| Action | Hand Gesture | Mechanism |
| --- | --- | --- |
| **Move Cursor** | Point Index Finger | Maps index tip coordinate to screen bounds with exponential decay smoothing. |
| **Left Click** | Pinch Thumb + Index Finger | Normalized distance drops below threshold while middle finger is curled. |
| **Right Click** | Pinch Thumb + Middle Finger | Normalized distance drops below threshold while index finger is curled. |
| **Scroll Mode** | Open Palm (All 5 Fingers Up) | Tracks vertical palm movement to send scroll commands. |
| **Exit** | Press `ESC` | Halts execution loops and safely releases system video handles. |

# ⚡ Quick Start
``` 
1. Prerequisites
Ensure you have Python 3.8+ installed on your system.

2. Installation
Clone the repository and install the dependencies:
``` 

## Clone the repository
```
git clone [https://github.com/KrisnaWirahadikusuma/HandPoint.git](https://github.com/KrisnaWirahadikusuma/HandPoint.git)
```
## Enter project folder
```
cd HandPoint
```
## Create virtual environment (Optional but recommended)
```
python -m venv .venv
```
## Activate virtual environment
### Windows:
```
.venv\Scripts\activate
```
### macOS/Linux:
```
source .venv/bin/activate
```

## Install requirements
```
pip install -r requirements.txt
```
# Run HandPoint
Execute the main controller script:

Bash
```
 python HandPoint.py
```
Note on Startup Calibration: Upon launching, hold your hand steady in front of the camera for roughly 20 frames while the system calculates your baseline palm size calibration.

## ⚙️ Configuration & Parameter Tuning
You can fine-tune tracking performance and gesture sensitivity by editing the top parameters in HandPoint.py:

## ⚙️ Configuration & Parameter Tuning

```python
# --- Camera System ---
CAM_INDEX = 0             # Camera device index (0 for built-in, 1+ for external)
 
# --- Motion Control ---
smoothing_factor = 3.0    # Higher = Smoother/Slower; Lower = Faster/Snappier
frame_reduction_x = 60    # Horizontal bounding margins for full-screen reach
frame_reduction_y = 60    # Vertical bounding margins for full-screen reach

# --- Click Sensitivity (State Machine) ---
LEFT_CLOSE_THR = 0.28     # Distance threshold to start Left Click
LEFT_OPEN_THR = 0.42      # Distance threshold to release Left Click
INTENT_HOLD_TIME = 0.12   # Duration (seconds) gesture must be held to register
CLICK_COOLDOWN = 0.35     # Delay (seconds) before next click can trigger
```

## 📂 Project Structure

```text
HandPoint/
├── HandPoint.py
├── requirements.txt
├── .gitignore
└── README.md
```
🧯 Troubleshooting
📄 License & Author
Developed with ❤️ by Krisna Wirahadikusuma

GitHub: @KrisnaWirahadikusuma
