import sys
import os
import random
import time
import subprocess
import qrcode
from PIL import Image, ImageDraw, ImageFont

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QFrame, QGraphicsDropShadowEffect, 
                             QScrollArea, QInputDialog, QMessageBox, QStyle, QStackedWidget, QCheckBox, QDateEdit, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve, QDate
from PyQt5.QtGui import QColor, QCursor, QIntValidator

# --- Logic Functions ---

def logic_generate_card(logger, data):
    logger.emit(f"<font color='#3b82f6'><b>[*] Génération de la carte d'identité...</b></font>")
    
    try:
        # Create Image
        width, height = 1011, 638 # Standard ID Card Ratio (~300 DPI)
        bg_color = (235, 245, 255) # Light Blueish background
        image = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(image)
        
        # Fonts
        try:
            font_header = ImageFont.truetype("arialbd.ttf", 55)
            font_label = ImageFont.truetype("arial.ttf", 28)
            font_val = ImageFont.truetype("arialbd.ttf", 32)
            font_mrz = ImageFont.truetype("consola.ttf", 45)
        except:
            logger.emit("<font color='#ef4444'>[!] Polices système introuvables, utilisation défaut.</font>")
            font_header = ImageFont.load_default()
            font_label = ImageFont.load_default()
            font_val = ImageFont.load_default()
            font_mrz = ImageFont.load_default()

        # --- Design ---
        
        # Header Strip
        header_text = data.get('header', 'REPUBLIQUE FRANCAISE').upper()
        draw.rectangle([(0, 0), (width, 100)], fill=(0, 51, 153)) # Dark Blue
        w_text = draw.textlength(header_text, font=font_header)
        draw.text(((width - w_text) / 2, 20), header_text, fill=(255, 255, 255), font=font_header)
        
        # Photo Placeholder
        photo_x, photo_y, photo_w, photo_h = 50, 130, 250, 320
        draw.rectangle([(photo_x, photo_y), (photo_x + photo_w, photo_y + photo_h)], fill=(200, 200, 200), outline=(100,100,100), width=2)
        draw.text((photo_x + 60, photo_y + 140), "PHOTO", fill=(150, 150, 150), font=font_header)

        # Fields Layout
        start_x = 340
        start_y = 130
        line_height = 75
        
        fields = [
            ("Nom / Surname", data.get('surname', '').upper()),
            ("Prénom(s) / Given names", data.get('name', '').title()),
            ("Sexe / Sex", data.get('gender', 'M').upper()), # Special handling
            ("Taille / Height", (data.get('height', '') + " cm") if data.get('height') else ""), # Special handling
            ("Adresse / Address", data.get('address', ''))
        ]
        
        current_y = start_y
        for label, value in fields:
            if "Sexe" in label:
                # Sexe + DOB on same line
                draw.text((start_x, current_y), "Sexe / Sex", fill=(0, 51, 153), font=font_label)
                draw.text((start_x, current_y + 30), value, fill=(0, 0, 0), font=font_val)
                
                draw.text((start_x + 250, current_y), "Né(e) le / Date of birth", fill=(0, 51, 153), font=font_label)
                draw.text((start_x + 250, current_y + 30), data.get('dob', ''), fill=(0, 0, 0), font=font_val)
            elif "Taille" in label:
                # Taille + Expiry on same line
                draw.text((start_x, current_y), label, fill=(0, 51, 153), font=font_label)
                draw.text((start_x, current_y + 30), value, fill=(0, 0, 0), font=font_val)
                
                draw.text((start_x + 250, current_y), "Expire le / Expiry", fill=(0, 51, 153), font=font_label)
                draw.text((start_x + 250, current_y + 30), data.get('expiry', ''), fill=(0, 0, 0), font=font_val)
            else:
                draw.text((start_x, current_y), label, fill=(0, 51, 153), font=font_label)
                draw.text((start_x, current_y + 30), value, fill=(0, 0, 0), font=font_val)
            
            current_y += line_height

        # ID Number
        idno = data.get('id_num') or str(random.randint(100000000, 999999999))
        draw.text((width - 320, 130), "N° Carte / Card No", fill=(0, 51, 153), font=font_label)
        draw.text((width - 320, 160), idno, fill=(200, 0, 0), font=font_val)

        # Fake Chip
        draw.rectangle([(60, 480), (140, 550)], fill=(210, 180, 140), outline=(180, 150, 100))

        # MRZ Generation
        mrz_y = height - 110
        surname_mrz = data.get('surname', 'NOM').upper().replace(' ', '<')
        name_mrz = data.get('name', 'PRENOM').upper().replace(' ', '<')
        line1 = f"IDFRA{surname_mrz}<<{name_mrz}"
        line1 = (line1 + "<" * 44)[:44]
        
        dob_mrz = data.get('dob', '010100').replace('/', '')[:6]
        sex_mrz = data.get('gender', 'M')[0].upper() if data.get('gender') else 'M'
        exp_mrz = data.get('expiry', '010130').replace('/', '')[:6]
        line2 = f"{idno}<{random.randint(0,9)}{dob_mrz}{random.randint(0,9)}{sex_mrz}{exp_mrz}{random.randint(0,9)}"
        line2 = (line2 + "<" * 44)[:44]
        
        draw.text((50, mrz_y), line1, fill=(0, 0, 0), font=font_mrz)
        draw.text((50, mrz_y + 50), line2, fill=(0, 0, 0), font=font_mrz)
            
        # QR Code
        if data.get('qr_enabled'):
            qr_data = data.get('qr_url') or f"{idno}|{surname_mrz}|{name_mrz}"
            qr = qrcode.make(qr_data)
            qr = qr.resize((150, 150))
            image.paste(qr, (width - 180, height - 250))
            
        # Save
        output_dir = os.path.join('output', 'ID Cards')
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        filename = f"id_card_{idno}.png"
        path = os.path.join(output_dir, filename)
        image.save(path)
        
        logger.emit(f"<font color='#22c55e'>[+] Carte générée : {path}</font>")
        
        # Open
        if os.name == 'nt':
            os.startfile(os.path.abspath(path))
            
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

class IDCardToolWindow(QMainWindow):
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
        
        title_label = QLabel("LE M // ID CARD FRAUD")
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

        self.menu_label = QLabel("ID Card Tool - LE M")
        self.menu_label.setObjectName("MenuLabel")
        self.menu_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.menu_label)

        # Scroll Area for Buttons/Inputs
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background: transparent; border: none;")
        
        self.stacked_widget = QStackedWidget()
        
        # --- Page Main ---
        page_main = QWidget()
        layout_main = QVBoxLayout(page_main)
        layout_main.setSpacing(8)
        layout_main.setContentsMargins(0, 0, 0, 0)
        
        self.btn_create = QPushButton("📝  Créer une Carte")
        self.btn_open = QPushButton("📂  Ouvrir Output")
        
        for btn in [self.btn_create, self.btn_open]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_main.addWidget(btn)
        layout_main.addStretch()
            
        # --- Page Form ---
        page_form = QWidget()
        layout_form = QVBoxLayout(page_form)
        layout_form.setSpacing(10)
        layout_form.setContentsMargins(0, 0, 0, 0)
        
        self.inputs = {}
        
        # Header
        self.inputs['header'] = QLineEdit()
        self.inputs['header'].setPlaceholderText("Pays / En-tête (ex: REPUBLIQUE FRANCAISE)")
        layout_form.addWidget(self.inputs['header'])

        # Surname
        self.inputs['surname'] = QLineEdit()
        self.inputs['surname'].setPlaceholderText("Nom de famille")
        layout_form.addWidget(self.inputs['surname'])

        # Name
        self.inputs['name'] = QLineEdit()
        self.inputs['name'].setPlaceholderText("Prénom(s)")
        layout_form.addWidget(self.inputs['name'])

        # Gender
        self.inputs['gender'] = QComboBox()
        self.inputs['gender'].addItems(["M", "F"])
        layout_form.addWidget(self.inputs['gender'])

        # DOB
        dob_layout = QHBoxLayout()
        self.inputs['dob'] = QDateEdit()
        self.inputs['dob'].setDisplayFormat("dd/MM/yyyy")
        self.inputs['dob'].setCalendarPopup(True)
        self.inputs['dob'].setDate(QDate.currentDate().addYears(-18))
        self.age_label = QLabel("Age: 18 ans")
        self.age_label.setStyleSheet("color: #a1a1aa; margin-left: 10px;")
        self.inputs['dob'].dateChanged.connect(self.update_age)
        dob_layout.addWidget(self.inputs['dob'])
        dob_layout.addWidget(self.age_label)
        layout_form.addLayout(dob_layout)

        # Height
        self.inputs['height'] = QComboBox()
        self.inputs['height'].addItems([str(i) for i in range(140, 221)])
        self.inputs['height'].setCurrentText("175")
        layout_form.addWidget(self.inputs['height'])

        # ID Num
        self.inputs['id_num'] = QLineEdit()
        self.inputs['id_num'].setPlaceholderText("Numéro ID (Optionnel)")
        layout_form.addWidget(self.inputs['id_num'])

        # Expiry
        self.inputs['expiry'] = QDateEdit()
        self.inputs['expiry'].setDisplayFormat("dd/MM/yyyy")
        self.inputs['expiry'].setCalendarPopup(True)
        self.inputs['expiry'].setDate(QDate.currentDate().addYears(10))
        layout_form.addWidget(self.inputs['expiry'])

        # Address
        self.inputs['address'] = QLineEdit()
        self.inputs['address'].setPlaceholderText("Adresse (Ville, Pays)")
        layout_form.addWidget(self.inputs['address'])
            
        # QR Options
        qr_layout = QHBoxLayout()
        self.chk_qr = QCheckBox("QR Code")
        self.chk_qr.setStyleSheet("color: #e4e4e7;")
        self.inp_qr_url = QLineEdit()
        self.inp_qr_url.setPlaceholderText("URL QR (Optionnel)")
        qr_layout.addWidget(self.chk_qr)
        qr_layout.addWidget(self.inp_qr_url)
        layout_form.addLayout(qr_layout)
        
        self.btn_gen = QPushButton("🚀  Générer")
        self.btn_gen.setObjectName("ActionBtn")
        self.btn_gen.setCursor(Qt.PointingHandCursor)
        layout_form.addWidget(self.btn_gen)
        
        btn_back = QPushButton("⬅️  Retour")
        btn_back.setObjectName("ActionBtn")
        btn_back.setCursor(Qt.PointingHandCursor)
        layout_form.addWidget(btn_back)
        
        self.stacked_widget.addWidget(page_main)
        self.stacked_widget.addWidget(page_form)
        
        # Navigation
        self.btn_create.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        btn_back.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        # Actions
        self.btn_gen.clicked.connect(self.action_generate)
        self.btn_open.clicked.connect(self.action_open_folder)

        scroll_area.setWidget(self.stacked_widget)
        left_layout.addWidget(scroll_area)

        self.btn_clear = QPushButton("🧹  Effacer Console")
        self.btn_clear.setObjectName("ClearBtn")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear_logs)
        left_layout.addWidget(self.btn_clear)

        btn_exit = QPushButton("⬅️  Retour")
        btn_exit.setObjectName("ExitBtn")
        btn_exit.setCursor(Qt.PointingHandCursor)
        btn_exit.clicked.connect(self.close)
        left_layout.addWidget(btn_exit)

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
            QComboBox, QDateEdit { background-color: #27272a; border: 1px solid #27272a; border-radius: 8px; padding: 12px; color: #f4f4f5; font-family: 'Consolas', monospace; font-size: 14px; }
            QComboBox::drop-down, QDateEdit::drop-down { border: none; background: transparent; }
            QComboBox::down-arrow, QDateEdit::down-arrow { image: none; border: none; }
            QComboBox QAbstractItemView {
                background-color: #27272a;
                color: #f4f4f5;
                selection-background-color: #3f3f46;
                selection-color: #ffffff;
                border: 1px solid #3f3f46;
            }
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

    def update_age(self):
        dob = self.inputs['dob'].date()
        today = QDate.currentDate()
        age = today.year() - dob.year()
        if today.month() < dob.month() or (today.month() == dob.month() and today.day() < dob.day()):
            age -= 1
        self.age_label.setText(f"Age: {age} ans")

    def action_generate(self):
        data = {}
        for k, v in self.inputs.items():
            if isinstance(v, QLineEdit): data[k] = v.text().strip()
            elif isinstance(v, QComboBox): data[k] = v.currentText()
            elif isinstance(v, QDateEdit): data[k] = v.date().toString("dd/MM/yyyy")
            
        data['qr_enabled'] = self.chk_qr.isChecked()
        data['qr_url'] = self.inp_qr_url.text().strip()
        
        if not data['surname'] or not data['name']:
            self.log_message("<font color='#ef4444'>[-] Champs 'Nom' et 'Prénom' requis.</font>")
            return
            
        self.start_task(logic_generate_card, data)

    def action_open_folder(self):
        if not os.path.exists('output'): os.makedirs('output')
        if os.name == 'nt':
            os.startfile(os.path.abspath('output'))
        else:
            subprocess.call(['xdg-open', 'output'])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = IDCardToolWindow()
    window.show()
    sys.exit(app.exec_())