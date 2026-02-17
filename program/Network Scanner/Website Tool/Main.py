import sys
import os
import socket
import subprocess
import requests
import urllib3
import ssl
import random
from urllib.parse import urlparse
import concurrent.futures
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QFrame, QGraphicsDropShadowEffect,
                             QScrollArea, QStyle, QStackedWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QCursor

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}

# --- Helper Functions ---

def prepare_target(url_input):
    url_input = url_input.strip()
    if not url_input: return None, None
    if url_input.startswith("http://") or url_input.startswith("https://"):
        parsed = urlparse(url_input)
        domain = parsed.netloc
        base_url = f"{parsed.scheme}://{domain}"
    else:
        domain = url_input.split('/')[0]
        base_url = f"http://{domain}"
    return domain, base_url

# --- Logic Functions ---

def logic_general_info(logger, url_input):
    domain, base_url = prepare_target(url_input)
    if not domain:
        logger.emit(f"<font color='#ef4444'><b>[-] URL invalide.</b></font>")
        return

    logger.emit(f"<font color='#3b82f6'><b>[*] Analyse générale de {domain}...</b></font>")
    try:
        ip = socket.gethostbyname(domain)
        logger.emit(f"<font color='#e4e4e7'>Adresse IP: {ip}</font>")
        
        res = requests.get(base_url, timeout=5, verify=False, headers=HEADERS)
        logger.emit(f"<font color='#e4e4e7'>Code Statut: {res.status_code} {res.reason}</font>")
        logger.emit(f"<font color='#e4e4e7'>Serveur: {res.headers.get('Server', 'Inconnu')}</font>")
        logger.emit(f"<font color='#e4e4e7'>Technologie: {res.headers.get('X-Powered-By', 'Inconnue')}</font>")
        logger.emit(f"<font color='#22c55e'>[+] Site accessible</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_http_headers(logger, url_input):
    domain, base_url = prepare_target(url_input)
    if not domain: return

    logger.emit(f"<font color='#3b82f6'><b>[*] Récupération des En-têtes HTTP...</b></font>")
    try:
        res = requests.head(base_url, timeout=5, verify=False, headers=HEADERS)
        for k, v in res.headers.items():
            logger.emit(f"<font color='#e4e4e7'><b>{k}</b>: {v}</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_ssl_check(logger, url_input):
    domain, _ = prepare_target(url_input)
    if not domain: return

    logger.emit(f"<font color='#3b82f6'><b>[*] Vérification Certificat SSL...</b></font>")
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(5)
            s.connect((domain, 443))
            cert = s.getpeercert()
            
            subject = dict(x[0] for x in cert['subject'])
            issuer = dict(x[0] for x in cert['issuer'])
            not_after = cert['notAfter']
            
            logger.emit(f"<font color='#22c55e'>[+] Certificat SSL Valide</font>")
            logger.emit(f"<font color='#e4e4e7'>Délivré à: {subject.get('commonName', 'N/A')}</font>")
            logger.emit(f"<font color='#e4e4e7'>Émis par: {issuer.get('commonName', 'N/A')}</font>")
            logger.emit(f"<font color='#e4e4e7'>Expire le: {not_after}</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur SSL (ou pas de HTTPS): {e}</font>")

def logic_robots_scan(logger, url_input):
    domain, base_url = prepare_target(url_input)
    if not domain: return

    logger.emit(f"<font color='#3b82f6'><b>[*] Recherche robots.txt...</b></font>")
    try:
        target = f"{base_url}/robots.txt"
        res = requests.get(target, timeout=5, verify=False, headers=HEADERS)
        if res.status_code == 200:
            logger.emit(f"<font color='#22c55e'>[+] robots.txt trouvé !</font>")
            lines = res.text.splitlines()
            for line in lines[:10]:
                if line.strip(): logger.emit(f"<font color='#a1a1aa'>    {line.strip()}</font>")
            if len(lines) > 10: logger.emit(f"<font color='#a1a1aa'>    ... (tronqué)</font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Pas de robots.txt (Code: {res.status_code})</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_admin_finder(logger, url_input):
    domain, base_url = prepare_target(url_input)
    if not domain: return

    logger.emit(f"<font color='#3b82f6'><b>[*] Recherche de pages d'administration (Rapide)...</b></font>")
    paths = ["admin", "login", "wp-admin", "dashboard", "cpanel", "user", "administrator", "phpmyadmin", "admin.php", "login.php"]
    found = False
    
    def check_url(path):
        try:
            target = f"{base_url}/{path}"
            res = requests.get(target, timeout=3, verify=False, headers=HEADERS)
            return path, res.status_code
        except:
            return path, None

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_url, p): p for p in paths}
        for future in concurrent.futures.as_completed(futures):
            path, status = future.result()
            if status == 200:
                logger.emit(f"<font color='#22c55e'>[+] Trouvé: /{path} (200 OK)</font>")
                found = True
            elif status == 403:
                logger.emit(f"<font color='#e4e4e7'>[!] Protégé: /{path} (403 Forbidden)</font>")
                found = True
            elif status in [301, 302]:
                logger.emit(f"<font color='#e4e4e7'>[>] Redirection: /{path} ({status})</font>")
                found = True

    if not found:
        logger.emit(f"<font color='#ef4444'>[-] Aucune page admin standard trouvée.</font>")
    else:
        logger.emit(f"<br><font color='#3b82f6'><b>[*] Scan terminé.</b></font>")

def logic_cms_detect(logger, url_input):
    domain, base_url = prepare_target(url_input)
    if not domain: return

    logger.emit(f"<font color='#3b82f6'><b>[*] Détection du CMS...</b></font>")
    try:
        res = requests.get(base_url, timeout=5, verify=False, headers=HEADERS)
        content = res.text.lower()
        
        detected = []
        if "wp-content" in content or "wordpress" in content: detected.append("WordPress")
        if "joomla" in content: detected.append("Joomla")
        if "drupal" in content: detected.append("Drupal")
        if "shopify" in content: detected.append("Shopify")
        if "wix" in content: detected.append("Wix")
        if "prestashop" in content: detected.append("PrestaShop")
        
        if detected:
            logger.emit(f"<font color='#22c55e'>[+] CMS Détecté: {', '.join(detected)}</font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Aucun CMS populaire détecté.</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_port_scan_web(logger, url_input):
    domain, _ = prepare_target(url_input)
    if not domain: return

    logger.emit(f"<font color='#3b82f6'><b>[*] Scan des ports Web sur {domain} (Rapide)...</b></font>")
    try:
        ip = socket.gethostbyname(domain)
        ports = [21, 22, 80, 443, 3306, 8080, 8443]
        
        def check_port(target_ip, target_port):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                res = s.connect_ex((target_ip, target_port))
                s.close()
                return target_port, res == 0
            except:
                return target_port, False

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(check_port, ip, p): p for p in ports}
            for future in concurrent.futures.as_completed(futures):
                port, is_open = future.result()
                if is_open:
                    logger.emit(f"<font color='#22c55e'>[+] Port {port} OUVERT</font>")

        logger.emit(f"<br><font color='#3b82f6'><b>[*] Scan terminé.</b></font>")
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

class WebsiteToolWindow(QMainWindow):
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
        
        title_label = QLabel("LE M // Website Tool")
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

        self.menu_label = QLabel("Website Tool - LE M")
        self.menu_label.setObjectName("MenuLabel")
        self.menu_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.menu_label)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("URL (vide = utiliser liste)")
        left_layout.addWidget(self.url_input)

        self.btn_edit = QPushButton()
        self.btn_edit.setObjectName("FolderBtn")
        self.btn_edit.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        self.btn_edit.setFixedSize(40, 40)
        self.btn_edit.setToolTip("Ouvrir la liste des sites (website.txt)")
        self.btn_edit.clicked.connect(self.open_website_file)
        
        btn_layout = QHBoxLayout()
        lbl_list = QLabel("Liste Site Web :")
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
        
        btn_menu_analyse = QPushButton("🔍  Analyse >")
        btn_menu_scan = QPushButton("🛡️  Scanners >")
        
        for btn in [btn_menu_analyse, btn_menu_scan]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_main.addWidget(btn)
        layout_main.addStretch()
            
        # --- Page Analyse ---
        page_analyse = QWidget()
        layout_analyse = QVBoxLayout(page_analyse)
        layout_analyse.setSpacing(8)
        layout_analyse.setContentsMargins(0, 0, 0, 0)
        
        self.btn_info = QPushButton("🔍  Infos Générales")
        self.btn_headers = QPushButton("📋  Headers HTTP")
        self.btn_ssl = QPushButton("🔒  Check SSL")
        self.btn_cms = QPushButton("🧩  Détection CMS")
        self.btn_robots = QPushButton("🤖  Robots.txt")
        btn_back_analyse = QPushButton("⬅️  Retour")
        
        for btn in [self.btn_info, self.btn_headers, self.btn_ssl, self.btn_cms, self.btn_robots, btn_back_analyse]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_analyse.addWidget(btn)
        layout_analyse.addStretch()
            
        # --- Page Scan ---
        page_scan = QWidget()
        layout_scan = QVBoxLayout(page_scan)
        layout_scan.setSpacing(8)
        layout_scan.setContentsMargins(0, 0, 0, 0)
        
        self.btn_admin = QPushButton("🔑  Admin Finder")
        self.btn_ports = QPushButton("🛡️  Ports Web")
        btn_back_scan = QPushButton("⬅️  Retour")
        
        for btn in [self.btn_admin, self.btn_ports, btn_back_scan]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_scan.addWidget(btn)
        layout_scan.addStretch()
            
        self.stacked_widget.addWidget(page_main)
        self.stacked_widget.addWidget(page_analyse)
        self.stacked_widget.addWidget(page_scan)
        
        self.btn_info.clicked.connect(lambda: self.start_task(logic_general_info, self.url_input.text().strip()))
        self.btn_headers.clicked.connect(lambda: self.start_task(logic_http_headers, self.url_input.text().strip()))
        self.btn_ssl.clicked.connect(lambda: self.start_task(logic_ssl_check, self.url_input.text().strip()))
        self.btn_cms.clicked.connect(lambda: self.start_task(logic_cms_detect, self.url_input.text().strip()))
        self.btn_admin.clicked.connect(lambda: self.start_task(logic_admin_finder, self.url_input.text().strip()))
        self.btn_robots.clicked.connect(lambda: self.start_task(logic_robots_scan, self.url_input.text().strip()))
        self.btn_ports.clicked.connect(lambda: self.start_task(logic_port_scan_web, self.url_input.text().strip()))
        
        # Navigation
        btn_menu_analyse.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        btn_menu_scan.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        btn_back_analyse.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_back_scan.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

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

    def open_website_file(self):
        if not os.path.exists('input'):
            os.makedirs('input')
        if not os.path.exists('input/website.txt') or os.path.getsize('input/website.txt') == 0:
            with open('input/website.txt', 'w') as f:
                f.write("google.com\nhttps://example.com\n# Mettez vos sites ici, un par ligne")
        
        try:
            if os.name == 'nt':
                os.startfile(os.path.abspath('input/website.txt'))
            else:
                subprocess.call(['xdg-open', 'input/website.txt'])
        except Exception as e:
            self.log_message(f"<font color='#ef4444'>[-] Erreur ouverture fichier: {e}</font>")

    def clear_logs(self):
        self.console.clear()

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
    window = WebsiteToolWindow()
    window.show()
    sys.exit(app.exec_())