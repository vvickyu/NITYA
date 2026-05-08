# 🎬 Nitya VFX Studio — v4.0

A full-featured VFX shot-tracking web app built with Streamlit. Runs on **GitHub Codespaces** with zero setup.

## ✨ What's new in v4.0

| Feature | Details |
|---|---|
| **Shot Detail Page** | 3-panel view — details, pipeline workflow, version history |
| **Artist Assignment Dropdown** | Assign artists from your roster directly on any shot |
| **Version Management** | Submit versions (v01, v02…), log delivery notes, track client feedback |
| **Pipeline Workflow** | Per-shot dept status cards for Roto, Paint, Tracking, CG, Comp |
| **Shot History** | Full audit trail of changes with date + artist |
| **Versions Table** | SQLite `versions` table with feedback, dates, batch tracking |

## 🚀 Running on GitHub Codespaces

Open the repo in GitHub Codespaces — the `.devcontainer/devcontainer.json` installs all dependencies and launches the app automatically on port 8501.

## 🏃 Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📁 File structure

```
nitya-vfx-studio/
├── app.py            ← Main Streamlit app (all pages + router)
├── database.py       ← SQLite layer (projects, artists, shots, versions, history)
├── excel_io.py       ← Excel export / import (openpyxl)
├── requirements.txt
├── .devcontainer/
│   └── devcontainer.json
└── nitya_vfx.db      ← Created automatically on first run
```

## 🔧 Tech stack

- **Streamlit** — UI framework (Codespaces-compatible)
- **SQLite** — local database (WAL mode, auto-migrating)
- **openpyxl / pandas** — Excel import & export
