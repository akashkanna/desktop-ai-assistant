"""
Gesture Overlay module for Jarvis Gesture Control.
Provides PySide6 widgets for drawing skeletons, showing telemetry debug tables,
and rendering floating HUD overlays on the desktop.
"""

import cv2
import time
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QSizePolicy
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QImage, QPixmap, QColor, QFont
from ui.theme.theme_manager import Colors, ThemeManager
from ui.components.base import GlassCard, SectionHeader

# Cyberpunk Neon Blue styling colors
COLOR_CYAN_BGR = (255, 229, 0)      # BGR for OpenCV
COLOR_CYAN_HEX = "#00E5FF"
COLOR_GLOW_BGR = (255, 0, 128)
COLOR_TEXT_MUTED = "#8A8A9F"

class GestureVisualsHelper:
    """Helper to draw skeleton, bounding boxes, and labels on camera frame."""
    
    CONNECTIONS = [
        ("WRIST", "THUMB_CMC"), ("THUMB_CMC", "THUMB_MCP"), ("THUMB_MCP", "THUMB_IP"), ("THUMB_IP", "THUMB_TIP"),
        ("WRIST", "INDEX_FINGER_MCP"), ("INDEX_FINGER_MCP", "INDEX_FINGER_PIP"), ("INDEX_FINGER_PIP", "INDEX_FINGER_DIP"), ("INDEX_FINGER_DIP", "INDEX_FINGER_TIP"),
        ("INDEX_FINGER_MCP", "MIDDLE_FINGER_MCP"), ("WRIST", "MIDDLE_FINGER_MCP"), ("MIDDLE_FINGER_MCP", "MIDDLE_FINGER_PIP"), ("MIDDLE_FINGER_PIP", "MIDDLE_FINGER_DIP"), ("MIDDLE_FINGER_DIP", "MIDDLE_FINGER_TIP"),
        ("MIDDLE_FINGER_MCP", "RING_FINGER_MCP"), ("WRIST", "RING_FINGER_MCP"), ("RING_FINGER_MCP", "RING_FINGER_PIP"), ("RING_FINGER_PIP", "RING_FINGER_DIP"), ("RING_FINGER_DIP", "RING_FINGER_TIP"),
        ("RING_FINGER_MCP", "PINKY_MCP"), ("WRIST", "PINKY_MCP"), ("PINKY_MCP", "PINKY_PIP"), ("PINKY_PIP", "PINKY_DIP"), ("PINKY_DIP", "PINKY_TIP"),
    ]

    @staticmethod
    def draw_skeleton(frame, hand_data):
        """Draws skeleton, joints, bounding box, and tag label on the BGR frame."""
        h, w, _ = frame.shape
        landmarks = hand_data["landmarks"]
        bbox = hand_data["bbox"]  # (x, y, w, h)
        label = hand_data["label"]
        confidence = hand_data["confidence"]
        
        # 1. Draw connections
        for start, end in GestureVisualsHelper.CONNECTIONS:
            if start in landmarks and end in landmarks:
                pt1 = (int(landmarks[start][0] * w), int(landmarks[start][1] * h))
                pt2 = (int(landmarks[end][0] * w), int(landmarks[end][1] * h))
                cv2.line(frame, pt1, pt2, COLOR_CYAN_BGR, 2)
                cv2.line(frame, pt1, pt2, COLOR_GLOW_BGR, 1)

        # 2. Draw joints
        for name, pt in landmarks.items():
            cx = int(pt[0] * w)
            cy = int(pt[1] * h)
            cv2.circle(frame, (cx, cy), 4, (0, 255, 255), -1)

        # 3. Draw Bounding Box
        bx, by, bw, bh = bbox
        cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), COLOR_CYAN_BGR, 2)
        
        # 4. Draw Tag Label
        tag = f"{label} {int(confidence * 100)}%"
        cv2.putText(frame, tag, (bx, max(20, by - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_CYAN_BGR, 1)
        
        return frame


class GestureDashboardPanel(QWidget):
    """Futuristic Jarvis-style Gesture telemetry & control panel."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(12)

        # --- LEFT PANEL: CAMERA MONITOR ---
        left_card = GlassCard(radius=16)
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.addWidget(SectionHeader("Ocular Stream"))
        
        self.feed_label = QLabel("Initializing Video Stream...")
        self.feed_label.setAlignment(Qt.AlignCenter)
        self.feed_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.feed_label.setMinimumSize(420, 320)
        self.feed_label.setStyleSheet("background-color: #060613; border: 1px solid rgba(0, 229, 255, 0.1); border-radius: 8px; color: #5f5f7f;")
        left_layout.addWidget(self.feed_label)
        main_layout.addWidget(left_card, stretch=2)

        # --- CENTER PANEL: RADAR TELEMETRY HUD ---
        center_card = GlassCard(radius=16)
        center_layout = QVBoxLayout(center_card)
        center_layout.setContentsMargins(12, 12, 12, 12)
        center_layout.addWidget(SectionHeader("HUD Radar"))
        
        radar_widget = QFrame()
        radar_widget.setStyleSheet("""
            background: radial-gradient(circle, rgba(0, 229, 255, 0.08) 0%, rgba(6, 6, 19, 0.6) 100%);
            border: 1px solid rgba(0, 229, 255, 0.15);
            border-radius: 12px;
        """)
        radar_vbox = QVBoxLayout(radar_widget)
        radar_vbox.setAlignment(Qt.AlignCenter)
        
        self.hud_glow = QLabel("⎋")
        self.hud_glow.setFont(QFont("Segoe UI", 56))
        self.hud_glow.setStyleSheet(f"color: {COLOR_CYAN_HEX};")
        self.hud_glow.setAlignment(Qt.AlignCenter)
        
        self.hud_mode = QLabel("STANDBY")
        self.hud_mode.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.hud_mode.setStyleSheet("color: #00E5FF; letter-spacing: 3px;")
        self.hud_mode.setAlignment(Qt.AlignCenter)
        
        radar_vbox.addWidget(self.hud_glow)
        radar_vbox.addWidget(self.hud_mode)
        
        center_layout.addWidget(radar_widget)
        main_layout.addWidget(center_card, stretch=1)

        # --- RIGHT PANEL: DETAILED METRICS & DEBUG PANEL ---
        right_card = GlassCard(radius=16)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.addWidget(SectionHeader("Debugging Telemetry"))

        # Setup metric displays
        self.lbl_status = self._add_metric(right_layout, "HAND STATUS", "Not Detected")
        self.lbl_gesture = self._add_metric(right_layout, "GESTURE", "None")
        self.lbl_confidence = self._add_metric(right_layout, "CONFIDENCE", "0%")
        self.lbl_state = self._add_metric(right_layout, "STATE", "NO_HAND")
        self.lbl_action = self._add_metric(right_layout, "ACTION", "None")
        self.lbl_fps = self._add_metric(right_layout, "FPS", "0.0")
        self.lbl_frame_received = self._add_metric(right_layout, "FRAME", "No")
        self.lbl_rgb_conversion = self._add_metric(right_layout, "RGB", "No")
        self.lbl_hands_detected = self._add_metric(right_layout, "HANDS", "0")
        self.lbl_left_hand = self._add_metric(right_layout, "LEFT HAND", "No")
        self.lbl_right_hand = self._add_metric(right_layout, "RIGHT HAND", "No")
        self.lbl_failure_reason = self._add_metric(right_layout, "FAILURE", "None")

        # Fingers debug grid (Thumb, Index, Middle, Ring, Pinky)
        finger_box = QFrame()
        finger_box.setStyleSheet("background-color: rgba(0, 229, 255, 0.03); border: 1px solid rgba(0, 229, 255, 0.08); border-radius: 8px; padding: 6px; margin-top: 5px;")
        finger_layout = QGridLayout(finger_box)
        finger_layout.setSpacing(4)
        finger_layout.setContentsMargins(4, 4, 4, 4)

        self.finger_labels = {}
        fingers_list = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
        for col, name in enumerate(fingers_list):
            lbl_title = QLabel(name.upper())
            lbl_title.setFont(QFont("Segoe UI", 8, QFont.Bold))
            lbl_title.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
            lbl_title.setAlignment(Qt.AlignCenter)
            
            lbl_state = QLabel("Closed")
            lbl_state.setFont(QFont("Segoe UI", 9, QFont.Bold))
            lbl_state.setStyleSheet("color: #EF4444;")
            lbl_state.setAlignment(Qt.AlignCenter)
            
            finger_layout.addWidget(lbl_title, 0, col)
            finger_layout.addWidget(lbl_state, 1, col)
            self.finger_labels[name.lower()] = lbl_state

        right_layout.addWidget(finger_box)
        right_layout.addStretch()
        
        main_layout.addWidget(right_card, stretch=1)

    def _add_metric(self, layout, name, default_val):
        row = QFrame()
        row.setStyleSheet("background-color: rgba(255,255,255,0.02); border-radius: 6px; padding: 4px;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(8, 4, 8, 4)
        
        title = QLabel(name)
        title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        title.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
        
        val = QLabel(default_val)
        val.setFont(QFont("Segoe UI", 10, QFont.Bold))
        val.setStyleSheet(f"color: {COLOR_CYAN_HEX};")
        val.setAlignment(Qt.AlignRight)
        
        rl.addWidget(title)
        rl.addWidget(val)
        layout.addWidget(row)
        return val

    @Slot(object, dict)
    def update_telemetry(self, cv_frame, telemetry):
        """Updates GUI labels, finger tracking states, and video display feed."""
        # 1. Update text telemetry fields
        gesture = telemetry.get("gesture", "None")
        conf = telemetry.get("confidence", 0.0)
        mode = telemetry.get("mode", "NO_HAND")
        action = telemetry.get("action", "None")
        fps = telemetry.get("fps", 0.0)
        
        hand_detected = telemetry.get("hand_count", 0) > 0
        self.lbl_status.setText("Detected" if hand_detected else "Not Detected")
        self.lbl_status.setStyleSheet("color: #10B981;" if hand_detected else "color: #EF4444;")
        
        self.lbl_gesture.setText(gesture)
        self.lbl_confidence.setText(f"{int(conf * 100)}%")
        self.lbl_state.setText(mode)
        self.lbl_action.setText(action)
        self.lbl_fps.setText(f"{fps:.1f}")
        self.lbl_frame_received.setText("Yes" if telemetry.get("camera_frame_received", False) else "No")
        self.lbl_rgb_conversion.setText("Yes" if telemetry.get("rgb_conversion", False) else "No")
        self.lbl_hands_detected.setText(str(telemetry.get("hand_count", 0)))
        self.lbl_left_hand.setText("Yes" if telemetry.get("hand_labels") and "Left" in telemetry.get("hand_labels") else "No")
        self.lbl_right_hand.setText("Yes" if telemetry.get("hand_labels") and "Right" in telemetry.get("hand_labels") else "No")
        failure_text = telemetry.get("failure_reason") or "None"
        self.lbl_failure_reason.setText(failure_text)

        # 2. Update individual fingers open/closed states
        fingers = telemetry.get("fingers", {})
        for name, lbl in self.finger_labels.items():
            is_open = fingers.get(name, False)
            lbl.setText("Open" if is_open else "Closed")
            lbl.setStyleSheet("color: #10B981;" if is_open else "color: #EF4444;")

        # Update HUD text
        self.hud_mode.setText(mode)
        if mode == "ACTION_EXECUTED":
            self.hud_glow.setStyleSheet("color: #10B981;") # Green
        elif mode == "GESTURE_PENDING":
            self.hud_glow.setStyleSheet("color: #FBBF24;") # Yellow
        elif mode == "TRACKING":
            self.hud_glow.setStyleSheet(f"color: {COLOR_CYAN_HEX};")
        else:
            self.hud_glow.setStyleSheet("color: #6B7280;") # Grey

        # 3. Render frame to canvas
        if cv_frame is not None:
            # Flip horizontally to match mirror representation
            flipped = cv2.flip(cv_frame, 1)
            rgb = cv2.cvtColor(flipped, cv2.COLOR_BGR2RGB)
            h, w, c = rgb.shape
            
            qimg = QImage(rgb.data, w, h, c * w, QImage.Format_RGB888)
            pix = QPixmap.fromImage(qimg)
            
            scaled_pix = pix.scaled(self.feed_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.feed_label.setPixmap(scaled_pix)


class GestureFloatingHUD(QWidget):
    """Futuristic floating HUD widget showing overlay details on top of desktops."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_hud()

    def _init_hud(self):
        self.setWindowFlags(
            Qt.Window |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.resize(250, 110)
        
        # Bottom-right layout alignment
        self.move(50, 50)  # default top-left offset

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        card = QFrame()
        card.setObjectName("HUDFrame")
        card.setStyleSheet(f"""
            QFrame#HUDFrame {{
                background-color: rgba(6, 6, 19, 0.85);
                border: 2px solid {COLOR_CYAN_HEX};
                border-radius: 10px;
            }}
        """)
        
        cl = QVBoxLayout(card)
        cl.setContentsMargins(10, 6, 10, 6)
        cl.setSpacing(2)
        
        title = QLabel("JARVIS HUD v2.0")
        title.setFont(QFont("Segoe UI", 8, QFont.Bold))
        title.setStyleSheet("color: #5f5f7f; letter-spacing: 2px;")
        
        self.lbl_state = QLabel("STATE: NO_HAND")
        self.lbl_state.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.lbl_state.setStyleSheet(f"color: {COLOR_CYAN_HEX};")
        
        self.lbl_gesture = QLabel("GESTURE: None")
        self.lbl_gesture.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.lbl_gesture.setStyleSheet("color: #FFFFFF;")
        
        self.lbl_action = QLabel("ACTION: None")
        self.lbl_action.setFont(QFont("Segoe UI", 9))
        self.lbl_action.setStyleSheet("color: #A0AEC0;")
        
        cl.addWidget(title)
        cl.addWidget(self.lbl_state)
        cl.addWidget(self.lbl_gesture)
        cl.addWidget(self.lbl_action)
        
        layout.addWidget(card)

    def update_hud(self, telemetry):
        """Updates fields on the floating overlay panel."""
        mode = telemetry.get("mode", "NO_HAND")
        gesture = telemetry.get("gesture", "None")
        action = telemetry.get("action", "None")
        
        self.lbl_state.setText(f"STATE: {mode}")
        self.lbl_gesture.setText(f"GESTURE: {gesture}")
        self.lbl_action.setText(f"ACTION: {action}")
        self.show()
