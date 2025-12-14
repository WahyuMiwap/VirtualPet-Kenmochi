# ==============================================================================
# PROYEK UAS PEMROGRAMAN BERORIENTASI OBJEK (PBO)
# JUDUL   : Kenmochi Touya - Virtual Pet Tamagotchi
# NAMA    : Muhammad Wahyu Firmansyah
# NIM     : 24091397035
# KELAS   : 2024B
# ==============================================================================

import pygame
import sys
import math
import random
import datetime
import json
import os

# ==========================================
# 1. KONFIGURASI (SETTINGS)
# ==========================================
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 700

# Palet Warna
COVER_BG_COLOR = (158, 142, 172)
BG_COLOR = (70, 180, 190)
BTN_HOVER_COLOR = (255, 255, 255) 

# Warna Tombol UI
BTN_EAT_COLOR = (255, 100, 100)
BTN_BATH_COLOR = (100, 200, 255)
BTN_SLEEP_COLOR = (150, 100, 200)
BTN_SING_COLOR = (255, 215, 0)
BTN_RESET_COLOR = (255, 50, 50)
BTN_MENU_COLOR = (100, 100, 200)
BTN_MAIN_MENU_COLOR = (50, 150, 150)
BTN_EXIT_MENU_COLOR = (200, 50, 50)

# Warna Bar Status
BAR_BG_COLOR = (50, 50, 50)
COL_HUNGER = (255, 100, 100)
COL_HYGIENE = (100, 255, 255)
COL_ENERGY = (255, 255, 100)
COL_FUN = (255, 100, 255)
TEXT_COLOR = (255, 255, 255)

# Posisi Y Karakter (Agar berdiri pas di meja)
DESK_HEIGHT_Y = 550 

# ==========================================
# 2. FUNGSI BANTUAN (HELPER)
# ==========================================
def make_round_image(image, size):
    """
    Memotong gambar menjadi bentuk lingkaran (Circle Crop).
    Digunakan untuk foto profil di menu cover.
    """
    orig_w, orig_h = image.get_size()
    min_dim = min(orig_w, orig_h)
    offset_x = (orig_w - min_dim) // 2
    offset_y = (orig_h - min_dim) // 2
    image = image.subsurface((offset_x, offset_y, min_dim, min_dim))
    image = pygame.transform.scale(image, size)
    mask = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (size[0]//2, size[1]//2), min(size)//2)
    final_surf = pygame.Surface(size, pygame.SRCALPHA)
    final_surf.blit(image, (0, 0))
    final_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return final_surf

# ==========================================
# 3. CLASS TOMBOL
# ==========================================
class Button:
    """
    Kelas untuk menangani pembuatan dan interaksi tombol UI.
    Mendukung efek hover (membesar saat kursor di atasnya).
    """
    def __init__(self, x, y, w, h, text, color, action_code):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.action_code = action_code
        self.is_hovered = False
    
    def draw(self, surface, font):
        draw_color = self.color
        draw_rect = self.rect.copy()
        
        # Logika Animasi Hover
        if self.is_hovered:
            r = min(255, self.color[0] + 50)
            g = min(255, self.color[1] + 50)
            b = min(255, self.color[2] + 50)
            draw_color = (r, g, b)
            draw_rect = draw_rect.inflate(4, 4)

        # Menggambar Shadow Tombol
        shadow_rect = draw_rect.copy()
        shadow_rect.y += 3
        pygame.draw.rect(surface, (30, 30, 30), shadow_rect, border_radius=12)

        # Menggambar Tombol Utama
        pygame.draw.rect(surface, draw_color, draw_rect, border_radius=12)
        pygame.draw.rect(surface, (255, 255, 255), draw_rect, 3, border_radius=12)
        
        # Render Teks
        text_surf = font.render(self.text, True, (50, 50, 50) if self.is_hovered else (255,255,255))
        text_rect = text_surf.get_rect(center=draw_rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# ==========================================
# 4. CLASS KENMOCHI (KARAKTER UTAMA)
# ==========================================
class Kenmochi(pygame.sprite.Sprite):
    """
    Kelas utama yang mengatur logika, status, dan animasi karakter.
    """
    def __init__(self):
        super().__init__()
        self.name = "Kenmochi"
        self.rect = pygame.Rect(0,0,0,0)
        self.stats = {"hunger": 90.0, "hygiene": 90.0, "energy": 90.0, "fun": 90.0}
        self.is_alive = True
        self.accumulated_time = 0
        
        # Status Aktivitas
        self.is_eating = False; self.eat_timer = 0
        self.is_bathing = False; self.bath_timer = 0
        self.is_sleeping = False 
        self.is_singing = False; self.sing_timer = 0; self.sing_notes = []
        
        # AI Idle (Logika Perilaku Otomatis)
        self.blink_timer = 0; self.next_blink_time = 100
        self.idle_timer = 0; self.is_bored = False; self.bored_duration = 0
        self.yawn_timer = 0; self.yawn_interval_timer = 0; self.yawn_duration_timer = 0; self.is_yawning = False
        
        # Interaksi User
        self.is_interacting = False; self.interact_timer = 0
        self.last_click_time = 0
        self.chat_text = ""
        self.interact_mode = ""

        # Fisika Drag & Drop
        self.is_dragging = False; self.is_falling = False; self.is_walking_back = False
        self.pos_x = SCREEN_WIDTH // 2 - 100
        self.pos_y = DESK_HEIGHT_Y - 90 
        self.velocity_y = 0
        self.target_x = SCREEN_WIDTH // 2 - 100
        self.frame_count = 0

        # Sistem Cutscene (Adegan Pindah Ruangan)
        self.in_cutscene = False
        self.cutscene_state = "NONE" 
        self.bg_location = "ROOM2" 
        self.fade_trigger = False
        self.fade_next_mode = ""

        # Aset Gambar
        self.sing_frames = []; self.food_images = []; self.bath_frames = []
        self.image_idle = None; self.has_image = False
        
        self.load_assets()
        self.load_data()

    def load_assets(self):
        """Memuat gambar dan aset animasi"""
        try:
            def load_img(filename, w, h):
                path = f"assets/{filename}"
                if not os.path.exists(path):
                    # Placeholder jika gambar hilang
                    s = pygame.Surface((w, h)); s.fill((255, 0, 255)); return s
                img = pygame.image.load(path).convert()
                img.set_colorkey(img.get_at((0, 0)))
                return pygame.transform.scale(img, (w, h))

            # Load Aset Utama
            self.image_idle = load_img("idle.png", 200, 180)
            self.image_blink = load_img("Blink.png", 200, 180)
            self.image_eat_open = load_img("makan_bukamulut.png", 200, 180)
            self.image_sleep = load_img("sleep.png", 200, 180)
            self.image_sing = load_img("sing1.png", 200, 180)
            self.image_badmood = load_img("badmood.png", 200, 180)
            self.image_bad = load_img("bad.png", 200, 180)
            self.image_dead = load_img("dead.png", 200, 180)
            self.image_yawn = load_img("yawn.png", 200, 180)
            
            # Sequence Animasi Mandi (Looping: 4->1->2->3->2->1->4)
            b1 = load_img("bath1.png", 200, 180)
            b2 = load_img("bath2.png", 200, 180)
            b3 = load_img("bath3.png", 200, 180)
            b4 = load_img("bath4.png", 200, 180)
            self.bath_frames = [b4, b1, b2, b3, b2, b1, b4]

            # Sequence Animasi Nyanyi & Makan
            self.sing_frames = [self.image_eat_open, self.image_blink, self.image_sing, self.image_idle]
            self.food_images = [load_img("eat1.png", 70, 70), load_img("eat2.png", 70, 70), load_img("eat3.png", 70, 70)]
            self.has_image = True; self.rect = self.image_idle.get_rect()
        except: self.has_image = False; self.rect = pygame.Rect(0,0,200,180)

    def save_data(self, current_session_seconds=0):
        total_time = self.accumulated_time + current_session_seconds
        data = { "stats": self.stats, "is_alive": self.is_alive, "play_time": total_time, "bg_location": "ROOM2" }
        try:
            with open("savegame.json", "w") as f: json.dump(data, f)
        except: pass

    def load_data(self):
        if not os.path.exists("savegame.json"): return 
        try:
            with open("savegame.json", "r") as f:
                data = json.load(f)
                self.stats = data["stats"]
                self.is_alive = data["is_alive"]
                self.accumulated_time = data.get("play_time", 0)
        except: pass

    def reset_idle(self):
        self.idle_timer = 0
        self.is_bored = False
        self.bored_duration = 0

    def reset_activity(self):
        self.is_eating = False; self.is_bathing = False; self.is_singing = False
        self.sing_notes = []; self.eat_timer = 0; self.bath_timer = 0; self.sing_timer = 0
        self.reset_idle()

    # --- INPUT HANDLER ---
    def handle_click(self, pos):
        if not self.rect.collidepoint(pos) or not self.is_alive or self.in_cutscene or self.is_sleeping: return
        current_time = pygame.time.get_ticks()
        if current_time - self.last_click_time < 400: self.start_drag(pos) # Double Click
        else: self.interact_touch() # Single Click
        self.last_click_time = current_time

    def start_drag(self, pos):
        self.reset_activity()
        self.is_dragging = True; self.is_falling = False; self.is_walking_back = False
        self.pos_x = pos[0] - 100; self.pos_y = pos[1] - 90

    def update_drag(self, pos):
        if self.is_dragging: self.pos_x = pos[0] - 100; self.pos_y = pos[1] - 90

    def stop_drag(self):
        if self.is_dragging: self.is_dragging = False; self.is_falling = True; self.velocity_y = 0

    def interact_touch(self):
        self.reset_activity()
        self.is_interacting = True; self.interact_timer = 60
        self.stats["fun"] = min(100, self.stats["fun"] + 5)
        if random.random() > 0.5:
            self.interact_mode = "TALK"; self.chat_text = random.choice(["Halo!", "Apa?", "Hehe!", "Lapar...", "Zzz?"])
        else: self.interact_mode = "BLINK"

    # --- CUTSCENE MANAGER (TIDUR & MANDI) ---
    def start_sleeping_sequence(self):
        if self.is_sleeping or self.in_cutscene: return
        self.reset_activity()
        self.in_cutscene = True
        self.cutscene_state = "TO_BED_OUT" 

    def start_wake_up_sequence(self):
        if not self.is_sleeping or self.in_cutscene: return
        self.in_cutscene = True
        self.cutscene_state = "WAKE_OUT"
    
    def start_bathing_sequence(self):
        if self.is_bathing or self.in_cutscene: return
        self.reset_activity()
        self.in_cutscene = True
        self.cutscene_state = "TO_BATH_OUT"

    def update_cutscene(self, center_y):
        ground_y = center_y - 90
        speed = 5
        
        # --- LOGIKA TIDUR (KE KIRI) ---
        if self.cutscene_state == "TO_BED_OUT":
            self.pos_x -= speed
            self.pos_y = ground_y + math.sin(pygame.time.get_ticks() * 0.02) * 15 
            if self.pos_x < -200: 
                self.fade_trigger = True; self.fade_next_mode = "TO_BED"
                self.cutscene_state = "WAIT_FADE"
        
        elif self.cutscene_state == "TO_BED_IN":
            self.bg_location = "ROOM3"
            self.pos_x = SCREEN_WIDTH + 100 
            self.cutscene_state = "WALK_IN_BED"

        elif self.cutscene_state == "WALK_IN_BED":
            self.pos_x -= speed
            self.pos_y = ground_y + math.sin(pygame.time.get_ticks() * 0.02) * 15
            if self.pos_x <= self.target_x: 
                self.pos_x = self.target_x; self.pos_y = ground_y
                self.in_cutscene = False; self.is_sleeping = True 
                self.cutscene_state = "NONE"

        elif self.cutscene_state == "WAKE_OUT":
            self.is_sleeping = False
            self.pos_x += speed
            self.pos_y = ground_y + math.sin(pygame.time.get_ticks() * 0.02) * 15
            if self.pos_x > SCREEN_WIDTH + 100:
                self.fade_trigger = True; self.fade_next_mode = "WAKE_UP"
                self.cutscene_state = "WAIT_FADE"

        elif self.cutscene_state == "WAKE_IN":
            self.bg_location = "ROOM2"
            self.pos_x = -200 
            self.cutscene_state = "WALK_IN_WAKE"

        elif self.cutscene_state == "WALK_IN_WAKE":
            self.pos_x += speed
            self.pos_y = ground_y + math.sin(pygame.time.get_ticks() * 0.02) * 15
            if self.pos_x >= self.target_x:
                self.pos_x = self.target_x; self.pos_y = ground_y
                self.in_cutscene = False; self.cutscene_state = "NONE"; self.reset_idle()

        # --- LOGIKA MANDI (KE KANAN) ---
        elif self.cutscene_state == "TO_BATH_OUT":
            self.pos_x += speed
            self.pos_y = ground_y + math.sin(pygame.time.get_ticks() * 0.02) * 15
            if self.pos_x > SCREEN_WIDTH + 100:
                self.fade_trigger = True; self.fade_next_mode = "TO_BATH"
                self.cutscene_state = "WAIT_FADE"

        elif self.cutscene_state == "TO_BATH_IN":
            self.bg_location = "ROOM4"
            self.pos_x = -200
            self.cutscene_state = "WALK_IN_BATH"

        elif self.cutscene_state == "WALK_IN_BATH":
            self.pos_x += speed
            self.pos_y = ground_y + math.sin(pygame.time.get_ticks() * 0.02) * 15
            if self.pos_x >= self.target_x:
                self.pos_x = self.target_x; self.pos_y = ground_y
                self.is_bathing = True
                self.bath_timer = 0
                self.cutscene_state = "BATHING"
        
        elif self.cutscene_state == "BATHING":
            self.bath_timer += 1
            if self.bath_timer > 240: # Mandi 4 detik
                self.is_bathing = False
                self.stats["hygiene"] = 100
                self.cutscene_state = "FINISH_BATH_OUT"

        elif self.cutscene_state == "FINISH_BATH_OUT":
            self.pos_x -= speed
            self.pos_y = ground_y + math.sin(pygame.time.get_ticks() * 0.02) * 15
            if self.pos_x < -200:
                self.fade_trigger = True; self.fade_next_mode = "FINISH_BATH"
                self.cutscene_state = "WAIT_FADE"

        elif self.cutscene_state == "FINISH_BATH_IN":
            self.bg_location = "ROOM2"
            self.pos_x = SCREEN_WIDTH + 100
            self.cutscene_state = "WALK_BACK_FROM_BATH"
        
        elif self.cutscene_state == "WALK_BACK_FROM_BATH":
            self.pos_x -= speed
            self.pos_y = ground_y + math.sin(pygame.time.get_ticks() * 0.02) * 15
            if self.pos_x <= self.target_x:
                self.pos_x = self.target_x; self.pos_y = ground_y
                self.in_cutscene = False
                self.cutscene_state = "NONE"
                self.reset_idle()

    def update_physics(self, center_y):
        if self.in_cutscene:
            self.update_cutscene(center_y)
            return

        ground_y = center_y - 90
        
        if self.is_falling:
            self.velocity_y += 1.5
            self.pos_y += self.velocity_y
            if self.pos_y >= ground_y:
                self.pos_y = ground_y; self.is_falling = False; self.velocity_y = 0
                if abs(self.pos_x - self.target_x) > 5: self.is_walking_back = True
        elif self.is_walking_back:
            speed = 3
            if self.pos_x < self.target_x: self.pos_x += speed
            else: self.pos_x -= speed
            self.pos_y = ground_y + math.sin(pygame.time.get_ticks() * 0.02) * 10
            if abs(self.pos_x - self.target_x) < 5:
                self.pos_x = self.target_x; self.pos_y = ground_y; self.is_walking_back = False
        elif not self.is_dragging and not self.is_sleeping and not self.is_bathing:
            self.frame_count += 0.08; self.pos_y = (ground_y) + math.sin(self.frame_count) * 8

    def update_stats(self):
        if not self.is_alive: return
        decay = 0.0185
        if not self.is_eating: self.stats["hunger"] -= 0.02
        if not self.is_sleeping: self.stats["energy"] -= decay
        if not self.is_singing: self.stats["fun"] -= 0.015
        if not self.is_bathing: self.stats["hygiene"] -= 0.01
        
        if self.is_sleeping: 
            self.stats["energy"] += 0.4; self.stats["hunger"] -= 0.005
            if self.stats["energy"] >= 100:
                self.stats["energy"] = 100
                self.start_wake_up_sequence()

        for k in self.stats:
            self.stats[k] = max(0, min(100, self.stats[k]))
            if self.stats[k] <= 0: self.is_alive = False

    def start_action(self, action):
        if not self.is_alive or self.is_dragging or self.is_falling or self.is_walking_back or self.in_cutscene: return
        if action == "EAT":
            self.reset_activity(); self.is_eating = True
            self.stats["hunger"] = min(100, self.stats["hunger"]+30)
        elif action == "BATH":
            self.start_bathing_sequence()
        elif action == "SING":
            self.reset_activity(); self.is_singing = True
            self.stats["fun"] = min(100, self.stats["fun"]+40)
        elif action == "SLEEP":
            self.start_sleeping_sequence()

    def draw(self, surface, center_x, center_y):
        self.update_stats()
        self.update_physics(center_y)
        self.rect.topleft = (self.pos_x, self.pos_y)
        
        curr_img = self.image_idle
        is_bad_mood = any(val < 50 for val in self.stats.values())
        if is_bad_mood: curr_img = self.image_badmood

        # --- LOGIKA PRIORITAS ---
        if not self.is_alive: curr_img = self.image_dead
        
        elif self.in_cutscene:
            if self.cutscene_state == "BATHING":
                # Animasi Mandi (Ping Pong)
                frame_idx = (self.bath_timer // 10) % len(self.bath_frames)
                curr_img = self.bath_frames[frame_idx]
            else:
                curr_img = self.image_idle
                if (pygame.time.get_ticks() // 150) % 2 == 0: curr_img = self.image_blink 
        
        elif self.is_dragging: curr_img = self.image_eat_open
        elif self.is_falling: curr_img = self.image_blink
        elif self.is_walking_back: 
            if is_bad_mood: curr_img = self.image_badmood
            else: curr_img = self.image_idle
        elif self.is_interacting:
            self.interact_timer -= 1
            if self.interact_mode == "TALK": curr_img = self.image_eat_open if (self.interact_timer // 10) % 2 == 0 else self.image_idle
            else: curr_img = self.image_blink
            if self.interact_timer <= 0: self.is_interacting = False
        
        elif self.is_eating:
            self.eat_timer += 1
            if self.eat_timer < 30: curr_img = self.image_eat_open
            elif self.eat_timer < 60: curr_img = self.image_blink
            elif self.eat_timer < 90: curr_img = self.image_eat_open
            else: curr_img = self.image_idle; self.is_eating = False
        elif self.is_singing:
            self.sing_timer += 1
            curr_img = self.sing_frames[(self.sing_timer//30)%len(self.sing_frames)]
            if self.sing_timer % 30 == 0: self.sing_notes.append([center_x+random.randint(40,80), self.pos_y+50, 255, random.choice(["♪","♫"])])
            if self.sing_timer > 720: self.is_singing = False; self.sing_notes = []
        elif self.is_sleeping: curr_img = self.image_sleep
        elif self.is_yawning:
            self.yawn_duration_timer += 1; curr_img = self.image_yawn
            if self.yawn_duration_timer > 60: self.is_yawning = False
        elif self.stats["energy"] < 50 and not self.is_eating: 
             self.yawn_timer += 1
             if self.yawn_timer > 420: self.is_yawning = True; self.yawn_timer = 0; self.yawn_duration_timer = 0
             elif is_bad_mood: curr_img = self.image_badmood
             else: curr_img = self.image_idle
        elif is_bad_mood: 
            curr_img = self.image_badmood
        elif not self.is_bored: 
            self.blink_timer += 1
            if self.blink_timer > self.next_blink_time: curr_img = self.image_blink
            else: curr_img = self.image_idle
            if self.blink_timer > self.next_blink_time + 10: 
                self.blink_timer = 0; self.next_blink_time = random.randint(100, 400)
            self.idle_timer += 1
            if self.idle_timer > 180: self.is_bored = True; self.bored_duration = 0
        else:
            curr_img = self.image_bad 
            self.bored_duration += 1
            if self.bored_duration > 180:
                self.is_bored = False; self.idle_timer = 0

        # --- RENDER ---
        if self.has_image:
            # Bayangan Dinamis
            shadow_w = 100
            if self.is_dragging or self.is_falling: shadow_w = 50
            elif self.is_walking_back or self.in_cutscene: shadow_w = 80
            elif self.is_sleeping or self.is_bathing: shadow_w = 100
            else: shadow_w = 100 - (math.sin(self.frame_count) * 16)

            pygame.draw.ellipse(surface, (50, 50, 50), (self.pos_x + 100 - shadow_w//2, center_y + 80, shadow_w, 15))
            surface.blit(curr_img, (self.pos_x, self.pos_y))
            
            if self.is_interacting and self.interact_mode == "TALK":
                font_chat = pygame.font.SysFont("Comic Sans MS", 16, bold=True)
                chat_surf = font_chat.render(self.chat_text, True, (0,0,0))
                bub_rect = chat_surf.get_rect(center=(self.pos_x + 180, self.pos_y + 20))
                pygame.draw.rect(surface, (255,255,255), bub_rect.inflate(10,5), border_radius=10)
                surface.blit(chat_surf, bub_rect)

            if self.is_eating:
                if self.eat_timer < 30: food_img_to_draw = self.food_images[0]
                elif self.eat_timer < 60: food_img_to_draw = self.food_images[1]
                else: food_img_to_draw = self.food_images[2]
                surface.blit(food_img_to_draw, (self.pos_x + 50, self.pos_y + 135))
            
            font_note = pygame.font.SysFont("Segoe UI Symbol", 30)
            for n in self.sing_notes:
                n[1] -= 1.5; n[0] += math.sin(n[1]*0.1)*2; n[2] -= 2
                if n[2] > 0: 
                    t = font_note.render(n[3], True, (50,50,50)); t.set_alpha(n[2]); surface.blit(t, (n[0], n[1]))
            self.sing_notes = [n for n in self.sing_notes if n[2] > 0]

# ==========================================
# 5. CLASS EGG (TELUR)
# ==========================================
class Egg(pygame.sprite.Sprite):
    """Kelas untuk menangani fase awal (telur)"""
    def __init__(self):
        super().__init__()
        self.frame = 0; self.click_count = 0; self.is_hatched = False; self.images = []
        self.hatch_timer = 0
        try:
            def load_and_resize(filename):
                img = pygame.image.load(f"assets/{filename}").convert()
                img.set_colorkey(img.get_at((0, 0)))
                ratio = 200 / img.get_width()
                return pygame.transform.scale(img, (200, int(img.get_height() * ratio)))
            self.images = [load_and_resize(f"egg{i}.png") for i in range(1, 4)]
            self.has_image = True; self.final_w = self.images[0].get_width()
        except: self.has_image = False

    def click(self):
        if self.is_hatched: return
        self.click_count += 1
        if self.click_count >= 3 and self.click_count < 6: self.frame = 1
        elif self.click_count >= 6: 
            self.frame = 2
            self.is_hatched = True 

    def draw(self, surface, desk_y):
        cx = SCREEN_WIDTH // 2
        if self.has_image:
            current_img = self.images[self.frame]
            offset_x = random.randint(-2, 2) if self.click_count > 0 and not self.is_hatched else 0
            
            img_h = current_img.get_height()
            pos_x = cx - self.final_w // 2 + offset_x
            pos_y = desk_y - img_h + 25 

            surface.blit(current_img, (pos_x, pos_y))
            
            if not self.is_hatched and pygame.time.get_ticks() % 1000 < 500:
                font = pygame.font.SysFont("Arial", 20, bold=True)
                surface.blit(font.render("KLIK TELUR!", True, (255,255,255)), (cx - 60, pos_y + img_h + 10))

# ==========================================
# 6. CLASS GAME (ENGINE UTAMA)
# ==========================================
class Game:
    """Kelas utama yang mengatur loop permainan, transisi, dan rendering"""
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Kenmochi Touya - Virtual Pet")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 14, bold=True)
        self.start_ticks = pygame.time.get_ticks() 
        self.music_started = False
        self.state = "COVER"
        
        # Load Backgrounds
        self.bg_room2 = None # Meja
        self.bg_room3 = None # Kamar
        self.bg_room4 = None # Kamar Mandi
        self.bg_x = 0; self.bg_y = 0
        try:
            # Room 2 (Meja)
            raw2 = pygame.image.load("assets/room2.png").convert()
            sw, sh = raw2.get_size()
            scale_factor = (SCREEN_HEIGHT * 1.5) / sh
            new_w, new_h = int(sw * scale_factor), int(sh * scale_factor)
            self.bg_room2 = pygame.transform.scale(raw2, (new_w, new_h))
            
            # Room 3 (Kamar)
            raw3 = pygame.image.load("assets/room3.png").convert()
            self.bg_room3 = pygame.transform.scale(raw3, (new_w, new_h))
            
            # Room 4 (Kamar Mandi)
            raw4 = pygame.image.load("assets/room4.png").convert()
            self.bg_room4 = pygame.transform.scale(raw4, (new_w, new_h))
            
            self.bg_x = -(new_w - SCREEN_WIDTH) // 2
            self.bg_y = -(new_h - SCREEN_HEIGHT)
        except: pass

        try:
            pygame.mixer.music.load("assets/Cover.mp3") 
            pygame.mixer.music.set_volume(0.6)
            pygame.mixer.music.play(-1) 
        except: pass

        self.egg = Egg()
        self.pet = Kenmochi()

        self.btns_cover = [
            Button(200, 450, 200, 50, "NEW GAME", BTN_MENU_COLOR, "NEW"),
            Button(200, 520, 200, 50, "LOAD GAME", BTN_MENU_COLOR, "LOAD"),
            Button(200, 590, 200, 50, "EXIT", BTN_RESET_COLOR, "EXIT")
        ]
        
        self.is_menu_open = False
        self.btn_menu = Button(50, 180, 120, 40, "MENU ▼", BTN_MAIN_MENU_COLOR, "MENU_TOGGLE")
        
        self.btns_actions = [
            Button(50, 230, 120, 40, "MAKAN", BTN_EAT_COLOR, "EAT"),
            Button(50, 280, 120, 40, "MANDI", BTN_BATH_COLOR, "BATH"),
            Button(50, 330, 120, 40, "NYANYI", BTN_SING_COLOR, "SING"),
            Button(50, 380, 120, 40, "TIDUR", BTN_SLEEP_COLOR, "SLEEP"),
            Button(50, 430, 120, 40, "KELUAR", BTN_EXIT_MENU_COLOR, "EXIT_GAME")
        ]
        
        self.btn_reset = Button(200, 350, 200, 60, "ULANGI (RESET)", BTN_RESET_COLOR, "RESET")
        self.dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.dark_overlay.set_alpha(150); self.dark_overlay.fill((0, 0, 0))

    def start_bgm_game(self):
        if not self.music_started:
            try:
                pygame.mixer.music.fadeout(500)
                pygame.mixer.music.load("assets/Backsound.mp3")
                pygame.mixer.music.set_volume(0.3)
                pygame.mixer.music.play(-1)
                self.music_started = True
            except: pass

    def draw_hud(self):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        secs = (pygame.time.get_ticks() - self.start_ticks) // 1000
        total_seconds = self.pet.accumulated_time + secs
        h, r = divmod(total_seconds, 3600); m, s = divmod(r, 60)
        timer = f"{h:02}:{m:02}:{s:02}"
        
        c_surf = self.font.render(f"CLOCK: {now}", True, (255,255,255))
        t_surf = self.font.render(f"TIME: {timer}", True, (255,255,255))
        
        self.screen.blit(c_surf, (SCREEN_WIDTH - c_surf.get_width() - 20, 20))
        self.screen.blit(t_surf, (SCREEN_WIDTH - t_surf.get_width() - 20, 40))

        bw=120; bh=15; sx=50; sy=50
        bars = [("KENYANG", self.pet.stats["hunger"], COL_HUNGER),
                ("BERSIH", self.pet.stats["hygiene"], COL_HYGIENE),
                ("SENANG", self.pet.stats["fun"], COL_FUN),
                ("ENERGI", self.pet.stats["energy"], COL_ENERGY)]
        
        for i, (lbl, val, col) in enumerate(bars):
            y = sy + i*30
            self.screen.blit(self.font.render(lbl, True, (255,255,255)), (sx, y))
            pygame.draw.rect(self.screen, BAR_BG_COLOR, (sx+80, y, bw, bh), border_radius=5)
            pygame.draw.rect(self.screen, col, (sx+80, y, int(val/100*bw), bh), border_radius=5)
            pygame.draw.rect(self.screen, (255,255,255), (sx+80, y, bw, bh), 1, border_radius=5)

    def fade_effect(self, target_state, action_callback=None):
        fade_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        fade_surf.fill((0, 0, 0))
        # Fade Out
        for alpha in range(0, 256, 15):
            fade_surf.set_alpha(alpha)
            if self.state == "COVER": self.draw_cover_screen()
            elif self.state == "GAME": self.draw_game_frame()
            self.screen.blit(fade_surf, (0,0))
            pygame.display.flip(); pygame.time.delay(10)

        if action_callback: action_callback()
        self.state = target_state

        # Fade In
        for alpha in range(255, -1, -15):
            fade_surf.set_alpha(alpha)
            if self.state == "GAME": self.draw_game_frame()
            elif self.state == "EGG": self.draw_egg_frame()
            self.screen.blit(fade_surf, (0,0))
            pygame.display.flip(); pygame.time.delay(10)

    def transition_bg_effect(self, next_bg_mode):
        fade_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        fade_surf.fill((0, 0, 0))
        # Fade Out Game Screen
        for alpha in range(0, 256, 15):
            fade_surf.set_alpha(alpha)
            self.draw_game_frame()
            self.screen.blit(fade_surf, (0,0))
            pygame.display.flip(); pygame.time.delay(10)
            
        if next_bg_mode == "TO_BED": self.pet.cutscene_state = "TO_BED_IN"
        elif next_bg_mode == "WAKE_UP": self.pet.cutscene_state = "WAKE_IN"
        elif next_bg_mode == "TO_BATH": self.pet.cutscene_state = "TO_BATH_IN"
        elif next_bg_mode == "FINISH_BATH": self.pet.cutscene_state = "FINISH_BATH_IN"

        self.pet.fade_trigger = False

        # Fade In
        for alpha in range(255, -1, -15):
            fade_surf.set_alpha(alpha)
            self.draw_game_frame()
            self.screen.blit(fade_surf, (0,0))
            pygame.display.flip(); pygame.time.delay(10)

    def draw_cover_screen(self):
        self.screen.fill(COVER_BG_COLOR)
        shadow_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        points = [(0, SCREEN_HEIGHT), (SCREEN_WIDTH, SCREEN_HEIGHT), (SCREEN_WIDTH, 0), (SCREEN_WIDTH//3, 0)]
        pygame.draw.polygon(shadow_surf, (30, 0, 60, 100), points) 
        self.screen.blit(shadow_surf, (0,0))

        now = datetime.datetime.now()
        # Format 24 Jam
        txt_time = pygame.font.SysFont("Consolas", 80, bold=True).render(now.strftime("%H:%M"), True, (200, 240, 255)) 
        txt_date = pygame.font.SysFont("Consolas", 40, bold=True).render(now.strftime("%Y/%m/%d"), True, (255, 255, 255))

        cx = SCREEN_WIDTH // 2
        # Center Clock
        self.screen.blit(txt_time, txt_time.get_rect(center=(cx, 120)))
        self.screen.blit(txt_date, txt_date.get_rect(center=(cx, 200)))
        
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.btns_cover:
            btn.check_hover(mouse_pos); btn.draw(self.screen, self.font)

    def draw_egg_frame(self):
        if self.bg_room2: self.screen.blit(self.bg_room2, (self.bg_x, self.bg_y))
        else: self.screen.fill(BG_COLOR)
        self.egg.draw(self.screen, DESK_HEIGHT_Y)

    def draw_game_frame(self):
        current_bg = self.bg_room2
        if self.pet.bg_location == "ROOM3": current_bg = self.bg_room3
        elif self.pet.bg_location == "ROOM4": current_bg = self.bg_room4

        if current_bg: self.screen.blit(current_bg, (self.bg_x, self.bg_y))
        else: self.screen.fill(BG_COLOR)

        self.pet.draw(self.screen, SCREEN_WIDTH//2, DESK_HEIGHT_Y)
        self.draw_hud()

        if self.pet.is_alive:
            # UI hanya muncul jika TIDAK CUTSCENE dan TIDAK TIDUR
            if not self.pet.in_cutscene and not self.pet.is_sleeping:
                self.btn_menu.draw(self.screen, self.font)
                if self.is_menu_open:
                    menu_bg_rect = pygame.Rect(50, 225, 120, 250)
                    pygame.draw.rect(self.screen, (30, 30, 30), menu_bg_rect, border_radius=10)
                    for btn in self.btns_actions: btn.draw(self.screen, self.font)
            
            # Jika sedang tidur, gambar overlay Zzz
            if self.pet.is_sleeping:
                self.screen.blit(self.dark_overlay, (0,0))
                z = pygame.font.SysFont("Comic Sans MS", 40, bold=True).render("Zzz...", True, (255,255,255))
                self.screen.blit(z, (SCREEN_WIDTH//2+50, DESK_HEIGHT_Y-100))
        else:
            self.screen.blit(self.dark_overlay, (0,0))
            die_txt = pygame.font.SysFont("Arial", 50, bold=True).render("GAME OVER", True, (255, 50, 50))
            self.screen.blit(die_txt, die_txt.get_rect(center=(SCREEN_WIDTH//2, 250)))
            self.btn_reset.check_hover(pygame.mouse.get_pos()); self.btn_reset.draw(self.screen, self.font)

    def run(self):
        while True:
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    current_session = (pygame.time.get_ticks() - self.start_ticks) // 1000
                    if self.state == "GAME" and self.pet.is_alive: self.pet.save_data(current_session)
                    pygame.quit(); sys.exit()
                
                if not self.pet.in_cutscene:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.state == "COVER":
                            for btn in self.btns_cover:
                                if btn.is_clicked(mouse_pos):
                                    if btn.action_code == "NEW":
                                        def start_new():
                                            if os.path.exists("savegame.json"): os.remove("savegame.json")
                                            self.pet = Kenmochi(); self.egg = Egg()
                                            self.start_ticks = pygame.time.get_ticks()
                                            self.start_bgm_game()
                                        self.fade_effect("EGG", start_new)
                                    elif btn.action_code == "LOAD":
                                        def start_load():
                                            self.start_ticks = pygame.time.get_ticks()
                                            self.start_bgm_game()
                                            if not self.pet.is_alive: 
                                                self.pet = Kenmochi(); self.egg = Egg()
                                                self.state = "EGG" 
                                        target = "GAME" if self.pet.is_alive else "EGG"
                                        self.fade_effect(target, start_load)
                                    elif btn.action_code == "EXIT": pygame.quit(); sys.exit()
                        
                        elif self.state == "EGG":
                            self.egg.click()

                        elif self.state == "GAME":
                            if self.pet.is_alive:
                                # Logika Menu hanya jalan jika TIDAK TIDUR
                                if not self.pet.is_sleeping:
                                    if self.btn_menu.is_clicked(mouse_pos):
                                        self.is_menu_open = not self.is_menu_open
                                    
                                    action_clicked = False
                                    if self.is_menu_open:
                                        for btn in self.btns_actions:
                                            if btn.is_clicked(mouse_pos):
                                                if btn.action_code == "EXIT_GAME":
                                                    cs = (pygame.time.get_ticks() - self.start_ticks) // 1000
                                                    self.pet.save_data(cs)
                                                    pygame.quit(); sys.exit()
                                                else:
                                                    self.pet.start_action(btn.action_code)
                                                    self.is_menu_open = False
                                                    action_clicked = True
                                    
                                    if not self.btn_menu.is_clicked(mouse_pos) and not action_clicked:
                                        self.pet.handle_click(mouse_pos)
                            else:
                                if self.btn_reset.is_clicked(mouse_pos):
                                    if os.path.exists("savegame.json"): os.remove("savegame.json")
                                    self.pet = Kenmochi(); self.egg = Egg()
                                    self.state = "EGG"; self.start_ticks = pygame.time.get_ticks()

                    elif event.type == pygame.MOUSEBUTTONUP:
                        if self.state == "GAME": self.pet.stop_drag()
                    
                    elif event.type == pygame.MOUSEMOTION:
                        if self.state == "GAME": 
                            self.pet.update_drag(mouse_pos)
                            # Update Hover hanya jika UI terlihat
                            if not self.pet.is_sleeping:
                                self.btn_menu.check_hover(mouse_pos)
                                if self.is_menu_open:
                                    for btn in self.btns_actions: btn.check_hover(mouse_pos)

            if self.state == "COVER": self.draw_cover_screen() 
            
            elif self.state == "EGG":
                self.draw_egg_frame()
                if self.egg.is_hatched:
                    self.egg.hatch_timer += 1
                    if self.egg.hatch_timer > 60: self.state = "GAME"

            elif self.state == "GAME":
                if self.pet.fade_trigger:
                    mode = "TO_BED"
                    if self.pet.cutscene_state == "WAIT_FADE_WAKE": mode = "WAKE_UP"
                    elif self.pet.cutscene_state == "WAIT_FADE_BED": mode = "TO_BED"
                    elif self.pet.cutscene_state == "WAIT_FADE": 
                        mode = self.pet.fade_next_mode
                    self.transition_bg_effect(mode)
                self.draw_game_frame()

            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    Game().run()