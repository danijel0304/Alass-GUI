#!/usr/bin/env python3
"""Small Tkinter GUI wrapper for the alass subtitle synchronizer."""

from __future__ import annotations

import os
import platform
import queue
import re
import shlex
import shutil
import stat
import subprocess
import tarfile
import tempfile
import threading
import tkinter as tk
import urllib.error
import urllib.request
import zipfile
import json
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


APP_TITLE = "Alass GUI"
APP_DIR = Path(__file__).resolve().parent
ALASS_RELEASE_API = "https://api.github.com/repos/kaegi/alass/releases/latest"
ALASS_RELEASES_URL = "https://github.com/kaegi/alass/releases"
SUBTITLE_EXTENSIONS = (".srt", ".ssa", ".ass", ".idx", ".sub")
VIDEO_EXTENSIONS = (".mp4", ".mkv", ".avi", ".mov", ".wmv", ".m4v", ".webm", ".ts", ".mpg", ".mpeg")
COMMON_ENCODINGS = [
    "auto",
    "utf-8",
    "windows-1250",
    "windows-1252",
    "iso-8859-1",
    "iso-8859-2",
    "shift_jis",
]
ENCODING_FALLBACKS = ["windows-1250", "windows-1252", "iso-8859-2", "iso-8859-1", "utf-8"]
PERCENT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")
PROGRESS_RECORD_RE = re.compile(r"^\s*\d+\s*/\s*\d+\s+\[")
SRT_TIMESPAN_RE = re.compile(
    r"^\s*\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}\s+-->\s+\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}(?:\s+.*)?$"
)
LOOSE_SRT_TIMESPAN_RE = re.compile(
    r"^\s*(\d{1,2}:\d{2}:\d{2})[,.](\d{1,3})\s*(?:-->|->|=>|-|–|—)\s*"
    r"(\d{1,2}:\d{2}:\d{2})[,.](\d{1,3})(.*)$"
)
TEXT = {
    "en": {
        "tab_single": "Sync",
        "tab_folder": "Folder",
        "tab_help": "Help",
        "language": "Language",
        "check_updates": "Check updates",
        "files": "Files",
        "alass_program": "Alass program",
        "video_file": "Video",
        "correct_subtitle": "Correct subtitle (optional)",
        "incorrect_subtitle": "Subtitle to fix",
        "output_subtitle": "Output subtitle",
        "choose": "Choose",
        "options": "Options",
        "split_penalty": "Split penalty",
        "interval": "Interval (ms)",
        "speed_opt": "Speed opt.",
        "fps_ref": "FPS reference",
        "fps_sub": "FPS subtitle",
        "audio_index": "Audio index",
        "encoding_ref": "Encoding ref.",
        "encoding_sub": "Encoding subtitle",
        "stat_tag": "Stat. tag",
        "no_split": "No splits (--no-split)",
        "allow_negative": "Allow negative timestamps",
        "disable_fps": "Disable FPS guessing",
        "repair_srt": "Repair simple SRT errors",
        "command": "Command",
        "save_mode": "Subtitle saving",
        "suffix_mode": "Keep original and add .synced",
        "backup_mode": "Move original to 'original prijevod', new subtitle matches video",
        "run_sync": "Start sync",
        "stop": "Stop",
        "progress": "Progress",
        "log": "Log",
        "folder": "Folder",
        "movies_folder": "Movies folder",
        "load_folder": "Load folder",
        "rescan": "Rescan",
        "include_subfolders": "Include subfolders",
        "open_folder": "Open folder",
        "selection": "Selection",
        "all_pairs": "Sync all found pairs",
        "selected_pairs": "Sync only checked items",
        "check_all": "Check all",
        "uncheck_all": "Uncheck all",
        "clear_all": "Clear all",
        "ask_on_start": "Ask on start",
        "movies_subtitles": "Movies and subtitles",
        "use": "Use",
        "movie": "Movie",
        "subtitle": "Subtitle",
        "output": "Output",
        "status": "Status",
        "folder_log": "Folder log",
        "ready": "Ready",
        "checking_updates": "Checking updates...",
        "latest_version": "You are using the latest version of the program",
        "current_subtitle": "Current subtitle: 0%",
        "total": "Total: 0%",
    },
    "hr": {
        "tab_single": "Sinkronizacija",
        "tab_folder": "Folder",
        "tab_help": "Help",
        "language": "Jezik",
        "check_updates": "Provjeri update",
        "files": "Datoteke",
        "alass_program": "Alass program",
        "video_file": "Video",
        "correct_subtitle": "Tocni prijevod (opcionalno)",
        "incorrect_subtitle": "Prijevod za popraviti",
        "output_subtitle": "Izlazni titl",
        "choose": "Odaberi",
        "options": "Opcije",
        "split_penalty": "Split penalty",
        "interval": "Interval (ms)",
        "speed_opt": "Speed opt.",
        "fps_ref": "FPS referenca",
        "fps_sub": "FPS titl",
        "audio_index": "Audio index",
        "encoding_ref": "Encoding ref.",
        "encoding_sub": "Encoding titl",
        "stat_tag": "Stat. tag",
        "no_split": "Bez splitova (--no-split)",
        "allow_negative": "Dopusti negativna vremena",
        "disable_fps": "Iskljuci FPS guessing",
        "repair_srt": "Popravi jednostavne SRT greske",
        "command": "Komanda",
        "save_mode": "Spremanje prijevoda",
        "suffix_mode": "Ostavi original i dodaj .synced",
        "backup_mode": "Original u folder 'original prijevod', novi kao video",
        "run_sync": "Pokreni sinkronizaciju",
        "stop": "Prekini",
        "progress": "Napredak",
        "log": "Log",
        "folder": "Folder",
        "movies_folder": "Folder s filmovima",
        "load_folder": "Ucitaj folder",
        "rescan": "Ponovno skeniraj",
        "include_subfolders": "Ukljuci podfoldere",
        "open_folder": "Otvori folder",
        "selection": "Odabir",
        "all_pairs": "Napravi sve pronadene parove",
        "selected_pairs": "Napravi samo oznacene checkboxom",
        "check_all": "Oznaci sve",
        "uncheck_all": "Makni sve",
        "clear_all": "Ocisti sve",
        "ask_on_start": "Pitaj pri pokretanju",
        "movies_subtitles": "Filmovi i titlovi",
        "use": "Use",
        "movie": "Film",
        "subtitle": "Titl",
        "output": "Izlaz",
        "status": "Status",
        "folder_log": "Folder log",
        "ready": "Spremno",
        "checking_updates": "Provjeravam update...",
        "latest_version": "Koristite najnoviju verziju programa",
        "current_subtitle": "Trenutni titl: 0%",
        "total": "Ukupno: 0%",
    },
}


class AlassGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.minsize(760, 520)

        self.log_queue: queue.Queue[tuple[str, str | None]] = queue.Queue()
        self.process: subprocess.Popen[str] | None = None
        self.worker: threading.Thread | None = None
        self.stop_requested = False
        self.active_log = "single"
        self.help_cache: dict[str, str] = {}

        self.language = tk.StringVar(value="en")
        self.alass_path = tk.StringVar(value=self._find_executable())
        self.video_file = tk.StringVar()
        self.correct_subtitle_file = tk.StringVar()
        self.incorrect_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.batch_folder = tk.StringVar()
        self.single_output_mode = tk.StringVar(value="suffix")
        self.batch_mode = tk.StringVar(value="selected")
        self.batch_output_mode = tk.StringVar(value="ask")
        self.include_subfolders = tk.BooleanVar(value=False)
        self.ffmpeg_path = tk.StringVar(value=os.environ.get("ALASS_FFMPEG_PATH", self._find_tool("ffmpeg")))
        self.ffprobe_path = tk.StringVar(value=os.environ.get("ALASS_FFPROBE_PATH", self._find_tool("ffprobe")))

        self.split_penalty = tk.StringVar(value="7")
        self.interval = tk.StringVar(value="1")
        self.speed_optimization = tk.StringVar(value="1")
        self.sub_fps_ref = tk.StringVar(value="30")
        self.sub_fps_inc = tk.StringVar(value="30")
        self.encoding_ref = tk.StringVar(value="auto")
        self.encoding_inc = tk.StringVar(value="auto")
        self.audio_index = tk.StringVar()
        self.statistics_tag = tk.StringVar()

        self.no_split = tk.BooleanVar(value=False)
        self.allow_negative = tk.BooleanVar(value=False)
        self.disable_fps_guessing = tk.BooleanVar(value=False)
        self.repair_srt = tk.BooleanVar(value=False)

        self.status = tk.StringVar(value=self._t("ready"))
        self.command_preview = tk.StringVar()
        self.single_progress = tk.DoubleVar(value=0)
        self.batch_current_progress = tk.DoubleVar(value=0)
        self.batch_total_progress = tk.DoubleVar(value=0)
        self.batch_current_label = tk.StringVar(value=self._t("current_subtitle"))
        self.batch_total_label = tk.StringVar(value=self._t("total"))
        self.jobs: dict[str, dict[str, str | bool]] = {}
        self.job_results: list[dict[str, str]] = []
        self.batch_items: dict[str, dict[str, str | bool]] = {}

        self._build_ui()
        self._bind_updates()
        self._refresh_command_preview()
        self.after(100, self._drain_log_queue)

    def _find_executable(self) -> str:
        candidates = ["alass.exe", "alass"] if os.name == "nt" else ["alass", "alass.exe"]
        for candidate in candidates:
            local_alass = APP_DIR / "bin" / candidate
            if local_alass.exists():
                return str(local_alass)
        return shutil.which("alass") or shutil.which("alass-cli") or shutil.which("alass.exe") or "alass"

    def _find_tool(self, name: str) -> str:
        candidates = [f"{name}.exe", name] if os.name == "nt" else [name, f"{name}.exe"]
        for candidate in candidates:
            local_tool = APP_DIR / "bin" / candidate
            if local_tool.exists():
                return str(local_tool)
        return shutil.which(name) or shutil.which(f"{name}.exe") or name

    def _tool_available(self, value: str) -> bool:
        tool = value.strip()
        if not tool:
            return False
        path = Path(tool)
        if path.parent != Path(".") or path.is_absolute():
            return path.is_file()
        return shutil.which(tool) is not None

    def _check_for_updates(self) -> None:
        if self.process is not None:
            messagebox.showinfo(APP_TITLE, "Finish the current sync before checking for updates.")
            return
        self.status.set(self._t("checking_updates"))
        self.update_button.configure(state="disabled")
        threading.Thread(target=self._update_worker, daemon=True).start()

    def _update_worker(self) -> None:
        try:
            release = self._fetch_latest_release()
            latest_tag = str(release.get("tag_name", "")).strip()
            current_version = self._current_alass_version()
            if latest_tag and self._same_version(current_version, latest_tag):
                version = current_version or latest_tag
                self.log_queue.put(("update_info", f"{self._t('latest_version')} ({version})."))
                return

            asset = self._select_release_asset(release)
            if not asset:
                self.log_queue.put(
                    (
                        "update_info",
                        "No matching binary asset was found for this OS. Open releases page:\n" + ALASS_RELEASES_URL,
                    )
                )
                return

            asset_name = str(asset.get("name", ""))
            answer = self._ask_yes_no_threadsafe(
                "Alass update",
                f"Current: {current_version or 'unknown'}\nLatest: {latest_tag or 'unknown'}\nAsset: {asset_name}\n\nDownload and install locally?",
            )
            if not answer:
                self.log_queue.put(("update_info", "Update cancelled."))
                return

            target = self._local_alass_target()
            installed = self._download_and_install_asset(str(asset["browser_download_url"]), asset_name, target)
            self.log_queue.put(("update_path", str(installed)))
            self.log_queue.put(("update_info", f"Updated local alass binary:\n{installed}"))
        except Exception as exc:  # noqa: BLE001 - update errors should be shown in GUI.
            self.log_queue.put(("update_info", f"Update failed: {exc}"))

    def _fetch_latest_release(self) -> dict:
        request = urllib.request.Request(ALASS_RELEASE_API, headers={"User-Agent": "Alass-GUI"})
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))

    def _current_alass_version(self) -> str:
        try:
            result = subprocess.run(
                [self.alass_path.get().strip() or "alass", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=5,
                check=False,
            )
            return (result.stdout or "").strip().splitlines()[0].replace("alass-cli", "").strip()
        except Exception:
            return ""

    def _same_version(self, current: str, latest_tag: str) -> bool:
        current_norm = current.lower().lstrip("v").strip()
        latest_norm = latest_tag.lower().lstrip("v").strip()
        return bool(current_norm and latest_norm and current_norm == latest_norm)

    def _select_release_asset(self, release: dict) -> dict | None:
        assets = release.get("assets") or []
        system = platform.system().lower()
        machine = platform.machine().lower()
        if "windows" in system:
            os_tokens = ("windows", "win", ".exe")
            bad_tokens = ("linux", "darwin", "apple", "macos", "osx")
        elif "darwin" in system:
            os_tokens = ("darwin", "apple", "macos", "osx")
            bad_tokens = ("linux", "windows", "win32", "win64", ".exe")
        else:
            os_tokens = ("linux", "unknown-linux", "gnu", "musl")
            bad_tokens = ("windows", "win32", "win64", ".exe", "darwin", "apple", "macos", "osx")
        arch_tokens = ("x86_64", "amd64", "64") if "64" in machine or "amd64" in machine else ("i686", "x86", "32")

        scored: list[tuple[int, dict]] = []
        for asset in assets:
            name = str(asset.get("name", "")).lower()
            if not name or "source" in name:
                continue
            if any(token in name for token in bad_tokens):
                continue
            score = 0
            if "alass" in name:
                score += 3
            if any(token in name for token in os_tokens):
                score += 5
            if any(token in name for token in arch_tokens):
                score += 2
            if name.endswith((".zip", ".tar.gz", ".tgz", ".exe")) or "alass" in name:
                score += 1
            if score >= 5:
                scored.append((score, asset))
        if not scored:
            return None
        return sorted(scored, key=lambda pair: pair[0], reverse=True)[0][1]

    def _local_alass_target(self) -> Path:
        bin_dir = APP_DIR / "bin"
        bin_dir.mkdir(exist_ok=True)
        return bin_dir / ("alass.exe" if os.name == "nt" else "alass")

    def _download_and_install_asset(self, url: str, asset_name: str, target: Path) -> Path:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            download_path = tmp_path / asset_name
            request = urllib.request.Request(url, headers={"User-Agent": "Alass-GUI"})
            with urllib.request.urlopen(request, timeout=60) as response, download_path.open("wb") as output:
                shutil.copyfileobj(response, output)

            binary = self._extract_alass_binary(download_path, tmp_path)
            if target.exists():
                backup = self._unique_path(target.with_name(f"{target.name}.bak"))
                shutil.copy2(target, backup)
            shutil.copy2(binary, target)
            if os.name != "nt":
                target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            return target

    def _extract_alass_binary(self, download_path: Path, tmp_path: Path) -> Path:
        name = download_path.name.lower()
        extract_dir = tmp_path / "extract"
        extract_dir.mkdir(exist_ok=True)
        if name.endswith(".zip"):
            with zipfile.ZipFile(download_path) as archive:
                archive.extractall(extract_dir)
            return self._find_extracted_binary(extract_dir)
        if name.endswith((".tar.gz", ".tgz")):
            with tarfile.open(download_path) as archive:
                archive.extractall(extract_dir)
            return self._find_extracted_binary(extract_dir)
        return download_path

    def _find_extracted_binary(self, folder: Path) -> Path:
        candidates = []
        for path in folder.rglob("*"):
            if not path.is_file():
                continue
            lower = path.name.lower()
            if lower in {"alass", "alass.exe", "alass-cli", "alass-cli.exe"} or lower.startswith("alass"):
                candidates.append(path)
        if not candidates:
            raise RuntimeError("Downloaded archive did not contain an alass binary.")
        return sorted(candidates, key=lambda p: (p.suffix.lower() not in {"", ".exe"}, len(str(p))))[0]

    def _ask_yes_no_threadsafe(self, title: str, message: str) -> bool:
        result: queue.Queue[bool] = queue.Queue(maxsize=1)

        def ask() -> None:
            result.put(messagebox.askyesno(title, message))

        self.after(0, ask)
        return result.get()

    def _build_ui(self) -> None:
        self._configure_style()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self, padding=(12, 8))
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(0, weight=1)
        self.update_button = ttk.Button(toolbar, text=self._t("check_updates"), command=self._check_for_updates)
        self.update_button.grid(row=0, column=1, sticky="e", padx=(0, 16))
        ttk.Label(toolbar, text=self._t("language")).grid(row=0, column=2, sticky="e", padx=(0, 8))
        language_combo = ttk.Combobox(
            toolbar,
            textvariable=self.language,
            values=("en", "hr"),
            width=10,
            state="readonly",
        )
        language_combo.grid(row=0, column=3, sticky="e")
        language_combo.bind("<<ComboboxSelected>>", lambda _event: self._change_language())

        tabs = ttk.Notebook(self)
        tabs.grid(row=1, column=0, sticky="nsew")

        run_tab = self._create_scrollable_tab(tabs, self._t("tab_single"))
        batch_tab = self._create_scrollable_tab(tabs, self._t("tab_folder"))
        help_tab = ttk.Frame(tabs, padding=16)
        tabs.add(help_tab, text=self._t("tab_help"))

        self._build_run_tab(run_tab)
        self._build_batch_tab(batch_tab)
        self._build_help_tab(help_tab)

    def _t(self, key: str) -> str:
        return TEXT.get(self.language.get(), TEXT["en"]).get(key, TEXT["en"].get(key, key))

    def _change_language(self) -> None:
        if self.process is not None:
            messagebox.showinfo(APP_TITLE, "Language can be changed after the current sync finishes.")
            self.language.set("hr" if self.language.get() == "en" else "en")
            return
        for child in self.winfo_children():
            child.destroy()
        self.status.set(self._t("ready"))
        self.batch_current_label.set(self._t("current_subtitle"))
        self.batch_total_label.set(self._t("total"))
        self._build_ui()
        for iid in self.batch_items:
            self._refresh_batch_row(iid)
        self._refresh_command_preview()

    def _create_scrollable_tab(self, tabs: ttk.Notebook, title: str) -> ttk.Frame:
        outer = ttk.Frame(tabs)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)
        tabs.add(outer, text=title)

        canvas = tk.Canvas(outer, bg="#eef2f6", highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        content = ttk.Frame(canvas, padding=16)
        window_id = canvas.create_window((0, 0), window=content, anchor="nw")

        def update_scroll_region(_event=None) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def update_content_width(event) -> None:
            canvas.itemconfigure(window_id, width=event.width)

        def on_mousewheel(event) -> None:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        content.bind("<Configure>", update_scroll_region)
        canvas.bind("<Configure>", update_content_width)
        canvas.bind("<Enter>", lambda _event: canvas.bind_all("<MouseWheel>", on_mousewheel))
        canvas.bind("<Leave>", lambda _event: canvas.unbind_all("<MouseWheel>"))
        return content

    def _configure_style(self) -> None:
        self.configure(bg="#eef2f6")
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", font=("DejaVu Sans", 10), background="#eef2f6", foreground="#17202a")
        style.configure("TFrame", background="#eef2f6")
        style.configure("TLabelframe", background="#eef2f6", bordercolor="#c8d2dc", relief="solid")
        style.configure("TLabelframe.Label", background="#eef2f6", foreground="#243447", font=("DejaVu Sans", 10, "bold"))
        style.configure("TLabel", background="#eef2f6", foreground="#243447")
        style.configure("TEntry", fieldbackground="#ffffff", bordercolor="#b9c6d3", lightcolor="#b9c6d3", darkcolor="#b9c6d3")
        style.configure("TCombobox", fieldbackground="#ffffff", bordercolor="#b9c6d3", arrowcolor="#243447")
        style.configure("TButton", padding=(12, 7), background="#d9e2ec", foreground="#17202a", bordercolor="#aebdca")
        style.map("TButton", background=[("active", "#c8d8e8"), ("disabled", "#e5e9ee")])
        style.configure("Accent.TButton", background="#2f6fed", foreground="#ffffff", bordercolor="#265cc6")
        style.map("Accent.TButton", background=[("active", "#285ec9"), ("disabled", "#9fb8e8")])
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground="#17202a", rowheight=28, bordercolor="#c8d2dc")
        style.configure("Treeview.Heading", background="#dce6f0", foreground="#17202a", font=("DejaVu Sans", 10, "bold"))
        style.configure("Horizontal.TProgressbar", troughcolor="#dbe4ee", background="#2f6fed", bordercolor="#c8d2dc", lightcolor="#2f6fed", darkcolor="#2f6fed")
        style.configure("TNotebook", background="#eef2f6", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(14, 8), background="#d9e2ec", foreground="#243447")
        style.map("TNotebook.Tab", background=[("selected", "#ffffff")])

    def _build_run_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(7, weight=1)

        files = ttk.LabelFrame(parent, text=self._t("files"), padding=12)
        files.grid(row=0, column=0, sticky="ew")
        files.columnconfigure(1, weight=1)

        self._path_row(files, 0, self._t("alass_program"), self.alass_path, self._choose_executable)
        self._path_row(files, 1, self._t("video_file"), self.video_file, self._choose_video)
        self._path_row(files, 2, self._t("correct_subtitle"), self.correct_subtitle_file, self._choose_reference_subtitle)
        self._path_row(files, 3, self._t("incorrect_subtitle"), self.incorrect_file, self._choose_incorrect)
        self._path_row(files, 4, self._t("output_subtitle"), self.output_file, self._choose_output, save=True)

        options = ttk.LabelFrame(parent, text=self._t("options"), padding=12)
        options.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        for idx in range(6):
            options.columnconfigure(idx, weight=1)

        self._entry_option(options, 0, 0, self._t("split_penalty"), self.split_penalty)
        self._entry_option(options, 0, 2, self._t("interval"), self.interval)
        self._entry_option(options, 0, 4, self._t("speed_opt"), self.speed_optimization)
        self._entry_option(options, 1, 0, self._t("fps_ref"), self.sub_fps_ref)
        self._entry_option(options, 1, 2, self._t("fps_sub"), self.sub_fps_inc)
        self._entry_option(options, 1, 4, self._t("audio_index"), self.audio_index)
        self._combo_option(options, 2, 0, self._t("encoding_ref"), self.encoding_ref)
        self._combo_option(options, 2, 2, self._t("encoding_sub"), self.encoding_inc)
        self._entry_option(options, 2, 4, self._t("stat_tag"), self.statistics_tag)

        checks = ttk.Frame(options)
        checks.grid(row=3, column=0, columnspan=6, sticky="ew", pady=(10, 0))
        ttk.Checkbutton(checks, text=self._t("no_split"), variable=self.no_split).pack(side=tk.LEFT, padx=(0, 18))
        ttk.Checkbutton(checks, text=self._t("allow_negative"), variable=self.allow_negative).pack(side=tk.LEFT, padx=(0, 18))
        ttk.Checkbutton(checks, text=self._t("disable_fps"), variable=self.disable_fps_guessing).pack(side=tk.LEFT, padx=(0, 18))
        ttk.Checkbutton(checks, text=self._t("repair_srt"), variable=self.repair_srt).pack(side=tk.LEFT)

        ffmpeg = ttk.LabelFrame(parent, text="FFmpeg", padding=12)
        ffmpeg.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        ffmpeg.columnconfigure(1, weight=1)
        ffmpeg.columnconfigure(3, weight=1)
        ttk.Label(ffmpeg, text="ffmpeg").grid(row=0, column=0, sticky="w")
        ttk.Entry(ffmpeg, textvariable=self.ffmpeg_path).grid(row=0, column=1, sticky="ew", padx=(8, 18))
        ttk.Label(ffmpeg, text="ffprobe").grid(row=0, column=2, sticky="w")
        ttk.Entry(ffmpeg, textvariable=self.ffprobe_path).grid(row=0, column=3, sticky="ew", padx=(8, 0))

        command_box = ttk.LabelFrame(parent, text=self._t("command"), padding=12)
        command_box.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        command_box.columnconfigure(0, weight=1)
        ttk.Entry(command_box, textvariable=self.command_preview, state="readonly").grid(row=0, column=0, sticky="ew")

        single_output_mode = ttk.LabelFrame(parent, text=self._t("save_mode"), padding=10)
        single_output_mode.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        ttk.Radiobutton(
            single_output_mode,
            text=self._t("suffix_mode"),
            variable=self.single_output_mode,
            value="suffix",
            command=self._refresh_single_output_mode,
        ).pack(side=tk.LEFT, padx=(0, 18))
        ttk.Radiobutton(
            single_output_mode,
            text=self._t("backup_mode"),
            variable=self.single_output_mode,
            value="backup",
            command=self._refresh_single_output_mode,
        ).pack(side=tk.LEFT)

        actions = ttk.Frame(parent)
        actions.grid(row=5, column=0, sticky="ew", pady=(12, 0))
        actions.columnconfigure(1, weight=1)
        self.run_button = ttk.Button(actions, text=self._t("run_sync"), command=self._run_alass, style="Accent.TButton")
        self.run_button.grid(row=0, column=0, sticky="w")
        self.stop_button = ttk.Button(actions, text=self._t("stop"), command=self._stop_alass, state="disabled")
        self.stop_button.grid(row=0, column=1, sticky="w", padx=(10, 0))
        ttk.Label(actions, textvariable=self.status).grid(row=0, column=2, sticky="e")

        single_progress_frame = ttk.LabelFrame(parent, text=self._t("progress"), padding=12)
        single_progress_frame.grid(row=6, column=0, sticky="ew", pady=(12, 0))
        single_progress_frame.columnconfigure(0, weight=1)
        ttk.Progressbar(single_progress_frame, variable=self.single_progress, maximum=100).grid(row=0, column=0, sticky="ew")

        log_frame = ttk.LabelFrame(parent, text=self._t("log"), padding=8)
        log_frame.grid(row=7, column=0, sticky="nsew", pady=(12, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.single_log = self._create_log(log_frame, height=12)
        log_scroll = ttk.Scrollbar(log_frame, command=self.single_log.yview)
        self.single_log.configure(yscrollcommand=log_scroll.set)
        self.single_log.grid(row=0, column=0, sticky="nsew")
        log_scroll.grid(row=0, column=1, sticky="ns")

    def _build_batch_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(3, weight=2)
        parent.rowconfigure(6, weight=1)

        top = ttk.LabelFrame(parent, text=self._t("folder"), padding=12)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text=self._t("movies_folder")).grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.batch_folder).grid(row=0, column=1, columnspan=3, sticky="ew", padx=8)
        ttk.Checkbutton(top, text=self._t("include_subfolders"), variable=self.include_subfolders).grid(
            row=1, column=1, sticky="w", padx=8, pady=(8, 0)
        )
        ttk.Button(top, text=self._t("load_folder"), command=self._choose_batch_folder).grid(row=1, column=2, padx=(0, 8), pady=(8, 0))
        ttk.Button(top, text=self._t("rescan"), command=self._scan_batch_folder).grid(row=1, column=3, pady=(8, 0))
        ttk.Button(top, text=self._t("open_folder"), command=self._open_selected_batch_folder).grid(
            row=2, column=2, columnspan=2, sticky="e", pady=(8, 0)
        )

        mode = ttk.LabelFrame(parent, text=self._t("selection"), padding=10)
        mode.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        ttk.Radiobutton(mode, text=self._t("all_pairs"), variable=self.batch_mode, value="all").pack(
            side=tk.LEFT, padx=(0, 18)
        )
        ttk.Radiobutton(mode, text=self._t("selected_pairs"), variable=self.batch_mode, value="selected").pack(
            side=tk.LEFT, padx=(0, 18)
        )
        ttk.Button(mode, text=self._t("check_all"), command=lambda: self._set_all_batch_checked(True)).pack(side=tk.LEFT)
        ttk.Button(mode, text=self._t("uncheck_all"), command=lambda: self._set_all_batch_checked(False)).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(mode, text=self._t("clear_all"), command=self._clear_batch_all).pack(side=tk.LEFT, padx=(8, 0))

        output_mode = ttk.LabelFrame(parent, text=self._t("save_mode"), padding=10)
        output_mode.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        ttk.Radiobutton(output_mode, text=self._t("ask_on_start"), variable=self.batch_output_mode, value="ask").pack(
            side=tk.LEFT, padx=(0, 18)
        )
        ttk.Radiobutton(output_mode, text=self._t("suffix_mode"), variable=self.batch_output_mode, value="suffix").pack(
            side=tk.LEFT, padx=(0, 18)
        )
        ttk.Radiobutton(
            output_mode,
            text=self._t("backup_mode"),
            variable=self.batch_output_mode,
            value="backup",
        ).pack(side=tk.LEFT)

        table_frame = ttk.LabelFrame(parent, text=self._t("movies_subtitles"), padding=8)
        table_frame.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("checked", "movie", "subtitle", "output", "status")
        self.batch_tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse", height=8)
        self.batch_tree.heading("checked", text=self._t("use"))
        self.batch_tree.heading("movie", text=self._t("movie"))
        self.batch_tree.heading("subtitle", text=self._t("subtitle"))
        self.batch_tree.heading("output", text=self._t("output"))
        self.batch_tree.heading("status", text=self._t("status"))
        self.batch_tree.column("checked", width=54, minwidth=54, stretch=False, anchor="center")
        self.batch_tree.column("movie", width=240)
        self.batch_tree.column("subtitle", width=240)
        self.batch_tree.column("output", width=240)
        self.batch_tree.column("status", width=110, stretch=False)
        self.batch_tree.grid(row=0, column=0, sticky="nsew")
        self.batch_tree.bind("<Button-1>", self._on_batch_click)
        batch_scroll = ttk.Scrollbar(table_frame, command=self.batch_tree.yview)
        self.batch_tree.configure(yscrollcommand=batch_scroll.set)
        batch_scroll.grid(row=0, column=1, sticky="ns")

        progress_frame = ttk.LabelFrame(parent, text=self._t("progress"), padding=12)
        progress_frame.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        progress_frame.columnconfigure(1, weight=1)
        ttk.Label(progress_frame, textvariable=self.batch_current_label).grid(row=0, column=0, sticky="w", padx=(0, 12))
        ttk.Progressbar(progress_frame, variable=self.batch_current_progress, maximum=100).grid(row=0, column=1, sticky="ew")
        ttk.Label(progress_frame, textvariable=self.batch_total_label).grid(row=1, column=0, sticky="w", padx=(0, 12), pady=(8, 0))
        ttk.Progressbar(progress_frame, variable=self.batch_total_progress, maximum=100).grid(row=1, column=1, sticky="ew", pady=(8, 0))

        bottom = ttk.Frame(parent)
        bottom.grid(row=5, column=0, sticky="ew", pady=(12, 0))
        bottom.columnconfigure(1, weight=1)
        self.batch_run_button = ttk.Button(bottom, text=self._t("run_sync"), command=self._run_batch, style="Accent.TButton")
        self.batch_run_button.grid(row=0, column=0, sticky="w")
        ttk.Button(bottom, text=self._t("stop"), command=self._stop_alass).grid(row=0, column=1, sticky="w", padx=(10, 0))
        ttk.Label(bottom, textvariable=self.status).grid(row=0, column=2, sticky="e")

        batch_log_frame = ttk.LabelFrame(parent, text=self._t("folder_log"), padding=8)
        batch_log_frame.grid(row=6, column=0, sticky="nsew", pady=(12, 0))
        batch_log_frame.columnconfigure(0, weight=1)
        batch_log_frame.rowconfigure(0, weight=1)
        self.batch_log = self._create_log(batch_log_frame, height=16)
        batch_log_scroll = ttk.Scrollbar(batch_log_frame, command=self.batch_log.yview)
        self.batch_log.configure(yscrollcommand=batch_log_scroll.set)
        self.batch_log.grid(row=0, column=0, sticky="nsew")
        batch_log_scroll.grid(row=0, column=1, sticky="ns")

    def _build_help_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        text = tk.Text(parent, wrap="word", padx=12, pady=10, bg="#ffffff", fg="#17202a", relief="flat")
        text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(parent, command=text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        text.configure(yscrollcommand=scroll.set)
        self._insert_help_text(text, HELP_TEXTS.get(self.language.get(), HELP_TEXTS["en"]))
        text.configure(state="disabled")

    def _insert_help_text(self, widget: tk.Text, help_text: str) -> None:
        widget.tag_configure("title", foreground="#1f5fbf", font=("DejaVu Sans", 14, "bold"))
        widget.tag_configure("section", foreground="#0f6b4f", font=("DejaVu Sans", 11, "bold"))
        widget.tag_configure("link", foreground="#1f5fbf", underline=True)
        widget.tag_configure("important", foreground="#9a3412", font=("DejaVu Sans", 10, "bold"))
        section_titles = {
            "About the program",
            "What alass does",
            "Single file workflow",
            "Folder workflow",
            "Saving modes",
            "Log and report",
            "Supported formats",
            "Important options",
            "Examples",
            "Sto program radi",
            "Osnovni postupak",
            "Rad s cijelim folderom",
            "Log i izvjestaj",
            "Podrzani formati",
            "Najvaznije opcije",
            "FFmpeg",
            "Primjeri",
        }
        for line in help_text.splitlines(keepends=True):
            tag = None
            stripped = line.strip()
            if stripped.startswith("Alass GUI"):
                tag = "title"
            elif stripped in section_titles:
                tag = "section"
            elif stripped.startswith("http"):
                tag = "link"
            elif stripped.startswith(("Keep original", "Move original", "Encoding", "Split penalty", "No splits", "Ostavi", "Original", "Encoding ref", "Bez splitova", "Split penalty")):
                tag = "important"
            widget.insert("end", line, tag if tag else ())

    def _create_log(self, parent: ttk.Frame, height: int = 10) -> tk.Text:
        return tk.Text(
            parent,
            height=height,
            wrap="word",
            state="disabled",
            bg="#0f1720",
            fg="#d8e2ee",
            insertbackground="#d8e2ee",
            selectbackground="#2f6fed",
            relief="flat",
            padx=10,
            pady=8,
        )

    def _path_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        command,
        save: bool = False,
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=8, pady=4)
        ttk.Button(parent, text=self._t("choose"), command=command).grid(row=row, column=2, sticky="e", pady=4)

    def _entry_option(self, parent: ttk.Frame, row: int, column: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=variable, width=14).grid(row=row, column=column + 1, sticky="ew", padx=(8, 18), pady=4)

    def _combo_option(self, parent: ttk.Frame, row: int, column: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", pady=4)
        ttk.Combobox(parent, textvariable=variable, values=COMMON_ENCODINGS, width=18).grid(
            row=row, column=column + 1, sticky="ew", padx=(8, 18), pady=4
        )

    def _bind_updates(self) -> None:
        variables = [
            self.alass_path,
            self.video_file,
            self.correct_subtitle_file,
            self.incorrect_file,
            self.output_file,
            self.single_output_mode,
            self.ffmpeg_path,
            self.ffprobe_path,
            self.split_penalty,
            self.interval,
            self.speed_optimization,
            self.sub_fps_ref,
            self.sub_fps_inc,
            self.encoding_ref,
            self.encoding_inc,
            self.audio_index,
            self.statistics_tag,
            self.no_split,
            self.allow_negative,
            self.disable_fps_guessing,
            self.repair_srt,
        ]
        for variable in variables:
            variable.trace_add("write", lambda *_: self._refresh_command_preview())

    def _choose_executable(self) -> None:
        path = filedialog.askopenfilename(title="Odaberi alass ili alass-cli")
        if path:
            self.alass_path.set(path)

    def _choose_video(self) -> None:
        initial_dir = self._single_initial_dir()
        path = self._choose_video_reference(initial_dir)
        if path:
            self.video_file.set(path)

    def _choose_reference_subtitle(self) -> None:
        initial_dir = self._single_initial_dir()
        path = filedialog.askopenfilename(
            title="Odaberi tocni referentni titl",
            initialdir=str(initial_dir),
            filetypes=[("Subtitle files", "*.srt *.ssa *.ass *.idx *.sub"), ("All files", "*.*")],
        )
        if path:
            self.correct_subtitle_file.set(path)

    def _single_initial_dir(self) -> Path:
        for value in (
            self.incorrect_file.get().strip(),
            self.video_file.get().strip(),
            self.correct_subtitle_file.get().strip(),
        ):
            if value:
                path = Path(value)
                if path.parent.is_dir():
                    return path.parent
        return APP_DIR

    def _choose_incorrect(self) -> None:
        path = filedialog.askopenfilename(
            title="Odaberi neispravan titl",
            filetypes=[("Subtitle files", "*.srt *.ssa *.ass *.idx *.sub"), ("All files", "*.*")],
        )
        if path:
            self.incorrect_file.set(path)
            if not self.output_file.get():
                self.output_file.set(self._suggest_output_path(path))
            self._refresh_single_output_mode()
            self._maybe_select_reference_for_subtitle(Path(path))

    def _choose_video_reference(self, initial_dir: Path) -> str:
        return filedialog.askopenfilename(
            title="Odaberi video za ovaj titl",
            initialdir=str(initial_dir),
            filetypes=[("Video files", "*.mp4 *.mkv *.avi *.mov *.wmv *.m4v *.webm *.ts *.mpg *.mpeg"), ("All files", "*.*")],
        )

    def _maybe_select_reference_for_subtitle(self, subtitle: Path) -> None:
        if self.video_file.get().strip():
            return

        video = self._match_video_for_subtitle(subtitle)
        if video is not None:
            self.video_file.set(str(video))
            return

        if messagebox.askyesno(
            APP_TITLE,
            "Nisam pronasao video istog imena kao odabrani titl.\n\nZelis li sada rucno odabrati video za ovaj titl?",
        ):
            path = self._choose_video_reference(subtitle.parent)
            if path:
                self.video_file.set(path)

    def _match_video_for_subtitle(self, subtitle: Path) -> Path | None:
        if not subtitle.parent.is_dir():
            return None

        videos = [p for p in subtitle.parent.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS]
        subtitle_stem = subtitle.stem.lower()
        exact = [video for video in videos if video.stem.lower() == subtitle_stem]
        if exact:
            return sorted(exact, key=lambda p: p.name.lower())[0]
        return None

    def _choose_output(self) -> None:
        initial = self.output_file.get() or self._suggest_output_path(self.incorrect_file.get())
        path = filedialog.asksaveasfilename(
            title="Spremi ispravljeni titl",
            initialfile=Path(initial).name if initial else "output.srt",
            initialdir=str(Path(initial).parent) if initial else None,
            filetypes=[("Subtitle files", "*.srt *.ssa *.ass *.idx *.sub"), ("All files", "*.*")],
        )
        if path:
            self.output_file.set(path)

    def _refresh_single_output_mode(self) -> None:
        if self.single_output_mode.get() == "suffix" and self.incorrect_file.get().strip():
            self.output_file.set(self._suggest_output_path(self.incorrect_file.get().strip()))

    def _choose_batch_folder(self) -> None:
        path = filedialog.askdirectory(title="Odaberi folder s filmovima i titlovima")
        if path:
            self.batch_folder.set(path)
            self._scan_batch_folder()

    def _open_selected_batch_folder(self) -> None:
        selected = self.batch_tree.selection()
        if selected:
            item = self.batch_items.get(selected[0])
            folder = Path(str(item["reference"])).parent if item else None
        else:
            folder_text = self.batch_folder.get().strip()
            folder = Path(folder_text) if folder_text else None
        if folder is None or not folder.is_dir():
            messagebox.showerror(APP_TITLE, "Nema foldera za otvoriti.")
            return

        try:
            if os.name == "nt":
                os.startfile(str(folder))  # type: ignore[attr-defined]
                return
            if platform.system() == "Darwin":
                subprocess.Popen(["open", str(folder)])
                return
            opener = shutil.which("xdg-open") or shutil.which("gio")
            if opener and Path(opener).name == "gio":
                subprocess.Popen([opener, "open", str(folder)])
            elif opener:
                subprocess.Popen([opener, str(folder)])
            else:
                messagebox.showerror(APP_TITLE, "Nije pronaden program za otvaranje foldera.")
        except Exception as exc:  # noqa: BLE001 - GUI should show launcher errors.
            messagebox.showerror(APP_TITLE, f"Ne mogu otvoriti folder: {exc}")

    def _scan_batch_folder(self) -> None:
        folder_text = self.batch_folder.get().strip()
        if not folder_text:
            messagebox.showerror(APP_TITLE, "Prvo odaberi folder.")
            return
        folder = Path(folder_text)
        if not folder.is_dir():
            messagebox.showerror(APP_TITLE, "Odabrana putanja nije folder.")
            return

        for item in self.batch_tree.get_children():
            self.batch_tree.delete(item)
        self.batch_items.clear()

        paths = folder.rglob("*") if self.include_subfolders.get() else folder.iterdir()
        files = [p for p in paths if p.is_file()]
        subtitles = [p for p in files if p.suffix.lower() in SUBTITLE_EXTENSIONS]
        movies = [p for p in files if p.suffix.lower() in VIDEO_EXTENSIONS]

        for movie in sorted(movies, key=lambda p: p.name.lower()):
            subtitle = self._match_subtitle(movie, subtitles)
            if subtitle is None:
                continue
            output = self._suggest_output_path(str(subtitle))
            iid = str(movie)
            self.batch_items[iid] = {
                "checked": True,
                "reference": str(movie),
                "incorrect": str(subtitle),
                "output": output,
                "final_output": output,
                "temp_output": output,
                "status": "Spremno",
            }
            self._refresh_batch_row(iid)

        scope = "s podfolderima" if self.include_subfolders.get() else "bez podfoldera"
        self.status.set(f"Pronadeno parova: {len(self.batch_items)} ({scope})")

    def _match_subtitle(self, movie: Path, subtitles: list[Path]) -> Path | None:
        movie_stem = movie.stem.lower()
        same_folder = [sub for sub in subtitles if sub.parent == movie.parent]
        exact = [sub for sub in same_folder if sub.stem.lower() == movie_stem]
        if exact:
            return sorted(exact, key=lambda p: p.name.lower())[0]
        exact_anywhere = [sub for sub in subtitles if sub.stem.lower() == movie_stem]
        if exact_anywhere:
            return sorted(exact_anywhere, key=lambda p: (p.parent != movie.parent, p.name.lower()))[0]
        partial = [
            sub
            for sub in same_folder
            if movie_stem in sub.stem.lower() or sub.stem.lower() in movie_stem
        ]
        if partial:
            return sorted(partial, key=lambda p: (abs(len(p.stem) - len(movie.stem)), p.name.lower()))[0]
        partial_anywhere = [
            sub
            for sub in subtitles
            if movie_stem in sub.stem.lower() or sub.stem.lower() in movie_stem
        ]
        if partial_anywhere:
            return sorted(
                partial_anywhere,
                key=lambda p: (p.parent != movie.parent, abs(len(p.stem) - len(movie.stem)), p.name.lower()),
            )[0]
        return None

    def _on_batch_click(self, event) -> None:
        region = self.batch_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        column = self.batch_tree.identify_column(event.x)
        if column != "#1":
            return
        iid = self.batch_tree.identify_row(event.y)
        if iid and iid in self.batch_items:
            self.batch_items[iid]["checked"] = not bool(self.batch_items[iid]["checked"])
            self._refresh_batch_row(iid)

    def _set_all_batch_checked(self, checked: bool) -> None:
        for iid in self.batch_items:
            self.batch_items[iid]["checked"] = checked
            self._refresh_batch_row(iid)

    def _clear_batch_all(self) -> None:
        if self.process is not None:
            return
        for item in self.batch_tree.get_children():
            self.batch_tree.delete(item)
        self.batch_items.clear()
        self.jobs.clear()
        self.job_results.clear()
        self.active_log = "batch"
        self._clear_log()
        self.batch_current_progress.set(0)
        self.batch_total_progress.set(0)
        self.batch_current_label.set(self._t("current_subtitle"))
        self.batch_total_label.set(self._t("total"))
        self.status.set(self._t("ready"))

    def _refresh_batch_row(self, iid: str) -> None:
        item = self.batch_items[iid]
        values = (
            "✓" if item["checked"] else "",
            Path(str(item["reference"])).name,
            Path(str(item["incorrect"])).name,
            Path(str(item["output"])).name,
            item["status"],
        )
        if self.batch_tree.exists(iid):
            self.batch_tree.item(iid, values=values)
        else:
            self.batch_tree.insert("", "end", iid=iid, values=values)

    def _suggest_output_path(self, incorrect_path: str) -> str:
        if not incorrect_path:
            return ""
        path = Path(incorrect_path)
        suffix = path.suffix if path.suffix.lower() in SUBTITLE_EXTENSIONS else ".srt"
        return str(path.with_name(f"{path.stem}.synced{suffix}"))

    def _build_command_for(self, reference: str, incorrect: str, output: str) -> list[str]:
        command = [
            self.alass_path.get().strip() or "alass",
            reference,
            incorrect,
            output,
            "--split-penalty",
            self.split_penalty.get().strip() or "7",
            "--interval",
            self.interval.get().strip() or "1",
            "--speed-optimization",
            self.speed_optimization.get().strip() or "1",
            "--sub-fps-ref",
            self.sub_fps_ref.get().strip() or "30",
            "--sub-fps-inc",
            self.sub_fps_inc.get().strip() or "30",
        ]
        encoding_ref = self.encoding_ref.get().strip()
        encoding_inc = self.encoding_inc.get().strip()
        if encoding_ref and encoding_ref != "auto":
            command.extend(["--encoding-ref", encoding_ref])
        if encoding_inc and encoding_inc != "auto":
            command.extend(["--encoding-inc", encoding_inc])
        if self.audio_index.get().strip():
            if self._supports_option("--index"):
                command.extend(["--index", self.audio_index.get().strip()])
        if self.statistics_tag.get().strip():
            command.extend(["--statistics-required-tag", self.statistics_tag.get().strip()])
        if self.no_split.get():
            command.append("--no-split")
        if self.allow_negative.get():
            command.append("--allow-negative-timestamps")
        if self.disable_fps_guessing.get():
            command.append("--disable-fps-guessing")
        return command

    def _single_reference_path(self) -> str:
        correct_subtitle = self.correct_subtitle_file.get().strip()
        if correct_subtitle:
            return correct_subtitle
        return self.video_file.get().strip()

    def _single_naming_reference_path(self) -> str:
        video = self.video_file.get().strip()
        if video:
            return video
        return self._single_reference_path()

    def _build_command(self) -> list[str]:
        reference = self._single_reference_path()
        if self.single_output_mode.get() == "backup" and reference and self.incorrect_file.get().strip():
            output = self._single_output_paths()[1]
        else:
            output = self.output_file.get().strip()
        return self._build_command_for(
            reference,
            self.incorrect_file.get().strip(),
            output,
        )

    def _command_with_option(self, command: list[str], option: str, value: str) -> list[str]:
        updated = list(command)
        if option in updated:
            index = updated.index(option)
            if index + 1 < len(updated):
                updated[index + 1] = value
                return updated
        updated.extend([option, value])
        return updated

    def _should_retry_encoding(self, command: list[str], output: str) -> bool:
        if self.encoding_inc.get().strip() != "auto":
            return False
        if "--encoding-inc" in command:
            return False
        markers = ["wrong charset encoding", "error while decoding subtitle from bytes to string"]
        return any(marker in output for marker in markers)

    def _decode_subtitle_for_validation(self, path: Path, encoding: str) -> str:
        data = path.read_bytes()
        candidates = [encoding] if encoding and encoding != "auto" else ["utf-8-sig", *ENCODING_FALLBACKS]
        last_error: UnicodeDecodeError | None = None
        for candidate in candidates:
            try:
                return data.decode(candidate)
            except UnicodeDecodeError as exc:
                last_error = exc
        if last_error is not None:
            raise last_error
        return data.decode("utf-8-sig")

    def _validate_srt_file(self, path_text: str, encoding: str) -> str | None:
        path = Path(path_text)
        if path.suffix.lower() != ".srt" or not path.is_file():
            return None

        try:
            text = self._decode_subtitle_for_validation(path, encoding)
        except UnicodeDecodeError as exc:
            return (
                f"SRT titl se ne moze procitati: {path.name}\n"
                f"Encoding '{encoding or 'auto'}' nije uspio na bajtu {exc.start}.\n"
                "Probaj rucno odabrati Encoding titl ili spremi titl kao UTF-8."
            )
        except OSError as exc:
            return f"SRT titl se ne moze otvoriti: {path}\n{exc}"

        error = self._find_srt_structure_error(text)
        if error is None:
            return None

        line_number, expected, found = error
        context = self._format_line_context(text, line_number)
        return (
            f"SRT titl nije ispravan: {path.name}\n"
            f"Linija {line_number}: ocekivan je {expected}, pronadeno je: {found!r}\n\n"
            f"{context}\n\n"
            "Popravi taj blok u titlu ili preuzmi drugi titl. Alass ne moze sinkronizirati SRT dok "
            "svaki blok nema timestamp liniju oblika 00:00:01,000 --> 00:00:03,000."
        )

    def _repair_srt_preview(self, path_text: str, encoding: str) -> str | None:
        path = Path(path_text)
        if path.suffix.lower() != ".srt" or not path.is_file():
            return None
        try:
            text = self._decode_subtitle_for_validation(path, encoding)
        except (OSError, UnicodeDecodeError):
            return None
        repaired = self._repair_srt_text(text)
        if repaired is None:
            return None
        repaired_text, summary = repaired
        if not repaired_text.strip():
            return None
        return self._format_repair_summary(path, summary)

    def _write_repaired_srt(self, path_text: str, encoding: str, repair_dir: Path) -> tuple[str, str] | None:
        path = Path(path_text)
        if path.suffix.lower() != ".srt" or not path.is_file():
            return None
        text = self._decode_subtitle_for_validation(path, encoding)
        repaired = self._repair_srt_text(text)
        if repaired is None:
            return None
        repaired_text, summary = repaired
        if not repaired_text.strip():
            return None

        repair_dir.mkdir(parents=True, exist_ok=True)
        repaired_path = repair_dir / f"{path.stem}.repaired{path.suffix}"
        counter = 1
        while repaired_path.exists():
            repaired_path = repair_dir / f"{path.stem}.repaired.{counter}{path.suffix}"
            counter += 1
        repaired_path.write_text(repaired_text, encoding="utf-8", newline="\n")
        return str(repaired_path), self._format_repair_summary(path, summary)

    def _repair_srt_text(self, text: str) -> tuple[str, dict[str, int]] | None:
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        blocks: list[list[str]] = []
        current: list[str] = []
        for line in lines:
            if line.strip():
                current.append(line)
            elif current:
                blocks.append(current)
                current = []
        if current:
            blocks.append(current)

        repaired_blocks: list[str] = []
        summary = {
            "kept": 0,
            "dropped": 0,
            "normalized_timestamps": 0,
            "renumbered": 0,
            "dropped_prefix_lines": 0,
        }
        next_index = 1

        for block in blocks:
            timestamp_index = None
            timestamp = None
            for index, line in enumerate(block):
                timestamp = self._normalize_srt_timespan(line)
                if timestamp is not None:
                    timestamp_index = index
                    break

            if timestamp_index is None or timestamp is None:
                summary["dropped"] += 1
                continue

            text_lines = [line.rstrip() for line in block[timestamp_index + 1 :] if line.strip()]
            if not text_lines:
                summary["dropped"] += 1
                continue

            if timestamp != block[timestamp_index].strip():
                summary["normalized_timestamps"] += 1
            original_index = block[0].lstrip("\ufeff").strip() if block else ""
            if timestamp_index != 1 or not original_index.isdigit() or int(original_index) != next_index:
                summary["renumbered"] += 1
            if timestamp_index > 1:
                summary["dropped_prefix_lines"] += timestamp_index - 1

            repaired_blocks.append("\n".join([str(next_index), timestamp, *text_lines]))
            summary["kept"] += 1
            next_index += 1

        if not repaired_blocks:
            return None
        return "\n\n".join(repaired_blocks) + "\n", summary

    def _normalize_srt_timespan(self, line: str) -> str | None:
        match = LOOSE_SRT_TIMESPAN_RE.match(line.strip())
        if not match:
            return None
        start_time, start_ms, end_time, end_ms, suffix = match.groups()
        start_ms = start_ms.ljust(3, "0")[:3]
        end_ms = end_ms.ljust(3, "0")[:3]
        suffix = suffix.rstrip()
        return f"{start_time},{start_ms} --> {end_time},{end_ms}{suffix}"

    def _format_repair_summary(self, path: Path, summary: dict[str, int]) -> str:
        parts = [f"SRT repair: {path.name}", f"blokova sacuvano: {summary['kept']}"]
        if summary["dropped"]:
            parts.append(f"izbaceno bez timestampa: {summary['dropped']}")
        if summary["normalized_timestamps"]:
            parts.append(f"normaliziranih timestampova: {summary['normalized_timestamps']}")
        if summary["renumbered"]:
            parts.append(f"renumeriranih blokova: {summary['renumbered']}")
        if summary["dropped_prefix_lines"]:
            parts.append(f"izbacenih redaka prije timestampa: {summary['dropped_prefix_lines']}")
        return " | ".join(parts)

    def _find_srt_structure_error(self, text: str) -> tuple[int, str, str] | None:
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        index = 0
        total = len(lines)
        while index < total:
            while index < total and not lines[index].strip():
                index += 1
            if index >= total:
                return None

            first_line_index = index
            first_line = lines[index].lstrip("\ufeff").strip()
            if SRT_TIMESPAN_RE.match(first_line):
                index += 1
            elif first_line.isdigit():
                index += 1
                if index >= total or not SRT_TIMESPAN_RE.match(lines[index].strip()):
                    found = lines[index].strip() if index < total else "kraj datoteke"
                    return index + 1, "SubRip timestamp linija", found
                index += 1
            else:
                return first_line_index + 1, "broj bloka ili SubRip timestamp linija", first_line

            while index < total and lines[index].strip():
                index += 1

        return None

    def _format_line_context(self, text: str, line_number: int) -> str:
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        start = max(1, line_number - 3)
        end = min(len(lines), line_number + 3)
        context_lines = ["Kontekst:"]
        for current in range(start, end + 1):
            marker = ">" if current == line_number else " "
            context_lines.append(f"{marker} {current}: {lines[current - 1]}")
        return "\n".join(context_lines)

    def _prepare_job_subtitles(
        self,
        iid: str | None,
        command: list[str],
        repair_dir: Path,
    ) -> tuple[list[str], str | None]:
        item = self.jobs.get(iid or "")
        if not item:
            return command, None

        updated_command = list(command)
        checks = [
            ("incorrect", 2, str(item.get("encoding", "auto"))),
        ]
        reference = str(item.get("reference", ""))
        if Path(reference).suffix.lower() == ".srt":
            checks.append(("reference", 1, self.encoding_ref.get().strip() or "auto"))

        for _kind, command_index, encoding in checks:
            if command_index >= len(updated_command):
                continue
            subtitle_path = updated_command[command_index]
            validation_error = self._validate_srt_file(subtitle_path, encoding)
            if not validation_error:
                continue
            if not self.repair_srt.get():
                return updated_command, validation_error

            try:
                repaired = self._write_repaired_srt(subtitle_path, encoding, repair_dir)
            except (OSError, UnicodeDecodeError) as exc:
                return updated_command, validation_error + f"\n\nAutomatski popravak nije uspio: {exc}"
            if repaired is None:
                return updated_command, validation_error + "\n\nAutomatski popravak nije uspio za ovaj titl."

            repaired_path, repair_summary = repaired
            updated_command[command_index] = repaired_path
            self.log_queue.put(("log", repair_summary + "\n"))

        return updated_command, None

    def _refresh_command_preview(self) -> None:
        self.command_preview.set(shlex.join(self._build_command()))

    def _validate(self) -> bool:
        required = [
            ("Alass program", self.alass_path.get()),
            (self._t("incorrect_subtitle"), self.incorrect_file.get()),
        ]
        if self.single_output_mode.get() != "backup":
            required.append((self._t("output_subtitle"), self.output_file.get()))
        missing = [name for name, value in required if not value.strip()]
        if not self._single_reference_path():
            missing.append(f"{self._t('video_file')} / {self._t('correct_subtitle')}")
        if missing:
            messagebox.showerror(APP_TITLE, "Nedostaje: " + ", ".join(missing))
            return False

        for name, value, minimum, maximum in [
            ("Split penalty", self.split_penalty.get(), 0.0, 1000.0),
            ("Interval", self.interval.get(), 1.0, None),
            ("Speed optimization", self.speed_optimization.get(), 0.0, None),
            ("FPS referenca", self.sub_fps_ref.get(), 0.0001, None),
            ("FPS titl", self.sub_fps_inc.get(), 0.0001, None),
        ]:
            try:
                parsed = float(value)
            except ValueError:
                messagebox.showerror(APP_TITLE, f"{name} mora biti broj.")
                return False
            if parsed < minimum or (maximum is not None and parsed > maximum):
                high = f" i najvise {maximum:g}" if maximum is not None else ""
                messagebox.showerror(APP_TITLE, f"{name} mora biti najmanje {minimum:g}{high}.")
                return False

        if self.audio_index.get().strip():
            try:
                if int(self.audio_index.get()) < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(APP_TITLE, "Audio index mora biti nenegativan cijeli broj.")
                return False
            if not self._supports_option("--index"):
                messagebox.showerror(
                    APP_TITLE,
                    "Odabrani alass binary ne podrzava --index. Polje Audio index ostavi prazno ili odaberi noviji binary.",
                )
                return False

        reference_suffix = Path(self._single_reference_path()).suffix.lower()
        if reference_suffix in VIDEO_EXTENSIONS:
            missing_tools = []
            if not self._tool_available(self.ffmpeg_path.get()):
                missing_tools.append("ffmpeg")
            if not self._tool_available(self.ffprobe_path.get()):
                missing_tools.append("ffprobe")
            if missing_tools:
                messagebox.showerror(
                    APP_TITLE,
                    "Za video referencu nedostaje: "
                    + ", ".join(missing_tools)
                    + ".\n\nDodaj alate u bin/ folder ili upisi pune putanje u FFmpeg polja.",
                )
                return False

        input_suffix = Path(self.incorrect_file.get()).suffix.lower()
        output_path = self._single_output_paths()[0] if self.single_output_mode.get() == "backup" else self.output_file.get()
        output_suffix = Path(output_path).suffix.lower()
        if input_suffix in SUBTITLE_EXTENSIONS and output_suffix != input_suffix:
            if not messagebox.askyesno(
                APP_TITLE,
                "Alass ne konvertira format titla. Izlaz obicno mora imati isti nastavak kao ulazni titl.\n\nNastaviti?",
            ):
                return False
        subtitle_checks = [
            (self.incorrect_file.get().strip(), self.encoding_inc.get().strip() or "auto"),
        ]
        reference = self._single_reference_path()
        if Path(reference).suffix.lower() == ".srt":
            subtitle_checks.append((reference, self.encoding_ref.get().strip() or "auto"))
        for subtitle_path, encoding in subtitle_checks:
            validation_error = self._validate_srt_file(subtitle_path, encoding)
            if validation_error:
                if self.repair_srt.get():
                    repair_summary = self._repair_srt_preview(subtitle_path, encoding)
                    if repair_summary:
                        continue
                    validation_error += "\n\nAutomatski popravak nije uspio za ovaj titl."
                messagebox.showerror(APP_TITLE, validation_error)
                return False
        return True

    def _validate_common_options(self) -> bool:
        old_values = (
            self.video_file.get(),
            self.correct_subtitle_file.get(),
            self.incorrect_file.get(),
            self.output_file.get(),
        )
        self.video_file.set("dummy.mp4")
        self.correct_subtitle_file.set("")
        self.incorrect_file.set("dummy.srt")
        self.output_file.set("dummy.srt")
        try:
            return self._validate()
        finally:
            self.video_file.set(old_values[0])
            self.correct_subtitle_file.set(old_values[1])
            self.incorrect_file.set(old_values[2])
            self.output_file.set(old_values[3])

    def _run_alass(self) -> None:
        if self.process is not None:
            return
        if not self._validate():
            return

        final_output, temp_output = self._single_output_paths()
        reference = self._single_reference_path()
        command = self._build_command_for(
            reference,
            self.incorrect_file.get().strip(),
            temp_output,
        )
        self.jobs = {
            "__single__": {
                "output_mode": self.single_output_mode.get(),
                "reference": reference,
                "video": self.video_file.get().strip(),
                "correct_subtitle": self.correct_subtitle_file.get().strip(),
                "incorrect": self.incorrect_file.get().strip(),
                "final_output": final_output,
                "temp_output": temp_output,
                "encoding": "auto",
                "status": "Ceka",
            }
        }
        env = os.environ.copy()
        env["ALASS_FFMPEG_PATH"] = self.ffmpeg_path.get().strip() or "ffmpeg"
        env["ALASS_FFPROBE_PATH"] = self.ffprobe_path.get().strip() or "ffprobe"

        self.active_log = "single"
        self._clear_log()
        self.job_results = []
        self.single_progress.set(0)
        self.status.set("Radi...")
        self.stop_requested = False
        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.batch_run_button.configure(state="disabled")

        self.worker = threading.Thread(target=self._worker_run, args=([("__single__", command)], env), daemon=True)
        self.worker.start()

    def _run_batch(self) -> None:
        if self.process is not None:
            return
        if not self.batch_folder.get().strip():
            messagebox.showerror(APP_TITLE, "Prvo odaberi folder.")
            return
        if not self.batch_items:
            self._scan_batch_folder()
        if not self.batch_items:
            messagebox.showerror(APP_TITLE, "Nema pronadenih parova film/titl u folderu.")
            return
        if not self._validate_common_options():
            return

        selected = [
            (iid, item)
            for iid, item in self.batch_items.items()
            if self.batch_mode.get() == "all" or bool(item["checked"])
        ]
        if not selected:
            messagebox.showerror(APP_TITLE, "Nema oznacenih stavki za sinkronizaciju.")
            return

        output_mode = self._resolve_batch_output_mode()
        if output_mode is None:
            return

        commands = []
        self.jobs = {}
        for iid, item in selected:
            item["status"] = "Ceka"
            final_output, temp_output = self._batch_output_paths(item, output_mode)
            item["output"] = final_output
            item["final_output"] = final_output
            item["temp_output"] = temp_output
            item["output_mode"] = output_mode
            item["encoding"] = "auto"
            self.jobs[iid] = dict(item)
            self._refresh_batch_row(iid)
            commands.append(
                (
                    iid,
                    self._build_command_for(
                        str(item["reference"]),
                        str(item["incorrect"]),
                        temp_output,
                    ),
                )
            )

        env = os.environ.copy()
        env["ALASS_FFMPEG_PATH"] = self.ffmpeg_path.get().strip() or "ffmpeg"
        env["ALASS_FFPROBE_PATH"] = self.ffprobe_path.get().strip() or "ffprobe"

        self.active_log = "batch"
        self._clear_log()
        self.job_results = []
        self.batch_current_progress.set(0)
        self.batch_total_progress.set(0)
        self.batch_current_label.set("Trenutni titl: 0%")
        self.batch_total_label.set("Ukupno: 0%")
        self.status.set(f"Radi folder: 0/{len(commands)}")
        self.stop_requested = False
        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.batch_run_button.configure(state="disabled")
        self.worker = threading.Thread(target=self._worker_run, args=(commands, env), daemon=True)
        self.worker.start()

    def _resolve_batch_output_mode(self) -> str | None:
        mode = self.batch_output_mode.get()
        if mode != "ask":
            return mode
        return self._ask_batch_output_mode()

    def _ask_batch_output_mode(self) -> str | None:
        dialog = tk.Toplevel(self)
        dialog.title("Spremanje prijevoda")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.configure(bg="#eef2f6")

        choice = tk.StringVar(value="")
        frame = ttk.Frame(dialog, padding=18)
        frame.grid(row=0, column=0, sticky="nsew")
        ttk.Label(frame, text="Kako zelis spremiti sinkronizirane titlove?", font=("DejaVu Sans", 11, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 14)
        )
        ttk.Button(
            frame,
            text="Ostavi original i dodaj .synced",
            command=lambda: self._close_choice_dialog(dialog, choice, "suffix"),
        ).grid(row=1, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(
            frame,
            text="Original u 'original prijevod'",
            command=lambda: self._close_choice_dialog(dialog, choice, "backup"),
        ).grid(row=1, column=1, sticky="ew", padx=(0, 8))
        ttk.Button(frame, text="Odustani", command=lambda: self._close_choice_dialog(dialog, choice, "")).grid(
            row=1, column=2, sticky="ew"
        )
        for column in range(3):
            frame.columnconfigure(column, weight=1)

        dialog.update_idletasks()
        x = self.winfo_rootx() + max(0, (self.winfo_width() - dialog.winfo_width()) // 2)
        y = self.winfo_rooty() + max(0, (self.winfo_height() - dialog.winfo_height()) // 2)
        dialog.geometry(f"+{x}+{y}")
        self.wait_window(dialog)
        return choice.get() or None

    def _close_choice_dialog(self, dialog: tk.Toplevel, choice: tk.StringVar, value: str) -> None:
        choice.set(value)
        dialog.destroy()

    def _batch_output_paths(self, item: dict[str, str | bool], output_mode: str) -> tuple[str, str]:
        incorrect = Path(str(item["incorrect"]))
        reference = Path(str(item["reference"]))
        if output_mode == "backup":
            final_output = reference.with_suffix(incorrect.suffix)
            temp_output = self._unique_path(final_output.with_name(f"{final_output.stem}.alass_tmp{final_output.suffix}"))
            return str(final_output), str(temp_output)
        output = self._suggest_output_path(str(incorrect))
        return output, output

    def _single_output_paths(self) -> tuple[str, str]:
        incorrect = Path(self.incorrect_file.get().strip())
        reference = Path(self._single_naming_reference_path())
        if self.single_output_mode.get() == "backup":
            final_output = reference.with_suffix(incorrect.suffix)
            temp_output = self._unique_path(final_output.with_name(f"{final_output.stem}.alass_tmp{final_output.suffix}"))
            return str(final_output), str(temp_output)
        output = self.output_file.get().strip() or self._suggest_output_path(str(incorrect))
        return output, output

    def _supports_option(self, option: str) -> bool:
        help_text = self._get_executable_help()
        return option in help_text

    def _get_executable_help(self) -> str:
        executable = self.alass_path.get().strip() or "alass"
        if executable in self.help_cache:
            return self.help_cache[executable]
        try:
            result = subprocess.run(
                [executable, "--help"],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=2,
            )
            help_text = result.stdout or ""
        except Exception:
            help_text = ""
        self.help_cache[executable] = help_text
        return help_text

    def _worker_run(self, commands: list[tuple[str | None, list[str]]], env: dict[str, str]) -> None:
        failures = 0
        stopped = False
        total = len(commands)
        repair_tmp = tempfile.TemporaryDirectory(prefix="alass_gui_srt_repair_")
        try:
            repair_dir = Path(repair_tmp.name)
            for index, (iid, command) in enumerate(commands, start=1):
                if self.stop_requested:
                    self.log_queue.put(("log", "\nBatch je prekinut.\n"))
                    stopped = True
                    break
                if iid is not None and iid != "__single__":
                    self.log_queue.put(("batch_total", f"{((index - 1) / total) * 100:.1f}"))
                if iid is not None and iid != "__single__":
                    self.log_queue.put(("batch_status", f"{iid}\tRadi"))
                    self.log_queue.put(("progress", f"Radi folder: {index}/{len(commands)}"))
                    self.log_queue.put(("percent", f"{iid}\t0"))
                else:
                    self.log_queue.put(("percent", "\t0"))
                self._mark_job(iid, status="Radi")
                self.log_queue.put(("log", f"Radim: {self._job_display_name(iid, command)}\n"))
                command, validation_error = self._prepare_job_subtitles(iid, command, repair_dir)
                if validation_error:
                    failures += 1
                    self._mark_job(iid, status="Greska SRT")
                    self._record_job_result(iid, "Greska SRT")
                    self.log_queue.put(("log", validation_error + "\n\n"))
                    if iid is not None and iid != "__single__":
                        self.log_queue.put(("batch_status", f"{iid}\tGreska SRT"))
                        self.log_queue.put(("batch_total", f"{(index / total) * 100:.1f}"))
                    continue
                return_code, output = self._run_process(command, env, iid)
                if return_code != 0 and self._should_retry_encoding(command, output):
                    for encoding in ENCODING_FALLBACKS:
                        if self.stop_requested:
                            break
                        retry_command = self._command_with_option(command, "--encoding-inc", encoding)
                        self._mark_job(iid, encoding=encoding)
                        self.log_queue.put(("log", f"Charset fallback: {encoding}\n"))
                        if iid is not None:
                            self.log_queue.put(("percent", f"{iid}\t0"))
                        else:
                            self.log_queue.put(("percent", "\t0"))
                        return_code, output = self._run_process(retry_command, env, iid)
                        if return_code == 0:
                            break
                if self.stop_requested:
                    if iid is not None and iid != "__single__":
                        self.log_queue.put(("batch_status", f"{iid}\tPrekinuto"))
                    stopped = True
                    break
                if return_code == 0:
                    if iid is not None and not self._post_process_output(iid):
                        return_code = 1
                        failures += 1
                        self._mark_job(iid, status="Greska backup")
                        self._record_job_result(iid, "Greska backup")
                        if iid != "__single__":
                            self.log_queue.put(("batch_status", f"{iid}\tGreska backup"))
                        continue
                    if iid is not None and iid != "__single__":
                        self.log_queue.put(("batch_status", f"{iid}\tGotovo"))
                    self.log_queue.put(("percent", f"{iid or ''}\t100"))
                    self._mark_job(iid, status="Gotovo")
                    self._record_job_result(iid, "Gotovo")
                    self.log_queue.put(("log", f"Gotovo: {self._job_display_name(iid, command)}\n\n"))
                else:
                    failures += 1
                    self._mark_job(iid, status=f"Greska {return_code}")
                    self._record_job_result(iid, f"Greska {return_code}")
                    if iid is not None and iid != "__single__":
                        self.log_queue.put(("batch_status", f"{iid}\tGreska {return_code}"))
                if iid is not None and iid != "__single__":
                    self.log_queue.put(("batch_total", f"{(index / total) * 100:.1f}"))
            self.log_queue.put(("summary", self._build_summary_text()))
            self.log_queue.put(("done", str(0 if failures == 0 and not stopped else 1)))
        except FileNotFoundError as exc:
            self.log_queue.put(("error", f"Program nije pronađen: {exc}\n"))
        except Exception as exc:  # noqa: BLE001 - GUI should surface unexpected launcher failures.
            self.log_queue.put(("error", f"Greska pri pokretanju: {exc}\n"))
        finally:
            repair_tmp.cleanup()

    def _post_process_output(self, iid: str) -> bool:
        item = self.jobs.get(iid) or self.batch_items.get(iid)
        if not item or item.get("output_mode") != "backup":
            return True

        original = Path(str(item["incorrect"]))
        temp_output = Path(str(item["temp_output"]))
        final_output = Path(str(item["final_output"]))
        backup_dir = original.parent / "original prijevod"

        try:
            backup_dir.mkdir(exist_ok=True)
            if original.exists():
                backup_path = self._unique_path(backup_dir / original.name)
                shutil.move(str(original), str(backup_path))
                self.log_queue.put(("log", f"Original premjesten u: {backup_path}\n"))
            if final_output.exists() and final_output != temp_output:
                backup_path = self._unique_path(backup_dir / final_output.name)
                shutil.move(str(final_output), str(backup_path))
                self.log_queue.put(("log", f"Postojeci finalni titl premjesten u: {backup_path}\n"))
            shutil.move(str(temp_output), str(final_output))
            self.log_queue.put(("log", f"Novi titl spremljen kao: {final_output}\n"))
            return True
        except Exception as exc:  # noqa: BLE001 - file operation errors must be visible in GUI.
            self.log_queue.put(("log", f"Greska pri spremanju/backupu: {exc}\n"))
            return False

    def _mark_job(self, iid: str | None, **updates: str) -> None:
        if iid is None:
            return
        item = self.jobs.get(iid)
        if not item:
            return
        item.update(updates)

    def _job_display_name(self, iid: str | None, command: list[str]) -> str:
        item = self.jobs.get(iid or "")
        if item:
            return Path(str(item["reference"])).name
        if len(command) > 1:
            return Path(command[1]).name
        return "titl"

    def _record_job_result(self, iid: str | None, status: str) -> None:
        item = self.jobs.get(iid or "")
        if not item:
            return
        self.job_results.append(
            {
                "status": status,
                "reference": str(item.get("reference", "")),
                "incorrect": str(item.get("incorrect", "")),
                "final_output": str(item.get("final_output", item.get("output", ""))),
                "output_mode": str(item.get("output_mode", "suffix")),
                "encoding": str(item.get("encoding", "auto")),
            }
        )

    def _build_summary_text(self) -> str:
        if not self.job_results:
            return "\nIzvjestaj: nema obradenih titlova.\n"

        ok_count = sum(1 for result in self.job_results if result["status"] == "Gotovo")
        fail_count = len(self.job_results) - ok_count
        lines = [
            "\nIzvjestaj",
            f"Ukupno: {len(self.job_results)} | Uspjelo: {ok_count} | Greske: {fail_count}",
            "",
        ]
        for index, result in enumerate(self.job_results, start=1):
            mode = "backup originala" if result["output_mode"] == "backup" else "novi .synced titl"
            lines.extend(
                [
                    f"{index}. {result['status']} - {Path(result['reference']).name}",
                    f"   Original titl: {Path(result['incorrect']).name}",
                    f"   Izlaz: {Path(result['final_output']).name}",
                    f"   Spremanje: {mode}",
                    f"   Encoding: {result['encoding']}",
                ]
            )
        return "\n".join(lines) + "\n"

    def _unique_path(self, path: Path) -> Path:
        if not path.exists():
            return path
        counter = 1
        while True:
            candidate = path.with_name(f"{path.stem}.{counter}{path.suffix}")
            if not candidate.exists():
                return candidate
            counter += 1

    def _run_process(self, command: list[str], env: dict[str, str], iid: str | None) -> tuple[int, str]:
        output_parts: list[str] = []
        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )
        assert self.process.stdout is not None
        buffer = ""
        while True:
            char = self.process.stdout.read(1)
            if char == "":
                break
            output_parts.append(char)
            if char not in {"\r", "\n"}:
                buffer += char
                continue
            self._handle_process_record(buffer, char, iid)
            buffer = ""
        if buffer:
            self._handle_process_record(buffer, "\n", iid)
        return_code = self.process.wait()
        self.process = None
        if return_code != 0:
            self.log_queue.put(("log", "Alass greska:\n" + self._compact_process_output("".join(output_parts)) + "\n\n"))
        return return_code, "".join(output_parts)

    def _handle_process_record(self, record: str, terminator: str, iid: str | None) -> None:
        if not record:
            return
        percent = self._extract_percent(record)
        if percent is not None:
            self.log_queue.put(("percent", f"{iid or ''}\t{percent:.1f}"))
        if percent is not None and (terminator == "\r" or self._is_progress_record(record)):
            return
        if percent is None and self._is_summary_record(record):
            self.log_queue.put(("log", record + ("\n" if terminator == "\n" else "")))

    def _is_summary_record(self, record: str) -> bool:
        wanted = ("shifted block", "failed", "error:")
        return any(token in record.lower() for token in wanted)

    def _is_progress_record(self, record: str) -> bool:
        return bool(PROGRESS_RECORD_RE.search(record))

    def _compact_process_output(self, output: str) -> str:
        lines = []
        for raw_line in output.replace("\r", "\n").splitlines():
            line = raw_line.strip()
            if not line or self._extract_percent(line) is not None or self._is_progress_record(line):
                continue
            lines.append(line)
        compact = "\n".join(lines[-8:]) if lines else "Nema dodatnih detalja."
        if "expected SubRip timespan line" in output:
            compact += (
                "\n\nSavjet: SRT datoteka ima pokvaren blok. Otvori titl u tekst editoru i provjeri liniju "
                "koju alass navodi; nakon broja bloka mora ici timestamp linija oblika "
                "00:00:01,000 --> 00:00:03,000."
            )
        return compact

    def _extract_percent(self, text: str) -> float | None:
        matches = PERCENT_RE.findall(text)
        if not matches:
            return None
        try:
            return min(100.0, max(0.0, float(matches[-1])))
        except ValueError:
            return None

    def _stop_alass(self) -> None:
        self.stop_requested = True
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            self._append_log("\nPrekidam proces...\n")

    def _drain_log_queue(self) -> None:
        try:
            while True:
                kind, payload = self.log_queue.get_nowait()
                if kind == "log" and payload is not None:
                    self._append_log(payload)
                elif kind == "done":
                    code = int(payload or "1")
                    self.status.set("Zavrseno" if code == 0 else f"Zavrsilo s greskom ({code})")
                    self._finish_process()
                elif kind == "progress" and payload is not None:
                    self.status.set(payload)
                elif kind == "percent" and payload is not None:
                    iid, value = payload.split("\t", 1)
                    self._update_progress(iid, float(value))
                elif kind == "batch_total" and payload is not None:
                    value = float(payload)
                    self.batch_total_progress.set(value)
                    self.batch_total_label.set(f"Ukupno: {value:.0f}%")
                elif kind == "summary" and payload is not None:
                    self._append_log(payload)
                elif kind == "update_path" and payload is not None:
                    self.alass_path.set(payload)
                    self.help_cache.clear()
                elif kind == "batch_status" and payload is not None:
                    iid, status = payload.split("\t", 1)
                    if iid in self.batch_items:
                        self.batch_items[iid]["status"] = status
                        self._refresh_batch_row(iid)
                elif kind == "error" and payload is not None:
                    self._append_log(payload)
                    self.status.set("Greska")
                    self._finish_process()
                elif kind == "update_info" and payload is not None:
                    self.active_log = "single"
                    self._append_log(payload + "\n")
                    self.status.set(self._t("ready"))
                    self.update_button.configure(state="normal")
        except queue.Empty:
            pass
        self.after(100, self._drain_log_queue)

    def _finish_process(self) -> None:
        self.process = None
        self.run_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.batch_run_button.configure(state="normal")

    def _append_log(self, text: str) -> None:
        widget = self._active_log_widget()
        widget.configure(state="normal")
        widget.insert("end", text)
        widget.see("end")
        widget.configure(state="disabled")

    def _clear_log(self) -> None:
        widget = self._active_log_widget()
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.configure(state="disabled")

    def _active_log_widget(self) -> tk.Text:
        return self.batch_log if self.active_log == "batch" else self.single_log

    def _update_progress(self, iid: str, value: float) -> None:
        if self.active_log == "batch" and iid:
            self.batch_current_progress.set(value)
            self.batch_current_label.set(f"Trenutni titl: {Path(iid).name} ({value:.0f}%)")
            if iid in self.batch_items and self.batch_items[iid]["status"] not in {"Gotovo", "Prekinuto"}:
                self.batch_items[iid]["status"] = f"{value:.0f}%"
                self._refresh_batch_row(iid)
        else:
            self.single_progress.set(value)
            self.status.set(f"Radi... {value:.0f}%")


HELP_TEXTS = {
    "en": """Alass GUI - quick help

About the program
This GUI uses the original open-source `alass` subtitle synchronizer from the internet project made by its author, available at:
https://github.com/kaegi/alass

The GUI is only a visual wrapper around that program. The portable package includes a local `bin/alass` executable and calls it with the options you choose.

What alass does
Alass synchronizes an incorrect subtitle against a reference video or a correct reference subtitle. It can fix a constant offset, cuts caused by different releases, and FPS-related timing differences.

Single file workflow
1. In Video, choose the video file for this subtitle. The video name does not have to match the subtitle name.
2. If you already have a synced subtitle for the same video, choose it in Correct subtitle. When this field is filled, alass uses it as the timing reference instead of the video audio.
3. In Subtitle to fix, choose the subtitle/translation that needs syncing.
4. If you choose the subtitle first and the video has the same name in the same folder, the GUI fills the Video field automatically. If no same-name video exists, it offers manual video selection.
5. Choose how subtitles should be saved.
6. Click Start sync.

Folder workflow
1. Open the Folder tab and load a folder.
2. Enable Include subfolders if videos and subtitles are inside nested folders.
3. The GUI first looks for same-name video/subtitle pairs in the same folder, for example Film.mkv and Film.srt. If there is no exact match, it tries the closest subtitle name.
4. Choose whether to sync all found pairs or only checked items.
5. Choose how subtitles should be saved.
6. Open folder opens the selected item's folder, or the loaded folder when nothing is selected.
7. Click Start sync.

Saving modes
Keep original and add .synced: original subtitles remain untouched and the synced subtitle is saved as name.synced.ext.
Move original to 'original prijevod': the old subtitle is moved into that folder, and the new subtitle is named like the video file.

Log and report
The GUI does not print every alass progress line. Progress is shown with progress bars, and the log shows important messages, errors, encoding fallback, and a final report.

Updates
The Check updates button asks GitHub for the latest kaegi/alass release. If a matching Windows or Linux release asset exists, the GUI can download it into local bin/ and keep a .bak backup of the previous binary.

Supported formats
Subtitles: .srt, .ssa, .ass, .idx and .sub.
The reference can be a subtitle or a common video file. Video references need ffmpeg and ffprobe.

Important options
Split penalty: controls how strongly alass avoids creating split segments. Useful values are usually 5 to 20. Default is 7.
No splits: uses one offset for the whole subtitle. Faster, but cannot fix releases with added or removed scenes.
Interval: smallest time step in milliseconds. Lower is more accurate, higher is faster. Default is 1.
Speed opt.: speeds up synchronization with a small possible accuracy cost. 0 disables it.
FPS reference / FPS subtitle: used for MicroDVD .sub files.
Encoding: leave auto if unsure. If alass reports a charset error, the GUI tries common fallbacks such as windows-1250.

Examples
Video as reference:
alass movie.mp4 bad.srt synced.srt

Subtitle as reference:
alass correct.ass bad.srt synced.srt
""",
    "hr": """Alass GUI - kratke upute

Sto program radi
Ovaj GUI koristi originalni open-source `alass` program za sinkronizaciju titlova s interneta, od autora projekta:
https://github.com/kaegi/alass

GUI je vizualni omotac oko tog programa. Portable paket ukljucuje lokalni `bin/alass` i poziva ga s opcijama koje odaberes.

Alass sinkronizira neispravan titl prema referentnom videu ili referentnom titlu. Moze ispraviti stalni vremenski pomak, rezove zbog reklama ili drugacije verzije filma, te razlike u FPS-u.

Osnovni postupak
1. U polju Video odaberi video datoteku za taj prijevod. Video i prijevod ne moraju imati isto ime.
2. Ako imas vec sinkroniziran prijevod za isti video, odaberi ga u polju Tocni prijevod. Kad je ovo polje popunjeno, alass koristi tocni prijevod kao vremensku referencu umjesto zvuka iz videa.
3. U polju Prijevod za popraviti odaberi titl/prijevod koji zelis ispraviti.
4. Ako prvo odaberes prijevod, a video istog imena postoji u istom folderu, GUI ce automatski popuniti polje Video. Ako takav video ne postoji, ponudit ce rucni izbor videa.
5. Provjeri Izlazni titl. Nastavak izlazne datoteke treba biti isti kao nastavak neispravnog titla jer alass ne konvertira format.
6. Odaberi nacin spremanja prijevoda. Mozes ostaviti original i napraviti ime.synced.ext, ili premjestiti original u folder "original prijevod" i novi titl nazvati isto kao video datoteku.
7. Klikni Pokreni sinkronizaciju.

Rad s cijelim folderom
1. Otvori tab Folder i klikni Ucitaj folder.
2. Ako zelis da GUI trazi i kroz podfoldere, ukljuci Ukljuci podfoldere prije skeniranja.
3. GUI trazi video datoteke i titlove. Najprije spaja datoteke s istim imenom u istom folderu, npr. Film.mkv i Film.srt. Ako nema tocno istog imena, pokusa naci najblizi titl po nazivu.
3. Odaberi Napravi sve pronadene parove ili Napravi samo oznacene checkboxom.
4. Odaberi nacin spremanja prijevoda. Mozes ostaviti original i napraviti ime.synced.ext, ili premjestiti original u folder "original prijevod" i novi titl nazvati isto kao video datoteku.
5. Checkbox u prvom stupcu ukljucuje ili iskljucuje pojedini film.
6. Gumb Otvori folder otvara folder odabrane stavke, ili ucitani folder ako nista nije odabrano.
7. Klikni Pokreni sinkronizaciju.

Log i izvjestaj
GUI vise ne ispisuje svaku progress liniju iz alassa. Progress se vidi kroz progress barove, a log prikazuje samo bitne poruke, greske, fallback encoding i zavrsni izvjestaj za svaki titl.

Update
Gumb Provjeri update pita GitHub za zadnji kaegi/alass release. Ako postoji odgovarajuci Windows ili Linux asset, GUI ga moze skinuti u lokalni bin/ folder i sacuvati .bak backup starog binaryja.

Podrzani formati
Referenca moze biti uobicajeni video format ako su instalirani ffmpeg i ffprobe. Referenca moze biti i titl.
Titlovi: .srt, .ssa, .ass, .idx i .sub. Izlaz zadrzava format neispravnog titla.

Najvaznije opcije
Split penalty: koliko algoritam izbjegava uvoditi nove rezove u titlu. Zadano je 7. Korisne vrijednosti su uglavnom 5 do 20. Vise vrijednosti uvode manje splitova, nize vrijednosti uvode vise splitova.
Bez splitova: koristi samo jedan vremenski pomak kroz cijeli titl. Brze je, ali ne popravlja verzije s izbacenim ili dodanim scenama.
Interval: najmanji vremenski korak u milisekundama. Manje je preciznije, vece je brze. Zadano je 1.
Speed opt.: ubrzava sinkronizaciju uz moguci mali gubitak tocnosti. 0 iskljucuje optimizaciju.
FPS referenca / FPS titl: koristi se za MicroDVD .sub datoteke koje vrijeme spremaju kao broj frameova.
Encoding ref. / Encoding titl: ostavi auto ako nisi siguran. GUI tada prvo ne salje encoding argumente i prepusta alassu autodetect. Ako alass javi charset gresku za titl, GUI automatski proba windows-1250, windows-1252, iso-8859-2, iso-8859-1 i utf-8.
Dopusti negativna vremena: po defaultu alass pomice negativne timestampove na pocetak datoteke. Ova opcija dopusta zapis negativnih vremena.
Iskljuci FPS guessing: iskljucuje automatsko trazenje razlike u framerateu izmedu reference i ulaznog titla.
Audio index: ako video ima vise audio trackova, ovdje mozes odabrati index koji alass treba koristiti.
Stat. tag: prosljeduje --statistics-required-tag i filtrira statisticki output po tagu, ako ga koristis.
Napomena za Audio index: instalirani alass 2.0.0 obicno ne podrzava --index. GUI ce javiti gresku ako popunis Audio index s binaryjem koji nema tu opciju.

FFmpeg
Za video referencu alass treba ffmpeg i ffprobe. Ako nisu u PATH-u, upisi pune putanje u polja ffmpeg i ffprobe.

Primjeri
Video kao referenca:
alass film.mp4 los_titl.srt ispravljeni_titl.srt

Titl kao referenca:
alass tocni_titl.ass los_titl.srt ispravljeni_titl.srt

Samo pomak bez splitova:
alass film.mp4 los_titl.srt ispravljeni_titl.srt --no-split
""",
}


if __name__ == "__main__":
    AlassGui().mainloop()
