import time
import sys
import shutil
import os
import hashlib
import subprocess
import msvcrt
import random
import math

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, os.path.join(BASE_DIR, 'program'))

def rgb_escape(r, g, b):
    return f'\x1b[38;2;{r};{g};{b}m'

def reset_color():
    return '\x1b[0m'

def blend_color(c1, c2, t):
    return (int(c1[0] + (c2[0] - c1[0]) * t), int(c1[1] + (c2[1] - c1[1]) * t), int(c1[2] + (c2[2] - c1[2]) * t))

def adjust_brightness(color, factor):
    return tuple(max(0, min(255, int(c * factor))) for c in color)

def glitch_text(line, intensity):
    chars = '@#$%&*+=-?/\\|<>[]{}01'
    return ''.join(random.choice(chars) if c!=' ' and random.random() < intensity else c for c in line)

def ascii_glitch_intro(ascii_lines, duration=5.0):
    term_cols, term_rows = shutil.get_terminal_size(fallback=(120, 40))
    max_ascii_w = max(len(line) for line in ascii_lines) if ascii_lines else 0
    margin_left = max(0, (term_cols - max_ascii_w) // 2)
    padding_top = max(0, (term_rows - len(ascii_lines)) // 2 - 2)
    steps = 40
    delay = duration / steps
    for i in range(steps):
        t = i / (steps - 1)
        intensity = 1.0 - t
        r, g, b = blend_color((138, 43, 226), (0, 120, 255), t)
        buffer = '\x1b[H' + '\n' * padding_top
        for line in ascii_lines:
            offset = ' ' * random.randint(0, int(6 * intensity))
            buffer += f"{' ' * margin_left}{offset}\x1b[38;2;{r};{g};{b}m{glitch_text(line, intensity)}\x1b[0m\x1b[K\n"
        sys.stdout.write(buffer)
        sys.stdout.flush()
        time.sleep(delay)
    os.system('cls' if os.name == 'nt' else 'clear')

def animate_color_cycle(c1, c2, steps=60):
    step, direct = 0, 1
    while True:
        yield blend_color(c1, c2, step / (steps - 1))
        step += direct
        if step >= steps - 1 or step <= 0: direct *= -1

def animate_float_cycle(a, b, steps=60):
    step, direct = 0, 1
    while True:
        yield (a + (b - a) * (step / (steps - 1)))
        step += direct
        if step >= steps - 1 or step <= 0: direct *= -1

def animate_box_edges(box_w, box_h, visible_frac=0.25):
    perim = 2 * (box_w - 2) + 2 * box_h
    v_len = max(1, int(perim * visible_frac))
    step = 0
    while True:
        mask = [False] * perim
        for i in range(v_len): mask[(step + i) % perim] = True
        yield mask
        step = (step + 1) % perim

def build_boxes(categories, box_width, box_height):
    boxes = []
    inner_w = max(2, box_width - 2)
    for title, items in categories:
        lines = [title.center(inner_w), '─' * inner_w]
        for it in items: lines.append(it.ljust(inner_w))
        while len(lines) < box_height: lines.append(' ' * inner_w)
        boxes.append(lines)
    return boxes

def _style_tool_line(text, base_rgb, is_selected, box_inner_w, pulse):
    clean = text.strip()
    if not clean: return ' ' * box_inner_w
    
    # Selection Effects
    effective_rgb = base_rgb
    offset_mar = ''
    if is_selected:
        # Brightness Pulse
        effective_rgb = adjust_brightness(base_rgb, 1.0 + 0.5 * pulse)
        # Static Horizontal Offset ("décalé")
        offset_mar = ' ' # Fixed 1-space shift for selected items
        
        cursor_rgb = (0, 255, 255) # Cyan
        cursor_rgb = adjust_brightness(cursor_rgb, 1.0 + 0.5 * pulse)
        cursor = f'{rgb_escape(*cursor_rgb)}▶{reset_color()}'
    else:
        cursor = ' '
    
    color_esc = rgb_escape(*effective_rgb)
    
    if '[' in clean and ']' in clean:
        start, end = clean.find('['), clean.find(']')
        num, name = clean[start:end+1], clean[end+1:]
        # Shifted line: [offset] [cursor] [colored line]
        res = f' {offset_mar}{cursor} {color_esc}{num} {name.strip()}{reset_color()}'
        v_len = 1 + len(offset_mar) + 1 + 1 + len(num) + 1 + len(name.strip())
        return res + ' ' * max(0, box_inner_w - v_len)
        
    res = f' {offset_mar}{cursor} {color_esc}{clean}{reset_color()}'
    v_len = 1 + len(offset_mar) + 1 + 1 + len(clean)
    return res + ' ' * max(0, box_inner_w - v_len)

def render_frame(ascii_lines, boxes, color_escape, mask, bw, bh, box_colors, sel_box, tick, pulse, sel_item):
    cols, rows = shutil.get_terminal_size()
    max_a_w = max(len(l) for l in ascii_lines) if ascii_lines else 1
    a_mar = max(0, (cols - max_a_w) // 2)
    content_h = len(ascii_lines) + 2 + bh + 2 + 1
    top_m = max(0, (rows - content_h) // 2)
    
    out = ['\x1b[H']
    for _ in range(top_m): out.append('\x1b[K')
    
    # ASCII
    a_o = int((math.sin(tick * 0.05) + 1.0) * 1)
    for l in ascii_lines:
        out.append(f"{color_escape}{' ' * (a_mar + a_o)}{l}{reset_color()}\x1b[K")
    out.append('\x1b[K')
    
    pad = 1
    total_w = len(boxes) * bw + (len(boxes)-1) * pad
    left_m = max(0, (cols - total_w) // 2)
    perim = 2 * (bw - 2) + 2 * bh
    
    for y in range(bh + 2):
        row = []
        for i, box in enumerate(boxes):
            c = box_colors[i] if i < len(box_colors) else (255,255,255)
            # Pulse the box border if it's the selected one
            if i == sel_box: c = adjust_brightness(c, 1.1 + 0.3 * pulse)
            esc = rgb_escape(*c)
            
            if y == 0: # TOP
                seg = ''.join('─' if mask[x] else ' ' for x in range(bw-2))
                row.append(f"{esc}╭{seg}╮{reset_color()}")
            elif y == bh + 1: # BOTTOM
                start_idx = (bw - 2) + bh
                seg = ''
                for x in range(bw - 2):
                    idx = (start_idx + (bw - 3 - x)) % perim
                    seg += '─' if mask[idx] else ' '
                row.append(f"{esc}╰{seg}╯{reset_color()}")
            else: # SIDES
                l_idx = (perim - (y - 1)) % perim
                r_idx = ((bw - 2) + (y - 1) - 1) % perim
                l_p = '│' if mask[l_idx] else ' '
                r_p = '│' if mask[r_idx] else ' '
                
                content = box[y - 1]
                if y - 1 == 0: # Title
                    styled = content.center(bw - 2)
                    row.append(f"{esc}{l_p}{styled}{r_p}{reset_color()}")
                elif y - 1 == 1: # Separator
                    row.append(f"{esc}{l_p}{content}{r_p}{reset_color()}")
                else: # Items
                    is_this_sel = (i == sel_box and (y - 3) == sel_item)
                    # Pass pulse to tool line styling (tick removed as shake is gone)
                    styled = _style_tool_line(content, c, is_this_sel, bw - 2, pulse)
                    row.append(f"{esc}{l_p}{styled}{reset_color()}{esc}{r_p}{reset_color()}")
                    
        out.append(' ' * left_m + (' ' * pad).join(row) + '\x1b[K')
    
    return '\n'.join(out)

def main():
    ascii_art = """
.       ✦       .         *        .
     *           .         ·      .         .
     .     ✦      .         *     .
                *     .       .

        ██▓    ▓█████     ███▄ ▄███▓
       ▓██▒    ▓█   ▀    ▓██▒▀█▀ ██▒
       ▒██░    ▒███      ▓██    ▓██░
       ▒██░    ▒▓█  ▄    ▒██    ▒██ 
       ░██████▒░▒████▒   ▒██▒   ░██▒
       ░ ▒░▓  ░░░ ▒░ ░   ░ ▒░   ░  ░
       ░ ░ ▒  ░ ░ ░  ░   ░  ░      ░
         ░ ░      ░      ░      ░   
           ░  ░   ░  ░          ░   
"""
    a_lines = ascii_art.strip('\n').splitlines()
    ascii_glitch_intro(a_lines, duration=3.0)
    
    categories = [
        ('Scam', ['[08] Id Card Fraud', '[09] CC Validator', '[10] Fake Adresse', '[11] Spoofer', '[12] Iban Generator', '[13] Fake Paypal Screen', '[14] Fake Voice']),
        ('Osint', ['[15] Dox Tool', '[16] Osint Tool']),
        ('Discord Tools', ['[20] Token Tool', '[21] Bot Tool', '[22] Webhook Tool', '[23] Serveur Tool', '[24] Self Bot Tool']),
        ('Network Scanner', ['[25] Ip Tool', '[26] Website Tool', '[27] Sql Tool']),
    ]
    
    mapping = {
        '[08] Id Card Fraud': 'Scam/Id Card Fraud/Main.py', '[09] CC Validator': 'Scam/CC Validator/Main.py', '[10] Fake Adresse': 'Scam/Fake Adresse/Main.py', '[11] Spoofer': 'Scam/Spoofer/Main.py',
        '[12] Iban Generator': 'Scam/Iban Generator/Main.py', '[13] Fake Paypal Screen': 'Scam/Fake Paypal Screen/Main.py', '[14] Fake Voice': 'Scam/Fake Voice/Main.py',
        '[15] Dox Tool': 'Osint/Dox Tool/Main.py', '[16] Osint Tool': 'Osint/Osint Tool/Main.py',
        '[20] Token Tool': 'Discord Tools/Token Tool/Main.py', '[21] Bot Tool': 'Discord Tools/Bot Tool/Main.py', '[22] Webhook Tool': 'Discord Tools/Webhook Tool/Main.py', '[23] Serveur Tool': 'Discord Tools/Serveur Tool/Main.py', '[24] Self Bot Tool': 'Discord Tools/Self Bot Tool/Main.py',
        '[25] Ip Tool': 'Network Scanner/Ip Tool/Main.py', '[26] Website Tool': 'Network Scanner/Website Tool/Main.py',
        '[27] Sql Tool': 'Network Scanner/Sql Tool/Main.py'
    }

    category_colors = [
        (255, 69, 0), (255, 20, 147), (30, 144, 255), (0, 255, 255),
        (88, 101, 242), (0, 255, 127), (255, 215, 0), (255, 0, 0)
    ]

    PAGE_SIZE = 4
    sel_box, sel_item = 0, 0
    tick = 0
    
    col_cycle = animate_color_cycle((135, 206, 250), (138, 43, 226), 60)
    br_cycle = animate_float_cycle(0.5, 1.2, 60)
    
    PYTHON = 'C:\\Users\\{}\\AppData\\Local\\Programs\\Python\\Python311\\python.exe'.format(os.getlogin())
    sys.stdout.write('\x1b[?25l')
    
    last_size = (0,0)
    e_gen = None
    
    try:
        while True:
            size = shutil.get_terminal_size()
            if size != last_size:
                os.system('cls' if os.name == 'nt' else 'clear')
                last_size = size
                e_gen = animate_box_edges((size.columns - 6) // min(PAGE_SIZE, len(categories)), max(len(c[1]) + 2 for c in categories), 0.25)
                
            p = sel_box // PAGE_SIZE
            p_start, p_end = p * PAGE_SIZE, min((p + 1) * PAGE_SIZE, len(categories))
            v_cats = categories[p_start:p_end]
            
            box_w = (size.columns - 6) // min(PAGE_SIZE, len(categories))
            box_h = max(len(c[1]) + 2 for c in categories)
            boxes = build_boxes(v_cats, box_w, box_h)
            
            if not e_gen:
                e_gen = animate_box_edges(box_w, box_h, 0.25)
            
            mask = next(e_gen)
            
            r, g, b = next(col_cycle)
            br = next(br_cycle)
            pulse_val = (br - 0.5) / 0.7 # 0.0 to 1.0 roughly
            
            b_cols = [adjust_brightness(category_colors[i], 1.7 - br) for i in range(p_start, p_end)]
            
            frame = render_frame(a_lines, boxes, rgb_escape(r, g, b), mask, box_w, box_h, b_cols, sel_box % PAGE_SIZE, tick, pulse_val, sel_item)
            footer = f"\x1b[K\n{rgb_escape(100, 100, 100)}{f' Page {p + 1}/{(len(categories) + PAGE_SIZE - 1) // PAGE_SIZE} '.center(size.columns)}{reset_color()}\x1b[J"
            
            sys.stdout.write(frame + footer)
            sys.stdout.flush()
            
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key in (b'\x00', b'\xe0'):
                    k2 = msvcrt.getch()
                    if k2 == b'H': sel_item -= 1
                    elif k2 == b'P': sel_item += 1
                    elif k2 == b'K': sel_box = (sel_box - 1) % len(categories)
                    elif k2 == b'M': sel_box = (sel_box + 1) % len(categories)
                elif key == b'\r':
                    chosen = v_cats[sel_box % PAGE_SIZE][1][sel_item]
                    rel_p = mapping.get(chosen)
                    if rel_p:
                        exe = os.path.join(BASE_DIR, 'program', rel_p)
                        if os.path.exists(exe):

                            sys.stdout.write('\x1b[2J\x1b[H' + reset_color() + '\x1b[?25h')
                            print(f"Executing {chosen}...")
                            try:
                                if exe.endswith('.py'):
                                    if chosen in ['[08] Id Card Fraud', '[09] CC Validator', '[10] Fake Adresse', '[11] Spoofer', '[12] Iban Generator', '[13] Fake Paypal Screen', '[14] Fake Voice', '[15] Dox Tool', '[16] Osint Tool', '[20] Token Tool', '[21] Bot Tool', '[22] Webhook Tool', '[23] Serveur Tool', '[24] Self Bot Tool', '[25] Ip Tool', '[26] Website Tool', '[27] Sql Tool']:
                                        py_exe = PYTHON.replace('python.exe', 'pythonw.exe') if 'python.exe' in PYTHON else 'pythonw'
                                        cmd = [py_exe, exe]
                                        subprocess.Popen(cmd, cwd=BASE_DIR)
                                    else:
                                        cmd = [PYTHON, '-u', exe] if os.path.exists(PYTHON) else ['py', '-3.11', '-u', exe]
                                        subprocess.Popen(cmd, cwd=BASE_DIR, creationflags=subprocess.CREATE_NEW_CONSOLE)
                                else:
                                    subprocess.run([exe], cwd=os.path.dirname(exe), check=True)
                            except Exception as e: print(f"Error: {e}"); time.sleep(2)
                            sys.stdout.write('\x1b[2J\x1b[H\x1b[?25l')
                    continue
                else:
                    try: c = key.decode('ascii').lower()
                    except: c = ''
                    if c in 'wk': sel_item -= 1
                    elif c in 'sj': sel_item += 1
                    elif c in 'ah': sel_box = (sel_box - 1) % len(categories)
                    elif c in 'dl': sel_box = (sel_box + 1) % len(categories)

            max_i = len(categories[sel_box][1])
            if sel_item < 0: sel_item = max_i - 1
            if sel_item >= max_i: sel_item = 0
            
            tick += 1
            time.sleep(0.04)
    except KeyboardInterrupt:
        sys.stdout.write(reset_color() + '\x1b[?25h\n')

if __name__ == '__main__':
    main()
