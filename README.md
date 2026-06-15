# Alass GUI

## English

**Alass GUI** is a small graphical wrapper for the original open-source **alass** subtitle synchronizer:

🔗 https://github.com/kaegi/alass

**What alass does:** alass compares an incorrect subtitle with a reference video or a correctly synced subtitle, then calculates the timing shifts needed to align it. It can fix simple delays, FPS drift, and release differences with cuts or added scenes.

### ✅ Features

- **Single subtitle sync**
- **Whole-folder batch sync**
- **Optional subfolder scanning**
- **Checkbox selection** for batch items
- **Open folder** button
- **Progress bars** and a short final report
- **Encoding fallback** for non-UTF-8 subtitles
- **Update check** for original `kaegi/alass` releases
- **English UI by default**, Croatian available in the language selector

### 📦 Portable layout

```text
Alass/
  alass_gui.py
  run_alass_gui.sh
  run_alass_gui.bat
  bin/alass        # Linux binary, if available
  bin/alass.exe    # Windows binary, if available
```

### ▶️ Run on Linux

```bash
cd /path/to/Alass
./run_alass_gui.sh
```

or:

```bash
python3 alass_gui.py
```

### ▶️ Run on Windows

Double-click:

```text
run_alass_gui.bat
```

or:

```bat
python alass_gui.py
```

### 🔧 Requirements

- **Python 3**
- **alass binary** in `bin/` or available in PATH
- **ffmpeg/ffprobe** in `bin/` or PATH when using video references

### 💾 Save modes

- Keep the original subtitle and create `name.synced.ext`
- Move the old subtitle to `original prijevod` and name the new subtitle like the video

### 🔄 Updates

Use **Check updates** in the top bar. If a matching release asset exists for your OS, the GUI downloads it into `bin/` and keeps a `.bak` backup of the old binary.


## Hrvatski

**Alass GUI** je mali grafički omotač za originalni open-source **alass** alat za sinkronizaciju titlova:

🔗 https://github.com/kaegi/alass

**Što alass radi:** alass uspoređuje neispravan titl s referentnim videom ili točno sinkroniziranim titlom, zatim izračuna vremenske pomake potrebne za poravnanje. Može popraviti običan delay, FPS drift i različite releaseove s izrezanim ili dodanim scenama.

### ✅ Mogućnosti

- **Sinkronizacija pojedinačnog titla**
- **Batch sinkronizacija cijelog foldera**
- **Opcionalno skeniranje podfoldera**
- **Checkbox izbor** stavki za batch
- Gumb **Otvori folder**
- **Progress barovi** i kratak završni izvještaj
- **Encoding fallback** za titlove koji nisu UTF-8
- **Provjera updatea** originalnog `kaegi/alass` releasea
- Sučelje se pokreće na **engleskom**, a hrvatski je dostupan kroz izbor jezika

### 📦 Portable struktura

```text
Alass/
  alass_gui.py
  run_alass_gui.sh
  run_alass_gui.bat
  bin/alass        # Linux binary, ako postoji
  bin/alass.exe    # Windows binary, ako postoji
```

### ▶️ Pokretanje na Linuxu

```bash
cd /putanja/do/Alass
./run_alass_gui.sh
```

ili:

```bash
python3 alass_gui.py
```

### ▶️ Pokretanje na Windowsima

Dvoklik na:

```text
run_alass_gui.bat
```

ili:

```bat
python alass_gui.py
```

### 🔧 Potrebno

- **Python 3**
- **alass binary** u `bin/` folderu ili dostupan u PATH-u
- **ffmpeg/ffprobe** u `bin/` ili PATH-u za video reference

### 💾 Načini spremanja

- Ostavi originalni titl i napravi `ime.synced.ext`
- Premjesti stari titl u `original prijevod`, a novi nazovi isto kao video

### 🔄 Update

Koristi **Check updates / Provjeri update** u gornjoj traci. Ako postoji odgovarajući release asset za tvoj OS, GUI ga skida u `bin/` i čuva `.bak` backup starog binaryja.
