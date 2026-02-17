import sys
import os
import requests
import threading
import time
import random
import urllib3
import urllib.parse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QFrame, QGraphicsDropShadowEffect, 
                             QScrollArea, QInputDialog, QMessageBox, QStyle, QStackedWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QCursor

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
API_BASE = 'https://discord.com/api/v9'

# --- Logic Functions ---

def get_headers(token):
    h = HEADERS.copy()
    h['Authorization'] = token
    h['Content-Type'] = 'application/json'
    return h

def logic_connect(logger, token):
    if not token:
        logger.emit("<font color='#ef4444'>[-] Token requis.</font>")
        return
    logger.emit(f"<font color='#3b82f6'><b>[*] Connexion au compte...</b></font>")
    try:
        r = requests.get(f'{API_BASE}/users/@me', headers=get_headers(token))
        if r.status_code == 200:
            u = r.json()
            logger.emit(f"<font color='#22c55e'>[+] Connecté: {u['username']}#{u['discriminator']}</font>")
            logger.emit(f"<font color='#e4e4e7'>    ID: {u['id']}</font>")
            logger.emit(f"<font color='#e4e4e7'>    Email: {u.get('email', 'N/A')}</font>")
            logger.emit(f"<font color='#e4e4e7'>    Téléphone: {u.get('phone', 'N/A')}</font>")
            nitro = u.get('premium_type', 0)
            nitro_str = "Aucun" if nitro == 0 else ("Nitro Classic" if nitro == 1 else "Nitro Boost")
            logger.emit(f"<font color='#e4e4e7'>    Nitro: {nitro_str}</font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Token invalide (Code {r.status_code})</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_hypesquad(logger, token, house_id):
    houses = {1: "Bravery (Violet)", 2: "Brilliance (Rouge)", 3: "Balance (Vert)"}
    house_name = houses.get(house_id, "Inconnu")
    
    logger.emit(f"<font color='#3b82f6'><b>[*] Changement HypeSquad vers {house_name}...</b></font>")
    try:
        r = requests.post(f'{API_BASE}/hypesquad/online', headers=get_headers(token), json={'house_id': house_id})
        if r.status_code == 204:
            logger.emit(f"<font color='#22c55e'>[+] Succès ! Vous êtes maintenant dans la maison {house_name}.</font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Échec ({r.status_code})</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_status_rotator(logger, token, text_input):
    if not token or not text_input: return
    texts = [t.strip() for t in text_input.split('|') if t.strip()]
    if not texts: return

    logger.emit(f"<font color='#3b82f6'><b>[*] Status Rotator démarré (Boucle infinie)...</b></font>")
    logger.emit(f"<font color='#a1a1aa'>[i] Textes: {', '.join(texts)}</font>")
    
    while True:
        for text in texts:
            try:
                requests.patch(f'{API_BASE}/users/@me/settings', headers=get_headers(token), json={'custom_status': {'text': text}})
                logger.emit(f"<font color='#e4e4e7'>[>] Statut changé: {text}</font>")
            except: pass
            time.sleep(5) # Délai entre les changements

def logic_mass_dm(logger, token, message):
    if not token or not message: return
    logger.emit(f"<font color='#3b82f6'><b>[*] Mass DM Amis en cours...</b></font>")
    try:
        r = requests.get(f'{API_BASE}/users/@me/relationships', headers=get_headers(token))
        if r.status_code != 200:
            logger.emit(f"<font color='#ef4444'>[-] Impossible de récupérer les amis.</font>")
            return
            
        friends = [f for f in r.json() if f['type'] == 1]
        logger.emit(f"<font color='#e4e4e7'>[i] {len(friends)} amis trouvés.</font>")
        
        count = 0
        for f in friends:
            uid = f['user']['id']
            username = f['user']['username']
            try:
                # Créer DM
                c = requests.post(f'{API_BASE}/users/@me/channels', headers=get_headers(token), json={'recipient_id': uid})
                if c.status_code in [200, 201]:
                    cid = c.json()['id']
                    # Envoyer
                    m = requests.post(f'{API_BASE}/channels/{cid}/messages', headers=get_headers(token), json={'content': message})
                    if m.status_code in [200, 201]:
                        logger.emit(f"<font color='#22c55e'>[+] Envoyé à {username}</font>")
                        count += 1
                    else:
                        logger.emit(f"<font color='#ef4444'>[-] Erreur envoi à {username} ({m.status_code})</font>")
                time.sleep(1.5) # Anti rate-limit
            except Exception as e:
                logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")
        logger.emit(f"<font color='#3b82f6'><b>[*] Terminé. {count} messages envoyés.</b></font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_clear_dms(logger, token):
    logger.emit(f"<font color='#3b82f6'><b>[*] Fermeture de tous les DMs...</b></font>")
    try:
        r = requests.get(f'{API_BASE}/users/@me/channels', headers=get_headers(token))
        channels = r.json()
        count = 0
        for c in channels:
            requests.delete(f'{API_BASE}/channels/{c["id"]}', headers=get_headers(token))
            count += 1
            time.sleep(0.3)
        logger.emit(f"<font color='#22c55e'>[+] {count} DMs fermés.</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_mass_leave(logger, token):
    logger.emit(f"<font color='#3b82f6'><b>[*] Quitter tous les serveurs...</b></font>")
    try:
        r = requests.get(f'{API_BASE}/users/@me/guilds', headers=get_headers(token))
        guilds = r.json()
        for g in guilds:
            if not g.get('owner'):
                requests.delete(f'{API_BASE}/users/@me/guilds/{g["id"]}', headers=get_headers(token))
                logger.emit(f"<font color='#22c55e'>[+] Quitté: {g['name']}</font>")
                time.sleep(0.5)
            else:
                logger.emit(f"<font color='#a1a1aa'>[!] Ignoré (Propriétaire): {g['name']}</font>")
        logger.emit(f"<font color='#3b82f6'><b>[*] Terminé.</b></font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_nitro_sniper(logger, token):
    logger.emit(f"<font color='#3b82f6'><b>[*] Nitro Sniper Démarré (Mode Passif)...</b></font>")
    logger.emit(f"<font color='#a1a1aa'>[i] Surveille les derniers messages des DMs ouverts.</font>")
    
    seen_codes = set()
    
    while True:
        try:
            # Récupérer les DMs
            r = requests.get(f'{API_BASE}/users/@me/channels', headers=get_headers(token))
            if r.status_code == 200:
                channels = r.json()
                for c in channels:
                    try:
                        # Vérifier dernier message
                        lid = c.get('last_message_id')
                        if lid:
                            msgs = requests.get(f'{API_BASE}/channels/{c["id"]}/messages?limit=1', headers=get_headers(token)).json()
                            if msgs:
                                content = msgs[0].get('content', '')
                                if 'discord.gift/' in content:
                                    code = content.split('discord.gift/')[1].split(' ')[0]
                                    if code not in seen_codes:
                                        logger.emit(f"<font color='#22c55e'>[!!!] CODE TROUVÉ: {code}</font>")
                                        # Tentative de claim
                                        res = requests.post(f'{API_BASE}/entitlements/gift-codes/{code}/redeem', headers=get_headers(token))
                                        if res.status_code == 200:
                                            logger.emit(f"<font color='#22c55e'>[$$$] NITRO CLAIMED !</font>")
                                        else:
                                            logger.emit(f"<font color='#ef4444'>[-] Échec claim ({res.status_code})</font>")
                                        seen_codes.add(code)
                    except: pass
            time.sleep(5)
        except: pass

def logic_delete_own_messages(logger, token, channel_id):
    if not token or not channel_id: return
    logger.emit(f"<font color='#3b82f6'><b>[*] Suppression de vos messages dans {channel_id}...</b></font>")
    
    headers = get_headers(token)
    try:
        # Get User ID first
        me = requests.get(f'{API_BASE}/users/@me', headers=headers).json()
        my_id = me.get('id')
        if not my_id: 
            logger.emit(f"<font color='#ef4444'>[-] Impossible de récupérer votre ID.</font>")
            return

        has_more = True
        last_id = None
        count = 0
        
        while has_more:
            url = f'{API_BASE}/channels/{channel_id}/messages?limit=100'
            if last_id: url += f'&before={last_id}'
            
            r = requests.get(url, headers=headers)
            if r.status_code != 200: break
            
            messages = r.json()
            if not messages: break
            
            last_id = messages[-1]['id']
            
            for msg in messages:
                if msg['author']['id'] == my_id:
                    requests.delete(f'{API_BASE}/channels/{channel_id}/messages/{msg["id"]}', headers=headers)
                    count += 1
                    time.sleep(1.2) # Avoid rate limit (Delete is strict)
                    if count % 5 == 0:
                        logger.emit(f"<font color='#e4e4e7'>[i] {count} messages supprimés...</font>")
        
        logger.emit(f"<font color='#22c55e'>[+] Terminé. Total supprimé: {count}</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_auto_bump(logger, token, channel_id, message, delay, count):
    if not token or not channel_id or not message: return
    logger.emit(f"<font color='#3b82f6'><b>[*] Auto-Bump démarré sur {channel_id}...</b></font>")
    
    headers = get_headers(token)
    for i in range(int(count)):
        try:
            r = requests.post(f'{API_BASE}/channels/{channel_id}/messages', headers=headers, json={'content': message})
            if r.status_code in [200, 201]:
                logger.emit(f"<font color='#22c55e'>[+] Message {i+1}/{count} envoyé.</font>")
            else:
                logger.emit(f"<font color='#ef4444'>[-] Erreur ({r.status_code})</font>")
            
            if i < int(count) - 1:
                time.sleep(float(delay))
        except Exception as e:
            logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")
            break
    logger.emit(f"<font color='#3b82f6'><b>[*] Auto-Bump terminé.</b></font>")

def logic_fake_typing(logger, token, channel_id, duration):
    if not token or not channel_id: return
    logger.emit(f"<font color='#3b82f6'><b>[*] Fake Typing sur {channel_id} pendant {duration}s...</b></font>")
    headers = get_headers(token)
    start = time.time()
    while time.time() - start < int(duration):
        try:
            requests.post(f'{API_BASE}/channels/{channel_id}/typing', headers=headers)
            time.sleep(9) # Typing lasts ~10s
        except: break
    logger.emit(f"<font color='#3b82f6'><b>[*] Fake Typing terminé.</b></font>")

def logic_ghost_ping(logger, token, channel_id, user_id, count):
    if not token or not channel_id or not user_id: return
    logger.emit(f"<font color='#3b82f6'><b>[*] Ghost Ping sur {user_id} dans {channel_id}...</b></font>")
    headers = get_headers(token)
    for i in range(int(count)):
        try:
            r = requests.post(f'{API_BASE}/channels/{channel_id}/messages', headers=headers, json={'content': f'<@{user_id}>'})
            if r.status_code in [200, 201]:
                msg_id = r.json()['id']
                requests.delete(f'{API_BASE}/channels/{channel_id}/messages/{msg_id}', headers=headers)
                logger.emit(f"<font color='#22c55e'>[+] Ping {i+1}/{count} effectué.</font>")
            else:
                logger.emit(f"<font color='#ef4444'>[-] Erreur envoi ({r.status_code})</font>")
            time.sleep(0.8)
        except Exception as e:
            logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_reaction_spam(logger, token, channel_id, emoji, count):
    if not token or not channel_id or not emoji: return
    logger.emit(f"<font color='#3b82f6'><b>[*] Reaction Spam dans {channel_id}...</b></font>")
    headers = get_headers(token)
    emoji_encoded = urllib.parse.quote(emoji)
    try:
        r = requests.get(f'{API_BASE}/channels/{channel_id}/messages?limit={count}', headers=headers)
        if r.status_code == 200:
            messages = r.json()
            for msg in messages:
                mid = msg['id']
                rr = requests.put(f'{API_BASE}/channels/{channel_id}/messages/{mid}/reactions/{emoji_encoded}/@me', headers=headers)
                if rr.status_code == 204:
                    logger.emit(f"<font color='#22c55e'>[+] Réaction ajoutée sur {mid}</font>")
                time.sleep(0.6)
        else:
            logger.emit(f"<font color='#ef4444'>[-] Impossible de récupérer les messages.</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_create_group_dms(logger, token):
    if not token: return
    logger.emit(f"<font color='#3b82f6'><b>[*] Création de Groupes DM (Spam)...</b></font>")
    headers = get_headers(token)
    try:
        r = requests.get(f'{API_BASE}/users/@me/relationships', headers=headers)
        friends = [f['user']['id'] for f in r.json() if f['type'] == 1]
        if len(friends) < 2:
            logger.emit(f"<font color='#ef4444'>[-] Pas assez d'amis pour créer des groupes.</font>")
            return
        random.shuffle(friends)
        chunks = [friends[i:i + 5] for i in range(0, len(friends), 5)]
        for chunk in chunks:
            if len(chunk) < 2: continue
            rr = requests.post(f'{API_BASE}/users/@me/channels', headers=headers, json={"recipients": chunk})
            if rr.status_code == 200:
                logger.emit(f"<font color='#22c55e'>[+] Groupe créé: {rr.json()['id']}</font>")
            time.sleep(2.5)
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_change_bio(logger, token, bio):
    if not token: return
    logger.emit(f"<font color='#3b82f6'><b>[*] Changement de la Bio...</b></font>")
    headers = get_headers(token)
    try:
        r = requests.patch(f'{API_BASE}/users/@me', headers=headers, json={'bio': bio})
        if r.status_code == 200:
             logger.emit(f"<font color='#22c55e'>[+] Bio mise à jour !</font>")
        else:
             logger.emit(f"<font color='#ef4444'>[-] Échec ({r.status_code})</font>")
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

class SelfBotToolWindow(QMainWindow):
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
        
        title_label = QLabel("LE M // Self Bot Tool")
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

        self.menu_label = QLabel("Self Bot Tool - LE M")
        self.menu_label.setObjectName("MenuLabel")
        self.menu_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.menu_label)

        # Token Input
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Votre Token Utilisateur")
        self.token_input.setEchoMode(QLineEdit.Password)
        left_layout.addWidget(self.token_input)

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
        
        self.btn_connect = QPushButton("🔌  Connexion / Infos")
        self.btn_menu_hs = QPushButton("🏠  HypeSquad >")
        self.btn_menu_spam = QPushButton("📢  Spam / Raid >")
        self.btn_menu_utils = QPushButton("🛠️  Outils / Compte >")
        
        for btn in [self.btn_connect, self.btn_menu_hs, self.btn_menu_spam, self.btn_menu_utils]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_main.addWidget(btn)
        layout_main.addStretch()
            
        # --- Page HypeSquad ---
        page_hs = QWidget()
        layout_hs = QVBoxLayout(page_hs)
        layout_hs.setSpacing(8)
        layout_hs.setContentsMargins(0, 0, 0, 0)
        
        btn_hs_bravery = QPushButton("🟣  Bravery")
        btn_hs_brilliance = QPushButton("🔴  Brilliance")
        btn_hs_balance = QPushButton("🟢  Balance")
        btn_back_hs = QPushButton("⬅️  Retour")
        
        for btn in [btn_hs_bravery, btn_hs_brilliance, btn_hs_balance, btn_back_hs]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_hs.addWidget(btn)
        layout_hs.addStretch()
            
        # --- Page Spam ---
        page_spam = QWidget()
        layout_spam = QVBoxLayout(page_spam)
        layout_spam.setSpacing(8)
        layout_spam.setContentsMargins(0, 0, 0, 0)
        
        btn_massdm = QPushButton("📨  Mass DM Amis")
        btn_bump = QPushButton("📢  Auto Bump")
        btn_typing = QPushButton("⌨️  Fake Typing")
        btn_ghost = QPushButton("👻  Ghost Ping")
        btn_react = QPushButton("😀  Reaction Spam")
        btn_group = QPushButton("👥  Créer Groupes")
        btn_back_spam = QPushButton("⬅️  Retour")
        
        for btn in [btn_massdm, btn_bump, btn_typing, btn_ghost, btn_react, btn_group, btn_back_spam]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_spam.addWidget(btn)
        layout_spam.addStretch()
            
        # --- Page Utils ---
        page_utils = QWidget()
        layout_utils = QVBoxLayout(page_utils)
        layout_utils.setSpacing(8)
        layout_utils.setContentsMargins(0, 0, 0, 0)
        
        btn_rotator = QPushButton("🔄  Status Rotator")
        btn_cleardm = QPushButton("🗑️  Fermer DMs")
        btn_leave = QPushButton("🏃  Quitter Serveurs")
        btn_sniper = QPushButton("🎁  Nitro Sniper")
        btn_del_msgs = QPushButton("🔥  Del Mes Messages")
        btn_bio = QPushButton("📝  Changer Bio")
        btn_back_utils = QPushButton("⬅️  Retour")
        
        for btn in [btn_rotator, btn_cleardm, btn_leave, btn_sniper, btn_del_msgs, btn_bio, btn_back_utils]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_utils.addWidget(btn)
        layout_utils.addStretch()

        self.stacked_widget.addWidget(page_main)
        self.stacked_widget.addWidget(page_hs)
        self.stacked_widget.addWidget(page_spam)
        self.stacked_widget.addWidget(page_utils)
        
        # Connect Actions
        self.btn_connect.clicked.connect(lambda: self.start_task(logic_connect, self.token_input.text()))
        
        # Navigation
        self.btn_menu_hs.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.btn_menu_spam.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        self.btn_menu_utils.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        btn_back_hs.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_back_spam.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_back_utils.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        # Logic
        btn_hs_bravery.clicked.connect(lambda: self.start_task(logic_hypesquad, self.token_input.text(), 1))
        btn_hs_brilliance.clicked.connect(lambda: self.start_task(logic_hypesquad, self.token_input.text(), 2))
        btn_hs_balance.clicked.connect(lambda: self.start_task(logic_hypesquad, self.token_input.text(), 3))
        btn_rotator.clicked.connect(self.action_rotator)
        btn_massdm.clicked.connect(self.action_massdm)
        btn_cleardm.clicked.connect(lambda: self.start_task(logic_clear_dms, self.token_input.text()))
        btn_leave.clicked.connect(lambda: self.start_task(logic_mass_leave, self.token_input.text()))
        btn_sniper.clicked.connect(lambda: self.start_task(logic_nitro_sniper, self.token_input.text()))
        btn_del_msgs.clicked.connect(self.action_del_msgs)
        btn_bump.clicked.connect(self.action_bump)
        btn_typing.clicked.connect(self.action_typing)
        btn_ghost.clicked.connect(self.action_ghost)
        btn_react.clicked.connect(self.action_react)
        btn_group.clicked.connect(lambda: self.start_task(logic_create_group_dms, self.token_input.text()))
        btn_bio.clicked.connect(self.action_bio)

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

    # --- Actions ---

    def action_rotator(self):
        text, ok = QInputDialog.getText(self, "Status Rotator", "Textes (séparés par | ) :")
        if ok and text:
            self.start_task(logic_status_rotator, self.token_input.text(), text)

    def action_massdm(self):
        msg, ok = QInputDialog.getText(self, "Mass DM", "Message à envoyer à tous les amis :")
        if ok and msg:
            self.start_task(logic_mass_dm, self.token_input.text(), msg)

    def action_del_msgs(self):
        cid, ok = QInputDialog.getText(self, "Suppression", "ID du Salon/DM :")
        if ok and cid:
            self.start_task(logic_delete_own_messages, self.token_input.text(), cid)

    def action_bump(self):
        cid, ok = QInputDialog.getText(self, "Auto Bump", "ID du Salon :")
        if ok and cid:
            msg, ok2 = QInputDialog.getText(self, "Auto Bump", "Message :")
            if ok2 and msg:
                delay, ok3 = QInputDialog.getInt(self, "Auto Bump", "Délai (secondes) :", 7200, 1, 86400)
                if ok3:
                    count, ok4 = QInputDialog.getInt(self, "Auto Bump", "Nombre de fois :", 10, 1, 1000)
                    if ok4:
                        self.start_task(logic_auto_bump, self.token_input.text(), cid, msg, delay, count)

    def action_typing(self):
        cid, ok = QInputDialog.getText(self, "Fake Typing", "ID du Salon :")
        if ok and cid:
            dur, ok2 = QInputDialog.getInt(self, "Fake Typing", "Durée (secondes) :", 60, 1, 3600)
            if ok2:
                self.start_task(logic_fake_typing, self.token_input.text(), cid, dur)

    def action_ghost(self):
        cid, ok = QInputDialog.getText(self, "Ghost Ping", "ID du Salon :")
        if ok and cid:
            uid, ok2 = QInputDialog.getText(self, "Ghost Ping", "ID de l'utilisateur à ping :")
            if ok2 and uid:
                count, ok3 = QInputDialog.getInt(self, "Ghost Ping", "Nombre de pings :", 5, 1, 50)
                if ok3:
                    self.start_task(logic_ghost_ping, self.token_input.text(), cid, uid, count)

    def action_react(self):
        cid, ok = QInputDialog.getText(self, "Reaction Spam", "ID du Salon :")
        if ok and cid:
            emoji, ok2 = QInputDialog.getText(self, "Reaction Spam", "Emoji (Unicode ou nom:id) :")
            if ok2 and emoji:
                count, ok3 = QInputDialog.getInt(self, "Reaction Spam", "Nombre de messages :", 10, 1, 50)
                if ok3:
                    self.start_task(logic_reaction_spam, self.token_input.text(), cid, emoji, count)

    def action_bio(self):
        bio, ok = QInputDialog.getMultiLineText(self, "Changer Bio", "Nouvelle Bio :")
        if ok:
            self.start_task(logic_change_bio, self.token_input.text(), bio)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SelfBotToolWindow()
    window.show()
    sys.exit(app.exec_())
