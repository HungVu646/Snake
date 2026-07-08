import csv
import heapq
import json
import math
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path

os.environ["SDL_WINDOWS_DPI_AWARENESS"] = "permonitorv2"
os.environ["SDL_VIDEO_HIGHDPI_DISABLED"] = "0"
os.environ["SDL_HINT_RENDER_SCALE_QUALITY"] = "2"
try:
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

import pygame
import pygame.gfxdraw

pygame.init()
pygame.font.init()

HQ = 4

BG = (8, 11, 20)
PANEL = (20, 26, 42)
PANEL2 = (15, 20, 33)
BORDER = (55, 66, 91)
TX = (227, 234, 248)
TX2 = (180, 195, 225)
GREEN = (0, 224, 138)
CYAN = (35, 196, 240)
GOLD = (255, 207, 61)
RED = (255, 91, 91)
ORANGE = (255, 140, 0)
OPEN = (59, 130, 246)
CLOSED = (100, 116, 140)

ROOT = Path(__file__).resolve().parent
SAVE_FILE = ROOT / "snake_config.json"
HISTORY_FILE = ROOT / "snake_history.json"

LEVELS = [
    {"cols": 15, "rows": 15, "obs": 3, "speed": 200, "name": "Dễ"},
    {"cols": 20, "rows": 20, "obs": 8, "speed": 140, "name": "Vừa"},
    {"cols": 26, "rows": 26, "obs": 16, "speed": 95, "name": "Khó"},
]

SKINS = [
    ("Ngọc Lục", [(167, 243, 208), (74, 222, 128), (21, 128, 61), (5, 46, 22)], (74, 222, 128)),
    ("Đại Dương", [(186, 230, 253), (56, 189, 248), (3, 105, 161), (8, 47, 73)], (56, 189, 248)),
    ("Hoàng Kim", [(254, 240, 138), (250, 204, 21), (161, 98, 7), (66, 32, 6)], (250, 204, 21)),
    ("Hồng Ngọc", [(251, 207, 232), (244, 114, 182), (190, 24, 93), (80, 7, 36)], (244, 114, 182)),
    ("Lửa", [(254, 215, 170), (251, 146, 60), (194, 65, 12), (67, 20, 7)], (251, 146, 60)),
    ("Tím Huyền", [(233, 213, 255), (192, 132, 252), (124, 58, 237), (46, 16, 101)], (192, 132, 252)),
    ("Titan", [(241, 245, 249), (148, 163, 184), (51, 65, 85), (15, 23, 42)], (148, 163, 184)),
    ("Đỏ Thẫm", [(254, 202, 202), (248, 113, 113), (185, 28, 28), (69, 10, 10)], (248, 113, 113)),
    ("Biển Sâu", [(153, 246, 228), (45, 212, 191), (15, 118, 110), (4, 47, 46)], (45, 212, 191)),
    ("Cầu Vồng", [(240, 171, 252), (129, 140, 248), (52, 211, 153), (251, 191, 36), (248, 113, 113)], (255, 255, 255)),
]

BONUS_TYPES = [
    {"emoji": "★", "color": GOLD, "pts": 50, "name": "SAO"},
    {"emoji": "♦", "color": CYAN, "pts": 80, "name": "KIM CƯƠNG"},
    {"emoji": "⚡", "color": ORANGE, "pts": 30, "name": "TỐC ĐỘ", "speed": True},
]

# ===== HÀM TIỆN ÍCH CHUNG =====
def clamp(x, a, b):
    """Giới hạn một giá trị nằm trong khoảng từ a đến b."""
    return max(a, min(b, x))


def lerp_color(a, b, t):
    """Pha trộn hai màu RGB theo hệ số t."""
    t = clamp(t, 0, 1)
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def skin_color(colors, t):
    """Lấy màu thân rắn theo vị trí trên gradient của skin."""
    if len(colors) == 1:
        return colors[0]
    pos = t * (len(colors) - 1)
    i = int(pos)
    if i >= len(colors) - 1:
        return colors[-1]
    return lerp_color(colors[i], colors[i + 1], pos - i)


def draw_text(surf, text, font, color, x, y, center=False):
    """Vẽ chữ có viền mỏng để nổi bật hơn trên nền tối."""
    txt = str(text)

    img = font.render(txt, True, color)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    # Viền đen mỏng giúp chữ sáng không bị chìm vào nền tối.
    outline = font.render(txt, True, (0, 0, 0))
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        surf.blit(outline, rect.move(dx, dy))

    # Đổ bóng nhẹ để chữ có chiều sâu hơn.
    shadow = font.render(txt, True, (10, 12, 18))
    surf.blit(shadow, rect.move(2, 2))

    surf.blit(img, rect)
    return rect


def rounded_rect(surf, rect, color, radius=12, border=None, width=1):
    """Vẽ khung bo góc có chống răng cưa bằng supersampling."""
    rect = pygame.Rect(rect)
    scale = HQ
    tmp = pygame.Surface((rect.w * scale + 4, rect.h * scale + 4), pygame.SRCALPHA)
    rr = pygame.Rect(2, 2, rect.w * scale, rect.h * scale)
    pygame.draw.rect(tmp, color, rr, border_radius=max(1, radius * scale))
    if border:
        pygame.draw.rect(tmp, border, rr, max(1, width * scale), border_radius=max(1, radius * scale))
    small = pygame.transform.smoothscale(tmp, (rect.w + 2, rect.h + 2))
    surf.blit(small, (rect.x - 1, rect.y - 1), special_flags=pygame.BLEND_PREMULTIPLIED)


def glow_circle(surf, x, y, r, color, strength=4):
    """Vẽ hình tròn phát sáng dùng cho hiệu ứng glow."""
    x, y, r = float(x), float(y), max(1.0, float(r))
    pad = int((r + strength * 7) * 2)
    size = max(8, pad * HQ)
    tmp = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = size // 2
    for i in range(strength, 0, -1):
        rr = int((r + i * 5) * HQ)
        alpha = int(10 + i * 10)
        pygame.draw.circle(tmp, (*color, alpha), (cx, cy), rr)
    pygame.draw.circle(tmp, (*color, 255), (cx, cy), int(r * HQ))
    pygame.draw.circle(tmp, (*lerp_color(color, (255,255,255), .35), 190), (cx-int(r*.22*HQ), cy-int(r*.25*HQ)), max(1, int(r*.32*HQ)))
    small = pygame.transform.smoothscale(tmp, (size // HQ, size // HQ))
    surf.blit(small, (int(x - small.get_width()/2), int(y - small.get_height()/2)), special_flags=pygame.BLEND_PREMULTIPLIED)


def radial_circle(surf, x, y, r, inner, mid, outer, glow=None, glow_power=0):
    """Vẽ hình tròn gradient dùng cho thức ăn và vật cản."""
    x, y, r = float(x), float(y), max(1.0, float(r))
    glow_extra = (glow_power * 4 if glow else 2)
    pad = int((r + glow_extra) * 2 + 8)
    size = max(10, pad * HQ)
    tmp = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = size // 2
    rr_base = int(r * HQ)
    if glow:
        for k in range(glow_power, 0, -1):
            rr = rr_base + int(k * 4 * HQ)
            alpha = max(5, 8 * k)
            pygame.draw.circle(tmp, (*glow, alpha), (cx, cy), rr)
    for i in range(rr_base, 0, -1):
        t = i / rr_base
        col = lerp_color(mid, outer, t) if t > .45 else lerp_color(inner, mid, t/.45)
        pygame.draw.circle(tmp, (*col, 255), (cx, cy), i)
    hi_r = max(1, int(rr_base * .28))
    pygame.draw.circle(tmp, (255,255,255,70), (cx-int(rr_base*.24), cy-int(rr_base*.28)), hi_r)
    pygame.draw.circle(tmp, (*outer, 230), (cx, cy), rr_base, max(1, HQ))
    small = pygame.transform.smoothscale(tmp, (size // HQ, size // HQ))
    surf.blit(small, (int(x - small.get_width()/2), int(y - small.get_height()/2)), special_flags=pygame.BLEND_PREMULTIPLIED)

def gradient_text(surface, text, font, x, y,
                  color_top, color_bottom,
                  center=False):
    txt = str(text)
    base = font.render(txt, True, (255, 255, 255))
    w, h = base.get_size()
    bright_top = lerp_color(color_top, (255, 255, 255), 0.25)
    bright_bottom = lerp_color(color_bottom, (255, 255, 255), 0.15)
    gradient = pygame.Surface((w, h), pygame.SRCALPHA)

    for iy in range(h):
        t = iy / max(1, h - 1)
        r = int(bright_top[0] * (1 - t) + bright_bottom[0] * t)
        g = int(bright_top[1] * (1 - t) + bright_bottom[1] * t)
        b = int(bright_top[2] * (1 - t) + bright_bottom[2] * t)
        pygame.draw.line(gradient, (r, g, b), (0, iy), (w, iy))
    gradient.blit(base, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    rect = gradient.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    shadow = font.render(txt, True, (0, 0, 0))
    shadow.set_alpha(180)
    surface.blit(shadow, rect.move(4, 4))
    glow = font.render(txt, True, bright_bottom)
    glow.set_alpha(65)
    for dx, dy in [
        (-4, 0), (4, 0), (0, -4), (0, 4),
        (-3, -3), (3, 3), (-3, 3), (3, -3)
    ]:
        surface.blit(glow, rect.move(dx, dy))
    outline = font.render(txt, True, (0, 0, 0))
    for dx, dy in [
        (-2, 0), (2, 0), (0, -2), (0, 2),
        (-2, -2), (2, 2), (-2, 2), (2, -2),
        (-3, 0), (3, 0), (0, -3), (0, 3)
    ]:
        surface.blit(outline, rect.move(dx, dy))

    surface.blit(gradient, rect)
    return rect

def draw_toggle(surf, rect, on):
    """Vẽ công tắc bật/tắt trong menu."""
    rounded_rect(surf, rect, (0,92,70) if on else (45,47,56), rect.h//2, (0,224,138) if on else BORDER, 1)
    cx = rect.x + rect.w - rect.h//2 if on else rect.x + rect.h//2
    pygame.draw.circle(surf, GREEN if on else (235,235,240), (cx, rect.centery), rect.h//2-3)


# ===== THÀNH PHẦN GIAO DIỆN DÙNG CHUNG =====
@dataclass
class Button:
    rect: pygame.Rect
    text: str
    action: str
    selected: bool = False
    small: str = ""

    def draw(self, surf, font, small_font):
        """Vẽ một nút lựa chọn trong giao diện."""
        bg = (18, 28, 42) if self.selected else PANEL
        border = GREEN if self.selected else BORDER
        rounded_rect(surf, self.rect, bg, 12, border, 2)
        draw_text(surf, self.text, font, GREEN if self.selected else TX, self.rect.centerx, self.rect.y + 18, True)
        if self.small:
            draw_text(surf, self.small, small_font, TX2, self.rect.centerx, self.rect.y + 42, True)


# ===== LỚP CHÍNH: LOGIC GAME VÀ GIAO DIỆN =====
class SnakeGame:
    def __init__(self):
        """Khởi tạo cửa sổ, font, trạng thái menu và dữ liệu lưu trữ."""
        self.display_flags = pygame.RESIZABLE | pygame.DOUBLEBUF
        info = pygame.display.Info()
        start_w = min(max(1280, info.current_w), 1810)
        start_h = min(max(800, info.current_h), 900)
        self.screen = pygame.display.set_mode((start_w, start_h), self.display_flags, vsync=1)
        pygame.display.set_caption("Snake A* Pathfinding - Python")
        self.clock = pygame.time.Clock()
        orbit = (pygame.font.match_font("orbitron") or
                 pygame.font.match_font("bahnschrift") or
                 pygame.font.match_font("consolas") or None)
        space = (pygame.font.match_font("space grotesk") or
                 pygame.font.match_font("segoeui") or
                 pygame.font.match_font("arial") or None)
        self.font_big = pygame.font.Font(orbit, 34)
        self.font_big.set_bold(True)
        self.font_title = pygame.font.Font(orbit, 28)
        self.font_title.set_bold(True)
        self.font_num = pygame.font.Font(orbit, 17)
        self.font_num.set_bold(True)
        self.font = pygame.font.Font(space, 18)
        self.font.set_bold(True)
        self.font_bold = pygame.font.Font(space, 18)
        self.font_bold.set_bold(True)
        self.font_small = pygame.font.Font(space, 13)
        self.font_small.set_bold(True)
        self.font_tiny = pygame.font.Font(space, 10)
        self.font_tiny.set_bold(True)
        self.mode = "menu"
        self.level_idx = 0
        self.skin_idx = 0
        self.player_name = "Player"
        self.name_active = False
        self.settings = {
            "showPath": True, "showExplored": True, "showGrid": True,
            "bonusFood": False, "combo": False, "speedBoost": False,
            "multiFood": False, "survivalMode": False,
        }
        self.high_scores = {"easy": 0, "medium": 0, "hard": 0}
        self.history = []
        self.load_config()
        self.load_history()
        self.buttons = []
        self.reset_runtime_only()

    def reset_runtime_only(self):
        """Đặt lại các biến chỉ dùng trong một lượt chơi."""
        self.cfg = LEVELS[self.level_idx].copy()
        self.cols = self.cfg["cols"]
        self.rows = self.cfg["rows"]
        self.cell = 24
        self.ox = self.oy = 0
        self.snake = []
        self.dir = (1, 0)
        self.ndir = (1, 0)
        self.foods = []
        self.obstacles = []
        self.path = []
        self.explored = []
        self.current_target = None
        self.current_target_name = ""
        self.ai = True
        self.paused = False
        self.dead = False
        self.score = 0
        self.total_steps = 0
        self.replans = 0
        self.astar_steps = 0
        self.astar_ms = 0.0
        self.last_tick = pygame.time.get_ticks()
        self.cur_speed_mult = 1.0
        self.speed_boost_until = 0
        self.bonus = None
        self.combo_count = 0
        self.combo_until = 0
        self.max_combo = 0
        self.survival_tick = 0
        self.spawn_interval = 20
        self.log_entries = []
        self.popups = []
        self.notifs = []
        self.game_over_reason = ""
        self.history_saved = False
        self.prev_head = None
        self.next_head = None

    def save_config(self):
        """Lưu cấu hình người chơi, skin, level và high score."""
        data = {"playerName": self.player_name, "skinIndex": self.skin_idx, "levelIndex": self.level_idx, "highScores": self.high_scores}
        SAVE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_config(self):
        """Đọc cấu hình đã lưu từ file JSON."""
        if SAVE_FILE.exists():
            try:
                data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
                self.player_name = data.get("playerName", "Player") or "Player"
                self.skin_idx = int(data.get("skinIndex", 0))
                self.level_idx = int(data.get("levelIndex", 0))
                self.high_scores = data.get("highScores", self.high_scores)
            except Exception:
                pass

    def load_history(self):
        """Đọc lịch sử các lượt chơi từ file JSON."""
        self.history = []
        if HISTORY_FILE.exists():
            try:
                data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self.history = data[-50:]
            except Exception:
                self.history = []

    def save_history(self):
        """Ghi lịch sử các lượt chơi ra file JSON."""
        try:
            HISTORY_FILE.write_text(json.dumps(self.history[-50:], ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def record_history(self, reason):
        """Lưu một lượt chơi vào lịch sử khi game kết thúc."""
        if self.history_saved:
            return
        self.history_saved = True
        entry = {
            "time": time.strftime("%d/%m/%Y %H:%M:%S"),
            "player": self.player_name or "Player",
            "level": self.cfg.get("name", LEVELS[self.level_idx]["name"]),
            "score": int(self.score),
            "length": len(self.snake),
            "steps": int(self.total_steps),
            "reason": reason,
        }
        self.history.append(entry)
        self.history = self.history[-50:]
        self.save_history()

    def start_game(self):
        """Bắt đầu ván mới từ các tùy chọn đang chọn ở menu."""
        self.save_config()
        self.mode = "game"
        self.reset_runtime_only()
        self.cfg = LEVELS[self.level_idx].copy()
        self.cols, self.rows = self.cfg["cols"], self.cfg["rows"]
        mx, my = self.cols // 2, self.rows // 2
        self.snake = [(mx, my), (mx - 1, my), (mx - 2, my)]
        self.dir = self.ndir = (1, 0)
        self.prev_head = self.next_head = (mx, my)
        self.size_grid()
        self.foods = []
        if not self.settings["survivalMode"]:
            for _ in range(3 if self.settings["multiFood"] else 1):
                self.add_food()
        self.init_obstacles()
        self.compute_ai_direction()
        self.last_tick = pygame.time.get_ticks()

    def size_grid(self):
        """Tính kích thước ô và vị trí bàn chơi theo kích thước cửa sổ."""
        w, h = self.screen.get_size()
        hud_h = 48
        status_h = 20
        right = 300 if w > 860 else 0
        area_w = w - right
        area_h = h - hud_h - status_h
        self.cell = max(10, int(min(area_w / self.cols, area_h / self.rows)))
        self.ox = int((area_w - self.cols * self.cell) / 2)
        self.oy = hud_h + int((area_h - self.rows * self.cell) / 2)

    def key(self, p):
        """Tạo khóa duy nhất cho một ô trên lưới."""
        return p[0] * 10000 + p[1]

    def occupied(self, x, y, skip_food=False):
        """Kiểm tra một ô có đang bị rắn, mồi, bonus hoặc vật cản chiếm không."""
        if (x, y) in self.snake:
            return True
        if not skip_food and (x, y) in self.foods:
            return True
        if any(o["x"] == x and o["y"] == y for o in self.obstacles):
            return True
        if self.bonus and self.bonus["x"] == x and self.bonus["y"] == y:
            return True
        return False

    def add_food(self):
        """Sinh một mồi mới ở ô trống."""
        for _ in range(500):
            x, y = random.randrange(self.cols), random.randrange(self.rows)
            if not self.occupied(x, y, True) and (x, y) not in self.foods:
                self.foods.append((x, y))
                return

    def init_obstacles(self):
        """Tạo danh sách vật cản di động theo cấp độ."""
        count = self.cfg["obs"] if not self.settings["survivalMode"] else max(2, self.cfg["obs"] // 2)
        self.obstacles = []
        for _ in range(count):
            for _ in range(300):
                x, y = random.randrange(self.cols), random.randrange(self.rows)
                if not self.occupied(x, y, True):
                    self.obstacles.append({"x": x, "y": y, "vx": random.choice([-1, 1]), "vy": random.choice([-1, 1]), "tick": 0, "interval": random.randint(5, 12)})
                    break

    def manhattan(self, a, b):
        """Tính khoảng cách Manhattan giữa hai ô."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def astar(self, start, goal):
        """Tìm đường ngắn nhất bằng thuật toán A* và trả về node đã duyệt."""
        blocked_snake = {self.key(p) for p in self.snake[1:]}
        blocked_obs = {o["x"] * 10000 + o["y"] for o in self.obstacles}
        open_heap = []
        counter = 0
        heapq.heappush(open_heap, (self.manhattan(start, goal), 0, counter, start, None))
        parent = {}
        gscore = {start: 0}
        closed = set()
        explored = []
        it = 0
        while open_heap and it < 4000:
            it += 1
            _, g, _, cur, par = heapq.heappop(open_heap)
            ck = self.key(cur)
            if ck in closed:
                continue
            closed.add(ck)
            parent[cur] = par
            explored.append(cur)
            if cur == goal:
                path = []
                p = cur
                while parent[p] is not None:
                    path.append(p)
                    p = parent[p]
                path.reverse()
                return path, explored, it
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cur[0] + dx, cur[1] + dy
                nk = nx * 10000 + ny
                if nx < 0 or nx >= self.cols or ny < 0 or ny >= self.rows:
                    continue
                if nk in closed or nk in blocked_snake or nk in blocked_obs:
                    continue
                ng = g + 1
                np = (nx, ny)
                if ng >= gscore.get(np, 10**9):
                    continue
                gscore[np] = ng
                counter += 1
                heapq.heappush(open_heap, (ng + self.manhattan(np, goal), ng, counter, np, cur))
        return None, explored, it

    def compute_ai_direction(self):
        """Chọn hướng đi tiếp theo cho AI dựa trên đường A* an toàn."""
        start = self.snake[0]
        target = None
        best_path = None
        best_exp = []
        best_it = 0
        t0 = time.perf_counter()
        if self.settings["survivalMode"]:
            best_score, best_cell = -1, None
            for x in range(self.cols):
                for y in range(self.rows):
                    if self.occupied(x, y):
                        continue
                    md = min([self.manhattan((x, y), (o["x"], o["y"])) for o in self.obstacles] or [99])
                    if md > best_score:
                        best_score, best_cell = md, (x, y)
            target = best_cell or (self.cols // 2, self.rows // 2)
            best_path, best_exp, best_it = self.astar(start, target)
        else:
            targets = []
            for f in self.foods:
                targets.append({"pos": f, "name": "mồi"})
            if self.bonus:
                bonus_pos = (self.bonus["x"], self.bonus["y"])
                bonus_name = self.bonus["type"].get("name", "bonus").lower()
                targets.append({"pos": bonus_pos, "name": f"bonus {bonus_name}"})

            for item in targets:
                path, exp, it = self.astar(start, item["pos"])
                if path and (
                    best_path is None
                    or len(path) < len(best_path)
                    or (len(path) == len(best_path) and item["name"].startswith("bonus"))
                ):
                    best_path = path
                    best_exp = exp
                    best_it = it
                    target = item["pos"]
                    self.current_target_name = item["name"]

            if best_path is None and targets:
                target = min(targets, key=lambda item: self.manhattan(start, item["pos"]))["pos"]
                fallback_item = next(item for item in targets if item["pos"] == target)
                self.current_target_name = fallback_item["name"]
                best_path, best_exp, best_it = self.astar(start, target)
        self.current_target = target
        if target is None:
            self.current_target_name = ""
        self.astar_ms = (time.perf_counter() - t0) * 1000
        self.astar_steps = best_it
        self.explored = best_exp
        self.path = best_path or []
        self.log_entries.append({"step": len(self.log_entries)+1, "timeMs": self.astar_ms, "nodes": self.astar_steps, "pathLen": len(self.path), "headX": start[0], "headY": start[1], "targetX": target[0] if target else -1, "targetY": target[1] if target else -1})
        if self.path:
            self.replans += 1
            return self.path[0][0] - start[0], self.path[0][1] - start[1]
        blocked = {self.key(p) for p in self.snake[1:]} | {o["x"] * 10000 + o["y"] for o in self.obstacles}
        for dx, dy in ((1,0), (-1,0), (0,1), (0,-1)):
            if (dx, dy) == (-self.dir[0], -self.dir[1]):
                continue
            nx, ny = start[0] + dx, start[1] + dy
            if 0 <= nx < self.cols and 0 <= ny < self.rows and nx * 10000 + ny not in blocked:
                return dx, dy
        return self.dir

    def move_obstacles(self):
        """Cập nhật vị trí vật cản di động sau mỗi tick."""
        for o in self.obstacles:
            o["tick"] += 1
            if o["tick"] < o["interval"]:
                continue
            o["tick"] = 0
            o["interval"] = random.randint(5, 12)
            nx, ny = o["x"] + o["vx"], o["y"] + o["vy"]
            if nx < 0 or nx >= self.cols:
                o["vx"] *= -1; nx = o["x"] + o["vx"]
            if ny < 0 or ny >= self.rows:
                o["vy"] *= -1; ny = o["y"] + o["vy"]
            if (nx, ny) not in self.snake and (nx, ny) not in self.foods:
                o["x"], o["y"] = nx, ny
        if self.settings["survivalMode"]:
            self.survival_tick += 1
            if self.survival_tick % self.spawn_interval == 0:
                self.spawn_interval = max(5, self.spawn_interval - 1)
                for _ in range(300):
                    x, y = random.randrange(self.cols), random.randrange(self.rows)
                    if not self.occupied(x, y, True):
                        self.obstacles.append({"x": x, "y": y, "vx": random.choice([-1, 1]), "vy": random.choice([-1, 1]), "tick": 0, "interval": random.randint(3, 8)})
                        self.score += 5
                        break

    def tick(self):
        """Cập nhật toàn bộ logic của một bước game."""
        now = pygame.time.get_ticks()
        speed = max(40, int(self.cfg["speed"] / self.cur_speed_mult))
        if now - self.last_tick < speed or self.paused or self.dead:
            return
        self.last_tick = now
        if self.speed_boost_until and now > self.speed_boost_until:
            self.cur_speed_mult = 1.0
            self.speed_boost_until = 0
            self.notifs.append(["Tốc độ bình thường", now + 1800, CYAN])
        if self.combo_until and now > self.combo_until:
            self.combo_count = 0
            self.combo_until = 0
        self.move_obstacles()
        if self.ai:
            self.dir = self.compute_ai_direction()
        elif self.ndir != (-self.dir[0], -self.dir[1]):
            self.dir = self.ndir
        hx, hy = self.snake[0]
        head = (hx + self.dir[0], hy + self.dir[1])
        if head[0] < 0 or head[0] >= self.cols or head[1] < 0 or head[1] >= self.rows:
            return self.game_over("Đâm vào tường!")
        if head in self.snake:
            return self.game_over("Đâm vào thân mình!")
        if any(o["x"] == head[0] and o["y"] == head[1] for o in self.obstacles):
            return self.game_over("Đâm vào chướng ngại vật!")
        self.prev_head = self.snake[0]
        self.next_head = head
        self.snake.insert(0, head)
        self.total_steps += 1
        grew = False
        if self.settings["survivalMode"]:
            self.score += 1
        else:
            if head in self.foods:
                grew = True
                self.foods.remove(head)
                pts = 10 + self.level_idx * 5
                if self.settings["combo"]:
                    self.combo_count += 1
                    self.combo_until = now + 3000
                    mult = 1 + (self.combo_count // 3) * 0.5
                    pts = round(pts * mult)
                    self.max_combo = max(self.max_combo, self.combo_count)
                self.score += pts
                self.popups.append([head, f"+{pts}", now + 850, GOLD if self.combo_count >= 3 else GREEN])
                while len(self.foods) < (3 if self.settings["multiFood"] else 1):
                    self.add_food()
                if self.settings["bonusFood"] and not self.bonus and random.random() < 0.30:
                    self.spawn_bonus()
                self.path = []
            if self.bonus and head == (self.bonus["x"], self.bonus["y"]):
                grew = True
                bt = self.bonus["type"]
                self.score += bt["pts"]
                self.popups.append([head, f"+{bt['pts']}", now + 850, GOLD])
                self.notifs.append([bt["name"], now + 2200, bt["color"]])
                if bt.get("speed") and self.settings["speedBoost"]:
                    self.cur_speed_mult = 1.6
                    self.speed_boost_until = now + 5000
                self.bonus = None
            if self.bonus and now > self.bonus["expires"]:
                self.bonus = None
        if not grew:
            self.snake.pop()
        self.update_high_score()

    def spawn_bonus(self):
        """Sinh mồi thưởng ngẫu nhiên nếu chế độ bonus được bật."""
        for _ in range(300):
            x, y = random.randrange(self.cols), random.randrange(self.rows)
            if not self.occupied(x, y):
                self.bonus = {"x": x, "y": y, "type": random.choice(BONUS_TYPES), "expires": pygame.time.get_ticks() + 8000, "spawned": pygame.time.get_ticks()}
                return

    def update_high_score(self):
        """Cập nhật điểm cao nhất theo cấp độ."""
        key = ["easy", "medium", "hard"][self.level_idx]
        if self.score > self.high_scores.get(key, 0):
            self.high_scores[key] = self.score
            self.save_config()

    def game_over(self, reason):
        """Kết thúc ván, lưu lịch sử và chuyển sang màn hình Game Over."""
        self.dead = True
        self.game_over_reason = reason
        self.update_high_score()
        self.record_history(reason)

    def export_log(self):
        """Xuất log A* của ván hiện tại ra file TXT."""
        if not self.log_entries:
            return
        fp = ROOT / f"snake_log_{int(time.time())}.txt"
        with fp.open("w", encoding="utf-8") as f:
            f.write("=== SNAKE A* LOG ===\n")
            f.write(f"Cấp độ: {self.cfg['name']} | Người chơi: {self.player_name}\n\n")
            for e in self.log_entries:
                f.write(f"Bước {e['step']}: A* {e['timeMs']:.2f}ms, duyệt {e['nodes']} node, đường đi {e['pathLen']} bước, rắn ({e['headX']},{e['headY']}), mục tiêu ({e['targetX']},{e['targetY']})\n")
            f.write(f"\nĐiểm: {self.score}, Độ dài: {len(self.snake)}, Tổng bước: {self.total_steps}\n")
        self.notifs.append([f"Đã export: {fp.name}", pygame.time.get_ticks()+2500, CYAN])

    # ----- GIAO DIỆN MENU -----
    def draw_menu(self):
        """Vẽ giao diện menu chính và các tùy chọn trước khi chơi."""
        self.screen.fill(BG)
        w, h = self.screen.get_size()
        cx = w // 2
        menu_w = min(480, w - 40)
        x0 = cx - menu_w // 2
        y = 28
        gradient_text(self.screen, "SNAKE A* PATHFINDING", self.font_big, cx, y + 10, GREEN, CYAN, True)
        self.buttons = []

        def card(y, height, label):
            r = pygame.Rect(x0, y, menu_w, height)
            rounded_rect(self.screen, r, (17, 21, 33), 14, (48, 56, 78), 1)
            draw_text(self.screen, label.upper(), self.font_tiny, TX2, x0 + 18, y + 12)
            return r

        y += 42
        r = card(y, 62, "+ Tên người chơi")
        name_rect = pygame.Rect(x0 + 16, y + 30, menu_w - 32, 30)
        rounded_rect(self.screen, name_rect, (31, 34, 45), 8, GREEN if self.name_active else (70,75,92), 1)
        text = self.player_name if self.player_name else "Nhập tên người chơi..."
        if self.name_active and pygame.time.get_ticks() // 430 % 2:
            text += "|"
        draw_text(self.screen, text, self.font_small, TX, name_rect.x + 12, name_rect.y + 8)
        self.buttons.append((name_rect, "name"))
        y += 78

        card_size, gap = 56, 9
        skin_cols = max(5, min(len(SKINS), (menu_w - 32 + gap) // (card_size + gap)))
        skin_rows = math.ceil(len(SKINS) / skin_cols)
        skin_card_h = 34 + skin_rows * card_size + (skin_rows - 1) * gap + 16
        r = card(y, skin_card_h, "* Màu rắn")
        sx, sy = x0 + 16, y + 34
        for i, sk in enumerate(SKINS):
            xx = sx + (i % skin_cols) * (card_size + gap)
            yy = sy + (i // skin_cols) * (card_size + gap)
            rr = pygame.Rect(xx, yy, card_size, card_size)
            rounded_rect(self.screen, rr, (10, 14, 26), 11, TX if i == self.skin_idx else (51,61,85), 2 if i == self.skin_idx else 1)

            preview = pygame.Surface((card_size, card_size), pygame.SRCALPHA)
            colors, glow = sk[1], sk[2]
            pts=[]
            for k in range(16):
                t=k/15
                pts.append((card_size*.20 + t*card_size*.60 + math.sin(t*math.pi*2.2)*card_size*.105,
                            card_size*.50 + math.cos(t*math.pi*1.8)*card_size*.175))
            for k in range(len(pts)-1, -1, -1):
                t=k/max(1,len(pts)-1)
                col=skin_color(colors,t)
                rad = max(2.4, card_size*.066*(1.08-t*.30))
                radial_circle(preview, pts[k][0], pts[k][1], rad,
                              lerp_color((255,255,255), col, .25), col, lerp_color(col,(0,0,0),.45),
                              glow if k==0 else None, 1 if k==0 else 0)

            mask = pygame.Surface((card_size, card_size), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255,255,255,255), (0,0,card_size,card_size), border_radius=11)
            preview.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
            self.screen.blit(preview, rr.topleft)

            if i == self.skin_idx:
                draw_text(self.screen, "✓", self.font_bold, TX, rr.centerx, rr.centery-2, True)
            self.buttons.append((rr, f"skin:{i}"))
        y += skin_card_h + 16

        r = card(y, 104, "x Cấp độ")
        names=[("♧", "Dễ", "15×15\n3 vật cản"), ("▲", "Vừa", "20×20\n8 vật cản"), ("☠", "Khó", "26×26\n16 vật cản")]
        bw=(menu_w-48)//3
        for i,(ico, name, sub) in enumerate(names):
            rr=pygame.Rect(x0+16+i*(bw+8), y+34, bw, 58)
            sel=i==self.level_idx
            rounded_rect(self.screen, rr, (10,35,31) if sel else (31,33,45), 10, GREEN if sel else (55,60,80), 1)
            draw_text(self.screen, ico, self.font_bold, TX, rr.centerx, rr.y+8, True)
            draw_text(self.screen, name, self.font_tiny, GREEN if sel else TX, rr.centerx, rr.y+29, True)
            lines=sub.split('\n')
            draw_text(self.screen, lines[0], self.font_tiny, TX2, rr.centerx, rr.y+42, True)
            draw_text(self.screen, lines[1], self.font_tiny, TX2, rr.centerx, rr.y+52, True)
            self.buttons.append((rr, f"level:{i}"))
        y += 120

        opts=[("showPath","Hiện đường đi","Vẽ đường A* tìm được"), ("showExplored","Hiện node đã duyệt","Open list / Closed list"), ("showGrid","Hiện lưới ô vuông",""),
              ("bonusFood","— Thức ăn thưởng (bonus)","⭐💎⚡ xuất hiện ngẫu nhiên, có giới hạn thời gian"), ("combo","— Combo điểm","Ăn liên tiếp nhanh để nhân điểm"), ("speedBoost","— Tăng tốc tạm thời","Thức ăn ⚡ tăng tốc rắn 5 giây"),
              ("multiFood","— Nhiều mồi (3 mồi)","Xuất hiện 3 mồi, AI chọn mồi an toàn nhất"), ("survivalMode","— Chế độ sinh tồn","Không có mồi, vật cản sinh ra liên tục")]
        r = card(y, min(304, h-y-58), "o Tuỳ chọn hiển thị")
        yy=y+35
        for idx,(key,label,desc) in enumerate(opts):
            if yy+28 > r.bottom-8: break
            row=pygame.Rect(x0+16, yy-2, menu_w-32, 28)
            draw_text(self.screen, label, self.font_tiny, TX, row.x, row.y+3)
            if desc:
                draw_text(self.screen, desc, self.font_tiny, TX2, row.x, row.y+15)
            tr=pygame.Rect(row.right-34, row.y+8, 30, 16)
            draw_toggle(self.screen, tr, self.settings[key])
            self.buttons.append((row, f"toggle:{key}"))
            yy += 31 if idx < 3 else 32
        y = r.bottom + 10

        hist = pygame.Rect(x0, y, menu_w, 36)
        rounded_rect(self.screen, hist, (17, 21, 33), 10, (48, 56, 78), 1)
        draw_text(self.screen, "XEM LỊCH SỬ NGƯỜI CHƠI", self.font_bold, TX, hist.centerx, hist.centery, True)
        self.buttons.append((hist, "history"))
        y += 46

        start = pygame.Rect(x0, y, menu_w, 42)
        grad=pygame.Surface(start.size, pygame.SRCALPHA)
        for xx in range(start.w):
            col=lerp_color(GREEN, CYAN, xx/max(1,start.w-1))
            pygame.draw.line(grad, (*col,255), (xx,0), (xx,start.h))
        mask=pygame.Surface(start.size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255,255,255,255), mask.get_rect(), border_radius=10)
        grad.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
        self.screen.blit(grad,start)
        draw_text(self.screen,"▶ BẮT ĐẦU", self.font_bold, (0,25,13), start.centerx, start.centery, True)
        self.buttons.append((start,"start"))

    # ----- GIAO DIỆN LỊCH SỬ NGƯỜI CHƠI -----
    def draw_history(self):
        """Vẽ giao diện xem lại lịch sử người chơi."""
        self.screen.fill(BG)
        w, h = self.screen.get_size()
        cx = w // 2
        box_w = min(760, w - 40)
        x0 = cx - box_w // 2
        y = 34
        gradient_text(self.screen, "LỊCH SỬ NGƯỜI CHƠI", self.font_big, cx, y, GREEN, CYAN, True)
        self.buttons = []

        panel = pygame.Rect(x0, y + 48, box_w, min(h - 140, 560))
        rounded_rect(self.screen, panel, (17, 21, 33), 14, (48, 56, 78), 1)
        draw_text(self.screen, "10 trận gần nhất", self.font_small, TX2, panel.x + 18, panel.y + 16)

        header_y = panel.y + 46
        cols = [18, 170, 300, 390, 470, 550]
        headers = ["Thời gian", "Người chơi", "Cấp", "Điểm", "Dài", "Lý do"]
        for off, head in zip(cols, headers):
            draw_text(self.screen, head, self.font_tiny, CYAN, panel.x + off, header_y)
        pygame.draw.line(self.screen, (48, 56, 78), (panel.x + 16, header_y + 18), (panel.right - 16, header_y + 18), 1)

        rows = list(reversed(self.history[-10:]))
        if not rows:
            draw_text(self.screen, "Chưa có lịch sử. Hãy chơi một ván để lưu kết quả.", self.font, TX2, panel.centerx, panel.centery, True)
        else:
            ry = header_y + 30
            for e in rows:
                if ry > panel.bottom - 34:
                    break
                pygame.draw.line(self.screen, (28, 34, 50), (panel.x + 16, ry + 24), (panel.right - 16, ry + 24), 1)
                vals = [
                    str(e.get("time", "-")),
                    str(e.get("player", "Player"))[:14],
                    str(e.get("level", "-")),
                    str(e.get("score", 0)),
                    str(e.get("length", 0)),
                    str(e.get("reason", "-"))[:24],
                ]
                colors = [TX, TX, GOLD, GREEN, CYAN, RED]
                for off, val, col in zip(cols, vals, colors):
                    draw_text(self.screen, val, self.font_tiny, col, panel.x + off, ry)
                ry += 34

        back = pygame.Rect(x0, panel.bottom + 14, 160, 38)
        rounded_rect(self.screen, back, (22, 28, 40), 10, (55, 64, 86), 1)
        draw_text(self.screen, "← MENU", self.font_bold, TX, back.centerx, back.centery, True)
        self.buttons.append((back, "menu"))

        clear = pygame.Rect(panel.right - 160, panel.bottom + 14, 160, 38)
        rounded_rect(self.screen, clear, (35, 18, 24), 10, (95, 48, 58), 1)
        draw_text(self.screen, "XÓA LỊCH SỬ", self.font_bold, RED, clear.centerx, clear.centery, True)
        self.buttons.append((clear, "clear_history"))

    def grid_to_px(self, p):
        """Chuyển tọa độ ô lưới sang tọa độ pixel trên màn hình."""
        return self.ox + p[0] * self.cell + self.cell // 2, self.oy + p[1] * self.cell + self.cell // 2

    # ----- GIAO DIỆN MÀN HÌNH CHƠI -----
    def draw_game(self):
        """Vẽ giao diện đang chơi gồm HUD, bàn chơi, panel và overlay."""
        self.screen.fill(BG)
        self.size_grid()
        w, h = self.screen.get_size()
        pygame.draw.rect(self.screen, (5, 8, 15), (0, 0, w, 48))
        pygame.draw.line(self.screen, (37,43,60), (0,47), (w,47))
        stats = [("Điểm", self.score, GREEN), ("Độ dài", len(self.snake), CYAN), ("Node duyệt", self.astar_steps, GOLD), ("Thời gian A*", f"{self.astar_ms:.2f}ms", TX)]
        if self.settings["combo"]:
            stats.append(("Combo", f"x{1+(self.combo_count//3)*0.5:.1f}", GOLD))
        x = 8
        for lab, val, col in stats:
            ww = 58 if lab != "Thời gian A*" else 86
            rounded_rect(self.screen, pygame.Rect(x, 7, ww, 34), (18, 23, 35), 7, (45,52,70), 1)
            draw_text(self.screen, lab.upper(), self.font_tiny, TX2, x + ww//2, 12, True)
            draw_text(self.screen, val, self.font_num, col, x + ww//2, 30, True)
            x += ww + 8
        btns = [("AI: " + ("BẬT" if self.ai else "TẮT"), "ai"), ("Dừng", "pause"), ("Export Log", "log"), ("← Menu", "menu")]
        self.buttons=[]
        bx = w - 8
        for text, act in reversed(btns):
            ww = 80 if act != "log" else 110
            bx -= ww
            r=pygame.Rect(bx, 10, ww, 28)
            if act == "ai" and self.ai:
                rounded_rect(self.screen, r, (12,36,31), 7, (0,100,76), 1)
                col=GREEN
            else:
                rounded_rect(self.screen, r, (18,23,35), 7, (48,56,78), 1)
                col=TX
            draw_text(self.screen, text, self.font_tiny, col, r.centerx, r.centery, True)
            self.buttons.append((r, act)); bx -= 8

        board = pygame.Rect(self.ox, self.oy, self.cols*self.cell, self.rows*self.cell)
        if self.settings["showGrid"]:
            for xx in range(self.cols+1):
                xg=self.ox+xx*self.cell
                pygame.draw.line(self.screen, (18,24,38), (xg,self.oy), (xg,self.oy+self.rows*self.cell), 1)
            for yy in range(self.rows+1):
                yg=self.oy+yy*self.cell
                pygame.draw.line(self.screen, (18,24,38), (self.ox,yg), (self.ox+self.cols*self.cell,yg), 1)
        pygame.draw.rect(self.screen, ORANGE if self.cur_speed_mult>1 else GREEN, board, 1)

        if self.settings["showExplored"]:
            for i,p in enumerate(self.explored):
                col=OPEN if i>len(self.explored)-15 else CLOSED
                a=82 if i>len(self.explored)-15 else 42
                ss=pygame.Surface((self.cell-2,self.cell-2), pygame.SRCALPHA); ss.fill((*col,a))
                self.screen.blit(ss,(self.ox+p[0]*self.cell+1,self.oy+p[1]*self.cell+1))
        if self.settings["showPath"]:
            for pth in self.path:
                ss=pygame.Surface((self.cell-2,self.cell-2), pygame.SRCALPHA); ss.fill((*GREEN,55))
                self.screen.blit(ss,(self.ox+pth[0]*self.cell+1,self.oy+pth[1]*self.cell+1))
            if self.path:
                pts=[self.grid_to_px(self.snake[0])] + [self.grid_to_px(p) for p in self.path]
                for a,b in zip(pts, pts[1:]):
                    ax,ay=a; bx2,by2=b; dist=max(1, math.hypot(bx2-ax, by2-ay)); dash=8
                    n=int(dist//dash)
                    for k in range(0,n,2):
                        t1=k/n if n else 0; t2=min(1,(k+1)/n) if n else 1
                        pygame.draw.line(self.screen, (*GREEN,), (ax+(bx2-ax)*t1, ay+(by2-ay)*t1), (ax+(bx2-ax)*t2, ay+(by2-ay)*t2), 2)
        for o in self.obstacles: self.draw_obstacle((o["x"], o["y"]))
        if self.bonus: self.draw_bonus((self.bonus["x"], self.bonus["y"]), self.bonus["type"])
        for f in self.foods: self.draw_food(f)
        self.draw_snake()
        self.draw_side_panel()
        self.draw_status_bar()
        self.draw_popups_notifs()
        if self.paused:
            self.overlay("⏸ TẠM DỪNG", f"Điểm: {self.score} · Độ dài: {len(self.snake)}", GOLD, [
                ("▶ Tiếp tục", "pause"),
                ("↩ Menu", "menu"),
            ])
        if self.dead:
            self.overlay("💀 GAME OVER", f"{self.game_over_reason}\nĐiểm: {self.score}", RED, [
                ("▶ Chơi lại", "restart"),
                ("📄 Export Log", "log"),
                ("↩ Menu", "menu"),
            ])

    def interp_head_px(self):
        """Tính vị trí nội suy của đầu rắn để chuyển động mượt."""
        now=pygame.time.get_ticks()
        speed=max(40, int(self.cfg["speed"] / self.cur_speed_mult))
        t=clamp((now-self.last_tick)/max(1,speed),0,1)
        a=self.prev_head or self.snake[0]
        b=self.next_head or self.snake[0]
        ax,ay=self.grid_to_px(a); bx,by=self.grid_to_px(b)
        return (ax+(bx-ax)*t, ay+(by-ay)*t)

    def draw_snake(self):
        """Vẽ thân rắn dạng slither với gradient, mắt và glow."""
        colors, glow = SKINS[self.skin_idx][1], SKINS[self.skin_idx][2]
        if not self.snake:
            return

        pts = [self.interp_head_px()] + [self.grid_to_px(p) for p in self.snake[1:]]
        smooth = []
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            steps = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / max(3, self.cell / 5)))
            for k in range(steps):
                t = k / steps
                smooth.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        smooth.append(pts[-1])

        N = len(smooth)
        base = self.cell * 0.33
        for i in range(N - 1, -1, -1):
            t = i / max(1, N - 1)
            taper = 1 if t < .88 else 1 - (t - .88) / .12 * .60
            r = max(2.2, base * taper)
            p = smooth[i]
            col = skin_color(colors, t)
            glow_power = 1 if i % 2 == 0 else 0
            radial_circle(
                self.screen, p[0], p[1], r,
                lerp_color((255, 255, 255), col, .33),
                col,
                lerp_color(col, (0, 0, 0), .50),
                glow if glow_power else None,
                glow_power,
            )

        h = smooth[0]
        n = smooth[min(4, N - 1)]
        ang = math.atan2(h[1] - n[1], h[0] - n[0]) if N > 1 else 0
        hr = self.cell * 0.38
        head_col = skin_color(colors, 0)
        radial_circle(
            self.screen, h[0], h[1], hr,
            lerp_color((255, 255, 255), head_col, .30),
            head_col,
            lerp_color(head_col, (0, 0, 0), .35),
            glow,
            1,
        )

        side_x = math.cos(ang - math.pi / 2)
        side_y = math.sin(ang - math.pi / 2)
        fwd_x = math.cos(ang)
        fwd_y = math.sin(ang)
        er = max(1.7, self.cell * 0.075)
        for ss in (-1, 1):
            ex = h[0] + fwd_x * hr * .22 + side_x * hr * .38 * ss
            ey = h[1] + fwd_y * hr * .22 + side_y * hr * .38 * ss
            pygame.gfxdraw.filled_circle(self.screen, int(ex), int(ey), int(er), (245, 255, 250))
            pygame.gfxdraw.aacircle(self.screen, int(ex), int(ey), int(er), (245, 255, 250))
            pygame.gfxdraw.filled_circle(self.screen, int(ex + fwd_x * er * .28), int(ey + fwd_y * er * .28), max(1, int(er * .45)), (5, 12, 10))

    def draw_food(self, p):
        """Vẽ mồi chính trên bàn chơi."""
        x,y=self.grid_to_px(p)
        pulse=1+math.sin(pygame.time.get_ticks()/180)*.10
        r=self.cell*.25*pulse
        radial_circle(self.screen,x,y,r,(255,248,210),GOLD,(146,102,10),GOLD,2)

    def draw_bonus(self, p, bt):
        """Vẽ mồi thưởng theo loại bonus."""
        x,y=self.grid_to_px(p)
        r=self.cell*.40*(1+math.sin(pygame.time.get_ticks()/150)*.12)
        radial_circle(self.screen,x,y,r,(255,255,255),bt["color"],(20,20,20),bt["color"],5)
        draw_text(self.screen,bt["emoji"],self.font_bold,(10,10,10),x,y-8,True)

    def draw_obstacle(self, p):
        """Vẽ vật cản di động màu đỏ."""
        x,y=self.grid_to_px(p)
        r=self.cell*.31
        radial_circle(self.screen,x,y,r,(120,35,35),(82,12,12),(24,0,0),RED,2)
        pygame.gfxdraw.aacircle(self.screen,int(x),int(y),int(r),(239,68,68))

    # ----- GIAO DIỆN PANEL THỐNG KÊ -----
    def draw_side_panel(self):
        """Vẽ bảng thống kê và chú giải bên phải."""
        w, h = self.screen.get_size()
        if w <= 900:
            return
        x = w - 300
        pygame.draw.rect(self.screen, (15, 20, 31), (x, 48, 300, h-68))
        pygame.draw.line(self.screen, BORDER, (x, 48), (x, h))
        y = 68
        draw_text(self.screen, "THỐNG KÊ", self.font_bold, TX2, x + 18, y); y += 34
        rows = [("Đường đi", len(self.path)), ("Node duyệt", self.astar_steps), ("Thời gian", f"{self.astar_ms:.2f}ms"), ("Tổng bước", self.total_steps), ("Tính lại", self.replans), ("Vật cản", len(self.obstacles)), ("High Score", self.high_scores[["easy","medium","hard"][self.level_idx]])]
        for a, b in rows:
            draw_text(self.screen, a, self.font_small, TX2, x + 18, y)
            draw_text(self.screen, b, self.font_small, TX, x + 210, y)
            y += 25
        y += 20
        draw_text(self.screen, "CHÚ GIẢI", self.font_bold, TX2, x + 18, y); y += 32
        legends = [(OPEN, "Open list"), (CLOSED, "Closed list"), (GREEN, "Đường đi"), (RED, "Vật cản"), (GOLD, "Thức ăn")]
        for col, txt in legends:
            pygame.draw.rect(self.screen, col, (x+20, y+3, 14, 14), border_radius=3)
            draw_text(self.screen, txt, self.font_small, TX2, x+44, y)
            y += 25

    def draw_status_bar(self):
        """Vẽ thanh trạng thái ở dưới cửa sổ game."""
        w,h=self.screen.get_size()
        y=h-20
        pygame.draw.rect(self.screen, (5,8,15), (0,y,w,20))
        pygame.draw.line(self.screen, (37,43,60), (0,y), (w,y))
        if self.settings["survivalMode"]:
            text=f"🛡 Sinh tồn: {self.score} tick · Vật cản: {len(self.obstacles)} · Tốc độ: {max(40,int(self.cfg['speed']/self.cur_speed_mult))}ms"
        elif self.path:
            target = self.current_target or (self.foods[0] if self.foods else (0, 0))
            text=f"A* tìm đường ({target[0]},{target[1]}): {len(self.path)} bước · duyệt {self.astar_steps} node · {self.astar_ms:.2f}ms"
        elif self.ai:
            text="⚠ Không tìm được đường an toàn — rắn đang né va chạm tạm thời"
        else:
            text="Điều khiển thủ công (mũi tên / WASD)"
        draw_text(self.screen, text, self.font_tiny, TX2, 10, y+5)

    def draw_popups_notifs(self):
        """Vẽ điểm cộng nổi và thông báo ngắn trong game."""
        now = pygame.time.get_ticks()
        self.popups = [p for p in self.popups if p[2] > now]
        for cell, txt, until, col in self.popups:
            x, y = self.grid_to_px(cell)
            dy = int((until - now) / 850 * 35)
            draw_text(self.screen, txt, self.font_bold, col, x, y - dy, True)
        self.notifs = [n for n in self.notifs if n[1] > now]
        y = 76
        for msg, until, col in self.notifs[-3:]:
            r = pygame.Rect(self.screen.get_width()//2 - 130, y, 260, 26)
            rounded_rect(self.screen, r, (20, 25, 34), 12, col, 1)
            draw_text(self.screen, msg, self.font_tiny, col, r.centerx, r.centery, True)
            y += 30

    # ----- GIAO DIỆN POPUP PAUSE / GAME OVER -----
    def overlay(self, title, info, color, actions=None):
        """Vẽ màn hình phủ cho Pause hoặc Game Over."""
        w, h = self.screen.get_size()
        dim = pygame.Surface((w, h), pygame.SRCALPHA)
        dim.fill((8, 11, 20, 205))
        self.screen.blit(dim, (0, 0))

        actions = actions or []
        box_h = 245 if actions else 220
        box_w = 430 if len(actions) >= 3 else 360
        r = pygame.Rect(w//2 - box_w//2, h//2 - box_h//2, box_w, box_h)
        rounded_rect(self.screen, r, (14, 20, 32), 18, BORDER, 1)

        draw_text(self.screen, title, self.font_big, color, r.centerx, r.y + 48, True)
        for i, line in enumerate(info.split("\n")):
            draw_text(self.screen, line, self.font, TX, r.centerx, r.y + 94 + i*28, True)

        if actions:
            total_gap = 10 * (len(actions) - 1)
            btn_w = 120 if len(actions) >= 3 else 135
            btn_h = 38
            start_x = r.centerx - (btn_w * len(actions) + total_gap) // 2
            y = r.bottom - 66
            for i, (label, action) in enumerate(actions):
                br = pygame.Rect(start_x + i * (btn_w + 10), y, btn_w, btn_h)
                if action in ("restart", "pause"):
                    grad = pygame.Surface(br.size, pygame.SRCALPHA)
                    for xx in range(br.w):
                        col = lerp_color(GREEN, CYAN, xx / max(1, br.w - 1))
                        pygame.draw.line(grad, (*col, 255), (xx, 0), (xx, br.h))
                    mask = pygame.Surface(br.size, pygame.SRCALPHA)
                    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=10)
                    grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    self.screen.blit(grad, br)
                    txt_col = (0, 25, 13)
                else:
                    rounded_rect(self.screen, br, (22, 28, 40), 10, (55, 64, 86), 1)
                    txt_col = TX
                draw_text(self.screen, label, self.font_small, txt_col, br.centerx, br.centery, True)
                self.buttons.append((br, action))
        else:
            draw_text(self.screen, "Space tiếp tục | Esc menu", self.font_small, TX2, r.centerx, r.bottom - 30, True)

    def handle_action(self, action):
        """Xử lý hành động khi người chơi bấm nút giao diện."""
        if action == "start": self.start_game()
        elif action == "restart": self.start_game()
        elif action == "name": self.name_active = True
        elif action == "history": self.mode = "history"
        elif action.startswith("level:"): self.level_idx = int(action.split(":")[1])
        elif action.startswith("skin:"): self.skin_idx = int(action.split(":")[1])
        elif action.startswith("toggle:"):
            k = action.split(":")[1]
            self.settings[k] = not self.settings[k]
        elif action == "ai": self.ai = not self.ai
        elif action == "pause": self.paused = not self.paused
        elif action == "log": self.export_log()
        elif action == "menu": self.mode = "menu"; self.dead = False; self.paused = False
        elif action == "clear_history":
            self.history = []
            self.save_history()

    def handle_events(self):
        """Xử lý bàn phím, chuột, nhập tên và đóng cửa sổ."""
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.save_config(); return False
            if e.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(e.size, self.display_flags, vsync=1)
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self.name_active = False if self.mode == "menu" else self.name_active
                for rect, action in self.buttons:
                    if rect.collidepoint(e.pos):
                        self.handle_action(action)
                        break
            if e.type == pygame.TEXTINPUT and self.mode == "menu" and self.name_active:
                if len(self.player_name) < 16:
                    self.player_name += e.text
            if e.type == pygame.KEYDOWN:
                if self.mode == "menu" and self.name_active:
                    if e.key == pygame.K_BACKSPACE:
                        self.player_name = self.player_name[:-1]
                    elif e.key == pygame.K_RETURN:
                        self.name_active = False
                if self.mode == "history":
                    if e.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                        self.mode = "menu"
                if self.mode == "game":
                    if e.key in (pygame.K_ESCAPE,): self.mode = "menu"
                    elif e.key == pygame.K_SPACE: self.paused = not self.paused
                    elif e.key == pygame.K_r and self.dead: self.start_game()
                    elif e.key == pygame.K_a: self.ai = not self.ai
                    elif e.key == pygame.K_l: self.export_log()
                    elif e.key == pygame.K_g: self.settings["showGrid"] = not self.settings["showGrid"]
                    elif e.key == pygame.K_p: self.settings["showPath"] = not self.settings["showPath"]
                    elif e.key == pygame.K_e: self.settings["showExplored"] = not self.settings["showExplored"]
                    if e.key in (pygame.K_UP, pygame.K_w): self.ndir = (0, -1)
                    elif e.key in (pygame.K_DOWN, pygame.K_s): self.ndir = (0, 1)
                    elif e.key in (pygame.K_LEFT, pygame.K_a): self.ndir = (-1, 0)
                    elif e.key in (pygame.K_RIGHT, pygame.K_d): self.ndir = (1, 0)
        return True

    def run(self):
        """Chạy vòng lặp chính của chương trình."""
        running = True
        while running:
            running = self.handle_events()
            if self.mode == "menu":
                self.draw_menu()
            elif self.mode == "history":
                self.draw_history()
            else:
                self.tick()
                self.draw_game()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()


if __name__ == "__main__":
    SnakeGame().run()
