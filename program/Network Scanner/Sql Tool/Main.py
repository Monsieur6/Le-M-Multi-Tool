import sys
import os
import requests
import threading
import time
import random
import urllib3
import concurrent.futures

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QFrame, QGraphicsDropShadowEffect, 
                             QScrollArea, QFileDialog, QInputDialog, QMessageBox, QStyle, QStackedWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QCursor

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}

# --- Logic Functions ---

def logic_sqli_scan(logger, url):
    if not url: 
        logger.emit("<font color='#ef4444'>[-] URL requise.</font>")
        return
    
    if not url.startswith("http"):
        url = "http://" + url
        
    logger.emit(f"<font color='#3b82f6'><b>[*] Scan SQL Injection sur {url}...</b></font>")
    
    errors = {
        "MySQL": ["You have an error in your SQL syntax;", "Warning: mysql_", "MySQL server version"],
        "SQL Server": ["Unclosed quotation mark after the character string", "Microsoft OLE DB Provider", "SQL Server"],
        "PostgreSQL": ["syntax error at or near", "PostgreSQL query failed"],
        "Oracle": ["ORA-01756", "quoted string not properly terminated"],
        "Access": ["Syntax error in query expression", "Data type mismatch in criteria expression"]
    }
    
    payloads = ["'", '"', "';", '"', "')"]
    vulnerable = False
    
    for p in payloads:
        target = f"{url}{p}"
        try:
            r = requests.get(target, headers=HEADERS, timeout=5, verify=False)
            for db, errs in errors.items():
                for err in errs:
                    if err in r.text:
                        logger.emit(f"<font color='#22c55e'>[+] Vulnérabilité Potentielle ({db}) !</font>")
                        logger.emit(f"<font color='#e4e4e7'>    Payload: {p}</font>")
                        logger.emit(f"<font color='#e4e4e7'>    Erreur: {err}</font>")
                        vulnerable = True
                        break
                if vulnerable: break
        except Exception as e:
            logger.emit(f"<font color='#ef4444'>[-] Erreur requête: {e}</font>")
        
        if vulnerable: break
        
    if not vulnerable:
        logger.emit(f"<font color='#ef4444'>[-] Aucune erreur SQL évidente trouvée avec les payloads basiques.</font>")

def logic_search_dump(logger, folder, search_term):
    if not folder or not os.path.isdir(folder):
        logger.emit("<font color='#ef4444'>[-] Dossier invalide.</font>")
        return
    if not search_term:
        logger.emit("<font color='#ef4444'>[-] Terme de recherche requis.</font>")
        return

    logger.emit(f"<font color='#3b82f6'><b>[*] Recherche de '{search_term}' dans {folder}...</b></font>")
    
    count = 0
    files_checked = 0
    
    for root, dirs, files in os.walk(folder):
        for file in files:
            files_checked += 1
            path = os.path.join(root, file)
            try:
                # Try utf-8 then latin-1
                try:
                    f = open(path, 'r', encoding='utf-8', errors='strict')
                    lines = f.readlines()
                    f.close()
                except:
                    f = open(path, 'r', encoding='latin-1', errors='ignore')
                    lines = f.readlines()
                    f.close()

                for i, line in enumerate(lines):
                    if search_term in line:
                        clean_line = line.strip()[:150] # Truncate for display
                        logger.emit(f"<font color='#22c55e'>[+] Trouvé ({file}:{i+1}): {clean_line}</font>")
                        count += 1
            except Exception as e:
                pass
            
            if files_checked % 500 == 0:
                 logger.emit(f"<font color='#a1a1aa'>[i] {files_checked} fichiers analysés...</font>")

    logger.emit(f"<font color='#3b82f6'><b>[*] Terminé. {count} résultats trouvés.</b></font>")

def logic_dork_gen(logger, count):
    logger.emit(f"<font color='#3b82f6'><b>[*] Génération de {count} Dorks SQLi...</b></font>")
    
    params = ["id=", "cat=", "item=", "page=", "article=", "news=", "product=", "category=", "type=", "view="]
    pages = ["index.php", "article.php", "news.php", "products.php", "view.php", "details.php", "gallery.php", "shop.php"]
    
    for _ in range(int(count)):
        dork = f"inurl:{random.choice(pages)}?{random.choice(params)}"
        logger.emit(f"<font color='#e4e4e7'>{dork}</font>")

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

class SqlToolWindow(QMainWindow):
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
        
        title_label = QLabel("LE M // Sql Tool")
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

        self.menu_label = QLabel("SQL Tool - LE M")
        self.menu_label.setObjectName("MenuLabel")
        self.menu_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.menu_label)

        # Input
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("URL ou Dossier Dump")
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
        
        self.btn_sqli = QPushButton("🔍  Scanner SQLi")
        self.btn_dump = QPushButton("📂  Recherche Dump")
        self.btn_dork = QPushButton("🎲  Générateur Dorks")
        
        for btn in [self.btn_sqli, self.btn_dump, self.btn_dork]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_main.addWidget(btn)
        layout_main.addStretch()
            
        # --- Page Scanner ---
        page_scan = QWidget()
        layout_scan = QVBoxLayout(page_scan)
        layout_scan.setSpacing(8)
        layout_scan.setContentsMargins(0, 0, 0, 0)
        
        self.btn_launch_scan = QPushButton("🚀  Lancer Scan")
        btn_back_scan = QPushButton("⬅️  Retour")
        
        for btn in [self.btn_launch_scan, btn_back_scan]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_scan.addWidget(btn)
        layout_scan.addStretch()
            
        # --- Page Dump ---
        page_dump = QWidget()
        layout_dump = QVBoxLayout(page_dump)
        layout_dump.setSpacing(8)
        layout_dump.setContentsMargins(0, 0, 0, 0)
        
        self.btn_select_folder = QPushButton("📂  Choisir Dossier")
        self.btn_search_dump = QPushButton("🔍  Rechercher")
        btn_back_dump = QPushButton("⬅️  Retour")
        
        for btn in [self.btn_select_folder, self.btn_search_dump, btn_back_dump]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_dump.addWidget(btn)
        layout_dump.addStretch()
            
        # --- Page Dorks ---
        page_dork = QWidget()
        layout_dork = QVBoxLayout(page_dork)
        layout_dork.setSpacing(8)
        layout_dork.setContentsMargins(0, 0, 0, 0)
        
        self.btn_gen_dork = QPushButton("🎲  Générer")
        btn_back_dork = QPushButton("⬅️  Retour")
        
        for btn in [self.btn_gen_dork, btn_back_dork]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_dork.addWidget(btn)
        layout_dork.addStretch()
            
        self.stacked_widget.addWidget(page_main)
        self.stacked_widget.addWidget(page_scan)
        self.stacked_widget.addWidget(page_dump)
        self.stacked_widget.addWidget(page_dork)
        
        # Navigation
        self.btn_sqli.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.btn_dump.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        self.btn_dork.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        btn_back_scan.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_back_dump.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_back_dork.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        # Actions
        self.btn_launch_scan.clicked.connect(lambda: self.start_task(logic_sqli_scan, self.input_field.text()))
        self.btn_select_folder.clicked.connect(self.action_select_folder)
        self.btn_search_dump.clicked.connect(self.action_search_dump)
        self.btn_gen_dork.clicked.connect(self.action_gen_dork)

        scroll_area.setWidget(self.stacked_widget)
        left_layout.addWidget(scroll_area)

        self.btn_clear = QPushButton("🧹  Effacer Console")
        self.btn_clear.setObjectName("ClearBtn")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear_logs)
        left_layout.addWidget(self.btn_clear)

        btn_exit = QPushButton("🚪  Quitter")
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

    def action_select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choisir un dossier de Dump")
        if folder:
            self.input_field.setText(folder)
            self.log_message(f"<font color='#a1a1aa'>[i] Dossier sélectionné: {folder}</font>")

    def action_search_dump(self):
        folder = self.input_field.text().strip()
        if not folder:
            self.log_message("<font color='#ef4444'>[-] Veuillez sélectionner un dossier d'abord.</font>")
            return
        
        term, ok = QInputDialog.getText(self, "Recherche", "Terme à rechercher (Email, Pseudo, etc.) :")
        if ok and term:
            self.start_task(logic_search_dump, folder, term)

    def action_gen_dork(self):
        count, ok = QInputDialog.getInt(self, "Générateur", "Nombre de Dorks :", 10, 1, 1000)
        if ok:
            self.start_task(logic_dork_gen, count)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SqlToolWindow()
    window.show()
    sys.exit(app.exec_())