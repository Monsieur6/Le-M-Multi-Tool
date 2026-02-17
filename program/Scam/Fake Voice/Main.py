import os
import sys
import asyncio
import time

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextBrowser, QFrame, QGraphicsDropShadowEffect, 
                             QScrollArea, QComboBox, QTextEdit, QCheckBox, QCompleter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor

# --- Logic ---

OUTPUT_DIR = os.path.join('output', 'Fake Voice')
if not os.path.exists(OUTPUT_DIR):
    try:
        os.makedirs(OUTPUT_DIR)
    except: pass

VOICES_DB = {
    "🇦🇫 Pashto / پښتو (Afghanistan)": {"Gul Nawaz": "ps-AF-GulNawazNeural", "Latifa": "ps-AF-LatifaNeural"},
    "🇦🇱 Albanian / Shqip (Albania)": {"Anila": "sq-AL-AnilaNeural", "Ilir": "sq-AL-IlirNeural"},
    "🇩🇿 Arabic / العربية (Algeria)": {"Amina": "ar-DZ-AminaNeural", "Ismael": "ar-DZ-IsmaelNeural"},
    "🇧🇭 Arabic / العربية (Bahrain)": {"Ali": "ar-BH-AliNeural", "Laila": "ar-BH-LailaNeural"},
    "🇪🇬 Arabic / العربية (Egypt)": {"Salma": "ar-EG-SalmaNeural", "Shakir": "ar-EG-ShakirNeural"},
    "🇮🇶 Arabic / العربية (Iraq)": {"Bassel": "ar-IQ-BasselNeural", "Rana": "ar-IQ-RanaNeural"},
    "🇯🇴 Arabic / العربية (Jordan)": {"Sana": "ar-JO-SanaNeural", "Taim": "ar-JO-TaimNeural"},
    "🇰🇼 Arabic / العربية (Kuwait)": {"Fahed": "ar-KW-FahedNeural", "Noura": "ar-KW-NouraNeural"},
    "🇱🇧 Arabic / العربية (Lebanon)": {"Layla": "ar-LB-LaylaNeural", "Rami": "ar-LB-RamiNeural"},
    "🇱🇾 Arabic / العربية (Libya)": {"Iman": "ar-LY-ImanNeural", "Omar": "ar-LY-OmarNeural"},
    "🇲🇦 Arabic / العربية (Morocco)": {"Jamal": "ar-MA-JamalNeural", "Mouna": "ar-MA-MounaNeural"},
    "🇴🇲 Arabic / العربية (Oman)": {"Abdullah": "ar-OM-AbdullahNeural", "Aysha": "ar-OM-AyshaNeural"},
    "🇶🇦 Arabic / العربية (Qatar)": {"Amal": "ar-QA-AmalNeural", "Moaz": "ar-QA-MoazNeural"},
    "🇸🇦 Arabic / العربية (Saudi Arabia)": {"Hamed": "ar-SA-HamedNeural", "Zariyah": "ar-SA-ZariyahNeural"},
    "🇸🇾 Arabic / العربية (Syria)": {"Amany": "ar-SY-AmanyNeural", "Laith": "ar-SY-LaithNeural"},
    "🇹🇳 Arabic / العربية (Tunisia)": {"Hedi": "ar-TN-HediNeural", "Reem": "ar-TN-ReemNeural"},
    "🇦🇪 Arabic / العربية (UAE)": {"Fatima": "ar-AE-FatimaNeural", "Hamdan": "ar-AE-HamdanNeural"},
    "🇾🇪 Arabic / العربية (Yemen)": {"Maryam": "ar-YE-MaryaNeural", "Saleh": "ar-YE-SalehNeural"},
    "🇦🇲 Armenian / Հայերեն (Armenia)": {"Anahit": "hy-AM-AnahitNeural", "Hayk": "hy-AM-HaykNeural"},
    "🇦🇿 Azerbaijani / Azərbaycan (Azerbaijan)": {"Babek": "az-AZ-BabekNeural", "Banu": "az-AZ-BanuNeural"},
    "🇧🇩 Bengali / বাংলা (Bangladesh)": {"Nabanita": "bn-BD-NabanitaNeural", "Pradeep": "bn-BD-PradeepNeural"},
    "🇮🇳 Bengali / বাংলা (India)": {"Bashkar": "bn-IN-BashkarNeural", "Tanishaa": "bn-IN-TanishaaNeural"},
    "🇧🇦 Bosnian / Bosanski (Bosnia)": {"Gorana": "bs-BA-GoranaNeural", "Toran": "bs-BA-ToranNeural"},
    "🇧🇬 Bulgarian / Български (Bulgaria)": {"Borislav": "bg-BG-BorislavNeural", "Kalina": "bg-BG-KalinaNeural"},
    "🇲🇲 Burmese / မြန်မာစာ (Myanmar)": {"Nilar": "my-MM-NilarNeural", "Thiha": "my-MM-ThihaNeural"},
    "🇪🇸 Catalan / Català (Spain)": {"Alba": "ca-ES-AlbaNeural", "Enric": "ca-ES-EnricNeural", "Joana": "ca-ES-JoanaNeural"},
    "🇨🇳 Chinese / 中文 (Mandarin, Simplified)": {"Xiaoxiao": "zh-CN-XiaoxiaoNeural", "Yunxi": "zh-CN-YunxiNeural"},
    "🇹🇼 Chinese / 中文 (Taiwanese Mandarin)": {"HsiaoChen": "zh-TW-HsiaoChenNeural", "YunJhe": "zh-TW-YunJheNeural"},
    "🇭🇰 Chinese / 中文 (Cantonese, Traditional)": {"HiuMaan": "zh-HK-HiuMaanNeural", "WanLung": "zh-HK-WanLungNeural"},
    "🇭🇷 Croatian / Hrvatski (Croatia)": {"Gabrijela": "hr-HR-GabrijelaNeural", "Srecko": "hr-HR-SreckoNeural"},
    "🇨🇿 Czech / Čeština (Czech Republic)": {"Antonin": "cs-CZ-AntoninNeural", "Vlasta": "cs-CZ-VlastaNeural"},
    "🇩🇰 Danish / Dansk (Denmark)": {"Christel": "da-DK-ChristelNeural", "Jeppe": "da-DK-JeppeNeural"},
    "🇧🇪 Dutch / Nederlands (Belgium)": {"Arnaud": "nl-BE-ArnaudNeural", "Dena": "nl-BE-DenaNeural"},
    "🇳🇱 Dutch / Nederlands (Netherlands)": {"Colette": "nl-NL-ColetteNeural", "Fenna": "nl-NL-FennaNeural", "Maarten": "nl-NL-MaartenNeural"},
    "🇦🇺 English (Australia)": {"Natasha": "en-AU-NatashaNeural", "William": "en-AU-WilliamNeural"},
    "🇨🇦 English (Canada)": {"Clara": "en-CA-ClaraNeural", "Liam": "en-CA-LiamNeural"},
    "🇭🇰 English (Hong Kong)": {"Sam": "en-HK-SamNeural", "Yan": "en-HK-YanNeural"},
    "🇮🇳 English (India)": {"Neerja": "en-IN-NeerjaNeural", "Prabhat": "en-IN-PrabhatNeural"},
    "🇮🇪 English (Ireland)": {"Connor": "en-IE-ConnorNeural", "Emily": "en-IE-EmilyNeural"},
    "🇰🇪 English (Kenya)": {"Asilia": "en-KE-AsiliaNeural", "Chilemba": "en-KE-ChilembaNeural"},
    "🇳🇿 English (New Zealand)": {"Mitchell": "en-NZ-MitchellNeural", "Molly": "en-NZ-MollyNeural"},
    "🇳🇬 English (Nigeria)": {"Abeo": "en-NG-AbeoNeural", "Ezinne": "en-NG-EzinneNeural"},
    "🇵🇭 English (Philippines)": {"James": "en-PH-JamesNeural", "Rosa": "en-PH-RosaNeural"},
    "🇸🇬 English (Singapore)": {"Luna": "en-SG-LunaNeural", "Wayne": "en-SG-WayneNeural"},
    "🇿🇦 English (South Africa)": {"Leah": "en-ZA-LeahNeural", "Luke": "en-ZA-LukeNeural"},
    "🇹🇿 English (Tanzania)": {"Elimu": "en-TZ-ElimuNeural", "Imani": "en-TZ-ImaniNeural"},
    "🇬🇧 English (UK)": {"Libby": "en-GB-LibbyNeural", "Maisie": "en-GB-MaisieNeural", "Ryan": "en-GB-RyanNeural", "Sonia": "en-GB-SoniaNeural", "Thomas": "en-GB-ThomasNeural"},
    "🇺🇸 English (USA)": {"Ana": "en-US-AnaNeural", "Aria": "en-US-AriaNeural", "Christopher": "en-US-ChristopherNeural", "Eric": "en-US-EricNeural", "Guy": "en-US-GuyNeural", "Jenny": "en-US-JennyNeural", "Michelle": "en-US-MichelleNeural"},
    "🇪🇪 Estonian / Eesti (Estonia)": {"Anu": "et-EE-AnuNeural", "Kert": "et-EE-KertNeural"},
    "🇵🇭 Filipino (Philippines)": {"Angelo": "fil-PH-AngeloNeural", "Blessica": "fil-PH-BlessicaNeural"},
    "🇫🇮 Finnish / Suomi (Finland)": {"Harri": "fi-FI-HarriNeural", "Noora": "fi-FI-NooraNeural"},
    "🇧🇪 French / Français (Belgium)": {"Charline": "fr-BE-CharlineNeural", "Gerard": "fr-BE-GerardNeural"},
    "🇨🇦 French / Français (Canada)": {"Antoine": "fr-CA-AntoineNeural", "Jean": "fr-CA-JeanNeural", "Sylvie": "fr-CA-SylvieNeural"},
    "🇫🇷 French / Français (France)": {"Celestine": "fr-FR-CelestineNeural", "Denise": "fr-FR-DeniseNeural", "Eloise": "fr-FR-EloiseNeural", "Henri": "fr-FR-HenriNeural", "Jerome": "fr-FR-JeromeNeural", "🔞 Mode Sexy (Denise Mod)": "fr-FR-DeniseNeural"},
    "🇨🇭 French / Français (Switzerland)": {"Ariane": "fr-CH-ArianeNeural", "Fabrice": "fr-CH-FabriceNeural"},
    "🇪🇸 Galician / Galego (Spain)": {"Roi": "gl-ES-RoiNeural", "Sabela": "gl-ES-SabelaNeural"},
    "🇬🇪 Georgian / ქართული (Georgia)": {"Eka": "ka-GE-EkaNeural", "Giorgi": "ka-GE-GiorgiNeural"},
    "🇦🇹 German / Deutsch (Austria)": {"Ingrid": "de-AT-IngridNeural", "Jonas": "de-AT-JonasNeural"},
    "🇩🇪 German / Deutsch (Germany)": {"Amala": "de-DE-AmalaNeural", "Conrad": "de-DE-ConradNeural", "Katja": "de-DE-KatjaNeural", "Killian": "de-DE-KillianNeural"},
    "🇨🇭 German / Deutsch (Switzerland)": {"Jan": "de-CH-JanNeural", "Leni": "de-CH-LeniNeural"},
    "🇬🇷 Greek / Ελληνικά (Greece)": {"Athina": "el-GR-AthinaNeural", "Nestoras": "el-GR-NestorasNeural"},
    "🇮🇳 Gujarati / ગુજરાતી (India)": {"Dhwani": "gu-IN-DhwaniNeural", "Niranjan": "gu-IN-NiranjanNeural"},
    "🇮🇱 Hebrew / עברית (Israel)": {"Avri": "he-IL-AvriNeural", "Hila": "he-IL-HilaNeural"},
    "🇮🇳 Hindi / हिन्दी (India)": {"Madhur": "hi-IN-MadhurNeural", "Swara": "hi-IN-SwaraNeural"},
    "🇭🇺 Hungarian / Magyar (Hungary)": {"Noemi": "hu-HU-NoemiNeural", "Tamas": "hu-HU-TamasNeural"},
    "🇮🇸 Icelandic / Íslenska (Iceland)": {"Gudrun": "is-IS-GudrunNeural", "Gunnar": "is-IS-GunnarNeural"},
    "🇮🇩 Indonesian / Bahasa Indonesia (Indonesia)": {"Ardi": "id-ID-ArdiNeural", "Gadis": "id-ID-GadisNeural"},
    "🇮🇪 Irish / Gaeilge (Ireland)": {"Colm": "ga-IE-ColmNeural", "Orla": "ga-IE-OrlaNeural"},
    "🇮🇹 Italian / Italiano (Italy)": {"Diego": "it-IT-DiegoNeural", "Elsa": "it-IT-ElsaNeural", "Isabella": "it-IT-IsabellaNeural"},
    "🇯🇵 Japanese / 日本語 (Japan)": {"Keita": "ja-JP-KeitaNeural", "Nanami": "ja-JP-NanamiNeural"},
    "🇮🇩 Javanese / Basa Jawa (Indonesia)": {"Dimas": "jv-ID-DimasNeural", "Siti": "jv-ID-SitiNeural"},
    "🇮🇳 Kannada / ಕನ್ನಡ (India)": {"Gagan": "kn-IN-GaganNeural", "Sapna": "kn-IN-SapnaNeural"},
    "🇰🇿 Kazakh / Қазақ (Kazakhstan)": {"Aigul": "kk-KZ-AigulNeural", "Daulet": "kk-KZ-DauletNeural"},
    "🇰🇭 Khmer / ខ្មែរ (Cambodia)": {"Piseth": "km-KH-PisethNeural", "Sreymom": "km-KH-SreymomNeural"},
    "🇰🇷 Korean / 한국어 (Korea)": {"InJoon": "ko-KR-InJoonNeural", "SunHi": "ko-KR-SunHiNeural"},
    "🇱🇦 Lao / ລາວ (Laos)": {"Chanthavong": "lo-LA-ChanthavongNeural", "Keomany": "lo-LA-KeomanyNeural"},
    "🇱🇻 Latvian / Latviešu (Latvia)": {"Everita": "lv-LV-EveritaNeural", "Nils": "lv-LV-NilsNeural"},
    "🇱🇹 Lithuanian / Lietuvių (Lithuania)": {"Leonas": "lt-LT-LeonasNeural", "Ona": "lt-LT-OnaNeural"},
    "🇲🇰 Macedonian / Македонски (North Macedonia)": {"Aleksandar": "mk-MK-AleksandarNeural", "Marija": "mk-MK-MarijaNeural"},
    "🇲🇾 Malay / Bahasa Melayu (Malaysia)": {"Osman": "ms-MY-OsmanNeural", "Yasmin": "ms-MY-YasminNeural"},
    "🇮🇳 Malayalam / മലയാളം (India)": {"Midhun": "ml-IN-MidhunNeural", "Sobhana": "ml-IN-SobhanaNeural"},
    "🇲🇹 Maltese / Malti (Malta)": {"Grace": "mt-MT-GraceNeural", "Joseph": "mt-MT-JosephNeural"},
    "🇮🇳 Marathi / मराठी (India)": {"Aarohi": "mr-IN-AarohiNeural", "Manohar": "mr-IN-ManoharNeural"},
    "🇲🇳 Mongolian / Монгол (Mongolia)": {"Bataa": "mn-MN-BataaNeural", "Yesui": "mn-MN-YesuiNeural"},
    "🇳🇵 Nepali / नेपाली (Nepal)": {"Hemkala": "ne-NP-HemkalaNeural", "Sagar": "ne-NP-SagarNeural"},
    "🇳🇴 Norwegian / Norsk (Norway)": {"Finn": "nb-NO-FinnNeural", "Pernille": "nb-NO-PernilleNeural"},
    "🇮🇷 Persian / فارسی (Iran)": {"Dilara": "fa-IR-DilaraNeural", "Farid": "fa-IR-FaridNeural"},
    "🇵🇱 Polish / Polski (Poland)": {"Marek": "pl-PL-MarekNeural", "Zofia": "pl-PL-ZofiaNeural"},
    "🇧🇷 Portuguese / Português (Brazil)": {"Antonio": "pt-BR-AntonioNeural", "Francisca": "pt-BR-FranciscaNeural"},
    "🇵🇹 Portuguese / Português (Portugal)": {"Duarte": "pt-PT-DuarteNeural", "Raquel": "pt-PT-RaquelNeural"},
    "🇷🇴 Romanian / Română (Romania)": {"Alina": "ro-RO-AlinaNeural", "Emil": "ro-RO-EmilNeural"},
    "🇷🇺 Russian / Русский (Russia)": {"Dmitry": "ru-RU-DmitryNeural", "Svetlana": "ru-RU-SvetlanaNeural"},
    "🇷🇸 Serbian / Српски (Serbia)": {"Nicholas": "sr-RS-NicholasNeural", "Sophie": "sr-RS-SophieNeural"},
    "🇱🇰 Sinhala / සිංහල (Sri Lanka)": {"Sameera": "si-LK-SameeraNeural", "Thilini": "si-LK-ThiliniNeural"},
    "🇸🇰 Slovak / Slovenčina (Slovakia)": {"Lukas": "sk-SK-LukasNeural", "Viktoria": "sk-SK-ViktoriaNeural"},
    "🇸🇮 Slovenian / Slovenščina (Slovenia)": {"Petra": "sl-SI-PetraNeural", "Rok": "sl-SI-RokNeural"},
    "🇸🇴 Somali / Soomaali (Somalia)": {"Muuse": "so-SO-MuuseNeural", "Ubax": "so-SO-UbaxNeural"},
    "🇦🇷 Spanish / Español (Argentina)": {"Elena": "es-AR-ElenaNeural", "Tomas": "es-AR-TomasNeural"},
    "🇧🇴 Spanish / Español (Bolivia)": {"Marcelo": "es-BO-MarceloNeural", "Sofia": "es-BO-SofiaNeural"},
    "🇨🇱 Spanish / Español (Chile)": {"Catalina": "es-CL-CatalinaNeural", "Lorenzo": "es-CL-LorenzoNeural"},
    "🇨🇴 Spanish / Español (Colombia)": {"Gonzalo": "es-CO-GonzaloNeural", "Salome": "es-CO-SalomeNeural"},
    "🇨🇷 Spanish / Español (Costa Rica)": {"Juan": "es-CR-JuanNeural", "Maria": "es-CR-MariaNeural"},
    "🇨🇺 Spanish / Español (Cuba)": {"Belkys": "es-CU-BelkysNeural", "Manuel": "es-CU-ManuelNeural"},
    "🇩🇴 Spanish / Español (Dominican Republic)": {"Emilio": "es-DO-EmilioNeural", "Ramona": "es-DO-RamonaNeural"},
    "🇪🇨 Spanish / Español (Ecuador)": {"Andrea": "es-EC-AndreaNeural", "Luis": "es-EC-LuisNeural"},
    "🇸🇻 Spanish / Español (El Salvador)": {"Lorena": "es-SV-LorenaNeural", "Rodrigo": "es-SV-RodrigoNeural"},
    "🇬🇶 Spanish / Español (Equatorial Guinea)": {"Javier": "es-GQ-JavierNeural", "Teresa": "es-GQ-TeresaNeural"},
    "🇬🇹 Spanish / Español (Guatemala)": {"Andres": "es-GT-AndresNeural", "Marta": "es-GT-MartaNeural"},
    "🇭🇳 Spanish / Español (Honduras)": {"Karla": "es-HN-KarlaNeural", "Kevin": "es-HN-KevinNeural"},
    "🇲🇽 Spanish / Español (Mexico)": {"Dalia": "es-MX-DaliaNeural", "Jorge": "es-MX-JorgeNeural"},
    "🇳🇮 Spanish / Español (Nicaragua)": {"Federico": "es-NI-FedericoNeural", "Yolanda": "es-NI-YolandaNeural"},
    "🇵🇦 Spanish / Español (Panama)": {"Margarita": "es-PA-MargaritaNeural", "Roberto": "es-PA-RobertoNeural"},
    "🇵🇾 Spanish / Español (Paraguay)": {"Mario": "es-PY-MarioNeural", "Tania": "es-PY-TaniaNeural"},
    "🇵🇪 Spanish / Español (Peru)": {"Alex": "es-PE-AlexNeural", "Camila": "es-PE-CamilaNeural"},
    "🇵🇷 Spanish / Español (Puerto Rico)": {"Karina": "es-PR-KarinaNeural", "Victor": "es-PR-VictorNeural"},
    "🇪🇸 Spanish / Español (Spain)": {"Alvaro": "es-ES-AlvaroNeural", "Elvira": "es-ES-ElviraNeural"},
    "🇺🇸 Spanish / Español (USA)": {"Alonso": "es-US-AlonsoNeural", "Paloma": "es-US-PalomaNeural"},
    "🇺🇾 Spanish / Español (Uruguay)": {"Mateo": "es-UY-MateoNeural", "Valentina": "es-UY-ValentinaNeural"},
    "🇻🇪 Spanish / Español (Venezuela)": {"Paola": "es-VE-PaolaNeural", "Sebastian": "es-VE-SebastianNeural"},
    "🇮🇩 Sundanese / Basa Sunda (Indonesia)": {"Jajang": "su-ID-JajangNeural", "Tuti": "su-ID-TutiNeural"},
    "🇰🇪 Swahili / Kiswahili (Kenya)": {"Rafiki": "sw-KE-RafikiNeural", "Rehema": "sw-KE-RehemaNeural"},
    "🇹🇿 Swahili / Kiswahili (Tanzania)": {"Daudi": "sw-TZ-DaudiNeural", "Rehema": "sw-TZ-RehemaNeural"},
    "🇸🇪 Swedish / Svenska (Sweden)": {"Mattias": "sv-SE-MattiasNeural", "Sofie": "sv-SE-SofieNeural"},
    "🇮🇳 Tamil / தமிழ் (India)": {"Pallavi": "ta-IN-PallaviNeural", "Valluvar": "ta-IN-ValluvarNeural"},
    "🇱🇰 Tamil / தமிழ் (Sri Lanka)": {"Kumar": "ta-LK-KumarNeural", "Saranya": "ta-LK-SaranyaNeural"},
    "🇮🇳 Telugu / తెలుగు (India)": {"Mohan": "te-IN-MohanNeural", "Shruti": "te-IN-ShrutiNeural"},
    "🇹🇭 Thai / ไทย (Thailand)": {"Niwat": "th-TH-NiwatNeural", "Premwadee": "th-TH-PremwadeeNeural"},
    "🇹🇷 Turkish / Türkçe (Turkey)": {"Ahmet": "tr-TR-AhmetNeural", "Emel": "tr-TR-EmelNeural"},
    "🇺🇦 Ukrainian / Українська (Ukraine)": {"Ostap": "uk-UA-OstapNeural", "Polina": "uk-UA-PolinaNeural"},
    "🇮🇳 Urdu / اردو (India)": {"Gul": "ur-IN-GulNeural", "Salman": "ur-IN-SalmanNeural"},
    "🇵🇰 Urdu / اردو (Pakistan)": {"Asad": "ur-PK-AsadNeural", "Uzma": "ur-PK-UzmaNeural"},
    "🇺🇿 Uzbek / O'zbek (Uzbekistan)": {"Madina": "uz-UZ-MadinaNeural", "Sardor": "uz-UZ-SardorNeural"},
    "🇻🇳 Vietnamese / Tiếng Việt (Vietnam)": {"HoaiMy": "vi-VN-HoaiMyNeural", "NamMinh": "vi-VN-NamMinhNeural"},
    "🇬🇧 Welsh / Cymraeg (United Kingdom)": {"Aled": "cy-GB-AledNeural", "Nia": "cy-GB-NiaNeural"},
    "🇿🇦 Zulu / isiZulu (South Africa)": {"Thando": "zu-ZA-ThandoNeural", "Themba": "zu-ZA-ThembaNeural"}
}

async def _generate_audio(logger, text, voice_name, voice_id):
    try:
        import edge_tts
    except ImportError:
        logger.emit("<font color='#ef4444'>[-] Module 'edge-tts' manquant. Installez-le : pip install edge-tts</font>")
        return

    logger.emit(f"<font color='#3b82f6'><b>[*] Génération de l'audio...</b></font>")
    
    rate = "+0%"
    pitch = "+0Hz"
    
    if "Sexy" in voice_name:
        rate = "-15%"
        pitch = "-2Hz"
        logger.emit("<font color='#e4e4e7'>[i] Mode Sexy activé (Ralenti + Pitch bas)</font>")

    filename = f"voice_{int(time.time())}.mp3"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    try:
        communicate = edge_tts.Communicate(text, voice_id, rate=rate, pitch=pitch)
        await communicate.save(filepath)
        
        logger.emit(f"<font color='#22c55e'>[+] Fichier généré : {filepath}</font>")
        
        # Play
        if os.name == 'nt':
            os.startfile(os.path.abspath(filepath))
            
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur: {e}</font>")

def logic_generate(logger, text, lang_name, voice_name):
    if not text:
        logger.emit("<font color='#ef4444'>[-] Veuillez entrer du texte.</font>")
        return
        
    voice_id = VOICES_DB.get(lang_name, {}).get(voice_name)
    if not voice_id:
        logger.emit("<font color='#ef4444'>[-] Voix invalide.</font>")
        return

    # Détection langue cible via l'ID de la voix (ex: fr-FR-Eloise -> fr)
    target_lang = voice_id.split('-')[0]
    if 'zh-CN' in voice_id: target_lang = 'zh-CN'
    if 'zh-TW' in voice_id: target_lang = 'zh-TW'

    # --- Traduction Auto ---
    try:
        from deep_translator import GoogleTranslator
        
        logger.emit(f"<font color='#a1a1aa'>[i] Traduction vers {target_lang}...</font>")
        translated_text = GoogleTranslator(source='auto', target=target_lang).translate(text)
        
        if translated_text:
            logger.emit(f"<font color='#e4e4e7'>    Traduit : {translated_text}</font>")
            text = translated_text
    except ImportError as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur import 'deep-translator': {e}</font>")
        logger.emit("<font color='#a1a1aa'>    Installez-le : pip install deep-translator</font>")
    except Exception as e:
        logger.emit(f"<font color='#ef4444'>[-] Erreur traduction : {e}</font>")

    asyncio.run(_generate_audio(logger, text, voice_name, voice_id))

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

class FakeVoiceWindow(QMainWindow):
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
        
        title_label = QLabel("LE M // Fake Voice")
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
        
        menu_label = QLabel("Fake Voice - LE M")
        menu_label.setObjectName("MenuLabel")
        menu_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(menu_label)
        
        # Inputs
        lbl_lang = QLabel("Langue :")
        lbl_lang.setStyleSheet("color: #a1a1aa; font-weight: bold;")
        left_layout.addWidget(lbl_lang)

        self.search_lang = QLineEdit()
        self.search_lang.setPlaceholderText("🔍 Rechercher une langue...")
        self.search_lang.setStyleSheet("background-color: #18181b; border: 1px solid #3f3f46; border-radius: 5px; padding: 5px; color: #e4e4e7; font-size: 12px;")
        self.search_lang.textChanged.connect(self.filter_languages)
        left_layout.addWidget(self.search_lang)

        self.combo_lang = QComboBox()
        self.combo_lang.addItems(sorted(list(VOICES_DB.keys())))
        self.combo_lang.currentTextChanged.connect(self.update_voices)
        left_layout.addWidget(self.combo_lang)

        lbl_voice = QLabel("Voix :")
        lbl_voice.setStyleSheet("color: #a1a1aa; font-weight: bold;")
        left_layout.addWidget(lbl_voice)
        
        self.combo_voice = QComboBox()
        left_layout.addWidget(self.combo_voice)
        
        lbl_text = QLabel("Texte à dire :")
        lbl_text.setStyleSheet("color: #a1a1aa; font-weight: bold;")
        left_layout.addWidget(lbl_text)
        
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Entrez votre texte ici...")
        left_layout.addWidget(self.input_text)
        
        self.btn_gen = QPushButton("🔊  Générer & Jouer")
        self.btn_gen.setObjectName("ActionBtn")
        self.btn_gen.setCursor(Qt.PointingHandCursor)
        self.btn_gen.clicked.connect(self.action_generate)
        left_layout.addWidget(self.btn_gen)
        
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
        
        self.update_voices(self.combo_lang.currentText())

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
            QComboBox QAbstractItemView { background-color: #27272a; color: #f4f4f5; selection-background-color: #3f3f46; selection-color: #ffffff; border: 1px solid #3f3f46; }
            QTextEdit { background-color: #27272a; border: 1px solid #27272a; border-radius: 8px; padding: 12px; color: #f4f4f5; font-family: 'Consolas', monospace; font-size: 14px; }
            QTextEdit:focus { border: 1px solid #6366f1; background-color: #202023; }
            QPushButton { background-color: #18181b; border: 1px solid #27272a; border-radius: 8px; padding: 12px 20px; color: #e4e4e7; font-weight: 600; text-align: left; }
            QPushButton:hover { background-color: #27272a; border-color: #3f3f46; color: #ffffff; }
            QPushButton:pressed { background-color: #3f3f46; }
            QPushButton#ActionBtn { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #7c3aed); border: 1px solid #6366f1; color: #ffffff; text-align: center; }
            QPushButton#ActionBtn:hover { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4338ca, stop:1 #6d28d9); border: 1px solid #818cf8; }
            QPushButton#ExitBtn { background-color: #18181b; border: 1px solid #ef4444; color: #ef4444; text-align: center; }
            QPushButton#ExitBtn:hover { background-color: #ef4444; color: #fff; }
            QPushButton#ClearBtn, QPushButton#FolderBtn { text-align: center; }
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

    def filter_languages(self, text):
        self.combo_lang.blockSignals(True)
        self.combo_lang.clear()
        filtered = [l for l in sorted(list(VOICES_DB.keys())) if text.lower() in l.lower()]
        self.combo_lang.addItems(filtered)
        self.combo_lang.blockSignals(False)
        if filtered:
            self.update_voices(filtered[0])
        else:
            self.combo_voice.clear()

    def update_voices(self, lang_name):
        self.combo_voice.clear()
        voices = VOICES_DB.get(lang_name, {})
        self.combo_voice.addItems(list(voices.keys()))

    def action_generate(self):
        text = self.input_text.toPlainText().strip()
        lang = self.combo_lang.currentText()
        voice = self.combo_voice.currentText()
        self.start_task(logic_generate, text, lang, voice)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FakeVoiceWindow()
    window.show()
    sys.exit(app.exec_())
