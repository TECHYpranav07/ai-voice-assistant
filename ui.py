import sys
import threading
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QFont, QColor, QPalette, QPainter, QPen, QBrush, QLinearGradient, QFontDatabase

# ─── Import your existing modules ───────────────────────────────────────────
from stt import listen
from tts import speak
from llm import ask_llm
from utils import handle_command
from wake_words import listen_for_wake_word


# ─── Worker thread: runs the assistant loop ──────────────────────────────────
class AssistantWorker(QThread):
    status_changed   = pyqtSignal(str)   # "idle" | "wake" | "listening" | "thinking" | "speaking"
    transcript_ready = pyqtSignal(str, str)  # (role, text)  role = "user" | "jarvis"

    def __init__(self):
        super().__init__()
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        self.status_changed.emit("wake")
        self.transcript_ready.emit("system", "Say  \"Hey Jarvis\"  to begin…")

        while self._running:
            # ── Wait for wake word ──────────────────────────────────────────
            self.status_changed.emit("wake")
            if not listen_for_wake_word():
                continue

            self.status_changed.emit("listening")
            self.transcript_ready.emit("jarvis", "I'm listening…")

            # ── Capture command ─────────────────────────────────────────────
            user_input = listen()
            if not user_input:
                self.status_changed.emit("wake")
                continue

            self.transcript_ready.emit("user", user_input)

            if "exit" in user_input or "quit" in user_input:
                self.status_changed.emit("idle")
                self.transcript_ready.emit("jarvis", "Goodbye!")
                speak("Goodbye!")
                self._running = False
                break

            # ── Handle command or ask LLM ───────────────────────────────────
            self.status_changed.emit("thinking")
            cmd_response = handle_command(user_input)

            if cmd_response:
                response = cmd_response
            else:
                response = ask_llm("Answer shortly: " + user_input)

            self.transcript_ready.emit("jarvis", response)
            self.status_changed.emit("speaking")
            speak(response)

        self.status_changed.emit("idle")


# ─── Animated orb widget ─────────────────────────────────────────────────────
class OrbWidget(QWidget):
    """A pulsing circle that changes colour with assistant state."""

    STATE_COLORS = {
        "idle":      ("#1a1a2e", "#16213e"),
        "wake":      ("#0f3460", "#533483"),
        "listening": ("#00b4d8", "#0077b6"),
        "thinking":  ("#f77f00", "#d62828"),
        "speaking":  ("#06d6a0", "#028090"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 180)
        self._state   = "idle"
        self._radius  = 70
        self._pulse   = 0.0
        self._dir     = 1

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(30)

    def set_state(self, state: str):
        self._state = state
        self.update()

    def _animate(self):
        speed = {"idle": 0.3, "wake": 0.5, "listening": 1.5,
                 "thinking": 2.0, "speaking": 1.2}.get(self._state, 0.5)
        self._pulse += speed * self._dir
        if self._pulse >= 12 or self._pulse <= 0:
            self._dir *= -1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        c1, c2 = self.STATE_COLORS.get(self._state, ("#1a1a2e", "#16213e"))
        cx, cy = self.width() // 2, self.height() // 2
        r       = int(self._radius + self._pulse)

        # Glow ring
        glow_pen = QPen(QColor(c2), 3)
        glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(glow_pen)
        for i in range(3, 0, -1):
            alpha = int(60 / i)
            c = QColor(c2)
            c.setAlpha(alpha)
            painter.setPen(QPen(c, i * 4))
            painter.drawEllipse(cx - r - i * 6, cy - r - i * 6,
                                (r + i * 6) * 2, (r + i * 6) * 2)

        # Gradient fill
        grad = QLinearGradient(cx - r, cy - r, cx + r, cy + r)
        grad.setColorAt(0, QColor(c1))
        grad.setColorAt(1, QColor(c2))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        # Inner highlight
        hi = QColor(255, 255, 255, 25)
        painter.setBrush(QBrush(hi))
        painter.drawEllipse(cx - r // 2, cy - r // 2, r, r // 2)


# ─── Transcript bubble ────────────────────────────────────────────────────────
class BubbleWidget(QFrame):
    def __init__(self, role: str, text: str, parent=None):
        super().__init__(parent)
        self.setObjectName("bubble")

        is_user = role == "user"
        is_sys  = role == "system"

        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setFont(QFont("Courier New", 11))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        if is_sys:
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #555577; font-style: italic;")
            layout.addWidget(lbl)
        elif is_user:
            layout.addStretch()
            lbl.setStyleSheet(
                "background: #0f3460; color: #e0e0ff; border-radius: 12px;"
                "padding: 8px 14px;"
            )
            layout.addWidget(lbl)
        else:  # jarvis
            lbl.setStyleSheet(
                "background: #1a1a2e; color: #00b4d8; border-radius: 12px;"
                "padding: 8px 14px; border: 1px solid #0f3460;"
            )
            layout.addWidget(lbl)
            layout.addStretch()


# ─── Main window ─────────────────────────────────────────────────────────────
class JarvisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S")
        self.setMinimumSize(520, 720)
        self._worker = None
        self._build_ui()
        self._apply_styles()

    # ── Build UI ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(64)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(20, 0, 20, 0)
        title = QLabel("J·A·R·V·I·S")
        title.setFont(QFont("Courier New", 18, QFont.Weight.Bold))
        title.setObjectName("title")
        subtitle = QLabel("Voice Assistant")
        subtitle.setObjectName("subtitle")
        subtitle.setFont(QFont("Courier New", 10))
        h_lay.addWidget(title)
        h_lay.addStretch()
        h_lay.addWidget(subtitle)

        # ── Orb area ──────────────────────────────────────────────────────────
        orb_area = QWidget()
        orb_area.setObjectName("orbArea")
        orb_lay = QVBoxLayout(orb_area)
        orb_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        orb_lay.setContentsMargins(0, 24, 0, 8)
        self._orb = OrbWidget()
        orb_lay.addWidget(self._orb, alignment=Qt.AlignmentFlag.AlignCenter)

        self._status_lbl = QLabel("OFFLINE")
        self._status_lbl.setObjectName("statusLbl")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_lbl.setFont(QFont("Courier New", 11, QFont.Weight.Bold))
        orb_lay.addWidget(self._status_lbl)

        # ── Transcript ────────────────────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setObjectName("transcript")
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._transcript_container = QWidget()
        self._transcript_layout    = QVBoxLayout(self._transcript_container)
        self._transcript_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._transcript_layout.setSpacing(6)
        self._transcript_layout.setContentsMargins(12, 12, 12, 12)
        self._scroll.setWidget(self._transcript_container)

        # ── Controls ──────────────────────────────────────────────────────────
        ctrl = QWidget()
        ctrl.setObjectName("controls")
        ctrl.setFixedHeight(80)
        c_lay = QHBoxLayout(ctrl)
        c_lay.setContentsMargins(20, 0, 20, 0)
        c_lay.setSpacing(14)

        self._btn_start = QPushButton("▶  START")
        self._btn_stop  = QPushButton("■  STOP")
        self._btn_clear = QPushButton("✕  CLEAR")

        for btn in (self._btn_start, self._btn_stop, self._btn_clear):
            btn.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
            btn.setFixedHeight(42)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self._btn_stop.setEnabled(False)
        self._btn_start.setObjectName("btnStart")
        self._btn_stop.setObjectName("btnStop")
        self._btn_clear.setObjectName("btnClear")

        c_lay.addWidget(self._btn_start)
        c_lay.addWidget(self._btn_stop)
        c_lay.addWidget(self._btn_clear)

        # ── Assemble ──────────────────────────────────────────────────────────
        root_layout.addWidget(header)
        root_layout.addWidget(orb_area)
        root_layout.addWidget(self._scroll, stretch=1)
        root_layout.addWidget(ctrl)

        # ── Connect ───────────────────────────────────────────────────────────
        self._btn_start.clicked.connect(self._start)
        self._btn_stop.clicked.connect(self._stop)
        self._btn_clear.clicked.connect(self._clear_transcript)

    # ── Styles ────────────────────────────────────────────────────────────────
    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: #0d0d1a;
                color: #c8c8e8;
            }
            #header {
                background: #0a0a14;
                border-bottom: 1px solid #1a1a3a;
            }
            #title   { color: #00b4d8; letter-spacing: 4px; }
            #subtitle{ color: #444466; }
            #orbArea { background: #0d0d1a; }
            #statusLbl { color: #444466; letter-spacing: 3px; margin-top: 6px; }
            #transcript {
                background: #0a0a14;
                border: none;
                border-top: 1px solid #1a1a3a;
                border-bottom: 1px solid #1a1a3a;
            }
            #transcript QScrollBar:vertical {
                background: #0d0d1a; width: 6px; border: none;
            }
            #transcript QScrollBar::handle:vertical {
                background: #1a1a3a; border-radius: 3px;
            }
            #controls { background: #0a0a14; }
            #btnStart {
                background: #0f3460; color: #00b4d8;
                border: 1px solid #00b4d8; border-radius: 8px;
            }
            #btnStart:hover  { background: #00b4d8; color: #0a0a14; }
            #btnStart:disabled { background: #0a0a14; color: #333355; border-color: #333355; }
            #btnStop {
                background: #2a0a14; color: #d62828;
                border: 1px solid #d62828; border-radius: 8px;
            }
            #btnStop:hover   { background: #d62828; color: #0a0a14; }
            #btnStop:disabled{ background: #0a0a14; color: #333355; border-color: #333355; }
            #btnClear {
                background: #1a1a2e; color: #555577;
                border: 1px solid #333355; border-radius: 8px;
            }
            #btnClear:hover  { background: #333355; color: #c8c8e8; }
        """)

    # ── Slots ─────────────────────────────────────────────────────────────────
    def _start(self):
        self._btn_start.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._status_lbl.setText("WAITING FOR WAKE WORD")

        self._worker = AssistantWorker()
        self._worker.status_changed.connect(self._on_status)
        self._worker.transcript_ready.connect(self._on_transcript)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _stop(self):
        if self._worker:
            self._worker.stop()
        self._btn_stop.setEnabled(False)

    def _clear_transcript(self):
        while self._transcript_layout.count():
            item = self._transcript_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_status(self, state: str):
        labels = {
            "idle":      "OFFLINE",
            "wake":      "WAITING FOR WAKE WORD",
            "listening": "LISTENING…",
            "thinking":  "THINKING…",
            "speaking":  "SPEAKING…",
        }
        self._status_lbl.setText(labels.get(state, state.upper()))
        self._orb.set_state(state)

    def _on_transcript(self, role: str, text: str):
        bubble = BubbleWidget(role, text)
        self._transcript_layout.addWidget(bubble)
        # Auto-scroll to bottom
        QTimer.singleShot(50, lambda: self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        ))

    def _on_finished(self):
        self._btn_start.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._status_lbl.setText("OFFLINE")
        self._orb.set_state("idle")

    def closeEvent(self, event):
        self._stop()
        event.accept()


# ─── Entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Dark palette base so native widgets don't flash white
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,        QColor("#0d0d1a"))
    palette.setColor(QPalette.ColorRole.WindowText,    QColor("#c8c8e8"))
    palette.setColor(QPalette.ColorRole.Base,          QColor("#0a0a14"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#0f0f20"))
    palette.setColor(QPalette.ColorRole.Text,          QColor("#c8c8e8"))
    palette.setColor(QPalette.ColorRole.Button,        QColor("#0f3460"))
    palette.setColor(QPalette.ColorRole.ButtonText,    QColor("#c8c8e8"))
    app.setPalette(palette)

    win = JarvisWindow()
    win.show()
    sys.exit(app.exec())