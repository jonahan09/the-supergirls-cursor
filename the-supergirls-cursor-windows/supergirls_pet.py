#!/usr/bin/env python3
import sys, math, random, json, ctypes
from ctypes import wintypes
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPixmap, QColor, QPen, QRegion, QCursor
from PyQt6.QtWidgets import (
    QApplication, QWidget, QMenu, QPushButton, QLabel,
    QHBoxLayout, QVBoxLayout, QGridLayout
)

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    ROOT = Path(sys._MEIPASS)
else:
    ROOT = Path(__file__).resolve().parent
SKINS_ROOT = ROOT / "skins"
with open(ROOT / "skins.json", "r", encoding="utf-8") as f:
    SKINS = json.load(f)

AURA_PALETTES = {
    "amarilla": {
        "outer": (255, 220, 40),
        "mid1": (255, 232, 78),
        "mid2": (255, 243, 150),
        "core": (255, 250, 235),
        "line1": (255, 240, 170),
        "line2": (255, 252, 240),
        "spark": (255, 232, 85),
        "spark_core": (255, 249, 215),
        "expr": (255, 238, 120),
    },
    "azul": {
        "outer": (70, 160, 255),
        "mid1": (92, 180, 255),
        "mid2": (145, 210, 255),
        "core": (232, 245, 255),
        "line1": (170, 220, 255),
        "line2": (240, 249, 255),
        "spark": (80, 175, 255),
        "spark_core": (225, 245, 255),
        "expr": (155, 220, 255),
    },
    "rosa": {
        "outer": (255, 90, 190),
        "mid1": (255, 118, 202),
        "mid2": (255, 170, 225),
        "core": (255, 236, 246),
        "line1": (255, 190, 225),
        "line2": (255, 245, 250),
        "spark": (255, 116, 202),
        "spark_core": (255, 235, 245),
        "expr": (255, 185, 225),
    },
    "naranja": {
        "outer": (255, 130, 48),
        "mid1": (255, 155, 62),
        "mid2": (255, 194, 112),
        "core": (255, 242, 225),
        "line1": (255, 204, 150),
        "line2": (255, 248, 238),
        "spark": (255, 148, 72),
        "spark_core": (255, 240, 222),
        "expr": (255, 205, 150),
    },
    "verde": {
        "outer": (90, 225, 100),
        "mid1": (105, 236, 116),
        "mid2": (154, 245, 160),
        "core": (236, 255, 236),
        "line1": (182, 245, 182),
        "line2": (245, 255, 245),
        "spark": (118, 235, 122),
        "spark_core": (236, 255, 236),
        "expr": (180, 245, 180),
    },
}

AURA_INTENSITY = {
    "suave": 0.70,
    "normal": 1.00,
    "intensa": 1.35,
}

FLIGHT_PROFILES = {
    "uniforme": {
        "_default": {"accel": 0.036, "damping": 0.84, "max_speed": 19.0}
    },
    "por_skin": {
        "amarilla": {"accel": 0.040, "damping": 0.84, "max_speed": 20.0},
        "azul":     {"accel": 0.030, "damping": 0.865, "max_speed": 16.5},
        "rosa":     {"accel": 0.034, "damping": 0.85, "max_speed": 17.5},
        "naranja":  {"accel": 0.045, "damping": 0.83, "max_speed": 21.0},
        "verde":    {"accel": 0.032, "damping": 0.855, "max_speed": 17.0},
        "_default": {"accel": 0.036, "damping": 0.84, "max_speed": 19.0},
    }
}

ANIMATION_MODES = {
    "normal": 0.072,
    "fluida": 0.050,
}

class CursorTracker:
    """Obtiene la posición global del cursor sin depender de X11/xdotool."""
    def get_pos(self):
        p = QCursor.pos()
        return p.x(), p.y()

class Pet(QWidget):
    def __init__(self, controller, skin_id="amarilla"):
        super().__init__()
        self.controller = controller
        self.cursor_tracker = CursorTracker()

        self.scale_px = 116
        self.follow_radius = 130
        self.click_hold_radius = 176
        self.following = True

        self.pos_x = 330.0
        self.pos_y = 220.0
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.dragging = False
        self.drag_offset = None

        self.phase = 0.0
        self.pose_name = "idle"
        self.expression = "calm"
        self.near_timer = 0.0
        self.frame_clock = 0.0
        self.frame_index = 0

        self.blinking = False
        self.blink_clock = 0.0
        self.next_blink = random.uniform(1.4, 3.0)

        self.afterimages = []
        self.sparkles = []
        self.skin_id = None
        self.frames = {}

        self.aura_mode = "normal"
        self.animation_mode = "fluida"
        self.flight_mode = "por_skin"

        self.last_mouse_pos = None
        self.mouse_still_time = 0.0
        self.perched = False
        self.perch_window_id = None
        self.perch_x = None
        self.perch_y = None
        self.perch_margin_y = 4

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setFixedSize(280, 280)
        self.move(int(self.pos_x), int(self.pos_y))
        self.setMask(QRegion(90, 72, 90, 110))

        self.load_skin(skin_id)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)

    def load_skin(self, skin_id):
        if skin_id not in SKINS:
            skin_id = "amarilla"
        base = SKINS_ROOT / skin_id / "sprites"
        poses = ["idle","up","up_right","right","down_right","down","down_left","left","up_left"]
        self.frames = {
            pose: [QPixmap(str(base / f"{pose}_{i}.png")) for i in range(4)]
            for pose in poses
        }
        self.skin_id = skin_id
        self.frame_index = 0
        self.update()

    def aura_palette(self):
        return AURA_PALETTES.get(self.skin_id, AURA_PALETTES["amarilla"])

    def motion_profile(self):
        group = FLIGHT_PROFILES.get(self.flight_mode, FLIGHT_PROFILES["uniforme"])
        return group.get(self.skin_id, group.get("_default", {"accel": 0.036, "damping": 0.84, "max_speed": 19.0}))

    def update_blink(self, dt):
        if not self.blinking:
            self.blink_clock += dt
            if self.blink_clock >= self.next_blink:
                self.blinking = True
                self.blink_clock = 0.0
        else:
            self.blink_clock += dt
            if self.blink_clock >= 0.18:
                self.blinking = False
                self.blink_clock = 0.0
                self.next_blink = random.uniform(1.4, 3.0)

    def update_mouse_stillness(self, dt):
        mx, my = self.cursor_tracker.get_pos()
        if self.last_mouse_pos is None:
            self.last_mouse_pos = (mx, my)
            self.mouse_still_time = 0.0
            return

        lx, ly = self.last_mouse_pos
        if abs(mx - lx) <= 2 and abs(my - ly) <= 2:
            self.mouse_still_time += dt
        else:
            self.mouse_still_time = 0.0
            if self.perched:
                self.leave_perch()
        self.last_mouse_pos = (mx, my)

    def get_window_under_cursor(self):
        """Devuelve la ventana de Windows bajo el cursor usando Win32.

        Formato compatible con la versión Linux original:
        (window_id, mouse_x, mouse_y, win_x, win_y, width, height)
        """
        if sys.platform != "win32":
            return None

        try:
            user32 = ctypes.windll.user32
            user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
            user32.GetCursorPos.restype = wintypes.BOOL
            user32.WindowFromPoint.argtypes = [wintypes.POINT]
            user32.WindowFromPoint.restype = wintypes.HWND
            user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
            user32.GetAncestor.restype = wintypes.HWND
            user32.IsWindowVisible.argtypes = [wintypes.HWND]
            user32.IsWindowVisible.restype = wintypes.BOOL
            user32.IsIconic.argtypes = [wintypes.HWND]
            user32.IsIconic.restype = wintypes.BOOL
            user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
            user32.GetWindowRect.restype = wintypes.BOOL
            user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
            user32.GetClassNameW.restype = ctypes.c_int

            pt = wintypes.POINT()
            if not user32.GetCursorPos(ctypes.byref(pt)):
                return None

            hwnd = user32.WindowFromPoint(pt)
            if not hwnd:
                return None

            # Trabajar con la ventana superior, no con un control hijo.
            GA_ROOT = 2
            root_hwnd = user32.GetAncestor(hwnd, GA_ROOT)
            if root_hwnd:
                hwnd = root_hwnd

            # Evitar posarse sobre la propia mascota o el selector.
            own_handles = {int(self.winId())}
            if self.controller is not None and hasattr(self.controller, "selector"):
                try:
                    own_handles.add(int(self.controller.selector.winId()))
                except Exception:
                    pass
            if int(hwnd) in own_handles:
                return None

            if not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):
                return None

            rect = wintypes.RECT()
            if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return None

            ww = int(rect.right - rect.left)
            wh = int(rect.bottom - rect.top)
            if ww <= 0 or wh <= 0:
                return None

            # Ignorar el escritorio y superficies del shell.
            class_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, class_buf, len(class_buf))
            if class_buf.value in {"Progman", "WorkerW", "Shell_TrayWnd"}:
                return None

            # QCursor y Win32 usan las mismas coordenadas en un proceso Qt6 DPI-aware.
            mx, my = self.cursor_tracker.get_pos()
            return (
                str(int(hwnd)),
                int(mx), int(my),
                int(rect.left), int(rect.top),
                ww, wh,
            )
        except Exception:
            return None

    def maybe_perch_on_window(self):
        if self.mouse_still_time < 0.65:
            return False

        info = self.get_window_under_cursor()
        if not info:
            return False

        win_id, mx, my, wx, wy, ww, wh = info
        if ww < 80 or wh < 24:
            return False

        pet_half = self.width() / 2
        target_left = mx - pet_half
        min_left = wx - self.width() * 0.18
        max_left = wx + ww - self.width() * 0.82
        target_left = max(min_left, min(max_left, target_left))
        target_top = wy - self.height() * 0.56 + self.perch_margin_y

        self.perched = True
        self.perch_window_id = win_id
        self.perch_x = float(target_left)
        self.perch_y = float(target_top)

        self.pos_x += (self.perch_x - self.pos_x) * 0.34
        self.pos_y += (self.perch_y - self.pos_y) * 0.34
        self.vel_x *= 0.55
        self.vel_y *= 0.55
        return True

    def leave_perch(self):
        self.perched = False
        self.perch_window_id = None
        self.perch_x = None
        self.perch_y = None

    def follow_cursor(self, dt):
        if self.maybe_perch_on_window():
            self.near_timer += dt
            self.move(int(self.pos_x), int(self.pos_y))
            return

        self.perched = False

        mx, my = self.cursor_tracker.get_pos()
        cx = self.pos_x + self.width()/2
        cy = self.pos_y + self.height()/2
        dx, dy = mx-cx, my-cy
        dist = math.hypot(dx, dy)
        radius = self.click_hold_radius if QApplication.mouseButtons() else self.follow_radius

        profile = self.motion_profile()

        if dist > radius:
            ux, uy = dx/dist, dy/dist
            tx = mx - ux*radius - self.width()/2
            ty = my - uy*radius - self.height()/2

            ax = (tx-self.pos_x) * profile["accel"]
            ay = (ty-self.pos_y) * profile["accel"]
            self.vel_x = (self.vel_x + ax) * profile["damping"]
            self.vel_y = (self.vel_y + ay) * profile["damping"]

            speed = math.hypot(self.vel_x, self.vel_y)
            if speed > profile["max_speed"]:
                s = profile["max_speed"] / speed
                self.vel_x *= s
                self.vel_y *= s

            self.pos_x += self.vel_x
            self.pos_y += self.vel_y
            self.near_timer = 0.0

            if speed > 1.8 and (not self.afterimages or self.afterimages[-1]["life"] < 0.78):
                self.afterimages.append({
                    "x": cx, "y": cy, "pose": self.pose_name,
                    "frame": self.frame_index, "life": 1.0
                })

            if random.random() < 0.60:
                self.sparkles.append({
                    "x": cx-ux*14, "y": cy-uy*14,
                    "vx": -ux*random.uniform(0.8, 1.9) + random.uniform(-0.4, 0.4),
                    "vy": -uy*random.uniform(0.8, 1.9) + random.uniform(-0.4, 0.4),
                    "life": 1.0, "size": random.uniform(1.8, 4.8)
                })
        else:
            self.vel_x *= 0.78
            self.vel_y *= 0.78
            self.pos_x += self.vel_x
            self.pos_y += self.vel_y
            self.near_timer += dt

        self.move(int(self.pos_x), int(self.pos_y))

    def update_pose(self, old_x, old_y):
        if self.perched or self.mouse_still_time > 0.65:
            self.pose_name = "idle"
            return

        dx = self.pos_x-old_x
        dy = self.pos_y-old_y
        speed = math.hypot(dx, dy)

        if speed < 0.35:
            self.pose_name = "idle"
            return

        angle = math.degrees(math.atan2(-dy, dx)) % 360
        if 67.5 <= angle < 112.5:
            self.pose_name = "up"
        elif 22.5 <= angle < 67.5:
            self.pose_name = "up_right"
        elif 112.5 <= angle < 157.5:
            self.pose_name = "up_left"
        elif 247.5 <= angle < 292.5:
            self.pose_name = "down"
        elif 292.5 <= angle < 337.5:
            self.pose_name = "down_right"
        elif 202.5 <= angle < 247.5:
            self.pose_name = "down_left"
        elif angle < 22.5 or angle >= 337.5:
            self.pose_name = "right"
        else:
            self.pose_name = "left"

    def update_expression(self):
        speed = math.hypot(self.vel_x, self.vel_y)
        if self.perched:
            self.expression = "happy"
        elif self.pose_name == "idle":
            self.expression = "happy" if self.near_timer > 1 else "calm"
        else:
            self.expression = "sparkle" if speed > 10 else ("determined" if speed > 4 else "happy")

    def update_frame_clock(self, dt):
        rate = ANIMATION_MODES.get(self.animation_mode, 0.05)
        if self.pose_name == "idle":
            rate *= 2.2
        self.frame_clock += dt
        if self.frame_clock >= rate:
            self.frame_clock = 0
            self.frame_index = (self.frame_index + 1) % 4

    def update_particles(self, dt):
        for p in self.sparkles:
            p["x"] += p["vx"] * 4.2
            p["y"] += p["vy"] * 4.2
            p["life"] -= dt * 2.3
        self.sparkles = [p for p in self.sparkles if p["life"] > 0]

        for a in self.afterimages:
            a["life"] -= dt * 2.0
        self.afterimages = [a for a in self.afterimages if a["life"] > 0]

    def current_pixmap(self):
        return self.frames[self.pose_name][self.frame_index]

    def blink_amount(self):
        if not self.blinking:
            return 0.0
        return math.sin(math.pi * min(1.0, self.blink_clock / 0.18))

    def tick(self):
        dt = 0.016
        self.phase += 0.12
        self.update_blink(dt)
        self.update_mouse_stillness(dt)

        old_x, old_y = self.pos_x, self.pos_y
        if self.following and not self.dragging:
            self.follow_cursor(dt)

        self.update_pose(old_x, old_y)
        self.update_expression()
        self.update_frame_clock(dt)
        self.update_particles(dt)
        self.update()

    def paintEvent(self, event):
        pm = self.current_pixmap()
        if pm.isNull():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)

        speed = math.hypot(self.vel_x, self.vel_y)
        moving = speed > 0.45 and self.following and not self.dragging and not self.perched

        cx = self.width()/2
        base_bob = 0.3 if self.perched else (0.8 if moving else 1.8)
        cy = self.height()/2 + math.sin(self.phase) * base_bob

        self.draw_afterimages(painter)
        if moving:
            self.draw_game_aura(painter, cx, cy)
        self.draw_sparkles(painter)

        if self.perched:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255, 34))
            painter.drawRect(int(cx - 28), int(cy + 44), 56, 2)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 26))
        painter.drawEllipse(QRectF(cx - 18, cy + 44, 36, 8))

        scaled = pm.scaled(
            self.scale_px,
            int(self.scale_px * pm.height() / max(1, pm.width())),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation
        )

        painter.save()
        painter.translate(cx, cy)

        if moving:
            # Más suave: menos deformación y un pad de máscara más grande
            tilt = max(-4.0, min(4.0, self.vel_x * 0.12))
            stretch = min(0.028, speed / 260.0)
            painter.rotate(tilt)
            painter.scale(1 + stretch, 1 - stretch * 0.10)
            mask_pad = 26
        elif self.perched:
            settle = 1.0 + math.sin(self.phase * 0.75) * 0.004
            painter.scale(settle, 1.0)
            mask_pad = 16
        else:
            breathe = 1.0 + math.sin(self.phase * 0.80) * 0.010
            painter.scale(breathe, breathe)
            mask_pad = 14

        painter.drawPixmap(-scaled.width()//2, -scaled.height()//2, scaled)
        self.draw_expression_overlay(painter, scaled)

        blink = self.blink_amount()
        if blink > 0.03:
            self.draw_blink(painter, scaled, blink)

        painter.restore()

        mx = int(cx - scaled.width()/2 - mask_pad)
        my = int(cy - scaled.height()/2 - mask_pad)
        mw = int(scaled.width() + mask_pad*2)
        mh = int(scaled.height() + mask_pad*2)
        mx = max(0, mx)
        my = max(0, my)
        mw = max(1, min(self.width() - mx, mw))
        mh = max(1, min(self.height() - my, mh))
        self.setMask(QRegion(mx, my, mw, mh))

    def draw_afterimages(self, painter):
        pal = self.aura_palette()
        for a in self.afterimages:
            pm = self.frames.get(a["pose"], self.frames["up"])[a["frame"]]
            pm = pm.scaled(
                self.scale_px,
                int(self.scale_px * pm.height() / max(1, pm.width())),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation
            )
            painter.save()
            painter.setOpacity(0.12 * a["life"])
            x = a["x"] - (self.pos_x + self.width()/2) + self.width()/2
            y = a["y"] - (self.pos_y + self.height()/2) + self.height()/2
            painter.drawPixmap(int(x - pm.width()/2), int(y - pm.height()/2), pm)
            # colored ghost tint
            rr, gg, bb = pal["outer"]
            painter.fillRect(
                int(x - pm.width()/2), int(y - pm.height()/2), pm.width(), pm.height(),
                QColor(rr, gg, bb, int(28 * a["life"]))
            )
            painter.restore()

    def draw_sparkles(self, painter):
        pal = self.aura_palette()
        sr, sg, sb = pal["spark"]
        cr, cg, cb = pal["spark_core"]
        painter.setPen(Qt.PenStyle.NoPen)
        for p in self.sparkles:
            sx = p["x"] - (self.pos_x + self.width()/2) + self.width()/2
            sy = p["y"] - (self.pos_y + self.height()/2) + self.height()/2
            alpha = int(180 * p["life"])
            painter.setBrush(QColor(sr, sg, sb, alpha))
            size = max(1, int(p["size"]))
            painter.drawRect(int(sx - size/2), int(sy - size/2), size, size)
            painter.setBrush(QColor(cr, cg, cb, min(255, alpha + 40)))
            painter.drawRect(int(sx - size/4), int(sy - size/4), max(1, size//2), max(1, size//2))

    def draw_game_aura(self, painter, cx, cy):
        mag = math.hypot(self.vel_x, self.vel_y)
        if mag < 0.05:
            return

        pal = self.aura_palette()
        mult = AURA_INTENSITY.get(self.aura_mode, 1.0)
        ux, uy = -self.vel_x/mag, -self.vel_y/mag
        px, py = -uy, ux
        length = (56 + min(96, mag * 8.6)) * (0.92 + 0.14 * mult)

        def rgba(rgb, alpha):
            return QColor(rgb[0], rgb[1], rgb[2], max(0, min(255, int(alpha))))

        def blocks(steps, width, rgb, alpha, jitter):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(rgba(rgb, alpha))
            for i in range(steps):
                t = i / max(1, steps - 1)
                bx = cx + ux * (8 + t * length)
                by = cy + uy * (8 + t * length)
                taper = max(2, int(width * (1 - t * 0.70) * mult))
                jx = int(round(math.sin(i*0.7 + self.phase) * jitter))
                jy = int(round(math.cos(i*0.6 + self.phase) * jitter))
                painter.drawRect(
                    int(bx + px * (-taper/2) + jx),
                    int(by + py * (-taper/2) + jy),
                    taper, taper
                )

        blocks(15, 18, pal["outer"], 42 * mult, 1.0)
        blocks(14, 13, pal["mid1"], 96 * mult, 0.7)
        blocks(13, 8, pal["mid2"], 170 * mult, 0.4)
        blocks(12, 4, pal["core"], 220 * mult, 0.2)

        for width, rgb, alpha in [
            (6, pal["line1"], 170 * mult),
            (3, pal["line2"], 235 * mult),
        ]:
            pen = QPen(rgba(rgb, alpha))
            pen.setWidth(max(1, int(width * mult)))
            painter.setPen(pen)
            painter.drawLine(
                QPointF(cx + ux*6, cy + uy*6),
                QPointF(cx + ux*(length*0.92), cy + uy*(length*0.92))
            )

    def draw_expression_overlay(self, painter, scaled):
        w, h = scaled.width(), scaled.height()
        eye_y = -h * (0.16 if self.pose_name == "idle" else 0.12)

        if self.expression == "happy":
            pen = QPen(QColor(255, 145, 170, 140))
            pen.setWidthF(2.8)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawPoint(QPointF(-w*0.18, h*0.02))
            painter.drawPoint(QPointF(w*0.18, h*0.02))

        elif self.expression == "determined":
            pen = QPen(QColor(22, 22, 22, 180))
            pen.setWidthF(2.2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(QPointF(-w*0.24, eye_y-4), QPointF(-w*0.12, eye_y-7))
            painter.drawLine(QPointF(w*0.12, eye_y-7), QPointF(w*0.24, eye_y-4))

        elif self.expression == "sparkle":
            rr, gg, bb = self.aura_palette()["expr"]
            pen = QPen(QColor(rr, gg, bb, 240))
            pen.setWidthF(1.5)
            painter.setPen(pen)
            for sx, sy in [(-w*0.18, eye_y-5), (w*0.18, eye_y-7)]:
                painter.drawLine(QPointF(sx-4, sy), QPointF(sx+4, sy))
                painter.drawLine(QPointF(sx, sy-4), QPointF(sx, sy+4))

    def draw_blink(self, painter, scaled, amount):
        w, h = scaled.width(), scaled.height()
        if self.pose_name == "idle":
            y = -h*0.15; lx = -w*0.18; rx = w*0.18; length = w*0.13
        else:
            y = -h*0.11; lx = -w*0.12; rx = w*0.20; length = w*0.12

        pen = QPen(QColor(18, 18, 18, int(255*amount)))
        pen.setWidthF(max(2.6, 5.2*amount))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(QPointF(lx-length/2, y), QPointF(lx+length/2, y))
        painter.drawLine(QPointF(rx-length/2, y), QPointF(rx+length/2, y))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.leave_perch()
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self.dragging and self.drag_offset is not None:
            p = event.globalPosition().toPoint() - self.drag_offset
            self.pos_x = p.x()
            self.pos_y = p.y()
            self.move(p)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False

    def show_menu(self, pos):
        menu = QMenu(self)

        follow = menu.addAction("✓ Seguir cursor" if self.following else "Seguir cursor")
        follow.triggered.connect(self.toggle_follow)

        perched_info = menu.addAction("Posarse en ventanas: activado")
        perched_info.setEnabled(False)

        skin_menu = menu.addMenu("Cambiar skin")
        for skin_id, data in SKINS.items():
            act = skin_menu.addAction(("✓ " if skin_id == self.skin_id else "") + data["label"])
            act.triggered.connect(lambda checked=False, sid=skin_id: self.load_skin(sid))

        menu.addSeparator()

        aura_menu = menu.addMenu("Aura")
        for mode, label in [("suave", "Suave"), ("normal", "Normal"), ("intensa", "Intensa")]:
            act = aura_menu.addAction(("✓ " if self.aura_mode == mode else "") + label)
            act.triggered.connect(lambda checked=False, m=mode: self.set_aura_mode(m))

        anim_menu = menu.addMenu("Animación")
        for mode, label in [("normal", "Normal"), ("fluida", "Fluida")]:
            act = anim_menu.addAction(("✓ " if self.animation_mode == mode else "") + label)
            act.triggered.connect(lambda checked=False, m=mode: self.set_animation_mode(m))

        flight_menu = menu.addMenu("Vuelo")
        for mode, label in [("uniforme", "Uniforme"), ("por_skin", "Único por chica")]:
            act = flight_menu.addAction(("✓ " if self.flight_mode == mode else "") + label)
            act.triggered.connect(lambda checked=False, m=mode: self.set_flight_mode(m))

        menu.addSeparator()

        selector = menu.addAction("Abrir selector")
        selector.triggered.connect(self.controller.show_selector)

        size_menu = menu.addMenu("Tamaño")
        bigger = size_menu.addAction("+ Más grande")
        bigger.triggered.connect(lambda: self.change_size(8))
        smaller = size_menu.addAction("− Más pequeña")
        smaller.triggered.connect(lambda: self.change_size(-8))
        reset_size = size_menu.addAction("Restablecer tamaño")
        reset_size.triggered.connect(self.reset_size)

        faster = menu.addAction("Más rápida")
        faster.triggered.connect(lambda: self.change_follow(-10))
        slower = menu.addAction("Más lenta")
        slower.triggered.connect(lambda: self.change_follow(10))

        menu.addSeparator()
        close = menu.addAction("Cerrar")
        close.triggered.connect(QApplication.quit)

        menu.exec(pos)

    def toggle_follow(self):
        self.following = not self.following
        if not self.following:
            self.leave_perch()

    def change_follow(self, delta):
        self.follow_radius = max(90, min(190, self.follow_radius + delta))
        self.click_hold_radius = self.follow_radius + 46

    def change_size(self, delta):
        self.scale_px = max(64, min(220, self.scale_px + delta))
        self.update()
        if self.controller is not None and hasattr(self.controller, "selector"):
            self.controller.selector.sync_from_pet()

    def reset_size(self):
        self.scale_px = 116
        self.update()
        if self.controller is not None and hasattr(self.controller, "selector"):
            self.controller.selector.sync_from_pet()

    def set_aura_mode(self, mode):
        self.aura_mode = mode
        self.update()
        if self.controller is not None and hasattr(self.controller, "selector"):
            self.controller.selector.sync_from_pet()

    def set_animation_mode(self, mode):
        self.animation_mode = mode
        if self.controller is not None and hasattr(self.controller, "selector"):
            self.controller.selector.sync_from_pet()

    def set_flight_mode(self, mode):
        self.flight_mode = mode
        if self.controller is not None and hasattr(self.controller, "selector"):
            self.controller.selector.sync_from_pet()

class SkinSelector(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("SuperGirls Pet v11 — Windows — 5 skins")
        self.setFixedSize(900, 360)

        main = QVBoxLayout(self)

        title = QLabel("Elige una chica — 5 skins disponibles")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        main.addWidget(title)

        grid = QGridLayout()
        ordered_ids = ["amarilla", "rosa", "naranja", "azul", "verde"]
        for col, skin_id in enumerate(ordered_ids):
            if skin_id not in SKINS:
                continue
            data = SKINS[skin_id]

            preview_label = QLabel()
            preview = QPixmap(str(SKINS_ROOT / skin_id / "preview.png"))
            preview_label.setPixmap(preview.scaled(
                105, 105,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation
            ))
            preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            button = QPushButton(data["label"])
            button.setMinimumWidth(125)
            button.setMinimumHeight(32)
            button.clicked.connect(lambda checked=False, sid=skin_id: self.choose(sid))

            grid.addWidget(preview_label, 0, col)
            grid.addWidget(button, 1, col)

        main.addLayout(grid)

        size_row = QHBoxLayout()
        size_row.addStretch()
        size_title = QLabel("Tamaño:")
        size_title.setStyleSheet("font-weight: 600;")
        size_row.addWidget(size_title)

        self.smaller_btn = QPushButton("− Más pequeña")
        self.smaller_btn.setMinimumWidth(130)
        self.smaller_btn.clicked.connect(lambda: self.change_size(-8))
        size_row.addWidget(self.smaller_btn)

        self.size_label = QLabel("116 px")
        self.size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.size_label.setMinimumWidth(70)
        self.size_label.setStyleSheet("font-weight: 600;")
        size_row.addWidget(self.size_label)

        self.bigger_btn = QPushButton("+ Más grande")
        self.bigger_btn.setMinimumWidth(130)
        self.bigger_btn.clicked.connect(lambda: self.change_size(8))
        size_row.addWidget(self.bigger_btn)
        size_row.addStretch()
        main.addLayout(size_row)

        options = QVBoxLayout()

        aura_row = QHBoxLayout()
        aura_row.addStretch()
        aura_row.addWidget(QLabel("Aura:"))
        self.aura_soft = QPushButton("Suave")
        self.aura_soft.clicked.connect(lambda: self.set_aura("suave"))
        aura_row.addWidget(self.aura_soft)
        self.aura_normal = QPushButton("Normal")
        self.aura_normal.clicked.connect(lambda: self.set_aura("normal"))
        aura_row.addWidget(self.aura_normal)
        self.aura_intense = QPushButton("Intensa")
        self.aura_intense.clicked.connect(lambda: self.set_aura("intensa"))
        aura_row.addWidget(self.aura_intense)
        aura_row.addStretch()
        options.addLayout(aura_row)

        anim_row = QHBoxLayout()
        anim_row.addStretch()
        anim_row.addWidget(QLabel("Animación:"))
        self.anim_normal = QPushButton("Normal")
        self.anim_normal.clicked.connect(lambda: self.set_anim("normal"))
        anim_row.addWidget(self.anim_normal)
        self.anim_fluid = QPushButton("Fluida")
        self.anim_fluid.clicked.connect(lambda: self.set_anim("fluida"))
        anim_row.addWidget(self.anim_fluid)
        anim_row.addStretch()
        options.addLayout(anim_row)

        flight_row = QHBoxLayout()
        flight_row.addStretch()
        flight_row.addWidget(QLabel("Vuelo:"))
        self.flight_uniform = QPushButton("Uniforme")
        self.flight_uniform.clicked.connect(lambda: self.set_flight("uniforme"))
        flight_row.addWidget(self.flight_uniform)
        self.flight_skin = QPushButton("Único por chica")
        self.flight_skin.clicked.connect(lambda: self.set_flight("por_skin"))
        flight_row.addWidget(self.flight_skin)
        flight_row.addStretch()
        options.addLayout(flight_row)

        main.addLayout(options)

        self.status = QLabel("Opciones añadidas: aura, animación y vuelo.")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(self.status)

        self.sync_from_pet()

    def ensure_pet(self):
        if self.controller.pet is None:
            self.controller.choose_skin("amarilla")

    def choose(self, skin_id):
        self.controller.choose_skin(skin_id)
        self.sync_from_pet()
        self.hide()

    def change_size(self, delta):
        self.ensure_pet()
        self.controller.pet.change_size(delta)
        self.sync_from_pet()

    def set_aura(self, mode):
        self.ensure_pet()
        self.controller.pet.set_aura_mode(mode)
        self.sync_from_pet()

    def set_anim(self, mode):
        self.ensure_pet()
        self.controller.pet.set_animation_mode(mode)
        self.sync_from_pet()

    def set_flight(self, mode):
        self.ensure_pet()
        self.controller.pet.set_flight_mode(mode)
        self.sync_from_pet()

    def sync_from_pet(self):
        if self.controller.pet is None:
            self.size_label.setText("116 px")
            self.status.setText("Opciones: Aura / Animación / Vuelo")
            return

        pet = self.controller.pet
        self.size_label.setText(f"{pet.scale_px} px")
        self.status.setText(
            f"Aura: {pet.aura_mode} | Animación: {pet.animation_mode} | Vuelo: {pet.flight_mode}"
        )

class Controller:
    def __init__(self):
        self.pet = None
        self.selector = SkinSelector(self)
        self.selector.show()

    def choose_skin(self, skin_id):
        if self.pet is None:
            self.pet = Pet(self, skin_id)
            self.pet.show()
        else:
            self.pet.load_skin(skin_id)
            self.pet.show()
            self.pet.raise_()
        self.selector.sync_from_pet()

    def show_selector(self):
        self.selector.sync_from_pet()
        self.selector.show()
        self.selector.raise_()
        self.selector.activateWindow()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("SuperGirls Pet v11 Windows")
    controller = Controller()
    sys.exit(app.exec())
