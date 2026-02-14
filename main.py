# main.py
import sys
import time
import concurrent.futures
from PyQt5.QtWidgets import QApplication, QMessageBox, QListWidgetItem, QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QColor, QBrush, QFont
from ui import MainWindow, PingDialog
from core import V2RayCoreManager

class ConfigItemWidget(QWidget):
    def __init__(self, base_text, index, ping_callback, delete_callback):
        super().__init__()
        self.base_text = base_text
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        self.lbl_text = QLabel(base_text)
        self.lbl_text.setStyleSheet("color: white;")
        layout.addWidget(self.lbl_text, stretch=1)
        
        self.btn_ping = QPushButton("⚡")
        self.btn_ping.setFixedSize(30, 30)
        self.btn_ping.setStyleSheet("QPushButton { background-color: #2d5a27; color: white; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #3b7533; }")
        self.btn_ping.clicked.connect(lambda: ping_callback(index))
        layout.addWidget(self.btn_ping)
        
        self.btn_delete = QPushButton("🗑")
        self.btn_delete.setFixedSize(30, 30)
        self.btn_delete.setStyleSheet("QPushButton { background-color: #8b0000; color: white; border-radius: 4px; } QPushButton:hover { background-color: #a80000; }")
        self.btn_delete.clicked.connect(lambda: delete_callback(index))
        layout.addWidget(self.btn_delete)

    def update_ping_status(self, latency_ms):
        if latency_ms >= 0:
            self.lbl_text.setText(f"{self.base_text} | Ping: {latency_ms} ms")
            if latency_ms <= 1000: color = "#2e7d32"
            elif latency_ms <= 2000: color = "#d48806"
            else: color = "#e65100"
            self.lbl_text.setStyleSheet(f"color: {color}; font-weight: bold;")
        else:
            self.lbl_text.setText(f"{self.base_text} | Ping: Timeout")
            self.lbl_text.setStyleSheet("color: #c62828; font-weight: bold;")

class FetchSubThread(QThread):
    success_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, core_manager, link):
        super().__init__()
        self.core = core_manager
        self.link = link

    def run(self):
        try:
            self.core.fetch_subscription(self.link)
            self.success_signal.emit()
        except Exception as e:
            self.error_signal.emit(str(e))

class BatchPingThread(QThread):
    progress_signal = pyqtSignal(int, int) 
    finished_signal = pyqtSignal()

    def __init__(self, core_manager, target_configs, target_url):
        super().__init__()
        self.core = core_manager
        self.target_configs = target_configs
        self.target_url = target_url

    def run(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures_map = {}
            for original_index, config_data in self.target_configs:
                if config_data.get("protocol") not in ["vmess", "vless"]:
                    self.progress_signal.emit(original_index, -1)
                    continue
                test_port = 20000 + original_index
                future = executor.submit(self.core.test_latency, config_data, test_port, self.target_url)
                futures_map[future] = original_index

            for future in concurrent.futures.as_completed(futures_map):
                original_index = futures_map[future]
                try:
                    latency_sec = future.result()
                    self.progress_signal.emit(original_index, int(latency_sec * 1000))
                except Exception:
                    self.progress_signal.emit(original_index, -1)
        self.finished_signal.emit()

class V2RayController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        base_font = QFont("Sans Serif", 10)
        base_font.setStyleHint(QFont.SansSerif)
        self.app.setFont(base_font)
        self.app.aboutToQuit.connect(self.cleanup_on_exit) 
        
        self.window = MainWindow()
        self.core = V2RayCoreManager()
        
        self.fetch_thread = None
        self.ping_thread = None
        
        self.window.btn_add_sub.clicked.connect(self.handle_add_sub)
        self.window.btn_update_sub.clicked.connect(self.handle_update_sub)
        self.window.btn_delete_sub.clicked.connect(self.handle_delete_sub)
        self.window.sub_combo.currentIndexChanged.connect(self.refresh_ui_for_sub)
        
        self.window.btn_connect.clicked.connect(self.handle_connect)
        self.window.btn_disconnect.clicked.connect(self.handle_disconnect)
        self.window.btn_ping_sub.clicked.connect(self.handle_batch_ping)
        
        self.refresh_combo_box()

    def cleanup_on_exit(self):
        self.core.stop_connection()
        try: self.core.set_system_proxy(enable=False)
        except Exception: pass

    def format_bytes(self, size_bytes):
        if size_bytes == 0: return "0 B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = 0
        while size_bytes >= 1024 and i < len(size_name) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.2f} {size_name[i]}"

    def refresh_combo_box(self):
        self.window.sub_combo.blockSignals(True)
        self.window.sub_combo.clear()
        for url, data in self.core.subscriptions.items():
            name = data.get("name", "Unknown Sub")
            self.window.sub_combo.addItem(name, url)
        self.window.sub_combo.blockSignals(False)
        self.refresh_ui_for_sub()

    def refresh_ui_for_sub(self):
        self.window.config_list.clear()
        current_url = self.window.sub_combo.currentData()
        
        if not current_url or current_url not in self.core.subscriptions:
            self.window.lbl_data_usage.setText("Data: N/A")
            self.window.lbl_expiry.setText("Expires: N/A")
            return

        sub_data = self.core.subscriptions[current_url]
        info = sub_data.get("info", {})
        
        if "data_str" in info:
            self.window.lbl_data_usage.setText(f"Data: {info['data_str']}")
            self.window.lbl_expiry.setText(f"Expires: {info['expire_str']}")
        elif info:
            total = info.get("total", 0)
            upload = info.get("upload", 0)
            download = info.get("download", 0)
            expire = info.get("expire", 0)
            used = upload + download
            data_str = f"Data: {self.format_bytes(used)} / {self.format_bytes(total)}"
            self.window.lbl_data_usage.setText(data_str)
            if expire > 0:
                days_left = max(0, (expire - int(time.time())) / 86400)
                self.window.lbl_expiry.setText(f"Expires: {days_left:.1f} Days")
            else:
                self.window.lbl_expiry.setText("Expires: Unlimited")
        else:
            self.window.lbl_data_usage.setText("Data: Unknown")
            self.window.lbl_expiry.setText("Expires: Unknown")

        for index, config in enumerate(sub_data.get("configs", [])):
            base_text = f"[{config['protocol'].upper()}] {config['remark']}"
            item = QListWidgetItem(self.window.config_list)
            widget = ConfigItemWidget(base_text, index, self.handle_single_ping, self.handle_single_delete)
            if "ping" in config:
                widget.update_ping_status(config["ping"])
            item.setSizeHint(widget.sizeHint())
            self.window.config_list.setItemWidget(item, widget)

    def execute_fetch(self, link: str):
        self.fetch_thread = FetchSubThread(self.core, link)
        self.fetch_thread.success_signal.connect(self.on_fetch_success)
        self.fetch_thread.error_signal.connect(self.on_fetch_error)
        self.fetch_thread.start()

    def handle_add_sub(self):
        link = self.window.sub_input.text().strip()
        if not link: return
        self.window.btn_add_sub.setEnabled(False)
        self.window.btn_add_sub.setText("Processing...")
        self.execute_fetch(link)

    def handle_update_sub(self):
        current_url = self.window.sub_combo.currentData()
        if not current_url: return
        self.window.btn_update_sub.setEnabled(False)
        self.window.btn_update_sub.setText("...")
        self.execute_fetch(current_url)

    def on_fetch_success(self):
        self.window.sub_input.clear()
        self.refresh_combo_box()
        self.window.btn_add_sub.setEnabled(True)
        self.window.btn_add_sub.setText("+ Add Sub")
        self.window.btn_update_sub.setEnabled(True)
        self.window.btn_update_sub.setText("Update")

    def on_fetch_error(self, error_msg):
        self.window.btn_add_sub.setEnabled(True)
        self.window.btn_add_sub.setText("+ Add Sub")
        self.window.btn_update_sub.setEnabled(True)
        self.window.btn_update_sub.setText("Update")
        QMessageBox.critical(self.window, "Network Error", error_msg)

    def handle_delete_sub(self):
        current_url = self.window.sub_combo.currentData()
        if current_url:
            self.core.delete_subscription(current_url)
            self.refresh_combo_box()

    def handle_single_delete(self, index):
        current_url = self.window.sub_combo.currentData()
        if not current_url or current_url not in self.core.subscriptions: return
        configs = self.core.subscriptions[current_url].get("configs", [])
        if 0 <= index < len(configs):
            del configs[index]
            self.core.save_configs()
            self.refresh_ui_for_sub()

    def handle_single_ping(self, index):
        current_url = self.window.sub_combo.currentData()
        if not current_url or current_url not in self.core.subscriptions: return
        configs = self.core.subscriptions[current_url].get("configs", [])
        if not (0 <= index < len(configs)): return

        dialog = PingDialog(self.window)
        if dialog.exec_():
            target_url = dialog.get_target_url()
            self.window.btn_ping_sub.setEnabled(False)
            self.window.sub_combo.setEnabled(False)
            target_configs = [(index, configs[index])]
            self.ping_thread = BatchPingThread(self.core, target_configs, target_url)
            self.ping_thread.progress_signal.connect(self.on_ping_progress)
            self.ping_thread.finished_signal.connect(self.on_ping_finished)
            self.ping_thread.start()

    def handle_batch_ping(self):
        current_url = self.window.sub_combo.currentData()
        if not current_url or current_url not in self.core.subscriptions: return
        configs = self.core.subscriptions[current_url].get("configs", [])
        if not configs: return

        dialog = PingDialog(self.window)
        if dialog.exec_():
            target_url = dialog.get_target_url()
            self.window.btn_ping_sub.setEnabled(False)
            self.window.btn_ping_sub.setText("Working...")
            self.window.sub_combo.setEnabled(False)
            target_configs = [(i, c) for i, c in enumerate(configs)]
            self.ping_thread = BatchPingThread(self.core, target_configs, target_url)
            self.ping_thread.progress_signal.connect(self.on_ping_progress)
            self.ping_thread.finished_signal.connect(self.on_ping_finished)
            self.ping_thread.start()

    def on_ping_progress(self, index, latency_ms):
        current_url = self.window.sub_combo.currentData()
        if not current_url: return
        self.core.subscriptions[current_url]["configs"][index]["ping"] = latency_ms
        item = self.window.config_list.item(index)
        if not item: return
        widget = self.window.config_list.itemWidget(item)
        if widget: widget.update_ping_status(latency_ms)

    def on_ping_finished(self):
        current_url = self.window.sub_combo.currentData()
        if current_url and current_url in self.core.subscriptions:
            configs = self.core.subscriptions[current_url]["configs"]
            configs.sort(key=lambda c: c.get("ping", float('inf')) if c.get("ping", -1) != -1 else float('inf'))
            self.core.save_configs()
            self.refresh_ui_for_sub()
        self.window.btn_ping_sub.setEnabled(True)
        self.window.btn_ping_sub.setText("Ping All")
        self.window.sub_combo.setEnabled(True)

    def handle_connect(self):
        current_url = self.window.sub_combo.currentData()
        selected_index = self.window.config_list.currentRow()
        if not current_url or selected_index < 0:
            QMessageBox.critical(self.window, "Selection Error", "No server selected. Click on a row background to select.")
            return

        config_data = self.core.subscriptions[current_url]["configs"][selected_index]
        port_str = self.window.port_input.text()
        if not port_str.isdigit(): return
            
        try:
            self.core.start_connection(config_data, int(port_str))
            if self.window.chk_system_proxy.isChecked():
                self.core.set_system_proxy(enable=True, socks_port=int(port_str))
            
            self.window.btn_connect.setEnabled(False)
            self.window.btn_disconnect.setEnabled(True)
            self.window.config_list.setEnabled(False)
            self.window.chk_system_proxy.setEnabled(False)
            self.window.sub_combo.setEnabled(False)
            self.window.btn_delete_sub.setEnabled(False)
            self.window.btn_update_sub.setEnabled(False)
            self.window.btn_ping_sub.setEnabled(False)
            
        except Exception as e:
            QMessageBox.critical(self.window, "Execution Error", f"Failed to start core:\n{e}")

    def handle_disconnect(self):
        self.core.stop_connection()
        try: self.core.set_system_proxy(enable=False)
        except Exception: pass
        
        self.window.btn_connect.setEnabled(True)
        self.window.btn_disconnect.setEnabled(False)
        self.window.config_list.setEnabled(True)
        self.window.chk_system_proxy.setEnabled(True)
        self.window.sub_combo.setEnabled(True)
        self.window.btn_delete_sub.setEnabled(True)
        self.window.btn_update_sub.setEnabled(True)
        self.window.btn_ping_sub.setEnabled(True)

    def run(self):
        self.window.show()
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    controller = V2RayController()
    controller.run()
