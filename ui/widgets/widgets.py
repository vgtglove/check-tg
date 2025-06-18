from PyQt5.QtWidgets import QTextEdit, QProgressBar, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize
from PyQt5.QtGui import QColor, QBrush, QPainter, QPen, QRadialGradient

# ========== Widgets ==========

# PhoneNumberEdit


class PhoneNumberEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.textChanged.connect(self.format_numbers)
        self._is_formatting = False

    def format_numbers(self):
        if self._is_formatting:
            return
        self._is_formatting = True
        cursor_position = self.textCursor().position()
        text = self.toPlainText()
        lines = text.split('\n')
        formatted_lines = []
        total_removed = 0
        for line in lines:
            original_length = len(line)
            formatted = ''.join(
                char for char in line if char.isdigit() or char == '+')
            if '+' in formatted:
                formatted = '+' + formatted.replace('+', '')
            formatted_lines.append(formatted)
            total_removed += original_length - len(formatted)
        new_text = '\n'.join(formatted_lines)
        self.setPlainText(new_text)
        new_cursor_position = max(0, cursor_position - total_removed)
        cursor = self.textCursor()
        cursor.setPosition(new_cursor_position)
        self.setTextCursor(cursor)
        self._is_formatting = False

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Plus, Qt.Key_Backspace, Qt.Key_Delete, Qt.Key_Return, Qt.Key_Enter) or \
           event.key() >= Qt.Key_0 and event.key() <= Qt.Key_9 or \
           event.modifiers() & (Qt.ControlModifier | Qt.MetaModifier):
            super().keyPressEvent(event)
        else:
            event.ignore()

# StyledProgressBar


class StyledProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 5px;
                text-align: center;
                height: 20px;
                background-color: #F5F5F5;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                                stop:0 #2196F3, stop:1 #4CAF50);
                border-radius: 5px;
            }
        """)
        self.setTextVisible(True)
        self.setFormat("%p%")

    def updateValue(self, value):
        current = self.value()
        if current != value:
            animation = QPropertyAnimation(self, b"value")
            animation.setDuration(300)
            animation.setStartValue(current)
            animation.setEndValue(value)
            animation.setEasingCurve(QEasingCurve.OutCubic)
            animation.start()

# AnimatedButton


class AnimatedButton(QPushButton):
    def __init__(self, text, color, parent=None):
        super().__init__(text, parent)
        self.base_color = color

        def adjust_color(color, factor=0.8):
            if color.startswith('#'):
                if len(color) == 7:
                    r = int(color[1:3], 16)
                    g = int(color[3:5], 16)
                    b = int(color[5:7], 16)
                    r = min(255, int(r * factor))
                    g = min(255, int(g * factor))
                    b = min(255, int(b * factor))
                    return f"#{r:02x}{g:02x}{b:02x}"
                else:
                    return color.replace('1', str(factor)[0])
            return color
        hover_color = adjust_color(color, 0.8)
        pressed_color = adjust_color(color, 0.6)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 13px;
                min-width: 120px;
                min-height: 35px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
            }}
            QPushButton:disabled {{
                background-color: #BDBDBD;
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumWidth(120)
        self.setMinimumHeight(35)

    def enterEvent(self, event):
        self.anim = QPropertyAnimation(self, b"size")
        self.anim.setDuration(100)
        current_size = self.size()
        self.anim.setStartValue(current_size)
        new_size = QSize(int(current_size.width() * 1.03),
                         int(current_size.height() * 1.03))
        self.anim.setEndValue(new_size)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim = QPropertyAnimation(self, b"size")
        self.anim.setDuration(100)
        self.anim.setStartValue(self.size())
        original_size = QSize(int(self.size().width() / 1.03),
                              int(self.size().height() / 1.03))
        self.anim.setEndValue(original_size)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.anim = QPropertyAnimation(self, b"size")
            self.anim.setDuration(50)
            self.anim.setStartValue(self.size())
            smaller_size = QSize(
                int(self.size().width() * 0.97), int(self.size().height() * 0.97))
            self.anim.setEndValue(smaller_size)
            self.anim.setEasingCurve(QEasingCurve.OutCubic)
            self.anim.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.anim = QPropertyAnimation(self, b"size")
            self.anim.setDuration(50)
            self.anim.setStartValue(self.size())
            hover_size = QSize(int(self.size().width() / 0.97 * 1.03),
                               int(self.size().height() / 0.97 * 1.03))
            self.anim.setEndValue(hover_size)
            self.anim.setEasingCurve(QEasingCurve.OutCubic)
            self.anim.start()
        super().mouseReleaseEvent(event)

# StatusIndicator


class StatusIndicator(QWidget):
    def __init__(self, status="空闲", parent=None):
        super().__init__(parent)
        self.status = status
        self.setMinimumSize(16, 16)
        self.setMaximumSize(16, 16)
        self.status_colors = {
            "错误": "#FF5722",
            "未授权": "#FF5722",
            "正在运行": "#4CAF50",
            "空闲": "#2196F3"
        }
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.blink)
        self.blink_on = True
        self.blink_alpha = 255
        self.updateState(status)

    def updateState(self, status):
        self.status = status
        if status == "正在运行":
            if not self.blink_timer.isActive():
                self.blink_timer.start(300)
        else:
            self.blink_timer.stop()
            self.blink_on = True
            self.blink_alpha = 255
        self.update()

    def blink(self):
        self.blink_alpha = 255 if self.blink_alpha == 120 else 120
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color_hex = self.status_colors.get(self.status, "#757575")
        color = QColor(color_hex)
        if self.status == "正在运行":
            color.setAlpha(self.blink_alpha)
        center = self.rect().center()
        gradient = QRadialGradient(center, self.width() / 2)
        gradient.setColorAt(0, color)
        gradient.setColorAt(0.7, color)
        gradient.setColorAt(1, color.darker(120))
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(color.darker(130), 1))
        painter.drawEllipse(self.rect().adjusted(2, 2, -2, -2))

# NumbersListWidget


class NumbersListWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.numbers = []
        self.display_limit = 1000

    def set_numbers(self, numbers):
        self.numbers = numbers
        self.update_display()

    def update_display(self):
        self.clear()
        total = len(self.numbers)
        display_count = min(total, self.display_limit)
        if display_count > 0:
            text = "\n".join(self.numbers[:display_count])
            if total > display_count:
                text += f"\n...\n(仅显示前 {display_count} 个，共 {total} 个号码)"
            else:
                text += f"\n\n共 {total} 个号码"
            self.setText(text)
        else:
            self.setText("没有号码")
