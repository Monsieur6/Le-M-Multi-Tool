import os
import random
import sys
import time

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextBrowser, QFrame, QGraphicsDropShadowEffect, 
                             QScrollArea, QComboBox, QSpinBox, QStackedWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor

# --- Logic ---

iban_formats = {
    'FR': {'length': 27, 'bban': 'BBBBBGSSSCCCCCCCCCCCCCCC', 'name': 'France'},
    'DE': {'length': 22, 'bban': 'BBBBBBBBCCCCCCCCCC', 'name': 'Germany'},
    'ES': {'length': 24, 'bban': 'BBBBGSSSCCCCCCCCCCCC', 'name': 'Spain'},
    'IT': {'length': 27, 'bban': 'KBBBBBBSSSSSCCCCCCCCCCCC', 'name': 'Italy'},
    'GB': {'length': 22, 'bban': 'BBBBSSSSSSCCCCCCCCCC', 'name': 'United Kingdom'},
    'BE': {'length': 16, 'bban': 'BBBCCCCCCCCCC', 'name': 'Belgium'},
    'NL': {'length': 18, 'bban': 'BBBBCCCCCCCCCC', 'name': 'Netherlands'},
    'CH': {'length': 21, 'bban': 'BBBBBKCCCCCCCCCCC', 'name': 'Switzerland'},
    'LU': {'length': 20, 'bban': 'BBBCCCCCCCCCCCCC', 'name': 'Luxembourg'},
    'PT': {'length': 25, 'bban': 'BBBBSSSSCCCCCCCCCCCBB', 'name': 'Portugal'},
    'AT': {'length': 20, 'bban': 'BBBBBCCCCCCCCCCCC', 'name': 'Austria'},
    'IE': {'length': 22, 'bban': 'BBBBSSSSSSCCCCCCCCCC', 'name': 'Ireland'}
}

def generate_bban(country_code):
    format_str = iban_formats[country_code]['bban']
    return ''.join((str(random.randint(0, 9)) for _ in format_str))

def calculate_check_digits(country_code, bban):
    temp = bban + country_code + '00'
    numeric = ''.join((str(ord(c) - 55) if c.isalpha() else c for c in temp))
    return f'{98 - int(numeric) % 97:02d}'

def generate_iban(country_code):
    bban = generate_bban(country_code)
    check_digits = calculate_check_digits(country_code, bban)
    return f'{country_code}{check_digits}{bban}'

def logic_generate(logger, country_name, count):
    # Find code from name
    code = None
    for k, v in iban_formats.items():
        if v['name'] == country_name:
            code = k
            break
    
    if not code:
        logger.emit("<font color='#ef4444'>[-] Pays invalide.</font>")
        return

    logger.emit(f"<font color='#3b82f6'><b>[*] Génération de {count} IBANs pour {country_name} ({code})...</b></font>")
    
    for i in range(count):
        iban = generate_iban(code)
        logger.emit(f"<font color='#22c55e'>{iban}</font>")
        time.sleep(0.05) # Small delay for effect
        
    logger.emit(f"<font color='#3b82f6'><b>[*] Terminé.</b></font>")

def logic_check(logger, iban):
    iban = iban.replace(' ', '').upper()
    if not (15 <= len(iban) <= 34 and iban[:2].isalpha()):
        logger.emit(f"<font color='#ef4444'>[-] Format IBAN invalide (longueur ou code pays).</font>")
        return

    # Déplacer les 4 premiers caractères à la fin
    rearranged_iban = iban[4:] + iban[:4]
    
    # Remplacer les lettres par des chiffres
    numeric_iban = ""
    for char in rearranged_iban:
        if char.isalpha():
            numeric_iban += str(ord(char) - ord('A') + 10)
        else:
            numeric_iban += char
    
    try:
        if int(numeric_iban) % 97 == 1:
            logger.emit(f"<font color='#22c55e'>[+] L'IBAN '{iban}' est <b>valide</b>.</font>")
        else:
            logger.emit(f"<font color='#ef4444'>[-] L'IBAN '{iban}' est <b>invalide</b> (checksum incorrect).</font>")
    except ValueError:
        logger.emit(f"<font color='#ef4444'>[-] Erreur de conversion de l'IBAN.</font>")

# --- Worker ---

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

# --- Window ---

class IbanGenWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(1000, 650)
        self.worker = None
        self.oldPos = self.pos()
        
        # Container
        self.container = QFrame()
        self.container.setObjectName("MainContainer")
        self.setCentralWidget(self.container)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0,0,0,180))
        self.container.setGraphicsEffect(shadow)
        
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)
        
        # Title Bar
        self.title_bar = QFrame()
        self.title_bar.setObjectName("TitleBar")
        self.title_bar.setFixedHeight(40)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(15,0,10,0)
        
        title_label = QLabel("LE M // Iban Generator")
        title_label.setObjectName("TitleLabel")
        
        btn_min = QPushButton("─")
        btn_min.setObjectName("TitleBtn")
        btn_min.setFixedSize(30,30)
        btn_min.clicked.connect(self.showMinimized)
        
        btn_close = QPushButton("✕")
        btn_close.setObjectName("TitleBtnClose")
        btn_close.setFixedSize(30,30)
        btn_close.clicked.connect(self.close)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(btn_min)
        title_layout.addWidget(btn_close)
        
        self.main_layout.addWidget(self.title_bar)
        
        # Content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0,0,0,0)
        
        # Left Panel
        left_panel = QFrame()
        left_panel.setObjectName("SidePanel")
        left_panel.setFixedWidth(320)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(15, 20, 15, 20)
        
        menu_label = QLabel("Iban Gen - LE M")
        menu_label.setObjectName("MenuLabel")
        menu_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(menu_label)
        
        # Scroll Area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background: transparent; border: none;")
        
        self.stacked_widget = QStackedWidget()
        
        # --- Page 0: Menu ---
        page_menu = QWidget()
        layout_menu = QVBoxLayout(page_menu)
        layout_menu.setSpacing(15)
        layout_menu.setContentsMargins(0, 20, 0, 20)
        
        btn_menu_gen = QPushButton("🎲  Générateur >")
        btn_menu_check = QPushButton("🔍  Vérificateur >")
        
        for btn in [btn_menu_gen, btn_menu_check]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_menu.addWidget(btn)
        layout_menu.addStretch()
        
        self.stacked_widget.addWidget(page_menu)
        
        # --- Page 1: Generator ---
        page_gen = QWidget()
        layout_gen = QVBoxLayout(page_gen)
        layout_gen.setSpacing(8)
        layout_gen.setContentsMargins(0, 0, 0, 0)
        
        lbl_country = QLabel("Pays :")
        lbl_country.setStyleSheet("color: #a1a1aa; font-weight: bold;")
        layout_gen.addWidget(lbl_country)
        
        self.combo_country = QComboBox()
        countries = [v['name'] for v in iban_formats.values()]
        countries.sort()
        self.combo_country.addItems(countries)
        layout_gen.addWidget(self.combo_country)
        
        lbl_count = QLabel("Nombre :")
        lbl_count.setStyleSheet("color: #a1a1aa; font-weight: bold;")
        layout_gen.addWidget(lbl_count)
        
        self.spin_count = QSpinBox()
        self.spin_count.setRange(1, 1000)
        self.spin_count.setValue(1)
        self.spin_count.setStyleSheet("""
            QSpinBox { background-color: #27272a; border: 1px solid #27272a; border-radius: 8px; padding: 10px; color: #f4f4f5; font-family: 'Consolas'; font-size: 14px; }
            QSpinBox::up-button, QSpinBox::down-button { background: transparent; }
        """)
        layout_gen.addWidget(self.spin_count)
        
        self.btn_gen = QPushButton("🎲  Générer")
        self.btn_gen.setObjectName("ActionBtn")
        self.btn_gen.setCursor(Qt.PointingHandCursor)
        self.btn_gen.clicked.connect(self.action_generate)
        layout_gen.addWidget(self.btn_gen)
        
        btn_back_gen = QPushButton("⬅️  Retour")
        btn_back_gen.setObjectName("ActionBtn")
        btn_back_gen.setCursor(Qt.PointingHandCursor)
        layout_gen.addWidget(btn_back_gen)
        layout_gen.addStretch()
        
        self.stacked_widget.addWidget(page_gen)
        
        # --- Page 2: Checker ---
        page_check = QWidget()
        layout_check = QVBoxLayout(page_check)
        layout_check.setSpacing(8)
        layout_check.setContentsMargins(0, 0, 0, 0)
        
        lbl_check = QLabel("Vérifier un IBAN :")
        lbl_check.setStyleSheet("color: #a1a1aa; font-weight: bold;")
        layout_check.addWidget(lbl_check)
        
        self.input_check_iban = QLineEdit()
        self.input_check_iban.setPlaceholderText("FR76...")
        layout_check.addWidget(self.input_check_iban)
        
        self.btn_check = QPushButton("🔍  Vérifier IBAN")
        self.btn_check.setObjectName("CheckBtn")
        self.btn_check.setCursor(Qt.PointingHandCursor)
        self.btn_check.clicked.connect(self.action_check)
        layout_check.addWidget(self.btn_check)
        
        btn_back_check = QPushButton("⬅️  Retour")
        btn_back_check.setObjectName("ActionBtn")
        btn_back_check.setCursor(Qt.PointingHandCursor)
        layout_check.addWidget(btn_back_check)
        layout_check.addStretch()
        
        self.stacked_widget.addWidget(page_check)
        
        # Navigation
        btn_menu_gen.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        btn_menu_check.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        btn_back_gen.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_back_check.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
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
        
        # Right Panel
        right_panel = QWidget()
        right_panel.setObjectName("RightPanel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0,0,0,0)
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
        right_layout.addWidget(self.console)
        
        self.status_bar = QFrame()
        self.status_bar.setObjectName("StatusBar")
        self.status_bar.setFixedHeight(30)
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(10,0,10,0)
        self.status_label = QLabel("Système Prêt")
        self.status_label.setObjectName("StatusLabel")
        status_layout.addWidget(self.status_label)
        right_layout.addWidget(self.status_bar)
        
        content_layout.addWidget(left_panel)
        content_layout.addWidget(right_panel)
        self.main_layout.addLayout(content_layout)
        
        self.apply_styles()
        
        # Animation
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
            QComboBox { background-color: #27272a; border: 1px solid #27272a; border-radius: 8px; padding: 12px; color: #f4f4f5; font-family: 'Consolas', monospace; font-size: 14px; }
            QComboBox::drop-down { border: none; background: transparent; }
            QComboBox::down-arrow { image: none; border: none; }
            QComboBox QAbstractItemView { background-color: #27272a; color: #f4f4f5; selection-background-color: #3f3f46; selection-color: #ffffff; border: 1px solid #3f3f46; }
            QLineEdit { background-color: #27272a; border: 1px solid #27272a; border-radius: 8px; padding: 12px; color: #f4f4f5; font-family: 'Consolas', monospace; font-size: 14px; }
            QLineEdit:focus { border: 1px solid #6366f1; background-color: #202023; }
            QPushButton { background-color: #18181b; border: 1px solid #27272a; border-radius: 8px; padding: 12px 20px; color: #e4e4e7; font-weight: 600; text-align: left; }
            QPushButton:hover { background-color: #27272a; border-color: #3f3f46; color: #ffffff; }
            QPushButton:pressed { background-color: #3f3f46; }
            QPushButton#ActionBtn { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #7c3aed); border: 1px solid #6366f1; color: #ffffff; text-align: center; }
            QPushButton#ActionBtn:hover { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4338ca, stop:1 #6d28d9); border: 1px solid #818cf8; }
            QPushButton#ExitBtn { background-color: #18181b; border: 1px solid #ef4444; color: #ef4444; text-align: center; }
            QPushButton#ExitBtn:hover { background-color: #ef4444; color: #fff; }
            QPushButton#ClearBtn, QPushButton#CheckBtn { text-align: center; }
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

    def action_generate(self):
        country = self.combo_country.currentText()
        count = self.spin_count.value()
        self.start_task(logic_generate, country, count)

    def action_check(self):
        iban_to_check = self.input_check_iban.text().strip()
        if not iban_to_check:
            self.log_message("<font color='#ef4444'>[-] Veuillez entrer un IBAN à vérifier.</font>")
            return
        self.start_task(logic_check, iban_to_check)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = IbanGenWindow()
    window.show()
    sys.exit(app.exec_())
