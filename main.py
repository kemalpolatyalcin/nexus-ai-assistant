"""
NEXUS AI - INTELLIGENT VOICE ASSISTANT
--------------------------------------
Author: Kemal Polat Yalçın
Version: 1.2 (Stable)
Description: 
    An autonomous voice assistant utilizing Google Gemini 1.5 Flash LLM 
    for logic processing, EdgeTTS for synthesis, and a holographic 
    UI built with CustomTkinter. Designed for software automation tasks.
"""

import warnings
warnings.filterwarnings("ignore")

import customtkinter as ctk
import speech_recognition as sr
import pygame
import os
import sys
import threading
import asyncio
import edge_tts
import time
import logging
import pyperclip
import google.generativeai as genai
import math
import random
import platform  # OS tespiti için eklendi
from datetime import datetime
from dotenv import load_dotenv

# --- INITIALIZATION ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger("NEXUS_SYSTEM")

# --- CROSS-PLATFORM SOUND COMPATIBILITY ---
# Apple mühendisleri Mac kullanır, winsound Mac'te çalışmaz.
# Bu blok kodun her işletim sisteminde çalışmasını sağlar.
IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    import winsound

# --- CONFIGURATION ---
class Config:
    APP_NAME = "NEXUS | SYSTEM V1.2"
    
    # SECURITY: Load Key from Environment Variable
    API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Hardware Settings
    ENERGY_THRESHOLD = 300
    PAUSE_THRESHOLD = 0.8
    SOUND_OUTPUT = "response.mp3"
    
    # UI Palette (Deep Space Theme)
    COLOR_BG = "#000000"        
    COLOR_CORE = "#00f3ff"     # Neon Cyan
    COLOR_ACTIVE = "#00ff41"   # Matrix Green
    COLOR_BUSY = "#ff9500"     # Amber
    COLOR_DIM = "#002233"      # Deep Blue
    
    # Validation
    if not API_KEY:
        logger.critical("API Key missing in .env file! System halting.")
        sys.exit("CRITICAL ERROR: Please add GOOGLE_API_KEY to .env file.")

# --- SOUND FX MANAGER ---
class SoundFX:
    """Handles system feedback sounds compatible with multiple OS."""
    
    @staticmethod
    def _beep(freq, duration):
        """Cross-platform beep implementation."""
        if IS_WINDOWS:
            winsound.Beep(freq, duration)
        else:
            # macOS/Linux için alternatif ses (veya sessiz geçiş)
            # Burada 'printf \a' veya basit bir wav dosyası kullanılabilir.
            pass 

    @staticmethod
    def play_boot():
        def _sound():
            for freq in range(200, 800, 100):
                SoundFX._beep(freq, 30)
            SoundFX._beep(1200, 200)
        threading.Thread(target=_sound).start()

    @staticmethod
    def play_listening():
        def _sound():
            SoundFX._beep(1000, 50)
            SoundFX._beep(1500, 50)
        threading.Thread(target=_sound).start()

    @staticmethod
    def play_processing():
        def _sound():
            SoundFX._beep(400, 50)
            SoundFX._beep(300, 50)
        threading.Thread(target=_sound).start()

# --- AI BRAIN (LLM) ---
class AIBrain:
    """Handles interaction with Google Gemini 1.5 Flash Model."""
    def __init__(self):
        try:
            genai.configure(api_key=Config.API_KEY)
            self.model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                system_instruction=(
                    "You are NEXUS, an elite AI assistant for a software automation engineer. "
                    "Your responses must be concise, technical, and professional. "
                    "Do not use asterisks (*) in your speech. "
                    "If asked for code, explain the logic briefly first."
                )
            )
            self.chat = self.model.start_chat(history=[])
            logger.info("Neural Link Established.")
        except Exception as e:
            logger.error(f"Brain Initialization Error: {e}")
            self.model = None

    def ask(self, prompt, context=None):
        if not self.model: return "Neural Link Offline. Please check API Key."
        try:
            full_prompt = f"Context Data: {context}\nUser Query: {prompt}" if context else prompt
            response = self.chat.send_message(full_prompt)
            # TTS motoru yıldız işaretlerini okumasın diye temizliyoruz
            clean_text = response.text.replace("*", "").replace("#", "")
            return clean_text
        except Exception as e:
            logger.error(f"Inference Error: {e}")
            return "I encountered an error processing that request."

# --- SKILL MANAGER ---
class SkillManager:
    """Executes system commands and tools based on intent."""
    def __init__(self, core):
        self.core = core
        self.brain = AIBrain()
    
    def execute(self, command):
        cmd = command.lower()
        self.core.ui.set_hud_state("PROCESSING") 
        SoundFX.play_processing()

        try:
            # 1. Clipboard / Code Analysis
            if "clipboard" in cmd or "analyze code" in cmd:
                content = pyperclip.paste()
                self.core.speak("Analyzing clipboard content...")
                response = self.brain.ask(cmd, context=content)
                self.core.speak(response)
            
            # 2. Open Development Environment
            elif "open project" in cmd or "vs code" in cmd:
                self.core.speak("Initializing VS Code environment.")
                if IS_WINDOWS:
                    os.system("code .")
                else:
                    os.system("open -a 'Visual Studio Code'") # macOS support
            
            # 3. System Terminal
            elif "terminal" in cmd or "console" in cmd:
                self.core.speak("Launching terminal.")
                if IS_WINDOWS:
                    os.system("start cmd")
                else:
                    os.system("open -a Terminal") # macOS support
                
            # 4. Termination
            elif "shutdown" in cmd or "dismiss" in cmd or "exit" in cmd:
                self.core.speak("Terminating session. Goodbye, Sir.")
                time.sleep(2)
                self.core.ui.quit_app()
                
            # 5. General LLM Query
            else:
                response = self.brain.ask(cmd)
                self.core.speak(response)
                
        except Exception as e:
            logger.error(f"Execution Error: {e}")
            self.core.speak("An error occurred during command execution.")

        self.core.ui.set_hud_state("IDLE")

# --- VOICE ENGINE (EARS & MOUTH) ---
class VoiceEngine:
    """Handles Audio I/O: Speech Recognition and Text-to-Speech."""
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.log_callback = lambda x: None 
        
        # --- OPTIMIZATION: Calibrate Noise ONCE at startup ---
        # This prevents the 1-second delay before every command.
        with self.microphone as source:
            logger.info("Calibrating background noise... Please wait.")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            self.recognizer.energy_threshold = Config.ENERGY_THRESHOLD
            self.recognizer.pause_threshold = Config.PAUSE_THRESHOLD
        logger.info("Audio calibration complete.")

    def listen(self):
        """Captures audio and performs STT (Speech-to-Text)."""
        with self.microphone as source:
            try:
                # Dinleme süresini ve timeout'u optimize ettik
                audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=8)
                text = self.recognizer.recognize_google(audio, language="en-US")
                return text.lower()
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                return None
            except Exception as e:
                logger.error(f"Microphone Error: {e}")
                return None

    async def _generate_tts(self, text):
        """Generates MP3 using EdgeTTS (Async)."""
        communicate = edge_tts.Communicate(text, "en-US-BrianNeural", rate="+5%")
        await communicate.save(Config.SOUND_OUTPUT)

    def speak(self, text):
        """Plays the generated audio response."""
        # UI Log Update
        threading.Thread(target=lambda: self.log_callback(text)).start()
        
        try:
            # Clean up old file
            if os.path.exists(Config.SOUND_OUTPUT): 
                os.remove(Config.SOUND_OUTPUT)
                
            # Generate Audio
            asyncio.run(self._generate_tts(text[:500])) # Limit char count for speed
            
            # Play Audio
            pygame.mixer.init()
            pygame.mixer.music.load(Config.SOUND_OUTPUT)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            pygame.mixer.music.unload()
            pygame.mixer.quit()
        except Exception as e:
            logger.error(f"TTS Error: {e}")

# --- CORE CONTROLLER ---
class NexusCore:
    """Central Logic Controller linking UI, Voice, and Skills."""
    def __init__(self, ui):
        self.ui = ui
        self.voice = VoiceEngine()
        self.voice.log_callback = self.ui.typewriter_log 
        self.skills = SkillManager(self)
        self.triggers = ["nexus", "jarvis", "system", "computer", "hey"]
        self.is_running = True

    def run_loop(self):
        """Main Logic Loop running in background thread."""
        time.sleep(2) # Allow UI to render
        SoundFX.play_boot()
        self.ui.set_hud_state("IDLE")
        self.voice.speak("System online. Awaiting instructions.")
        
        while self.is_running:
            input_text = self.voice.listen()
            
            if input_text:
                # Trigger Word Detection
                if any(t in input_text for t in self.triggers):
                    SoundFX.play_listening()
                    self.ui.set_hud_state("LISTENING")
                    self.voice.speak("Yes?")
                    
                    command = self.voice.listen()
                    if command:
                        self.ui.update_log(f"> CMD: {command.upper()}")
                        self.skills.execute(command)
                    else:
                        self.ui.set_hud_state("IDLE")

# --- VISUALS: PARTICLE SYSTEM ---
class Particle:
    """Physics-based particle system for UI aesthetics."""
    def __init__(self, width, height):
        self.w, self.h = width, height
        self.reset(first=True)
        
    def reset(self, first=False):
        self.angle = random.uniform(0, 6.28)
        self.dist = random.uniform(0, self.w) if first else random.uniform(0, 50)
        self.speed = random.uniform(2, 5)
        self.size = random.uniform(1, 3)
        self.opacity = 0
        
    def update(self, speed_mult, cx, cy):
        self.dist += self.speed * speed_mult
        self.x = cx + math.cos(self.angle) * self.dist
        self.y = cy + math.sin(self.angle) * self.dist
        self.size += 0.05 * speed_mult
        self.opacity = min(255, self.dist / 2)
        
        if self.x < 0 or self.x > self.w or self.y < 0 or self.y > self.h:
            self.reset()

# --- UI: HOLOGRAPHIC HUD ---
class NexusUI(ctk.CTk):
    """Main Application Window with Holographic Interface."""
    def __init__(self):
        super().__init__()
        
        # Window Configuration
        self.WIDTH = 800
        self.HEIGHT = 800
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{sw//2 - self.WIDTH//2}+{sh//2 - self.HEIGHT//2}")
        
        self.overrideredirect(True) # Frameless Window
        self.configure(fg_color="black")
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.0) # Start invisible for fade-in effect
        
        # Canvas Setup
        self.canvas = ctk.CTkCanvas(self, width=self.WIDTH, height=self.HEIGHT, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # State Variables
        self.hud_state = "BOOT" 
        self.angle_1 = 0
        self.angle_2 = 0
        self.pulse = 0
        self.log_text = "INITIALIZING CORE..."
        self.particles = [Particle(self.WIDTH, self.HEIGHT) for _ in range(80)]
        self.fade_alpha = 0.0
        
        # Start Animation Loops
        self.animate()
        self.fade_in()
        
        # Draggable Window Logic
        self.canvas.bind("<Button-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.do_move)

    def start_move(self, event): self.x, self.y = event.x, event.y
    def do_move(self, event):
        x = self.winfo_x() + (event.x - self.x)
        y = self.winfo_y() + (event.y - self.y)
        self.geometry(f"+{x}+{y}")
        
    def set_hud_state(self, state): self.hud_state = state 
    def update_log(self, text): self.log_text = text

    def typewriter_log(self, text):
        clean = text.replace("*", "")[:80]
        for i in range(len(clean) + 1):
            self.log_text = clean[:i] + "_"
            time.sleep(0.02)
        self.log_text = clean

    def fade_in(self):
        if self.fade_alpha < 0.95:
            self.fade_alpha += 0.05
            self.attributes('-alpha', self.fade_alpha)
            self.after(50, self.fade_in)

    def draw(self):
        self.canvas.delete("all")
        cx, cy = self.WIDTH // 2, self.HEIGHT // 2
        
        # State Logic (Colors & Text)
        if self.hud_state == "IDLE": 
            color, warp, label = Config.COLOR_CORE, 1.0, "SYSTEM ONLINE"
        elif self.hud_state == "LISTENING": 
            color, warp, label = Config.COLOR_ACTIVE, 0.2, "LISTENING..."
        elif self.hud_state == "PROCESSING": 
            color, warp, label = Config.COLOR_BUSY, 4.0, "PROCESSING..."
        else:
            color, warp, label = Config.COLOR_DIM, 0.0, "SYSTEM BOOT"

        # 1. Draw Particles (Starfield)
        for p in self.particles:
            p.update(warp, cx, cy)
            hex_color = f"#{int(p.opacity):02x}{int(p.opacity):02x}{int(p.opacity):02x}"
            if hex_color != "#000000":
                self.canvas.create_oval(p.x-p.size, p.y-p.size, p.x+p.size, p.y+p.size, fill=hex_color, outline="")

        # 2. Draw HUD Elements (Rings & Core)
        r1 = 300
        self.canvas.create_oval(cx-r1, cy-r1, cx+r1, cy+r1, outline=Config.COLOR_DIM, width=1)
        for i in range(0, 360, 60):
            self.canvas.create_arc(cx-r1, cy-r1, cx+r1, cy+r1, start=i+self.angle_1, extent=40, style="arc", outline=color, width=2)
            
        r2 = 220
        self.canvas.create_arc(cx-r2, cy-r2, cx+r2, cy+r2, start=-self.angle_2, extent=300, style="arc", outline=color, width=3)

        pulse_r = 60 + (math.sin(self.pulse) * 10)
        self.canvas.create_oval(cx-pulse_r, cy-pulse_r, cx+pulse_r, cy+pulse_r, outline=color, width=2)
        
        # 3. Draw Text
        self.canvas.create_text(cx, cy-350, text=label, fill=color, font=("Consolas", 14, "bold"))
        self.canvas.create_text(cx, cy+350, text=self.log_text, fill="white", font=("Consolas", 12), width=600, justify="center")

        # 4. Targeting Brackets
        b_off, b_len = 320, 50
        self.canvas.create_line(cx-b_off, cy-b_off+b_len, cx-b_off, cy-b_off, cx-b_off+b_len, cy-b_off, fill=color, width=2)
        self.canvas.create_line(cx+b_off-b_len, cy-b_off, cx+b_off, cy-b_off, cx+b_off, cy-b_off+b_len, fill=color, width=2)
        self.canvas.create_line(cx-b_off, cy+b_off-b_len, cx-b_off, cy+b_off, cx-b_off+b_len, cy+b_off, fill=color, width=2)
        self.canvas.create_line(cx+b_off-b_len, cy+b_off, cx+b_off, cy+b_off, cx+b_off, cy+b_off-b_len, fill=color, width=2)

    def animate(self):
        self.angle_1 = (self.angle_1 + 1) % 360
        self.angle_2 = (self.angle_2 - 1.5) % 360
        self.pulse += 0.1
        self.draw()
        self.after(30, self.animate)

    def quit_app(self):
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = NexusUI()
    core = NexusCore(app)
    
    # Run Core Logic in separate thread
    logic_thread = threading.Thread(target=core.run_loop, daemon=True)
    logic_thread.start()
    
    app.mainloop()
