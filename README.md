# Automatic Football Analysis

An end-to-end computer vision pipeline that analyzes football (soccer) match footage to produce tracking video, statistics, and AI-powered tactical reports.

---

## Overview

The system processes a raw match video and outputs:
- An **annotated video** with player tracking, team colors, IDs, and real-time possession overlay
- A **statistics file** with passing, shooting, speed, distance, and possession data
- An **AI analysis file** with tactical insights powered by Claude AI
- A **PDF report** combining charts, player tables, and the AI analysis

---

## Features

- Player, goalkeeper, referee, and ball detection using a fine-tuned **YOLOv11x** model
- Multi-object tracking with **ByteTrack**
- Camera motion compensation via **Lucas-Kanade optical flow**
- Perspective transformation to a top-down pitch view for accurate spatial measurements
- Automatic team assignment via **K-means color clustering**
- Ball possession tracking per player and per team
- Pass detection, turnover detection, and pass accuracy calculation
- Shot detection with on-target / off-target classification
- Formation detection (e.g. 4-3-3, 5-2-3) per team
- Per-player speed (km/h) and distance (m) metrics
- AI-generated match overview and tactical recommendations via **Claude API**
- Professional **PDF report** with charts and player performance tables

---

## Project Structure

```
├── main.py                          # Entry point
├── models/
│   └── best11x.pt                   # YOLOv11x weights (not included in repo)
├── VideoData/                       # Input videos
├── output/                          # Generated outputs
├── stubs/                           # Cached tracks for faster re-runs
├── track/
│   └── tracking.py                  # Detection & tracking
├── team_assigner/
│   └── team_assigner.py             # Team color clustering
├── player_ball_assigner/
│   └── player_ball_assigner.py      # Ball possession assignment
├── camera_movement/
│   └── camera_movement.py           # Camera motion estimation
├── view_transformer/
│   └── view_transformer.py          # Perspective transform to top-down view
├── development_and_analysis/
│   ├── speed_and_distance_detector.py
│   ├── pass_detector.py
│   ├── shot_detector.py
│   ├── formation_detector.py
│   ├── llm_analyst.py               # Claude API integration
│   └── pdf_reporter.py              # PDF report generation
└── utils/
    ├── video_utils.py
    └── bbox_utils.py
```

---

## Requirements

- Python 3.10+
- A GPU is strongly recommended for inference

Install dependencies:

```bash
pip install ultralytics supervision opencv-python numpy pandas scikit-learn anthropic reportlab python-dotenv
```

---

## Setup

1. **Clone the repository**

```bash
git clone https://github.com/Mocheta/Automatic-Football-Analysis.git
cd Automatic-Football-Analysis
```

2. **Add the model weights**

Download or place your trained `best11x.pt` file in the `models/` directory.

3. **Set your Anthropic API key**

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your-api-key-here
```

---

## Usage

```bash
python main.py [video_path]
```

- `video_path` is optional. Defaults to `VideoData/test (3).mp4`.

**Example:**

```bash
python main.py VideoData/match.mp4
```

---

## Outputs

All outputs are saved to the `output/` directory, named after the input video file.

| File | Description |
|---|---|
| `output_{name}_video.mp4` | Annotated video with tracking overlays |
| `Stats_{name}.txt` | Full match statistics |
| `Analysis_{name}.txt` | AI-generated tactical analysis |
| `Report_{name}.pdf` | PDF report with charts and player tables |

---

## Notes

- Input video is assumed to be broadcast format (1920×1080) at 24 fps.
- Tracking results are cached in `stubs/` as `.pkl` files — delete them to force re-detection.
- The pitch dimensions used for the perspective transform are 68m × 23.32m (standard half-pitch view).

---

## Models & APIs

| Component | Details |
|---|---|
| Object detection | YOLOv11x fine-tuned on football footage (4 classes: ball, player, goalkeeper, referee) |
| Tracking | ByteTrack via the `supervision` library |
| Team assignment | K-means clustering on player crop colors |
| AI analysis | Anthropic Claude (`claude-opus-4-7`) with extended thinking |

---

## License

This project was developed as a university thesis. Feel free to use it for educational and research purposes.
