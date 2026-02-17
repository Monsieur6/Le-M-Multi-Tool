import sys
import os
import random
import string
import datetime
from PIL import Image, ImageDraw, ImageFont

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextBrowser, QFrame, QGraphicsDropShadowEffect, 
                             QScrollArea, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor

# --- Logic ---

IMAGE_PATH = 'input/paypal.png'
OUTPUT_DIR = os.path.join('output', 'Fake Image Paypal')
OUTPUT_PATH = os.path.join(OUTPUT_DIR, 'paypal_sortie.png')
BG_COLOR = (245, 247, 252)

positions = {
    'amount': {'x1': 43, 'y1': 116, 'x2': 533, 'y2': 155, 'font_size': 31, 'font_path': 'arialbd.ttf'},
    'name': {'x1': 350, 'y1': 121, 'x2': 529, 'y2': 149, 'font_size': 38, 'font_path': 'arialbd.ttf'},
    'date': {'x1': 436, 'y1': 252, 'x2': 533, 'y2': 275, 'font_size': 11, 'font_path': 'arial.ttf'},
    'id': {'x1': 36, 'y1': 252, 'x2': 163, 'y2': 275, 'font_size': 11, 'font_path': 'arialbd.ttf'},
    'eur1': {'x1': 495, 'y1': 324, 'x2': 532, 'y2': 338, 'font_size': 13, 'font_path': 'arial.ttf'},
    'eur2': {'x1': 495, 'y1': 352, 'x2': 532, 'y2': 366, 'font_size': 13, 'font_path': 'arial.ttf'},
    'eur3': {'x1': 495, 'y1': 479, 'x2': 532, 'y2': 493, 'font_size': 13, 'font_path': 'arialbd.ttf'},
    'eur4': {'x1': 495, 'y1': 416, 'x2': 532, 'y2': 435, 'font_size': 11, 'font_path': 'arial.ttf'},
    'payment': {'x1': 38, 'y1': 421, 'x2': 166, 'y2': 431, 'font_size': 11, 'font_path': 'arialbd.ttf'},
    'val1': {'x1': 415, 'y1': 324, 'x2': 495, 'y2': 338, 'font_size': 13, 'font_path': 'arial.ttf'},
    'val2': {'x1': 415, 'y1': 352, 'x2': 495, 'y2': 366, 'font_size': 13, 'font_path': 'arial.ttf'},
    'val3': {'x1': 415, 'y1': 479, 'x2': 495, 'y2': 493, 'font_size': 13, 'font_path': 'arialbd.ttf'},
    'val4': {'x1': 415, 'y1': 416, 'x2': 495, 'y2': 435, 'font_size': 11, 'font_path': 'arialbd.ttf'}
}

def generate_random_id(length=16):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def generate_random_last4():
    return ''.join((random.choice(string.digits) for _ in range(4)))

def draw_text(draw, key, text, subtle_bold=False, y_offset=0, align='center', extra_dx=0):
    if not text: return
    
    info = positions[key]
    x1, y1, x2, y2 = (info['x1'], info['y1'], info['x2'], info['y2'])
    font_size = info['font_size']
    
    try:
        font = ImageFont.truetype(info['font_path'], font_size)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

    draw.rectangle([x1, y1, x2, y2], fill=BG_COLOR)
    
    cx = (x1 + x2) / 2 + extra_dx
    cy = (y1 + y2) / 2 + y_offset
    anchor = 'mm'
    
    if align == 'right':
        cx = x2 - 2 + extra_dx
        anchor = 'rm'
    elif align == 'left':
        cx = x1 + 2 + extra_dx
        anchor = 'lm'
        
    color = (0, 102, 204) if key == 'id' else (0, 0, 0)
    
    draw.text((cx, cy), text, font=font, fill=color, anchor=anchor, stroke_width=1 if subtle_bold else 0, stroke_fill=color)
    
    if key == 'id':
        bbox = draw.textbbox((cx, cy), text, font=font, anchor=anchor)
        underline_y = bbox[3] + 1
        draw.line([(bbox[0], underline_y), (bbox[2], underline_y)], fill=color, width=1)

def logic_generate(logger, amount, name, date, currency):
    if not os.path.exists('input'): os.makedirs('input')
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    
    if not os.path.exists(IMAGE_PATH):
        logger.emit(f"<font color='#ef4444'>[-] Image template introuvable: {IMAGE_PATH}</font>")
        return

    logger.emit(f"<font color='#3b82f6'><b>[*] Génération du reçu PayPal...</b></font>")
    
    try:
        img = Image.open(IMAGE_PATH).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        gen_id = generate_random_id()
        gen_payment = f'MASTER_CARD x-{generate_random_last4()}'
        
        # Formater le montant (ex: 15,00)
        try:
            amount_val = float(amount.replace(',', '.'))
            amount_str = f"{amount_val:.2f}".replace('.', ',')
        except:
            amount_str = amount.replace('.', ',')
        
        # Nettoyer toute la zone de titre pour enlever les artefacts ":" ou autres
        draw.rectangle([positions['amount']['x1'], positions['amount']['y1']-5, positions['amount']['x2'], positions['amount']['y2']+5], fill=BG_COLOR)
        
        # Titre principal concaténé pour éviter les trous
        full_title = f"{amount_str} {currency} EUR à {name}"
        draw_text(draw, 'amount', full_title, subtle_bold=True, align='center')
        
        # Date
        draw_text(draw, 'date', date)
        
        # Mode de paiement
        draw_text(draw, 'payment', gen_payment, y_offset=-3)
        draw_text(draw, 'val4', amount_str, align='right')
        draw_text(draw, 'eur4', f"{currency} EUR", align='left')
        
        # ID de transaction
        draw_text(draw, 'id', gen_id)
        
        # Colonnes de montants
        draw_text(draw, 'val1', amount_str, align='right')
        draw_text(draw, 'val2', "0,00", align='right')
        draw_text(draw, 'val3', amount_str, align='right')
        
        # Colonnes de devises (symbole + EUR)
        for k in ['eur1', 'eur2', 'eur3']:
            draw_text(draw, k, f"{currency} EUR", align='left')
            
        img.save(OUTPUT_PATH)
        logger.emit(f"<font color='#22c55e'>[+] Image générée avec succès !</font>")
        logger.emit(f"<font color='#22c55e'>    Sauvegardé dans: {OUTPUT_PATH}</font>")
        
        if os.name == 'nt':
            os.startfile(os.path.abspath(OUTPUT_PATH))
            
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

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

class FakePaypalWindow(QMainWindow):
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
        
        title_label = QLabel("LE M // Fake Paypal Screen")
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
        left_layout.setSpacing(15)
        left_layout.setContentsMargins(20,20,20,20)
        
        menu_label = QLabel("Fake Paypal - LE M")
        menu_label.setObjectName("MenuLabel")
        menu_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(menu_label)
        
        # Inputs
        lbl_amount = QLabel("Montant :")
        lbl_amount.setStyleSheet("color: #a1a1aa; font-weight: bold;")
        left_layout.addWidget(lbl_amount)
        
        self.input_amount = QLineEdit()
        self.input_amount.setPlaceholderText("ex: 15,00")
        left_layout.addWidget(self.input_amount)
        
        lbl_name = QLabel("Nom :")
        lbl_name.setStyleSheet("color: #a1a1aa; font-weight: bold;")
        left_layout.addWidget(lbl_name)
        
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("ex: Le M")
        left_layout.addWidget(self.input_name)
        
        lbl_date = QLabel("Date :")
        lbl_date.setStyleSheet("color: #a1a1aa; font-weight: bold;")
        left_layout.addWidget(lbl_date)
        
        self.input_date = QLineEdit()
        self.input_date.setText(datetime.datetime.now().strftime("%d %b %Y"))
        left_layout.addWidget(self.input_date)
        
        lbl_curr = QLabel("Devise :")
        lbl_curr.setStyleSheet("color: #a1a1aa; font-weight: bold;")
        left_layout.addWidget(lbl_curr)
        
        self.combo_curr = QComboBox()
        self.combo_curr.addItems(["€", "$", "£"])
        left_layout.addWidget(self.combo_curr)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #333; max-height: 1px;")
        left_layout.addWidget(line)
        
        self.btn_gen = QPushButton("🎨  Générer Image")
        self.btn_gen.setObjectName("ActionBtn")
        self.btn_gen.setCursor(Qt.PointingHandCursor)
        self.btn_gen.clicked.connect(self.action_generate)
        left_layout.addWidget(self.btn_gen)
        
        left_layout.addStretch()
        
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
            QPushButton#ClearBtn { text-align: center; }
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
        amount = self.input_amount.text().strip()
        name = self.input_name.text().strip()
        date = self.input_date.text().strip()
        curr = self.combo_curr.currentText()
        
        if not amount or not name:
            self.log_message("<font color='#ef4444'>[-] Veuillez remplir le montant et le nom.</font>")
            return
            
        self.start_task(logic_generate, amount, name, date, curr)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FakePaypalWindow()
    window.show()
    sys.exit(app.exec_())