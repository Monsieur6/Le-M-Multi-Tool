import sys
import os
import requests
import threading
import time
import json
import random
import string
import concurrent.futures
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QFrame, QGraphicsDropShadowEffect, 
                             QScrollArea, QInputDialog, QMessageBox, QStyle, QStackedWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QCursor

WEBHOOK_FILE = 'input/webhook.txt'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}

# --- Logic Functions ---

def load_webhooks():
    if not os.path.exists('input'):
        os.makedirs('input')
    if os.path.exists(WEBHOOK_FILE):
        with open(WEBHOOK_FILE, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    else:
        with open(WEBHOOK_FILE, 'w') as f:
            f.write("https://discord.com/api/webhooks/...\n# Mettez vos Webhooks ici, un par ligne")
        return []

def logic_webhook_info(logger, url_input):
    urls = [url_input] if url_input else load_webhooks()
    if not urls:
        logger.emit("<font color='#ef4444'>[-] Aucun Webhook fourni.</font>")
        return

    logger.emit(f"<font color='#3b82f6'><b>[*] Analyse de {len(urls)} Webhook(s)...</b></font>")
    
    for url in urls:
        try:
            res = requests.get(url, headers=HEADERS)
            if res.status_code == 200:
                info = res.json()
                logger.emit(f"<font color='#22c55e'>[+] VALIDE: {info.get('name', 'N/A')}</font>")
                logger.emit(f"<font color='#e4e4e7'>    ID: {info.get('id')}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Token: {info.get('token')[:20]}...</font>")
                logger.emit(f"<font color='#e4e4e7'>    Serveur ID: {info.get('guild_id', 'N/A')}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Salon ID: {info.get('channel_id', 'N/A')}</font>")
                if 'user' in info:
                    logger.emit(f"<font color='#e4e4e7'>    Créateur: {info['user']['username']} (ID: {info['user']['id']})</font>")
            else:
                logger.emit(f"<font color='#ef4444'>[-] INVALIDE ({res.status_code}): {url[:30]}...</font>")
        except Exception as e:
            logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_webhook_delete(logger, url_input):
    if not url_input:
        logger.emit("<font color='#ef4444'>[-] Veuillez entrer une URL de Webhook pour la suppression.</font>")
        return

    logger.emit(f"<font color='#ef4444'><b>[*] Tentative de suppression...</b></font>")
    try:
        res = requests.delete(url_input, headers=HEADERS)
        if res.status_code in [204, 200]:
            logger.emit(f"<font color='#22c55e'>[+] Webhook supprimé avec succès !</font>")
        elif res.status_code == 404:
            logger.emit(f"<font color='#ef4444'>[-] Webhook introuvable (déjà supprimé ?).</font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Échec de la suppression (Code {res.status_code}).</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_webhook_spam(logger, url_input, message, count):
    if not url_input or not message: return
    
    logger.emit(f"<font color='#3b82f6'><b>[*] Spam de {count} messages...</b></font>")
    
    def send_msg(i):
        try:
            res = requests.post(url_input, json={'content': message}, headers=HEADERS)
            if res.status_code in [200, 204]:
                return True
            elif res.status_code == 429:
                time.sleep(float(res.json().get('retry_after', 1)))
                return False
            else:
                return False
        except:
            return False

    success_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(send_msg, i) for i in range(int(count))]
        for future in concurrent.futures.as_completed(futures):
            if future.result(): success_count += 1
            
    logger.emit(f"<font color='#22c55e'>[+] Terminé: {success_count}/{count} messages envoyés.</font>")

def logic_generator(logger, count):
    logger.emit(f"<font color='#3b82f6'><b>[*] Génération et test de {count} Webhooks (Bruteforce)...</b></font>")
    logger.emit(f"<font color='#a1a1aa'>Note: La probabilité de trouver un webhook valide est extrêmement faible.</font>")
    
    valid_found = 0
    
    def check_random():
        # ID is usually 18-19 digits, Token is ~68 chars
        w_id = ''.join(random.choices(string.digits, k=19))
        w_token = ''.join(random.choices(string.ascii_letters + string.digits + '-' + '_', k=68))
        url = f"https://discord.com/api/webhooks/{w_id}/{w_token}"
        
        try:
            res = requests.head(url, timeout=2, headers=HEADERS)
            if res.status_code == 200:
                return url
        except:
            pass
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(check_random) for _ in range(int(count))]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                logger.emit(f"<font color='#22c55e'>[!!!] TROUVÉ: {res}</font>")
                valid_found += 1
            
    if valid_found == 0:
        logger.emit(f"<font color='#ef4444'>[-] Aucun webhook valide trouvé dans ce lot.</font>")

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

class WebhookToolWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(1000, 650)
        self.worker = None
        self.oldPos = self.pos()
        
        # Main Container
        self.container = QFrame()
        self.container.setObjectName("MainContainer")
        self.setCentralWidget(self.container)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.container.setGraphicsEffect(shadow)
        
        # Layout
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- Title Bar ---
        self.title_bar = QFrame()
        self.title_bar.setObjectName("TitleBar")
        self.title_bar.setFixedHeight(40)
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(15, 0, 10, 0)
        
        title_label = QLabel("LE M // Webhook Tool")
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
        left_layout.setSpacing(5)
        left_layout.setContentsMargins(15, 20, 15, 20)

        self.menu_label = QLabel("Webhook Tool - LE M")
        self.menu_label.setObjectName("MenuLabel")
        self.menu_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.menu_label)

        # Inputs
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Webhook URL (vide = utiliser liste)")
        left_layout.addWidget(self.url_input)

        self.btn_edit = QPushButton()
        self.btn_edit.setObjectName("FolderBtn")
        self.btn_edit.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        self.btn_edit.setFixedSize(40, 40)
        self.btn_edit.setToolTip("Ouvrir le fichier webhook.txt")
        self.btn_edit.clicked.connect(self.open_webhook_file)
        
        btn_layout = QHBoxLayout()
        lbl_list = QLabel("Liste Webhook :")
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
        layout_main.setSpacing(2)
        layout_main.setContentsMargins(0, 0, 0, 0)
        
        self.btn_info = QPushButton("🔍  Infos Webhook")
        btn_menu_actions = QPushButton("⚡  Actions >")
        self.btn_gen = QPushButton("🎲  Générateur (Brute)")
        
        for btn in [self.btn_info, btn_menu_actions, self.btn_gen]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_main.addWidget(btn)
        layout_main.addStretch()
            
        # --- Page Actions ---
        page_actions = QWidget()
        layout_actions = QVBoxLayout(page_actions)
        layout_actions.setSpacing(2)
        layout_actions.setContentsMargins(0, 0, 0, 0)
        
        self.btn_del = QPushButton("🗑️  Supprimer Webhook")
        self.btn_spam = QPushButton("📢  Spammer Webhook")
        btn_back_actions = QPushButton("⬅️  Retour")
        
        for btn in [self.btn_del, self.btn_spam, btn_back_actions]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_actions.addWidget(btn)
        layout_actions.addStretch()
            
        self.stacked_widget.addWidget(page_main)
        self.stacked_widget.addWidget(page_actions)
        
        # Connect Actions
        self.btn_info.clicked.connect(lambda: self.start_task(logic_webhook_info, self.url_input.text()))
        self.btn_del.clicked.connect(self.action_delete)
        self.btn_spam.clicked.connect(self.action_spam)
        self.btn_gen.clicked.connect(self.action_gen)
        
        # Navigation
        btn_menu_actions.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        btn_back_actions.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

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

    def clear_logs(self):
        self.console.clear()

    def open_webhook_file(self):
        if not os.path.exists('input'):
            os.makedirs('input')
        if not os.path.exists(WEBHOOK_FILE) or os.path.getsize(WEBHOOK_FILE) == 0:
            with open(WEBHOOK_FILE, 'w') as f:
                f.write("https://discord.com/api/webhooks/...\n# Mettez vos Webhooks ici, un par ligne")
        
        try:
            if os.name == 'nt':
                os.startfile(os.path.abspath(WEBHOOK_FILE))
            else:
                subprocess.call(['xdg-open', WEBHOOK_FILE])
        except Exception as e:
            self.log_message(f"<font color='#ef4444'>[-] Erreur ouverture fichier: {e}</font>")

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

    # --- Actions ---

    def action_delete(self):
        url = self.url_input.text().strip()
        if not url:
            self.log_message("<font color='#ef4444'>[-] URL requise pour la suppression.</font>")
            return
        
        confirm = QMessageBox.warning(self, "Attention", "Voulez-vous vraiment SUPPRIMER ce webhook ?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.start_task(logic_webhook_delete, url)

    def action_spam(self):
        url = self.url_input.text().strip()
        if not url:
            self.log_message("<font color='#ef4444'>[-] URL requise pour le spam.</font>")
            return
        
        msg, ok = QInputDialog.getText(self, "Spam", "Message à envoyer :")
        if ok and msg:
            count, ok2 = QInputDialog.getInt(self, "Spam", "Nombre de messages :", 10, 1, 1000)
            if ok2:
                self.start_task(logic_webhook_spam, url, msg, count)

    def action_gen(self):
        count, ok = QInputDialog.getInt(self, "Générateur", "Nombre de tentatives :", 100, 1, 100000)
        if ok:
            self.start_task(logic_generator, count)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WebhookToolWindow()
    window.show()
    sys.exit(app.exec_())
