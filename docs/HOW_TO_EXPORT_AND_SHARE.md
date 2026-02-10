# How to Export & Share ARKE: Guardians of Earth

This guide walks you through exporting the game so friends can play it.

---

## Option A: Web Export + itch.io (RECOMMENDED - Easiest for friends)

Friends just click a link and play in their browser. No downloads needed.

### Step 1: Install Export Templates in Godot

1. Open the project in **Godot 4.2+**
2. Go to **Editor > Manage Export Templates**
3. Click **Download and Install** (this downloads ~600 MB once)
4. Wait for it to finish

### Step 2: Export for Web

1. Go to **Project > Export** (or Ctrl+Shift+E)
2. The **"Web (HTML5)"** preset should already be listed
3. Click **Export Project**
4. Choose or create the folder `builds/web/`
5. Save as `index.html`
6. Click **Export** (not "Export with Debug")

This creates these files in `builds/web/`:
```
index.html          (main page)
index.js            (engine loader)
index.wasm          (game engine)
index.pck           (game data)
index.icon.png      (favicon)
index.apple-touch-icon.png
```

### Step 3: Upload to itch.io (Free)

1. Go to https://itch.io and create a free account
2. Click **Dashboard > Create new project**
3. Fill in:
   - **Title:** ARKE: Guardians of Earth
   - **Kind of project:** HTML
   - **Classification:** Games
   - **Upload:** Zip the entire `builds/web/` folder and upload it
   - Check **"This file will be played in the browser"**
   - **Embed options:** Set to 960x540 (or 1920x1080 for full size)
   - **Frame option:** Click to launch (recommended)
4. Add a description, screenshots, tags (educational, science, pixel-art, 2d)
5. Set **Visibility:** Public (or Draft/Restricted for testing first)
6. Click **Save & view page**

Now share the itch.io link with your friends!

### Important Web Export Notes

- **SharedArrayBuffer:** Some browsers require HTTPS + specific headers. itch.io handles this automatically.
- **Audio:** Browser autoplay policies may require the user to click before audio plays. The game already handles this (click to start on title screen).
- **Performance:** The web version runs slightly slower than desktop. Our game is lightweight so this shouldn't be an issue.

---

## Option B: Windows Desktop Export (.exe)

For friends on Windows who prefer a download.

### Export Steps

1. In Godot, go to **Project > Export**
2. Select **"Windows Desktop"**
3. Click **Export Project**
4. Save to `builds/windows/ARKE_Guardians_of_Earth.exe`
5. Make sure **"Embed PCK"** is checked (single file is easier to share)

### Share

- Zip the `builds/windows/` folder
- Send the zip via Google Drive, Dropbox, OneDrive, etc.
- Friends unzip and double-click the .exe

### Note on Windows SmartScreen

Windows may show "Windows protected your PC" warning since the game isn't signed. Friends need to click **"More info" > "Run anyway"**. This is normal for indie games.

---

## Option C: Linux Export

1. In Godot, go to **Project > Export**
2. Select **"Linux"**
3. Export to `builds/linux/ARKE_Guardians_of_Earth.x86_64`
4. Zip and share

Friends run: `chmod +x ARKE_Guardians_of_Earth.x86_64 && ./ARKE_Guardians_of_Earth.x86_64`

---

## Option D: macOS Export

1. In Godot, go to **Project > Export**
2. Select **"macOS"**
3. Export to `builds/macos/ARKE_Guardians_of_Earth.zip`
4. Share the zip

Friends may need to right-click > Open to bypass Gatekeeper on unsigned apps.

---

## Option E: Quick Test Without Exporting

If friends have Godot installed, they can just:

1. Clone the repository: `git clone <repo-url>`
2. Open Godot, import the `game/project.godot` file
3. Press F5 to play

---

## Command-Line Export (Advanced)

You can export from command line without opening the Godot editor:

```bash
# Web export
godot --headless --export-release "Web (HTML5)" builds/web/index.html

# Windows export
godot --headless --export-release "Windows Desktop" builds/windows/ARKE_Guardians_of_Earth.exe

# Linux export
godot --headless --export-release "Linux" builds/linux/ARKE_Guardians_of_Earth.x86_64

# macOS export
godot --headless --export-release "macOS" builds/macos/ARKE_Guardians_of_Earth.zip
```

**Note:** You need export templates installed first. Install them via:
```bash
godot --headless --export-templates-download
```

---

## Recommended Sharing Platforms

| Platform | Best For | Cost |
|----------|----------|------|
| **itch.io** | Web games, indie games | Free |
| **Google Drive** | Direct file sharing | Free (15 GB) |
| **GitHub Releases** | Developer-friendly distribution | Free |
| **Dropbox** | Simple file sharing | Free (2 GB) |

---

## Quick Checklist

- [ ] Install Godot 4.2+ export templates
- [ ] Export for Web (HTML5)
- [ ] Create itch.io account
- [ ] Upload web build to itch.io
- [ ] Set embed size to 960x540
- [ ] Test the itch.io page in browser
- [ ] Share the link with friends!
- [ ] (Optional) Export Windows/Mac/Linux builds too
