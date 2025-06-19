import configparser
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QGroupBox, QGridLayout, QTextEdit, QTableWidget, QTableWidgetItem, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

# ========== Dialogs ==========

# ConfigDialog


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
        from PyQt5.QtWidgets import QMessageBox
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

# AboutDialog


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

# ContactDialog


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

# ChangelogDialog


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

# ActivityResultDialog


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

# SendMessageDialog


class SendMessageDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("发送消息")
        self.setFixedSize(400, 250)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: #424242;
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
        label = QLabel("请输入要发送的消息：")
        layout.addWidget(label)
        self.message_edit = QTextEdit()
        self.message_edit.setPlaceholderText("在此输入消息内容...")
        layout.addWidget(self.message_edit)
        btn_layout = QHBoxLayout()
        send_btn = QPushButton("发送")
        send_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(send_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def get_message(self):
        return self.message_edit.toPlainText().strip()
