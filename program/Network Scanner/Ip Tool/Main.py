import sys
import os
import socket
import subprocess
import requests
import urllib3
import concurrent.futures
import random
import ipaddress
from urllib.parse import urlparse
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QFrame, QGraphicsDropShadowEffect,
                             QScrollArea, QStyle, QStackedWidget, QInputDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QCursor

# --- Helper Functions ---

def prepare_ip(user_input):
    user_input = user_input.strip()
    if not user_input: return None
    
    # Remove protocol if present to get domain/ip
    if "://" in user_input:
        try:
            parsed = urlparse(user_input)
            user_input = parsed.netloc
        except:
            pass
            
    # Remove path if present
    if "/" in user_input:
        user_input = user_input.split('/')[0]

    try:
        # Try to resolve to check if valid
        ip = socket.gethostbyname(user_input)
        return ip
    except:
        return None

# --- Logic Functions ---

def logic_geoip(logger, user_input):
    ip = prepare_ip(user_input)
    if not ip:
        logger.emit("<font color='#ef4444'><b>[-] IP/Domaine invalide.</b></font>")
        return

    logger.emit(f"<font color='#3b82f6'><b>[*] GeoIP Lookup pour {ip}...</b></font>")
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,regionName,city,zip,lat,lon,timezone,isp,org,as,query", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data['status'] == 'fail':
                logger.emit(f"<font color='#ef4444'>[-] Erreur API: {data['message']}</font>")
            else:
                logger.emit(f"<font color='#22c55e'>[+] Localisation trouvée</font>")
                logger.emit(f"<font color='#e4e4e7'>    IP: {data.get('query')}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Pays: {data.get('country')} ({data.get('countryCode')})</font>")
                logger.emit(f"<font color='#e4e4e7'>    Région: {data.get('regionName')}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Ville: {data.get('city')}</font>")
                logger.emit(f"<font color='#e4e4e7'>    ZIP: {data.get('zip')}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Timezone: {data.get('timezone')}</font>")
                logger.emit(f"<font color='#e4e4e7'>    ISP: {data.get('isp')}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Org: {data.get('org')}</font>")
                logger.emit(f"<font color='#e4e4e7'>    AS: {data.get('as')}</font>")
                
                maps_url = f"https://www.google.com/maps/search/?api=1&query={data.get('lat')},{data.get('lon')}"
                logger.emit(f"<font color='#3b82f6'>    Maps: <a href='{maps_url}'>Ouvrir Google Maps</a></font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Erreur HTTP: {r.status_code}</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_reverse_dns(logger, user_input):
    ip = prepare_ip(user_input)
    if not ip: return
    
    logger.emit(f"<font color='#3b82f6'><b>[*] Reverse DNS pour {ip}...</b></font>")
    try:
        host = socket.gethostbyaddr(ip)
        logger.emit(f"<font color='#22c55e'>[+] Hostname: {host[0]}</font>")
        if len(host[1]) > 0:
            logger.emit(f"<font color='#e4e4e7'>    Alias: {', '.join(host[1])}</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Pas de PTR ou erreur: {e}</font>")

def logic_ping(logger, user_input):
    ip = prepare_ip(user_input)
    if not ip: return
    
    logger.emit(f"<font color='#3b82f6'><b>[*] Ping {ip}...</b></font>")
    param = '-n' if os.name == 'nt' else '-c'
    command = ['ping', param, '4', ip]
    
    try:
        kwargs = {}
        if os.name == 'nt':
            kwargs['creationflags'] = 0x08000000
            
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            logger.emit(f"<font color='#22c55e'>[+] Ping réussi.</font>")
            lines = stdout.splitlines()
            # Filter empty lines and display relevant ones
            for line in lines:
                if line.strip() and not line.startswith("Pinging") and not line.startswith("Envoi"):
                     logger.emit(f"<font color='#a1a1aa'>    {line.strip()}</font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Ping échoué.</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur exécution: {e}</font>")

def logic_port_scan(logger, user_input):
    ip = prepare_ip(user_input)
    if not ip: return
    
    logger.emit(f"<font color='#3b82f6'><b>[*] Scan de ports sur {ip} (Top Ports)...</b></font>")
    ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 3306, 3389, 5900, 8080, 8443]
    
    def check(p):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            res = s.connect_ex((ip, p))
            s.close()
            return p, res == 0
        except:
            return p, False

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(check, p): p for p in ports}
        for future in concurrent.futures.as_completed(futures):
            port, is_open = future.result()
            if is_open:
                logger.emit(f"<font color='#22c55e'>[+] Port {port} OUVERT</font>")
    
    logger.emit(f"<br><font color='#3b82f6'><b>[*] Scan terminé.</b></font>")

def logic_traceroute(logger, user_input):
    ip = prepare_ip(user_input)
    if not ip: 
        logger.emit("<font color='#ef4444'><b>[-] IP invalide.</b></font>")
        return
    
    logger.emit(f"<font color='#3b82f6'><b>[*] Traceroute vers {ip}...</b></font>")
    cmd = ['tracert', '-d', ip] if os.name == 'nt' else ['traceroute', '-n', ip]
    
    try:
        kwargs = {}
        if os.name == 'nt':
            kwargs['creationflags'] = 0x08000000
            
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, **kwargs)
        for line in process.stdout:
            if line.strip():
                logger.emit(f"<font color='#a1a1aa'>{line.strip()}</font>")
        process.wait()
        logger.emit(f"<font color='#22c55e'>[+] Traceroute terminé.</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_my_ip(logger):
    logger.emit(f"<font color='#3b82f6'><b>[*] Récupération de vos IPs...</b></font>")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        logger.emit(f"<font color='#22c55e'>[+] IP Locale: {local_ip}</font>")
    except:
        logger.emit(f"<font color='#ef4444'>[-] Impossible de trouver l'IP locale.</font>")
    
    try:
        pub_ip = requests.get("https://api.ipify.org", timeout=5).text
        logger.emit(f"<font color='#22c55e'>[+] IP Publique: {pub_ip}</font>")
    except:
        logger.emit(f"<font color='#ef4444'>[-] Impossible de trouver l'IP publique.</font>")

def logic_subnet_calc(logger, user_input):
    if not user_input:
        logger.emit("<font color='#ef4444'><b>[-] Entrée requise (ex: 192.168.1.0/24).</b></font>")
        return
    
    if "/" not in user_input:
        user_input += "/24"
        logger.emit(f"<font color='#a1a1aa'>[i] Ajout du masque par défaut /24</font>")

    logger.emit(f"<font color='#3b82f6'><b>[*] Calculateur de Sous-réseau ({user_input})...</b></font>")
    try:
        net = ipaddress.ip_network(user_input, strict=False)
        logger.emit(f"<font color='#e4e4e7'>    Réseau: {net.network_address}</font>")
        logger.emit(f"<font color='#e4e4e7'>    Masque: {net.netmask}</font>")
        logger.emit(f"<font color='#e4e4e7'>    Broadcast: {net.broadcast_address}</font>")
        logger.emit(f"<font color='#e4e4e7'>    Total IPs: {net.num_addresses}</font>")
        if net.num_addresses > 1:
            logger.emit(f"<font color='#e4e4e7'>    Plage: {list(net.hosts())[0]} - {list(net.hosts())[-1]}</font>")
    except ValueError as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur format: {e}</font>")

def logic_dns_lookup(logger, user_input):
    # Nettoyage de l'entrée pour nslookup
    clean_input = user_input.strip()
    if "://" in clean_input: 
        try: clean_input = urlparse(clean_input).netloc
        except: pass
    if "/" in clean_input: clean_input = clean_input.split('/')[0]
    
    if not clean_input:
        logger.emit("<font color='#ef4444'><b>[-] Entrée requise.</b></font>")
        return

    logger.emit(f"<font color='#3b82f6'><b>[*] DNS Lookup pour {clean_input}...</b></font>")
    cmd = ['nslookup', clean_input]
    try:
        kwargs = {}
        if os.name == 'nt': kwargs['creationflags'] = 0x08000000
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **kwargs)
        out, _ = process.communicate()
        for line in out.splitlines():
            if line.strip():
                logger.emit(f"<font color='#e4e4e7'>{line.strip()}</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_ip_convert(logger, user_input):
    ip = prepare_ip(user_input)
    if not ip: return
    
    logger.emit(f"<font color='#3b82f6'><b>[*] Conversion IP {ip}...</b></font>")
    try:
        ip_obj = ipaddress.ip_address(ip)
        logger.emit(f"<font color='#e4e4e7'>    Décimal: {int(ip_obj)}</font>")
        logger.emit(f"<font color='#e4e4e7'>    Binaire: {bin(int(ip_obj))}</font>")
        logger.emit(f"<font color='#e4e4e7'>    Hex: {hex(int(ip_obj))}</font>")
        if ip_obj.version == 4:
            logger.emit(f"<font color='#e4e4e7'>    IPv6 (Mapped): {ipaddress.IPv6Address('::ffff:' + ip)}</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_mac_lookup(logger, mac):
    if not mac: return
    logger.emit(f"<font color='#3b82f6'><b>[*] Recherche MAC Vendor pour {mac}...</b></font>")
    try:
        r = requests.get(f"https://api.macvendors.com/{mac}", timeout=5)
        if r.status_code == 200:
            logger.emit(f"<font color='#22c55e'>[+] Vendor: {r.text}</font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Introuvable ou Erreur API.</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_http_headers(logger, user_input):
    ip = prepare_ip(user_input)
    if not ip: return
    
    logger.emit(f"<font color='#3b82f6'><b>[*] Analyse HTTP Headers pour {ip}...</b></font>")
    try:
        # Try HTTP
        try:
            r = requests.head(f"http://{ip}", timeout=3)
            logger.emit(f"<font color='#22c55e'>[+] HTTP (80) - {r.status_code} {r.reason}</font>")
            for k, v in r.headers.items():
                logger.emit(f"<font color='#e4e4e7'>    {k}: {v}</font>")
        except:
            logger.emit(f"<font color='#a1a1aa'>[-] HTTP (80) inaccessible.</font>")

        # Try HTTPS
        try:
            r = requests.head(f"https://{ip}", timeout=3, verify=False)
            logger.emit(f"<font color='#22c55e'>[+] HTTPS (443) - {r.status_code} {r.reason}</font>")
            for k, v in r.headers.items():
                logger.emit(f"<font color='#e4e4e7'>    {k}: {v}</font>")
        except:
            logger.emit(f"<font color='#a1a1aa'>[-] HTTPS (443) inaccessible.</font>")
            
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_whois_rdap(logger, user_input):
    ip = prepare_ip(user_input)
    if not ip: return
    
    logger.emit(f"<font color='#3b82f6'><b>[*] Whois (RDAP) pour {ip}...</b></font>")
    try:
        r = requests.get(f"https://rdap.arin.net/registry/ip/{ip}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            logger.emit(f"<font color='#22c55e'>[+] Informations trouvées</font>")
            if 'name' in data: logger.emit(f"<font color='#e4e4e7'>    Nom Réseau: {data['name']}</font>")
            if 'handle' in data: logger.emit(f"<font color='#e4e4e7'>    Handle: {data['handle']}</font>")
            if 'startAddress' in data: logger.emit(f"<font color='#e4e4e7'>    Début Plage: {data['startAddress']}</font>")
            if 'endAddress' in data: logger.emit(f"<font color='#e4e4e7'>    Fin Plage: {data['endAddress']}</font>")
            if 'parentHandle' in data: logger.emit(f"<font color='#e4e4e7'>    Parent: {data['parentHandle']}</font>")
            logger.emit(f"<font color='#a1a1aa'>    (Source: ARIN RDAP)</font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Erreur RDAP: {r.status_code}</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

# --- Worker Thread ---

class Worker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, target, *args):
        super().__init__()
        self.target = target
        self.args = args

    def run(self):
        self.target(self.log_signal, *self.args)
        self.finished_signal.emit()

# --- Main Window ---

class IpToolWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(1000, 650)
        self.worker = None
        self.oldPos = self.pos()
        
        self.container = QFrame()
        self.container.setObjectName("MainContainer")
        self.setCentralWidget(self.container)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.container.setGraphicsEffect(shadow)
        
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- Title Bar ---
        self.title_bar = QFrame()
        self.title_bar.setObjectName("TitleBar")
        self.title_bar.setFixedHeight(40)
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(15, 0, 10, 0)
        
        title_label = QLabel("LE M // Ip Tool")
        title_label.setObjectName("TitleLabel")
        
        btn_min = QPushButton("─")
        btn_min.setObjectName("TitleBtn")
        btn_min.setFixedSize(30, 30)
        btn_min.clicked.connect(self.showMinimized)
        
        btn_close = QPushButton("✕")
        btn_close.setObjectName("TitleBtnClose")
        btn_close.setFixedSize(30, 30)
        btn_close.clicked.connect(self.close)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(btn_min)
        title_layout.addWidget(btn_close)
        
        self.main_layout.addWidget(self.title_bar)
        
        # --- Content ---
        content_layout = QHBoxLayout()
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # --- Left Panel ---
        left_panel = QFrame()
        left_panel.setObjectName("SidePanel")
        left_panel.setFixedWidth(320)
        
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(15, 20, 15, 20)

        self.menu_label = QLabel("IP Tool - LE M")
        self.menu_label.setObjectName("MenuLabel")
        self.menu_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.menu_label)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("IP / Domaine (vide = liste)")
        left_layout.addWidget(self.ip_input)

        self.btn_edit = QPushButton()
        self.btn_edit.setObjectName("FolderBtn")
        self.btn_edit.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        self.btn_edit.setFixedSize(40, 40)
        self.btn_edit.setToolTip("Ouvrir la liste des IP (ip.txt)")
        self.btn_edit.clicked.connect(self.open_ip_file)
        
        btn_layout = QHBoxLayout()
        lbl_list = QLabel("Liste IP :")
        lbl_list.setStyleSheet("color: #a1a1aa; font-weight: bold; font-size: 13px; margin-right: 5px;")
        btn_layout.addStretch()
        btn_layout.addWidget(lbl_list)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addStretch()
        left_layout.addLayout(btn_layout)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #333; max-height: 1px;")
        left_layout.addWidget(line)

        # Scroll Area for Buttons
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background: transparent; border: none;")

        self.stacked_widget = QStackedWidget()
        
        # --- Page Main ---
        page_main = QWidget()
        layout_main = QVBoxLayout(page_main)
        layout_main.setSpacing(8)
        layout_main.setContentsMargins(0, 0, 0, 0)
        
        btn_menu_info = QPushButton("📍  GeoIP / Info >")
        btn_menu_tools = QPushButton("🛠️  Network Tools >")
        btn_menu_utils = QPushButton("🧮  Utils / Générateur >")
        
        for btn in [btn_menu_info, btn_menu_tools, btn_menu_utils]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_main.addWidget(btn)
        layout_main.addStretch()
            
        # --- Page Info ---
        page_info = QWidget()
        layout_info = QVBoxLayout(page_info)
        layout_info.setSpacing(8)
        layout_info.setContentsMargins(0, 0, 0, 0)
        
        self.btn_geoip = QPushButton("📍  GeoIP Lookup")
        self.btn_rdns = QPushButton("🔄  Reverse DNS")
        self.btn_myip = QPushButton("🏠  Mon IP")
        self.btn_whois = QPushButton("📜  Whois (RDAP)")
        btn_back_info = QPushButton("⬅️  Retour")
        
        for btn in [self.btn_geoip, self.btn_rdns, self.btn_myip, self.btn_whois, btn_back_info]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_info.addWidget(btn)
        layout_info.addStretch()
            
        # --- Page Tools ---
        page_tools = QWidget()
        layout_tools = QVBoxLayout(page_tools)
        layout_tools.setSpacing(8)
        layout_tools.setContentsMargins(0, 0, 0, 0)
        
        self.btn_ping = QPushButton("🏓  Ping")
        self.btn_scan = QPushButton("🔍  Port Scan")
        self.btn_trace = QPushButton("👣  Traceroute")
        self.btn_dns = QPushButton("📖  DNS Lookup")
        self.btn_headers = QPushButton("🌐  HTTP Headers")
        btn_back_tools = QPushButton("⬅️  Retour")
        
        for btn in [self.btn_ping, self.btn_scan, self.btn_trace, self.btn_dns, self.btn_headers, btn_back_tools]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_tools.addWidget(btn)
        layout_tools.addStretch()

        # --- Page Utils ---
        page_utils = QWidget()
        layout_utils = QVBoxLayout(page_utils)
        layout_utils.setSpacing(8)
        layout_utils.setContentsMargins(0, 0, 0, 0)
        
        self.btn_gen = QPushButton("🎲  Générateur IP")
        self.btn_subnet = QPushButton("🧮  Calculateur Sous-réseau")
        self.btn_convert = QPushButton("🔢  Convertisseur IP")
        self.btn_mac = QPushButton("🏷️  MAC Vendor Lookup")
        btn_back_utils = QPushButton("⬅️  Retour")
        
        for btn in [self.btn_gen, self.btn_subnet, self.btn_convert, self.btn_mac, btn_back_utils]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_utils.addWidget(btn)
        layout_utils.addStretch()
            
        self.stacked_widget.addWidget(page_main)
        self.stacked_widget.addWidget(page_info)
        self.stacked_widget.addWidget(page_tools)
        self.stacked_widget.addWidget(page_utils)
        
        # Connect Actions
        self.btn_geoip.clicked.connect(lambda: self.start_task(logic_geoip, self.ip_input.text()))
        self.btn_rdns.clicked.connect(lambda: self.start_task(logic_reverse_dns, self.ip_input.text()))
        self.btn_ping.clicked.connect(lambda: self.start_task(logic_ping, self.ip_input.text()))
        self.btn_scan.clicked.connect(lambda: self.start_task(logic_port_scan, self.ip_input.text()))
        self.btn_myip.clicked.connect(lambda: self.start_task(logic_my_ip))
        self.btn_whois.clicked.connect(lambda: self.start_task(logic_whois_rdap, self.ip_input.text()))
        self.btn_trace.clicked.connect(lambda: self.start_task(logic_traceroute, self.ip_input.text()))
        self.btn_gen.clicked.connect(self.action_gen_ip)
        self.btn_subnet.clicked.connect(lambda: self.start_task(logic_subnet_calc, self.ip_input.text()))
        self.btn_dns.clicked.connect(lambda: self.start_task(logic_dns_lookup, self.ip_input.text()))
        self.btn_convert.clicked.connect(lambda: self.start_task(logic_ip_convert, self.ip_input.text()))
        self.btn_headers.clicked.connect(lambda: self.start_task(logic_http_headers, self.ip_input.text()))
        self.btn_mac.clicked.connect(self.action_mac_lookup)
        
        # Navigation
        btn_menu_info.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        btn_menu_tools.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        btn_menu_utils.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        btn_back_info.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_back_tools.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_back_utils.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        scroll_area.setWidget(self.stacked_widget)
        left_layout.addWidget(scroll_area)

        self.btn_clear = QPushButton("🧹  Effacer Console")
        self.btn_clear.setObjectName("ClearBtn")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear_logs)
        left_layout.addWidget(self.btn_clear)

        btn_back = QPushButton("⬅️  Retour")
        btn_back.setObjectName("ExitBtn")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(self.close)
        left_layout.addWidget(btn_back)

        # --- Right Panel ---
        right_panel = QWidget()
        right_panel.setObjectName("RightPanel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_frame.setFixedHeight(50)
        header_layout = QHBoxLayout(header_frame)
        term_label = QLabel("SORTIE TERMINAL")
        term_label.setObjectName("HeaderLabel")
        header_layout.addWidget(term_label)
        header_layout.addStretch()
        right_layout.addWidget(header_frame)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        right_layout.addWidget(self.console)

        self.status_bar = QFrame()
        self.status_bar.setObjectName("StatusBar")
        self.status_bar.setFixedHeight(30)
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(10, 0, 10, 0)
        
        self.status_label = QLabel("Système Prêt")
        self.status_label.setObjectName("StatusLabel")
        status_layout.addWidget(self.status_label)
        
        right_layout.addWidget(self.status_bar)

        content_layout.addWidget(left_panel)
        content_layout.addWidget(right_panel)
        self.main_layout.addLayout(content_layout)

        self.apply_styles()

        self.setWindowOpacity(0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(500)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)
        self.anim.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: transparent; }
            QFrame#MainContainer { background-color: #09090b; border: 1px solid #27272a; border-radius: 12px; }
            QFrame#SidePanel { background-color: #101012; border-right: 1px solid #27272a; border-bottom-left-radius: 12px; }
            QFrame#HeaderFrame { background-color: #101012; border-bottom: 1px solid #27272a; }
            QFrame#TitleBar { background-color: #101012; border-bottom: 1px solid #27272a; border-top-left-radius: 12px; border-top-right-radius: 12px; }
            QLabel#TitleLabel { color: #71717a; font-family: 'Consolas'; font-weight: bold; font-size: 12px; }
            QPushButton#TitleBtn, QPushButton#TitleBtnClose { background-color: transparent; border: none; color: #71717a; font-weight: bold; font-size: 14px; padding: 0; }
            QPushButton#TitleBtn:hover { color: #fff; }
            QPushButton#TitleBtnClose:hover { color: #ef4444; }
            QLabel#HeaderLabel { color: #71717a; font-weight: bold; letter-spacing: 1px; padding-left: 10px; }
            QFrame#StatusBar { background-color: #101012; border-top: 1px solid #27272a; border-bottom-right-radius: 12px; }
            QLabel#StatusLabel { color: #52525b; font-size: 12px; }
            QLineEdit { background-color: #27272a; border: 1px solid #27272a; border-radius: 8px; padding: 12px; color: #f4f4f5; font-family: 'Consolas', monospace; font-size: 14px; }
            QLineEdit:focus { border: 1px solid #6366f1; background-color: #202023; }
            QPushButton { background-color: #18181b; border: 1px solid #27272a; border-radius: 8px; padding: 12px 20px; color: #e4e4e7; font-weight: 600; text-align: left; }
            QPushButton:hover { background-color: #27272a; border-color: #3f3f46; color: #ffffff; }
            QPushButton:pressed { background-color: #3f3f46; }
            QPushButton#ActionBtn { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #7c3aed); border: 1px solid #6366f1; color: #ffffff; text-align: center; }
            QPushButton#ActionBtn:hover { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4338ca, stop:1 #6d28d9); border: 1px solid #818cf8; }
            QPushButton#ExitBtn { background-color: #18181b; border: 1px solid #ef4444; color: #ef4444; text-align: center; }
            QPushButton#ExitBtn:hover { background-color: #ef4444; color: #fff; }
            QPushButton#ClearBtn { text-align: center; }
            QPushButton#FolderBtn { text-align: center; padding: 0; }
            QTextEdit { background-color: #000000; border: none; color: #22c55e; font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; padding: 20px; line-height: 1.5; border-bottom-right-radius: 12px; }
            QLabel#MenuLabel { font-size: 16px; font-weight: 800; color: #6366f1; padding: 10px 0; letter-spacing: 1px; }
            QScrollBar:vertical { border: none; background: #101012; width: 8px; margin: 0px; }
            QScrollBar::handle:vertical { background: #3f3f46; min-height: 20px; border-radius: 4px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

    def log_message(self, message):
        self.console.append(message)
        sb = self.console.verticalScrollBar()
        sb.setValue(sb.maximum())

    def open_ip_file(self):
        if not os.path.exists('input'):
            os.makedirs('input')
        if not os.path.exists('input/ip.txt') or os.path.getsize('input/ip.txt') == 0:
            with open('input/ip.txt', 'w') as f:
                f.write("8.8.8.8\n1.1.1.1\n# Mettez vos IP ici, une par ligne")
        
        try:
            if os.name == 'nt':
                os.startfile(os.path.abspath('input/ip.txt'))
            else:
                subprocess.call(['xdg-open', 'input/ip.txt'])
        except Exception as e:
            self.log_message(f"<font color='#ef4444'>[-] Erreur ouverture fichier: {e}</font>")

    def clear_logs(self):
        self.console.clear()

    def action_gen_ip(self):
        ip = ".".join(str(random.randint(0, 255)) for _ in range(4))
        self.ip_input.setText(ip)
        self.log_message(f"<font color='#3b82f6'><b>[*] IP Aléatoire générée: {ip}</b></font>")

    def action_mac_lookup(self):
        mac, ok = QInputDialog.getText(self, "MAC Lookup", "Adresse MAC (ex: 00:11:22:33:44:55):")
        if ok and mac:
            self.start_task(logic_mac_lookup, mac)

    def start_task(self, func, *args):
        if self.worker and self.worker.isRunning():
            self.log_message("<font color='#ef4444'>[-] Une tâche est déjà en cours.</font>")
            return

        self.status_label.setText("Traitement en cours...")
        self.worker = Worker(func, *args)
        self.worker.log_signal.connect(self.log_message)
        self.worker.finished_signal.connect(self.task_finished)
        self.worker.start()

    def task_finished(self):
        self.status_label.setText("Système Prêt")
        self.log_message("<font color='#3f3f46'>----------------------------------------</font>")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IpToolWindow()
    window.show()
    sys.exit(app.exec_())