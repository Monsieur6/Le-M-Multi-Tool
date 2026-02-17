import sys
import os
import requests
import concurrent.futures
import urllib3
import socket
import re
import json
import webbrowser

# Optional imports handling
try:
    import dns.resolver
except ImportError:
    dns = None
try:
    import phonenumbers
    from phonenumbers import geocoder, carrier, timezone
except ImportError:
    phonenumbers = None
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
try:
    import whois
except ImportError:
    whois = None

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextBrowser, QFrame, QGraphicsDropShadowEffect, 
                             QScrollArea, QStackedWidget, QFileDialog, QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QCursor

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}

# --- Logic Functions ---

def check_libs(logger, libs):
    missing = []
    if 'bs4' in libs and BeautifulSoup is None: missing.append('beautifulsoup4')
    if 'dns' in libs and dns is None: missing.append('dnspython')
    if 'phonenumbers' in libs and phonenumbers is None: missing.append('phonenumbers')
    if 'whois' in libs and whois is None: missing.append('python-whois')
    if missing:
        logger.emit(f"<font color='#ef4444'>[!] Bibliothèques manquantes : {', '.join(missing)}</font>")
        logger.emit(f"<font color='#e4e4e7'>    Installez-les : pip install {' '.join(missing)}</font>")
        return False
    return True

def logic_username_tracker(logger, username):
    if not username:
        logger.emit("<font color='#ef4444'>[-] Pseudo requis.</font>")
        return

    logger.emit(f"<font color='#3b82f6'><b>[*] Recherche du pseudo '{username}'...</b></font>")
    
    # List based on provided snippet + extras
    sites = {
        "Instagram": {"url": f"https://www.instagram.com/{username}/", "check": "status"},
        "Twitter": {"url": f"https://twitter.com/{username}", "check": "status"},
        "GitHub": {"url": f"https://github.com/{username}", "check": "status"},
        "TikTok": {"url": f"https://www.tiktok.com/@{username}", "check": "status"},
        "Reddit": {"url": f"https://www.reddit.com/user/{username}", "check": "content", "error": "nobody on Reddit goes by that name"},
        "Pinterest": {"url": f"https://www.pinterest.com/{username}/", "check": "status"},
        "SoundCloud": {"url": f"https://soundcloud.com/{username}", "check": "status"},
        "Steam": {"url": f"https://steamcommunity.com/id/{username}", "check": "content", "error": "The specified profile could not be found"},
        "Twitch": {"url": f"https://www.twitch.tv/{username}", "check": "status"},
        "Spotify": {"url": f"https://open.spotify.com/user/{username}", "check": "status"},
        "Patreon": {"url": f"https://www.patreon.com/{username}", "check": "status"},
        "About.me": {"url": f"https://about.me/{username}", "check": "status"},
        "Roblox": {"url": f"https://www.roblox.com/user.aspx?username={username}", "check": "status"},
        "Pastebin": {"url": f"https://pastebin.com/u/{username}", "check": "status"},
        "Wattpad": {"url": f"https://www.wattpad.com/user/{username}", "check": "status"},
        "Canva": {"url": f"https://www.canva.com/{username}", "check": "status"},
        "Codecademy": {"url": f"https://www.codecademy.com/profiles/{username}", "check": "status"},
        "Gumroad": {"url": f"https://gumroad.com/{username}", "check": "status"},
        "Vimeo": {"url": f"https://vimeo.com/{username}", "check": "status"},
        "Wikipedia": {"url": f"https://en.wikipedia.org/wiki/User:{username}", "check": "status"},
        "HackerNews": {"url": f"https://news.ycombinator.com/user?id={username}", "check": "content", "error": "No such user"},
        "ProductHunt": {"url": f"https://www.producthunt.com/@{username}", "check": "status"},
        "Medium": {"url": f"https://medium.com/@{username}", "check": "status"},
        "Fiverr": {"url": f"https://www.fiverr.com/{username}", "check": "status"},
        "Ebay": {"url": f"https://www.ebay.com/usr/{username}", "check": "status"},
        "Slack": {"url": f"https://{username}.slack.com", "check": "status"},
        "TripAdvisor": {"url": f"https://www.tripadvisor.com/members/{username}", "check": "status"},
        "Blogger": {"url": f"https://{username}.blogspot.com", "check": "status"},
        "Tumblr": {"url": f"https://{username}.tumblr.com", "check": "status"},
        "LiveJournal": {"url": f"https://{username}.livejournal.com", "check": "status"},
        "WordPress": {"url": f"https://{username}.wordpress.com", "check": "status"},
    }

    def check_site(name, data):
        url = data["url"]
        try:
            r = requests.get(url, headers=HEADERS, timeout=5)
            found = False
            
            if data["check"] == "status":
                if r.status_code == 200: found = True
            elif data["check"] == "content":
                if r.status_code == 200 and data["error"].lower() not in r.text.lower(): found = True
            
            if found:
                return f"<font color='#22c55e'>[+] {name}: <a href='{url}'>{url}</a></font>"
            else:
                return None # Silent for not found to reduce spam
        except:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(check_site, name, data) for name, data in sites.items()]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res: logger.emit(res)

    logger.emit("<font color='#3b82f6'><b>[*] Recherche terminée.</b></font>")

def logic_email_lookup(logger, email):
    if not check_libs(logger, ['dns']): return
    if not email or "@" not in email:
        logger.emit("<font color='#ef4444'>[-] Email invalide.</font>")
        return

    domain = email.split('@')[1]
    logger.emit(f"<font color='#3b82f6'><b>[*] Infos DNS pour '{domain}'...</b></font>")

    # MX
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        logger.emit(f"<font color='#e4e4e7'>[MX] Serveurs Mail:</font>")
        for mx in mx_records:
            logger.emit(f"<font color='#22c55e'>    - {mx.exchange} (Prio: {mx.preference})</font>")
    except Exception as e:
        logger.emit(f"<font color='#a1a1aa'>[-] Pas de MX ou erreur: {e}</font>")

    # SPF
    try:
        spf_records = dns.resolver.resolve(domain, 'TXT')
        for spf in spf_records:
            txt = str(spf)
            if "v=spf1" in txt:
                logger.emit(f"<font color='#22c55e'>[SPF] Enregistrement trouvé: {txt}</font>")
    except:
        logger.emit(f"<font color='#a1a1aa'>[-] Pas de SPF trouvé.</font>")

    # DMARC
    try:
        dmarc = dns.resolver.resolve(f'_dmarc.{domain}', 'TXT')
        for d in dmarc:
            logger.emit(f"<font color='#22c55e'>[DMARC] {d}</font>")
    except:
        logger.emit(f"<font color='#a1a1aa'>[-] Pas de DMARC trouvé.</font>")

def logic_email_tracker(logger, email):
    if not email or "@" not in email:
        logger.emit("<font color='#ef4444'>[-] Email invalide.</font>")
        return

    logger.emit(f"<font color='#3b82f6'><b>[*] Recherche de comptes pour '{email}'...</b></font>")
    logger.emit(f"<font color='#a1a1aa'>[i] Analyse des services publics (Sans API Key)...</font>")

    session = requests.Session()
    headers = HEADERS

    # 1. Gravatar
    try:
        hash_email = __import__('hashlib').md5(email.lower().encode()).hexdigest()
        gravatar_url = f"https://www.gravatar.com/avatar/{hash_email}?d=404"
        if requests.get(gravatar_url).status_code == 200:
            logger.emit(f"<font color='#22c55e'>[+] Gravatar: COMPTE TROUVÉ</font>")
            logger.emit(f"    <a href='{gravatar_url}'>Avatar Link</a>")
        else:
            logger.emit(f"<font color='#a1a1aa'>[-] Gravatar: Non trouvé</font>")
    except: pass

    # 2. Spotify
    try:
        r = requests.get(f"https://spclient.wg.spotify.com/signup/public/v1/account?validate=1&email={email}", headers=headers)
        if r.status_code == 200:
            if r.json().get("status") == 20:
                logger.emit(f"<font color='#22c55e'>[+] Spotify: COMPTE TROUVÉ</font>")
            else:
                logger.emit(f"<font color='#a1a1aa'>[-] Spotify: Non trouvé</font>")
    except: pass

    # 3. Duolingo
    try:
        r = requests.get(f"https://www.duolingo.com/2017-06-30/users?email={email}", headers=headers)
        if r.status_code == 200:
            data = r.json()
            if data.get("users"):
                logger.emit(f"<font color='#22c55e'>[+] Duolingo: COMPTE TROUVÉ</font>")
            else:
                logger.emit(f"<font color='#a1a1aa'>[-] Duolingo: Non trouvé</font>")
    except: pass

    # 4. Firefox Sync
    try:
        r = requests.post("https://api.accounts.firefox.com/v1/account/status", json={"email": email})
        if r.status_code == 200 and "false" not in r.text:
            logger.emit(f"<font color='#22c55e'>[+] Firefox Sync: COMPTE TROUVÉ</font>")
        else:
            logger.emit(f"<font color='#a1a1aa'>[-] Firefox Sync: Non trouvé</font>")
    except: pass

    # 5. Imgur
    try:
        data = {'email': email}
        r = requests.post('https://imgur.com/signin/ajax_email_available', data=data, headers=headers)
        if r.status_code == 200:
            if r.json()['data']['available'] == False:
                logger.emit(f"<font color='#22c55e'>[+] Imgur: COMPTE TROUVÉ</font>")
            else:
                logger.emit(f"<font color='#a1a1aa'>[-] Imgur: Non trouvé</font>")
    except: pass

    # 6. WordPress.com
    try:
        r = requests.get(f"https://public-api.wordpress.com/rest/v1.1/users/validate-sign-up-details?email={email}", headers=headers)
        if r.status_code == 200:
            if not r.json().get("valid"):
                 logger.emit(f"<font color='#22c55e'>[+] WordPress.com: COMPTE TROUVÉ</font>")
            else:
                 logger.emit(f"<font color='#a1a1aa'>[-] WordPress.com: Non trouvé</font>")
    except: pass

    logger.emit("<font color='#3b82f6'><b>[*] Fin de l'analyse des comptes.</b></font>")

def logic_avatar_lookup(logger, email):
    if not email or "@" not in email:
        logger.emit("<font color='#ef4444'>[-] Email invalide.</font>")
        return
    logger.emit(f"<font color='#3b82f6'><b>[*] Recherche d'Avatar (Gravatar) pour '{email}'...</b></font>")
    try:
        hash_email = __import__('hashlib').md5(email.lower().encode()).hexdigest()
        gravatar_url = f"https://www.gravatar.com/avatar/{hash_email}?d=404"
        if requests.get(gravatar_url).status_code == 200:
            logger.emit(f"<font color='#22c55e'>[+] Avatar trouvé !</font>")
            logger.emit(f"<font color='#3b82f6'>    <a href='{gravatar_url}'>Voir l'image</a></font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Aucun avatar trouvé.</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_phone_lookup(logger, phone):
    if not phone:
        logger.emit("<font color='#ef4444'>[-] Numéro requis.</font>")
        return

    logger.emit(f"<font color='#3b82f6'><b>[*] Analyse du numéro '{phone}'...</b></font>")

    if phonenumbers:
        try:
            parsed = phonenumbers.parse(phone, None)
            if not phonenumbers.is_valid_number(parsed):
                logger.emit("<font color='#ef4444'>[-] Numéro invalide (lib).</font>")
            else:
                logger.emit(f"<font color='#22c55e'>[+] Numéro Valide</font>")
                logger.emit(f"<font color='#e4e4e7'>    Format International: {phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Pays: {geocoder.description_for_number(parsed, 'fr')}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Opérateur: {carrier.name_for_number(parsed, 'fr')}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Timezone: {timezone.time_zones_for_number(parsed)}</font>")
        except Exception as e:
            logger.emit(f"<font color='#ef4444'>[-] Erreur parsing: {e}</font>")
    else:
        logger.emit("<font color='#a1a1aa'>[i] Lib 'phonenumbers' absente. Analyse basique.</font>")
        # Fallback to basic regex
        clean_phone = re.sub(r'\D', '', phone)
        country = "Inconnu"
        if clean_phone.startswith("33"): country = "France (+33)"
        elif clean_phone.startswith("1"): country = "USA/Canada (+1)"
        elif clean_phone.startswith("44"): country = "UK (+44)"
        logger.emit(f"<font color='#e4e4e7'>Format Nettoyé: {clean_phone}</font>")
        logger.emit(f"<font color='#e4e4e7'>Pays Estimé: {country}</font>")

    # WhatsApp Link
    clean_phone = re.sub(r'\D', '', phone)
    wa_url = f"https://api.whatsapp.com/send?phone={clean_phone}"
    logger.emit(f"<font color='#22c55e'>[+] Lien WhatsApp: <a href='{wa_url}'>Ouvrir</a></font>")

def logic_subdomain_scanner(logger, domain):
    if not domain:
        logger.emit("<font color='#ef4444'>[-] Domaine requis.</font>")
        return
    
    logger.emit(f"<font color='#3b82f6'><b>[*] Recherche de sous-domaines pour '{domain}' (crt.sh)...</b></font>")
    try:
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            subs = set()
            for entry in data:
                name = entry['name_value']
                if "\n" in name:
                    for sub in name.split("\n"): subs.add(sub)
                else:
                    subs.add(name)
            
            logger.emit(f"<font color='#22c55e'>[+] {len(subs)} Sous-domaines trouvés :</font>")
            for s in sorted(list(subs)):
                logger.emit(f"<font color='#e4e4e7'>    - {s}</font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Erreur API ({r.status_code})</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_whois_lookup(logger, domain):
    if not check_libs(logger, ['whois']): return
    if not domain:
        logger.emit("<font color='#ef4444'>[-] Domaine requis.</font>")
        return
    
    logger.emit(f"<font color='#3b82f6'><b>[*] Recherche WHOIS pour '{domain}'...</b></font>")
    try:
        w = whois.whois(domain)
        logger.emit(f"<font color='#22c55e'>[+] Informations WHOIS trouvées:</font>")
        if w.get('creation_date'): logger.emit(f"<font color='#e4e4e7'>    Date Création: {w.creation_date}</font>")
        if w.get('expiration_date'): logger.emit(f"<font color='#e4e4e7'>    Date Expiration: {w.expiration_date}</font>")
        if w.get('registrar'): logger.emit(f"<font color='#e4e4e7'>    Registrar: {w.registrar}</font>")
        if w.get('name_servers'): logger.emit(f"<font color='#e4e4e7'>    Serveurs DNS: {w.name_servers}</font>")
        if w.get('org'): logger.emit(f"<font color='#e4e4e7'>    Organisation: {w.org}</font>")
        if w.get('emails'): logger.emit(f"<font color='#e4e4e7'>    Emails: {w.emails}</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur WHOIS: {e}</font>")

def logic_reverse_image_search(logger, image_url):
    if not image_url or not image_url.startswith('http'):
        logger.emit("<font color='#ef4444'>[-] URL d'image valide requise (http...).</font>")
        return
    
    logger.emit(f"<font color='#3b82f6'><b>[*] Lancement de la recherche d'image inversée...</b></font>")
    
    google_url = f"https://www.google.com/searchbyimage?image_url={image_url}"
    yandex_url = f"https://yandex.com/images/search?rpt=imageview&url={image_url}"
    tineye_url = f"https://tineye.com/search?url={image_url}"
    
    try:
        webbrowser.open(google_url)
        webbrowser.open(yandex_url)
        webbrowser.open(tineye_url)
        logger.emit(f"<font color='#22c55e'>[+] Onglets ouverts dans votre navigateur pour Google, Yandex et TinEye.</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur ouverture navigateur: {e}</font>")

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

class OsintToolWindow(QMainWindow):
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
        
        title_label = QLabel("LE M // Osint Tool")
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

        self.menu_label = QLabel("Osint Tool - LE M")
        self.menu_label.setObjectName("MenuLabel")
        self.menu_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.menu_label)

        # Scroll Area for Buttons
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background: transparent; border: none;")
        
        self.stacked_widget = QStackedWidget()

        # --- Page 0: Selection Menu ---
        self.page_menu = QWidget()
        layout_menu = QVBoxLayout(self.page_menu)
        layout_menu.setSpacing(15)
        layout_menu.setContentsMargins(0, 20, 0, 20)

        self.btn_menu_user = QPushButton("👤  User Tool >")
        self.btn_menu_email = QPushButton("📧  Email Tool >")
        self.btn_menu_phone = QPushButton("📱  Phone Tool >")
        self.btn_menu_domain = QPushButton("🌐  Domain Tool >")
        self.btn_menu_image = QPushButton("🖼️  Image Tool >")
        
        for btn in [self.btn_menu_user, self.btn_menu_email, self.btn_menu_phone, self.btn_menu_domain, self.btn_menu_image]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_menu.addWidget(btn)
        layout_menu.addStretch()

        self.stacked_widget.addWidget(self.page_menu)
        
        # --- Page 1: User Tool ---
        self.page_user = QWidget()
        layout_user = QVBoxLayout(self.page_user)
        layout_user.setSpacing(8)
        layout_user.setContentsMargins(0, 0, 0, 0)
        
        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Pseudo / Username")
        layout_user.addWidget(self.input_user)
        
        btn_user_track = QPushButton("👤  Username Tracker")
        btn_back_user = QPushButton("⬅️  Retour")
        
        for btn in [btn_user_track, btn_back_user]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_user.addWidget(btn)
            
        self.stacked_widget.addWidget(self.page_user)

        # --- Page 2: Email Tool ---
        self.page_email = QWidget()
        layout_email = QVBoxLayout(self.page_email)
        layout_email.setSpacing(8)
        layout_email.setContentsMargins(0, 0, 0, 0)
        
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Adresse Email")
        layout_email.addWidget(self.input_email)
        
        btn_email_track = QPushButton("📧  Email Tracker (Comptes)")
        btn_email_dns = QPushButton("🔍  Email Lookup (DNS)")
        btn_avatar = QPushButton("🖼️  Avatar Lookup (Photo)")
        btn_back_email = QPushButton("⬅️  Retour")
        
        for btn in [btn_email_track, btn_email_dns, btn_avatar, btn_back_email]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_email.addWidget(btn)
            
        self.stacked_widget.addWidget(self.page_email)

        # --- Page 3: Phone Tool ---
        self.page_phone = QWidget()
        layout_phone = QVBoxLayout(self.page_phone)
        layout_phone.setSpacing(8)
        layout_phone.setContentsMargins(0, 0, 0, 0)
        
        self.input_phone = QLineEdit()
        self.input_phone.setPlaceholderText("Numéro de Téléphone (ex: +336...)")
        layout_phone.addWidget(self.input_phone)
        
        btn_phone_look = QPushButton("📱  Phone Lookup")
        btn_back_phone = QPushButton("⬅️  Retour")
        
        for btn in [btn_phone_look, btn_back_phone]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_phone.addWidget(btn)
            
        self.stacked_widget.addWidget(self.page_phone)

        # --- Page 4: Domain Tool ---
        self.page_domain = QWidget()
        layout_domain = QVBoxLayout(self.page_domain)
        layout_domain.setSpacing(8)
        layout_domain.setContentsMargins(0, 0, 0, 0)
        
        self.input_domain = QLineEdit()
        self.input_domain.setPlaceholderText("Domaine (ex: google.com)")
        layout_domain.addWidget(self.input_domain)
        
        btn_whois = QPushButton("📖  WHOIS Lookup")
        btn_subdomain = QPushButton("🔗  Subdomain Scanner")
        btn_back_domain = QPushButton("⬅️  Retour")
        
        for btn in [btn_whois, btn_subdomain, btn_back_domain]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_domain.addWidget(btn)
            
        self.stacked_widget.addWidget(self.page_domain)

        # --- Page 5: Image Tool ---
        self.page_image = QWidget()
        layout_image = QVBoxLayout(self.page_image)
        layout_image.setSpacing(8)
        layout_image.setContentsMargins(0, 0, 0, 0)
        
        self.input_image = QLineEdit()
        self.input_image.setPlaceholderText("URL de l'image (http...)")
        layout_image.addWidget(self.input_image)
        
        btn_reverse_search = QPushButton("🔎  Recherche Inversée")
        btn_back_image = QPushButton("⬅️  Retour")
        
        for btn in [btn_reverse_search, btn_back_image]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_image.addWidget(btn)
            
        self.stacked_widget.addWidget(self.page_image)
            
        self.stacked_widget.setCurrentIndex(0)
        
        # Navigation
        self.btn_menu_user.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.btn_menu_email.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        self.btn_menu_phone.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        self.btn_menu_domain.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(4))
        self.btn_menu_image.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(5))
        
        btn_back_user.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_back_email.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_back_phone.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_back_domain.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_back_image.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        # Actions User
        btn_user_track.clicked.connect(lambda: self.start_task(logic_username_tracker, self.input_user.text()))
        
        # Actions Email
        btn_email_track.clicked.connect(lambda: self.start_task(logic_email_tracker, self.input_email.text()))
        btn_email_dns.clicked.connect(lambda: self.start_task(logic_email_lookup, self.input_email.text()))
        btn_avatar.clicked.connect(lambda: self.start_task(logic_avatar_lookup, self.input_email.text()))
        
        # Actions Phone
        btn_phone_look.clicked.connect(lambda: self.start_task(logic_phone_lookup, self.input_phone.text()))

        # Actions Domain
        btn_whois.clicked.connect(lambda: self.start_task(logic_whois_lookup, self.input_domain.text()))
        btn_subdomain.clicked.connect(lambda: self.start_task(logic_subdomain_scanner, self.input_domain.text()))
        
        # Actions Image
        btn_reverse_search.clicked.connect(lambda: self.start_task(logic_reverse_image_search, self.input_image.text()))

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
    window = OsintToolWindow()
    window.show()
    sys.exit(app.exec_())