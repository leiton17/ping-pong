import pygame
import random
import math
import sys
import os
import json
import colorsys
from array import array

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

W, H, FPS = 800, 520, 60
TABLE = pygame.Rect(50, 100, 700, 370)

screen = pygame.display.set_mode((W, H), pygame.SCALED | pygame.RESIZABLE)
pygame.display.set_caption("Ping Pong Toon!")
clock = pygame.time.Clock()
canvas = pygame.Surface((W, H))

# ---------- COLORES Y FUENTES ----------
SKY_TOP, SKY_BOT = (120, 210, 255), (255, 240, 170)
WHITE, OUTLINE = (255, 255, 255), (30, 30, 70)
RED, BLUE, YELLOW = (240, 70, 80), (70, 140, 255), (255, 210, 60)
ORANGE, GREEN = (255, 150, 40), (80, 200, 100)
WOOD = (170, 110, 60)

def make_font(size):
    return pygame.font.SysFont("comicsansms", size, bold=True)

F_BIG, F_MID, F_SMALL, F_TINY = make_font(64), make_font(32), make_font(21), make_font(16)

def lighten(c, k):
    return tuple(min(255, int(v + (255 - v) * k)) for v in c)

def draw_text(surf, text, font, color, center, outline=OUTLINE, o=3):
    base = font.render(text, True, outline)
    for dx in range(-o, o + 1):
        for dy in range(-o, o + 1):
            if dx * dx + dy * dy <= o * o + 1:
                surf.blit(base, base.get_rect(center=(center[0] + dx, center[1] + dy)))
    img = font.render(text, True, color)
    surf.blit(img, img.get_rect(center=center))

def draw_coin(surf, pos, r=11):
    pygame.draw.circle(surf, OUTLINE, pos, r + 2)
    pygame.draw.circle(surf, YELLOW, pos, r)
    pygame.draw.circle(surf, (255, 240, 150), (pos[0] - r // 3, pos[1] - r // 3), max(2, r // 3))

def draw_panel(surf, rect, alpha=215):
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(s, (255, 255, 255, alpha), s.get_rect(), border_radius=24)
    surf.blit(s, rect.topleft)
    pygame.draw.rect(surf, OUTLINE, rect, width=5, border_radius=24)

background = pygame.Surface((W, H))
for y in range(H):
    t = y / H
    pygame.draw.line(background, tuple(int(SKY_TOP[i] * (1 - t) + SKY_BOT[i] * t) for i in range(3)), (0, y), (W, y))
for cx, cy, s in [(120, 40, 1.0), (420, 30, 1.3), (680, 50, 0.9)]:
    for dx, dy, r in [(-25, 5, 22), (0, -8, 28), (28, 4, 22), (10, 10, 20)]:
        pygame.draw.circle(background, WHITE, (int(cx + dx * s), int(cy + dy * s)), int(r * s))

# ---------- GUARDADO ----------
SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "pingpong_save.json")
SAVE = {"coins": 0, "music": 0.5, "sfx": 0.7, "shake": True,
        "owned": {"paddle": [0], "ball": [0], "table": [0]},
        "equipped": {"paddle": 0, "ball": 0, "table": 0}}

def load_save():
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in data.items():
            if k in SAVE:
                if isinstance(SAVE[k], dict) and isinstance(v, dict):
                    SAVE[k].update(v)
                else:
                    SAVE[k] = v
    except Exception:
        pass

def write_save():
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(SAVE, f)
    except Exception:
        pass

load_save()

# ---------- SONIDO (generado por código) ----------
SFX, MUSIC = {}, None
try:
    _channels = pygame.mixer.get_init()[2]

    def make_sound(notes, wave="square", vol=0.35):
        buf, phase, sr = array("h"), 0.0, 44100
        for freq, ms, slide in notes:
            n = int(sr * ms / 1000)
            for i in range(n):
                f = freq + slide * (i / n)
                if f <= 0:
                    v = 0.0
                else:
                    phase += 2 * math.pi * f / sr
                    s = math.sin(phase)
                    v = (1.0 if s >= 0 else -1.0) if wave == "square" else (
                        2 / math.pi * math.asin(s) if wave == "tri" else s)
                env = min(1.0, i / 60) * (1 - i / n)
                val = int(32767 * vol * env * v)
                for _ in range(_channels):
                    buf.append(val)
        return pygame.mixer.Sound(buffer=buf.tobytes())

    SFX = {
        "hit": make_sound([(520, 70, -150)]),
        "smash": make_sound([(300, 140, 500)], vol=0.45),
        "wall": make_sound([(330, 45, 0)], "sine", 0.4),
        "score": make_sound([(440, 90, 0), (660, 160, 0)]),
        "win": make_sound([(523, 110, 0), (659, 110, 0), (784, 110, 0), (1047, 300, 0)]),
        "click": make_sound([(800, 40, 200)], "sine", 0.4),
        "coin": make_sound([(988, 60, 0), (1319, 140, 0)]),
        "no": make_sound([(200, 160, -60)]),
        "tick": make_sound([(600, 60, 0)], "sine", 0.4),
        "go": make_sound([(900, 180, 200)]),
    }
    seq = [523, 659, 784, 659, 587, 740, 880, 740, 523, 659, 784, 1047, 880, 784, 659, 587]
    notes = []
    for fq in seq:
        notes += [(fq, 150, 0), (0, 20, 0)]
    MUSIC = make_sound(notes, "tri", 0.3)
except Exception:
    SFX, MUSIC = {}, None

def play(name):
    s = SFX.get(name)
    if s:
        s.set_volume(SAVE["sfx"])
        s.play()

def apply_volume():
    if MUSIC:
        MUSIC.set_volume(SAVE["music"] * 0.5)

apply_volume()
if MUSIC:
    MUSIC.play(loops=-1)

# ---------- SKINS ----------
PADDLE_SKINS = [
    dict(name="Clásico", price=0, color=(240, 70, 80), accent=WHITE, kind="stripe"),
    dict(name="Océano", price=15, color=(70, 140, 255), accent=(200, 240, 255), kind="stripe"),
    dict(name="Slime", price=25, color=(110, 220, 90), accent=(230, 255, 160), kind="dots"),
    dict(name="Chicle", price=30, color=(255, 130, 200), accent=(255, 230, 245), kind="dots"),
    dict(name="Ninja", price=40, color=(50, 50, 70), accent=(230, 60, 70), kind="stripe"),
    dict(name="Dorada", price=50, color=(255, 200, 40), accent=(255, 245, 170), kind="stripe"),
    dict(name="Fuego", price=60, color=(255, 110, 30), accent=(255, 230, 70), kind="flame"),
    dict(name="Arcoíris", price=100, color=None, accent=WHITE, kind="stripe"),
]
BALL_SKINS = [
    dict(name="Clásica", price=0, color=ORANGE, kind="plain", trail=(255, 200, 120)),
    dict(name="Tenis", price=15, color=(205, 240, 70), kind="seam", seam=WHITE, trail=(220, 255, 140)),
    dict(name="Béisbol", price=25, color=(250, 250, 250), kind="seam", seam=(220, 40, 40), trail=(255, 200, 200)),
    dict(name="Carita", price=30, color=(255, 220, 60), kind="smile", trail=(255, 240, 150)),
    dict(name="Hielo", price=40, color=(150, 230, 255), kind="plain", trail=(200, 245, 255)),
    dict(name="Galaxia", price=50, color=(90, 60, 170), kind="galaxy", trail=(170, 140, 255)),
    dict(name="Fuego", price=60, color=(255, 90, 30), kind="plain", trail=(255, 220, 60)),
    dict(name="Dorada", price=100, color=(255, 200, 40), kind="plain", trail=(255, 240, 150)),
]
TABLE_SKINS = [
    dict(name="Azul", price=0, top=(40, 110, 220), dark=(25, 75, 160), line=WHITE),
    dict(name="Torneo", price=20, top=(30, 140, 80), dark=(20, 95, 55), line=WHITE),
    dict(name="Madera", price=30, top=(195, 135, 75), dark=(140, 90, 45), line=(255, 240, 210)),
    dict(name="Rosa", price=40, top=(235, 100, 170), dark=(180, 60, 120), line=WHITE),
    dict(name="Noche", price=50, top=(45, 45, 100), dark=(25, 25, 65), line=(120, 240, 255)),
    dict(name="Hielo", price=60, top=(130, 210, 240), dark=(90, 160, 200), line=WHITE),
]
CATS = [("Raquetas", "paddle", PADDLE_SKINS), ("Pelotas", "ball", BALL_SKINS), ("Mesas", "table", TABLE_SKINS)]
DIFFS = [("Fácil", 4.2, 55), ("Normal", 5.6, 28), ("Difícil", 7.4, 10)]

def skin_color(skin):
    if skin["color"] is None:
        r, g, b = colorsys.hsv_to_rgb((pygame.time.get_ticks() / 1500) % 1, 0.7, 1)
        return (int(r * 255), int(g * 255), int(b * 255))
    return skin["color"]

def eq_skin(key):
    skins = {"paddle": PADDLE_SKINS, "ball": BALL_SKINS, "table": TABLE_SKINS}[key]
    return skins[SAVE["equipped"][key]]

# ---------- DIBUJO DE OBJETOS ----------
def draw_paddle(surf, r, side, skin, wiggle=0):
    col = skin_color(skin)
    if wiggle:
        r = r.move(-side * int(math.sin(wiggle * 0.9) * 4), 0)
    sh = pygame.Surface((r.w + 8, r.h + 8), pygame.SRCALPHA)
    pygame.draw.rect(sh, (0, 0, 0, 70), sh.get_rect(), border_radius=12)
    surf.blit(sh, (r.x + 3, r.y + 8))
    handle = pygame.Rect(0, 0, int(r.w * 0.8), int(r.w * 0.7))
    if side == -1:
        handle.midright = (r.left + 2, r.centery)
    else:
        handle.midleft = (r.right - 2, r.centery)
    pygame.draw.rect(surf, OUTLINE, handle.inflate(4, 4), border_radius=6)
    pygame.draw.rect(surf, WOOD, handle, border_radius=5)
    pygame.draw.rect(surf, OUTLINE, r.inflate(6, 6), border_radius=12)
    pygame.draw.rect(surf, col, r, border_radius=10)
    acc, kind = skin["accent"], skin["kind"]
    if kind in ("stripe", "flame"):
        pygame.draw.rect(surf, acc, (r.x + 4, r.y + 8, max(3, r.w // 5), max(6, r.h - 40)), border_radius=3)
    if kind == "dots":
        for k in (0.25, 0.5, 0.75):
            pygame.draw.circle(surf, acc, (r.centerx, int(r.y + r.h * k)), max(2, r.w // 5))
    if kind == "flame":
        pts = [(r.left + 3, r.bottom - 4), (r.centerx, r.bottom - int(r.h * 0.4)), (r.right - 3, r.bottom - 4)]
        pygame.draw.polygon(surf, acc, pts)

def draw_ball(surf, x, y, R, skin, hop=0, squash=0, shadow=True):
    if shadow:
        sw = max(8, int(R * 2.2 - hop * 0.4))
        s = pygame.Surface((sw * 2, sw), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, 80), s.get_rect())
        surf.blit(s, s.get_rect(center=(x, y + R + 4)))
    sq = squash / 8
    w, h = int(R * 2 * (1 + 0.35 * sq)), int(R * 2 * (1 - 0.25 * sq))
    body = pygame.Rect(0, 0, w, h)
    body.center = (int(x), int(y - hop))
    pygame.draw.ellipse(surf, OUTLINE, body.inflate(6, 6))
    pygame.draw.ellipse(surf, skin["color"], body)
    k = skin["kind"]
    if k == "seam":
        pygame.draw.arc(surf, skin["seam"], pygame.Rect(body.left - w * 0.45, body.top + 2, w * 0.9, h - 4), -0.9, 0.9, 2)
        pygame.draw.arc(surf, skin["seam"], pygame.Rect(body.right - w * 0.45, body.top + 2, w * 0.9, h - 4), math.pi - 0.9, math.pi + 0.9, 2)
    elif k == "smile":
        pygame.draw.circle(surf, OUTLINE, (body.centerx - w // 5, body.centery - h // 8), max(2, R // 6))
        pygame.draw.circle(surf, OUTLINE, (body.centerx + w // 5, body.centery - h // 8), max(2, R // 6))
        pygame.draw.arc(surf, OUTLINE, pygame.Rect(body.centerx - w // 4, body.centery - h // 8, w // 2, int(h * 0.5)), math.pi + 0.4, 2 * math.pi - 0.4, 2)
    elif k == "galaxy":
        for fx, fy in [(-0.3, -0.2), (0.25, 0.1), (-0.1, 0.35), (0.3, -0.35)]:
            pygame.draw.circle(surf, WHITE, (int(body.centerx + fx * w), int(body.centery + fy * h)), 2)
    if k != "smile":
        pygame.draw.ellipse(surf, WHITE, (body.x + w * 0.2, body.y + h * 0.15, w * 0.28, h * 0.25))

def draw_table(surf, sk, rect=TABLE):
    for lx in (rect.left + 40, rect.right - 60):
        pygame.draw.rect(surf, OUTLINE, (lx - 3, rect.bottom - 5, 26, 52), border_radius=6)
        pygame.draw.rect(surf, (90, 90, 120), (lx, rect.bottom - 5, 20, 48), border_radius=5)
    s = pygame.Surface((rect.w + 40, 50), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, 60), s.get_rect())
    surf.blit(s, (rect.x - 20, rect.bottom + 25))
    pygame.draw.rect(surf, OUTLINE, rect.inflate(16, 16).move(0, 8), border_radius=22)
    pygame.draw.rect(surf, sk["dark"], rect.inflate(10, 10).move(0, 8), border_radius=20)
    pygame.draw.rect(surf, OUTLINE, rect.inflate(10, 10), border_radius=20)
    pygame.draw.rect(surf, sk["top"], rect, border_radius=16)
    pygame.draw.rect(surf, sk["line"], rect.inflate(-16, -16), width=4, border_radius=12)
    pygame.draw.line(surf, sk["line"], (rect.left + 8, rect.centery), (rect.right - 8, rect.centery), 3)
    nx = rect.centerx
    for y in range(rect.top - 6, rect.bottom + 6, 12):
        pygame.draw.rect(surf, WHITE, (nx - 3, y, 6, 7), border_radius=2)
    for py in (rect.top - 12, rect.bottom + 4):
        pygame.draw.rect(surf, OUTLINE, (nx - 9, py, 18, 14), border_radius=6)
        pygame.draw.rect(surf, RED, (nx - 6, py + 2, 12, 10), border_radius=4)

def draw_table_preview(surf, center, sk):
    r = pygame.Rect(0, 0, 110, 64)
    r.center = center
    pygame.draw.rect(surf, OUTLINE, r.inflate(8, 8), border_radius=12)
    pygame.draw.rect(surf, sk["top"], r, border_radius=9)
    pygame.draw.rect(surf, sk["line"], r.inflate(-12, -12), width=3, border_radius=6)
    pygame.draw.line(surf, sk["line"], (r.centerx, r.top + 4), (r.centerx, r.bottom - 4), 3)

# ---------- PARTÍCULAS ----------
particles, floaters = [], []

def burst(x, y, color, n=14, speed=5, gravity=0.0):
    for _ in range(n):
        a, v = random.uniform(0, math.tau), random.uniform(1, speed)
        particles.append([x, y, math.cos(a) * v, math.sin(a) * v, random.randint(18, 34), color, random.randint(3, 7), gravity])

def confetti(n=120):
    for _ in range(n):
        particles.append([random.randint(0, W), -10, random.uniform(-1.5, 1.5), random.uniform(2, 6), random.randint(60, 110),
                          random.choice([RED, BLUE, YELLOW, ORANGE, GREEN]), random.randint(5, 9), 0.05])

def update_particles():
    for p in particles[:]:
        p[0] += p[2]; p[1] += p[3]; p[3] += p[7]; p[4] -= 1
        if p[4] <= 0:
            particles.remove(p)
    for f in floaters[:]:
        f[2] -= 1; f[3] -= 1
        if f[3] <= 0:
            floaters.remove(f)

def draw_particles(surf):
    for p in particles:
        pygame.draw.circle(surf, OUTLINE, (int(p[0]), int(p[1])), p[6] + 1)
        pygame.draw.circle(surf, p[5], (int(p[0]), int(p[1])), p[6])
    for text, x, y, life, color in floaters:
        pass

# ---------- UI ----------
class Button:
    def __init__(self, bid, rect, text, color=YELLOW, font=None, sel=False):
        self.id, self.rect, self.text = bid, pygame.Rect(rect), text
        self.color, self.font, self.sel = color, font or F_MID, sel

    def draw(self, surf, mouse):
        hover = self.rect.collidepoint(mouse)
        r = self.rect.move(0, -4 if hover else 0)
        pygame.draw.rect(surf, OUTLINE, self.rect.move(0, 6).inflate(6, 6), border_radius=18)
        pygame.draw.rect(surf, OUTLINE, r.inflate(6, 6), border_radius=18)
        pygame.draw.rect(surf, lighten(self.color, 0.25 if hover else 0), r, border_radius=15)
        pygame.draw.rect(surf, lighten(self.color, 0.5), (r.x + 8, r.y + 5, r.w - 16, 6), border_radius=3)
        if self.sel:
            pygame.draw.rect(surf, WHITE, r.inflate(14, 14), width=4, border_radius=20)
        draw_text(surf, self.text, self.font, WHITE, r.center, o=2)

class Slider:
    def __init__(self, key, label, rect):
        self.key, self.label, self.rect = key, label, pygame.Rect(rect)

    def hit(self, pos):
        return self.rect.inflate(30, 34).collidepoint(pos)

    def set_from_x(self, x):
        SAVE[self.key] = round(max(0, min(1, (x - self.rect.left) / self.rect.w)), 2)
        apply_volume()

    def draw(self, surf):
        v = SAVE[self.key]
        draw_text(surf, f"{self.label}: {int(v * 100)}%", F_SMALL, WHITE, (self.rect.centerx, self.rect.y - 26), o=2)
        pygame.draw.rect(surf, OUTLINE, self.rect.inflate(8, 8), border_radius=12)
        pygame.draw.rect(surf, (200, 210, 230), self.rect, border_radius=8)
        pygame.draw.rect(surf, YELLOW, (self.rect.x, self.rect.y, int(self.rect.w * v), self.rect.h), border_radius=8)
        kx = self.rect.x + int(self.rect.w * v)
        pygame.draw.circle(surf, OUTLINE, (kx, self.rect.centery), 16)
        pygame.draw.circle(surf, WHITE, (kx, self.rect.centery), 12)

# ---------- OBJETOS DE JUEGO ----------
class Paddle:
    PW, PH = 22, 92

    def __init__(self, side):
        self.side, self.skin, self.ai, self.wiggle = side, PADDLE_SKINS[0], False, 0
        self.home()

    def home(self):
        self.pos = [float(TABLE.left + 70 if self.side == -1 else TABLE.right - 70), float(TABLE.centery)]
        self.vx = self.vy = 0.0

    @property
    def rect(self):
        return pygame.Rect(int(self.pos[0] - self.PW / 2), int(self.pos[1] - self.PH / 2), self.PW, self.PH)

    def move_by(self, dx, dy):
        ox, oy = self.pos
        nx = max(TABLE.left + self.PW // 2 + 6, min(TABLE.right - self.PW // 2 - 6, ox + dx))
        ny = max(TABLE.top + self.PH // 2 + 6, min(TABLE.bottom - self.PH // 2 - 6, oy + dy))
        self.pos = [nx, ny]
        self.vx, self.vy = nx - ox, ny - oy
        if self.wiggle > 0:
            self.wiggle -= 1

class Ball:
    R = 13

    def __init__(self, speed=6.0):
        self.base = speed
        self.reset(1)

    def reset(self, direction):
        self.x, self.y = TABLE.centerx, TABLE.centery
        self.speed = self.base
        a = random.uniform(-0.45, 0.45)
        self.vx, self.vy = direction * self.speed * math.cos(a), self.speed * math.sin(a)
        self.trail, self.squash, self.cd = [], 0, 0

    def step(self):
        self.x += self.vx
        self.y += self.vy
        bounced = False
        if TABLE.left < self.x < TABLE.right:
            top, bot = TABLE.top + self.R + 4, TABLE.bottom - self.R - 4
            if self.y < top:
                self.y, self.vy, bounced = top, abs(self.vy), True
            elif self.y > bot:
                self.y, self.vy, bounced = bot, -abs(self.vy), True
        if bounced:
            self.squash = 8
        self.trail.append((self.x, self.y))
        if len(self.trail) > 12:
            self.trail.pop(0)
        self.squash = max(0, self.squash - 1)
        self.cd = max(0, self.cd - 1)
        return bounced

    def draw(self, surf, skin):
        for i, (tx, ty) in enumerate(self.trail):
            r = int(self.R * (i / max(1, len(self.trail))) * 0.8)
            if r > 1:
                pygame.draw.circle(surf, skin["trail"], (int(tx), int(ty)), r)
        hop = abs(math.sin(self.x * 0.025)) * 16 if TABLE.left < self.x < TABLE.right else 0
        draw_ball(surf, self.x, self.y, self.R, skin, hop, self.squash)

# ---------- JUEGO ----------
class Game:
    def __init__(self):
        self.state = "menu"
        self.mode, self.diff, self.win_score = 1, 1, 7
        self.p1, self.p2 = Paddle(-1), Paddle(1)
        self.ball = Ball()
        self.demo = Ball(4.0)
        self.scores, self.rally, self.shake = [0, 0], 0, 0
        self.serve_timer, self.last_n = 0, 0
        self.earned, self.winner_text = 0, ""
        self.mouse_active, self.paused_from = False, "play"
        self.tab, self.toast, self.settings_back = 0, ("", 0), "menu"
        self.dragging = None
        self.go("menu")

    # ----- cambio de pantallas -----
    def go(self, state):
        self.state = state
        self.buttons, self.sliders, self.cards = [], [], []
        getattr(self, "build_" + state)()

    def build_menu(self):
        x = W // 2 - 130
        self.buttons = [Button("play", (x, 235, 260, 56), "JUGAR", GREEN),
                        Button("shop", (x, 303, 260, 56), "TIENDA", ORANGE),
                        Button("settings", (x, 371, 260, 56), "AJUSTES", BLUE),
                        Button("quit", (x, 439, 260, 56), "SALIR", RED)]

    def build_mode(self):
        b = [Button("p1", (110, 130, 270, 80), "1 JUGADOR", GREEN),
             Button("p2", (420, 130, 270, 80), "2 JUGADORES", BLUE)]
        for i, (name, _, _) in enumerate(DIFFS):
            b.append(Button(f"d{i}", (160 + i * 170, 275, 140, 50), name, ORANGE, F_SMALL, sel=(self.diff == i)))
        for i, pts in enumerate((5, 7, 11)):
            b.append(Button(f"w{pts}", (160 + i * 170, 375, 140, 50), f"{pts} pts", BLUE, F_SMALL, sel=(self.win_score == pts)))
        b.append(Button("back", (W // 2 - 100, 450, 200, 50), "VOLVER", RED, F_SMALL))
        self.buttons = b

    def build_shop(self):
        for i, (name, _, _) in enumerate(CATS):
            self.buttons.append(Button(f"tab{i}", (130 + i * 175, 72, 165, 44), name,
                                       YELLOW if i == self.tab else (140, 170, 220), F_SMALL, sel=(i == self.tab)))
        self.buttons.append(Button("back", (50, 442, 180, 50), "VOLVER", RED, F_SMALL))
        skins = CATS[self.tab][2]
        for i in range(len(skins)):
            col, row = i % 4, i // 4
            self.cards.append((pygame.Rect(56 + col * 176, 128 + row * 150, 160, 140), i))

    def build_settings(self):
        cx = W // 2
        self.sliders = [Slider("music", "Música", (cx - 150, 195, 300, 14)),
                        Slider("sfx", "Efectos", (cx - 150, 270, 300, 14))]
        self.buttons = [Button("shake", (cx - 140, 320, 280, 50), f"Temblor: {'SÍ' if SAVE['shake'] else 'NO'}", ORANGE, F_SMALL),
                        Button("full", (cx - 140, 380, 280, 50), "Pantalla completa", BLUE, F_SMALL),
                        Button("back", (cx - 100, 448, 200, 50), "VOLVER", RED, F_SMALL)]

    def build_serve(self):
        self.buttons = [Button("pause", (W - 72, 14, 52, 52), "II", ORANGE, F_SMALL)]

    build_play = build_serve

    def build_pause(self):
        x = W // 2 - 130
        self.buttons = [Button("resume", (x, 170, 260, 56), "CONTINUAR", GREEN),
                        Button("settings", (x, 238, 260, 56), "AJUSTES", BLUE),
                        Button("menu", (x, 306, 260, 56), "MENÚ PRINCIPAL", ORANGE, F_SMALL),
                        Button("quit", (x, 374, 260, 56), "SALIR", RED)]

    def build_over(self):
        x = W // 2 - 130
        self.buttons = [Button("again", (x, 330, 260, 56), "REVANCHA", GREEN),
                        Button("menu", (x, 400, 260, 56), "MENÚ", ORANGE)]

    # ----- partida -----
    def start_match(self):
        self.scores, self.rally, self.earned = [0, 0], 0, 0
        self.p1.skin = eq_skin("paddle")
        self.p2.skin = PADDLE_SKINS[1] if SAVE["equipped"]["paddle"] != 1 else PADDLE_SKINS[0]
        self.p2.ai = (self.mode == 1)
        self.p1.home(); self.p2.home()
        self.ball.reset(random.choice([-1, 1]))
        particles.clear(); floaters.clear()
        self.serve_timer, self.last_n, self.mouse_active = FPS * 3, 0, False
        self.go("serve")

    def quit(self):
        write_save()
        pygame.quit()
        sys.exit()

    def escape(self):
        s = self.state
        if s in ("serve", "play"):
            self.paused_from = s; self.go("pause")
        elif s == "pause":
            self.resume()
        elif s == "settings":
            self.go(self.settings_back)
        elif s in ("mode", "shop"):
            self.go("menu")

    def resume(self):
        s = self.paused_from
        self.go(s)

    def on_button(self, bid):
        play("click")
        if bid == "play": self.go("mode")
        elif bid == "shop": self.tab = 0; self.go("shop")
        elif bid == "settings":
            self.settings_back = "pause" if self.state == "pause" else "menu"
            self.go("settings")
        elif bid == "quit": self.quit()
        elif bid == "p1": self.mode = 1; self.start_match()
        elif bid == "p2": self.mode = 2; self.start_match()
        elif bid.startswith("tab"): self.tab = int(bid[3:]); self.go("shop")
        elif bid in ("d0", "d1", "d2"): self.diff = int(bid[1]); self.go("mode")
        elif bid in ("w5", "w7", "w11"): self.win_score = int(bid[1:]); self.go("mode")
        elif bid == "back":
            if self.state == "settings": self.go(self.settings_back)
            else: self.go("menu")
        elif bid == "shake": SAVE["shake"] = not SAVE["shake"]; self.go("settings")
        elif bid == "full": pygame.display.toggle_fullscreen()
        elif bid == "pause": self.paused_from = self.state; self.go("pause")
        elif bid == "resume": self.resume()
        elif bid == "menu": write_save(); self.go("menu")
        elif bid == "again": self.start_match()

    def card_click(self, idx):
        _, key, skins = CATS[self.tab]
        skin = skins[idx]
        if idx in SAVE["owned"][key]:
            SAVE["equipped"][key] = idx; play("click"); self.toast = ("¡Equipado!", 90)
        elif SAVE["coins"] >= skin["price"]:
            SAVE["coins"] -= skin["price"]
            SAVE["owned"][key].append(idx)
            SAVE["equipped"][key] = idx
            play("coin"); self.toast = ("¡Comprado!", 90)
            burst(random.randint(200, 600), 250, YELLOW, 25, 6)
        else:
            play("no"); self.toast = (f"Te faltan {skin['price'] - SAVE['coins']} monedas", 90)
        write_save()

    # ----- eventos -----
    def handle(self, e):
        if e.type == pygame.QUIT:
            self.quit()
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.escape()
            elif self.state in ("serve", "play") and e.key in (pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d,
                                                              pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                self.mouse_active = False
        elif e.type == pygame.MOUSEMOTION:
            if self.state in ("serve", "play"):
                self.mouse_active = True
            if self.dragging:
                self.dragging.set_from_x(e.pos[0])
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            if self.dragging:
                self.dragging = None
                play("click")
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for s in self.sliders:
                if s.hit(e.pos):
                    self.dragging = s
                    s.set_from_x(e.pos[0])
                    return
            for b in self.buttons:
                if b.rect.collidepoint(e.pos):
                    self.on_button(b.id)
                    return
            for rect, idx in self.cards:
                if rect.collidepoint(e.pos):
                    self.card_click(idx)
                    return

    # ----- actualización -----
    def update_paddles(self):
        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pos()
        p1, p2 = self.p1, self.p2
        speed = 7.0

        def kdir(u, d, l, r):
            return keys[r] - keys[l], keys[d] - keys[u]

        dx, dy = kdir(pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d)
        if self.mode == 1:
            ax, ay = kdir(pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT)
            dx, dy = dx + ax, dy + ay
        if dx or dy:
            self.mouse_active = False
        if self.mode == 1 and self.mouse_active and not (dx or dy):
            vx, vy = mouse[0] - p1.pos[0], mouse[1] - p1.pos[1]
            dist = math.hypot(vx, vy)
            step = min(dist, 12.0)
            p1.move_by(vx / dist * step if dist else 0, vy / dist * step if dist else 0)
        else:
            n = math.hypot(dx, dy) or 1
            p1.move_by(dx / n * speed if dx or dy else 0, dy / n * speed if dx or dy else 0)

        if self.mode == 2:
            dx, dy = kdir(pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT)
            n = math.hypot(dx, dy) or 1
            p2.move_by(dx / n * speed if dx or dy else 0, dy / n * speed if dx or dy else 0)
        else:
            self.ai_move(p2)

    def ai_move(self, p):
        b = self.ball
        _, sp, err = DIFFS[self.diff]
        t = pygame.time.get_ticks()
        if self.state != "play":
            tx, ty = TABLE.right - 90, TABLE.centery
        elif b.vx > 0:
            lead = max(0.0, (p.pos[0] - b.x) / max(1.0, b.vx))
            ty = b.y + b.vy * lead * 0.8 + math.sin(t * 0.004) * err
            tx = max(TABLE.centerx + 30, min(TABLE.right - 30, b.x + 28))
        else:
            tx, ty = TABLE.right - 90, TABLE.centery + math.sin(t * 0.002) * 40
        vx, vy = tx - p.pos[0], ty - p.pos[1]
        dist = math.hypot(vx, vy)
        step = min(sp, dist)
        p.move_by(vx / dist * step if dist > 1 else 0, vy / dist * step if dist > 1 else 0)

    def circle_hits_rect(self, b, r):
        cx, cy = max(r.left, min(b.x, r.right)), max(r.top, min(b.y, r.bottom))
        return (b.x - cx) ** 2 + (b.y - cy) ** 2 <= b.R ** 2

    def do_hit(self, p):
        b, r = self.ball, p.rect
        rel = max(-1, min(1, (b.y - p.pos[1]) / (p.PH / 2 + b.R)))
        pspeed = math.hypot(p.vx, p.vy)
        ang = max(-1.1, min(1.1, rel * 0.85 + p.vy * 0.05))
        b.speed = min(15, max(6.5, b.speed * 1.04) + pspeed * 0.12)
        smash = pspeed > 8
        if smash:
            b.speed = min(16, b.speed + 2)

        # J1 (izquierda) manda la pelota a la derecha; J2 (derecha) a la izquierda
        direction = 1 if p.side == -1 else -1
        b.vx = direction * b.speed * math.cos(ang)
        b.vy = b.speed * math.sin(ang)

        # Saca la pelota por el lado hacia el que va, para que nunca se quede dentro de la raqueta
        if direction == 1:
            b.x = max(b.x, r.right + b.R)
        else:
            b.x = min(b.x, r.left - b.R)

        b.squash, b.cd, p.wiggle = 8, 10, 10
        self.rally += 1
        self.shake = 10 if smash else 6
        col = skin_color(p.skin)
        burst(b.x, b.y, col, 14, 5)
        burst(b.x, b.y, YELLOW, 6, 6)
        play("smash" if smash else "hit")
        if smash:
            floaters.append(["¡SMASH!", b.x, b.y - 30, 40, YELLOW])
        elif self.rally in (5, 10, 15, 20):
            floaters.append([f"¡Racha {self.rally}!", W // 2, 130, 50, YELLOW])

    def point(self, i):
        self.scores[i] += 1
        self.shake = 12
        self.rally = 0
        if self.mode == 2 or i == 0:
            self.earned += 1
        burst(W // 2, H // 2, skin_color((self.p1, self.p2)[i].skin), 40, 8, 0.1)
        play("score")
        if self.scores[i] >= self.win_score:
            bonus = 0
            if self.mode == 1:
                if i == 0:
                    bonus = [6, 10, 16][self.diff]
                    self.winner_text = "¡GANASTE!"
                else:
                    self.winner_text = "¡GANÓ LA COMPU!"
            else:
                bonus = 5
                self.winner_text = f"¡JUGADOR {i + 1} GANA!"
            self.earned += bonus
            SAVE["coins"] += self.earned
            write_save()
            confetti()
            play("win")
            self.go("over")
        else:
            self.p1.home(); self.p2.home()
            self.ball.reset(-1 if i == 1 else 1)
            self.serve_timer, self.last_n = FPS * 2, 0
            self.state = "serve"

    def update(self):
        update_particles()
        if self.toast[1] > 0:
            self.toast = (self.toast[0], self.toast[1] - 1)
        if self.state in ("serve", "play"):
            self.update_paddles()
            b = self.ball
            if self.state == "serve":
                self.serve_timer -= 1
                n = self.serve_timer // FPS + 1
                if n != self.last_n and self.serve_timer > 0:
                    self.last_n = n
                    play("tick")
                if self.serve_timer <= 0:
                    self.state = "play"
                    play("go")
            else:
                if b.step():
                    play("wall")
                    burst(b.x, b.y, WHITE, 6, 3)
                for p in (self.p1, self.p2):
                    if b.cd == 0 and self.circle_hits_rect(b, p.rect):
                        self.do_hit(p)
                if b.x < TABLE.left - 50:
                    self.point(1)
                elif b.x > TABLE.right + 50:
                    self.point(0)
        elif self.state in ("menu", "mode", "shop", "settings"):
            d = self.demo
            d.step()
            if d.x < TABLE.left + 20 or d.x > TABLE.right - 20:
                d.vx *= -1

    # ----- dibujo -----
    def draw_scene(self, c):
        c.blit(background, (0, 0))
        draw_table(c, eq_skin("table"))
        for p, rx in ((self.p1, TABLE.left + 8), (self.p2, TABLE.right - 22)):
            s = pygame.Surface((14, TABLE.h - 16), pygame.SRCALPHA)
            s.fill((*skin_color(p.skin), 90))
            c.blit(s, (rx, TABLE.top + 8))
        for p in (self.p1, self.p2):
            draw_paddle(c, p.rect, p.side, p.skin, p.wiggle)
        self.ball.draw(c, eq_skin("ball"))
        draw_particles(c)
        # marcador
        names = ("TÚ", "COMPU") if self.mode == 1 else ("J1", "J2")
        for i, p in enumerate((self.p1, self.p2)):
            cx = 150 if i == 0 else W - 180
            pygame.draw.circle(c, OUTLINE, (cx, 45), 36)
            pygame.draw.circle(c, skin_color(p.skin), (cx, 45), 31)
            draw_text(c, str(self.scores[i]), F_MID, WHITE, (cx, 43))
            draw_text(c, names[i], F_TINY, WHITE, (cx, 88), o=2)
        draw_text(c, "VS", F_MID, YELLOW, (W // 2 - 15, 45))
        if self.rally >= 4:
            draw_text(c, f"Racha {self.rally}", F_SMALL, YELLOW, (W // 2 - 15, 82), o=2)
        for text, x, y, life, color in floaters:
            draw_text(c, text, F_MID, color, (int(x), int(y - (50 - life) * 0.6)), o=3)
        if self.state == "serve":
            draw_text(c, str(self.serve_timer // FPS + 1), F_BIG, YELLOW, (W // 2, H // 2 - 70), o=5)
            hint = "Mueve con el mouse o con WASD / flechas" if self.mode == 1 else "J1: W A S D     J2: flechas"
            draw_text(c, hint, F_SMALL, WHITE, (W // 2, H - 22), o=2)

    def draw_menu_bg(self, c):
        c.blit(background, (0, 0))
        draw_table(c, eq_skin("table"))
        self.demo.draw(c, eq_skin("ball"))
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 90))
        c.blit(dim, (0, 0))

    def draw_coins(self, c, pos):
        draw_coin(c, (pos[0] - 34, pos[1]))
        draw_text(c, str(SAVE["coins"]), F_MID, YELLOW, (pos[0] + 6, pos[1]), o=2)

    def draw(self):
        c, mouse, s = canvas, pygame.mouse.get_pos(), self.state
        if s in ("serve", "play", "pause", "over"):
            self.draw_scene(c)
            if s in ("pause", "over"):
                dim = pygame.Surface((W, H), pygame.SRCALPHA)
                dim.fill((0, 0, 0, 140))
                c.blit(dim, (0, 0))
        else:
            self.draw_menu_bg(c)

        if s == "menu":
            bob = math.sin(pygame.time.get_ticks() * 0.005) * 6
            draw_text(c, "PING PONG", F_BIG, YELLOW, (W // 2, 90 + bob), o=5)
            draw_text(c, "TOON!", F_BIG, RED, (W // 2, 155 + bob), o=5)
            self.draw_coins(c, (W - 80, 30))
        elif s == "mode":
            draw_text(c, "ELIGE TU PARTIDA", F_MID, YELLOW, (W // 2, 70), o=4)
            draw_text(c, "Dificultad (vs compu)", F_SMALL, WHITE, (W // 2, 250), o=2)
            draw_text(c, "Puntos para ganar", F_SMALL, WHITE, (W // 2, 350), o=2)
        elif s == "shop":
            draw_panel(c, pygame.Rect(30, 60, W - 60, H - 68))
            draw_text(c, "TIENDA", F_MID, YELLOW, (W // 2 - 270, 30), o=4)
            self.draw_coins(c, (W - 80, 30))
            _, key, skins = CATS[self.tab]
            for rect, idx in self.cards:
                sk = skins[idx]
                hover = rect.collidepoint(mouse)
                r = rect.move(0, -3 if hover else 0)
                owned, eq = idx in SAVE["owned"][key], idx == SAVE["equipped"][key]
                pygame.draw.rect(c, OUTLINE, r.move(0, 5), border_radius=16)
                pygame.draw.rect(c, (215, 255, 220) if eq else WHITE, r, border_radius=16)
                pygame.draw.rect(c, OUTLINE, r, width=4, border_radius=16)
                pc = (r.centerx, r.y + 50)
                if key == "paddle":
                    draw_paddle(c, pygame.Rect(pc[0] - 9, pc[1] - 32, 18, 64), -1, sk)
                elif key == "ball":
                    draw_ball(c, pc[0], pc[1], 20, sk, shadow=False)
                else:
                    draw_table_preview(c, pc, sk)
                draw_text(c, sk["name"], F_SMALL, WHITE, (r.centerx, r.y + 98), o=2)
                if eq:
                    draw_text(c, "EQUIPADO", F_TINY, (60, 190, 90), (r.centerx, r.y + 122), o=2)
                elif owned:
                    draw_text(c, "EQUIPAR", F_TINY, BLUE, (r.centerx, r.y + 122), o=2)
                else:
                    draw_coin(c, (r.centerx - 22, r.y + 122), 9)
                    draw_text(c, str(sk["price"]), F_SMALL, YELLOW, (r.centerx + 6, r.y + 121), o=2)
            if self.toast[1] > 0:
                draw_text(c, self.toast[0], F_SMALL, YELLOW, (W // 2 + 130, 467), o=3)
        elif s == "settings":
            draw_panel(c, pygame.Rect(W // 2 - 220, 80, 440, 430), 170)
            draw_text(c, "AJUSTES", F_MID, YELLOW, (W // 2, 125), o=4)
            for sl in self.sliders:
                sl.draw(c)
        elif s == "pause":
            draw_text(c, "PAUSA", F_BIG, YELLOW, (W // 2, 110), o=5)
        elif s == "over":
            draw_text(c, self.winner_text, F_BIG, YELLOW, (W // 2, 150), o=5)
            draw_text(c, f"{self.scores[0]}  -  {self.scores[1]}", F_MID, WHITE, (W // 2, 225))
            draw_coin(c, (W // 2 - 90, 280), 13)
            draw_text(c, f"+{self.earned} monedas", F_MID, YELLOW, (W // 2 + 10, 280), o=3)
        draw_particles(c)
        for b in self.buttons:
            b.draw(c, mouse)

        ox = oy = 0
        if self.shake > 0:
            if SAVE["shake"]:
                ox, oy = random.randint(-self.shake, self.shake), random.randint(-self.shake, self.shake)
            self.shake -= 1
        screen.fill(SKY_TOP)
        screen.blit(c, (ox, oy))
        pygame.display.flip()

def main():
    game = Game()
    while True:
        for e in pygame.event.get():
            game.handle(e)
        game.update()
        game.draw()
        clock.tick(FPS)

main()