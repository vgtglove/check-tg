import sys
import os
import configparser
import json
from datetime import datetime, timedelta
from typing import List, Optional
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QTextEdit, QLabel,
                             QProgressBar, QFileDialog, QMessageBox, QLineEdit,
                             QFrame, QGroupBox, QSplitter, QTableWidget,
                             QTableWidgetItem, QHeaderView, QInputDialog, QMenu, QAction, QDialog, QGridLayout, QScrollArea, QCheckBox, QSizePolicy,
                             QMenuBar, QComboBox, QTabWidget, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QDateTime, QPropertyAnimation, QEasingCurve, QRect, QPoint, QSize
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QCursor, QBrush, QPainter, QPen, QRadialGradient
from ui.dialogs.dialogs import ConfigDialog, AboutDialog, ContactDialog, ChangelogDialog, ActivityResultDialog
from ui.widgets.widgets import PhoneNumberEdit, StyledProgressBar, AnimatedButton, StatusIndicator, NumbersListWidget

# ========== 以下为UI相关类 ==========

# StatusIndicator, AnimatedButton, StyledProgressBar, PhoneNumberEdit, ConfigDialog, AboutDialog, ContactDialog, ChangelogDialog, ActivityResultDialog, NumbersListWidget
# 以及TelegramGUI主窗口类

# ... 这里插入上述所有UI相关类的完整定义 ...

# 注意：不包含主程序入口和业务逻辑线程类（如CheckThread、ActivityCheckThread、PhoneNumberImportThread、UserActivityStatus、SessionStatus等），这些保留在telegram_gui.py或utils中。


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


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = configparser.ConfigParser()
        self.config.read('config.ini', encoding='utf-8')
        self.initUI()

    def initUI(self):
        self.setWindowTitle('配置')
        self.setFixedWidth(400)
        layout = QVBoxLayout()
        api_group = QGroupBox('API设置')
        api_layout = QGridLayout()
        api_layout.addWidget(QLabel('API ID:'), 0, 0)
        self.api_id_edit = QLineEdit()
        self.api_id_edit.setText(self.config.get(
            'API', 'api_id', fallback='2040'))
        api_layout.addWidget(self.api_id_edit, 0, 1)
        api_layout.addWidget(QLabel('API Hash:'), 1, 0)
        self.api_hash_edit = QLineEdit()
        self.api_hash_edit.setText(self.config.get(
            'API', 'api_hash', fallback='b18441a1ff607e10a989891a5462e627'))
        api_layout.addWidget(self.api_hash_edit, 1, 1)
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        settings_group = QGroupBox('通用设置')
        settings_layout = QGridLayout()
        settings_layout.addWidget(QLabel('默认冷却时间(秒):'), 0, 0)
        self.cooldown_edit = QLineEdit()
        self.cooldown_edit.setText(self.config.get(
            'Settings', 'cooldown_time', fallback='180'))
        settings_layout.addWidget(self.cooldown_edit, 0, 1)
        settings_layout.addWidget(QLabel('默认批量大小:'), 1, 0)
        self.batch_size_edit = QLineEdit()
        self.batch_size_edit.setText(self.config.get(
            'Settings', 'batch_size', fallback='10'))
        settings_layout.addWidget(self.batch_size_edit, 1, 1)
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        btn_layout = QHBoxLayout()
        save_btn = QPushButton('保存')
        save_btn.clicked.connect(self.save_config)
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def save_config(self):
        try:
            if not self.config.has_section('API'):
                self.config.add_section('API')
            if not self.config.has_section('Settings'):
                self.config.add_section('Settings')
            self.config.set('API', 'api_id', self.api_id_edit.text())
            self.config.set('API', 'api_hash', self.api_hash_edit.text())
            self.config.set('Settings', 'cooldown_time',
                            self.cooldown_edit.text())
            self.config.set('Settings', 'batch_size',
                            self.batch_size_edit.text())
            with open('config.ini', 'w', encoding='utf-8') as f:
                self.config.write(f)
            QMessageBox.information(self, '成功', '配置已保存！')
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, '错误', f'保存配置时出错：{str(e)}')


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


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于软件")
        self.setFixedSize(400, 300)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: #424242;
            }
            QLabel#title {
                font-size: 18px;
                font-weight: bold;
                color: #1976D2;
            }
            QLabel#version {
                font-size: 14px;
                color: #757575;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        layout = QVBoxLayout()
        title_label = QLabel("Telegram消息工具")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignCenter)
        version_label = QLabel("版本 1.0.0")
        version_label.setObjectName("version")
        version_label.setAlignment(Qt.AlignCenter)
        description = QLabel(
            "Telegram消息工具是一款高效的电话号码检测软件，用于确认哪些电话号码已在Telegram上注册。")
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        copyright_label = QLabel("© 2025 zat 版权所有")
        copyright_label.setAlignment(Qt.AlignCenter)
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(title_label)
        layout.addWidget(version_label)
        layout.addSpacing(20)
        layout.addWidget(description)
        layout.addSpacing(20)
        layout.addWidget(copyright_label)
        layout.addSpacing(30)
        layout.addWidget(ok_button, 0, Qt.AlignCenter)
        self.setLayout(layout)


class ContactDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("联系我们")
        self.setFixedSize(400, 300)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: #424242;
            }
            QLabel#title {
                font-size: 18px;
                font-weight: bold;
                color: #1976D2;
            }
            QTextEdit {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background-color: #F5F5F5;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        layout = QVBoxLayout()
        title_label = QLabel("联系我们")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignCenter)
        contact_info = QTextEdit()
        contact_info.setReadOnly(True)
        contact_info.setHtml("""
            <div style="text-align: center; margin: 10px;">
                <p><b>客服TG: @jofax</b></p>
                <p><b>官方TG群: @kupof</b></p>
            </div>
        """)
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(title_label)
        layout.addSpacing(20)
        layout.addWidget(contact_info)
        layout.addSpacing(20)
        layout.addWidget(ok_button, 0, Qt.AlignCenter)
        self.setLayout(layout)


class ChangelogDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("更新日志")
        self.setFixedSize(500, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: #424242;
            }
            QLabel#title {
                font-size: 18px;
                font-weight: bold;
                color: #1976D2;
            }
            QTextEdit {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background-color: #F8F8F8;
                font-family: Arial, sans-serif;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        layout = QVBoxLayout()
        title_label = QLabel("更新日志")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignCenter)
        changelog = QTextEdit()
        changelog.setReadOnly(True)
        changelog.setHtml("""
            <div style="margin: 10px;">
                <p style="font-size: 14px; font-weight: bold; color: #1976D2;">如若有新版本将在以下群发布</p>
                <p style="font-size: 14px; font-weight: bold; color: #1976D2;">官方TG群发布: @kupof</p>
                <ul>
                <li>版本 1.0.1 (2024-04-07)</li>
                <li>支持TG活跃度检测</li>
                <li>优化支持数百万号码一次性导入筛选</li>
                <li>新增一键删除不可用Session</li>
                </ul>
                <ul>
                    <li>版本 1.0.0 (2024-04-05)</li>
                    <li>支持批量协议号轮询</li>
                    <li>支持批量检测号码</li>
                    <li>支持从文件导入号码</li>
                </ul>
            </div>
        """)
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(title_label)
        layout.addSpacing(10)
        layout.addWidget(changelog)
        layout.addSpacing(15)
        layout.addWidget(ok_button, 0, Qt.AlignCenter)
        self.setLayout(layout)


class ActivityResultDialog(QDialog):
    def __init__(self, activity_results, parent=None):
        super().__init__(parent)
        self.activity_results = activity_results
        self.setWindowTitle("活跃度检测结果")
        self.setMinimumSize(900, 600)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels([
            "手机号", "活跃状态", "最后在线", "检测时间", "距离最后在线"])
        self.result_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E0E0E0;
                background-color: white;
                gridline-color: #F0F0F0;
            }
            QTableWidget::item {
                padding: 4px;
                border-bottom: 1px solid #F0F0F0;
            }
            QTableWidget::item:selected {
                background-color: #E3F2FD;
                color: #000000;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 6px;
                border: none;
                border-right: 1px solid #E0E0E0;
                border-bottom: 1px solid #E0E0E0;
                font-weight: bold;
                color: #424242;
            }
        """)
        self.result_table.setRowCount(len(self.activity_results))
        for row, activity in enumerate(self.activity_results):
            phone_item = QTableWidgetItem(activity.phone_number)
            self.result_table.setItem(row, 0, phone_item)
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(5, 0, 5, 0)
            status_layout.setSpacing(8)
            indicator = QWidget()
            indicator.setMinimumSize(16, 16)
            indicator.setMaximumSize(16, 16)
            indicator.setStyleSheet(
                f"background-color: {activity.status_color}; border-radius: 8px;")
            status_label = QLabel(activity.activity_status)
            status_label.setStyleSheet(
                f"color: {activity.status_color}; font-weight: bold;")
            status_layout.addWidget(indicator)
            status_layout.addWidget(status_label)
            status_layout.addStretch()
            self.result_table.setCellWidget(row, 1, status_widget)
            last_seen_text = ""
            if activity.last_seen:
                last_seen_text = activity.last_seen.strftime("%d日 %H:%M:%S")
            last_seen_item = QTableWidgetItem(last_seen_text)
            self.result_table.setItem(row, 2, last_seen_item)
            check_time_text = ""
            if activity.check_time:
                check_time_text = activity.check_time.strftime("%d日 %H:%M:%S")
            check_time_item = QTableWidgetItem(check_time_text)
            self.result_table.setItem(row, 3, check_time_item)
            time_diff_text = "未知"
            if activity.last_seen and activity.check_time:
                time_diff = activity.check_time - activity.last_seen
                days = time_diff.days
                hours, remainder = divmod(time_diff.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                if days > 0:
                    time_diff_text = f"{days}天{hours}小时{minutes}分"
                elif hours > 0:
                    time_diff_text = f"{hours}小时{minutes}分"
                else:
                    time_diff_text = f"{minutes}分{seconds}秒"
            time_diff_item = QTableWidgetItem(time_diff_text)
            self.result_table.setItem(row, 4, time_diff_item)
            self.result_table.setRowHeight(row, 40)
            if row % 2 == 0:
                for col in range(self.result_table.columnCount()):
                    if self.result_table.item(row, col):
                        self.result_table.item(
                            row, col).setBackground(QColor("#F9F9F9"))
        self.result_table.setColumnWidth(0, 130)
        self.result_table.setColumnWidth(1, 120)
        self.result_table.setColumnWidth(2, 140)
        self.result_table.setColumnWidth(3, 140)
        self.result_table.setColumnWidth(4, 130)
        stats_panel = QWidget()
        stats_layout = QHBoxLayout(stats_panel)
        total_count = len(self.activity_results)
        active_count = sum(1 for a in self.activity_results if a.is_active)
        active_pct = active_count / total_count * 100 if total_count > 0 else 0
        stats_label = QLabel(
            f"总计: {total_count} 个号码，活跃: {active_count} 个 ({active_pct:.1f}%)")
        stats_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #1976D2;")
        stats_layout.addWidget(stats_label)
        stats_layout.addStretch()
        buttons_layout = QHBoxLayout()
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        layout.addWidget(self.result_table)
        layout.addWidget(stats_panel)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)


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
