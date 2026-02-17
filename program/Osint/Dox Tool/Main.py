import sys
import os
import requests
import concurrent.futures
import urllib3
import datetime
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextBrowser, QFrame, QGraphicsDropShadowEffect, 
                             QScrollArea, QStackedWidget, QFileDialog, QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QCursor

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
TOKEN_FILE = 'input/bot_token.txt'

# --- Logic Functions ---

HELP_TEXT = "<b>Aide Dox Tool</b><br><br>" \
            "<b>Recherche Discord:</b> Trouve des infos via un ID Discord (nécessite un Token Bot).<br>" \
            "<b>Recherche DB:</b> Cherche un terme (email, pseudo) dans vos fichiers de base de données locaux (dossier DB).<br>" \
            "<b>Créer Dox:</b> Assistant pour générer une fiche de renseignements propre."

def load_bot_token():
    if not os.path.exists('input'): os.makedirs('input')
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            t = f.read().strip()
            if t and not t.startswith('#'): return t
    return ""

def logic_discord_lookup(logger, token, user_id):
    if not token:
        logger.emit("<font color='#ef4444'>[-] Token de Bot requis (voir Bot Tool).</font>")
        return
    if not user_id or not user_id.isdigit():
        logger.emit("<font color='#ef4444'>[-] ID Utilisateur invalide.</font>")
        return

    logger.emit(f"<font color='#3b82f6'><b>[*] Recherche Discord pour l'ID {user_id}...</b></font>")
    headers = {'Authorization': f'Bot {token}', 'Content-Type': 'application/json'}
    
    try:
        r = requests.get(f'https://discord.com/api/v9/users/{user_id}', headers=headers)
        if r.status_code == 200:
            u = r.json()
            created_at = (int(user_id) >> 22) + 1420070400000
            date_str = datetime.datetime.fromtimestamp(created_at / 1000).strftime('%Y-%m-%d %H:%M:%S')
            
            logger.emit(f"<font color='#22c55e'>[+] Utilisateur Trouvé !</font>")
            logger.emit(f"<font color='#e4e4e7'>    Pseudo: {u['username']}#{u['discriminator']}</font>")
            logger.emit(f"<font color='#e4e4e7'>    ID: {u['id']}</font>")
            logger.emit(f"<font color='#e4e4e7'>    Création: {date_str}</font>")
            if u.get('avatar'):
                ext = "gif" if u['avatar'].startswith("a_") else "png"
                logger.emit(f"<font color='#3b82f6'>    Avatar: <a href='https://cdn.discordapp.com/avatars/{u['id']}/{u['avatar']}.{ext}'>Lien</a></font>")
            if u.get('banner'):
                ext = "gif" if u['banner'].startswith("a_") else "png"
                logger.emit(f"<font color='#3b82f6'>    Bannière: <a href='https://cdn.discordapp.com/banners/{u['id']}/{u['banner']}.{ext}'>Lien</a></font>")
            logger.emit(f"<font color='#e4e4e7'>    Bot: {'Oui' if u.get('bot') else 'Non'}</font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] Introuvable ou Erreur ({r.status_code})</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_search_db(logger, target, search_term):
    if not target or not os.path.exists(target):
        logger.emit("<font color='#ef4444'>[-] Cible invalide.</font>")
        return
    if not search_term:
        logger.emit("<font color='#ef4444'>[-] Terme de recherche requis.</font>")
        return

    logger.emit(f"<font color='#3b82f6'><b>[*] Recherche de '{search_term}' dans {os.path.basename(target)}...</b></font>")
    
    count = 0
    files_checked = 0
    
    def scan_file(fpath):
        c = 0
        try:
            try:
                f = open(fpath, 'r', encoding='utf-8', errors='strict')
                lines = f.readlines()
                f.close()
            except:
                f = open(fpath, 'r', encoding='latin-1', errors='ignore')
                lines = f.readlines()
                f.close()

            for i, line in enumerate(lines):
                if search_term in line:
                    clean_line = line.strip()[:200]
                    logger.emit(f"<font color='#22c55e'>[+] Trouvé ({os.path.basename(fpath)}:{i+1}): {clean_line}</font>")
                    c += 1
        except: pass
        return c

    if os.path.isfile(target):
        count += scan_file(target)
    elif os.path.isdir(target):
        for root, dirs, files in os.walk(target):
            for file in files:
                files_checked += 1
                path = os.path.join(root, file)
                count += scan_file(path)
                if files_checked % 500 == 0:
                     logger.emit(f"<font color='#a1a1aa'>[i] {files_checked} fichiers analysés...</font>")

    logger.emit(f"<font color='#3b82f6'><b>[*] Terminé. {count} résultats trouvés.</b></font>")

def logic_save_dox(logger, data, art_style):
    logger.emit(f"<font color='#3b82f6'><b>[*] Génération du rapport Dox...</b></font>")
    
    # Collection d'Arts ASCII
    arts = {
        "Hacker (Hood)": r"""
                       ...
                     ;::::;
                   ;::::; :;
                 ;:::::'   :;
                ;:::::;     ;.
               ,:::::'       ;           OOO\
               ::::::;       ;          OOOOO\
               ;:::::;       ;         OOOOOOOO
              ,;::::::;     ;'         / OOOOOOO
            ;:::::::::`. ,,,;.        /  / DOOOOOO
          .';:::::::::::::::::;,     /  /     DOOOO
         ,::::::;::::::;;;;::::;,   /  /        DOOO
        ;`::::::`'::::::;;;::::: ,#/  /          DOOO
        :`:::::::`;::::::;;::: ;::#  /            DOOO
        ::`:::::::`;:::::::: ;::::# /              DOO
        `:`:::::::`;:::::: ;::::::#/               DOO
         :::`:::::::`;; ;:::::::::##                OO
         ::::`:::::::`;::::::::;:::#                OO
         `:::::`::::::::::::;'`:;::#                O
          `:::::`::::::::;' /  / `:#
           ::::::`:::::;'  /  /   `#
""",
        "Aucun": ""
    }

    selected_art = arts.get(art_style, "")
    
    content = ""
    if selected_art:
        content += selected_art + "\n"
    
    content += "="*70 + "\n"
    content += "                      DOX REPORT / FICHE\n"
    content += "="*70 + "\n\n"
    
    # Construction du contenu basé sur les réponses
    sections = [
        ("IDENTITÉ", ["Prénom", "Nom", "Alias", "Date Naissance", "Sexe", "Nationalité"]),
        ("CONTACT", ["Email", "Téléphone", "Adresse", "Ville", "Code Postal"]),
        ("NUMÉRIQUE", ["IP", "Discord ID", "Twitter", "Instagram"]),
        ("AUTRES", ["Notes"])
    ]
    
    for title, fields in sections:
        content += f"[{title}]\n" + "-"*40 + "\n"
        for f in fields:
            val = data.get(f, "")
            content += f"[*] {f:<15} : {val}\n"
        content += "\n"

    content += "="*70 + "\n"
    content += "                  GÉNÉRÉ PAR LE M MULTI TOOL\n"
    content += "="*70 + "\n"

    output_dir = os.path.join('output', 'Dox Reports')
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    
    # Nom de fichier unique
    safe_alias = "".join([c for c in data.get("Alias", "target") if c.isalnum()])
    filename = f"dox_{safe_alias}_{int(time.time())}.txt"
    path = os.path.join(output_dir, filename)
    
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.emit(f"<font color='#22c55e'>[+] Dox sauvegardé: {path}</font>")
        if os.name == 'nt':
            os.startfile(os.path.abspath(path))
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur écriture: {e}</font>")

def logic_dox_tracker(logger):
    logger.emit(f"<font color='#3b82f6'><b>[*] Dox Tracker - Historique...</b></font>")
    output_dir = os.path.join('output', 'Dox Reports')
    
    if not os.path.exists(output_dir):
        logger.emit(f"<font color='#a1a1aa'>[-] Aucun dossier '{output_dir}' trouvé.</font>")
        return
    
    files = [f for f in os.listdir(output_dir) if f.startswith('dox_') and f.endswith('.txt')]
    if not files:
        logger.emit("<font color='#a1a1aa'>[-] Aucun Dox trouvé dans l'historique.</font>")
        return
    
    logger.emit(f"<font color='#22c55e'>[+] {len(files)} Dox trouvés :</font>")
    for f in files:
        # Extract alias from filename dox_ALIAS_timestamp.txt
        logger.emit(f"<font color='#e4e4e7'>    - {f}</font>")

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

class DoxToolWindow(QMainWindow):
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
        
        title_label = QLabel("LE M // Dox Tool")
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

        self.menu_label = QLabel("Dox Tool - LE M")
        self.menu_label.setObjectName("MenuLabel")
        self.menu_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.menu_label)

        # Inputs
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Recherche dans DB / ID Discord")
        left_layout.addWidget(self.input_field)

        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Bot Token (Pour Discord)")
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setText(load_bot_token())
        left_layout.addWidget(self.token_input)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #333; max-height: 1px;")
        left_layout.addWidget(line)

        # Create DB folder if not exists
        if not os.path.exists('DB'): os.makedirs('DB')

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
        
        self.btn_discord = QPushButton("👾  Recherche Discord")
        self.btn_search_db = QPushButton("📂  Recherche dans DB")
        self.btn_template = QPushButton("📝  Créer Dox (Assistant)")
        self.btn_tracker = QPushButton("🕵️  Dox Tracker")
        
        for btn in [self.btn_discord, self.btn_search_db, self.btn_template, self.btn_tracker]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_main.addWidget(btn)
        layout_main.addStretch()
            
        self.stacked_widget.addWidget(page_main)
        
        # Actions
        self.btn_discord.clicked.connect(lambda: self.start_task(logic_discord_lookup, self.token_input.text(), self.input_field.text()))
        self.btn_search_db.clicked.connect(self.action_search_db)
        self.btn_template.clicked.connect(self.action_wizard_template)
        self.btn_tracker.clicked.connect(lambda: self.start_task(logic_dox_tracker))

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

    def action_search_db(self):
        term = self.input_field.text().strip()
        if not term:
            self.log_message("<font color='#ef4444'>[-] Veuillez entrer un terme de recherche dans la barre en haut.</font>")
            return
        
        start_dir = os.path.join(os.getcwd(), 'DB')
        fpath, _ = QFileDialog.getOpenFileName(self, "Choisir un fichier de DB", start_dir, "Fichiers Texte (*.txt *.sql *.csv);;Tous les fichiers (*)")
        if fpath:
            self.start_task(logic_search_db, fpath, term)

    def action_wizard_template(self):
        # Questions
        fields = [
            "Prénom", "Nom", "Alias", "Date Naissance", "Sexe", "Nationalité",
            "Email", "Téléphone", "Adresse", "Ville", "Code Postal",
            "IP", "Discord ID", "Twitter", "Instagram", "Notes"
        ]
        
        data = {}
        for field in fields:
            text, ok = QInputDialog.getText(self, "Dox Wizard", f"{field} :")
            if not ok: return # Annulé
            data[field] = text.strip()
            
        # Art Selection
        arts = ["Hacker (Hood)", "Aucun"]
        item, ok = QInputDialog.getItem(self, "Style", "Choisir un Art ASCII :", arts, 0, False)
        if not ok: return
        
        self.start_task(logic_save_dox, data, item)

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
    window = DoxToolWindow()
    window.show()
    sys.exit(app.exec_())
