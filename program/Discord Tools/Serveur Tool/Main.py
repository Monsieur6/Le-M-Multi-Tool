import sys
import os
import requests
import threading
import time
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QFrame, QGraphicsDropShadowEffect, 
                             QScrollArea, QInputDialog, QMessageBox, QStyle, QStackedWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QCursor

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}

# --- Logic Functions ---

def resolve_id(input_val):
    if not input_val: return None
    if input_val.isdigit(): return input_val
    # Try invite resolve
    code = input_val.split('/')[-1]
    try:
        r = requests.get(f"https://discord.com/api/v9/invites/{code}", headers=HEADERS)
        if r.status_code == 200:
            return r.json().get('guild', {}).get('id')
    except: pass
    return None

def logic_invite_info(logger, invite_input):
    if not invite_input:
        logger.emit("<font color='#ef4444'>[-] Veuillez entrer un lien d'invitation ou un code.</font>")
        return

    code = invite_input.split('/')[-1]
    logger.emit(f"<font color='#3b82f6'><b>[*] Analyse de l'invitation {code}...</b></font>")
    
    try:
        res = requests.get(f"https://discord.com/api/v9/invites/{code}?with_counts=true&with_expiration=true", headers=HEADERS)
        if res.status_code == 200:
            data = res.json()
            guild = data.get('guild', {})
            inviter = data.get('inviter', {})
            channel = data.get('channel', {})
            
            logger.emit(f"<font color='#22c55e'>[+] Invitation Valide</font>")
            logger.emit(f"<font color='#e4e4e7'>--- Serveur ---</font>")
            logger.emit(f"<font color='#e4e4e7'>Nom: {guild.get('name', 'N/A')}</font>")
            logger.emit(f"<font color='#e4e4e7'>ID: {guild.get('id', 'N/A')}</font>")
            logger.emit(f"<font color='#e4e4e7'>Description: {guild.get('description', 'Aucune')}</font>")
            logger.emit(f"<font color='#e4e4e7'>Membres: {data.get('approximate_member_count', 'N/A')} (En ligne: {data.get('approximate_presence_count', 'N/A')})</font>")
            logger.emit(f"<font color='#e4e4e7'>Niveau NSFW: {guild.get('nsfw_level', 'N/A')}</font>")
            logger.emit(f"<font color='#e4e4e7'>Boosts: {guild.get('premium_subscription_count', 0)}</font>")
            features = guild.get('features', [])
            if features:
                logger.emit(f"<font color='#e4e4e7'>Fonctionnalités: {', '.join(features[:5])}...</font>")
            
            if inviter:
                logger.emit(f"<br><font color='#e4e4e7'>--- Inviteur ---</font>")
                logger.emit(f"<font color='#e4e4e7'>Pseudo: {inviter.get('username')}#{inviter.get('discriminator')}</font>")
                logger.emit(f"<font color='#e4e4e7'>ID: {inviter.get('id')}</font>")
            
            if channel:
                logger.emit(f"<br><font color='#e4e4e7'>--- Salon ---</font>")
                logger.emit(f"<font color='#e4e4e7'>Nom: {channel.get('name')}</font>")
                logger.emit(f"<font color='#e4e4e7'>ID: {channel.get('id')}</font>")
                logger.emit(f"<font color='#e4e4e7'>Type: {channel.get('type')}</font>")
                
            if data.get('expires_at'):
                logger.emit(f"<font color='#ef4444'>Expire le: {data.get('expires_at')}</font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Invitation Invalide ou Expirée (Code {res.status_code})</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_widget_info(logger, input_val):
    if not input_val:
        logger.emit("<font color='#ef4444'>[-] Invitation ou ID Serveur requis.</font>")
        return

    guild_id = input_val
    # Si ce n'est pas un ID (chiffres), on essaie de résoudre l'invitation
    if not input_val.isdigit():
        code = input_val.split('/')[-1]
        try:
            r = requests.get(f"https://discord.com/api/v9/invites/{code}", headers=HEADERS)
            if r.status_code == 200:
                guild_id = r.json().get('guild', {}).get('id')
                logger.emit(f"<font color='#a1a1aa'>[i] ID résolu depuis l'invitation: {guild_id}</font>")
            else:
                logger.emit("<font color='#ef4444'>[-] Impossible de résoudre l'invitation pour obtenir l'ID.</font>")
                return
        except:
            return

    logger.emit(f"<font color='#3b82f6'><b>[*] Recherche Widget pour {guild_id}...</b></font>")
    try:
        res = requests.get(f"https://discord.com/api/guilds/{guild_id}/widget.json", headers=HEADERS)
        if res.status_code == 200:
            data = res.json()
            logger.emit(f"<font color='#22c55e'>[+] Widget Trouvé !</font>")
            logger.emit(f"<font color='#e4e4e7'>Nom: {data.get('name', 'N/A')}</font>")
            logger.emit(f"<font color='#e4e4e7'>Lien Instantané: {data.get('instant_invite', 'N/A')}</font>")
            logger.emit(f"<font color='#e4e4e7'>Membres en ligne: {data.get('presence_count', 0)}</font>")
            
            members = data.get('members', [])
            if members:
                logger.emit(f"<font color='#e4e4e7'>Exemple de membres:</font>")
                for m in members[:10]:
                    logger.emit(f"<font color='#a1a1aa'>- {m.get('username')} ({m.get('status')})</font>")
        elif res.status_code == 403:
            logger.emit(f"<font color='#ef4444'>[-] Widget désactivé sur ce serveur.</font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Erreur ou serveur introuvable ({res.status_code})</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_download_assets(logger, invite_input, asset_type):
    if not invite_input:
        logger.emit("<font color='#ef4444'>[-] Lien d'invitation requis pour récupérer les assets.</font>")
        return

    code = invite_input.split('/')[-1]
    try:
        res = requests.get(f"https://discord.com/api/v9/invites/{code}", headers=HEADERS)
        if res.status_code == 200:
            guild = res.json().get('guild', {})
            guild_id = guild.get('id')
            
            url = ""
            filename = ""
            
            if asset_type == "icon":
                icon_hash = guild.get('icon')
                if not icon_hash:
                    logger.emit("<font color='#ef4444'>[-] Ce serveur n'a pas d'icône.</font>")
                    return
                ext = "gif" if icon_hash.startswith("a_") else "png"
                url = f"https://cdn.discordapp.com/icons/{guild_id}/{icon_hash}.{ext}?size=1024"
                filename = f"icon_{guild_id}.{ext}"
                
            elif asset_type == "banner":
                banner_hash = guild.get('banner')
                if not banner_hash:
                    logger.emit("<font color='#ef4444'>[-] Ce serveur n'a pas de bannière.</font>")
                    return
                ext = "gif" if banner_hash.startswith("a_") else "png"
                url = f"https://cdn.discordapp.com/banners/{guild_id}/{banner_hash}.{ext}?size=1024"
                filename = f"banner_{guild_id}.{ext}"
                
            elif asset_type == "splash":
                splash_hash = guild.get('splash')
                if not splash_hash:
                    logger.emit("<font color='#ef4444'>[-] Ce serveur n'a pas de splash.</font>")
                    return
                url = f"https://cdn.discordapp.com/splashes/{guild_id}/{splash_hash}.png?size=1024"
                filename = f"splash_{guild_id}.png"

            if url:
                logger.emit(f"<font color='#3b82f6'><b>[*] Téléchargement de {filename}...</b></font>")
                r = requests.get(url, headers=HEADERS)
                if r.status_code == 200:
                    output_dir = os.path.join('output', 'Server Assets')
                    if not os.path.exists(output_dir): os.makedirs(output_dir)
                    path = os.path.join(output_dir, filename)
                    with open(path, 'wb') as f:
                        f.write(r.content)
                    logger.emit(f"<font color='#22c55e'>[+] Sauvegardé dans {path}</font>")
                else:
                    logger.emit(f"<font color='#ef4444'>[-] Erreur téléchargement ({r.status_code})</font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Invitation invalide.</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_deep_info(logger, token, input_val):
    if not token:
        logger.emit("<font color='#ef4444'>[-] Token requis pour cette option.</font>")
        return
    gid = resolve_id(input_val)
    if not gid:
        logger.emit("<font color='#ef4444'>[-] ID Serveur introuvable.</font>")
        return

    logger.emit(f"<font color='#3b82f6'><b>[*] Récupération infos détaillées (Auth)...</b></font>")
    headers = {'Authorization': token, 'User-Agent': HEADERS['User-Agent']}
    try:
        res = requests.get(f"https://discord.com/api/v9/guilds/{gid}", headers=headers)
        if res.status_code == 200:
            g = res.json()
            logger.emit(f"<font color='#22c55e'>[+] Serveur: {g.get('name')}</font>")
            logger.emit(f"<font color='#e4e4e7'>    ID: {g.get('id')}</font>")
            logger.emit(f"<font color='#e4e4e7'>    Propriétaire ID: {g.get('owner_id')}</font>")
            logger.emit(f"<font color='#e4e4e7'>    Région: {g.get('region', 'N/A')}</font>")
            logger.emit(f"<font color='#e4e4e7'>    Niveau de vérification: {g.get('verification_level')}</font>")
            logger.emit(f"<font color='#e4e4e7'>    MFA Level: {g.get('mfa_level')}</font>")
            logger.emit(f"<font color='#e4e4e7'>    Boosts: {g.get('premium_subscription_count')}</font>")
            logger.emit(f"<font color='#e4e4e7'>    Description: {g.get('description') or 'Aucune'}</font>")
            logger.emit(f"<font color='#e4e4e7'>    Vanity URL: {g.get('vanity_url_code') or 'Non'}</font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Erreur ({res.status_code}): Impossible d'accéder aux infos (Token invalide ou pas dans le serveur ?)</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_dl_emojis(logger, token, input_val):
    if not token:
        logger.emit("<font color='#ef4444'>[-] Token requis.</font>")
        return
    gid = resolve_id(input_val)
    if not gid: return

    logger.emit(f"<font color='#3b82f6'><b>[*] Téléchargement des Emojis...</b></font>")
    headers = {'Authorization': token, 'User-Agent': HEADERS['User-Agent']}
    try:
        res = requests.get(f"https://discord.com/api/v9/guilds/{gid}/emojis", headers=headers)
        if res.status_code == 200:
            emojis = res.json()
            if not emojis:
                logger.emit("<font color='#e4e4e7'>[-] Aucun emoji trouvé.</font>")
                return
            
            base_dir = os.path.join('output', 'Server Emojis')
            if not os.path.exists(base_dir): os.makedirs(base_dir)
            folder = os.path.join(base_dir, f'emojis_{gid}')
            if not os.path.exists(folder): os.makedirs(folder)
            
            count = 0
            for e in emojis:
                eid = e['id']
                ename = e['name']
                animated = e.get('animated', False)
                ext = 'gif' if animated else 'png'
                url = f"https://cdn.discordapp.com/emojis/{eid}.{ext}"
                
                r = requests.get(url)
                if r.status_code == 200:
                    with open(os.path.join(folder, f"{ename}_{eid}.{ext}"), 'wb') as f:
                        f.write(r.content)
                    count += 1
            logger.emit(f"<font color='#22c55e'>[+] {count} Emojis téléchargés dans {folder}</font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Erreur accès ({res.status_code})</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_dl_stickers(logger, token, input_val):
    if not token:
        logger.emit("<font color='#ef4444'>[-] Token requis.</font>")
        return
    gid = resolve_id(input_val)
    if not gid: return

    logger.emit(f"<font color='#3b82f6'><b>[*] Téléchargement des Stickers...</b></font>")
    headers = {'Authorization': token, 'User-Agent': HEADERS['User-Agent']}
    try:
        res = requests.get(f"https://discord.com/api/v9/guilds/{gid}/stickers", headers=headers)
        if res.status_code == 200:
            stickers = res.json()
            if not stickers:
                logger.emit("<font color='#e4e4e7'>[-] Aucun sticker trouvé.</font>")
                return
            
            base_dir = os.path.join('output', 'Server Stickers')
            if not os.path.exists(base_dir): os.makedirs(base_dir)
            folder = os.path.join(base_dir, f'stickers_{gid}')
            if not os.path.exists(folder): os.makedirs(folder)
            
            count = 0
            for s in stickers:
                sid = s['id']
                sname = s['name']
                fmt = s.get('format_type', 1) # 1=PNG, 2=APNG, 3=LOTTIE
                ext = 'png'
                if fmt == 2: ext = 'png'
                elif fmt == 3: ext = 'json'
                
                url = f"https://cdn.discordapp.com/stickers/{sid}.{ext}"
                
                r = requests.get(url)
                if r.status_code == 200:
                    safe_name = "".join([c for c in sname if c.isalpha() or c.isdigit() or c==' ']).strip()
                    with open(os.path.join(folder, f"{safe_name}_{sid}.{ext}"), 'wb') as f:
                        f.write(r.content)
                    count += 1
            logger.emit(f"<font color='#22c55e'>[+] {count} Stickers téléchargés dans {folder}</font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Erreur accès ({res.status_code})</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_list_roles(logger, token, input_val):
    if not token:
        logger.emit("<font color='#ef4444'>[-] Token requis.</font>")
        return
    gid = resolve_id(input_val)
    if not gid: return

    logger.emit(f"<font color='#3b82f6'><b>[*] Liste des Rôles...</b></font>")
    headers = {'Authorization': token, 'User-Agent': HEADERS['User-Agent']}
    try:
        res = requests.get(f"https://discord.com/api/v9/guilds/{gid}/roles", headers=headers)
        if res.status_code == 200:
            roles = res.json()
            roles.sort(key=lambda x: x.get('position', 0), reverse=True)
            
            for r in roles:
                name = r['name']
                rid = r['id']
                color = r.get('color', 0)
                hex_col = f"#{color:06x}" if color else "None"
                logger.emit(f"<font color='#e4e4e7'>{name} (ID: {rid}) - Color: {hex_col}</font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Erreur accès ({res.status_code})</font>")
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

class ServerToolWindow(QMainWindow):
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
        
        title_label = QLabel("LE M // Serveur Tool")
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

        self.menu_label = QLabel("Server Tool - LE M")
        self.menu_label.setObjectName("MenuLabel")
        self.menu_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.menu_label)

        # Token Input (Optional)
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Token (Optionnel - Pour fonctions avancées)")
        self.token_input.setEchoMode(QLineEdit.Password)
        left_layout.addWidget(self.token_input)

        # Inputs
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Invitation ou ID Serveur")
        left_layout.addWidget(self.input_field)

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
        
        btn_menu_info = QPushButton("🔍  Informations >")
        btn_menu_dl = QPushButton("💾  Téléchargements >")
        
        for btn in [btn_menu_info, btn_menu_dl]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_main.addWidget(btn)
        layout_main.addStretch()
            
        # --- Page Info ---
        page_info = QWidget()
        layout_info = QVBoxLayout(page_info)
        layout_info.setSpacing(2)
        layout_info.setContentsMargins(0, 0, 0, 0)
        
        self.btn_info = QPushButton("🔍  Infos Invitation")
        self.btn_deep = QPushButton("🕵️  Infos Détaillées")
        self.btn_widget = QPushButton("📊  Infos Widget")
        self.btn_roles = QPushButton("📜  Liste Rôles")
        btn_back_info = QPushButton("⬅️  Retour")
        
        for btn in [self.btn_info, self.btn_deep, self.btn_widget, self.btn_roles, btn_back_info]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_info.addWidget(btn)
        layout_info.addStretch()
            
        # --- Page DL ---
        page_dl = QWidget()
        layout_dl = QVBoxLayout(page_dl)
        layout_dl.setSpacing(2)
        layout_dl.setContentsMargins(0, 0, 0, 0)
        
        self.btn_emojis = QPushButton("😀  DL Emojis")
        self.btn_stickers = QPushButton("🏷️  DL Stickers")
        self.btn_icon = QPushButton("🖼️  DL Icone")
        self.btn_banner = QPushButton("🖼️  DL Bannière")
        self.btn_splash = QPushButton("🖼️  DL Splash")
        btn_back_dl = QPushButton("⬅️  Retour")
        
        for btn in [self.btn_emojis, self.btn_stickers, self.btn_icon, self.btn_banner, self.btn_splash, btn_back_dl]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_dl.addWidget(btn)
        layout_dl.addStretch()
            
        self.stacked_widget.addWidget(page_main)
        self.stacked_widget.addWidget(page_info)
        self.stacked_widget.addWidget(page_dl)
        
        # Connect Actions
        self.btn_info.clicked.connect(lambda: self.start_task(logic_invite_info, self.input_field.text()))
        self.btn_deep.clicked.connect(lambda: self.start_task(logic_deep_info, self.token_input.text(), self.input_field.text()))
        self.btn_widget.clicked.connect(lambda: self.start_task(logic_widget_info, self.input_field.text()))
        self.btn_roles.clicked.connect(lambda: self.start_task(logic_list_roles, self.token_input.text(), self.input_field.text()))
        self.btn_emojis.clicked.connect(lambda: self.start_task(logic_dl_emojis, self.token_input.text(), self.input_field.text()))
        self.btn_stickers.clicked.connect(lambda: self.start_task(logic_dl_stickers, self.token_input.text(), self.input_field.text()))
        self.btn_icon.clicked.connect(lambda: self.start_task(logic_download_assets, self.input_field.text(), "icon"))
        self.btn_banner.clicked.connect(lambda: self.start_task(logic_download_assets, self.input_field.text(), "banner"))
        self.btn_splash.clicked.connect(lambda: self.start_task(logic_download_assets, self.input_field.text(), "splash"))
        
        # Navigation
        btn_menu_info.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        btn_menu_dl.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        btn_back_info.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_back_dl.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ServerToolWindow()
    window.show()
    sys.exit(app.exec_())
