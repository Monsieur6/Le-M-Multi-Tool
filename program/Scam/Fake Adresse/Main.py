import sys
import os
import requests
import threading
import time
import json
import urllib3
import random
import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextBrowser, QFrame, QGraphicsDropShadowEffect, 
                             QScrollArea, QInputDialog, QMessageBox, QStyle, QStackedWidget, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QCursor

# --- Logic Functions ---

city_zip_codes = {
    'France': {
        'Paris': ['75001', '75002', '75003', '75004', '75005', '75006', '75007', '75008', '75009', '75010', '75011', '75012', '75013', '75014', '75015', '75016', '75017', '75018', '75019', '75020', '75116'],
        'Marseille': ['13001', '13002', '13003', '13004', '13005', '13006', '13007', '13008', '13009', '13010', '13011', '13012', '13013', '13014', '13015', '13016'],
        'Lyon': ['69001', '69002', '69003', '69004', '69005', '69006', '69007', '69008', '69009']
    },
    'USA': {
        'New York': ['10001', '10002', '10003', '10004', '10005', '10006', '10007', '10008', '10009', '10010', '10011', '10012', '10013', '10014', '10015', '10016', '10017', '10018', '10019', '10020'],
        'Los Angeles': ['90001', '90002', '90003', '90004', '90005', '90006', '90007', '90008', '90009', '90010', '90011', '90012', '90013', '90014', '90015', '90016', '90017', '90018', '90019', '90020'],
        'Chicago': ['60601', '60602', '60603', '60604', '60605', '60606', '60607', '60608', '60609', '60610', '60611', '60612', '60613', '60614', '60615', '60616', '60617', '60618', '60619', '60620']
    },
    'Germany': {
        'Berlin': ['10115', '10117', '10119', '10178', '10179', '10243', '10245', '10247', '10249', '10315', '10317', '10318', '10319', '10365', '10367', '10369', '10405', '10407', '10409', '10435'],
        'Munich': ['80331', '80333', '80335', '80336', '80337', '80339', '80469', '80471', '80473', '80475', '80479', '80538', '80539', '80634', '80636', '80637', '80639', '80796', '80797', '80798'],
        'Hamburg': ['20095', '20097', '20099', '20144', '20146', '20148', '20149', '20251', '20253', '20255', '20257', '20259', '20354', '20355', '20357', '20359', '20457', '20459', '20535', '20537']
    },
    'Belgium': {
        'Brussels': ['1000', '1020', '1030', '1040', '1050', '1060', '1070', '1080', '1081', '1082', '1083', '1084', '1085', '1086', '1087', '1088', '1089', '1090', '1099', '1100'],
        'Antwerp': ['2000', '2018', '2020', '2030', '2040', '2050', '2060', '2070', '2080', '2090', '2100', '2110', '2120', '2130', '2140', '2150', '2160', '2170', '2180', '2190'],
        'Ghent': ['9000', '9001', '9002', '9003', '9004', '9005', '9006', '9007', '9008', '9009', '9010', '9011', '9012', '9013', '9014', '9015', '9016', '9017', '9018', '9019']
    },
    'Norway': {
        'Oslo': ['0001', '0002', '0003', '0004', '0005', '0006', '0007', '0008', '0009', '0010', '0011', '0012', '0013', '0014', '0015', '0016', '0017', '0018', '0019', '0020'],
        'Bergen': ['5000', '5001', '5002', '5003', '5004', '5005', '5006', '5007', '5008', '5009', '5010', '5011', '5012', '5013', '5014', '5015', '5016', '5017', '5018', '5019'],
        'Stavanger': ['4000', '4001', '4002', '4003', '4004', '4005', '4006', '4007', '4008', '4009', '4010', '4011', '4012', '4013', '4014', '4015', '4016', '4017', '4018', '4019']
    },
    'United Kingdom': {
        'London': ['E1 6AN', 'W1A 1AA', 'SW1A 1AA', 'EC1A 1BB', 'SE1 7PB'],
        'Manchester': ['M1 1AD', 'M2 3DE', 'M3 4FG', 'M4 5HI', 'M5 6JK'],
        'Birmingham': ['B1 1AA', 'B2 2BB', 'B3 3CC', 'B4 4DD', 'B5 5EE'],
        'Leeds': ['LS1 1UR', 'LS2 2AA', 'LS3 3BB', 'LS4 4CC', 'LS5 5DD'],
        'Glasgow': ['G1 1XQ', 'G2 2AA', 'G3 3BB', 'G4 4CC', 'G5 5DD']
    },
    'Spain': {
        'Madrid': ['28001', '28002', '28003', '28004', '28005'],
        'Barcelona': ['08001', '08002', '08003', '08004', '08005'],
        'Valencia': ['46001', '46002', '46003', '46004', '46005'],
        'Seville': ['41001', '41002', '41003', '41004', '41005'],
        'Bilbao': ['48001', '48002', '48003', '48004', '48005']
    },
    'Italy': {
        'Rome': ['00118', '00119', '00120', '00121', '00122'],
        'Milan': ['20121', '20122', '20123', '20124', '20125'],
        'Naples': ['80121', '80122', '80123', '80124', '80125'],
        'Turin': ['10121', '10122', '10123', '10124', '10125'],
        'Florence': ['50121', '50122', '50123', '50124', '50125']
    },
    'Canada': {
        'Toronto': ['M5H 2N2', 'M5V 2T6', 'M4B 1B3', 'M6P 2T1', 'M5J 2N8'],
        'Montreal': ['H3B 1A7', 'H2Y 1T1', 'H3G 1M8', 'H2Z 1A1', 'H3A 2A6'],
        'Vancouver': ['V6B 1A1', 'V5K 1A1', 'V6Z 2E6', 'V6C 2R6', 'V6E 3V6'],
        'Calgary': ['T2P 1J9', 'T2R 0G4', 'T2S 1A1', 'T2T 2T2', 'T2V 4V4'],
        'Ottawa': ['K1P 1J1', 'K1A 0A9', 'K1N 5T5', 'K1R 7S8', 'K1S 5B6']
    },
    'Australia': {
        'Sydney': ['2000', '2001', '2002', '2003', '2004'],
        'Melbourne': ['3000', '3001', '3002', '3003', '3004'],
        'Brisbane': ['4000', '4001', '4002', '4003', '4004'],
        'Perth': ['6000', '6001', '6002', '6003', '6004'],
        'Adelaide': ['5000', '5001', '5002', '5003', '5004']
    },
    'Brazil': {
        'São Paulo': ['01000-000', '01310-100', '01415-000', '05426-100', '04538-132'],
        'Rio de Janeiro': ['20040-002', '22041-001', '22450-000', '22270-010', '20550-013'],
        'Brasília': ['70040-010', '70297-400', '70610-200', '70710-900', '71680-357'],
        'Salvador': ['40020-000', '41810-000', '41720-070', '40140-110', '40296-710'],
        'Fortaleza': ['60165-121', '60175-055', '60150-161', '60325-002', '60811-341']
    },
    'Switzerland': {
        'Zurich': ['8001', '8002', '8003', '8004', '8005'],
        'Geneva': ['1201', '1202', '1203', '1204', '1205'],
        'Basel': ['4001', '4051', '4052', '4053', '4054'],
        'Lausanne': ['1003', '1004', '1005', '1006', '1007'],
        'Bern': ['3005', '3006', '3007', '3008', '3011']
    },
    'Netherlands': {
        'Amsterdam': ['1012 JS', '1017 PR', '1071 XX', '1091 GH', '1102 BR'],
        'Rotterdam': ['3011 AA', '3012 KA', '3013 AL', '3014 GT', '3015 GD'],
        'The Hague': ['2511 BT', '2512 AA', '2513 AB', '2514 AC', '2515 AD'],
        'Utrecht': ['3511 AA', '3512 AB', '3513 AC', '3514 AD', '3515 AE'],
        'Eindhoven': ['5611 AA', '5612 AB', '5613 AC', '5614 AD', '5615 AE']
    },
    'Turkey': {
        'Istanbul': ['34000', '34100', '34200', '34300', '34400'],
        'Ankara': ['06000', '06100', '06200', '06300', '06400'],
        'Izmir': ['35000', '35100', '35200', '35300', '35400'],
        'Bursa': ['16000', '16100', '16200', '16300', '16400'],
        'Antalya': ['07000', '07100', '07200', '07300', '07400']
    },
    'Poland': {
        'Warsaw': ['00-001', '00-002', '00-003', '00-004', '00-005'],
        'Kraków': ['30-001', '30-002', '30-003', '30-004', '30-005'],
        'Łódź': ['90-001', '90-002', '90-003', '90-004', '90-005'],
        'Wrocław': ['50-001', '50-002', '50-003', '50-004', '50-005'],
        'Poznań': ['60-001', '60-002', '60-003', '60-004', '60-005']
    },
    'Portugal': {
        'Lisbon': ['1000-001', '1100-001', '1200-001', '1300-001', '1400-001'],
        'Porto': ['4000-001', '4100-001', '4200-001', '4300-001', '4400-001'],
        'Braga': ['4700-001', '4710-001', '4720-001', '4730-001', '4740-001']
    },
    'Russia': {
        'Moscow': ['101000', '102000', '103000', '104000', '105000'],
        'Saint Petersburg': ['190000', '191000', '192000', '193000', '194000'],
        'Novosibirsk': ['630000', '630001', '630002', '630003', '630004']
    },
    'Japan': {
        'Tokyo': ['100-0001', '100-0002', '100-0003', '100-0004', '100-0005'],
        'Osaka': ['530-0001', '530-0002', '530-0003', '530-0004', '530-0005'],
        'Kyoto': ['600-8001', '600-8002', '600-8003', '600-8004', '600-8005']
    },
    'China': {
        'Beijing': ['100000', '100001', '100002', '100003', '100004'],
        'Shanghai': ['200000', '200001', '200002', '200003', '200004'],
        'Guangzhou': ['510000', '510001', '510002', '510003', '510004']
    },
    'India': {
        'Mumbai': ['400001', '400002', '400003', '400004', '400005'],
        'Delhi': ['110001', '110002', '110003', '110004', '110005'],
        'Bangalore': ['560001', '560002', '560003', '560004', '560005']
    },
    'Mexico': {
        'Mexico City': ['01000', '02000', '03000', '04000', '05000'],
        'Guadalajara': ['44100', '44200', '44300', '44400', '44500'],
        'Monterrey': ['64000', '64100', '64200', '64300', '64400']
    },
    'Sweden': {
        'Stockholm': ['111 22', '112 23', '113 24', '114 25', '115 26'],
        'Gothenburg': ['411 03', '412 04', '413 05', '414 06', '415 07'],
        'Malmö': ['211 11', '212 12', '213 13', '214 14', '215 15']
    },
    'Denmark': {
        'Copenhagen': ['1000', '1100', '1200', '1300', '1400'],
        'Aarhus': ['8000', '8100', '8200', '8300', '8400'],
        'Odense': ['5000', '5100', '5200', '5300', '5400']
    },
    'Finland': {
        'Helsinki': ['00100', '00120', '00130', '00140', '00150'],
        'Espoo': ['02100', '02110', '02120', '02130', '02140'],
        'Tampere': ['33100', '33180', '33200', '33210', '33230']
    },
    'Ireland': {
        'Dublin': ['D01', 'D02', 'D03', 'D04', 'D05'],
        'Cork': ['T12', 'T23', 'T34', 'T45', 'T56'],
        'Galway': ['H91', 'H92', 'H93', 'H94', 'H95']
    },
    'Austria': {
        'Vienna': ['1010', '1020', '1030', '1040', '1050'],
        'Graz': ['8010', '8020', '8030', '8040', '8050'],
        'Salzburg': ['5020', '5023', '5026', '5061', '5071']
    },
    'Greece': {
        'Athens': ['104 31', '104 32', '104 33', '104 34', '104 35'],
        'Thessaloniki': ['546 21', '546 22', '546 23', '546 24', '546 25'],
        'Patras': ['262 21', '262 22', '262 23', '262 24', '262 25']
    },
    'Iran': {
        'Tehran': ['11369', '14155', '19979', '15875', '19395'],
        'Mashhad': ['91337', '91735', '91857', '91775', '91881'],
        'Isfahan': ['81464', '81746', '81647', '81546', '81856']
    },
    'New Zealand': {
        'Auckland': ['1010', '1011', '1021', '1023', '1024'],
        'Wellington': ['6011', '6012', '6021', '6022', '6023'],
        'Christchurch': ['8011', '8013', '8014', '8022', '8023']
    },
    'Serbia': {
        'Belgrade': ['11000', '11010', '11030', '11050', '11060'],
        'Novi Sad': ['21000', '21101', '21102', '21103', '21104'],
        'Niš': ['18000', '18101', '18102', '18103', '18104']
    },
    'Ukraine': {
        'Kyiv': ['01000', '01001', '01010', '01011', '01015'],
        'Kharkiv': ['61000', '61001', '61002', '61003', '61004'],
        'Odesa': ['65000', '65001', '65002', '65003', '65004']
    },
    'South Korea': {
        'Seoul': ['04524', '06000', '03000', '05000', '02000'],
        'Busan': ['48000', '46000', '47000', '49000', '48099'],
        'Incheon': ['21000', '22000', '23000', '21999', '22999']
    },
    'Thailand': {
        'Bangkok': ['10100', '10200', '10300', '10400', '10500'],
        'Chiang Mai': ['50000', '50100', '50200', '50300', '50230'],
        'Phuket': ['83000', '83100', '83110', '83120', '83130']
    },
    'Vietnam': {
        'Hanoi': ['100000', '110000', '120000', '130000', '140000'],
        'Ho Chi Minh City': ['700000', '710000', '720000', '730000', '740000'],
        'Da Nang': ['550000', '560000', '570000', '550100', '550200']
    },
    'Argentina': {
        'Buenos Aires': ['C1002', 'C1003', 'C1004', 'C1005', 'C1006'],
        'Cordoba': ['X5000', 'X5001', 'X5002', 'X5003', 'X5004'],
        'Rosario': ['S2000', 'S2001', 'S2002', 'S2003', 'S2004']
    },
    'Chile': {
        'Santiago': ['8320000', '8330000', '8340000', '8350000', '8360000'],
        'Valparaíso': ['2340000', '2350000', '2360000', '2370000', '2380000'],
        'Concepción': ['4030000', '4040000', '4050000', '4060000', '4070000']
    },
    'Colombia': {
        'Bogotá': ['110111', '110221', '110311', '110411', '110511'],
        'Medellín': ['050001', '050002', '050003', '050004', '050005'],
        'Cali': ['760001', '760002', '760003', '760004', '760005']
    },
    'Egypt': {
        'Cairo': ['11511', '11512', '11513', '11514', '11515'],
        'Alexandria': ['21500', '21501', '21502', '21503', '21504'],
        'Giza': ['12511', '12512', '12513', '12514', '12515']
    },
    'South Africa': {
        'Cape Town': ['8001', '8002', '8003', '8004', '8005'],
        'Johannesburg': ['2001', '2002', '2003', '2004', '2005'],
        'Durban': ['4001', '4002', '4003', '4004', '4005']
    },
    'Czech Republic': {
        'Prague': ['110 00', '120 00', '130 00', '140 00', '150 00'],
        'Brno': ['602 00', '603 00', '604 00', '605 00', '606 00'],
        'Ostrava': ['702 00', '703 00', '704 00', '705 00', '706 00']
    },
    'Hungary': {
        'Budapest': ['1051', '1052', '1061', '1062', '1071'],
        'Debrecen': ['4024', '4025', '4026', '4027', '4028'],
        'Szeged': ['6720', '6721', '6722', '6723', '6724']
    },
    'Romania': {
        'Bucharest': ['010011', '020011', '030011', '040011', '050011'],
        'Cluj-Napoca': ['400001', '400002', '400003', '400004', '400005'],
        'Timisoara': ['300001', '300002', '300003', '300004', '300005']
    },
    'Bangladesh': {
        'Dhaka': ['1000', '1100', '1200', '1212', '1230'],
        'Chittagong': ['4000', '4100', '4200', '4202', '4204'],
        'Khulna': ['9000', '9100', '9200', '9208', '9210']
    },
    'Algeria': {
        'Algiers': ['16000', '16001', '16002', '16003', '16004'],
        'Oran': ['31000', '31001', '31002', '31003', '31004'],
        'Constantine': ['25000', '25001', '25002', '25003', '25004']
    },
    'Tunisia': {
        'Tunis': ['1000', '1001', '1002', '1003', '1004'],
        'Sfax': ['3000', '3001', '3002', '3003', '3004'],
        'Sousse': ['4000', '4001', '4002', '4003', '4004']
    },
    'Kenya': {
        'Nairobi': ['00100', '00200', '00500', '00600', '00800'],
        'Mombasa': ['80100', '80200', '80300', '80400', '80500'],
        'Kisumu': ['40100', '40200', '40300', '40400', '40500']
    },
    'Ethiopia': {
        'Addis Ababa': ['1000', '1001', '1002', '1003', '1004'],
        'Dire Dawa': ['3000', '3001', '3002', '3003', '3004'],
        'Mekelle': ['7000', '7001', '7002', '7003', '7004']
    },
    'Ghana': {
        'Accra': ['GA-001', 'GA-002', 'GA-003', 'GA-004', 'GA-005'],
        'Kumasi': ['AK-001', 'AK-002', 'AK-003', 'AK-004', 'AK-005'],
        'Tamale': ['NT-001', 'NT-002', 'NT-003', 'NT-004', 'NT-005']
    },
    'Tanzania': {
        'Dar es Salaam': ['11000', '11101', '11102', '11103', '11104'],
        'Mwanza': ['33000', '33101', '33102', '33103', '33104'],
        'Arusha': ['23000', '23101', '23102', '23103', '23104']
    },
    'Uganda': {
        'Kampala': ['10101', '10102', '10103', '10104', '10105'],
        'Entebbe': ['10201', '10202', '10203', '10204', '10205'],
        'Jinja': ['10301', '10302', '10303', '10304', '10305']
    },
    'Venezuela': {
        'Caracas': ['1010', '1020', '1030', '1040', '1050'],
        'Maracaibo': ['4001', '4002', '4003', '4004', '4005'],
        'Valencia': ['2001', '2002', '2003', '2004', '2005']
    },
    'Ecuador': {
        'Quito': ['170101', '170102', '170103', '170104', '170105'],
        'Guayaquil': ['090101', '090102', '090103', '090104', '090105'],
        'Cuenca': ['010101', '010102', '010103', '010104', '010105']
    },
    'Bolivia': {
        'La Paz': ['0001', '0002', '0003', '0004', '0005'],
        'Santa Cruz': ['1001', '1002', '1003', '1004', '1005'],
        'Cochabamba': ['2001', '2002', '2003', '2004', '2005']
    },
    'Paraguay': {
        'Asunción': ['1001', '1101', '1201', '1301', '1401'],
        'Ciudad del Este': ['7000', '7001', '7002', '7003', '7004'],
        'Encarnación': ['6000', '6001', '6002', '6003', '6004']
    },
    'Uruguay': {
        'Montevideo': ['11000', '11100', '11200', '11300', '11400'],
        'Salto': ['50000', '50001', '50002', '50003', '50004'],
        'Ciudad de la Costa': ['15000', '15001', '15002', '15003', '15004']
    },
    'Philippines': {
        'Manila': ['1000', '1001', '1002', '1003', '1004'],
        'Quezon City': ['1100', '1101', '1102', '1103', '1104'],
        'Cebu City': ['6000', '6001', '6002', '6003', '6004']
    },
    'Indonesia': {
        'Jakarta': ['10110', '10120', '10130', '10140', '10150'],
        'Surabaya': ['60111', '60112', '60113', '60114', '60115'],
        'Bandung': ['40111', '40112', '40113', '40114', '40115']
    },
    'Malaysia': {
        'Kuala Lumpur': ['50000', '50050', '50100', '50150', '50200'],
        'George Town': ['10000', '10050', '10100', '10150', '10200'],
        'Johor Bahru': ['80000', '80050', '80100', '80150', '80200']
    },
    'Singapore': {
        'Singapore': ['018956', '048624', '238877', '500000', '600000']
    },
    'Pakistan': {
        'Karachi': ['74000', '74200', '74400', '74600', '74800'],
        'Lahore': ['54000', '54020', '54040', '54060', '54080'],
        'Islamabad': ['44000', '44010', '44020', '44030', '44040']
    },
    'Nigeria': {
        'Lagos': ['100001', '101001', '102001', '103001', '104001'],
        'Abuja': ['900001', '900101', '900201', '900301', '900401'],
        'Kano': ['700001', '700101', '700201', '700301', '700401']
    },
    'Morocco': {
        'Casablanca': ['20000', '20100', '20200', '20300', '20400'],
        'Rabat': ['10000', '10100', '10200', '10300', '10400'],
        'Marrakech': ['40000', '40100', '40200', '40300', '40400']
    },
    'Saudi Arabia': {
        'Riyadh': ['11564', '12211', '12212', '12213', '12214'],
        'Jeddah': ['21442', '23421', '23422', '23423', '23424'],
        'Mecca': ['21955', '24231', '24232', '24233', '24234']
    },
    'Israel': {
        'Tel Aviv': ['61000', '62000', '63000', '64000', '65000'],
        'Jerusalem': ['91000', '92000', '93000', '94000', '95000'],
        'Haifa': ['31000', '32000', '33000', '34000', '35000']
    },
    'Peru': {
        'Lima': ['15001', '15002', '15003', '15004', '15005'],
        'Arequipa': ['04001', '04002', '04003', '04004', '04005'],
        'Trujillo': ['13001', '13002', '13003', '13004', '13005']
    }
}

city_streets = {
    'France': {
        'Paris': ['Rue de la Paix', 'Avenue des Champs-Élysées', 'Boulevard Saint-Germain'],
        'Marseille': ['Rue Saint-Ferréol', 'Cours Julien', 'Rue de la République'],
        'Lyon': ['Rue de la République', 'Rue Mercière', 'Cours Vitton']
    },
    'USA': {
        'New York': ['Broadway', 'Wall Street', 'Fifth Avenue'],
        'Los Angeles': ['Sunset Boulevard', 'Hollywood Boulevard', 'Rodeo Drive'],
        'Chicago': ['Michigan Avenue', 'State Street', 'Lake Shore Drive']
    },
    'Germany': {
        'Berlin': ['Unter den Linden', 'Friedrichstrasse', 'Kurfürstendamm'],
        'Munich': ['Maximilianstrasse', 'Leopoldstrasse', 'Sendlinger Strasse'],
        'Hamburg': ['Reeperbahn', 'Mönckebergstrasse', 'Spitalerstrasse']
    },
    'Belgium': {
        'Brussels': ['Rue Neuve', 'Avenue Louise', 'Boulevard Anspach'],
        'Antwerp': ['Meir', 'Handelsstraat', 'Pelgrimstraat'],
        'Ghent': ['Veldstraat', 'Korenmarkt', 'Sint-Baafsplein']
    },
    'Norway': {
        'Oslo': ['Karl Johans gate', 'Bogstadveien', 'Grünerløkka'],
        'Bergen': ['Bryggen', 'Torgallmenningen', 'Strømgaten'],
        'Stavanger': ['Øvre Holmegate', 'Vågen', 'Løkkeveien']
    },
    'United Kingdom': {
        'London': ['Oxford Street', 'Regent Street', 'Bond Street', 'Piccadilly', 'Baker Street'],
        'Manchester': ['Deansgate', 'Market Street', 'King Street', 'Portland Street', 'Oxford Road'],
        'Birmingham': ['New Street', 'Corporation Street', 'High Street', 'Broad Street', 'Bull Ring'],
        'Leeds': ['Briggate', 'The Headrow', 'Vicar Lane', 'Boar Lane', 'Albion Street'],
        'Glasgow': ['Buchanan Street', 'Sauchiehall Street', 'Argyle Street', 'George Square', 'High Street']
    },
    'Spain': {
        'Madrid': ['Gran Vía', 'Calle de Alcalá', 'Paseo de la Castellana', 'Calle Mayor', 'Calle de Serrano'],
        'Barcelona': ['La Rambla', 'Passeig de Gràcia', 'Avinguda Diagonal', 'Carrer de Ferran', 'Carrer de Balmes'],
        'Valencia': ['Calle Colón', 'Calle Xàtiva', 'Avenida del Puerto', 'Gran Vía Marqués del Turia', 'Calle San Vicente Mártir'],
        'Seville': ['Avenida de la Constitución', 'Calle Sierpes', 'Calle Tetuán', 'Calle Betis', 'Paseo de Colón'],
        'Bilbao': ['Gran Vía de Don Diego López de Haro', 'Calle Ercilla', 'Calle Ledesma', 'Alameda de Urquijo', 'Calle Autonomía']
    },
    'Italy': {
        'Rome': ['Via del Corso', 'Via dei Condotti', 'Via Veneto', 'Via Nazionale', 'Via Appia Nuova'],
        'Milan': ['Via Montenapoleone', 'Corso Buenos Aires', 'Via Dante', 'Corso Vittorio Emanuele II', 'Via della Spiga'],
        'Naples': ['Spaccanapoli', 'Via Toledo', 'Corso Umberto I', 'Via dei Tribunali', 'Via Chiaia'],
        'Turin': ['Via Roma', 'Via Po', 'Via Garibaldi', 'Corso Vittorio Emanuele II', 'Piazza Castello'],
        'Florence': ['Via de\' Tornabuoni', 'Via dei Calzaiuoli', 'Via Roma', 'Piazza della Signoria', 'Ponte Vecchio']
    },
    'Canada': {
        'Toronto': ['Yonge Street', 'Queen Street West', 'King Street West', 'Bay Street', 'Bloor Street'],
        'Montreal': ['Saint Catherine Street', 'Saint Laurent Boulevard', 'Sherbrooke Street', 'Peel Street', 'Crescent Street'],
        'Vancouver': ['Robson Street', 'Granville Street', 'Burrard Street', 'Davie Street', 'Denman Street'],
        'Calgary': ['Stephen Avenue', '17th Avenue SW', 'Macleod Trail', 'Crowchild Trail', 'Bow Trail'],
        'Ottawa': ['Rideau Street', 'Bank Street', 'Elgin Street', 'Sussex Drive', 'Wellington Street']
    },
    'Australia': {
        'Sydney': ['George Street', 'Pitt Street', 'Oxford Street', 'Macquarie Street', 'Elizabeth Street'],
        'Melbourne': ['Collins Street', 'Bourke Street', 'Swanston Street', 'Flinders Street', 'Elizabeth Street'],
        'Brisbane': ['Queen Street', 'Adelaide Street', 'Ann Street', 'Edward Street', 'Albert Street'],
        'Perth': ['St Georges Terrace', 'Hay Street', 'Murray Street', 'William Street', 'Barrack Street'],
        'Adelaide': ['Rundle Mall', 'King William Street', 'North Terrace', 'Gouger Street', 'Hindley Street']
    },
    'Brazil': {
        'São Paulo': ['Avenida Paulista', 'Rua Oscar Freire', 'Avenida Brigadeiro Faria Lima', 'Rua Augusta', 'Avenida Ipiranga'],
        'Rio de Janeiro': ['Avenida Atlântica', 'Avenida Vieira Souto', 'Rua Visconde de Pirajá', 'Avenida Rio Branco', 'Rua do Catete'],
        'Brasília': ['Eixo Monumental', 'W3 Sul', 'W3 Norte', 'L2 Sul', 'L2 Norte'],
        'Salvador': ['Avenida Sete de Setembro', 'Avenida Oceânica', 'Rua Chile', 'Avenida Tancredo Neves', 'Avenida Paralela'],
        'Fortaleza': ['Avenida Beira Mar', 'Avenida Monsenhor Tabosa', 'Rua Santos Dumont', 'Avenida Dom Luís', 'Avenida Santos Dumont']
    },
    'Switzerland': {
        'Zurich': ['Bahnhofstrasse', 'Niederdorfstrasse', 'Langstrasse', 'Rennweg', 'Augustinergasse'],
        'Geneva': ['Rue du Rhône', 'Rue de la Confédération', 'Rue du Marché', 'Rue de la Croix-d\'Or', 'Rue de Rive'],
        'Basel': ['Freie Strasse', 'Gerbergasse', 'Marktplatz', 'Steinenvorstadt', 'Clarastrasse'],
        'Lausanne': ['Rue de Bourg', 'Place Saint-François', 'Rue du Petit-Chêne', 'Place de la Riponne', 'Avenue de la Gare'],
        'Bern': ['Kramgasse', 'Marktgasse', 'Spitalgasse', 'Gerechtigkeitsgasse', 'Bärenplatz']
    },
    'Netherlands': {
        'Amsterdam': ['Kalverstraat', 'Damrak', 'Leidsestraat', 'Nieuwendijk', 'PC Hooftstraat'],
        'Rotterdam': ['Coolsingel', 'Lijnbaan', 'Beurstraverse', 'Witte de Withstraat', 'Nieuwe Binnenweg'],
        'The Hague': ['Spuistraat', 'Grote Marktstraat', 'Lange Poten', 'Noordeinde', 'Denneweg'],
        'Utrecht': ['Oudegracht', 'Steenweg', 'Lange Elisabethstraat', 'Vredenburg', 'Lijnmarkt'],
        'Eindhoven': ['Demer', 'Rechtestraat', 'Vrijstraat', 'Kleine Berg', 'Stratumseind']
    },
    'Turkey': {
        'Istanbul': ['İstiklal Caddesi', 'Bağdat Caddesi', 'Abdi İpekçi Caddesi', 'Nispetiye Caddesi', 'Alemdar Caddesi'],
        'Ankara': ['Atatürk Bulvarı', 'Tunalı Hilmi Caddesi', 'Arjantin Caddesi', 'Filistin Caddesi', 'Cinnah Caddesi'],
        'Izmir': ['Kıbrıs Şehitleri Caddesi', 'Atatürk Caddesi', 'Plevne Bulvarı', 'Talatpaşa Bulvarı', 'Cumhuriyet Bulvarı'],
        'Bursa': ['Atatürk Caddesi', 'Altıparmak Caddesi', 'Çekirge Caddesi', 'Fevzi Çakmak Caddesi', 'Haşim İşcan Caddesi'],
        'Antalya': ['Işıklar Caddesi', 'Güllük Caddesi', 'Konyaaltı Caddesi', 'Lara Caddesi', 'Atatürk Caddesi']
    },
    'Poland': {
        'Warsaw': ['Nowy Świat', 'Krakowskie Przedmieście', 'Marszałkowska', 'Aleje Jerozolimskie', 'Chmielna'],
        'Kraków': ['Floriańska', 'Grodzka', 'Szewska', 'Sławkowska', 'Długa'],
        'Łódź': ['Piotrkowska', 'Aleja Kościuszki', 'Narutowicza', 'Zachodnia', 'Mickiewicza'],
        'Wrocław': ['Świdnicka', 'Oławska', 'Ruska', 'Kiełbaśnicza', 'Więzienna'],
        'Poznań': ['Półwiejska', 'Święty Marcin', 'Głogowska', 'Dąbrowskiego', 'Grunwaldzka']
    },
    'Portugal': {
        'Lisbon': ['Avenida da Liberdade', 'Rua Augusta', 'Rua do Ouro', 'Rua da Prata', 'Avenida Almirante Reis'],
        'Porto': ['Avenida dos Aliados', 'Rua de Santa Catarina', 'Rua de Cedofeita', 'Avenida da Boavista', 'Rua das Flores'],
        'Braga': ['Avenida da Liberdade', 'Rua do Souto', 'Avenida Central', 'Rua dos Chãos', 'Rua de São Marcos']
    },
    'Russia': {
        'Moscow': ['Tverskaya Street', 'Arbat Street', 'Leninsky Avenue', 'Kutuzovsky Prospect', 'Novy Arbat'],
        'Saint Petersburg': ['Nevsky Prospect', 'Liteyny Prospect', 'Sadovaya Street', 'Rubinstein Street', 'Zhukovsky Street'],
        'Novosibirsk': ['Krasny Prospect', 'Lenin Street', 'Gogol Street', 'Frunze Street', 'Sovetskaya Street']
    },
    'Japan': {
        'Tokyo': ['Ginza', 'Takeshita Street', 'Omotesando', 'Chuo-dori', 'Meiji-dori'],
        'Osaka': ['Dotonbori', 'Midosuji', 'Shinsaibashi-suji', 'Sennichimae', 'Sakaisuji'],
        'Kyoto': ['Shijo-dori', 'Kawaramachi-dori', 'Karasuma-dori', 'Oike-dori', 'Sanjo-dori']
    },
    'China': {
        'Beijing': ['Wangfujing', 'Chang\'an Avenue', 'Qianmen Street', 'Sanlitun', 'Nanluoguxiang'],
        'Shanghai': ['Nanjing Road', 'Huaihai Road', 'The Bund', 'West Nanjing Road', 'Middle Huaihai Road'],
        'Guangzhou': ['Beijing Road', 'Shangxiajiu', 'Tianhe Road', 'Huanshi Road', 'Dongfeng Road']
    },
    'India': {
        'Mumbai': ['Marine Drive', 'Colaba Causeway', 'Linking Road', 'Hill Road', 'Fashion Street'],
        'Delhi': ['Chandni Chowk', 'Connaught Place', 'Janpath', 'Khan Market', 'Paharganj'],
        'Bangalore': ['MG Road', 'Brigade Road', 'Commercial Street', 'Indiranagar 100ft Road', 'Residency Road']
    },
    'Mexico': {
        'Mexico City': ['Paseo de la Reforma', 'Avenida Insurgentes', 'Avenida Presidente Masaryk', 'Calle Madero', 'Avenida Juárez'],
        'Guadalajara': ['Avenida Vallarta', 'Avenida Chapultepec', 'Calle López Cotilla', 'Avenida México', 'Avenida Hidalgo'],
        'Monterrey': ['Avenida Constitución', 'Calzada San Pedro', 'Avenida Garza Sada', 'Calle Morelos', 'Avenida Juárez']
    },
    'Sweden': {
        'Stockholm': ['Drottninggatan', 'Birger Jarlsgatan', 'Kungsgatan', 'Sveavägen', 'Strandvägen'],
        'Gothenburg': ['Kungsportsavenyen', 'Linnégatan', 'Kungsgatan', 'Vasagatan', 'Östra Hamngatan'],
        'Malmö': ['Södergatan', 'Stora Nygatan', 'Baltzarsgatan', 'Bergsgatan', 'Amiralsgatan']
    },
    'Denmark': {
        'Copenhagen': ['Strøget', 'Nyhavn', 'Vesterbrogade', 'Nørrebrogade', 'Amagerbrogade'],
        'Aarhus': ['Strøget', 'Søndergade', 'Frederiksgade', 'Nørre Allé', 'Vestergade'],
        'Odense': ['Vestergade', 'Kongensgade', 'Nørregade', 'Overgade', 'Nedergade']
    },
    'Finland': {
        'Helsinki': ['Aleksanterinkatu', 'Mannerheimintie', 'Esplanadi', 'Bulevardi', 'Fredrikinkatu'],
        'Espoo': ['Merituulentie', 'Tapiolantie', 'Länsiväylä', 'Turunväylä', 'Kehä I'],
        'Tampere': ['Hämeenkatu', 'Kauppakatu', 'Kuninkaankatu', 'Satakunnankatu', 'Itsenäisyydenkatu']
    },
    'Ireland': {
        'Dublin': ['Grafton Street', 'O\'Connell Street', 'Henry Street', 'Dame Street', 'Dawson Street'],
        'Cork': ['St. Patrick\'s Street', 'Oliver Plunkett Street', 'Grand Parade', 'South Mall', 'Washington Street'],
        'Galway': ['Shop Street', 'Quay Street', 'High Street', 'Eyre Square', 'Dominick Street']
    },
    'Austria': {
        'Vienna': ['Kärntner Straße', 'Mariahilfer Straße', 'Graben', 'Kohlmarkt', 'Ringstraße'],
        'Graz': ['Herrengasse', 'Sporgasse', 'Sackstraße', 'Murgasse', 'Schmiedgasse'],
        'Salzburg': ['Getreidegasse', 'Linzer Gasse', 'Judengasse', 'Goldgasse', 'Kaigasse']
    },
    'Greece': {
        'Athens': ['Ermou Street', 'Panepistimiou Street', 'Stadiou Street', 'Athinas Street', 'Patission Street'],
        'Thessaloniki': ['Tsimiski Street', 'Egnatia Street', 'Nikis Avenue', 'Mitropoleos Street', 'Agias Sofias Street'],
        'Patras': ['Maizonos Street', 'Korinthou Street', 'Agiou Andreou Street', 'Riga Fereou Street', 'Gounari Street']
    },
    'Iran': {
        'Tehran': ['Valiasr Street', 'Enghelab Street', 'Shariati Street', 'Pasdaran Street', 'Jordan Street'],
        'Mashhad': ['Imam Reza Street', 'Ahmadabad Street', 'Sajjad Boulevard', 'Vakilabad Boulevard', 'Tabarsi Street'],
        'Isfahan': ['Chahar Bagh', 'Sepah Street', 'Bozorgmehr Street', 'Amadegah Street', 'Nazar Street']
    },
    'New Zealand': {
        'Auckland': ['Queen Street', 'Karangahape Road', 'Ponsonby Road', 'Dominion Road', 'Tamaki Drive'],
        'Wellington': ['Lambton Quay', 'Cuba Street', 'Courtenay Place', 'Willis Street', 'The Terrace'],
        'Christchurch': ['Colombo Street', 'Riccarton Road', 'Papanui Road', 'Bealey Avenue', 'Moorhouse Avenue']
    },
    'Serbia': {
        'Belgrade': ['Knez Mihailova', 'Terazije', 'Bulevar kralja Aleksandra', 'Nemanjina', 'Slavija'],
        'Novi Sad': ['Zmaj Jovina', 'Dunavska', 'Bulevar oslobođenja', 'Jevrejska', 'Futoška'],
        'Niš': ['Obrenovićeva', 'Vožda Karađorđa', 'Nikole Pašića', 'Bulevar Nemanjića', 'Knjaževačka']
    },
    'Ukraine': {
        'Kyiv': ['Khreshchatyk', 'Volodymyrska', 'Saksahanskoho', 'Velyka Vasylkivska', 'Lesi Ukrainky'],
        'Kharkiv': ['Sumska', 'Pushkinska', 'Poltavskyi Shliakh', 'Klochkivska', 'Moskovskyi Avenue'],
        'Odesa': ['Deribasivska', 'Hrebtska', 'Katerynynska', 'Pushkinska', 'Lanzheronivska']
    },
    'South Korea': {
        'Seoul': ['Gangnam-daero', 'Teheran-ro', 'Sejong-daero', 'Jongno', 'Itaewon-ro'],
        'Busan': ['Jungang-daero', 'Haeundae-ro', 'Gwangbok-ro', 'Seomyeon-ro', 'Dalmaji-gil'],
        'Incheon': ['Inha-ro', 'Wolmi-ro', 'Songdo-daero', 'Bupyeong-daero', 'Arts Center-daero']
    },
    'Thailand': {
        'Bangkok': ['Sukhumvit Road', 'Silom Road', 'Khao San Road', 'Yaowarat Road', 'Ratchadamnoen Avenue'],
        'Chiang Mai': ['Nimmanhaemin Road', 'Tha Phae Road', 'Chang Klan Road', 'Huay Kaew Road', 'Charoen Prathet Road'],
        'Phuket': ['Thalang Road', 'Bangla Road', 'Phang Nga Road', 'Dibuk Road', 'Rat-U-Thit Road']
    },
    'Vietnam': {
        'Hanoi': ['Nguyen Hue', 'Trang Tien', 'Hang Gai', 'Dinh Tien Hoang', 'Le Thai To'],
        'Ho Chi Minh City': ['Dong Khoi', 'Le Loi', 'Nguyen Hue', 'Bui Vien', 'Pham Ngu Lao'],
        'Da Nang': ['Bach Dang', 'Tran Phu', 'Le Duan', 'Nguyen Van Linh', 'Vo Nguyen Giap']
    },
    'Argentina': {
        'Buenos Aires': ['Avenida 9 de Julio', 'Avenida Corrientes', 'Calle Florida', 'Avenida de Mayo', 'Avenida Santa Fe'],
        'Cordoba': ['Avenida Colón', 'Avenida General Paz', 'Calle San Martín', 'Bulevar Chacabuco', 'Avenida Vélez Sarsfield'],
        'Rosario': ['Bulevar Oroño', 'Calle Córdoba', 'Avenida Pellegrini', 'Peatonal San Martín', 'Avenida Belgrano']
    },
    'Chile': {
        'Santiago': ['Avenida Libertador General Bernardo O\'Higgins', 'Paseo Ahumada', 'Avenida Providencia', 'Avenida Apoquindo', 'Calle Estado'],
        'Valparaíso': ['Avenida Pedro Montt', 'Calle Esmeralda', 'Calle Condell', 'Avenida Brasil', 'Avenida Errázuriz'],
        'Concepción': ['Calle Barros Arana', 'Avenida O\'Higgins', 'Calle Aníbal Pinto', 'Avenida Los Carrera', 'Calle Caupolicán']
    },
    'Colombia': {
        'Bogotá': ['Carrera 7', 'Avenida Jiménez', 'Calle 26', 'Avenida Caracas', 'Carrera 15'],
        'Medellín': ['Carrera 43A', 'Calle 10', 'Avenida El Poblado', 'Carrera 70', 'Avenida Oriental'],
        'Cali': ['Avenida 6', 'Calle 5', 'Carrera 1', 'Avenida Roosevelt', 'Calle 9']
    },
    'Egypt': {
        'Cairo': ['Tahrir Square', 'Corniche El Nile', 'Qasr El Nil Street', 'Talaat Harb Street', 'Ramses Street'],
        'Alexandria': ['Corniche', 'Saad Zaghloul Street', 'Fouad Street', 'Nabi Daniel Street', 'Safia Zaghloul Street'],
        'Giza': ['Pyramids Road', 'Faisal Street', 'Haram Street', 'King Faisal Street', 'Dokki Street']
    },
    'South Africa': {
        'Cape Town': ['Long Street', 'Adderley Street', 'Kloof Street', 'Bree Street', 'Victoria Road'],
        'Johannesburg': ['Nelson Mandela Bridge', 'Commissioner Street', 'Main Street', 'Fox Street', 'Vilakazi Street'],
        'Durban': ['Florida Road', 'West Street', 'Smith Street', 'Umhlanga Rocks Drive', 'Marine Parade']
    },
    'Czech Republic': {
        'Prague': ['Wenceslas Square', 'Charles Bridge', 'Pařížská', 'Na Příkopě', 'Celetná'],
        'Brno': ['Masarykova', 'Česká', 'Joštova', 'Náměstí Svobody', 'Husova'],
        'Ostrava': ['Stodolní', 'Nádražní', '28. října', 'Poštovní', 'Masarykovo náměstí']
    },
    'Hungary': {
        'Budapest': ['Váci utca', 'Andrássy út', 'Király utca', 'Nagykörút', 'Rákóczi út'],
        'Debrecen': ['Piac utca', 'Kossuth utca', 'Csapó utca', 'Hatvan utca', 'Széchenyi utca'],
        'Szeged': ['Kárász utca', 'Tisza Lajos körút', 'Széchenyi tér', 'Dugonics tér', 'Kelemen László utca']
    },
    'Romania': {
        'Bucharest': ['Calea Victoriei', 'Bulevardul Magheru', 'Lipscani', 'Bulevardul Unirii', 'Șoseaua Kiseleff'],
        'Cluj-Napoca': ['Bulevardul Eroilor', 'Strada Memorandumului', 'Piața Unirii', 'Strada Horea', 'Strada Napoca'],
        'Timisoara': ['Piața Victoriei', 'Strada Alba Iulia', 'Piața Unirii', 'Strada Mărășești', 'Bulevardul Revoluției']
    },
    'Bangladesh': {
        'Dhaka': ['Kazi Nazrul Islam Avenue', 'Mirpur Road', 'Elephant Road', 'Begum Rokeya Sarani', 'Satmasjid Road'],
        'Chittagong': ['CDA Avenue', 'Sheikh Mujib Road', 'Agrabad Access Road', 'Strand Road', 'Port Connecting Road'],
        'Khulna': ['Khan Jahan Ali Road', 'KDA Avenue', 'Sher-e-Bangla Road', 'Lower Jessore Road', 'Cemetery Road']
    },
    'Algeria': {
        'Algiers': ['Rue Didouche Mourad', 'Boulevard Che Guevara', 'Rue Larbi Ben M\'hidi', 'Boulevard Zighoud Youcef', 'Rue Hassiba Ben Bouali'],
        'Oran': ['Boulevard de la Soummam', 'Rue Larbi Ben M\'hidi', 'Boulevard Front de Mer', 'Rue Khemisti Mohamed', 'Avenue Loubet'],
        'Constantine': ['Boulevard de l\'Abime', 'Rue Didouche Mourad', 'Avenue Aouati Mostefa', 'Rue Kitouni Abdelmalek', 'Boulevard Zighoud Youcef']
    },
    'Tunisia': {
        'Tunis': ['Avenue Habib Bourguiba', 'Avenue de Paris', 'Avenue Mohamed V', 'Rue de Marseille', 'Avenue de la Liberté'],
        'Sfax': ['Avenue Hedi Chaker', 'Avenue Habib Thameur', 'Rue Patrice Lumumba', 'Avenue 14 Janvier', 'Route de Tunis'],
        'Sousse': ['Avenue Habib Bourguiba', 'Boulevard 14 Janvier', 'Route Touristique', 'Avenue Leopold Senghor', 'Rue de l\'Indépendance']
    },
    'Kenya': {
        'Nairobi': ['Kenyatta Avenue', 'Moi Avenue', 'Haile Selassie Avenue', 'Uhuru Highway', 'Kimathi Street'],
        'Mombasa': ['Moi Avenue', 'Nkrumah Road', 'Digo Road', 'Nyerere Avenue', 'Haile Selassie Road'],
        'Kisumu': ['Oginga Odinga Road', 'Jomo Kenyatta Highway', 'Obote Road', 'Kisumu-Kakamega Road', 'Ring Road']
    },
    'Ethiopia': {
        'Addis Ababa': ['Bole Road', 'Churchill Avenue', 'Menelik II Avenue', 'Haile Gebrselassie Road', 'Entoto Street'],
        'Dire Dawa': ['Keira Road', 'Taiwan Road', 'Chat Tera Road', 'Shell Road', 'Number One Road'],
        'Mekelle': ['Romanat Square', 'Quiha Road', 'Ayder Road', 'Hawelti Road', 'Castle Road']
    },
    'Ghana': {
        'Accra': ['Independence Avenue', 'Ring Road', 'Oxford Street', 'Liberation Road', 'Kojo Thompson Road'],
        'Kumasi': ['Harper Road', 'Prempeh II Road', 'Fuller Road', 'Lake Road', '24th February Road'],
        'Tamale': ['Bolgatanga Road', 'Salaga Road', 'Hospital Road', 'Education Ridge Road', 'Industrial Area Road']
    },
    'Tanzania': {
        'Dar es Salaam': ['Nyerere Road', 'Samora Avenue', 'Ali Hassan Mwinyi Road', 'Morogoro Road', 'Bagamoyo Road'],
        'Mwanza': ['Kenyatta Road', 'Nyerere Road', 'Makongoro Road', 'Balewa Road', 'Station Road'],
        'Arusha': ['Sokoine Road', 'Boma Road', 'Old Moshi Road', 'Goliondoi Road', 'Seth Benjamin Street']
    },
    'Uganda': {
        'Kampala': ['Kampala Road', 'Jinja Road', 'Bombo Road', 'Entebbe Road', 'Yusuf Lule Road'],
        'Entebbe': ['Portal Road', 'Kampala Road', 'Circular Road', 'Airport Road', 'Lugard Avenue'],
        'Jinja': ['Main Street', 'Nizam Road', 'Lubas Road', 'Clive Road', 'Gabula Road']
    },
    'Venezuela': {
        'Caracas': ['Avenida Bolívar', 'Avenida Urdaneta', 'Avenida Baralt', 'Avenida Sucre', 'Avenida Francisco de Miranda'],
        'Maracaibo': ['Avenida 5 de Julio', 'Avenida Bella Vista', 'Avenida El Milagro', 'Calle 72', 'Avenida La Limpia'],
        'Valencia': ['Avenida Bolívar Norte', 'Avenida Cedeño', 'Avenida Lara', 'Avenida Andrés Eloy Blanco', 'Calle 137']
    },
    'Ecuador': {
        'Quito': ['Avenida Amazonas', 'Avenida 10 de Agosto', 'Calle Guayaquil', 'Avenida 6 de Diciembre', 'Calle García Moreno'],
        'Guayaquil': ['Avenida 9 de Octubre', 'Malecón 2000', 'Avenida de las Américas', 'Calle Panamá', 'Avenida Quito'],
        'Cuenca': ['Calle Larga', 'Avenida Solano', 'Calle Gran Colombia', 'Calle Bolívar', 'Avenida Huayna Cápac']
    },
    'Bolivia': {
        'La Paz': ['Avenida 16 de Julio', 'Calle Comercio', 'Avenida Mariscal Santa Cruz', 'Calle Sagárnaga', 'Avenida Arce'],
        'Santa Cruz': ['Avenida Monseñor Rivero', 'Avenida Cañoto', 'Calle 24 de Septiembre', 'Avenida Irala', 'Avenida Cristo Redentor'],
        'Cochabamba': ['Avenida Ballivián', 'El Prado', 'Avenida Heroínas', 'Calle España', 'Avenida Ayacucho']
    },
    'Paraguay': {
        'Asunción': ['Calle Palma', 'Avenida Mariscal López', 'Calle Estrella', 'Avenida España', 'Calle Oliva'],
        'Ciudad del Este': ['Avenida Monseñor Rodríguez', 'Ruta Internacional', 'Avenida San Blas', 'Avenida Pioneros del Este', 'Calle Boquerón'],
        'Encarnación': ['Avenida Costanera', 'Calle Mariscal Estigarribia', 'Calle Juan León Mallorquín', 'Avenida Irrazábal', 'Calle Carlos Antonio López']
    },
    'Uruguay': {
        'Montevideo': ['Avenida 18 de Julio', 'Rambla', 'Bulevar Artigas', 'Avenida Italia', 'Calle Sarandí'],
        'Salto': ['Calle Uruguay', 'Avenida Barbieri', 'Calle Artigas', 'Avenida Blandengues', 'Costanera Norte'],
        'Ciudad de la Costa': ['Avenida Giannattasio', 'Rambla Costanera', 'Avenida Alvear', 'Calle Gestido', 'Avenida Pérez Butler']
    },
    'Philippines': {
        'Manila': ['Rizal Avenue', 'Taft Avenue', 'España Boulevard', 'Quezon Boulevard', 'Recto Avenue'],
        'Quezon City': ['Commonwealth Avenue', 'Quezon Avenue', 'EDSA', 'Aurora Boulevard', 'Katipunan Avenue'],
        'Cebu City': ['Osmeña Boulevard', 'Colon Street', 'Mango Avenue', 'Gorordo Avenue', 'Escario Street']
    },
    'Indonesia': {
        'Jakarta': ['Jalan Sudirman', 'Jalan Thamrin', 'Jalan Gatot Subroto', 'Jalan Rasuna Said', 'Jalan Gajah Mada'],
        'Surabaya': ['Jalan Tunjungan', 'Jalan Darmo', 'Jalan Pemuda', 'Jalan Basuki Rahmat', 'Jalan Panglima Sudirman'],
        'Bandung': ['Jalan Braga', 'Jalan Asia Afrika', 'Jalan Dago', 'Jalan Riau', 'Jalan Cihampelas']
    },
    'Malaysia': {
        'Kuala Lumpur': ['Jalan Bukit Bintang', 'Jalan Ampang', 'Jalan Sultan Ismail', 'Jalan Tun Razak', 'Jalan Pudu'],
        'George Town': ['Penang Road', 'Chulia Street', 'Beach Street', 'Light Street', 'Burmah Road'],
        'Johor Bahru': ['Jalan Wong Ah Fook', 'Jalan Tebrau', 'Jalan Skudai', 'Jalan Tun Abdul Razak', 'Jalan Stulang Laut']
    },
    'Singapore': {
        'Singapore': ['Orchard Road', 'Serangoon Road', 'Beach Road', 'Robinson Road', 'Eu Tong Sen Street']
    },
    'Pakistan': {
        'Karachi': ['Shahrah-e-Faisal', 'M.A. Jinnah Road', 'I.I. Chundrigar Road', 'Clifton Road', 'Tariq Road'],
        'Lahore': ['Mall Road', 'Ferozepur Road', 'Jail Road', 'Gulberg Main Boulevard', 'MM Alam Road'],
        'Islamabad': ['Jinnah Avenue', 'Constitution Avenue', 'Blue Area', 'Margalla Road', 'Kashmir Highway']
    },
    'Nigeria': {
        'Lagos': ['Broad Street', 'Marina Road', 'Adetokunbo Ademola Street', 'Awolowo Road', 'Allen Avenue'],
        'Abuja': ['Herbert Macaulay Way', 'Ahmadu Bello Way', 'Shehu Shagari Way', 'Independence Avenue', 'Constitution Avenue'],
        'Kano': ['Murtala Muhammed Way', 'Ibrahim Taiwo Road', 'Zoo Road', 'Zaria Road', 'Bompai Road']
    },
    'Morocco': {
        'Casablanca': ['Boulevard Mohammed V', 'Boulevard d\'Anfa', 'Boulevard Zerktouni', 'Avenue des FAR', 'Boulevard Hassan II'],
        'Rabat': ['Avenue Mohammed V', 'Avenue Hassan II', 'Avenue Allal Ben Abdallah', 'Avenue Fal Ould Oumeir', 'Avenue de France'],
        'Marrakech': ['Avenue Mohammed V', 'Avenue Hassan II', 'Boulevard Mohamed VI', 'Rue de la Liberté', 'Avenue Prince Moulay Rachid']
    },
    'Saudi Arabia': {
        'Riyadh': ['King Fahd Road', 'Olaya Street', 'Tahlia Street', 'King Abdullah Road', 'Makkah Al Mukarramah Road'],
        'Jeddah': ['Tahlia Street', 'King Abdulaziz Road', 'Prince Sultan Street', 'Madinah Road', 'Corniche Road'],
        'Mecca': ['Ibrahim Al Khalil Street', 'Ajyad Street', 'Al Masjid Al Haram Road', 'Aziziyah Main Road', 'Umm Al Qura Road']
    },
    'Israel': {
        'Tel Aviv': ['Dizengoff Street', 'Rothschild Boulevard', 'Allenby Street', 'Ibn Gabirol Street', 'King George Street'],
        'Jerusalem': ['Jaffa Road', 'King George Street', 'Ben Yehuda Street', 'Herzl Boulevard', 'Hebron Road'],
        'Haifa': ['Hanassi Avenue', 'Herzl Street', 'HaAtzmaut Road', 'Ben Gurion Boulevard', 'Moriah Avenue']
    },
    'Peru': {
        'Lima': ['Avenida Arequipa', 'Avenida Javier Prado', 'Avenida Larco', 'Jirón de la Unión', 'Avenida Tacna'],
        'Arequipa': ['Calle Mercaderes', 'Avenida Ejército', 'Calle Santa Catalina', 'Calle San Francisco', 'Avenida Cayma'],
        'Trujillo': ['Avenida España', 'Jirón Pizarro', 'Avenida Larco', 'Avenida Mansiche', 'Jirón Gamarra']
    }
}

def generate_ssn():
    return f'{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}'

def generate_credit_card():
    brands = ['Visa', 'MasterCard', 'American Express', 'Discover']
    brand = random.choice(brands)
    number = ''.join([str(random.randint(0, 9)) for _ in range(16)])
    expire_month = random.randint(1, 12)
    expire_year = random.randint(datetime.datetime.now().year, datetime.datetime.now().year + 5)
    cvv = random.randint(100, 999)
    return {'brand': brand, 'number': number, 'expire': f'{expire_year}/{expire_month:02d}', 'cvv': cvv}

def generate_offline_identity(logger, nat):
    logger.emit(f"<font color='#ef4444'>[!] API indisponible, génération locale...</font>")
    
    first_names = [
        "Jean", "Pierre", "Paul", "Marie", "Sophie", "Julie", "Thomas", "Nicolas", "Lucas", "Emma", "Lea", "Chloé", 
        "John", "David", "Michael", "Sarah", "Jessica", "Emily", "James", "Robert", "Jennifer", "Linda", "Elizabeth",
        "Hans", "Klaus", "Julia", "Anna", "Stefan", "Ursula", "Monika",
        "Antonio", "Jose", "Manuel", "Maria", "Carmen", "Ana", "Isabel",
        "Alessandro", "Giuseppe", "Marco", "Francesca", "Giulia", "Sofia",
        "Liam", "Noah", "Oliver", "Elijah", "William", "James", "Benjamin", "Lucas", "Henry", "Alexander"
    ]
    last_names = [
        "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy", "Moreau", 
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
        "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker",
        "Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano", "Colombo",
        "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves"
    ]
    
    # Mapping for detailed data
    country_map = {
        'FR': 'France', 'US': 'USA', 'DE': 'Germany', 'BE': 'Belgium', 'NO': 'Norway',
        'GB': 'United Kingdom', 'ES': 'Spain', 'IT': 'Italy', 'CA': 'Canada', 'AU': 'Australia',
        'BR': 'Brazil', 'CH': 'Switzerland', 'NL': 'Netherlands', 'TR': 'Turkey', 'PL': 'Poland',
        'PT': 'Portugal', 'RU': 'Russia', 'JP': 'Japan', 'CN': 'China', 'IN': 'India',
        'MX': 'Mexico', 'SE': 'Sweden', 'DK': 'Denmark', 'FI': 'Finland', 'IE': 'Ireland',
        'AT': 'Austria', 'GR': 'Greece', 'IR': 'Iran', 'NZ': 'New Zealand', 'RS': 'Serbia',
        'UA': 'Ukraine', 'KR': 'South Korea', 'TH': 'Thailand', 'VN': 'Vietnam',
        'AR': 'Argentina', 'CL': 'Chile', 'CO': 'Colombia', 'EG': 'Egypt', 'ZA': 'South Africa',
        'CZ': 'Czech Republic', 'HU': 'Hungary', 'RO': 'Romania', 'BD': 'Bangladesh',
        'DZ': 'Algeria', 'TN': 'Tunisia', 'KE': 'Kenya', 'ET': 'Ethiopia', 'GH': 'Ghana',
        'TZ': 'Tanzania', 'UG': 'Uganda', 'VE': 'Venezuela', 'EC': 'Ecuador', 'BO': 'Bolivia',
        'PY': 'Paraguay', 'UY': 'Uruguay', 'PH': 'Philippines',
        'ID': 'Indonesia', 'MY': 'Malaysia', 'SG': 'Singapore', 'PK': 'Pakistan',
        'NG': 'Nigeria', 'MA': 'Morocco', 'SA': 'Saudi Arabia', 'IL': 'Israel', 'PE': 'Peru'
    }
    full_country = country_map.get(nat.upper())
    
    gender = random.choice(["Homme", "Femme"])
    fname = random.choice(first_names)
    lname = random.choice(last_names)
    
    if full_country and full_country in city_zip_codes:
        city = random.choice(list(city_zip_codes[full_country].keys()))
        zip_code = random.choice(city_zip_codes[full_country][city])
        street_name = random.choice(city_streets[full_country].get(city, ['Main Street']))
        street = f"{random.randint(1, 999)} {street_name}"
        country_name = full_country
    else:
        # Fallback for other countries
        city, zip_code = ("Paris", "75000")
        street = f"{random.randint(1, 999)} Rue Principale"
        country_name = nat.upper()

    ssn = generate_ssn()
    cc = generate_credit_card()
    
    logger.emit(f"<font color='#22c55e'>[+] Identité Générée (Locale) :</font>")
    logger.emit(f"<font color='#e4e4e7'>    Nom: {fname} {lname}</font>")
    logger.emit(f"<font color='#e4e4e7'>    Sexe: {gender}</font>")
    logger.emit(f"<font color='#e4e4e7'>    Adresse: {street}, {zip_code} {city}</font>")
    logger.emit(f"<font color='#e4e4e7'>    Pays: {country_name}</font>")
    logger.emit(f"<font color='#e4e4e7'>    Email: {fname.lower()}.{lname.lower()}@example.com</font>")
    logger.emit(f"<font color='#e4e4e7'>    SSN: {ssn}</font>")
    logger.emit(f"<font color='#e4e4e7'>    Carte Crédit: {cc['brand']} - {cc['number']}</font>")
    logger.emit(f"<font color='#e4e4e7'>    Exp: {cc['expire']} | CVV: {cc['cvv']}</font>")

def logic_gen_identity(logger, nat):
    logger.emit(f"<font color='#3b82f6'><b>[*] Génération d'identité ({nat})...</b></font>")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
    
    for i in range(3):
        try:
            url = f"https://randomuser.me/api/?nat={nat.lower()}"
            res = requests.get(url, headers=headers, timeout=10, verify=False)
            if res.status_code == 200:
                json_data = res.json()
                if not json_data.get('results'):
                    if i < 2:
                        time.sleep(1)
                        continue
                    break
                data = json_data['results'][0]
                
                gender = data['gender']
                name = f"{data['name']['title']} {data['name']['first']} {data['name']['last']}"
                
                loc = data['location']
                street = f"{loc.get('street', {}).get('number', '')} {loc.get('street', {}).get('name', '')}"
                city = loc['city']
                state = loc['state']
                country = loc['country']
                postcode = str(loc['postcode'])
                
                email = data['email']
                login = data['login']
                dob = data['dob']
                phone = data['phone']
                cell = data['cell']
                
                id_info = data.get('id', {})
                id_val = f"{id_info.get('name') or 'N/A'} - {id_info.get('value') or 'N/A'}"
                pic = data['picture']['large']

                ssn = generate_ssn()
                cc = generate_credit_card()
                
                logger.emit(f"<font color='#22c55e'>[+] Identité Générée :</font>")
                logger.emit(f"<font color='#e4e4e7'>    Nom: {name}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Sexe: {gender}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Né(e) le: {dob['date'][:10]} ({dob['age']} ans)</font>")
                logger.emit(f"<font color='#e4e4e7'>    Adresse: {street}, {postcode} {city}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Région: {state}, {country}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Email: {email}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Utilisateur: {login['username']}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Mot de passe: {login['password']}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Téléphone: {phone}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Mobile: {cell}</font>")
                logger.emit(f"<font color='#e4e4e7'>    ID National: {id_val}</font>")
                logger.emit(f"<font color='#e4e4e7'>    SSN (Généré): {ssn}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Carte Crédit (Généré): {cc['brand']} - {cc['number']}</font>")
                logger.emit(f"<font color='#e4e4e7'>    Exp: {cc['expire']} | CVV: {cc['cvv']}</font>")
                logger.emit(f"<font color='#3b82f6'>    Photo: <a href='{pic}'>Voir l'image</a></font>")
                return
            else:
                if i < 2:
                    time.sleep(1)
                    continue
                break
        except Exception as e:
            if i < 2:
                time.sleep(1)
                continue
            break
    
    generate_offline_identity(logger, nat)

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

class FakeAddressToolWindow(QMainWindow):
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
        
        title_label = QLabel("LE M // Fake Adresse ")
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

        self.menu_label = QLabel("Fake Address - LE M")
        self.menu_label.setObjectName("MenuLabel")
        self.menu_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.menu_label)

        # Inputs
        lbl_nat = QLabel("Nationalité :")
        lbl_nat.setStyleSheet("color: #a1a1aa; font-weight: bold; font-size: 13px;")
        left_layout.addWidget(lbl_nat)

        self.combo_nat = QComboBox()
        self.combo_nat.addItems(["FR", "US", "DE", "GB", "ES", "IT", "CA", "AU", "BR", "CH", "DK", "FI", "IE", "IN", "IR", "MX", "NL", "NO", "NZ", "RS", "TR", "UA", "BE", "PL", "PT", "RU", "JP", "CN", "AT", "GR", "SE", "KR", "TH", "VN", "AR", "CL", "CO", "EG", "ZA", "CZ", "HU", "RO", "BD", "DZ", "TN", "KE", "ET", "GH", "TZ", "UG", "VE", "EC", "BO", "PY", "UY", "PH", "ID", "MY", "SG", "PK", "NG", "MA", "SA", "IL", "PE"])
        left_layout.addWidget(self.combo_nat)

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
        
        self.btn_gen = QPushButton("🎲  Générer Identité")
        
        for btn in [self.btn_gen]:
            btn.setObjectName("ActionBtn")
            btn.setCursor(Qt.PointingHandCursor)
            layout_main.addWidget(btn)
        layout_main.addStretch()
            
        self.stacked_widget.addWidget(page_main)
        
        # Actions
        self.btn_gen.clicked.connect(lambda: self.start_task(logic_gen_identity, self.combo_nat.currentText()))

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
            QComboBox { background-color: #27272a; border: 1px solid #27272a; border-radius: 8px; padding: 12px; color: #f4f4f5; font-family: 'Consolas', monospace; font-size: 14px; }
            QComboBox::drop-down { border: none; background: transparent; }
            QComboBox::down-arrow { image: none; border: none; }
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
    window = FakeAddressToolWindow()
    window.show()
    sys.exit(app.exec_())