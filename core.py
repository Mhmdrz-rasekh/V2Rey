# core.py
import requests
import base64
import json
import urllib.parse
import os
import subprocess
import time
import re
from urllib.parse import unquote

class V2RayCoreManager:
    def __init__(self):
        self.subscriptions = {} 
        self.data_file = "subscriptions.json"
        self.xray_process = None
        self.config_path = "xray_temp_config.json"
        self.load_configs()

    def load_configs(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    for k, v in raw_data.items():
                        if isinstance(v, list):
                            self.subscriptions[k] = {"name": "Unknown Sub", "info": {}, "configs": v}
                        else:
                            self.subscriptions[k] = v
            except json.JSONDecodeError:
                self.subscriptions = {}

    def save_configs(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.subscriptions, f, ensure_ascii=False, indent=4)

    def _format_persian_metrics(self, text: str, metric_type: str) -> str:
        if not text: return "N/A"
        parts = []
        if metric_type == "data":
            tb = re.search(r'(\d+(?:\.\d+)?)\s*(?:ترابایت|TB|tb)', text)
            gb = re.search(r'(\d+(?:\.\d+)?)\s*(?:گیگابایت|GB|gb)', text)
            mb = re.search(r'(\d+(?:\.\d+)?)\s*(?:مگابایت|MB|mb)', text)
            if tb: parts.append(f"{tb.group(1)}TB")
            if gb: parts.append(f"{gb.group(1)}GB")
            if mb: parts.append(f"{mb.group(1)}MB")
        elif metric_type == "time":
            d = re.search(r'(\d+)\s*(?:روز|Day|days)', text)
            h = re.search(r'(\d+)\s*(?:ساعت|Hour|hours)', text)
            m = re.search(r'(\d+)\s*(?:دقیقه|Minute|minutes)', text)
            if d: parts.append(f"{d.group(1)}d")
            if h: parts.append(f"{h.group(1)}h")
            if m: parts.append(f"{m.group(1)}m")
        return ", ".join(parts) if parts else text

    def parse_config(self, raw_link: str) -> dict:
        parsed_data = {"raw": raw_link, "protocol": "unknown", "remark": "Unknown Server", "details": {}}
        try:
            if raw_link.startswith("vmess://"):
                parsed_data["protocol"] = "vmess"
                b64_str = raw_link.replace("vmess://", "").strip()
                b64_str += '=' * ((4 - len(b64_str) % 4) % 4)
                config_dict = json.loads(base64.b64decode(b64_str).decode('utf-8'))
                parsed_data["remark"] = config_dict.get("ps", "Unnamed Vmess")
                parsed_data["details"] = config_dict
            elif raw_link.startswith("vless://"):
                parsed_data["protocol"] = "vless"
                parsed_url = urllib.parse.urlparse(raw_link)
                user_info = parsed_url.netloc.split('@')
                if len(user_info) == 2:
                    uuid = user_info[0]
                    server_port = user_info[1].split(':')
                    server = server_port[0]
                    port = int(server_port[1]) if len(server_port) > 1 else 443
                else: raise ValueError("Invalid VLESS")
                query_params = urllib.parse.parse_qs(parsed_url.query)
                params = {k: v[0] for k, v in query_params.items()}
                parsed_data["remark"] = unquote(parsed_url.fragment, encoding='utf-8') if parsed_url.fragment else "Unnamed Vless"
                parsed_data["details"] = {"id": uuid, "server": server, "port": port, **params}
            elif raw_link.startswith("trojan://"):
                parsed_data["protocol"] = "trojan"
                parsed_data["remark"] = unquote(raw_link.split("#")[-1], encoding='utf-8') if "#" in raw_link else "Unnamed Trojan"
        except Exception:
            parsed_data["remark"] = "Parse Error"
        return parsed_data

    def fetch_subscription(self, url: str):
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            sub_name = "Subscription"
            if "profile-title" in response.headers:
                sub_name = unquote(response.headers["profile-title"])
            elif "Content-Disposition" in response.headers:
                disp = response.headers["Content-Disposition"]
                if "filename=" in disp:
                    sub_name = disp.split("filename=")[1].strip('"\'')
            sub_info = {}
            if "subscription-userinfo" in response.headers:
                info_parts = response.headers["subscription-userinfo"].split(";")
                for part in info_parts:
                    if "=" in part:
                        k, v = part.strip().split("=")
                        sub_info[k.lower()] = int(v)
            raw_data = response.text.strip()
            raw_data += '=' * ((4 - len(raw_data) % 4) % 4)
            decoded_text = base64.b64decode(raw_data).decode('utf-8')
            raw_links = [line.strip() for line in decoded_text.splitlines() if line.strip()]
            parsed_links = [self.parse_config(link) for link in raw_links]

            real_configs = []
            inline_name = None
            inline_data = None
            inline_expire = None

            for config in parsed_links:
                remark = config.get("remark", "")
                server_ip = config.get("details", {}).get("server", "")
                if "اسم:" in remark:
                    inline_name = remark.split("اسم:")[-1].strip()
                    continue
                if "حجم باقی مانده:" in remark:
                    raw_val = remark.split("حجم باقی مانده:")[-1].strip()
                    inline_data = self._format_persian_metrics(raw_val, "data")
                    continue
                if "زمان باقی مانده:" in remark:
                    raw_val = remark.split("زمان باقی مانده:")[-1].strip()
                    inline_expire = self._format_persian_metrics(raw_val, "time")
                    continue
                if server_ip in ["127.0.0.1", "8.8.8.8", "0.0.0.0"]:
                    continue
                real_configs.append(config)

            if inline_name: sub_name = inline_name
            if inline_data or inline_expire:
                sub_info["data_str"] = inline_data if inline_data else "N/A"
                sub_info["expire_str"] = inline_expire if inline_expire else "N/A"

            self.subscriptions[url] = {
                "name": sub_name,
                "info": sub_info,
                "configs": real_configs
            }
            self.save_configs()
        except Exception as e: raise RuntimeError(f"Network error: {e}")

    def delete_subscription(self, url: str):
        if url in self.subscriptions:
            del self.subscriptions[url]
            self.save_configs()

    def generate_xray_config(self, config_data: dict, socks_port: int, output_path: str = None):
        if output_path is None: output_path = self.config_path
        protocol = config_data.get("protocol")
        if protocol not in ["vmess", "vless"]: raise NotImplementedError("Protocol not supported.")
        details = config_data.get("details", {})
        http_port = int(socks_port) + 1
        inbounds = [{"port": int(socks_port), "listen": "127.0.0.1", "protocol": "socks", "settings": {"udp": True}}, {"port": http_port, "listen": "127.0.0.1", "protocol": "http", "settings": {"allowTransparent": False}}]
        outbound = {}
        if protocol == "vmess":
            outbound = {"protocol": "vmess", "settings": {"vnext": [{"address": details.get("add", ""), "port": int(details.get("port", 443)), "users": [{"id": details.get("id", ""), "alterId": int(details.get("aid", 0))}]}]}, "streamSettings": {"network": details.get("net", "tcp"), "security": details.get("tls", "none")}}
            if details.get("net") == "ws": outbound["streamSettings"]["wsSettings"] = {"path": details.get("path", "/"), "headers": {"Host": details.get("host", "")}}
        elif protocol == "vless":
            outbound = {"protocol": "vless", "settings": {"vnext": [{"address": details.get("server", ""), "port": int(details.get("port", 443)), "users": [{"id": details.get("id", ""), "encryption": details.get("encryption", "none"), "flow": details.get("flow", "")}]}]}, "streamSettings": {"network": details.get("type", "tcp"), "security": details.get("security", "none")}}
            net_type = details.get("type", "tcp")
            if net_type == "ws": outbound["streamSettings"]["wsSettings"] = {"path": details.get("path", "/"), "headers": {"Host": details.get("host", details.get("sni", ""))}}
            elif net_type == "grpc": outbound["streamSettings"]["grpcSettings"] = {"serviceName": details.get("serviceName", ""), "multiMode": details.get("mode", "multi") == "multi"}
            security = details.get("security", "none")
            if security == "tls": outbound["streamSettings"]["tlsSettings"] = {"serverName": details.get("sni", ""), "fingerprint": details.get("fp", "chrome")}
            elif security == "reality": outbound["streamSettings"]["realitySettings"] = {"serverName": details.get("sni", ""), "fingerprint": details.get("fp", "chrome"), "publicKey": details.get("pbk", ""), "shortId": details.get("sid", ""), "spiderX": details.get("spx", "/")}
        with open(output_path, 'w', encoding='utf-8') as f: json.dump({"inbounds": inbounds, "outbounds": [outbound]}, f, indent=4)

    def start_connection(self, config_data: dict, socks_port: int):
        self.stop_connection()
        self.generate_xray_config(config_data, socks_port)
        try:
            self.xray_process = subprocess.Popen(["xray", "run", "-c", self.config_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1.5)
            if self.xray_process.poll() is not None: raise RuntimeError("Core terminated.")
        except FileNotFoundError: raise FileNotFoundError("xray binary not found.")

    def stop_connection(self):
        if self.xray_process:
            self.xray_process.terminate()
            self.xray_process.wait()
            self.xray_process = None

    def test_latency(self, config_data: dict, test_port: int, ping_url: str = "http://connectivitycheck.gstatic.com/generate_204") -> float:
        temp_config_path = f"xray_ping_config_{test_port}.json"
        try: self.generate_xray_config(config_data, test_port, output_path=temp_config_path)
        except Exception: raise RuntimeError("Config Error")
        
        temp_process = subprocess.Popen(["xray", "run", "-c", temp_config_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            # زمان خواب افزایش پیدا کرد تا هسته برای اتصال فرصت کافی داشته باشد
            time.sleep(2.5) 
            if temp_process.poll() is not None: raise RuntimeError("Core died")
            proxies = {"http": f"socks5h://127.0.0.1:{test_port}", "https": f"socks5h://127.0.0.1:{test_port}"}
            start_time = time.time()
            
            # تایم اوت اتصال افزایش پیدا کرد
            requests.get(ping_url, proxies=proxies, timeout=7)
            return time.time() - start_time
        except Exception: raise RuntimeError("Timeout")
        finally:
            temp_process.terminate()
            temp_process.wait()
            if os.path.exists(temp_config_path): os.remove(temp_config_path)

    def set_system_proxy(self, enable: bool, socks_port: int = 10808):
        desktop_env = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        http_port = socks_port + 1
        if "gnome" in desktop_env:
            if enable:
                os.system(f'gsettings set org.gnome.system.proxy mode "manual" && gsettings set org.gnome.system.proxy.socks host "127.0.0.1" && gsettings set org.gnome.system.proxy.socks port {socks_port} && gsettings set org.gnome.system.proxy.http host "127.0.0.1" && gsettings set org.gnome.system.proxy.http port {http_port} && gsettings set org.gnome.system.proxy.https host "127.0.0.1" && gsettings set org.gnome.system.proxy.https port {http_port} && gsettings set org.gnome.system.proxy.ftp host "127.0.0.1" && gsettings set org.gnome.system.proxy.ftp port {http_port}')
            else: os.system('gsettings set org.gnome.system.proxy mode "none"')
        elif "kde" in desktop_env:
            if enable: os.system(f'kwriteconfig5 --file kioslaverc --group "Proxy Settings" --key ProxyType 1 && kwriteconfig5 --file kioslaverc --group "Proxy Settings" --key socksProxy "socks://127.0.0.1:{socks_port}" && kwriteconfig5 --file kioslaverc --group "Proxy Settings" --key httpProxy "http://127.0.0.1:{http_port}" && kwriteconfig5 --file kioslaverc --group "Proxy Settings" --key httpsProxy "http://127.0.0.1:{http_port}"')
            else: os.system('kwriteconfig5 --file kioslaverc --group "Proxy Settings" --key ProxyType 0')
            os.system('qdbus org.kde.kded5 /kded org.kde.kded5.reconfigure "proxy"')
