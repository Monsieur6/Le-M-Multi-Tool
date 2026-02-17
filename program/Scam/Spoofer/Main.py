import sys
import os
import random
import string
import winreg
import uuid
import ctypes
import time
import json

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTextBrowser, 
                             QFrame, QGraphicsDropShadowEffect, QScrollArea, QStackedWidget, QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor

BACKUP_PATH = os.path.join(os.path.dirname(__file__), 'backup.json')

# --- Logic Functions ---

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def generate_random_id(length=7):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def logic_backup_init():
    if os.path.exists(BACKUP_PATH): return
    
    data = {}
    def save_key(key_path, val_names):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
            if key_path not in data: data[key_path] = {}
            for v in val_names:
                try:
                    val, type_ = winreg.QueryValueEx(key, v)
                    data[key_path][v] = (val, type_)
                except: pass
            winreg.CloseKey(key)
        except: pass

    save_key(r"SOFTWARE\Microsoft\Cryptography", ["MachineGuid"])
    save_key(r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", ["ProductId", "InstallDate", "RegisteredOwner", "RegisteredOrganization", "BuildGUID"])
    save_key(r"SYSTEM\CurrentControlSet\Control\ComputerName\ComputerName", ["ComputerName"])
    save_key(r"SYSTEM\CurrentControlSet\Control\ComputerName\ActiveComputerName", ["ComputerName"])
    save_key(r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters", ["Hostname", "NV Hostname"])
    save_key(r"HARDWARE\DESCRIPTION\System\CentralProcessor\0", ["ProcessorNameString"])
    save_key(r"HARDWARE\DESCRIPTION\System\BIOS", ["BIOSVendor", "BIOSVersion", "BIOSReleaseDate", "BaseBoardManufacturer", "BaseBoardProduct", "SystemManufacturer", "SystemProductName"])
    save_key(r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate", ["SusClientId"])
    save_key(r"SYSTEM\CurrentControlSet\Control\IDConfigDB\Hardware Profiles\0001", ["HwProfileGuid"])
    save_key(r"SOFTWARE\Microsoft\SqmClient", ["MachineId"])
    
    for i in range(10):
        save_key(fr"SYSTEM\CurrentControlSet\Control\Class\{{4d36e968-e325-11ce-bfc1-08002be10318}}\{i:04d}", ["DriverDesc"])

    try:
        with open(BACKUP_PATH, 'w') as f:
            json.dump(data, f)
    except: pass

def logic_check_ids(logger):
    logger.emit(f"<font color='#3f3f46'>--------------------------------------------------</font>")
    logger.emit(f"<font color='#3b82f6'><b>[*] Lecture des identifiants actuels...</b></font>")
    logger.emit(f"<font color='#3f3f46'>--------------------------------------------------</font>")
    try:
        def read_reg(key_path, value_name):
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
                val, _ = winreg.QueryValueEx(key, value_name)
                winreg.CloseKey(key)
                return str(val)
            except: return "Inaccessible"

        # 1. System IDs
        logger.emit(f"<font color='#e4e4e7'><b>[SYSTEM]</b></font>")
        k_crypto = r'SOFTWARE\Microsoft\Cryptography'
        k_win = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion'
        k_comp = r'SYSTEM\CurrentControlSet\Control\ComputerName\ActiveComputerName'
        
        logger.emit(f"<font color='#a1a1aa'>    MachineGuid : {read_reg(k_crypto, 'MachineGuid')}</font>")
        logger.emit(f"<font color='#a1a1aa'>    ProductId   : {read_reg(k_win, 'ProductId')}</font>")
        logger.emit(f"<font color='#a1a1aa'>    InstallDate : {read_reg(k_win, 'InstallDate')}</font>")
        logger.emit(f"<font color='#a1a1aa'>    Nom du PC   : {read_reg(k_comp, 'ComputerName')}</font>")
        logger.emit(f"<font color='#a1a1aa'>    Propriétaire: {read_reg(k_win, 'RegisteredOwner')}</font>")

        # 2. Hardware Info (Registry cached)
        logger.emit(f"<br><font color='#e4e4e7'><b>[HARDWARE]</b></font>")
        k_cpu = r'HARDWARE\DESCRIPTION\System\CentralProcessor\0'
        logger.emit(f"<font color='#a1a1aa'>    CPU         : {read_reg(k_cpu, 'ProcessorNameString')}</font>")
        
        # Try to find GPU in first few keys
        gpu = "Inaccessible"
        for i in range(5):
            val = read_reg(fr'SYSTEM\CurrentControlSet\Control\Class\{{4d36e968-e325-11ce-bfc1-08002be10318}}\{i:04d}', 'DriverDesc')
            if val != "Inaccessible":
                gpu = val
                break
        logger.emit(f"<font color='#a1a1aa'>    GPU         : {gpu}</font>")
        
        # 3. BIOS / Board
        logger.emit(f"<br><font color='#e4e4e7'><b>[BIOS/BOARD]</b></font>")
        k_bios = r'HARDWARE\DESCRIPTION\System\BIOS'
        logger.emit(f"<font color='#a1a1aa'>    BIOS Vendor : {read_reg(k_bios, 'BIOSVendor')}</font>")
        logger.emit(f"<font color='#a1a1aa'>    BIOS Ver    : {read_reg(k_bios, 'BIOSVersion')}</font>")
        logger.emit(f"<font color='#a1a1aa'>    Board Mfg   : {read_reg(k_bios, 'BaseBoardManufacturer')}</font>")
        logger.emit(f"<font color='#a1a1aa'>    System Mfg  : {read_reg(k_bios, 'SystemManufacturer')}</font>")

    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur globale: {e}</font>")

def logic_spoof_custom(logger, options=None):
    if not is_admin():
        logger.emit("<font color='#ef4444'><b>[-] ERREUR : Droits Administrateur requis !</b></font>")
        logger.emit("<font color='#a1a1aa'>    Veuillez relancer le tool en tant qu'admin.</font>")
        return

    logger.emit(f"<font color='#3f3f46'>--------------------------------------------------</font>")
    logger.emit(f"<font color='#3b82f6'><b>[*] Lancement du Spoofing...</b></font>")
    logger.emit(f"<font color='#3f3f46'>--------------------------------------------------</font>")
    
    def write_reg(key_path, value_name, value, reg_type=winreg.REG_SZ):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(key, value_name, 0, reg_type, value)
            winreg.CloseKey(key)
            return True
        except: return False

    def rnd_id(l=10): return ''.join(random.choices(string.ascii_uppercase + string.digits, k=l))

    # Default to all if options is None
    if options is None:
        options = {k: True for k in ['guid', 'ids', 'pcname', 'owner', 'cpu', 'gpu', 'bios', 'network']}

    try:
        # 1. MachineGuid
        if options.get('guid'):
            new_guid = str(uuid.uuid4())
            if write_reg(r"SOFTWARE\Microsoft\Cryptography", "MachineGuid", new_guid):
                logger.emit(f"<font color='#22c55e'>[+] MachineGuid -> {new_guid}</font>")
            
            new_hw_profile = f"{{{str(uuid.uuid4())}}}"
            if write_reg(r"SYSTEM\CurrentControlSet\Control\IDConfigDB\Hardware Profiles\0001", "HwProfileGuid", new_hw_profile):
                logger.emit(f"<font color='#22c55e'>[+] HwProfileGuid -> {new_hw_profile}</font>")
            
            new_machine_id = f"{{{str(uuid.uuid4())}}}"
            if write_reg(r"SOFTWARE\Microsoft\SqmClient", "MachineId", new_machine_id):
                logger.emit(f"<font color='#22c55e'>[+] SqmClient MachineId -> {new_machine_id}</font>")

            try:
                sus_id = str(uuid.uuid4())
                write_reg(r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate", "SusClientId", sus_id)
                logger.emit(f"<font color='#22c55e'>[+] Windows Update SusClientId -> {sus_id}</font>")
            except: pass
        
        # 2. ProductId
        if options.get('ids'):
            new_pid = f"{random.randint(10000,99999)}-{random.randint(10000,99999)}-{random.randint(10000,99999)}-{random.randint(10000,99999)}"
            if write_reg(r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "ProductId", new_pid):
                logger.emit(f"<font color='#22c55e'>[+] ProductId -> {new_pid}</font>")
            write_reg(r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "BuildGUID", str(uuid.uuid4()))
            
            # Extra IDs
            write_reg(r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "OfflineInstallId", str(uuid.uuid4()))
            write_reg(r"SOFTWARE\Microsoft\Internet Explorer\Registration", "ProductId", rnd_id(15))
        
        # 3. ComputerName
        if options.get('pcname'):
            new_name = f"DESKTOP-{rnd_id(7)}"
            write_reg(r"SYSTEM\CurrentControlSet\Control\ComputerName\ComputerName", "ComputerName", new_name)
            write_reg(r"SYSTEM\CurrentControlSet\Control\ComputerName\ActiveComputerName", "ComputerName", new_name)
            write_reg(r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters", "Hostname", new_name)
            write_reg(r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters", "NV Hostname", new_name)
            logger.emit(f"<font color='#22c55e'>[+] Nom du PC -> {new_name}</font>")

        # 4. InstallDate & Owner
        if options.get('owner'):
            new_date = int(time.time()) - random.randint(1000000, 50000000)
            write_reg(r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "InstallDate", new_date, winreg.REG_DWORD)
            write_reg(r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "RegisteredOwner", rnd_id(8))
            write_reg(r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "RegisteredOrganization", rnd_id(8))
            logger.emit(f"<font color='#22c55e'>[+] Owner & InstallDate spoofés</font>")

        # 5. CPU Name
        if options.get('cpu'):
            cpus = [
                "Intel(R) Core(TM) i9-13900K CPU @ 3.00GHz", 
                "AMD Ryzen 9 7950X 16-Core Processor", 
                "Intel(R) Core(TM) i7-12700K CPU @ 3.60GHz", 
                "AMD Ryzen 7 5800X 8-Core Processor",
                "Intel(R) Core(TM) i5-13600K CPU @ 3.50GHz"
            ]
            new_cpu = random.choice(cpus)
            if write_reg(r"HARDWARE\DESCRIPTION\System\CentralProcessor\0", "ProcessorNameString", new_cpu):
                logger.emit(f"<font color='#22c55e'>[+] CPU Name -> {new_cpu}</font>")

        # 6. GPU Name (Try multiple keys)
        if options.get('gpu'):
            gpus = [
                "NVIDIA GeForce RTX 4090", "AMD Radeon RX 7900 XTX", 
                "NVIDIA GeForce RTX 3080", "Intel Arc A770",
                "NVIDIA GeForce RTX 3060 Ti"
            ]
            new_gpu = random.choice(gpus)
            for i in range(100):
                key = fr"SYSTEM\CurrentControlSet\Control\Class\{{4d36e968-e325-11ce-bfc1-08002be10318}}\{i:04d}"
                write_reg(key, "DriverDesc", new_gpu)
            logger.emit(f"<font color='#22c55e'>[+] GPU Name -> {new_gpu}</font>")

        # 7. BIOS / BaseBoard
        if options.get('bios'):
            bios_vendors = ["American Megatrends Inc.", "AMI", "Insyde Corp.", "Phoenix Technologies Ltd."]
            board_mfgs = ["ASUSTeK COMPUTER INC.", "Gigabyte Technology Co., Ltd.", "MSI", "ASRock"]
            
            write_reg(r"HARDWARE\DESCRIPTION\System\BIOS", "BIOSVendor", random.choice(bios_vendors))
            write_reg(r"HARDWARE\DESCRIPTION\System\BIOS", "BIOSVersion", f"{random.choice(['F', 'V', 'A'])}{random.randint(10,99)}")
            write_reg(r"HARDWARE\DESCRIPTION\System\BIOS", "BIOSReleaseDate", f"{random.randint(1,12)}/{random.randint(1,28)}/{random.randint(2018,2023)}")
            
            mfg = random.choice(board_mfgs)
            write_reg(r"HARDWARE\DESCRIPTION\System\BIOS", "BaseBoardManufacturer", mfg)
            write_reg(r"HARDWARE\DESCRIPTION\System\BIOS", "BaseBoardProduct", f"Z{random.randint(390,790)}-{rnd_id(4)}")
            write_reg(r"HARDWARE\DESCRIPTION\System\BIOS", "SystemManufacturer", mfg)
            write_reg(r"HARDWARE\DESCRIPTION\System\BIOS", "SystemProductName", f"System Product Name")
            logger.emit(f"<font color='#22c55e'>[+] BIOS & BaseBoard spoofés</font>")

        # 8. Network (MAC)
        if options.get('network'):
            mac_prefix = random.choice(["02", "06", "0A", "0E"])
            mac_suffix = ''.join(random.choices("0123456789ABCDEF", k=10))
            new_mac = mac_prefix + mac_suffix
            
            count_net = 0
            base_net = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}"
            for i in range(20):
                key_path = fr"{base_net}\{i:04d}"
                if write_reg(key_path, "NetworkAddress", new_mac):
                    count_net += 1
            
            if count_net > 0:
                logger.emit(f"<font color='#22c55e'>[+] MAC Address -> {new_mac} (sur {count_net} interfaces)</font>")
            else:
                logger.emit(f"<font color='#a1a1aa'>[-] Aucune interface réseau trouvée.</font>")
        
        logger.emit(f"<br><font color='#e4e4e7'><b>[!] Spoofing terminé. Redémarrage recommandé.</b></font>")

    except PermissionError:
        logger.emit("<font color='#ef4444'>[-] Permission refusée. Êtes-vous Admin ?</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_restore(logger):
    if not os.path.exists(BACKUP_PATH):
        logger.emit("<font color='#ef4444'>[-] Aucune sauvegarde trouvée (backup.json).</font>")
        return

    logger.emit(f"<font color='#3f3f46'>--------------------------------------------------</font>")
    logger.emit(f"<font color='#3b82f6'><b>[*] Restauration des IDs d'origine...</b></font>")
    logger.emit(f"<font color='#3f3f46'>--------------------------------------------------</font>")
    
    try:
        with open(BACKUP_PATH, 'r') as f:
            data = json.load(f)
            
        count = 0
        for key_path, values in data.items():
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_ALL_ACCESS)
                for v_name, v_data in values.items():
                    # v_data is [value, type]
                    val, type_ = v_data
                    winreg.SetValueEx(key, v_name, 0, type_, val)
                    count += 1
                winreg.CloseKey(key)
            except: pass
            
        logger.emit(f"<font color='#22c55e'>[+] Restauration terminée ({count} valeurs).</font>")
        logger.emit(f"<font color='#e4e4e7'>[!] Redémarrez votre PC pour appliquer.</font>")
        
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

class SpooferToolWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(1000, 650)
        self.worker = None
        self.oldPos = self.pos()
        
        # Backup on start
        logic_backup_init()
        
        self.container = QFrame()
        self.container.setObjectName("MainContainer")
        self.setCentralWidget(self.container)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.container.setGraphicsEffect(shadow)
        
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Header
        self.title_bar = QFrame()
        self.title_bar.setObjectName("TitleBar")
        self.title_bar.setFixedHeight(40)
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(15, 0, 10, 0)
        
        title_label = QLabel("LE M // Spoofer")
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
        
        # Content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Left
        left_panel = QFrame()
        left_panel.setObjectName("SidePanel")
        left_panel.setFixedWidth(320)

        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(15, 20, 15, 20)

        self.menu_label = QLabel("Spoofer - LE M")
        self.menu_label.setObjectName("MenuLabel")
        self.menu_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.menu_label)

        # Scroll Area for Buttons
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("background: transparent; border: none;")
        
        self.stacked_widget = QStackedWidget()
        
        # --- Page Main ---
        page_main = QWidget()
        layout_main = QVBoxLayout(page_main)
        layout_main.setSpacing(8)
        layout_main.setContentsMargins(0, 0, 0, 0)

        self.btn_check = QPushButton("🔍  Vérifier IDs Actuels")
        self.btn_spoof = QPushButton("🚀  SPOOF TOUT (Admin)")
        self.btn_custom = QPushButton("⚙️  Spoof Personnalisé")
        self.btn_restore = QPushButton("♻️  Restaurer IDs d'origine")
        
        for btn in [self.btn_check, self.btn_spoof, self.btn_custom, self.btn_restore]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_main.addWidget(btn)
        layout_main.addStretch()
            
        # --- Page Custom ---
        page_custom = QWidget()
        layout_custom = QVBoxLayout(page_custom)
        layout_custom.setSpacing(15)
        layout_custom.setContentsMargins(20, 20, 20, 20)
        
        self.chk_guid = QCheckBox("GUIDs (Machine, HwProfile, SQM...)")
        self.chk_ids = QCheckBox("Product IDs, BuildGUID & IE")
        self.chk_pcname = QCheckBox("Nom du PC & Hostname")
        self.chk_owner = QCheckBox("Propriétaire & Date Install")
        self.chk_cpu = QCheckBox("CPU Name")
        self.chk_gpu = QCheckBox("GPU Name")
        self.chk_bios = QCheckBox("BIOS & BaseBoard")
        self.chk_net = QCheckBox("Réseau (MAC Address)")
        
        checks = [self.chk_guid, self.chk_ids, self.chk_pcname, self.chk_owner, self.chk_cpu, self.chk_gpu, self.chk_bios, self.chk_net]
        for chk in checks:
            chk.setStyleSheet("""
                QCheckBox { color: #e4e4e7; font-size: 13px; padding: 8px; border-radius: 5px; }
                QCheckBox:hover { background-color: #18181b; }
                QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 1px solid #3f3f46; background: #09090b; }
                QCheckBox::indicator:checked { background: #6366f1; border-color: #6366f1; }
            """)
            chk.setCursor(Qt.PointingHandCursor)
            chk.setChecked(True)
            layout_custom.addWidget(chk)
            
        layout_custom.addStretch()
            
        self.btn_spoof_selected = QPushButton("🚀  Lancer Spoof Sélectionné")
        self.btn_spoof_selected.setObjectName("ActionBtn")
        self.btn_spoof_selected.setCursor(Qt.PointingHandCursor)
        layout_custom.addWidget(self.btn_spoof_selected)
        
        btn_back_custom = QPushButton("⬅️  Retour")
        btn_back_custom.setObjectName("ActionBtn")
        btn_back_custom.setCursor(Qt.PointingHandCursor)
        layout_custom.addWidget(btn_back_custom)
        
        self.stacked_widget.addWidget(page_main)
        self.stacked_widget.addWidget(page_custom)
        
        # Actions
        self.btn_check.clicked.connect(lambda: self.start_task(logic_check_ids))
        self.btn_spoof.clicked.connect(lambda: self.start_task(logic_spoof_custom, None))
        self.btn_custom.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.btn_restore.clicked.connect(lambda: self.start_task(logic_restore))
        
        self.btn_spoof_selected.clicked.connect(self.action_spoof_custom)
        btn_back_custom.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        scroll_area.setWidget(self.stacked_widget)
        left_layout.addWidget(scroll_area)

        self.btn_clear = QPushButton("🧹  Effacer Console")
        self.btn_clear.setObjectName("ClearBtn")
        self.btn_clear.clicked.connect(self.clear_logs)
        left_layout.addWidget(self.btn_clear)

        btn_back = QPushButton("⬅️  Retour")
        btn_back.setObjectName("ExitBtn")
        btn_back.clicked.connect(self.close)
        left_layout.addWidget(btn_back)

        # Right
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

        content_layout.addWidget(left_panel)
        content_layout.addWidget(right_panel)
        self.main_layout.addLayout(content_layout)

        self.apply_styles()

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
            QPushButton { background-color: #18181b; border: 1px solid #27272a; border-radius: 8px; padding: 12px 20px; color: #e4e4e7; font-weight: 600; }
            QPushButton:hover { background-color: #27272a; border-color: #3f3f46; color: #ffffff; }
            QPushButton#ActionBtn { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #7c3aed); border: 1px solid #6366f1; color: #ffffff; }
            QPushButton#ActionBtn:hover { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4338ca, stop:1 #6d28d9); border: 1px solid #818cf8; }
            QPushButton#ExitBtn { background-color: #18181b; border: 1px solid #ef4444; color: #ef4444; }
            QPushButton#ExitBtn:hover { background-color: #ef4444; color: #fff; }
            QTextBrowser { background-color: #000000; border: none; color: #22c55e; font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; padding: 20px; line-height: 1.5; border-bottom-right-radius: 12px; }
            QLabel#MenuLabel { font-size: 16px; font-weight: 800; color: #6366f1; padding: 10px 0; letter-spacing: 1px; }
            QCheckBox { spacing: 8px; }
            QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #3f3f46; border-radius: 4px; background: #18181b; }
            QCheckBox::indicator:checked { background: #6366f1; border: 1px solid #6366f1; }
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
        self.worker = Worker(func, *args)
        self.worker.log_signal.connect(self.log_message)
        self.worker.start()

    def action_spoof_custom(self):
        opts = {
            'guid': self.chk_guid.isChecked(),
            'ids': self.chk_ids.isChecked(),
            'pcname': self.chk_pcname.isChecked(),
            'owner': self.chk_owner.isChecked(),
            'cpu': self.chk_cpu.isChecked(),
            'gpu': self.chk_gpu.isChecked(),
            'bios': self.chk_bios.isChecked(),
            'network': self.chk_net.isChecked()
        }
        self.start_task(logic_spoof_custom, opts)

if __name__ == '__main__':
    if not is_admin():
        try:
            # Relance le script en tant qu'administrateur
            params = " ".join([f'"{arg}"' for arg in sys.argv])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 0)
        except: pass
        sys.exit()

    app = QApplication(sys.argv)
    window = SpooferToolWindow()
    window.show()
    sys.exit(app.exec_())