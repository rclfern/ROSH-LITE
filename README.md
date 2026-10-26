# Traffic Data Analytics Prototype

A local Streamlit dashboard redesigned to follow a dark-navy-sidebar / bright-workspace traffic operations UI concept.

## What's implemented

- Responsive navy-and-off-white visual design with locally available Windows fonts, no web font downloads.
- Navigable Overview, Video sources, Corridors, Incidents, Reports, Local agent, Settings.
- Interactive selector for three traffic scenarios.
- Local MP4 playback when files exist.
- A **schematic, illustrative** road-network view and sample traffic metrics, events, and plots.
- Demo incident acknowledgment, local CSV export, and optional Qwen text chat through Ollama.

**Important:** Sample statistics, incidents, roadway colors, and network map are fabricated for UI demonstration. This app does not connect to live traffic feeds or perform YOLO/video analysis yet. The map is a schematic, not a geographic map. Local Ollama chat receives only sample scenario text, not video frames.

## Install on Windows

Open VS Code in your existing project folder. Copy `app.py`, `requirements.txt`, and `.streamlit/config.toml` into that folder. **Keep your existing `.venv` and `videos` folders.**

In the VS Code PowerShell terminal:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Browse to `http://localhost:8501` on the same laptop.

## Add video files

Create the `videos` folder beside `app.py`, then add:

- `normal_traffic.mp4`
- `rainy_traffic.mp4`
- `vehicle_collision.mp4`

Use short MP4 clips that you are permitted to use. Browser-friendly H.264 MP4 is recommended.

## Optional Qwen chat

Install Ollama separately and obtain a local Qwen model, for example:

```powershell
ollama pull qwen3-vl:2b
```

The Local agent page contacts `http://127.0.0.1:11434`. You can change the model name in Settings. Qwen Code CLI alone does not provide this API. Local chat does not yet analyze footage.

## Save to existing GitHub repository

With files saved locally, from your project root:

```powershell
git status
git add app.py requirements.txt .streamlit/config.toml README.md .gitignore
git commit -m "Redesign traffic dashboard to Figma-style layout"
git push
```

Check your employer's policies before uploading work project files to GitHub. Sample video files are gitignored by default.
