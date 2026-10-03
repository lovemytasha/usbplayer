# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import platform
import threading
import random
import tkinter as tk
from tkinter import messagebox
import numpy as np
import psutil

try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False
    print("python-vlc not installed. Run: pip install python-vlc")

try:
    import soundcard as sc
    SOUNDCARD_AVAILABLE = True
except ImportError:
    SOUNDCARD_AVAILABLE = False
    print("soundcard not installed, real spectrum unavailable")

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    print("pystray/Pillow not installed, tray unavailable")

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False
    print("customtkinter not installed. Run: pip install customtkinter")

try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    WINREG_AVAILABLE = False

NUM_BARS = 16
FPS = 30
FFT_SIZE = 2048
SMOOTH = 0.6

MUSIC_EXTS = (
    '.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac',
    '.wma', '.ape', '.opus', '.aiff', '.aif', '.wv',
    '.alac', '.ac3', '.dts', '.mid', '.midi', '.amr',
    '.mp4', '.mkv', '.avi', '.mov', '.flv', '.webm',
)

AUTOSTART_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_NAME = "USBMusicPlayer"

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".usb_music_player")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "theme": "military",
    "lang": "zh_CN",
    "volume": 70,
    "mode": "sequence",
    "window_x": None,
    "window_y": None,
    "autostart": False,
    "show_boot": True,
}


def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            cfg = dict(DEFAULT_CONFIG)
            cfg.update(data)
            return cfg
    except Exception as e:
        print(f"config load error: {e}")
    return dict(DEFAULT_CONFIG)


def save_config(cfg):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"config save error: {e}")


CONFIG = load_config()

FORMAT_ITEMS = {
    "format_full": [
        "MP3 (.mp3)", "WAV (.wav)", "FLAC (.flac)",
        "OGG (.ogg)", "M4A (.m4a)", "AAC (.aac)",
        "WMA (.wma)", "APE (.ape)", "OPUS (.opus)",
        "AIFF (.aiff/.aif)", "WavPack (.wv)",
        "ALAC (.alac)", "AC3 (.ac3)", "DTS (.dts)",
        "MIDI (.mid/.midi)", "AMR (.amr)",
    ],
    "format_video": [
        "MP4 (.mp4)", "MKV (.mkv)", "AVI (.avi)",
        "MOV (.mov)", "FLV (.flv)", "WebM (.webm)",
    ],
}

LANGUAGES = {
    "zh_CN": {
        "name": "简体中文",
        "app_title": "U盘音乐播放器",
        "header_title": "U盘音乐播放器",
        "waiting_usb": "等待U盘",
        "no_play": "暂无播放",
        "insert_usb_hint": "插入U盘自动播放",
        "playing": "▶ 播放中",
        "paused": "⏸ 暂停",
        "stopped": "⏹ 停止",
        "track_info": "第 {idx}/{total} 首",
        "mode_sequence": "顺序播放",
        "mode_loop_all": "列表循环",
        "mode_loop_one": "单曲循环",
        "mode_shuffle": "随机播放",
        "format_dialog_title": "格式支持说明",
        "format_header": "支持的音频格式",
        "format_sub": "基于 VLC 后端，几乎支持所有主流格式",
        "format_full": "完全支持（VLC 原生解码）",
        "format_video": "视频音轨（仅播放声音）",
        "format_note": "视频文件（MP4/MKV 等）只播放其中的音轨",
        "close": "关闭",
        "cancel": "取消",
        "play": "播放",
        "autostart_label": "开机自动启动（最小化到托盘）",
        "autostart_title": "开机自启",
        "autostart_on_ask": "是否要让本程序开机时自动启动？\n\n开启后，每次开机程序会最小化到系统托盘，\n随时插入U盘都能自动检测播放。",
        "autostart_off_ask": "检测到已开启开机自启。\n\n是否要关闭开机自启？",
        "autostart_enabled": "已开启开机自启。\n下次开机会自动运行并缩到托盘。",
        "autostart_disabled": "已关闭开机自启。",
        "autostart_fail": "设置失败，请检查权限。",
        "notice": "提示",
        "error": "错误",
        "multi_usb_title": "检测到多个U盘",
        "multi_usb_sub": "请选择要播放的U盘",
        "select_usb": "选择U盘",
        "tray_show": "显示主窗口",
        "tray_pause": "暂停/继续",
        "tray_next": "下一首",
        "tray_quit": "退出",
        "tray_tip": "托盘已启用",
        "spectrum_real": "真实频谱",
        "spectrum_sim": "模拟律动",
        "viz_title": "🎵 律动",
        "viz_title_military": "▸ AUDIO_SPECTRUM",
        "format_btn": "📄  格式说明",
        "missing_vlc": "未安装 python-vlc。\n\n请运行:\n  pip install python-vlc",
        "missing_ctk": "未安装 customtkinter。\n\n请运行:\n  pip install customtkinter",
        "missing_dep_title": "缺少依赖",
        "boot_skip": "Press any key to skip",
    },
    "en_US": {
        "name": "English",
        "app_title": "USB Music Player",
        "header_title": "USB Music Player",
        "waiting_usb": "Waiting for USB",
        "no_play": "No track playing",
        "insert_usb_hint": "Insert USB to auto-play",
        "playing": "▶ Playing",
        "paused": "⏸ Paused",
        "stopped": "⏹ Stopped",
        "track_info": "Track {idx}/{total}",
        "mode_sequence": "Sequential",
        "mode_loop_all": "Loop All",
        "mode_loop_one": "Loop One",
        "mode_shuffle": "Shuffle",
        "format_dialog_title": "Format Support",
        "format_header": "Supported Audio Formats",
        "format_sub": "Powered by VLC, supports almost all formats",
        "format_full": "Fully Supported (VLC native)",
        "format_video": "Video Tracks (audio only)",
        "format_note": "Video files (MP4/MKV etc.) play audio only",
        "close": "Close",
        "cancel": "Cancel",
        "play": "Play",
        "autostart_label": "Auto-start on boot (minimize to tray)",
        "autostart_title": "Auto-start",
        "autostart_on_ask": "Enable auto-start on boot?\n\nThe app will minimize to tray on startup,\nand auto-play music whenever a USB is inserted.",
        "autostart_off_ask": "Auto-start is enabled.\n\nDisable it?",
        "autostart_enabled": "Auto-start enabled.\nIt will run on next boot.",
        "autostart_disabled": "Auto-start disabled.",
        "autostart_fail": "Failed to set. Check permissions.",
        "notice": "Notice",
        "error": "Error",
        "multi_usb_title": "Multiple USB Drives Detected",
        "multi_usb_sub": "Please select a drive to play",
        "select_usb": "Select USB",
        "tray_show": "Show Window",
        "tray_pause": "Play/Pause",
        "tray_next": "Next Track",
        "tray_quit": "Quit",
        "tray_tip": "Tray enabled",
        "spectrum_real": "Real Spectrum",
        "spectrum_sim": "Simulated",
        "viz_title": "🎵 Visualizer",
        "viz_title_military": "▸ AUDIO_SPECTRUM",
        "format_btn": "📄  Formats",
        "missing_vlc": "python-vlc not installed.\n\nRun:\n  pip install python-vlc",
        "missing_ctk": "customtkinter not installed.\n\nRun:\n  pip install customtkinter",
        "missing_dep_title": "Missing Dependency",
        "boot_skip": "Press any key to skip",
    },
}

CURRENT_LANG = CONFIG.get("lang", "zh_CN")


def tr(key, **kwargs):
    lang = LANGUAGES.get(CURRENT_LANG, LANGUAGES["zh_CN"])
    text = lang.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


THEMES = {
    "military": {
        "name": "战术HUD",
        "bg_main": "#060a08",
        "bg_card": "#0c1410",
        "bg_card_hover": "#132019",
        "bg_input": "#0a110d",
        "accent": "#00ff88",
        "accent_hover": "#33ffa3",
        "accent_dim": "#0a4d2e",
        "text_main": "#c8f0d8",
        "text_sub": "#4a7a5c",
        "text_dim": "#2a4436",
        "danger": "#ff4757",
        "highlight": "#00ff88",
        "font_family": "Consolas",
        "font_size_title": 16,
        "font_size_main": 13,
        "font_size_small": 11,
        "font_size_tiny": 10,
        "corner": 4,
        "border_width": 1,
        "border_color": "#0f3a22",
        "bar_colors": ["#0a4d2e", "#0d6640", "#00a854",
                       "#00cc6a", "#00e87a", "#00ff88"],
        "prefix_icon": "▸",
        "header_title": "SYS://USB_AUDIO_TERMINAL",
    },
    "system": {
        "name": "系统风格",
        "bg_main": ("#f5f5f7", "#0f0f17"),
        "bg_card": ("#ffffff", "#1e1e2e"),
        "bg_card_hover": ("#f0f0f2", "#26263a"),
        "bg_input": ("#e8e8ec", "#2a2a3d"),
        "accent": ("#0078d4", "#7c9cff"),
        "accent_hover": ("#0068b8", "#6b8bf0"),
        "accent_dim": ("#cce4f7", "#3a4a7a"),
        "text_main": ("#1c1c1e", "#e4e6f0"),
        "text_sub": ("#6e6e73", "#8b8fa3"),
        "text_dim": ("#a0a0a5", "#5a5a6d"),
        "danger": ("#d13438", "#f38ba8"),
        "highlight": ("#0078d4", "#f5c2e7"),
        "font_family": "Microsoft YaHei UI",
        "font_size_title": 20,
        "font_size_main": 13,
        "font_size_small": 11,
        "font_size_tiny": 10,
        "corner": 12,
        "border_width": 0,
        "border_color": None,
        "bar_colors": ["#5a7dc9", "#6b8bf0", "#7c9cff",
                       "#9b9cf5", "#bda6f0", "#dda8e8"],
        "prefix_icon": "",
        "header_title": "",
    },
}

CURRENT_THEME = CONFIG.get("theme", "military")


def get_theme():
    return THEMES[CURRENT_THEME]


def resolve_color(color):
    if isinstance(color, tuple):
        mode = ctk.get_appearance_mode()
        return color[1] if mode == "Dark" else color[0]
    return color


def theme_font(size_key="font_size_main", bold=False):
    t = get_theme()
    return ctk.CTkFont(
        family=t["font_family"],
        size=t[size_key],
        weight="bold" if bold else "normal"
    )


def format_time(ms):
    if ms is None or ms < 0:
        return "00:00"
    s = ms // 1000
    return f"{s // 60:02d}:{s % 60:02d}"


def get_exe_path():
    if getattr(sys, 'frozen', False):
        return sys.executable
    return os.path.abspath(sys.argv[0])


def is_autostart_enabled():
    if not WINREG_AVAILABLE or platform.system() != "Windows":
        return False
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY,
                             0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, AUTOSTART_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception:
        return False


def set_autostart(enable):
    if not WINREG_AVAILABLE or platform.system() != "Windows":
        return False
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY,
                             0, winreg.KEY_SET_VALUE)
        if enable:
            winreg.SetValueEx(key, AUTOSTART_NAME, 0, winreg.REG_SZ,
                              f'"{get_exe_path()}"')
        else:
            try:
                winreg.DeleteValue(key, AUTOSTART_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"autostart error: {e}")
        return False


def ask_autostart_confirm(parent):
    if not WINREG_AVAILABLE or platform.system() != "Windows":
        return
    if is_autostart_enabled():
        ans = messagebox.askyesno(
            tr("autostart_title"), tr("autostart_off_ask"), parent=parent)
        if ans:
            set_autostart(False)
            CONFIG["autostart"] = False
            save_config(CONFIG)
            messagebox.showinfo(tr("notice"), tr("autostart_disabled"),
                                parent=parent)
        return
    ans = messagebox.askyesno(
        tr("autostart_title"), tr("autostart_on_ask"), parent=parent)
    if ans:
        if set_autostart(True):
            CONFIG["autostart"] = True
            save_config(CONFIG)
            messagebox.showinfo(tr("notice"), tr("autostart_enabled"),
                                parent=parent)
        else:
            messagebox.showerror(tr("error"), tr("autostart_fail"),
                                 parent=parent)


class BootSplash:
    def __init__(self, root, on_finish):
        self.root = root
        self.on_finish = on_finish
        self.finished = False
        self._after_ids = []

        self.bg = "#060a08"
        self.accent = "#00ff88"
        self.dim = "#0a4d2e"
        self.text = "#c8f0d8"

        self._w = 520
        self._h = 760
        self._scan_y = 60
        self._scan_dir = 1
        self.line_y = []

        self.frame = tk.Frame(root, bg=self.bg)
        self.frame.place(x=0, y=0, relwidth=1, relheight=1)

        self.canvas = tk.Canvas(self.frame, bg=self.bg,
                                highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.root.bind("<Key>", lambda e: self._skip())
        self.frame.bind("<Button-1>", lambda e: self._skip())

        self._after(150, self._init_draw)

    def _after(self, ms, fn):
        aid = self.root.after(ms, fn)
        self._after_ids.append(aid)
        return aid

    def _init_draw(self):
        self._draw_all()
        self._start_animations()

    def _draw_all(self):
        self.canvas.update_idletasks()
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100 or h < 100:
            w, h = 520, 760

        self._w = w
        self._h = h

        self.canvas.delete("all")

        for i in range(0, w + 30, 30):
            self.canvas.create_line(i, 0, i, h, fill="#0a1208", width=1)
        for j in range(0, h + 30, 30):
            self.canvas.create_line(0, j, w, j, fill="#0a1208", width=1)

        self.canvas.create_rectangle(8, 8, w - 8, h - 8,
                                     outline=self.dim, width=1)
        self.canvas.create_line(8, 8, 8, 30, fill=self.accent, width=2)
        self.canvas.create_line(8, 8, 30, 8, fill=self.accent, width=2)
        self.canvas.create_line(w - 8, 8, w - 8, 30, fill=self.accent, width=2)
        self.canvas.create_line(w - 8, 8, w - 30, 8, fill=self.accent, width=2)
        self.canvas.create_line(8, h - 8, 8, h - 30, fill=self.accent, width=2)
        self.canvas.create_line(8, h - 8, 30, h - 8, fill=self.accent, width=2)
        self.canvas.create_line(w - 8, h - 8, w - 8, h - 30, fill=self.accent, width=2)
        self.canvas.create_line(w - 8, h - 8, w - 30, h - 8, fill=self.accent, width=2)

        self.canvas.create_text(
            30, 30, anchor="nw",
            text="SYS://USB_AUDIO_TERMINAL",
            fill=self.accent,
            font=("Consolas", 15, "bold"))
        self.canvas.create_text(
            w - 30, 32, anchor="ne",
            text="v1.0.0",
            fill=self.dim,
            font=("Consolas", 9))
        self.canvas.create_line(30, 56, w - 30, 56, fill=self.dim, width=1)

        self.scan_line_id = self.canvas.create_line(
            20, 60, w - 20, 60, fill=self.accent, width=1)

        self.progress_bg = self.canvas.create_rectangle(
            30, h - 60, w - 30, h - 44,
            fill="#0a110d", outline=self.dim, width=1)
        self.progress_bar = self.canvas.create_rectangle(
            32, h - 58, 32, h - 46,
            fill=self.accent, outline="")
        self.progress_text = self.canvas.create_text(
            w // 2, h - 52, text="0%",
            fill=self.text, font=("Consolas", 9, "bold"))

        self.cursor_id = self.canvas.create_rectangle(
            30, h - 30, 40, h - 20, fill=self.accent, outline="")

        self.canvas.create_text(
            w - 30, h - 30, anchor="se",
            text=tr("boot_skip"),
            fill=self.dim,
            font=("Consolas", 8))

    def _start_animations(self):
        self._blink_cursor()
        self._animate_scan()
        self.lines = [
            ("[BOOT]", "Initializing audio subsystem"),
            ("[BOOT]", "Loading VLC core"),
            ("[BOOT]", "Mounting USB watcher"),
            ("[BOOT]", "Calibrating spectrum engine"),
            ("[BOOT]", "Starting tray service"),
            ("[ OK ]", "System ready"),
        ]
        self._animate_lines(0)

    def _blink_cursor(self):
        if self.finished:
            return
        try:
            state = self.canvas.itemcget(self.cursor_id, "fill")
            new = self.bg if state == self.accent else self.accent
            self.canvas.itemconfig(self.cursor_id, fill=new)
        except Exception:
            return
        self._after(500, self._blink_cursor)

    def _animate_scan(self):
        if self.finished:
            return
        try:
            self._scan_y += self._scan_dir * 3
            limit_low = 60
            limit_high = self._h - 120
            if self._scan_y >= limit_high or self._scan_y <= limit_low:
                self._scan_dir *= -1
            self.canvas.coords(self.scan_line_id,
                               20, self._scan_y,
                               self._w - 20, self._scan_y)
            color = self.accent if self._scan_dir > 0 else self.dim
            self.canvas.itemconfig(self.scan_line_id, fill=color)
        except Exception:
            return
        self._after(30, self._animate_scan)

    def _animate_lines(self, idx):
        if self.finished:
            return
        if idx >= len(self.lines):
            self._animate_progress(0)
            return

        tag, msg = self.lines[idx]
        y = 90 + idx * 30
        self.line_y.append(y)

        self.canvas.create_text(
            30, y, anchor="nw", text=tag,
            fill=self.accent,
            font=("Consolas", 10, "bold"))
        text_id = self.canvas.create_text(
            110, y, anchor="nw", text="",
            fill=self.text,
            font=("Consolas", 10))

        self._type_text(text_id, msg, 0, idx)

    def _type_text(self, text_id, full_text, pos, line_idx):
        if self.finished:
            return
        if pos <= len(full_text):
            self.canvas.itemconfig(text_id, text=full_text[:pos])
            self._after(14, lambda: self._type_text(
                text_id, full_text, pos + 1, line_idx))
        else:
            self.canvas.create_text(
                self._w - 20, self.line_y[line_idx], anchor="ne",
                text="✓",
                fill=self.accent,
                font=("Consolas", 11, "bold"))
            self._after(100, lambda: self._animate_lines(line_idx + 1))

    def _animate_progress(self, val):
        if self.finished:
            return
        if val > 100:
            self.canvas.create_text(
                self._w // 2, self._h - 80, anchor="center",
                text="► ALL SYSTEMS NOMINAL",
                fill=self.accent,
                font=("Consolas", 11, "bold"))
            self._after(400, self._fade_out)
            return

        bar_right = 32 + (self._w - 30 - 32) * val / 100
        self.canvas.coords(self.progress_bar,
                           32, self._h - 58,
                           bar_right, self._h - 46)
        self.canvas.itemconfig(self.progress_text, text=f"{val}%")

        step = random.randint(2, 7)
        self._after(30, lambda: self._animate_progress(val + step))

    def _fade_out(self):
        if self.finished:
            return
        try:
            alpha = self.root.attributes("-alpha")
        except Exception:
            alpha = 1.0
        alpha -= 0.1
        if alpha <= 0:
            self._finish()
            return
        try:
            self.root.attributes("-alpha", alpha)
        except Exception:
            self._finish()
            return
        self._after(30, self._fade_out)

    def _skip(self):
        if not self.finished:
            self._finish()

    def _finish(self):
        if self.finished:
            return
        self.finished = True

        for aid in self._after_ids:
            try:
                self.root.after_cancel(aid)
            except Exception:
                pass
        self._after_ids = []

        try:
            self.root.unbind("<Key>")
        except Exception:
            pass

        try:
            self.frame.destroy()
        except Exception:
            pass

        if self.on_finish:
            self.on_finish()


class USBWatcher:
    def __init__(self):
        self.system = platform.system()
        self._last_seen = self.get_drives()
        self._pending = set(self._last_seen)

    def get_drives(self):
        drives = set()
        if self.system == "Windows":
            for partition in psutil.disk_partitions():
                if 'cdrom' in partition.opts:
                    continue
                if 'removable' in partition.opts:
                    drives.add(partition.device)
        elif self.system == "Linux":
            for base in ['/media', '/mnt', '/run/media']:
                if os.path.exists(base):
                    for user_dir in os.listdir(base):
                        path = os.path.join(base, user_dir)
                        if os.path.isdir(path):
                            drives.add(path)
        elif self.system == "Darwin":
            if os.path.exists('/Volumes'):
                for vol in os.listdir('/Volumes'):
                    path = os.path.join('/Volumes', vol)
                    if os.path.ismount(path):
                        drives.add(path)
        return drives

    def check(self):
        current = self.get_drives()
        new = current - self._last_seen
        removed = self._last_seen - current
        self._last_seen = current
        return new, removed

    def pop_pending(self):
        p = set(self._pending)
        self._pending = set()
        return p


class SpectrumCapture:
    def __init__(self, num_bars=NUM_BARS):
        self.num_bars = num_bars
        self.spectrum = np.zeros(num_bars, dtype=float)
        self.lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._enabled = SOUNDCARD_AVAILABLE
        self._window = np.hanning(FFT_SIZE)
        self._bin_edges = self._make_bin_edges()

    def _make_bin_edges(self):
        return np.logspace(np.log10(20), np.log10(16000), self.num_bars + 1)

    def _freq_to_bin(self, freq, sample_rate):
        return int(freq / (sample_rate / 2) * (FFT_SIZE // 2))

    def start(self):
        if not self._enabled:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        try:
            speaker = sc.default_speaker()
            if speaker is None:
                raise RuntimeError("no speaker")
            mic = None
            try:
                mic = sc.get_microphone(id=str(speaker.name),
                                        include_loopback=True)
            except Exception:
                mic = None
            if mic is None:
                mic = sc.default_microphone()

            with mic.recorder(samplerate=44100, channels=2) as rec:
                while not self._stop.is_set():
                    data = rec.record(numframes=FFT_SIZE)
                    if data.ndim > 1:
                        data = data.mean(axis=1)
                    fft = np.abs(np.fft.rfft(data * self._window))
                    fft = fft / (np.max(fft) + 1e-9)
                    sample_rate = 44100
                    bars = []
                    for i in range(self.num_bars):
                        f_lo = self._bin_edges[i]
                        f_hi = self._bin_edges[i + 1]
                        b_lo = max(1, self._freq_to_bin(f_lo, sample_rate))
                        b_hi = max(b_lo + 1,
                                   self._freq_to_bin(f_hi, sample_rate))
                        b_hi = min(b_hi, len(fft))
                        if b_lo >= len(fft):
                            bars.append(0.0)
                            continue
                        val = float(np.mean(fft[b_lo:b_hi]))
                        bars.append(min(1.0, val * 3.0))
                    with self.lock:
                        self.spectrum = (SMOOTH * np.array(bars)
                                         + (1 - SMOOTH) * self.spectrum)
        except Exception as e:
            print(f"spectrum error: {e}")
            self._enabled = False

    def get(self):
        with self.lock:
            return self.spectrum.copy()

    @property
    def enabled(self):
        return self._enabled and SOUNDCARD_AVAILABLE


class MusicPlayer:
    MODES = ["sequence", "loop_all", "loop_one", "shuffle"]

    def __init__(self):
        if not VLC_AVAILABLE:
            raise RuntimeError("python-vlc not installed")
        self.instance = vlc.Instance("--no-video", "--quiet")
        self.player = self.instance.media_player_new()

        self.playlist = []
        self.current_index = 0
        self.playing = False
        self.paused = False
        self.mode = CONFIG.get("mode", "sequence")
        if self.mode not in self.MODES:
            self.mode = "sequence"
        self.volume = int(CONFIG.get("volume", 70))
        self.player.audio_set_volume(self.volume)
        self.lock = threading.Lock()

        self.spectrum_cap = SpectrumCapture(NUM_BARS)
        self.spectrum_cap.start()
        self._sim_phase = 0.0

        self.on_state_change = None

    def mode_display(self):
        return tr(f"mode_{self.mode}")

    def _notify(self):
        if self.on_state_change:
            try:
                self.on_state_change()
            except Exception:
                pass

    def find_music(self, folder):
        result = []
        for root, _, files in os.walk(folder):
            for f in files:
                if f.lower().endswith(MUSIC_EXTS):
                    result.append(os.path.join(root, f))
        return result

    def play_from(self, drive):
        with self.lock:
            self.playlist = self.find_music(drive)
            if not self.playlist:
                print(f"{drive}: no audio files")
                self._notify()
                return
            print(f"found {len(self.playlist)} files")
            self.current_index = 0
            self._play_current()

    def _play_current(self):
        if not self.playlist:
            return
        if self.current_index >= len(self.playlist):
            self.current_index = 0
        path = self.playlist[self.current_index]
        print(f"play [{self.current_index + 1}/{len(self.playlist)}] "
              f"[{self.mode}]: {os.path.basename(path)}")
        try:
            media = self.instance.media_new(path)
            self.player.set_media(media)
            self.player.audio_set_volume(self.volume)
            self.player.play()
            self.playing = True
            self.paused = False
        except Exception as e:
            print(f"play failed: {e}")
            self._advance(skip_error=True)
            return
        self._notify()

    def get_spectrum(self):
        if self.spectrum_cap.enabled:
            return self.spectrum_cap.get()
        if self.playing and not self.paused:
            self._sim_phase += 0.15
            bars = []
            for i in range(NUM_BARS):
                base = 0.5 + 0.5 * np.sin(self._sim_phase + i * 0.5)
                noise = random.uniform(0.3, 1.0)
                val = base * noise * (1.0 - i / NUM_BARS * 0.6)
                bars.append(max(0.0, min(1.0, val)))
            return np.array(bars)
        return np.zeros(NUM_BARS, dtype=float)

    def stop_spectrum(self):
        self.spectrum_cap.stop()

    def get_time_ms(self):
        try:
            t = self.player.get_time()
            return t if t and t > 0 else 0
        except Exception:
            return 0

    def get_length_ms(self):
        try:
            l = self.player.get_length()
            return l if l and l > 0 else 0
        except Exception:
            return 0

    def seek(self, ms):
        try:
            self.player.set_time(int(ms))
        except Exception as e:
            print(f"seek failed: {e}")

    def _advance(self, skip_error=False):
        if not self.playlist:
            return
        if self.mode == "loop_one" and not skip_error:
            self._play_current()
            return
        if self.mode == "shuffle":
            if len(self.playlist) == 1:
                self._play_current()
                return
            new_index = self.current_index
            while new_index == self.current_index:
                new_index = random.randint(0, len(self.playlist) - 1)
            self.current_index = new_index
            self._play_current()
            return

        self.current_index += 1
        if self.current_index >= len(self.playlist):
            if self.mode == "loop_all":
                self.current_index = 0
                self._play_current()
            else:
                print("playlist finished")
                self.playing = False
                self.paused = False
                self._notify()
        else:
            self._play_current()

    def next(self):
        with self.lock:
            if not self.playlist:
                return
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self._play_current()

    def prev(self):
        with self.lock:
            if not self.playlist:
                return
            if self.get_time_ms() > 3000:
                self._play_current()
                return
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self._play_current()

    def toggle_pause(self):
        with self.lock:
            if not self.playing:
                return
            if self.paused:
                self.player.play()
                self.paused = False
            else:
                self.player.pause()
                self.paused = True
            self._notify()

    def stop(self):
        with self.lock:
            self.player.stop()
            self.playing = False
            self.paused = False
            self.playlist = []
            self.current_index = 0
            self._notify()

    def switch_mode(self):
        with self.lock:
            idx = self.MODES.index(self.mode)
            self.mode = self.MODES[(idx + 1) % len(self.MODES)]
            CONFIG["mode"] = self.mode
            save_config(CONFIG)
            self._notify()

    def set_volume(self, value):
        with self.lock:
            self.volume = int(max(0, min(100, value * 100)))
            self.player.audio_set_volume(self.volume)
            CONFIG["volume"] = self.volume
            save_config(CONFIG)
            self._notify()

    def update(self):
        if not self.playing or self.paused:
            return
        state = self.player.get_state()
        if state in (vlc.State.Ended, vlc.State.Error):
            with self.lock:
                self._advance(skip_error=(state == vlc.State.Error))


class PlayerGUI:
    def __init__(self, player):
        self.player = player
        self.root = ctk.CTk()
        self.root.resizable(False, False)
        self.root.geometry("520x760")

        player.on_state_change = self.refresh

        self._seeking = False
        self.tray = None
        self._viz_anim_id = None
        self._viz_bars = []
        self._viz_height = 80

        self.autostart_var = None
        self.volume_var = None
        self.progress_var = None
        self.time_cur_var = None
        self.time_total_var = None
        self.mode_var = None

        self._restore_window_position()
        self._build_ui()

        self.tray = TrayIcon(player, self)
        self.tray.start()

        self._tick_progress()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close_to_tray)

    def _restore_window_position(self):
        wx = CONFIG.get("window_x")
        wy = CONFIG.get("window_y")
        if wx is not None and wy is not None:
            try:
                self.root.geometry(f"520x760+{int(wx)}+{int(wy)}")
            except Exception:
                pass

    def _save_window_position(self):
        try:
            CONFIG["window_x"] = self.root.winfo_x()
            CONFIG["window_y"] = self.root.winfo_y()
            save_config(CONFIG)
        except Exception:
            pass

    def _build_ui(self):
        t = get_theme()
        self.root.title(tr("app_title"))
        self.root.configure(fg_color=resolve_color(t["bg_main"]))

        for w in self.root.winfo_children():
            w.destroy()

        header = ctk.CTkFrame(self.root, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(18, 8))

        if CURRENT_THEME == "military":
            title_text = t["header_title"]
            ctk.CTkLabel(header, text=title_text,
                         font=ctk.CTkFont(family=t["font_family"],
                                          size=t["font_size_title"],
                                          weight="bold"),
                         text_color=resolve_color(t["accent"])).pack(side="left")
        else:
            ctk.CTkLabel(header, text=tr("header_title"),
                         font=theme_font("font_size_title", bold=True),
                         text_color=resolve_color(t["text_main"])).pack(side="left")

        theme_btn = ctk.CTkButton(
            header, text="⇄", width=36, height=32,
            corner_radius=t["corner"],
            font=theme_font("font_size_main"),
            fg_color=resolve_color(t["bg_card"]),
            hover_color=resolve_color(t["bg_card_hover"]),
            text_color=resolve_color(t["accent"]),
            border_width=t["border_width"],
            border_color=resolve_color(t["border_color"])
            if t["border_color"] else None,
            command=self.toggle_theme)
        theme_btn.pack(side="right", padx=(6, 0))

        lang_menu = ctk.CTkOptionMenu(
            header,
            values=[LANGUAGES[k]["name"] for k in LANGUAGES],
            command=self.on_lang_changed,
            width=100, height=32,
            corner_radius=t["corner"],
            font=theme_font("font_size_small"),
            fg_color=resolve_color(t["bg_card"]),
            button_color=resolve_color(t["bg_card"]),
            button_hover_color=resolve_color(t["bg_card_hover"]),
            text_color=resolve_color(t["accent"]),
            dropdown_fg_color=resolve_color(t["bg_card"]),
            dropdown_text_color=resolve_color(t["text_main"]))
        lang_menu.set(LANGUAGES[CURRENT_LANG]["name"])
        lang_menu.pack(side="right", padx=(6, 0))

        self.state_dot = ctk.CTkLabel(
            header, text=tr("waiting_usb"),
            font=theme_font("font_size_small"),
            text_color=resolve_color(t["text_sub"]))
        self.state_dot.pack(side="right")

        if CURRENT_THEME == "military":
            scan_line = ctk.CTkFrame(
                self.root, fg_color=resolve_color(t["accent_dim"]),
                height=1, corner_radius=0)
            scan_line.pack(fill="x", padx=20, pady=(0, 4))
            status_bar = ctk.CTkFrame(self.root, fg_color="transparent")
            status_bar.pack(fill="x", padx=24, pady=(0, 6))
            ctk.CTkLabel(status_bar,
                         text="[SYS]  ● ACTIVE   //   VLC_CORE   //   SCAN: 0.5s",
                         font=ctk.CTkFont(family=t["font_family"], size=9),
                         text_color=resolve_color(t["text_dim"])).pack(side="left")

        card = ctk.CTkFrame(self.root,
                            fg_color=resolve_color(t["bg_card"]),
                            corner_radius=t["corner"],
                            border_width=t["border_width"],
                            border_color=resolve_color(t["border_color"])
                            if t["border_color"] else None)
        card.pack(fill="x", padx=20, pady=8)

        self.song_title = ctk.CTkLabel(
            card, text=tr("no_play"),
            font=theme_font("font_size_main", bold=True),
            text_color=resolve_color(t["text_main"]), anchor="w")
        self.song_title.pack(fill="x", padx=18, pady=(16, 2))

        self.song_meta = ctk.CTkLabel(
            card, text=tr("insert_usb_hint"),
            font=theme_font("font_size_small"),
            text_color=resolve_color(t["text_sub"]), anchor="w")
        self.song_meta.pack(fill="x", padx=18, pady=(0, 12))

        self.time_cur_var = tk.StringVar(value="00:00")
        self.time_total_var = tk.StringVar(value="00:00")

        prog_row = ctk.CTkFrame(card, fg_color="transparent")
        prog_row.pack(fill="x", padx=18, pady=(0, 16))

        ctk.CTkLabel(prog_row, textvariable=self.time_cur_var,
                     font=ctk.CTkFont(family=t["font_family"], size=11),
                     text_color=resolve_color(t["text_sub"]),
                     width=42).pack(side="left")

        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ctk.CTkSlider(
            prog_row, from_=0, to=1000, variable=self.progress_var,
            command=self.on_progress_drag,
            button_color=resolve_color(t["accent"]),
            button_hover_color=resolve_color(t["accent_hover"]),
            progress_color=resolve_color(t["accent"]),
            fg_color=resolve_color(t["bg_input"]),
            height=16)
        self.progress.pack(side="left", fill="x", expand=True, padx=8)
        self.progress.bind("<ButtonPress-1>", self._on_seek_start)
        self.progress.bind("<ButtonRelease-1>", self._on_seek_end)

        ctk.CTkLabel(prog_row, textvariable=self.time_total_var,
                     font=ctk.CTkFont(family=t["font_family"], size=11),
                     text_color=resolve_color(t["text_sub"]),
                     width=42).pack(side="left")

        ctrl = ctk.CTkFrame(self.root, fg_color="transparent")
        ctrl.pack(pady=(14, 8))

        btn_cfg = {
            "width": 70, "height": 46,
            "corner_radius": t["corner"],
            "font": theme_font("font_size_title", bold=True),
            "fg_color": resolve_color(t["bg_card"]),
            "hover_color": resolve_color(t["bg_card_hover"]),
            "text_color": resolve_color(t["text_main"]),
            "border_width": t["border_width"],
            "border_color": resolve_color(t["border_color"])
            if t["border_color"] else None,
        }

        ctk.CTkButton(ctrl, text="⏮", command=self.player.prev,
                      **btn_cfg).grid(row=0, column=0, padx=5)

        self.pause_btn = ctk.CTkButton(
            ctrl, text="▶", command=self.on_pause,
            width=70, height=46, corner_radius=t["corner"],
            font=theme_font("font_size_title", bold=True),
            fg_color=resolve_color(t["accent"]),
            hover_color=resolve_color(t["accent_hover"]),
            text_color="#060a08" if CURRENT_THEME == "military" else "#ffffff")
        self.pause_btn.grid(row=0, column=1, padx=5)

        ctk.CTkButton(ctrl, text="⏭", command=self.player.next,
                      **btn_cfg).grid(row=0, column=2, padx=5)

        ctk.CTkButton(ctrl, text="🔁", command=self.player.switch_mode,
                      **btn_cfg).grid(row=0, column=3, padx=5)

        self.mode_var = tk.StringVar(value=self.player.mode_display())
        ctk.CTkLabel(self.root, textvariable=self.mode_var,
                     font=theme_font("font_size_small"),
                     text_color=resolve_color(t["text_sub"])).pack(pady=(0, 4))

        vol_frame = ctk.CTkFrame(self.root,
                                 fg_color=resolve_color(t["bg_card"]),
                                 corner_radius=t["corner"],
                                 border_width=t["border_width"],
                                 border_color=resolve_color(t["border_color"])
                                 if t["border_color"] else None)
        vol_frame.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(vol_frame, text="🔊",
                     font=theme_font("font_size_main"),
                     text_color=resolve_color(t["text_main"])).pack(
                         side="left", padx=(16, 8), pady=12)

        self.volume_var = tk.DoubleVar(value=self.player.volume)
        self.volume_slider = ctk.CTkSlider(
            vol_frame, from_=0, to=100, variable=self.volume_var,
            command=self.on_volume_change,
            button_color=resolve_color(t["accent"]),
            button_hover_color=resolve_color(t["accent_hover"]),
            progress_color=resolve_color(t["accent"]),
            fg_color=resolve_color(t["bg_input"]),
            height=16)
        self.volume_slider.pack(side="left", fill="x", expand=True,
                                padx=4, pady=12)

        self.vol_label = ctk.CTkLabel(
            vol_frame, text=f"{int(self.player.volume)}",
            font=ctk.CTkFont(family=t["font_family"], size=11),
            text_color=resolve_color(t["text_sub"]), width=30)
        self.vol_label.pack(side="left", padx=(4, 16))

        viz_card = ctk.CTkFrame(self.root,
                                fg_color=resolve_color(t["bg_card"]),
                                corner_radius=t["corner"],
                                border_width=t["border_width"],
                                border_color=resolve_color(t["border_color"])
                                if t["border_color"] else None)
        viz_card.pack(fill="x", padx=20, pady=8)

        viz_header = ctk.CTkFrame(viz_card, fg_color="transparent")
        viz_header.pack(fill="x", padx=16, pady=(12, 4))

        viz_title = tr("viz_title_military") if CURRENT_THEME == "military" \
            else tr("viz_title")
        ctk.CTkLabel(viz_header, text=viz_title,
                     font=theme_font("font_size_small"),
                     text_color=resolve_color(t["text_sub"])).pack(side="left")

        self.viz_src_label = ctk.CTkLabel(
            viz_header,
            text=tr("spectrum_real") if self.player.spectrum_cap.enabled
            else tr("spectrum_sim"),
            font=theme_font("font_size_tiny"),
            text_color=resolve_color(t["text_dim"]))
        self.viz_src_label.pack(side="right")

        self.viz_canvas = tk.Canvas(
            viz_card, bg=resolve_color(t["bg_card"]),
            highlightthickness=0, height=self._viz_height)
        self.viz_canvas.pack(fill="x", padx=16, pady=(0, 14))

        self._build_viz_bars()

        if self._viz_anim_id:
            try:
                self.root.after_cancel(self._viz_anim_id)
            except Exception:
                pass
            self._viz_anim_id = None
        self._animate_viz()

        func = ctk.CTkFrame(self.root, fg_color="transparent")
        func.pack(fill="x", padx=20, pady=(4, 8))

        ctk.CTkButton(
            func, text=tr("format_btn"), command=self.show_format_dialog,
            height=40, corner_radius=t["corner"],
            font=theme_font("font_size_small"),
            fg_color=resolve_color(t["bg_card"]),
            hover_color=resolve_color(t["bg_card_hover"]),
            text_color=resolve_color(t["accent"]),
            border_width=t["border_width"],
            border_color=resolve_color(t["border_color"])
            if t["border_color"] else None).pack(fill="x", expand=True)

        self.autostart_var = tk.BooleanVar(value=is_autostart_enabled())
        ctk.CTkCheckBox(
            self.root, text=tr("autostart_label"),
            variable=self.autostart_var,
            command=self.on_toggle_autostart,
            font=theme_font("font_size_small"),
            text_color=resolve_color(t["text_sub"]),
            fg_color=resolve_color(t["accent"]),
            hover_color=resolve_color(t["accent_hover"]),
            border_color=resolve_color(t["text_dim"]),
            checkmark_color="#060a08" if CURRENT_THEME == "military"
            else "#ffffff").pack(pady=(4, 4))

        spec_src = tr("spectrum_real") if self.player.spectrum_cap.enabled \
            else tr("spectrum_sim")

        if CURRENT_THEME == "military":
            bottom_text = (f"[SYS] CORE:VLC   "
                           f"SPECTRUM:{spec_src.upper()}   "
                           f"TRAY:{'ON' if TRAY_AVAILABLE else 'OFF'}")
            ctk.CTkLabel(self.root,
                         text=bottom_text,
                         font=ctk.CTkFont(family=t["font_family"], size=9),
                         text_color=resolve_color(t["text_dim"])).pack(
                             pady=(0, 14))
        else:
            tray_tip = f" · {tr('tray_tip')}" if TRAY_AVAILABLE else ""
            ctk.CTkLabel(self.root,
                         text=f"VLC · {spec_src}{tray_tip}",
                         font=theme_font("font_size_tiny"),
                         text_color=resolve_color(t["text_dim"])).pack(
                             pady=(0, 14))

        self.refresh()

    def toggle_theme(self):
        global CURRENT_THEME
        playing = self.player.playing
        paused = self.player.paused

        if CURRENT_THEME == "military":
            CURRENT_THEME = "system"
        else:
            CURRENT_THEME = "military"

        CONFIG["theme"] = CURRENT_THEME
        save_config(CONFIG)
        print(f"theme: {get_theme()['name']}")

        self._build_ui()

        self.player.playing = playing
        self.player.paused = paused

    def on_lang_changed(self, choice):
        global CURRENT_LANG
        for code, info in LANGUAGES.items():
            if info["name"] == choice:
                CURRENT_LANG = code
                break
        CONFIG["lang"] = CURRENT_LANG
        save_config(CONFIG)
        print(f"lang: {LANGUAGES[CURRENT_LANG]['name']}")

        playing = self.player.playing
        paused = self.player.paused

        if self.tray:
            self.tray.stop()
        self._build_ui()
        self.tray = TrayIcon(self.player, self)
        self.tray.start()

        self.player.playing = playing
        self.player.paused = paused

    def _build_viz_bars(self):
        self.viz_canvas.delete("all")
        self._viz_bars = []

        self.viz_canvas.update_idletasks()
        w = self.viz_canvas.winfo_width()
        if w < 50:
            w = 440

        t = get_theme()
        gap = 3
        bar_w = (w - gap * (NUM_BARS - 1)) / NUM_BARS

        for i in range(NUM_BARS):
            x0 = i * (bar_w + gap)
            x1 = x0 + bar_w
            color = self._bar_color(i, t)
            rect = self.viz_canvas.create_rectangle(
                x0, self._viz_height, x1, self._viz_height,
                fill=color, outline="")
            self._viz_bars.append((rect, x0, x1))

    def _bar_color(self, i, theme):
        colors = theme["bar_colors"]
        idx = int(i / NUM_BARS * len(colors))
        idx = min(idx, len(colors) - 1)
        return resolve_color(colors[idx])

    def _animate_viz(self):
        try:
            spectrum = self.player.get_spectrum()
            for i, (rect, x0, x1) in enumerate(self._viz_bars):
                val = float(spectrum[i]) if i < len(spectrum) else 0.0
                bar_h = max(2, val * self._viz_height)
                self.viz_canvas.coords(
                    rect, x0, self._viz_height - bar_h, x1, self._viz_height)
        except Exception:
            pass
        self._viz_anim_id = self.root.after(
            int(1000 / FPS), self._animate_viz)

    def _on_seek_start(self, event):
        self._seeking = True

    def _on_seek_end(self, event):
        self._seeking = False
        length = self.player.get_length_ms()
        if length > 0:
            ratio = self.progress_var.get() / 1000.0
            self.player.seek(ratio * length)

    def on_progress_drag(self, val):
        length = self.player.get_length_ms()
        if length > 0:
            ratio = float(val) / 1000.0
            self.time_cur_var.set(format_time(ratio * length))

    def _tick_progress(self):
        try:
            if self.player.playing and not self._seeking:
                cur = self.player.get_time_ms()
                total = self.player.get_length_ms()
                if total > 0:
                    self.progress_var.set(cur / total * 1000)
                    self.progress.set(cur / total * 1000)
                    self.time_cur_var.set(format_time(cur))
                    self.time_total_var.set(format_time(total))
            elif not self.player.playing:
                self.progress_var.set(0)
                self.progress.set(0)
                self.time_cur_var.set("00:00")
                self.time_total_var.set("00:00")
        except Exception:
            pass
        self.root.after(200, self._tick_progress)

    def on_close_to_tray(self):
        self._save_window_position()
        self.root.withdraw()
        print("minimized to tray")

    def restore_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def on_toggle_autostart(self):
        enable = self.autostart_var.get()
        ok = set_autostart(enable)
        if ok:
            CONFIG["autostart"] = enable
            save_config(CONFIG)
        else:
            messagebox.showerror(tr("error"), tr("autostart_fail"))
            self.autostart_var.set(is_autostart_enabled())

    def show_format_dialog(self):
        FormatDialog(self.root)

    def on_pause(self):
        self.player.toggle_pause()

    def on_volume_change(self, val):
        self.player.set_volume(float(val) / 100.0)
        self.vol_label.configure(text=f"{int(float(val))}")

    def refresh(self):
        self.root.after(0, self._do_refresh)

    def _do_refresh(self):
        t = get_theme()
        if self.player.playlist:
            name = os.path.basename(
                self.player.playlist[self.player.current_index])
            self.song_title.configure(text=name)
            idx = self.player.current_index + 1
            total = len(self.player.playlist)
            state = tr("paused") if self.player.paused else \
                (tr("playing") if self.player.playing else tr("stopped"))
            self.song_meta.configure(
                text=f"{state}   ·   " + tr("track_info", idx=idx, total=total))

            if CURRENT_THEME == "military":
                self.state_dot.configure(
                    text=f"● ONLINE  //  {self.player.mode.upper()}",
                    text_color=resolve_color(t["accent"]))
            else:
                self.state_dot.configure(
                    text=self.player.mode_display(),
                    text_color=resolve_color(t["accent"]))
        else:
            self.song_title.configure(text=tr("no_play"))
            self.song_meta.configure(text=tr("insert_usb_hint"))

            if CURRENT_THEME == "military":
                self.state_dot.configure(
                    text="○ STANDBY  //  WAITING_USB",
                    text_color=resolve_color(t["text_dim"]))
            else:
                self.state_dot.configure(
                    text=tr("waiting_usb"),
                    text_color=resolve_color(t["text_sub"]))

        self.pause_btn.configure(
            text="⏸" if self.player.playing and not self.player.paused
            else "▶")
        if self.mode_var:
            self.mode_var.set(self.player.mode_display())

        vol = self.player.volume
        if self.volume_var and abs(self.volume_var.get() - vol) > 1:
            self.volume_var.set(vol)
            if hasattr(self, "volume_slider"):
                self.volume_slider.set(vol)

    def on_close(self):
        self._save_window_position()
        CONFIG["volume"] = self.player.volume
        CONFIG["mode"] = self.player.mode
        CONFIG["theme"] = CURRENT_THEME
        CONFIG["lang"] = CURRENT_LANG
        save_config(CONFIG)

        if self._viz_anim_id:
            try:
                self.root.after_cancel(self._viz_anim_id)
            except Exception:
                pass
            self._viz_anim_id = None
        if self.tray:
            self.tray.stop()
        self.player.stop()
        self.player.stop_spectrum()
        try:
            self.root.destroy()
        except Exception:
            pass
        os._exit(0)

    def run(self):
        self.root.mainloop()


class FormatDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        t = get_theme()
        self.title(tr("format_dialog_title"))
        self.geometry("460x520")
        self.resizable(False, False)
        self.configure(fg_color=resolve_color(t["bg_main"]))
        self.transient(parent)
        self.grab_set()

        ctk.CTkLabel(self, text=tr("format_header"),
                     font=theme_font("font_size_title", bold=True),
                     text_color=resolve_color(t["text_main"])).pack(
                         pady=(20, 2))
        ctk.CTkLabel(self, text=tr("format_sub"),
                     font=theme_font("font_size_small"),
                     text_color=resolve_color(t["text_sub"])).pack(
                         pady=(0, 12))

        scroll = ctk.CTkScrollableFrame(
            self, fg_color=resolve_color(t["bg_card"]),
            corner_radius=t["corner"],
            border_width=t["border_width"],
            border_color=resolve_color(t["border_color"])
            if t["border_color"] else None)
        scroll.pack(fill="both", expand=True, padx=18, pady=(0, 12))

        for cat_key, formats in FORMAT_ITEMS.items():
            ctk.CTkLabel(scroll, text=tr(cat_key),
                         font=theme_font("font_size_main", bold=True),
                         text_color=resolve_color(t["accent"]),
                         anchor="w").pack(fill="x", pady=(12, 6), padx=6)
            for fmt in formats:
                ctk.CTkLabel(scroll, text="  • " + fmt,
                             font=theme_font("font_size_small"),
                             text_color=resolve_color(t["text_main"]),
                             anchor="w").pack(fill="x", padx=18, pady=1)

        ctk.CTkLabel(self, text="ℹ " + tr("format_note"),
                     font=theme_font("font_size_tiny"),
                     text_color=resolve_color(t["text_sub"])).pack(
                         pady=(0, 4))

        ctk.CTkButton(self, text=tr("close"), width=120, height=36,
                      corner_radius=t["corner"],
                      fg_color=resolve_color(t["accent"]),
                      hover_color=resolve_color(t["accent_hover"]),
                      text_color="#060a08" if CURRENT_THEME == "military"
                      else "#ffffff",
                      command=self.destroy).pack(pady=(0, 18))


class DriveSelectDialog(ctk.CTkToplevel):
    def __init__(self, parent, drives, callback):
        super().__init__(parent)
        t = get_theme()
        self.callback = callback
        self.drives = drives

        self.title(tr("select_usb"))
        self.geometry("420x" + str(140 + len(drives) * 52))
        self.resizable(False, False)
        self.configure(fg_color=resolve_color(t["bg_main"]))
        self.transient(parent)
        self.grab_set()

        ctk.CTkLabel(self, text=tr("multi_usb_title"),
                     font=theme_font("font_size_title", bold=True),
                     text_color=resolve_color(t["text_main"])).pack(
                         pady=(20, 4))
        ctk.CTkLabel(self, text=tr("multi_usb_sub"),
                     font=theme_font("font_size_small"),
                     text_color=resolve_color(t["text_sub"])).pack(
                         pady=(0, 14))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24)

        self.radio_var = tk.StringVar(value=drives[0])

        for drive in drives:
            row = ctk.CTkFrame(
                btn_frame, fg_color=resolve_color(t["bg_card"]),
                corner_radius=t["corner"],
                border_width=t["border_width"],
                border_color=resolve_color(t["border_color"])
                if t["border_color"] else None)
            row.pack(fill="x", pady=4)

            ctk.CTkRadioButton(
                row, text="", variable=self.radio_var, value=drive,
                fg_color=resolve_color(t["accent"]),
                hover_color=resolve_color(t["accent_hover"]),
                border_color=resolve_color(t["text_dim"]),
                width=20).pack(side="left", padx=(14, 6), pady=14)

            label_text = self._drive_label(drive)
            ctk.CTkLabel(row, text=label_text,
                         font=theme_font("font_size_main"),
                         text_color=resolve_color(t["text_main"]),
                         anchor="w").pack(side="left", fill="x",
                                          expand=True, pady=14)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(14, 18))

        ctk.CTkButton(btn_row, text=tr("cancel"), width=100, height=36,
                      corner_radius=t["corner"],
                      fg_color=resolve_color(t["bg_card"]),
                      hover_color=resolve_color(t["bg_card_hover"]),
                      text_color=resolve_color(t["text_sub"]),
                      command=self._on_cancel).pack(side="right", padx=(8, 0))

        ctk.CTkButton(btn_row, text=tr("play"), width=100, height=36,
                      corner_radius=t["corner"],
                      fg_color=resolve_color(t["accent"]),
                      hover_color=resolve_color(t["accent_hover"]),
                      text_color="#060a08" if CURRENT_THEME == "military"
                      else "#ffffff",
                      command=self._on_confirm).pack(side="right")

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _drive_label(self, drive):
        label = drive
        if platform.system() == "Windows":
            try:
                import ctypes
                buf = ctypes.create_unicode_buffer(1024)
                ctypes.windll.kernel32.GetVolumeInformationW(
                    ctypes.c_wchar_p(drive), buf, 1024,
                    None, None, None, None, 0)
                if buf.value:
                    label = f"{drive}  ({buf.value})"
            except Exception:
                pass
        return label

    def _on_confirm(self):
        chosen = self.radio_var.get()
        self.grab_release()
        self.destroy()
        if self.callback:
            self.callback(chosen)

    def _on_cancel(self):
        self.grab_release()
        self.destroy()
        if self.callback:
            self.callback(None)


class TrayIcon:
    def __init__(self, player, gui):
        self.player = player
        self.gui = gui
        self.icon = None

    def _make_image(self):
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        if CURRENT_THEME == "military":
            bg = (6, 10, 8, 255)
            bars_color = [(0, 168, 84), (0, 204, 106), (0, 255, 136)]
            d.rectangle((4, 4, size - 4, size - 4), fill=bg,
                        outline=(0, 255, 136, 255), width=2)
        else:
            bg = (30, 30, 46, 255)
            bars_color = [(124, 156, 255), (245, 194, 231), (203, 166, 247)]
            d.ellipse((4, 4, size - 4, size - 4), fill=bg)

        bars = [(18, 40), (28, 20), (38, 32)]
        for i, (x, h) in enumerate(bars):
            d.rectangle((x, h, x + 6, 52), fill=bars_color[i] + (255,))
        return img

    def start(self):
        if not TRAY_AVAILABLE:
            return
        menu = pystray.Menu(
            pystray.MenuItem(tr("tray_show"), self._show_window, default=True),
            pystray.MenuItem(tr("tray_pause"), self._toggle_pause),
            pystray.MenuItem(tr("tray_next"), self._next),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(tr("tray_quit"), self._quit),
        )
        self.icon = pystray.Icon(
            "usb_player", self._make_image(), tr("app_title"), menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def _show_window(self, icon=None, item=None):
        self.gui.root.after(0, self.gui.restore_window)

    def _toggle_pause(self, icon=None, item=None):
        self.player.toggle_pause()

    def _next(self, icon=None, item=None):
        self.player.next()

    def _quit(self, icon=None, item=None):
        if self.icon:
            self.icon.stop()
        self.gui.root.after(0, self.gui.on_close)

    def stop(self):
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass


def play_drive_with_choice(player, gui, drives):
    drives = list(drives)
    if not drives:
        return
    if len(drives) == 1:
        player.play_from(drives[0])
        return
    print(f"multiple USB: {drives}")

    def on_choice(chosen):
        if chosen:
            player.play_from(chosen)
        else:
            print("user cancelled")

    gui.root.after(0, lambda: DriveSelectDialog(gui.root, drives, on_choice))


def usb_watch_loop(player, gui, stop_event):
    watcher = USBWatcher()

    pending = watcher.pop_pending()
    if pending:
        print(f"USB on start: {pending}")
        play_drive_with_choice(player, gui, pending)

    while not stop_event.is_set():
        try:
            new, removed = watcher.check()
            if new:
                print(f"USB detected: {new}")
                play_drive_with_choice(player, gui, new)
            for drive in removed:
                print(f"USB removed: {drive}")
                player.stop()
            player.update()
        except Exception as e:
            print(f"watch error: {e}")
        time.sleep(0.5)


def main():
    global CURRENT_THEME, CURRENT_LANG

    if not VLC_AVAILABLE:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(tr("missing_dep_title"), tr("missing_vlc"))
        return
    if not CTK_AVAILABLE:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(tr("missing_dep_title"), tr("missing_ctk"))
        return

    if "--lang=en_US" in sys.argv:
        CURRENT_LANG = "en_US"
    elif "--lang=zh_CN" in sys.argv:
        CURRENT_LANG = "zh_CN"
    else:
        CURRENT_LANG = CONFIG.get("lang", "zh_CN")

    CURRENT_THEME = CONFIG.get("theme", "military")
    if CURRENT_THEME not in THEMES:
        CURRENT_THEME = "military"

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    player = MusicPlayer()
    stop_event = threading.Event()

    def launch_main():
        try:
            gui = PlayerGUI(player)
        except Exception as e:
            print(f"GUI error: {e}")
            import traceback
            traceback.print_exc()
            return

        threading.Thread(
            target=usb_watch_loop,
            args=(player, gui, stop_event),
            daemon=True
        ).start()

        gui.root.after(500, lambda: ask_autostart_confirm(gui.root))

        try:
            gui.run()
        except Exception as e:
            print(f"mainloop error: {e}")

    show_boot = CONFIG.get("show_boot", True)
    if "--no-boot" in sys.argv:
        show_boot = False

    if show_boot:
        boot_root = ctk.CTk()
        boot_root.geometry("520x760")
        boot_root.resizable(False, False)
        boot_root.title(tr("app_title"))

        sw = boot_root.winfo_screenwidth()
        sh = boot_root.winfo_screenheight()
        bx = (sw - 520) // 2
        by = (sh - 760) // 2
        boot_root.geometry(f"520x760+{bx}+{by}")

        def after_boot():
            try:
                boot_root.destroy()
            except Exception:
                pass
            launch_main()

        BootSplash(boot_root, after_boot)

        try:
            boot_root.mainloop()
        except Exception as e:
            print(f"boot error: {e}")
            try:
                boot_root.destroy()
            except Exception:
                pass
            launch_main()
    else:
        launch_main()

    try:
        stop_event.set()
        player.stop()
        player.stop_spectrum()
    except Exception:
        pass


if __name__ == "__main__":
    main()