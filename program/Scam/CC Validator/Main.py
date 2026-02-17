import sys
import os
import re
import requests
import random
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QFrame, QGraphicsDropShadowEffect, 
                             QScrollArea, QStackedWidget, QInputDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QCursor

# --- Logic Functions ---

def luhn_check(card_number):
    try:
        digits = [int(d) for d in str(card_number)]
        checksum = 0
        reverse_digits = digits[::-1]
        for i, digit in enumerate(reverse_digits):
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        return checksum % 10 == 0
    except:
        return False

def calculate_luhn_digit(partial_cc):
    digits = [int(d) for d in str(partial_cc)]
    digits.append(0)
    checksum = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return (10 - (checksum % 10)) % 10

def get_card_brand(card_number):
    brands = {
        '^4[0-9]{12}(?:[0-9]{3})?$': 'Visa', 
        '^5[1-5][0-9]{14}$': 'MasterCard', 
        '^3[47][0-9]{13}$': 'American Express', 
        '^6(?:011|5[0-9]{2})[0-9]{12}$': 'Discover', 
        '^3(?:0[0-5]|[68][0-9])[0-9]{11}$': 'Diners Club', 
        '^(?:2131|1800|35\\d{3})\\d{11}$': 'JCB'
    }
    for pattern, brand in brands.items():
        if re.match(pattern, str(card_number)):
            return brand
    return 'Unknown'

def get_bin_info(card_number):
    try:
        bin_number = str(card_number)[:6]
        url = f'https://lookup.binlist.net/{bin_number}'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'Bank': data.get('bank', {}).get('name', 'Unknown'), 
                'Country': data.get('country', {}).get('name', 'Unknown'), 
                'Type': data.get('type', 'Unknown'), 
                'Brand': data.get('scheme', 'Unknown').capitalize()
            }
    except: pass
    return {'Error': 'Info non disponible'}

def logic_validate(logger, cc_num):
    cc_num = str(cc_num).replace(' ', '').replace('-', '').strip()
    if not cc_num.isdigit():
        logger.emit("<font color='#ef4444'>[-] Numéro invalide (chiffres uniquement).</font>")
        return

    logger.emit(f"<font color='#3b82f6'><b>[*] Analyse de {cc_num[:6]}...</b></font>")
    
    # Luhn
    if luhn_check(cc_num):
        logger.emit("<font color='#22c55e'>[+] LUHN: VALIDE</font>")
    else:
        logger.emit("<font color='#ef4444'>[-] LUHN: INVALIDE</font>")
        return

    # Brand
    brand = get_card_brand(cc_num)
    logger.emit(f"<font color='#e4e4e7'>    Marque: {brand}</font>")

    # BIN
    bin_info = get_bin_info(cc_num)
    if 'Error' not in bin_info:
        logger.emit(f"<font color='#e4e4e7'>    Banque: {bin_info.get('Bank')}</font>")
        logger.emit(f"<font color='#e4e4e7'>    Pays: {bin_info.get('Country')}</font>")
        logger.emit(f"<font color='#e4e4e7'>    Type: {bin_info.get('Type')}</font>")
        logger.emit(f"<font color='#e4e4e7'>    Niveau: {bin_info.get('Brand')}</font>")
    else:
        logger.emit("<font color='#a1a1aa'>[-] Info BIN non disponible (Rate limit ou inconnu).</font>")

def logic_generate(logger, bin_format, amount, month, year, cvv):
    if not amount or not str(amount).isdigit():
        amount = 10

    logger.emit(f"<font color='#3b82f6'><b>[*] Génération de {amount} cartes...</b></font>")
    
    if not bin_format:
        bin_format = "453598xxxxxxxxxx"
    
    clean_bin = bin_format.lower().replace(' ', '')
    
    # Pre-check BIN info
    logger.emit(f"<font color='#a1a1aa'>[*] Récupération infos BIN {clean_bin[:6]}...</font>")
    b_info = get_bin_info(clean_bin)
    info_str = f"{b_info.get('Brand')} - {b_info.get('Bank')} ({b_info.get('Country')})"
    logger.emit(f"<font color='#e4e4e7'>    Cible: {info_str}</font>")
    
    generated_text = ""
    try:
        for i in range(int(amount)):
            temp_cc = ""
            for char in clean_bin:
                if char == 'x': temp_cc += str(random.randint(0, 9))
                else: temp_cc += char
                
            # Auto-detect length target (15 for Amex starting with 3, else 16)
            target_len = 15 if temp_cc.startswith('3') else 16
            
            while len(temp_cc) < (target_len - 1):
                temp_cc += str(random.randint(0, 9))
                
            temp_cc = temp_cc[:target_len-1]
            
            check = calculate_luhn_digit(temp_cc)
            final_cc = temp_cc + str(check)
            
            m = month if month else f"{random.randint(1,12):02d}"
            y = year if year else f"{random.randint(24,30)}"
            c = cvv if cvv else f"{random.randint(100,999)}"
            if target_len == 15 and len(c) == 3: c = f"{random.randint(1000,9999)}"
            
            # Random Name
            firsts = ["Pierre", "Paul", "Jacques", "Marie", "Sophie", "Jean", "Michel", "Nathalie", "Isabelle", "Thomas", "Lucas", "Lea"]
            lasts = ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy", "Moreau", "Simon", "Laurent"]
            rnd_name = f"{random.choice(firsts)} {random.choice(lasts)}"

            full = f"{final_cc}|{m}|{y}|{c}"
            
            # Format Bloc Note
            block = f"Carte {i + 1}\n"
            block += "----------\n"
            block += f"Numero : {final_cc}\n"
            block += f"Date   : {m}/{y}\n"
            block += f"CVV    : {c}\n"
            block += f"Nom    : {rnd_name.upper()}\n"
            block += f"Infos  : {info_str}\n\n"
            
            generated_text += block
            logger.emit(f"<font color='#22c55e'>[+] {full} -> VALIDE (Luhn)</font>")
            
        output_dir = os.path.join('output', 'CC Generator')
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        
        file_path = os.path.join(output_dir, 'generated_cc.txt')
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(generated_text)
        logger.emit(f"<font color='#22c55e'>[+] Sauvegardé dans {file_path}</font>")
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

class CCToolWindow(QMainWindow):
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
        
        title_label = QLabel("LE M // CC INTELLIGENCE")
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

        self.menu_label = QLabel("CC Tool - LE M")
        self.menu_label.setObjectName("MenuLabel")
        self.menu_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.menu_label)

        # Scroll Area for Buttons
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background: transparent; border: none;")
        
        self.stacked_widget = QStackedWidget()
        
        # --- Page Menu (0) ---
        page_menu = QWidget()
        layout_menu = QVBoxLayout(page_menu)
        layout_menu.setSpacing(10)
        layout_menu.setContentsMargins(0, 20, 0, 20)
        
        btn_go_valid = QPushButton("✅  Validateur")
        btn_go_gen = QPushButton("🎲  Générateur")
        
        for btn in [btn_go_valid, btn_go_gen]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_menu.addWidget(btn)
        layout_menu.addStretch()
        
        self.stacked_widget.addWidget(page_menu)
        
        # --- Page Validator (1) ---
        page_valid = QWidget()
        layout_valid = QVBoxLayout(page_valid)
        layout_valid.setSpacing(8)
        layout_valid.setContentsMargins(0, 0, 0, 0)
        
        self.input_cc = QLineEdit()
        self.input_cc.setPlaceholderText("Numéro de Carte")
        layout_valid.addWidget(self.input_cc)
        
        self.btn_validate = QPushButton("✅  Valider Carte")
        self.btn_validate.setObjectName("ActionBtn")
        self.btn_validate.setCursor(Qt.PointingHandCursor)
        layout_valid.addWidget(self.btn_validate)
        
        btn_back_valid = QPushButton("⬅️  Retour")
        btn_back_valid.setObjectName("ActionBtn")
        btn_back_valid.setCursor(Qt.PointingHandCursor)
        layout_valid.addWidget(btn_back_valid)
        
        layout_valid.addStretch()
        self.stacked_widget.addWidget(page_valid)
        
        # --- Page Generator (2) ---
        page_gen = QWidget()
        layout_gen = QVBoxLayout(page_gen)
        layout_gen.setSpacing(8)
        layout_gen.setContentsMargins(0, 0, 0, 0)
        
        self.inp_bin = QLineEdit()
        self.inp_bin.setPlaceholderText("Format BIN (ex: 453598xxxxxxxxxx)")
        layout_gen.addWidget(self.inp_bin)
        
        hbox_date = QHBoxLayout()
        self.inp_month = QLineEdit()
        self.inp_month.setPlaceholderText("MM")
        self.inp_year = QLineEdit()
        self.inp_year.setPlaceholderText("YY")
        self.inp_cvv = QLineEdit()
        self.inp_cvv.setPlaceholderText("CVV")
        hbox_date.addWidget(self.inp_month)
        hbox_date.addWidget(self.inp_year)
        hbox_date.addWidget(self.inp_cvv)
        layout_gen.addLayout(hbox_date)
        
        self.btn_gen = QPushButton("🚀  Générer & Vérifier")
        self.btn_gen.setObjectName("ActionBtn")
        self.btn_gen.setCursor(Qt.PointingHandCursor)
        layout_gen.addWidget(self.btn_gen)
        
        btn_back_gen = QPushButton("⬅️  Retour")
        btn_back_gen.setObjectName("ActionBtn")
        btn_back_gen.setCursor(Qt.PointingHandCursor)
        layout_gen.addWidget(btn_back_gen)
        
        layout_gen.addStretch()
        self.stacked_widget.addWidget(page_gen)
        
        # --- Connections ---
        btn_go_valid.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        btn_go_gen.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        btn_back_valid.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_back_gen.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        self.btn_validate.clicked.connect(lambda: self.start_task(logic_validate, self.input_cc.text()))
        self.btn_gen.clicked.connect(self.action_generate)

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

    def action_generate(self):
        amount, ok = QInputDialog.getInt(self, "Générateur", "Nombre de cartes à générer :", 10, 1, 1000)
        if ok:
            self.start_task(logic_generate, self.inp_bin.text(), amount, self.inp_month.text(), self.inp_year.text(), self.inp_cvv.text())

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
    window = CCToolWindow()
    window.show()
    sys.exit(app.exec_())