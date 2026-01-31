"""
NEXUS AI - Automation Voice Assistant
Author: Kemal Polat Yalçın
Version: 1.2.1
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
import platform
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger("NEXUS")

IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    import winsound

class Config:
    APP_NAME = "NEXUS | SYSTEM V1.2"
    API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Audio Settings
    ENERGY_THRESHOLD = 300
    PAUSE_THRESHOLD = 0.8
    SOUND_OUTPUT = "response.mp3"
    
    # Theme Colors
    COLOR_BG = "#000000"        
    COLOR_CORE = "#00f3ff"
    COLOR_ACTIVE = "#00ff41"
    COLOR_BUSY = "#ff9500"
    COLOR_DIM = "#002233"
    
    if not API_KEY:
        logger.critical("API Key missing in environment variables.")
        # sys.exit(1) # Hata vermemesi icin gecici bypass, kullanici .env koymali

class SoundFX:
    """Handles cross-platform system feedback sounds."""
    
    @staticmethod
    def _beep(freq, duration):
        if IS_WINDOWS:
            try:
                winsound.Beep(freq, duration)
            except:
                pass
            
    @staticmethod
    def play_boot():
        def _sound():
            for freq in range(200, 800, 100):
                SoundFX._beep(freq, 30)
            SoundFX._beep(1200, 200)
        threading.Thread(target=_sound).start()

    @staticmethod
    def play_ack():
        def _sound():
            SoundFX._beep(1000, 50)
            SoundFX._beep(1500, 50)
        threading.Thread(target=_sound).start()

    @staticmethod
    def play_processing():
        def _sound():
            SoundFX._beep(400, 50)
        threading.Thread(target=_sound).start()

class AIBrain:
    """Wrapper for Google Gemini 1.5 Flash API."""
    def __init__(self):
        try:
            if Config.API_KEY:
                genai.configure(api_key=Config.API_KEY)
                self.model = genai.GenerativeModel(
                    model_name='gemini-1.5-flash',
                    system_instruction="You are NEXUS, a technical assistant. Be concise. No markdown formatting in speech."
                )
                self.chat = self.model.start_chat(history=[])
            else:
                self.model = None
        except Exception as e:
            logger.error(f"LLM Init Failed: {e}")
            self.model = None

    def ask(self, prompt, context=None):
        if not self.model: return "System offline. Check API Key."
        try:
            full_prompt = f"Context: {context}\nQuery: {prompt}" if context else prompt
            response = self.chat.send_message(full_prompt)
            return response.text.replace("*", "").replace("#", "")
        except Exception as e:
            logger.error(f"Inference Error: {e}")
            return "Processing error."

class SkillManager:
    """Executes automation tasks and system commands."""
    def __init__(self, core):
        self.core = core
        self.brain = AIBrain()
    
    def execute(self, command):
        cmd = command.lower()
        self.core.ui.set_status("PROCESSING") 
        SoundFX.play_processing()

        try:
            if "clipboard" in cmd or "analyze" in cmd:
                content = pyperclip.paste()
                self.core.speak("Analyzing clipboard...")
                response = self.brain.ask(cmd, context=content)
                self.core.speak(response)
            
            elif "vs code" in cmd or "code" in cmd:
                self.core.speak("Opening VS Code.")
                os.system("code ." if IS_WINDOWS else "open -a 'Visual Studio Code'")
            
            elif "terminal" in cmd:
                self.core.speak("Launching terminal.")
                os.system("start cmd" if IS_WINDOWS else "open -a Terminal")
                
            elif "exit" in cmd or "shutdown" in cmd:
                self.core.speak("Shutting down.")
                time.sleep(1)
                self.core.ui.quit_app()
                
            else:
                response = self.brain.ask(cmd)
                self.core.speak(response)
                
        except Exception as e:
            logger.error(f"Skill Execution Failed: {e}")
            self.core.speak("Command failed.")

        self.core.ui.set_status("IDLE")

class VoiceEngine:
    """Handles Speech-to-Text and Text-to-Speech operations."""
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Otomatik mikrofon secimi icin default birakildi
        self.microphone = sr.Microphone()
        self.log_callback = lambda x: None 
        
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                self.recognizer.energy_threshold = Config.ENERGY_THRESHOLD
                self.recognizer.pause_threshold = Config.PAUSE_THRESHOLD
        except Exception as e:
            logger.warning(f"Mic calibration warning: {e}")

    def listen(self):
        with self.microphone as source:
            try:
                audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=8)
                return self.recognizer.recognize_google(audio, language="en-US").lower()
            except (sr.WaitTimeoutError, sr.UnknownValueError):
                return None
            except Exception as e:
                logger.error(f"Mic Error: {e}")
                return None

    async def _generate_audio(self, text):
        communicate = edge_tts.Communicate(text, "en-US-BrianNeural", rate="+5%")
        await communicate.save(Config.SOUND_OUTPUT)

    def speak(self, text):
        threading.Thread(target=lambda: self.log_callback(text)).start()
        try:
            if os.path.exists(Config.SOUND_OUTPUT): os.remove(Config.SOUND_OUTPUT)
            asyncio.run(self._generate_audio(text[:500]))
            
            pygame.mixer.init()
            pygame.mixer.music.load(Config.SOUND_OUTPUT)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.quit()
        except Exception as e:
            logger.error(f"TTS Error: {e}")

class NexusCore:
    def __init__(self, ui):
        self.ui = ui
        self.voice = VoiceEngine()
        self.voice.log_callback = self.ui.typewriter_log 
        self.skills = SkillManager(self)
        self.triggers = ["nexus", "system", "computer"]
        self.is_running = True

    def run(self):
        time.sleep(2)
        SoundFX.play_boot()
        self.ui.set_status("IDLE")
        self.voice.speak("Online.")
        
        while self.is_running:
            input_text = self.voice.listen()
            if input_text and any(t in input_text for t in self.triggers):
                SoundFX.play_ack()
                self.ui.set_status("LISTENING")
                self.voice.speak("Yes?")
                
                command = self.voice.listen()
                if command:
                    self.ui.update_log(f"> {command.upper()}")
                    self.skills.execute(command)
                else:
                    self.ui.set_status("IDLE")

class Particle:
    def __init__(self, w, h):
        self.w, self.h = w, h
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

class NexusUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.WIDTH, self.HEIGHT = 800, 800
        
        try:
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        except:
            sw, sh = 1920, 1080
            
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{sw//2 - self.WIDTH//2}+{sh//2 - self.HEIGHT//2}")
        
        self.overrideredirect(True)
        self.configure(fg_color="black")
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.0)
        
        self.canvas = ctk.CTkCanvas(self, width=self.WIDTH, height=self.HEIGHT, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # DEGISTIRILDI: self.state ismi cakisiyordu, nexus_status yapildi
        self.nexus_status = "BOOT" 
        
        self.angle_1 = self.angle_2 = self.pulse = 0
        self.log_text = "INITIALIZING..."
        self.particles = [Particle(self.WIDTH, self.HEIGHT) for _ in range(80)]
        self.fade_alpha = 0.0
        
        self.animate()
        self.fade_in()
        
        self.canvas.bind("<Button-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.do_move)

    def start_move(self, event): self.x, self.y = event.x, event.y
    def do_move(self, event):
        self.geometry(f"+{self.winfo_x() + (event.x - self.x)}+{self.winfo_y() + (event.y - self.y)}")
        
    def set_status(self, status): self.nexus_status = status 
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
        
        # nexus_status kullaniliyor artik
        if self.nexus_status == "IDLE": color, warp, label = Config.COLOR_CORE, 1.0, "ONLINE"
        elif self.nexus_status == "LISTENING": color, warp, label = Config.COLOR_ACTIVE, 0.2, "LISTENING"
        elif self.nexus_status == "PROCESSING": color, warp, label = Config.COLOR_BUSY, 4.0, "PROCESSING"
        else: color, warp, label = Config.COLOR_DIM, 0.0, "BOOT"

        # Particles
        for p in self.particles:
            p.update(warp, cx, cy)
            hex_c = f"#{int(p.opacity):02x}{int(p.opacity):02x}{int(p.opacity):02x}"
            if hex_c != "#000000":
                self.canvas.create_oval(p.x-p.size, p.y-p.size, p.x+p.size, p.y+p.size, fill=hex_c, outline="")

        # HUD Rings
        r1 = 300
        self.canvas.create_oval(cx-r1, cy-r1, cx+r1, cy+r1, outline=Config.COLOR_DIM, width=1)
        for i in range(0, 360, 60):
            self.canvas.create_arc(cx-r1, cy-r1, cx+r1, cy+r1, start=i+self.angle_1, extent=40, style="arc", outline=color, width=2)
            
        r2 = 220
        self.canvas.create_arc(cx-r2, cy-r2, cx+r2, cy+r2, start=-self.angle_2, extent=300, style="arc", outline=color, width=3)

        pulse_r = 60 + (math.sin(self.pulse) * 10)
        self.canvas.create_oval(cx-pulse_r, cy-pulse_r, cx+pulse_r, cy+pulse_r, outline=color, width=2)
        
        # Labels
        self.canvas.create_text(cx, cy-350, text=label, fill=color, font=("Consolas", 14, "bold"))
        self.canvas.create_text(cx, cy+350, text=self.log_text, fill="white", font=("Consolas", 12), width=600, justify="center")

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
    threading.Thread(target=core.run, daemon=True).start()
    app.mainloop()