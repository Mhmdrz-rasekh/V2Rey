# ui.py
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QListWidget, QCheckBox, QLabel, 
                             QComboBox, QFrame, QDialog, QStyledItemDelegate)
from PyQt5.QtCore import Qt

class PingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ping Target Selection")
        self.resize(350, 180)
        self.setStyleSheet("QDialog { background-color: #2b2b2b; color: white; } QLabel { color: white; }")
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Select Predefined Target:"))
        self.combo = QComboBox()
        
        # --- جادوی رفع سفیدی لیست در لینوکس ---
        self.combo.setItemDelegate(QStyledItemDelegate())
        
        self.combo.setStyleSheet("""
            QComboBox { background-color: #3c3c3c; color: white; padding: 4px; border: 1px solid #555; }
            QComboBox QAbstractItemView { background-color: #2b2b2b; color: white; selection-background-color: #005f87; }
        """)
        
        self.combo.addItem("Google Connectivity Check", "http://connectivitycheck.gstatic.com/generate_204")
        self.combo.addItem("Google Static 204", "http://www.gstatic.com/generate_204")
        self.combo.addItem("Cloudflare Captive Portal", "http://cp.cloudflare.com")
        self.combo.addItem("Kernel.org", "http://kernel.org")
        self.combo.addItem("Firefox Portal Detect", "http://detectportal.firefox.com")
        self.combo.addItem("Apple Hotspot Detect", "http://captive.apple.com/hotspot-detect.html")
        self.combo.addItem("Cloudflare DNS (1.1.1.1)", "https://1.1.1.1")
        
        layout.addWidget(self.combo)
        
        layout.addWidget(QLabel("Or Enter Custom URL (Must include http/https):"))
        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("e.g., https://bing.com")
        self.custom_input.setStyleSheet("QLineEdit { background-color: #3c3c3c; color: white; padding: 4px; border: 1px solid #555; }")
        layout.addWidget(self.custom_input)
        
        self.btn_start = QPushButton("🚀 Start Ping")
        self.btn_start.setStyleSheet("QPushButton { background-color: #005f87; color: white; padding: 6px; font-weight: bold; border-radius: 4px; }")
        self.btn_start.clicked.connect(self.accept)
        layout.addWidget(self.btn_start)

    def get_target_url(self):
        custom_url = self.custom_input.text().strip()
        if custom_url:
            if not custom_url.startswith("http"):
                custom_url = "http://" + custom_url
            return custom_url
        return self.combo.currentData()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("V2Ray Client")
        self.resize(700, 750)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        sub_layout = QHBoxLayout()
        self.sub_input = QLineEdit()
        self.sub_input.setPlaceholderText("Enter new subscription link here...")
        self.btn_add_sub = QPushButton("+ Add Sub")
        sub_layout.addWidget(self.sub_input)
        sub_layout.addWidget(self.btn_add_sub)
        main_layout.addLayout(sub_layout)
        
        card_frame = QFrame()
        card_frame.setStyleSheet("""
            QFrame { background-color: #2b2b2b; border-radius: 8px; padding: 10px; margin-top: 10px; } 
            QLabel { color: #e0e0e0; font-size: 13px; }
        """)
        card_layout = QVBoxLayout(card_frame)
        
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Active Sub:"))
        
        self.sub_combo = QComboBox()
        self.sub_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        
        # --- جادوی رفع سفیدی لیست در لینوکس ---
        self.sub_combo.setItemDelegate(QStyledItemDelegate())
        
        self.sub_combo.setStyleSheet("""
            QComboBox { background-color: #3c3c3c; color: white; border: 1px solid #555; padding: 4px; }
            QComboBox QAbstractItemView { background-color: #2b2b2b; color: white; selection-background-color: #005f87; }
        """)
        
        self.btn_update_sub = QPushButton("Update")
        self.btn_update_sub.setStyleSheet("QPushButton { background-color: #005f87; color: white; padding: 4px 10px; border-radius: 4px; }")
        
        self.btn_ping_sub = QPushButton("Ping All")
        self.btn_ping_sub.setStyleSheet("QPushButton { background-color: #2d5a27; color: white; padding: 4px 10px; border-radius: 4px; }")
        
        self.btn_delete_sub = QPushButton("Delete")
        self.btn_delete_sub.setStyleSheet("QPushButton { background-color: #8b0000; color: white; padding: 4px 10px; border-radius: 4px; }")
        
        controls_layout.addWidget(self.sub_combo, stretch=1)
        controls_layout.addWidget(self.btn_update_sub)
        controls_layout.addWidget(self.btn_ping_sub)
        controls_layout.addWidget(self.btn_delete_sub)
        card_layout.addLayout(controls_layout)
        
        metrics_layout = QHBoxLayout()
        self.lbl_data_usage = QLabel("Data: N/A")
        self.lbl_expiry = QLabel("Expires: N/A")
        metrics_layout.addWidget(self.lbl_data_usage)
        metrics_layout.addWidget(self.lbl_expiry)
        metrics_layout.setAlignment(Qt.AlignLeft)
        card_layout.addLayout(metrics_layout)
        
        main_layout.addWidget(card_frame)

        main_layout.addWidget(QLabel("Servers in active subscription:"))
        self.config_list = QListWidget()
        main_layout.addWidget(self.config_list)

        settings_layout = QHBoxLayout()
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Port (e.g., 10808)")
        self.port_input.setText("10808") 
        self.chk_system_proxy = QCheckBox("Set as System Proxy (Global)")
        settings_layout.addWidget(QLabel("Base Inbound Port:"))
        settings_layout.addWidget(self.port_input)
        settings_layout.addWidget(self.chk_system_proxy)
        main_layout.addLayout(settings_layout)
        
        control_layout = QHBoxLayout()
        self.btn_connect = QPushButton("Connect")
        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_disconnect.setEnabled(False) 
        control_layout.addWidget(self.btn_connect)
        control_layout.addWidget(self.btn_disconnect)
        main_layout.addLayout(control_layout)
