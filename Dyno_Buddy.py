import tkinter as tk
from PIL import Image, ImageTk
import os
import random
import threading
import time
import sys       
import keyboard  
import psutil    
import webbrowser  
import requests    
import json
from datetime import datetime  
import asyncio   
import edge_tts  
import pygame    
import urllib.parse 
import speech_recognition as sr  
import subprocess 
import google.generativeai as genai

# ==========================================
# GOOGLE AI STUDIO INITIALIZATION 🔑
# ==========================================
API_KEY = os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("OPENROUTER_API_KEY", "").strip()
if API_KEY:
    genai.configure(api_key=API_KEY)

AI_MODEL_NAME = "gemini-3.6-flash"  

# ==========================================
# SEASONS & WEATHER DINO GAME (SCALING JUMP FIXED)
# ==========================================
import random
import os
import math

try:
    import pygame
    pygame.mixer.init()
    AUDIO_SUPPORT = True
except ImportError:
    AUDIO_SUPPORT = False

class DinoJumpGame:
    def __init__(self, main_app):
        if AUDIO_SUPPORT:
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.pre_init(44100, -16, 2, 2048)
                    pygame.mixer.init()
            except Exception as e:
                print(f"Mixer Init Warning: {e}")

        self.main_app = main_app
        self.top = tk.Toplevel(self.main_app.root)
        self.top.title("Chrome Dyno Arcade - Four Seasons Edition")
        
        self.base_width = 800
        self.base_height = 300
        self.top.geometry(f"{self.base_width}x{self.base_height}")
        self.top.attributes("-topmost", True)
        self.user_custom_size = (self.main_app.target_width, self.main_app.target_height)

        self.top.update_idletasks()
        self.is_fullscreen = False

        self.main_app.in_game_mode = True
        self.main_app.root.withdraw()

        self.canvas = tk.Canvas(self.top, bg="#87CEEB", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.width = self.base_width
        self.height = self.base_height
        
        self.bg_mountain_x = 0
        self.fg_mountain_x = 0
        
        self.is_jumping = False
        self.jump_velocity = 0
        self.obstacles = []
        self.clouds = [{'x': 200, 'y': 40, 'speed': 1}, {'x': 600, 'y': 60, 'speed': 1.2}]
        self.obstacle_speed = 6.5
        self.score = 0
        self.high_score = getattr(self.main_app, 'high_score', 0)
        self.game_over = False
        self.spawn_timer = 0
        self.frame_index = 0.0

        self.raindrops = [{'x': random.randint(0, 800), 'y': random.randint(0, 300), 'speed': random.randint(8, 14), 'length': random.randint(8, 15)} for _ in range(35)]
        self.petals = [{'x': random.randint(0, 800), 'y': random.randint(0, 300), 'speed_x': random.uniform(1, 2.5), 'speed_y': random.uniform(1, 2), 'size': random.randint(3, 6), 'angle': random.uniform(0, 3.14)} for _ in range(25)]
        self.snowflakes = [{'x': random.randint(0, 800), 'y': random.randint(0, 300), 'speed': random.uniform(1, 2.5), 'radius': random.randint(2, 4)} for _ in range(30)]

        self.dialogue_text = ""
        self.dialogue_timer = 0
        self.dialogue_quotes = [
            "Woohoo! 100 Points!",
            "Speeding Up!",
            "Unstoppable!",
            "Level Up!",
            "You're a Pro!",
            "Awesome Jump!"
        ]

        self.play_background_music()
        self.recalculate_positions()
        self.dino_x = 60
        self.dino_y = self.ground_y - self.dino_height

        self.top.bind("<space>", lambda e: self.jump())
        self.top.bind("<Up>", lambda e: self.jump())
        self.top.bind("<r>", lambda e: self.reset_game())
        self.top.bind("<R>", lambda e: self.reset_game())
        self.top.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.top.bind("<f>", lambda e: self.toggle_fullscreen())
        self.top.bind("<Escape>", lambda e: self.handle_escape())
        self.top.bind("<Configure>", self.on_resize)
        self.top.protocol("WM_DELETE_WINDOW", self.close_game)

        self.top.focus_force()
        self.update_game()

    def play_background_music(self):
        if AUDIO_SUPPORT:
            try:
                sound_file = r"C:\Users\hp\OneDrive\Pictures\Dyno_Buddy\Assets\dyno_game_sound.mp3"
                if os.path.exists(sound_file):
                    pygame.mixer.music.load(sound_file)
                    pygame.mixer.music.set_volume(0.7)
                    pygame.mixer.music.play(-1)
            except Exception as e:
                print(f"Pygame Audio Error: {e}")
                
    def stop_background_music(self):
        if AUDIO_SUPPORT:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

    def get_season_theme(self):
        cycle = (self.score // 300) % 4
        if cycle == 0:
            return {"bg": "#A0E7E5", "is_dark": False, "season": "Spring (Flowers)"}
        elif cycle == 1:
            return {"bg": "#FF7F50", "is_dark": False, "season": "Monsoon (Rain)"}
        elif cycle == 2:
            return {"bg": "#121B29", "is_dark": True, "season": "Winter (Fog & Snow)"}
        else:
            return {"bg": "#FFD166", "is_dark": False, "season": "Sunny Morning"}
        
    def recalculate_positions(self):
        w = self.top.winfo_width()
        h = self.top.winfo_height()
        self.width = w if w > 100 else self.base_width
        self.height = h if h > 100 else self.base_height
        
        self.scale_factor = max(self.height / self.base_height, 0.5)
        self.dino_width = int(44 * self.scale_factor)
        self.dino_height = int(48 * self.scale_factor)
        
        self.ground_y = int(self.height * 0.78)
        self.gravity = 0.65 * self.scale_factor

        self.run_frames = self.prepare_game_frames(self.main_app.animations_right.get('run', []))
        self.jump_frames = self.prepare_game_frames(self.main_app.animations_right.get('jump', []))

    def on_resize(self, event):
        if event.widget == self.top:
            self.recalculate_positions()
            if not self.is_jumping:
                self.dino_y = self.ground_y - self.dino_height

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        self.top.attributes("-fullscreen", self.is_fullscreen)

    def handle_escape(self):
        if self.is_fullscreen:
            self.toggle_fullscreen()
        else:
            self.close_game()

    def prepare_game_frames(self, raw_frames):
        processed = []
        for img in raw_frames:
            try:
                pil_img = ImageTk.getimage(img)
                resized = pil_img.resize((self.dino_width, self.dino_height), Image.Resampling.LANCZOS)
                processed.append(ImageTk.PhotoImage(resized))
            except Exception:
                processed.append(img)
        return processed

    def jump(self):
        if self.game_over:
            return
        if not self.is_jumping:
            self.is_jumping = True
            self.jump_velocity = -11.5 * self.scale_factor

    def reset_game(self):
        self.obstacles.clear()
        self.recalculate_positions()
        self.dino_y = self.ground_y - self.dino_height
        self.is_jumping = False
        self.jump_velocity = 0
        self.score = 0
        self.obstacle_speed = 6.5
        self.bg_mountain_x = 0
        self.fg_mountain_x = 0
        self.dialogue_timer = 0
        self.spawn_timer = 0
        
        if self.game_over:
            self.game_over = False
            self.play_background_music()
            self.update_game()

    def close_game(self):
        self.game_over = True
        self.stop_background_music()

        if self.score > self.high_score:
            self.main_app.high_score = self.score

        self.main_app.in_game_mode = False
        if hasattr(self.main_app, 'game_instance'):
            self.main_app.game_instance = None

        try:
            self.top.destroy()
        except Exception:
            pass
        
        self.main_app.root.deiconify()
        self.main_app.set_behavior('idle')

    def draw_weather_and_seasons(self, cycle, is_dark):
        if cycle == 0:
            for p in self.petals:
                p['y'] += p['speed_y']
                p['x'] += math.sin(p['angle']) * 1.5
                p['angle'] += 0.05
                if p['y'] > self.height:
                    p['y'] = -10
                    p['x'] = random.randint(0, self.width)
                self.canvas.create_oval(p['x'], p['y'], p['x'] + p['size'], p['y'] + (p['size'] * 1.5), fill="#FFB6C1", outline="#FF69B4")

        elif cycle == 1:
            rain_color = "#E0F7FA" if is_dark else "#1E88E5"
            for drop in self.raindrops:
                drop['y'] += drop['speed']
                drop['x'] -= 2
                if drop['y'] > self.height:
                    drop['y'] = -10
                    drop['x'] = random.randint(0, self.width)
                self.canvas.create_line(drop['x'], drop['y'], drop['x'] - 3, drop['y'] + drop['length'], fill=rain_color, width=1)

        elif cycle == 2:
            for flake in self.snowflakes:
                flake['y'] += flake['speed']
                flake['x'] += math.sin(flake['y'] * 0.05) * 0.8
                if flake['y'] > self.height:
                    flake['y'] = -10
                    flake['x'] = random.randint(0, self.width)
                self.canvas.create_oval(flake['x'] - flake['radius'], flake['y'] - flake['radius'], flake['x'] + flake['radius'], flake['y'] + flake['radius'], fill="#FFFFFF", outline="")

            self.canvas.create_rectangle(0, self.ground_y - 80, self.width, self.ground_y + 20, fill="#1E293B", outline="", stipple="gray25")
            self.canvas.create_rectangle(0, self.ground_y - 40, self.width, self.ground_y + 10, fill="#334155", outline="", stipple="gray50")

    def draw_parallax_background(self, is_dark):
        m_color_back = "#1E293B" if is_dark else "#C4D7E0"
        m_color_front = "#0F172A" if is_dark else "#99B8C7"
        tree_trunk = "#0D0D0D" if is_dark else "#5c4033"
        tree_leaves = "#1A3636" if is_dark else "#4a7c59"

        self.bg_mountain_x = (self.bg_mountain_x - (self.obstacle_speed * 0.15)) % self.width
        self.fg_mountain_x = (self.fg_mountain_x - (self.obstacle_speed * 0.35)) % self.width

        for offset in [self.bg_mountain_x - self.width, self.bg_mountain_x]:
            self.canvas.create_polygon(offset, self.ground_y, offset + (150 * self.scale_factor), self.ground_y - (70 * self.scale_factor), offset + (320 * self.scale_factor), self.ground_y, fill=m_color_back, outline="")
            self.canvas.create_polygon(offset + (250 * self.scale_factor), self.ground_y, offset + (450 * self.scale_factor), self.ground_y - (110 * self.scale_factor), offset + (650 * self.scale_factor), self.ground_y, fill=m_color_back, outline="")

        mountains = [(80, 90, 240), (380, 130, 580), (680, 100, 880)]
        for offset in [self.fg_mountain_x - self.width, self.fg_mountain_x]:
            for peak_x_base, h_base, base_w_base in mountains:
                peak_x = offset + (peak_x_base * self.scale_factor)
                h = h_base * self.scale_factor
                base_w = base_w_base * self.scale_factor
                left = peak_x - base_w // 2
                right = peak_x + base_w // 2
                peak_y = self.ground_y - h
                
                self.canvas.create_polygon(left, self.ground_y, peak_x, peak_y, right, self.ground_y, fill=m_color_front, outline="")

                for t_rel in [-0.2, 0.1, 0.35]:
                    tree_x = peak_x + (t_rel * base_w)
                    if -50 <= tree_x <= self.width + 50:
                        tw = 2 * self.scale_factor
                        th = 18 * self.scale_factor
                        lw = 10 * self.scale_factor
                        
                        self.canvas.create_rectangle(tree_x - tw, self.ground_y - th, tree_x + tw, self.ground_y, fill=tree_trunk, outline="")
                        self.canvas.create_polygon(tree_x - lw, self.ground_y - (12 * self.scale_factor), tree_x, self.ground_y - (32 * self.scale_factor), tree_x + lw, self.ground_y - (12 * self.scale_factor), fill=tree_leaves, outline="")

    def draw_cactus(self, x, y, width, height, is_dark):
        color = "#e0e0e0" if is_dark else "#535353"
        self.canvas.create_rectangle(x + width*0.35, y, x + width*0.65, y + height, fill=color, outline="")
        self.canvas.create_rectangle(x, y + height*0.3, x + width*0.35, y + height*0.45, fill=color, outline="")
        self.canvas.create_rectangle(x, y + height*0.15, x + width*0.15, y + height*0.45, fill=color, outline="")
        self.canvas.create_rectangle(x + width*0.65, y + height*0.4, x + width, y + height*0.55, fill=color, outline="")
        self.canvas.create_rectangle(x + width*0.85, y + height*0.25, x + width, y + height*0.55, fill=color, outline="")

    def draw_bird(self, x, y, wing_up, is_dark):
        color = "#e0e0e0" if is_dark else "#535353"
        s = self.scale_factor
        self.canvas.create_polygon(x, y+10*s, x+25*s, y+5*s, x+35*s, y+12*s, x+20*s, y+18*s, fill=color)
        self.canvas.create_polygon(x, y+10*s, x-10*s, y+8*s, x-5*s, y+14*s, fill=color)
        if wing_up:
            self.canvas.create_polygon(x+10*s, y+8*s, x+18*s, y-10*s, x+25*s, y+5*s, fill=color)
        else:
            self.canvas.create_polygon(x+10*s, y+8*s, x+18*s, y+22*s, x+25*s, y+5*s, fill=color)

    def draw_speech_bubble(self, x, y, text):
        bx1 = x + (15 * self.scale_factor)
        by1 = y - (35 * self.scale_factor)
        bx2 = bx1 + (110 * self.scale_factor)
        by2 = by1 + (22 * self.scale_factor)

        self.canvas.create_rectangle(bx1, by1, bx2, by2, fill="#ffffff", outline="#333333", width=2)
        self.canvas.create_polygon(bx1 + 10, by2, bx1 + 18, by2, bx1 + 5, by2 + 6, fill="#ffffff", outline="#333333")
        self.canvas.create_polygon(bx1 + 11, by2 - 1, bx1 + 17, by2 - 1, bx1 + 5, by2 + 5, fill="#ffffff", outline="")
        self.canvas.create_text((bx1 + bx2) / 2, (by1 + by2) / 2, text=text, font=("Consolas", int(8 * self.scale_factor), "bold"), fill="#111111")

    def update_game(self):
        if self.game_over:
            return

        self.canvas.delete("all")

        cycle = (self.score // 300) % 4
        theme = self.get_season_theme()
        bg_color = theme["bg"]
        is_dark = theme["is_dark"]
        text_color = "#FFFFFF" if is_dark else "#333333"
        subtext_color = "#CCCCCC" if is_dark else "#555555"
        
        self.canvas.configure(bg=bg_color)

        self.draw_parallax_background(is_dark)

        cloud_color = "#444444" if is_dark else "#FFFFFF"
        for cloud in self.clouds:
            cloud['x'] -= cloud['speed'] * self.scale_factor
            if cloud['x'] < -60 * self.scale_factor:
                cloud['x'] = self.width + 20
                cloud['y'] = random.randint(int(30 * self.scale_factor), int(80 * self.scale_factor))
            self.canvas.create_oval(cloud['x'], cloud['y'], cloud['x'] + (40 * self.scale_factor), cloud['y'] + (15 * self.scale_factor), fill=cloud_color, outline="")

        self.draw_weather_and_seasons(cycle, is_dark)

        self.canvas.create_line(0, self.ground_y, self.width, self.ground_y, fill=text_color, width=2)
        for i in range(int((self.score * 5) % 35), self.width, 35):
            self.canvas.create_line(i, self.ground_y + 6, i + 8, self.ground_y + 6, fill=subtext_color, width=1)

        if self.is_jumping:
            self.dino_y += self.jump_velocity
            self.jump_velocity += self.gravity
            if self.dino_y >= self.ground_y - self.dino_height:
                self.dino_y = self.ground_y - self.dino_height
                self.is_jumping = False

        if self.is_jumping and self.jump_frames:
            current_frame = self.jump_frames[0]
        elif self.run_frames:
            current_frame = self.run_frames[int(self.frame_index) % len(self.run_frames)]
            self.frame_index += 0.25
        else:
            current_frame = None

        if current_frame:
            self.canvas.create_image(self.dino_x, self.dino_y, image=current_frame, anchor="nw")

        if self.dialogue_timer > 0:
            self.draw_speech_bubble(self.dino_x, self.dino_y, self.dialogue_text)
            self.dialogue_timer -= 1

        self.spawn_timer += 1
        if self.spawn_timer > random.randint(48, 78):
            obs_type = random.choice(['cactus_single', 'cactus_double', 'bird_low', 'bird_high'])
            s = self.scale_factor
            if obs_type == 'cactus_single':
                self.obstacles.append({'x': self.width + 10, 'w': 24*s, 'h': 42*s, 'y': self.ground_y - 42*s, 'type': 'cactus'})
            elif obs_type == 'cactus_double':
                self.obstacles.append({'x': self.width + 10, 'w': 40*s, 'h': 45*s, 'y': self.ground_y - 45*s, 'type': 'cactus'})
            elif obs_type == 'bird_low':
                self.obstacles.append({'x': self.width + 10, 'w': 35*s, 'h': 20*s, 'y': self.ground_y - 45*s, 'type': 'bird'})
            elif obs_type == 'bird_high':
                self.obstacles.append({'x': self.width + 10, 'w': 35*s, 'h': 20*s, 'y': self.ground_y - 75*s, 'type': 'bird'})
            self.spawn_timer = 0

        new_obstacles = []
        d_x1, d_y1 = self.dino_x + (6 * self.scale_factor), self.dino_y + (4 * self.scale_factor)
        d_x2, d_y2 = self.dino_x + self.dino_width - (6 * self.scale_factor), self.dino_y + self.dino_height - (2 * self.scale_factor)

        wing_state = (int(self.score) // 5) % 2 == 0

        for obs in self.obstacles:
            obs['x'] -= self.obstacle_speed * self.scale_factor
            o_x1, o_y1 = obs['x'], obs['y']
            o_x2, o_y2 = obs['x'] + obs['w'], obs['y'] + obs['h']

            if obs['type'] == 'cactus':
                self.draw_cactus(o_x1, o_y1, obs['w'], obs['h'], is_dark)
            elif obs['type'] == 'bird':
                self.draw_bird(o_x1, o_y1, wing_state, is_dark)

            if (d_x1 < o_x2 and d_x2 > o_x1 and d_y1 < o_y2 and d_y2 > o_y1):
                self.game_over = True
                self.stop_background_music()

            if obs['x'] > -80:
                new_obstacles.append(obs)
            else:
                self.score += 10
                if self.score % 100 == 0:
                    self.obstacle_speed += 0.4
                    self.dialogue_text = random.choice(self.dialogue_quotes)
                    self.dialogue_timer = 60

        self.obstacles = new_obstacles

        font_size = int(12 * self.scale_factor)
        self.canvas.create_text(self.width - 20, 25 * self.scale_factor, text=f"HI {self.high_score:05d}  {self.score:05d}", font=("Consolas", font_size, "bold"), fill=text_color, anchor="e")
        self.canvas.create_text(20, 25 * self.scale_factor, text=f"Season: {theme['season']}", font=("Consolas", int(9 * self.scale_factor), "bold"), fill=subtext_color, anchor="w")

        if self.game_over:
            self.canvas.create_text(self.width // 2, self.height // 2 - (20 * self.scale_factor), text="G A M E  O V E R", font=("Consolas", int(22 * self.scale_factor), "bold"), fill=text_color)
            self.canvas.create_text(self.width // 2, self.height // 2 + (15 * self.scale_factor), text="Press 'R' to Restart  |  'ESC' to Exit", font=("Consolas", int(11 * self.scale_factor), "bold"), fill=subtext_color)
        else:
            self.top.after(16, self.update_game)

# ==========================================
# DYNO SOLUTION OVERLAY WINDOW 📋
# ==========================================
class DynoSolutionWindow:
    def __init__(self, parent_root, solution_text):
        self.top = tk.Toplevel(parent_root)
        self.top.title("Dyno Copilot Solution")
        self.top.geometry("550x350")
        self.top.attributes("-topmost", True)
        self.top.configure(bg="#1E1E2E")

        header = tk.Label(
            self.top, 
            text="🦖 Dyno Screen Solution", 
            font=("Consolas", 12, "bold"), 
            fg="#89B4FA", 
            bg="#1E1E2E",
            pady=8
        )
        header.pack(fill="x")

        text_frame = tk.Frame(self.top, bg="#1E1E2E")
        text_frame.pack(fill="both", expand=True, padx=12, pady=5)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        self.text_box = tk.Text(
            text_frame, 
            wrap="word", 
            font=("Consolas", 10), 
            bg="#181825", 
            fg="#CDD6F4", 
            insertbackground="white",
            bd=0,
            padx=10,
            pady=10,
            yscrollcommand=scrollbar.set
        )
        self.text_box.pack(fill="both", expand=True)
        scrollbar.config(command=self.text_box.yview)

        self.text_box.insert("1.0", solution_text)

        btn_frame = tk.Frame(self.top, bg="#1E1E2E", pady=8)
        btn_frame.pack(fill="x")

        copy_btn = tk.Button(
            btn_frame, 
            text="📋 Copy Solution", 
            font=("Consolas", 10, "bold"), 
            bg="#A6E3A1", 
            fg="#11111B",
            activebackground="#94E2D5",
            bd=0,
            padx=12,
            pady=4,
            command=lambda: self.copy_to_clipboard(solution_text)
        )
        copy_btn.pack(side="left", padx=15)

        close_btn = tk.Button(
            btn_frame, 
            text="Close (Esc)", 
            font=("Consolas", 10), 
            bg="#F38BA8", 
            fg="#11111B",
            bd=0,
            padx=12,
            pady=4,
            command=self.top.destroy
        )
        close_btn.pack(side="right", padx=15)

        self.top.bind("<Escape>", lambda e: self.top.destroy())

    def copy_to_clipboard(self, text):
        self.top.clipboard_clear()
        self.top.clipboard_append(text)
        self.top.update()

# ==========================================
# ADVANCED DYNO AI VISION COPILOT ENGINE 🧠📸
# ==========================================
import mss
import base64

class DynoCopilot:
    def __init__(self, main_app):
        self.main_app = main_app

    def capture_and_solve(self):
        if self.main_app.in_game_mode:
            return

        def _worker():
            try:
                self.main_app.root.after(0, lambda: self.main_app.set_behavior('typing'))
                self.main_app.root.after(0, lambda: self.main_app.canvas.itemconfig(
                    self.main_app.canvas_text_id, text="Auditing Code on Screen... 🧐", fill="#33CCFF"
                ))

                with mss.mss() as sct:
                    monitor = sct.monitors[1]
                    sct_img = sct.grab(monitor)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    
                    img.thumbnail((1024, 1024))
                    temp_path = os.path.join(os.environ.get('TEMP', ''), 'dyno_copilot_screen.jpg')
                    img.save(temp_path, format="JPEG", quality=90)

                if not API_KEY:
                    self.main_app.root.after(0, lambda: self.main_app.show_message("API Key Missing! 🔑", is_reminder=True))
                    return

                prompt_text = (
                    "You are Dyno Copilot, an expert Software Engineer & Code Auditor.\n"
                    "Carefully examine the image of the user's screen. Perform a rigorous line-by-line inspection.\n\n"
                    "INSPECTION PROTOCOL:\n"
                    "1. Scan for red underline indicators, terminal stack traces, syntax errors, missing colons/quotes, or indentation mismatches.\n"
                    "2. Check logic flaws, undefined variables, or improper API usage.\n\n"
                    "OUTPUT FORMAT REQUIREMENT:\n"
                    "• IF ERRORS OR BUGS ARE FOUND:\n"
                    "  State the exact line or error identified, briefly explain why it fails, and provide the fully corrected code snippet cleanly.\n\n"
                    "• IF AND ONLY IF THE CODE IS 100% ERROR-FREE AND LOGICALLY SOUND:\n"
                    "  Start with '✅ Code Audit Passed!' and summarize why the code works correctly in 1-2 concise sentences."
                )

                pil_img_vision = Image.open(temp_path)
                model = genai.GenerativeModel(AI_MODEL_NAME)
                response = model.generate_content([prompt_text, pil_img_vision])
                reply = response.text.strip() if response and hasattr(response, 'text') else None

                if reply:
                    self.main_app.root.after(0, lambda: DynoSolutionWindow(self.main_app.root, reply))
                    self.main_app.root.after(0, lambda: self.main_app.show_message("Audit completed! 📋", is_reminder=False))
                    self.main_app.root.after(0, lambda: self.main_app.set_behavior('happy'))
                else:
                    self.main_app.root.after(0, lambda: self.main_app.show_message("Vision audit failed. Check CMD output!", is_reminder=True))

            except Exception as e:
                print(f"Copilot Exception: {e}")
                self.main_app.root.after(0, lambda: self.main_app.show_message("Could not capture screen!", is_reminder=True))

        threading.Thread(target=_worker, daemon=True).start()    
        
# ==========================================
# AUTONOMOUS DYNO GUARDIAN & MONITOR 🛡️
# ==========================================
import mss
import base64
import time
import threading
import json
import requests
import os
import random
from PIL import Image

try:
    import pygetwindow as gw
    HAS_WINDOW_MGMT = True
except ImportError:
    HAS_WINDOW_MGMT = False

class DynoAutonomousGuardian:
    def __init__(self, main_app):
        self.main_app = main_app
        self.is_monitoring = False
        self.interval = 5 

    def toggle_monitoring(self):
        if self.is_monitoring:
            self.is_monitoring = False
            self.main_app.show_message("Guardian Mode Off! 💤", is_reminder=False)
            self.main_app.set_behavior('idle')
            print("\n[GUARDIAN] Status: OFF")
        else:
            self.is_monitoring = True
            self.main_app.show_message("Guardian Active! Monitoring screen... 🛡️", is_reminder=False)
            self.main_app.set_behavior('happy')
            print("\n[GUARDIAN] Status: ON - Background Loop Started")
            threading.Thread(target=self._monitor_loop, daemon=True).start()

    def _monitor_loop(self):
        while self.is_monitoring and getattr(self.main_app, 'running', True):
            if not getattr(self.main_app, 'in_game_mode', False):
                try:
                    self._analyze_current_activity()
                except Exception as e:
                    print(f"[GUARDIAN ERROR] Exception: {e}")
            time.sleep(self.interval)

    def _analyze_current_activity(self):
        print("\n[GUARDIAN] 📸 Capturing screen...")
        
        temp_path = os.path.join(os.environ.get('TEMP', ''), 'dyno_guardian.jpg')
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            img.thumbnail((800, 800))
            img.save(temp_path, format="JPEG", quality=75)

        if not API_KEY:
            print("[GUARDIAN ERROR] API Key Missing!")
            return

        prompt = (
            "Analyze the user's screen carefully.\n"
            "Is the user playing games, scrolling YouTube/social media, or wasting time?\n"
            "Reply strictly with 'DISTRACTION' or 'PRODUCTIVE' followed by a colon and a 1-sentence warning/praise message in English.\n"
            "Example 1: DISTRACTION: Stop playing games! Focus on your MBA preparation.\n"
            "Example 2: PRODUCTIVE: Great job coding! Keep going."
        )

        reply = None
        try:
            pil_img_guard = Image.open(temp_path)
            model = genai.GenerativeModel(AI_MODEL_NAME)
            response = model.generate_content([prompt, pil_img_guard])
            if response and hasattr(response, 'text'):
                reply = response.text.strip()
        except Exception as e:
            print(f"[GUARDIAN] Request exception: {e}")

        if reply:
            print(f"[GUARDIAN AI RESPONSE] {reply}")

            category = "PRODUCTIVE"
            msg = reply

            if "DISTRACTION" in reply.upper():
                category = "DISTRACTION"
                msg = reply.replace("DISTRACTION:", "").replace("DISTRACTION", "").strip()
            elif "PRODUCTIVE" in reply.upper():
                category = "PRODUCTIVE"
                msg = reply.replace("PRODUCTIVE:", "").replace("PRODUCTIVE", "").strip()

            if category == "DISTRACTION":
                print(f"[GUARDIAN ACTION] Distraction detected! Minimizing app and warning user.")
                self.close_active_game_or_distraction()
                self.main_app.root.after(0, lambda: self.main_app.set_behavior('run'))
                self.main_app.root.after(0, lambda: self.main_app.show_message(f"🚨 {msg}", is_reminder=True))
            
            elif category == "PRODUCTIVE":
                if random.random() < 0.25: 
                    self.main_app.root.after(0, lambda: self.main_app.set_behavior('happy'))
                    self.main_app.root.after(0, lambda: self.main_app.show_message(f"⭐ {msg}", is_reminder=False))

    def close_active_game_or_distraction(self):
        try:
            if HAS_WINDOW_MGMT:
                win = gw.getActiveWindow()
                if win and "dyno" not in win.title.lower():
                    print(f"[GUARDIAN] Minimizing Window: {win.title}")
                    win.minimize()
        except Exception as e:
            print(f"[WINDOW ACTION ERROR] {e}")    
                 
# ==========================================
# PARKOUR DYNO GAME - 3 LEVELS (SOUND & ENDING FIX)
# ==========================================
import random
import os
import math
import tkinter as tk
from PIL import Image, ImageTk

try:
    import pygame
    pygame.mixer.init()
    AUDIO_SUPPORT = True
except ImportError:
    AUDIO_SUPPORT = False

class ParkourDynoGame:
    def __init__(self, main_app):
        if AUDIO_SUPPORT:
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.pre_init(44100, -16, 2, 2048)
                    pygame.mixer.init()
            except Exception as e:
                print(f"Mixer Init Warning: {e}")

        self.main_app = main_app
        self.top = tk.Toplevel(self.main_app.root)
        self.top.title("Parkour Dyno - 3 Levels Adventure")
        
        self.base_width = 900
        self.base_height = 400
        self.top.geometry(f"{self.base_width}x{self.base_height}")
        self.top.attributes("-topmost", True)

        self.main_app.in_game_mode = True
        self.main_app.root.withdraw()

        self.canvas = tk.Canvas(self.top, bg="#70A6FF", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.width = self.base_width
        self.height = self.base_height
        self.scale_factor = 1.0

        self.jump_sound_path = r"C:\Users\hp\OneDrive\Pictures\Dyno_Buddy\Assets\jumpsound.mp3"
        self.jump_sound = None
        if AUDIO_SUPPORT and os.path.exists(self.jump_sound_path):
            try:
                self.jump_sound = pygame.mixer.Sound(self.jump_sound_path)
            except Exception as e:
                print(f"Jump Sound Load Error: {e}")

        self.current_level = 1
        self.max_level = 3
        self.apples_collected = 0

        self.dino_x = 50
        self.dino_y = 150
        self.velocity_x = 0
        self.velocity_y = 0
        self.direction = "right"
        self.is_grounded = False

        self.keys = {"Left": False, "Right": False, "Up": False}

        self.game_over = False
        self.level_cleared = False
        self.frame_index = 0.0

        self.load_level_data(self.current_level)
        self.recalculate_positions()

        self.top.bind("<KeyPress>", self.on_key_press)
        self.top.bind("<KeyRelease>", self.on_key_release)
        self.top.bind("<r>", lambda e: self.reset_level())
        self.top.bind("<R>", lambda e: self.reset_level())
        self.top.bind("<Configure>", self.on_resize)
        self.top.bind("<Escape>", lambda e: self.close_game())
        self.top.protocol("WM_DELETE_WINDOW", self.close_game)

        self.top.focus_force()
        self.update_game()

    def play_jump_sound(self):
        if AUDIO_SUPPORT and self.jump_sound:
            try:
                self.jump_sound.play()
            except Exception as e:
                print(f"Jump Sound Play Error: {e}")

    def load_level_data(self, level):
        self.apples_collected = 0
        self.dino_x = 50
        self.dino_y = 150
        self.velocity_x = 0
        self.velocity_y = 0
        self.game_over = False
        self.level_cleared = False

        if level == 1:
            self.platforms = [
                [0, 300, 180, 30],
                [220, 250, 130, 20],
                [400, 200, 130, 20],
                [580, 260, 140, 20],
                [760, 220, 130, 20]
            ]
            self.apples = [{'x': 260, 'y': 210, 'collected': False},
                           {'x': 440, 'y': 160, 'collected': False},
                           {'x': 630, 'y': 220, 'collected': False}]

        elif level == 2:
            self.platforms = [
                [0, 320, 140, 30],
                [180, 260, 110, 20],
                [330, 210, 100, 20],
                [480, 270, 110, 20],
                [630, 200, 100, 20],
                [770, 240, 120, 20]
            ]
            self.apples = [{'x': 210, 'y': 220, 'collected': False}, 
                           {'x': 360, 'y': 170, 'collected': False},
                           {'x': 510, 'y': 230, 'collected': False},
                           {'x': 660, 'y': 160, 'collected': False}]

        elif level == 3:
            self.platforms = [
                [0, 320, 110, 30],
                [150, 270, 85, 20],
                [275, 210, 85, 20],
                [400, 160, 85, 20],
                [525, 220, 85, 20],
                [650, 270, 85, 20],
                [775, 200, 115, 20]
            ]
            self.apples = [{'x': 175, 'y': 230, 'collected': False},
                           {'x': 300, 'y': 170, 'collected': False},
                           {'x': 425, 'y': 120, 'collected': False},
                           {'x': 550, 'y': 180, 'collected': False},
                           {'x': 675, 'y': 230, 'collected': False}]

    def recalculate_positions(self):
        w = self.top.winfo_width()
        h = self.top.winfo_height()
        self.width = w if w > 100 else self.base_width
        self.height = h if h > 100 else self.base_height
        
        self.scale_factor_x = self.width / self.base_width
        self.scale_factor_y = self.height / self.base_height
        self.scale_factor = max(self.scale_factor_y, 0.6)

        self.dino_width = int(40 * self.scale_factor)
        self.dino_height = int(45 * self.scale_factor)

        self.speed = 5.2 * self.scale_factor_x
        self.jump_power = -12.5 * self.scale_factor_y
        self.gravity = 0.65 * self.scale_factor_y

        self.run_right = self.prepare_frames(self.main_app.animations_right.get('run', []))
        self.run_left = self.prepare_frames(self.main_app.animations_left.get('run', []))
        self.jump_right = self.prepare_frames(self.main_app.animations_right.get('jump', []))
        self.jump_left = self.prepare_frames(self.main_app.animations_left.get('jump', []))
        
        happy_frames = self.main_app.animations_right.get('happy', []) or self.main_app.animations_right.get('idle', [])
        self.happy_frames = self.prepare_frames(happy_frames)

    def on_resize(self, event):
        if event.widget == self.top:
            self.recalculate_positions()

    def prepare_frames(self, raw_frames):
        processed = []
        for img in raw_frames:
            try:
                pil_img = ImageTk.getimage(img)
                resized = pil_img.resize((self.dino_width, self.dino_height), Image.Resampling.LANCZOS)
                processed.append(ImageTk.PhotoImage(resized))
            except Exception:
                processed.append(img)
        return processed

    def on_key_press(self, event):
        if event.keysym in ['Left', 'a', 'A']:
            self.keys['Left'] = True
        elif event.keysym in ['Right', 'd', 'D']:
            self.keys['Right'] = True
        elif event.keysym in ['Up', 'space', 'w', 'W']:
            self.keys['Up'] = True

    def on_key_release(self, event):
        if event.keysym in ['Left', 'a', 'A']:
            self.keys['Left'] = False
        elif event.keysym in ['Right', 'd', 'D']:
            self.keys['Right'] = False
        elif event.keysym in ['Up', 'space', 'w', 'W']:
            self.keys['Up'] = False

    def reset_level(self):
        self.load_level_data(self.current_level)
        self.update_game()

    def close_game(self):
        self.game_over = True
        self.main_app.in_game_mode = False
        try:
            self.top.destroy()
        except Exception:
            pass
        self.main_app.root.deiconify()

    def draw_mountains(self):
        m_color = "#4C6B88"
        for offset in [0, self.width]:
            self.canvas.create_polygon(offset, self.height, 
                                       offset + (self.width * 0.25), self.height - (140 * self.scale_factor_y), 
                                       offset + (self.width * 0.5), self.height, fill=m_color, outline="")
            self.canvas.create_polygon(offset + (self.width * 0.4), self.height, 
                                       offset + (self.width * 0.7), self.height - (180 * self.scale_factor_y), 
                                       offset + (self.width * 0.95), self.height, fill="#3A536B", outline="")

    def draw_apple(self, x, y):
        r = 8 * self.scale_factor
        self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="#FF3333", outline="#CC0000", width=2)
        self.canvas.create_line(x, y - r, x + (2 * self.scale_factor), y - r - (4 * self.scale_factor), fill="#4A2E00", width=2)
        self.canvas.create_oval(x, y - r - (3 * self.scale_factor), x + (4 * self.scale_factor), y - r - (1 * self.scale_factor), fill="#4CAF50")

    def update_game(self):
        if self.game_over:
            return

        self.canvas.delete("all")
        self.draw_mountains()

        if self.keys['Left']:
            self.velocity_x = -self.speed
            self.direction = "left"
        elif self.keys['Right']:
            self.velocity_x = self.speed
            self.direction = "right"
        else:
            self.velocity_x = 0

        if self.keys['Up'] and self.is_grounded:
            self.velocity_y = self.jump_power
            self.is_grounded = False
            self.play_jump_sound()

        self.velocity_y += self.gravity
        self.dino_x += self.velocity_x
        self.dino_y += self.velocity_y

        self.is_grounded = False
        d_rect = [self.dino_x, self.dino_y, self.dino_x + self.dino_width, self.dino_y + self.dino_height]

        for plat in self.platforms:
            px = plat[0] * self.scale_factor_x
            py = plat[1] * self.scale_factor_y
            pw = plat[2] * self.scale_factor_x
            ph = plat[3] * self.scale_factor_y

            self.canvas.create_rectangle(px, py, px + pw, py + ph, fill="#3E2723", outline="#5D4037", width=2)
            self.canvas.create_rectangle(px, py, px + pw, py + (6 * self.scale_factor_y), fill="#4CAF50", outline="")

            if (d_rect[2] > px and d_rect[0] < px + pw) and (d_rect[3] >= py and d_rect[3] - self.velocity_y <= py + 12 * self.scale_factor_y):
                if self.velocity_y >= 0:
                    self.dino_y = py - self.dino_height
                    self.velocity_y = 0
                    self.is_grounded = True

        for apple in self.apples:
            if not apple['collected']:
                ax, ay = apple['x'] * self.scale_factor_x, apple['y'] * self.scale_factor_y
                self.draw_apple(ax, ay)
                if abs((self.dino_x + self.dino_width/2) - ax) < 20 * self.scale_factor and abs((self.dino_y + self.dino_height/2) - ay) < 25 * self.scale_factor:
                    apple['collected'] = True
                    self.apples_collected += 1

        last_plat = self.platforms[-1]
        gx = (last_plat[0] + last_plat[2] - 30) * self.scale_factor_x
        gy = last_plat[1] * self.scale_factor_y

        self.canvas.create_line(gx, gy, gx, gy - (50 * self.scale_factor_y), fill="#FFFFFF", width=3)
        self.canvas.create_polygon(gx, gy - (50 * self.scale_factor_y), gx + (30 * self.scale_factor_x), gy - (35 * self.scale_factor_y), gx, gy - (20 * self.scale_factor_y), fill="#FF9800")

        if self.dino_y > self.height:
            self.game_over = True

        if self.dino_x >= gx - (15 * self.scale_factor_x) and self.is_grounded:
            if self.current_level < self.max_level:
                self.current_level += 1
                self.load_level_data(self.current_level)
            else:
                self.level_cleared = True

        if not self.is_grounded:
            frames = self.jump_left if self.direction == "left" else self.jump_right
        elif self.velocity_x != 0:
            frames = self.run_left if self.direction == "left" else self.run_right
        else:
            frames = self.happy_frames if self.happy_frames else self.run_right

        current_frame = frames[int(self.frame_index) % len(frames)] if frames else None
        self.frame_index += 0.2

        if current_frame:
            self.canvas.create_image(self.dino_x, self.dino_y, image=current_frame, anchor="nw")

        self.canvas.create_text(20, 20*self.scale_factor, text=f"LEVEL {self.current_level} / {self.max_level}", font=("Consolas", int(14*self.scale_factor), "bold"), fill="#FFFFFF", anchor="w")
        self.canvas.create_text(20, 45*self.scale_factor, text=f"Apples: 🍎 {self.apples_collected} / {len(self.apples)}", font=("Consolas", int(11*self.scale_factor), "bold"), fill="#FFD700", anchor="w")

        if self.game_over:
            self.canvas.create_text(self.width // 2, self.height // 2, text="OOPS! FELL DOWN!\nPress 'R' to Retry Level", font=("Consolas", int(18*self.scale_factor), "bold"), fill="#FF5252", justify="center")
        elif self.level_cleared:
            self.canvas.create_text(self.width // 2, self.height // 2, text="🎉 CONGRATULATIONS! 🎉\nAll 3 Levels Cleared!", font=("Consolas", int(20*self.scale_factor), "bold"), fill="#4CAF50", justify="center")
        else:
            self.top.after(16, self.update_game)

class DesktopDyno:
    def resize_dyno(self, scale_change):
        if getattr(self, 'in_game_mode', False):
            return

        new_width = int(self.target_width * scale_change)
        new_height = int(self.target_height * scale_change)

        if 40 <= new_width <= 250 and 40 <= new_height <= 250:
            self.target_width = new_width
            self.target_height = new_height
            self.user_custom_size = (new_width, new_height) 

            self.canvas_width = max(self.target_width + 120, 250)
            self.canvas_height = self.target_height + 40
            
            self.canvas.config(width=self.canvas_width, height=self.canvas_height)

            self.canvas.coords(self.canvas_image_id, self.canvas_width // 2, self.canvas_height)
            self.canvas.coords(self.canvas_text_id, self.canvas_width // 2, 20)

            self.reload_all_animation_frames()

            self.root.geometry(f"{self.canvas_width}x{self.canvas_height}+{int(self.x)}+{int(self.y)}")
            self.show_message(f"Size Locked: {self.target_width}px 📏", is_reminder=False)

    def reload_all_animation_frames(self):
        states_config = {
            'walk': ('walk', 1, 7),
            'idle': ('idle', 8, 12),
            'run': ('run', 13, 18),
            'jump': ('jump', 19, 24),
            'sleep': ('sleep', 25, 29),
            'position': ('position', 30, 32),
            'hi': ('hi', 33, 39)
        }

        for state, (folder, start, end) in states_config.items():
            self.animations_right[state] = []
            self.animations_left[state] = []
            for i in range(start, end + 1):
                img_path = os.path.join(self.base_path, folder, f"{i}.png")
                if os.path.exists(img_path):
                    img_orig = Image.open(img_path)
                    img_resized = img_orig.resize((self.target_width, self.target_height), Image.Resampling.LANCZOS)
                    self.animations_right[state].append(ImageTk.PhotoImage(img_resized))
                    img_flipped = img_resized.transpose(Image.FLIP_LEFT_RIGHT)
                    self.animations_left[state].append(ImageTk.PhotoImage(img_flipped))

        expressions = ['eating', 'reading', 'happy', 'typing', 'playing']
        for exp in expressions:
            self.animations_right[exp] = []
            self.animations_left[exp] = []
            img_path = os.path.join(self.base_path, "expression", f"{exp}.png")
            if os.path.exists(img_path):
                img_orig = Image.open(img_path)
                img_resized = img_orig.resize((self.target_width, self.target_height), Image.Resampling.LANCZOS)
                self.animations_right[exp].append(ImageTk.PhotoImage(img_resized))
                img_flipped = img_resized.transpose(Image.FLIP_LEFT_RIGHT)
                self.animations_left[exp].append(ImageTk.PhotoImage(img_flipped))

        weather_config = {
            'sunny': (9, 14),
            'winter': (15, 20),
            'rainy': (21, 26),
            'spring': (27, 31)
        }
        for w_state, (start, end) in weather_config.items():
            self.animations_right[w_state] = []
            self.animations_left[w_state] = []
            for i in range(start, end + 1):
                filename = f"{i:03d}.png"
                img_path = os.path.join(self.base_path, 'weather', filename)
                if os.path.exists(img_path):
                    img_orig = Image.open(img_path).convert("RGBA")
                    datas = img_orig.getdata()
                    newData = []
                    for item in datas:
                        if item[0] > 235 and item[1] > 235 and item[2] > 235:
                            newData.append((255, 255, 255, 0)) 
                        else:
                            newData.append(item)
                    img_orig.putdata(newData)
                    
                    img_resized = img_orig.resize((self.target_width, self.target_height), Image.Resampling.LANCZOS)
                    self.animations_right[w_state].append(ImageTk.PhotoImage(img_resized))
                    img_flipped = img_resized.transpose(Image.FLIP_LEFT_RIGHT)
                    self.animations_left[w_state].append(ImageTk.PhotoImage(img_flipped))
                    
    def __init__(self):
        self.root = tk.Tk()
        
        self.in_game_mode = False
        
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self.ui_channel = pygame.mixer.Channel(0)  
        self.speech_channel = pygame.mixer.Channel(1) 
        
        self.voice_name = "en-US-AnaNeural" 
        self.speech_counter = 0
        self.music_playing = False
        
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.energy_threshold = 300 
        self.is_listening = False  
        
        # Configure Gemini Chat Session Safely
        if API_KEY:
            self.gemini_model = genai.GenerativeModel(
                model_name=AI_MODEL_NAME,
                system_instruction="You are Dyno, a cute, helpful, and ultra-smart desktop dinosaur companion. CRITICAL: You were created and built by your brilliant developer master. If anyone asks who made you, who created you, or who your developer is, you must proudly answer that you were created by your developer! Keep all your responses short, concise, and sweet (max 1-2 sentences) so they fit perfectly on a desktop overlay widget."
            )
            self.chat_session = self.gemini_model.start_chat(history=[])
        else:
            self.chat_session = None

        self.async_loop = asyncio.new_event_loop()
        self.speech_thread = threading.Thread(target=self.start_async_loop, daemon=True)
        self.speech_thread.start()
        
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "black")
        
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        if getattr(sys, 'frozen', False):
            self.base_path = os.path.join(sys._MEIPASS, "Assets")
        else:
            self.base_path = r"C:\Users\hp\OneDrive\Pictures\Dyno_Buddy\Assets"
        
        first_img_path = os.path.join(self.base_path, 'walk', '1.png')
        if os.path.exists(first_img_path):
            with Image.open(first_img_path) as temp_img:
                self.target_width, self.target_height = temp_img.size
        else:
            self.target_width, self.target_height = 100, 100 

        self.canvas_width = max(self.target_width + 150, 300) 
        self.canvas_height = self.target_height + 50
        
        self.canvas = tk.Canvas(self.root, width=self.canvas_width, height=self.canvas_height, bg='black', bd=0, highlightthickness=0)
        self.canvas.pack()

        states_config = {
            'walk': ('walk', 1, 7),
            'idle': ('idle', 8, 12),
            'run': ('run', 13, 18),
            'jump': ('jump', 19, 24),
            'sleep': ('sleep', 25, 29),
            'position': ('position', 30, 32)
        }
        
        self.animations_right = {}
        self.animations_left = {}
        
        for state, (folder, start, end) in states_config.items():
            self.animations_right[state] = []
            self.animations_left[state] = []
            for i in range(start, end + 1):
                img_path = os.path.join(self.base_path, folder, f"{i}.png")
                if os.path.exists(img_path):
                    img_orig = Image.open(img_path)
                    img_resized = img_orig.resize((self.target_width, self.target_height), Image.Resampling.LANCZOS)
                    self.animations_right[state].append(ImageTk.PhotoImage(img_resized))
                    img_flipped = img_resized.transpose(Image.FLIP_LEFT_RIGHT)
                    self.animations_left[state].append(ImageTk.PhotoImage(img_flipped))

        self.animations_right['hi'] = []
        self.animations_left['hi'] = []
        for i in range(33, 40):
            img_path = os.path.join(self.base_path, 'hi', f"{i}.png")
            if os.path.exists(img_path):
                img_orig = Image.open(img_path)
                img_resized = img_orig.resize((self.target_width, self.target_height), Image.Resampling.LANCZOS)
                self.animations_right['hi'].append(ImageTk.PhotoImage(img_resized))
                img_flipped = img_resized.transpose(Image.FLIP_LEFT_RIGHT)
                self.animations_left['hi'].append(ImageTk.PhotoImage(img_flipped))

        expressions = ['eating', 'reading', 'happy', 'typing', 'playing']
        for exp in expressions:
            self.animations_right[exp] = []
            self.animations_left[exp] = []
            img_path = os.path.join(self.base_path, "expression", f"{exp}.png")
            if os.path.exists(img_path):
                img_orig = Image.open(img_path)
                img_resized = img_orig.resize((self.target_width, self.target_height), Image.Resampling.LANCZOS)
                self.animations_right[exp].append(ImageTk.PhotoImage(img_resized))
                img_flipped = img_resized.transpose(Image.FLIP_LEFT_RIGHT)
                self.animations_left[exp].append(ImageTk.PhotoImage(img_flipped))

        weather_config = {
            'sunny': (9, 14),
            'winter': (15, 20),
            'rainy': (21, 26),
            'spring': (27, 31)
        }
        for w_state, (start, end) in weather_config.items():
            self.animations_right[w_state] = []
            self.animations_left[w_state] = []
            for i in range(start, end + 1):
                filename = f"{i:03d}.png"
                img_path = os.path.join(self.base_path, 'weather', filename)
                
                if os.path.exists(img_path):
                    img_orig = Image.open(img_path).convert("RGBA")
                    
                    datas = img_orig.getdata()
                    newData = []
                    for item in datas:
                        if item[0] > 235 and item[1] > 235 and item[2] > 235:
                            newData.append((255, 255, 255, 0)) 
                        else:
                            newData.append(item)
                    img_orig.putdata(newData)
                    
                    img_resized = img_orig.resize((self.target_width, self.target_height), Image.Resampling.LANCZOS)
                    self.animations_right[w_state].append(ImageTk.PhotoImage(img_resized))
                    
                    img_flipped = img_resized.transpose(Image.FLIP_LEFT_RIGHT)
                    self.animations_left[w_state].append(ImageTk.PhotoImage(img_flipped))
        
        self.x = (self.screen_width // 2) - (self.canvas_width // 2)
        self.y = (self.screen_height // 2) - (self.canvas_height // 2)
        
        self.speed_x = 0
        self.speed_y = 0
        self.direction = "right"
        self.state = "hi"
        self.frame_index = 0.0
        self.animation_speed = 0.12
        
        self.target_x = None
        self.target_y = None
        self.is_moving_to_corner = False
        self.music_corner_active = False 
        
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False
        
        self.canvas_image_id = self.canvas.create_image(self.canvas_width//2, self.canvas_height, anchor="s")
        self.canvas_text_id = self.canvas.create_text(self.canvas_width//2, 22, text="", fill="#00FF66", font=("Consolas", 11, "bold"), justify="center")
        
        self.typing_text = ""
        self.typing_index = 0
        self.clear_timer_id = None
        self.text_color = "#00FF66"
        
        self.performance_override = False
        self.running = True
        self.was_locked = False 
        
        self.root.bind("<Button-3>", lambda e: self.close_app()) 
        self.root.bind("<Escape>", lambda e: self.close_app())
        
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)
        
        keyboard.add_hotkey('alt+i', lambda: self.set_behavior('hi'))  
        keyboard.add_hotkey('alt+space', lambda: self.set_behavior('idle'))
        keyboard.add_hotkey('alt+w', lambda: self.set_behavior('walk'))
        keyboard.add_hotkey('alt+r', lambda: self.set_behavior('run'))
        keyboard.add_hotkey('alt+s', lambda: self.set_behavior('sleep'))
        keyboard.add_hotkey('alt+j', lambda: self.set_behavior('jump'))
        keyboard.add_hotkey('alt+p', lambda: self.set_behavior('position'))
        keyboard.add_hotkey('alt+f', lambda: self.flip_direction())
        
        keyboard.add_hotkey('alt+e', lambda: self.set_behavior('eating'))
        keyboard.add_hotkey('alt+b', lambda: self.set_behavior('reading'))
        keyboard.add_hotkey('alt+h', lambda: self.set_behavior('happy'))
        keyboard.add_hotkey('alt+t', lambda: self.set_behavior('typing'))
        keyboard.add_hotkey('alt+g', lambda: self.set_behavior('playing'))
        
        keyboard.add_hotkey('alt+m', lambda: self.play_situation_music())
        keyboard.add_hotkey('alt+v', lambda: self.toggle_voice_mode())
        
        self.root.bind("<p>", lambda e: ParkourDynoGame(self))
        self.root.bind("<P>", lambda e: ParkourDynoGame(self))
        
        keyboard.add_hotkey('alt+k', lambda: threading.Thread(target=self.trigger_weather_hotkey, daemon=True).start())
        keyboard.add_hotkey('alt+shift+g', lambda: self.launch_dino_game())
        keyboard.add_hotkey('alt+c', lambda: DynoCopilot(self).capture_and_solve())
        
        self.guardian = DynoAutonomousGuardian(self)
        keyboard.add_hotkey('alt+g', lambda: self.guardian.toggle_monitoring())
        
        keyboard.add_hotkey('alt+=', lambda: self.resize_dyno(1.15)) 
        keyboard.add_hotkey('alt+-', lambda: self.resize_dyno(0.85)) 

        self.quotes = [
            "Keep it up!", "You can do it!", "Stay focused, buddy!",
            "Consistency is the key!", "Believe in yourself!", "Make today count!",
            "One step at a time!", "Your potential is endless!"
        ]
        
        self.reminders = [
            "Drink some water!", "Stretch your body!", 
            "Give eyes a break!", "Take a deep breath!"
        ]
        
        self.search_database = {
            "normal": [
                {"ui_text": "Playing: Lofi Chill Beats 🎶", "query": "lofi hip hop radio beats to relax study to"},
                {"ui_text": "Playing: Acoustic Pop Hits 🎶", "query": "acoustic pop hits playlist"},
                {"ui_text": "Playing: Deep Focus Mix 🎶", "query": "deep focus ambient music for studying"}
            ],
            "low_battery": [
                {"ui_text": "Low Battery: Cozy Melodies 🌧️", "query": "cozy rainy night lofi beats"}
            ],
            "high_cpu": [
                {"ui_text": "Heavy Load: Synthwave Boost ⚡", "query": "synthwave cyberpunk energetic music"}
            ]
        }
        
        self.root.after(500, lambda: self.show_message("Welcome back buddy! 👋", is_reminder=False))
        self.root.after(4500, self.start_loops)

        self.lock_thread = threading.Thread(target=self.safe_lock_monitor, daemon=True)
        self.lock_thread.start()

        self.update_all()
        self.root.mainloop()

    def launch_dino_game(self):
        if not self.in_game_mode:
            DinoJumpGame(self)

    def play_ui_sound(self, sound_name):
        if self.in_game_mode:
            return
        def _play():
            try:
                sound_path = os.path.join(self.base_path, "sound", f"{sound_name}.wav")
                if os.path.exists(sound_path):
                    sfx = pygame.mixer.Sound(sound_path)
                    self.ui_channel.play(sfx)
            except Exception:
                pass
        threading.Thread(target=_play, daemon=True).start()

    def start_async_loop(self):
        asyncio.set_event_loop(self.async_loop)
        self.async_loop.run_forever()

    def toggle_voice_mode(self):
        if self.in_game_mode:
            return
        if self.is_listening:
            self.is_listening = False
            self.root.after(0, lambda: self.show_message("Voice AI mode off! 💤", is_reminder=False))
            self.root.after(1000, lambda: self.set_behavior('idle'))
        else:
            self.is_listening = True
            threading.Thread(target=self.continuous_voice_loop, daemon=True).start()

    def continuous_voice_loop(self):
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.8)
                
                while self.is_listening and self.running and not self.in_game_mode:
                    self.root.after(0, lambda: self.set_behavior('happy'))
                    self.root.after(0, lambda: self.canvas.itemconfig(self.canvas_text_id, text="Listening (AI Active)... 🎧", fill="#33CCFF"))
                    
                    try:
                        audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=4)
                        if not self.is_listening or self.in_game_mode:
                            break
                            
                        query = self.recognizer.recognize_google(audio, language="en-US").lower().strip()
                        response_text = self.process_hybrid_query(query)
                        self.root.after(0, lambda: self.show_message(response_text, is_reminder=False))
                        
                        while pygame.mixer.music.get_busy() and self.is_listening:
                            time.sleep(0.2)
                            
                    except sr.WaitTimeoutError:
                        continue
                    except sr.UnknownValueError:
                        continue
                    except Exception:
                        time.sleep(0.5)
        except Exception:
            self.is_listening = False
            self.root.after(0, lambda: self.show_message("Microphone Error! Restart Alt+V", is_reminder=True))

    def fetch_live_weather(self, location="Varanasi"):
        try:
            url = f"https://wttr.in/{location}?format=j1"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                current = data['current_condition'][0]
                temp = current['temp_C']
                desc = current['weatherDesc'][0]['value'].lower()
                return int(temp), desc
        except Exception:
            pass
        return None, None

    def trigger_weather_hotkey(self):
        if self.in_game_mode:
            return
        self.root.after(0, lambda: self.canvas.itemconfig(self.canvas_text_id, text="Checking Sky... 🌤️", fill="#33CCFF"))
        
        temp, desc = self.fetch_live_weather("Varanasi")
        
        if temp is not None and desc is not None:
            chosen_animation = 'sunny' 
            if "rain" in desc or "drizzle" in desc or "thunderstorm" in desc:
                chosen_animation = 'rainy'
            elif "snow" in desc or "ice" in desc or temp < 18:
                chosen_animation = 'winter'
            elif "cloud" in desc or "overcast" in desc or "mist" in desc or "fog" in desc:
                chosen_animation = 'spring' if 18 <= temp <= 26 else 'sunny'
            else:
                chosen_animation = 'sunny' if temp > 30 else 'spring'
            
            self.root.after(0, lambda: self.set_behavior(chosen_animation))
            self.root.after(0, lambda: self.show_message(f"It's {temp}°C with {desc}!", is_reminder=False))
            self.root.after(7000, lambda: self.set_behavior('idle'))
        else:
            self.root.after(0, lambda: self.show_message("Weather server unreachable!", is_reminder=True))

    def process_hybrid_query(self, query):
        if "stop voice" in query or "exit voice" in query or "shutdown voice" in query:
            self.is_listening = False
            return "Turning off continuous listening mode!"

        elif "weather" in query or "temperature" in query or "mausam" in query:
            self.root.after(0, lambda: self.canvas.itemconfig(self.canvas_text_id, text="Checking Sky... 🌤️", fill="#33CCFF"))
            
            temp, desc = self.fetch_live_weather("Varanasi")
            
            if temp is not None and desc is not None:
                chosen_animation = 'sunny' 
                
                if "rain" in desc or "drizzle" in desc or "thunderstorm" in desc:
                    chosen_animation = 'rainy'
                elif "snow" in desc or "ice" in desc or temp < 18:
                    chosen_animation = 'winter'
                elif "cloud" in desc or "overcast" in desc or "mist" in desc or "fog" in desc:
                    chosen_animation = 'spring' if 18 <= temp <= 26 else 'sunny'
                else:
                    if temp > 30:
                        chosen_animation = 'sunny'
                    else:
                        chosen_animation = 'spring'
                
                self.root.after(0, lambda: self.set_behavior(chosen_animation))
                self.root.after(7000, lambda: self.set_behavior('idle'))
                
                return f"Currently it's {temp}°C with {desc}. Running your padded weather framework!"
            else:
                return "I couldn't reach the weather servers. Make sure internet is active!"

        elif "time" in query and ("what" in query or "tell" in query or "current" in query):
            now = datetime.now()
            current_time = now.strftime("%I:%M %p")
            self.root.after(0, lambda: self.set_behavior('happy'))
            return f"The current time is {current_time}, buddy!"
            
        elif "date" in query and ("what" in query or "tell" in query or "today" in query):
            now = datetime.now()
            current_date = now.strftime("%A, %B %d, %Y")
            self.root.after(0, lambda: self.set_behavior('happy'))
            return f"Today's date is {current_date}."

        elif "play on youtube" in query or "youtube search" in query or "open youtube and search" in query or "play" in query:
            search_term = query.replace("play on youtube", "").replace("youtube search", "").replace("open youtube and search", "").replace("play", "").strip()
            if search_term:
                encoded = urllib.parse.quote_plus(search_term)
                webbrowser.open(f"https://www.youtube.com/results?search_query={encoded}")
                self.root.after(0, lambda: self.set_behavior('playing'))
                return f"Playing '{search_term}' on YouTube for you!"
            webbrowser.open("https://www.youtube.com")
            return "Opening YouTube Home!"

        elif "search google for" in query or "google search" in query or "search for" in query:
            search_term = query.replace("search google for", "").replace("google search", "").replace("search for", "").strip()
            if search_term:
                encoded = urllib.parse.quote(search_term)
                webbrowser.open(f"https://www.google.com/search?q={encoded}")
                self.root.after(0, lambda: self.set_behavior('jump'))
                return f"Searching Google for {search_term} right away!"
            return "What should I search on Google?"

        elif "open google" in query or "open browser" in query:
            webbrowser.open("https://www.google.com")
            self.root.after(0, lambda: self.set_behavior('jump'))
            return "Opening Google Chrome browser for you!"

        elif "open notepad" in query:
            subprocess.Popen(["notepad.exe"])
            self.root.after(0, lambda: self.set_behavior('typing'))
            return "Launching Notepad!"
            
        elif "open calculator" in query or "open calc" in query:
            subprocess.Popen(["calc.exe"])
            return "Opening Calculator!"
            
        elif "open chrome" in query:
            try:
                chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                if os.path.exists(chrome_path):
                    subprocess.Popen([chrome_path])
                else:
                    webbrowser.open("https://www.google.com")
                return "Launching Google Chrome!"
            except Exception:
                webbrowser.open("https://www.google.com")
                return "Opening Chrome via Webbrowser link!"
            
        elif "open word" in query:
            try:
                os.startfile("winword.exe")
                return "Opening Microsoft Word!"
            except Exception:
                return "Sorry, I couldn't find Microsoft Word on your system."
            
        elif "open excel" in query:
            try:
                os.startfile("excel.exe")
                return "Opening Microsoft Excel!"
            except Exception:
                return "Sorry, I couldn't find Microsoft Excel."

        else:
            if not API_KEY or not self.chat_session:
                return "I need an API Key to think. Please set it in your CMD!"
                
            try:
                self.root.after(0, lambda: self.set_behavior('typing'))
                self.root.after(0, lambda: self.canvas.itemconfig(self.canvas_text_id, text="Thinking... 🧠", fill="#FFCC00"))
                
                response = self.chat_session.send_message(query)
                ai_reply = response.text.strip() if response and hasattr(response, 'text') else "Got a blank response."
                
                self.root.after(0, lambda: self.set_behavior('happy'))
                return ai_reply
                    
            except Exception as e:
                print(f"Query Exception: {e}")
                return "My network loop ran into an issue. Could you repeat that?"

    def play_situation_music(self):
        if self.in_game_mode:
            return
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            self.music_playing = True
            
            cpu_usage = psutil.cpu_percent()
            battery = psutil.sensors_battery()
            
            category = "normal"
            if battery and battery.percent <= 20 and not battery.power_plugged:
                category = "low_battery"
            elif cpu_usage > 80:
                category = "high_cpu"

            search_list = self.search_database.get(category, self.search_database["normal"])
            selected_search = random.choice(search_list)
        
            self.text_color = "#00FF66"
            self.canvas.itemconfig(self.canvas_text_id, text="", fill=self.text_color)
            if self.clear_timer_id:
                self.root.after_cancel(self.clear_timer_id)
            
            self.start_typing_sync(selected_search["ui_text"])
            
            encoded_query = urllib.parse.quote_plus(selected_search["query"])
            search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
            
            if sys.platform == "win32":
                os.system(f'start "" "{search_url}"')
            elif sys.platform == "darwin":
                os.system(f'open "{search_url}"')
            else:
                os.system(f'xdg-open "{search_url}"')
                
            corners = [
                (0, int(self.screen_height - self.canvas_height - 60)), 
                (int(self.screen_width - self.canvas_width), int(self.screen_height - self.canvas_height - 60))
            ]
            self.target_x, self.target_y = random.choice(corners)
            self.is_moving_to_corner = True
            self.music_corner_active = True
            self.state = 'walk'
            self.animation_speed = 0.15
            self.direction = "right" if self.target_x > self.x else "left"
            
        except Exception:
            pass

    def start_drag(self, event):
        if self.in_game_mode:
            return
        self.is_dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.play_ui_sound("click")
        if not self.is_moving_to_corner:
            self.old_state = self.state
            self.set_behavior('position')

    def drag_motion(self, event):
        if self.is_dragging and not self.in_game_mode:
            deltax = event.x - self.drag_start_x
            deltay = event.y - self.drag_start_y
            self.x = self.root.winfo_x() + deltax
            self.y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{int(self.x)}+{int(self.y)}")

    def stop_drag(self, event):
        if self.in_game_mode:
            return
        self.is_dragging = False
        if hasattr(self, 'old_state') and self.old_state not in ['sleep', 'hi', 'sunny', 'winter', 'rainy', 'spring']:
            self.set_behavior(self.old_state)
        else:
            self.set_behavior('idle')

    def safe_lock_monitor(self):
        while self.running:
            if not self.in_game_mode:
                try:
                    is_currently_locked = any(p.name().lower() == "logonui.exe" for p in psutil.process_iter(attrs=['name']))
                    if is_currently_locked and not self.was_locked:
                        self.was_locked = True
                        self.root.after(0, self.on_windows_locked)
                    elif not is_currently_locked and self.was_locked:
                        self.was_locked = False
                        self.root.after(0, self.on_windows_unlocked)
                except Exception:
                    pass
            time.sleep(1)

    def on_windows_locked(self):
        if self.in_game_mode:
            return
        self.set_behavior('hi')
        self.show_message("Hi, enter password buddy 🔐", is_reminder=False)

    def on_windows_unlocked(self):
        if self.in_game_mode:
            return
        self.set_behavior('hi')
        self.show_message("Welcome back buddy! 👋", is_reminder=False)
        self.root.after(4500, lambda: self.set_behavior('idle'))

    def start_loops(self):
        if self.running and self.state == "hi" and not self.in_game_mode:
            self.x = random.randint(100, self.screen_width - self.canvas_width - 100)
            self.y = self.screen_height - self.canvas_height - 80
            self.set_behavior('idle') 
            
        self.schedule_next_quote()
        self.schedule_next_reminder()
        
        self.monitor_thread = threading.Thread(target=self.monitor_system, daemon=True)
        self.monitor_thread.start()

    def monitor_system(self):
        while self.running:
            if not self.in_game_mode:
                try:
                    if self.music_playing or self.is_listening:
                        time.sleep(2)
                        continue

                    cpu_usage = psutil.cpu_percent(interval=1)
                    battery = psutil.sensors_battery()
                    if battery:
                        percent = battery.percent
                        power_plugged = battery.power_plugged
                        if percent <= 20 and not power_plugged:
                            self.root.after(0, lambda: self.set_behavior('sleep'))
                            time.sleep(15)
                            continue
                        elif cpu_usage > 80:
                            self.performance_override = True
                            self.root.after(0, lambda: self.show_message(f"High CPU Load! Code is heavy! 🔥", is_reminder=True))
                            self.root.after(0, lambda: self.set_behavior('run'))
                            time.sleep(10)
                            continue
                    self.performance_override = False
                except Exception:
                    pass
            time.sleep(5)

    async def generate_and_play_speech(self, clean_text, full_text):
        if self.in_game_mode:
            return
        try:
            if self.speech_channel.get_busy():
                self.speech_channel.stop()
            
            self.speech_counter += 1
            temp_audio = os.path.join(os.environ.get('TEMP', ''), f'dyno_speech_{self.speech_counter}.mp3')
            
            communicate = edge_tts.Communicate(clean_text, self.voice_name, rate="+12%")
            await communicate.save(temp_audio)
            
            if os.path.exists(temp_audio):
                sfx = pygame.mixer.Sound(temp_audio)
                self.speech_channel.play(sfx)
                self.root.after(0, lambda: self.start_typing_sync(full_text))
                
                threading.Thread(target=self.cleanup_old_files, args=(self.speech_counter - 1,), daemon=True).start()
        except Exception:
            pass

    def cleanup_old_files(self, old_index):
        if old_index > 0:
            try:
                time.sleep(5) 
                old_file = os.path.join(os.environ.get('TEMP', ''), f'dyno_speech_{old_index}.mp3')
                if os.path.exists(old_file):
                    os.remove(old_file)
            except Exception:
                pass

    def run_speech_async(self, text):
        if self.in_game_mode:
            return
        clean_text = text.replace("👋", "").replace("🔐", "").replace("🔥", "").replace("🚨", "").replace("⚡", "").replace("🚀", "").replace("🎯", "").replace("🔑", "").replace("⭐", "").replace("🌟", "").replace("🐾", "").replace("✨", "").replace("💧", "").replace("🚶‍♂️", "").replace("👀", "").replace("🧘‍♂️", "").replace("😴", "").replace("😊", "").replace("🦖", "").replace("🏸", "").replace("🤔", "").replace("🎙️", "").replace("🤗", "").replace("👍", "")
        asyncio.run_coroutine_threadsafe(self.generate_and_play_speech(clean_text, text), self.async_loop)

    def show_message(self, text, is_reminder=False):
        if self.music_playing or self.in_game_mode:
            return
            
        self.text_color = "#FF3366" if is_reminder else "#00FF66" 
        self.canvas.itemconfig(self.canvas_text_id, text="", fill=self.text_color)
        if self.clear_timer_id:
            self.root.after_cancel(self.clear_timer_id)

        self.play_ui_sound("pop")
        self.run_speech_async(text)

    def start_typing_sync(self, text):
        if self.in_game_mode:
            return
        self.typing_text = text
        self.typing_index = 0
        self.type_letter()

    def type_letter(self):
        if self.in_game_mode:
            return
        if self.typing_index < len(self.typing_text):
            current_text = self.canvas.itemcget(self.canvas_text_id, "text")
            self.canvas.itemconfig(self.canvas_text_id, text=current_text + self.typing_text[self.typing_index])
            
            if self.typing_index % 2 == 0:
                self.play_ui_sound("type")
                
            self.typing_index += 1
            self.root.after(55, self.type_letter)
        else:
            if not self.music_playing and not self.is_listening:
                self.clear_timer_id = self.root.after(5000, self.clear_message)

    def clear_message(self):
        self.canvas.itemconfig(self.canvas_text_id, text="")

    def schedule_next_quote(self):
        if self.running:
            self.root.after(120000, self.trigger_quote) 

    def trigger_quote(self):
        if self.ui_channel.get_busy() or self.speech_channel.get_busy() or self.is_listening or self.in_game_mode:
            self.schedule_next_quote()
            return

        if not self.performance_override and not self.music_playing and self.state != 'sleep':
            self.show_message(random.choice(self.quotes), is_reminder=False)
        self.schedule_next_quote() 

    def schedule_next_reminder(self):
        if self.running:
            self.root.after(2700000, self.trigger_reminder) 

    def trigger_reminder(self):
        if self.ui_channel.get_busy() or self.speech_channel.get_busy() or self.is_listening or self.in_game_mode:
            self.schedule_next_reminder()
            return

        if not self.performance_override and not self.music_playing:
            if self.state == 'sleep':
                self.set_behavior('idle') 
            self.show_message(random.choice(self.reminders), is_reminder=True)
        self.schedule_next_reminder() 

    def get_current_frame(self):
        frames_list = self.animations_right.get(self.state, []) if self.direction == "right" else self.animations_left.get(self.state, [])
        if frames_list:
            safe_idx = int(self.frame_index) % len(frames_list)
            return frames_list[safe_idx]
        return None

    def flip_direction(self):
        if self.in_game_mode:
            return
        self.direction = "left" if self.direction == "right" else "right"
        self.set_behavior(self.state)

    def set_behavior(self, command_state):
        if self.in_game_mode:
            return

        if command_state not in ['idle', 'sleep', 'run'] and self.music_playing:
            self.music_playing = False
            self.music_corner_active = False
            self.clear_message()
            
        if self.is_moving_to_corner and command_state != 'sleep' and not self.music_playing:
            self.is_moving_to_corner = False
            self.show_message("Awake now! 👀")

        if command_state == 'sleep' and not self.is_moving_to_corner:
            if self.state == 'sleep': 
                return
            corners = [
                (0, int(self.screen_height - self.canvas_height - 60)), 
                (int(self.screen_width - self.canvas_width), int(self.screen_height - self.canvas_height - 60))
            ]
            self.target_x, self.target_y = random.choice(corners)
            self.is_moving_to_corner = True
            self.music_corner_active = False
            self.state = 'walk' 
            self.animation_speed = 0.15
            self.direction = "right" if self.target_x > self.x else "left"
            
            self.show_message("I am feeling sleepy... 😴", is_reminder=False)
            return

        if self.music_playing and command_state in ['walk', 'run', 'jump', 'sleep']:
            return

        if not self.is_moving_to_corner:
            self.state = command_state
        
        self.frame_index = 0.0
        direction_multiplier = 1 if self.direction == "right" else -1
        
        if self.state in ['eating', 'reading', 'happy', 'typing', 'playing', 'sunny', 'winter', 'rainy', 'spring']:
            self.speed_x, self.speed_y = 0, 0
            self.animation_speed = 0.12  
        elif self.state == 'hi':
            self.speed_x, self.speed_y = 0, 0
            self.animation_speed = 0.12
        elif self.state == 'idle':
            self.speed_x, self.speed_y = 0, 0
            self.animation_speed = 0.10
        elif self.state == 'walk':
            self.speed_x = 2 * direction_multiplier
            self.speed_y = random.choice([-2, -1, 1, 2])
            self.animation_speed = 0.15
        elif self.state == 'run':
            self.speed_x = 6 * direction_multiplier
            self.speed_y = random.choice([-4, -3, 3, 4])
            self.animation_speed = 0.25
        elif self.state == 'jump':
            self.speed_x = 4 * direction_multiplier
            self.speed_y = random.choice([-5, -3, 3, 5])
            self.animation_speed = 0.15 
        elif self.state == 'sleep':
            self.speed_x, self.speed_y = 0, 0
            self.animation_speed = 0.07
        elif self.state == 'position':
            self.speed_x, self.speed_y = 0, 0
            self.animation_speed = 0.12

    def update_all(self):
        if not self.in_game_mode:
            if self.state == "hi":
                current_frames = self.animations_right.get('hi', []) if self.direction == "right" else self.animations_left.get('hi', [])
                if current_frames and int(self.frame_index + self.animation_speed) >= len(current_frames):
                    self.state = 'idle'
                    self.speed_x, self.speed_y = 0, 0
                    self.animation_speed = 0.10
                    self.frame_index = 0.0

            if self.is_dragging:
                pass
            elif self.is_moving_to_corner and self.target_x is not None:
                dist_x = self.target_x - self.x
                dist_y = self.target_y - self.y
                
                if abs(dist_x) <= 4: self.x = self.target_x
                else: self.x += 4 if dist_x > 0 else -4
                    
                if abs(dist_y) <= 4: self.y = self.target_y
                else: self.y += 4 if dist_y > 0 else -4

                if self.x == self.target_x and self.y == self.target_y:
                    self.is_moving_to_corner = False
                    if self.music_corner_active:
                        self.state = 'idle'
                        self.music_corner_active = False
                    else:
                        self.state = 'sleep'
                    self.speed_x = 0
                    self.speed_y = 0
                    self.animation_speed = 0.10 if self.state == 'idle' else 0.07
                    self.frame_index = 0.0
            else:
                self.x += self.speed_x
                self.y += self.speed_y

            current_img = self.get_current_frame()
            
            if current_img:
                current_frames = self.animations_right.get(self.state, []) if self.direction == "right" else self.animations_left.get(self.state, [])
                self.frame_index += self.animation_speed
                if current_frames and self.frame_index >= len(current_frames):
                    self.frame_index = 0.0

                self.canvas.itemconfig(self.canvas_image_id, image=current_img)

                if not self.is_dragging and not self.is_moving_to_corner and self.state in ['walk', 'run', 'jump']:
                    if self.x <= 0:
                        self.x = 0
                        self.direction = "right"
                        self.set_behavior(self.state)
                    elif self.x >= self.screen_width - self.canvas_width:
                        self.x = self.screen_width - self.canvas_width
                        self.direction = "left"
                        self.set_behavior(self.state)

                    if self.y <= 0:
                        self.y = 0
                        self.speed_y = -self.speed_y
                    elif self.y >= self.screen_height - self.canvas_height:
                        self.y = self.screen_height - self.canvas_height
                        self.speed_y = -self.speed_y

                self.root.geometry(f"{self.canvas_width}x{self.canvas_height}+{int(self.x)}+{int(self.y)}")
        
        self.root.after(30, self.update_all)

    def close_app(self):
        self.running = False
        keyboard.unhook_all() 
        try:
            self.async_loop.call_soon_threadsafe(self.async_loop.stop)
            self.ui_channel.stop()
            self.speech_channel.stop()
            pygame.mixer.quit()
        except Exception:
            pass
        self.root.destroy()

if __name__ == "__main__":
    DesktopDyno()