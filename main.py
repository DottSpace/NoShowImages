import os
os.environ["SDL_ENABLE_SCREEN_KEYBOARD"] = "0"

import pygame
import random
import sys

pygame.init()
pygame.font.init()

try:
    pygame.key.stop_text_input()
except AttributeError:
    pass

# --- CONFIGURAZIONE SCHERMO FULLSCREEN RETRÒ ---
info_object = pygame.display.Info()
WIDTH = info_object.current_w if info_object.current_w > 0 else 400
HEIGHT = info_object.current_h if info_object.current_h > 0 else 800

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN if info_object.current_w > 0 else 0)
pygame.display.set_caption("Snake 3310")
clock = pygame.time.Clock()

# --- COLORI NOKIA 3310 ---
COLOR_LCD_BG = (155, 175, 130)       # Verde chiaro LCD
COLOR_PIXEL_DARK = (20, 30, 15)      # Nero/Verde scuro pixel
COLOR_GRID_LINE = (140, 160, 115)     # Griglia sottile
COLOR_BTN_BG = (130, 150, 105)        # Pulsanti

# --- FONT PROPORZIONATI ---
FONT_XLARGE = pygame.font.SysFont("monospace", int(WIDTH * 0.080), bold=True)
FONT_LARGE  = pygame.font.SysFont("monospace", int(WIDTH * 0.048), bold=True)
FONT_MED    = pygame.font.SysFont("monospace", int(WIDTH * 0.034), bold=True)
FONT_SMALL  = pygame.font.SysFont("monospace", int(WIDTH * 0.025), bold=True)

# --- D-PAD TASTIERINO SIMMETRICO (Griglia 3x3) ---
PAD_AREA_TOP = int(HEIGHT * 0.58)
PAD_CENTER_X = WIDTH // 2
PAD_CENTER_Y = PAD_AREA_TOP + (HEIGHT - PAD_AREA_TOP) // 2

BTN_SIZE = int(WIDTH * 0.22)
GAP = int(WIDTH * 0.035)
DIST = BTN_SIZE + GAP

btn_up    = pygame.Rect(PAD_CENTER_X - BTN_SIZE//2, PAD_CENTER_Y - DIST - BTN_SIZE//2, BTN_SIZE, BTN_SIZE)
btn_down  = pygame.Rect(PAD_CENTER_X - BTN_SIZE//2, PAD_CENTER_Y + DIST - BTN_SIZE//2, BTN_SIZE, BTN_SIZE)
btn_left  = pygame.Rect(PAD_CENTER_X - DIST - BTN_SIZE//2, PAD_CENTER_Y - BTN_SIZE//2, BTN_SIZE, BTN_SIZE)
btn_right = pygame.Rect(PAD_CENTER_X + DIST - BTN_SIZE//2, PAD_CENTER_Y - BTN_SIZE//2, BTN_SIZE, BTN_SIZE)

# Tasto Indietro In-Game
btn_in_game_back = pygame.Rect(WIDTH - 65, 10, 50, 38)


def draw_vector_arrow(surface, rect, direction, color):
    cx, cy = rect.centerx, rect.centery
    s = rect.width * 0.25
    if direction == "UP":
        points = [(cx, cy - s), (cx - s, cy + s), (cx + s, cy + s)]
    elif direction == "DOWN":
        points = [(cx, cy + s), (cx - s, cy - s), (cx + s, cy - s)]
    elif direction == "LEFT":
        points = [(cx - s, cy), (cx + s, cy - s), (cx + s, cy + s)]
    elif direction == "RIGHT":
        points = [(cx + s, cy), (cx - s, cy - s), (cx - s, cy + s)]
    pygame.draw.polygon(surface, color, points)


class SnakeGame:
    def __init__(self):
        self.state = "MAIN_MENU" 
        self.mode = "CLASSIC_OLD" 
        
        self.cheat_little_grid = False
        self.cheat_godmode = False
        
        self.secret_click_count = 0
        self.code_input = ""
        self.setup_onscreen_keyboard()
        self.reset_game()

    def setup_onscreen_keyboard(self):
        # Configurazione tastiera estilo smartphone/PC con barra spaziatrice grande
        rows = [
            [('Q',1),('W',1),('E',1),('R',1),('T',1),('Y',1),('U',1),('I',1),('O',1),('P',1)],
            [('A',1),('S',1),('D',1),('F',1),('G',1),('H',1),('J',1),('K',1),('L',1)],
            [('Z',1),('X',1),('C',1),('V',1),('B',1),('N',1),('M',1)],
            [('DEL',2.2), ('SPACE',5.2), ('ENT',2.2)]
        ]
        self.keyboard_buttons = []
        start_y = int(HEIGHT * 0.26)
        
        margin_x = 10
        available_w = WIDTH - (margin_x * 2)
        gap = 3
        unit_w = (available_w - (9 * gap)) / 10.0
        kh = int(HEIGHT * 0.052)
        
        for row in rows:
            total_units = sum(u for _, u in row)
            num_gaps = len(row) - 1
            row_px_w = (total_units * unit_w) + (num_gaps * gap)
            
            curr_x = (WIDTH - row_px_w) / 2.0
            
            for char, u in row:
                w = u * unit_w
                rect = pygame.Rect(int(curr_x), start_y, int(w), kh)
                self.keyboard_buttons.append((rect, char))
                curr_x += w + gap
            start_y += kh + 5

    def reset_game(self):
        if self.cheat_little_grid:
            self.cols, self.rows = 8, 8
        else:
            self.cols, self.rows = 20, 20

        header_h = int(HEIGHT * 0.18)
        play_area_h = int(HEIGHT * 0.38)
        self.cell_size = min((WIDTH - 24) // self.cols, play_area_h // self.rows)
        
        self.grid_w = self.cell_size * self.cols
        self.grid_h = self.cell_size * self.rows
        self.grid_x = (WIDTH - self.grid_w) // 2
        self.grid_y = header_h

        self.total_cells = self.cols * self.rows
        self.snake = [(self.cols//2, self.rows//2), (self.cols//2 - 1, self.rows//2), (self.cols//2 - 2, self.rows//2)]
        self.direction = (1, 0)
        self.input_buffer = []
        self.apples = []
        self.score = 0
        
        if self.mode == "EASY":
            self.base_fps = 6
        elif self.mode == "HARD":
            self.base_fps = 9
        elif self.mode == "SECRET":
            self.base_fps = 12
        else:
            self.base_fps = 8

        self.current_fps = self.base_fps
        self.spawn_apples()

    def spawn_apples(self):
        target_count = 1 if self.mode in ["CLASSIC_OLD", "EASY"] else 3
        while len(self.apples) < target_count:
            empty = [(x, y) for x in range(self.cols) for y in range(self.rows)
                     if (x, y) not in self.snake and (x, y) not in self.apples]
            if not empty:
                break
            self.apples.append(random.choice(empty))

    def handle_input(self, new_dir):
        last_dir = self.input_buffer[-1] if self.input_buffer else self.direction
        if (new_dir[0] != -last_dir[0] or new_dir[1] != -last_dir[1]):
            if len(self.input_buffer) < 2:
                self.input_buffer.append(new_dir)

    def update(self):
        if self.state != "PLAYING":
            return

        if self.input_buffer:
            self.direction = self.input_buffer.pop(0)

        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_x, new_y = head_x + dx, head_y + dy

        if self.mode in ["CLASSIC_OLD", "SECRET"] or self.cheat_godmode:
            new_x %= self.cols
            new_y %= self.rows
        else:
            if new_x < 0 or new_x >= self.cols or new_y < 0 or new_y >= self.rows:
                self.state = "GAMEOVER"
                return

        new_head = (new_x, new_y)

        if new_head in self.snake and not self.cheat_godmode:
            self.state = "GAMEOVER"
            return

        self.snake.insert(0, new_head)

        if new_head in self.apples:
            self.apples.remove(new_head)
            self.score += 1
            if len(self.snake) == self.total_cells:
                self.state = "WIN"
                return
            if self.mode == "HARD":
                self.current_fps = min(20, self.base_fps + (self.score * 0.4))
            self.spawn_apples()
        else:
            self.snake.pop()

    def draw(self):
        screen.fill(COLOR_LCD_BG)

        if self.state == "MAIN_MENU":
            self.draw_main_menu()
        elif self.state == "MODE_MENU":
            self.draw_mode_menu()
        elif self.state == "CODE_MENU":
            self.draw_code_menu()
        else:
            self.draw_gameplay()

        pygame.display.flip()

    def draw_main_menu(self):
        title = FONT_XLARGE.render("SNAKE", True, COLOR_PIXEL_DARK)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, int(HEIGHT * 0.10)))

        p_size = int(WIDTH * 0.055)
        start_x = WIDTH // 2 - int(p_size * 3)
        start_y = int(HEIGHT * 0.24)
        
        snake_pixel_art = [
            (0,0), (1,0), (2,0), (3,0), (4,0),
            (4,1),
            (4,2), (3,2), (2,2), (1,2), (0,2),
            (0,3),
            (0,4), (1,4), (2,4), (3,4), (4,4), (5,4)
        ]
        for px, py in snake_pixel_art:
            pygame.draw.rect(screen, COLOR_PIXEL_DARK, 
                             (start_x + px*p_size, start_y + py*p_size, p_size-2, p_size-2))

        btn_w, btn_h = int(WIDTH * 0.65), int(HEIGHT * 0.08)
        btn_play = pygame.Rect((WIDTH - btn_w)//2, int(HEIGHT * 0.58), btn_w, btn_h)
        self.main_play_btn = btn_play
        pygame.draw.rect(screen, COLOR_PIXEL_DARK, btn_play)
        txt_play = FONT_LARGE.render("[ GIOCA ]", True, COLOR_LCD_BG)
        screen.blit(txt_play, (btn_play.centerx - txt_play.get_width()//2, btn_play.centery - txt_play.get_height()//2))

    def draw_mode_menu(self):
        # Titolo posizionato con ottimo margine dal bordo superiore
        title = FONT_LARGE.render("MODALITÀ", True, COLOR_PIXEL_DARK)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, int(HEIGHT * 0.035)))

        modes = [
            ("FACILE", "EASY", "Lento | Muri | 1 Mela"),
            ("CLASSIC OLD", "CLASSIC_OLD", "Pacman | 1 Mela"),
            ("CLASSIC NEW", "CLASSIC_NEW", "Muri Solidi | 3 Mele"),
            ("DIFFICILE", "HARD", "Muri | Speed Up"),
            ("SECRET", "SECRET", "???")
        ]

        self.mode_buttons = []
        start_y = int(HEIGHT * 0.10)  # Inizio distanziato dal titolo
        btn_w = int(WIDTH * 0.88)
        btn_h = int(HEIGHT * 0.072)

        for name, key, desc in modes:
            rect = pygame.Rect((WIDTH - btn_w)//2, start_y, btn_w, btn_h)
            self.mode_buttons.append((rect, key))
            
            is_selected = (self.mode == key)
            bg_col = COLOR_PIXEL_DARK if is_selected else COLOR_BTN_BG
            txt_col = COLOR_LCD_BG if is_selected else COLOR_PIXEL_DARK
            
            pygame.draw.rect(screen, bg_col, rect)
            pygame.draw.rect(screen, COLOR_PIXEL_DARK, rect, 2)

            txt_name = FONT_MED.render(name, True, txt_col)
            txt_desc = FONT_SMALL.render(desc, True, txt_col)
            
            screen.blit(txt_name, (rect.x + 12, rect.y + int(rect.height * 0.12)))
            screen.blit(txt_desc, (rect.x + 12, rect.y + int(rect.height * 0.55)))
            start_y += btn_h + 6

        # Pulsante AVVIA
        start_btn = pygame.Rect((WIDTH - btn_w)//2, start_y + 4, btn_w, int(btn_h * 1.1))
        self.start_play_btn = start_btn
        pygame.draw.rect(screen, COLOR_PIXEL_DARK, start_btn)
        txt_start = FONT_LARGE.render("[ AVVIA ]", True, COLOR_LCD_BG)
        screen.blit(txt_start, (start_btn.centerx - txt_start.get_width()//2, start_btn.centery - txt_start.get_height()//2))

        # Tasto INDIETRO in Basso
        self.btn_mode_back = pygame.Rect((WIDTH - btn_w)//2, HEIGHT - 55, btn_w, 42)
        pygame.draw.rect(screen, COLOR_BTN_BG, self.btn_mode_back)
        pygame.draw.rect(screen, COLOR_PIXEL_DARK, self.btn_mode_back, 2)
        txt_b = FONT_MED.render("< INDIETRO", True, COLOR_PIXEL_DARK)
        screen.blit(txt_b, (self.btn_mode_back.centerx - txt_b.get_width()//2, self.btn_mode_back.centery - txt_b.get_height()//2))

    def draw_code_menu(self):
        title = FONT_LARGE.render("CODE MENU", True, COLOR_PIXEL_DARK)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, int(HEIGHT * 0.03)))

        box_input = pygame.Rect(15, int(HEIGHT * 0.09), WIDTH - 30, int(HEIGHT * 0.06))
        pygame.draw.rect(screen, COLOR_LCD_BG, box_input)
        pygame.draw.rect(screen, COLOR_PIXEL_DARK, box_input, 2)
        txt_inp = FONT_MED.render(f"> {self.code_input}_", True, COLOR_PIXEL_DARK)
        screen.blit(txt_inp, (box_input.x + 10, box_input.centery - txt_inp.get_height()//2))

        st_lg = "ATTIVO" if self.cheat_little_grid else "OFF"
        st_gm = "ATTIVO" if self.cheat_godmode else "OFF"
        
        t_lg = FONT_SMALL.render(f"LITTLE GRID: {st_lg}", True, COLOR_PIXEL_DARK)
        t_gm = FONT_SMALL.render(f"GODMODE: {st_gm}", True, COLOR_PIXEL_DARK)
        screen.blit(t_lg, (20, int(HEIGHT * 0.165)))
        screen.blit(t_gm, (20, int(HEIGHT * 0.205)))

        for rect, char in self.keyboard_buttons:
            pygame.draw.rect(screen, COLOR_BTN_BG, rect)
            pygame.draw.rect(screen, COLOR_PIXEL_DARK, rect, 1)
            txt_c = FONT_SMALL.render(char, True, COLOR_PIXEL_DARK)
            screen.blit(txt_c, (rect.centerx - txt_c.get_width()//2, rect.centery - txt_c.get_height()//2))

        btn_w = WIDTH - 40
        btn_h = int(HEIGHT * 0.065)

        self.btn_submit_code = pygame.Rect(20, int(HEIGHT * 0.52), btn_w, btn_h)
        pygame.draw.rect(screen, COLOR_PIXEL_DARK, self.btn_submit_code)
        txt_sub = FONT_MED.render("[ APPLICA CODICE ]", True, COLOR_LCD_BG)
        screen.blit(txt_sub, (self.btn_submit_code.centerx - txt_sub.get_width()//2, self.btn_submit_code.centery - txt_sub.get_height()//2))

        self.btn_code_back = pygame.Rect(20, int(HEIGHT * 0.60), btn_w, btn_h)
        pygame.draw.rect(screen, COLOR_BTN_BG, self.btn_code_back)
        pygame.draw.rect(screen, COLOR_PIXEL_DARK, self.btn_code_back, 2)
        txt_back = FONT_MED.render("< INDIETRO", True, COLOR_PIXEL_DARK)
        screen.blit(txt_back, (self.btn_code_back.centerx - txt_back.get_width()//2, self.btn_code_back.centery - txt_back.get_height()//2))

    def draw_gameplay(self):
        pygame.draw.rect(screen, COLOR_BTN_BG, btn_in_game_back)
        pygame.draw.rect(screen, COLOR_PIXEL_DARK, btn_in_game_back, 2)
        draw_vector_arrow(screen, btn_in_game_back, "LEFT", COLOR_PIXEL_DARK)

        curr_y = 10
        
        txt_score = FONT_MED.render(f"SCORE: {self.score:04d}", True, COLOR_PIXEL_DARK)
        screen.blit(txt_score, (15, curr_y))
        curr_y += txt_score.get_height() + 2

        txt_mode = FONT_SMALL.render(f"MODO: {self.mode.replace('_', ' ')}", True, COLOR_PIXEL_DARK)
        screen.blit(txt_mode, (15, curr_y))
        curr_y += txt_mode.get_height() + 4

        if self.cheat_little_grid:
            txt_lg = FONT_SMALL.render("* CHEAT: LITTLE GRID *", True, COLOR_PIXEL_DARK)
            screen.blit(txt_lg, (15, curr_y))
            curr_y += txt_lg.get_height() + 2

        if self.cheat_godmode:
            txt_gm = FONT_SMALL.render("* CHEAT: GODMODE *", True, COLOR_PIXEL_DARK)
            screen.blit(txt_gm, (15, curr_y))
            curr_y += txt_gm.get_height() + 2

        grid_rect = pygame.Rect(self.grid_x, self.grid_y, self.grid_w, self.grid_h)
        pygame.draw.rect(screen, COLOR_PIXEL_DARK, grid_rect, 3)

        for x in range(self.cols):
            for y in range(self.rows):
                px = self.grid_x + x * self.cell_size
                py = self.grid_y + y * self.cell_size
                pygame.draw.rect(screen, COLOR_GRID_LINE, (px, py, self.cell_size, self.cell_size), 1)

        for ax, ay in self.apples:
            cx = self.grid_x + ax * self.cell_size + self.cell_size // 2
            cy = self.grid_y + ay * self.cell_size + self.cell_size // 2
            rad = self.cell_size // 2 - 1
            pygame.draw.circle(screen, COLOR_PIXEL_DARK, (cx, cy), max(2, rad))
            pygame.draw.circle(screen, COLOR_LCD_BG, (cx, cy), max(1, rad // 2))

        for sx, sy in self.snake:
            px = self.grid_x + sx * self.cell_size
            py = self.grid_y + sy * self.cell_size
            pygame.draw.rect(screen, COLOR_PIXEL_DARK, (px + 1, py + 1, self.cell_size - 2, self.cell_size - 2))

        pygame.draw.line(screen, COLOR_PIXEL_DARK, (15, PAD_AREA_TOP - 10), (WIDTH - 15, PAD_AREA_TOP - 10), 3)

        for btn, dir_label in [(btn_up, "UP"), (btn_down, "DOWN"), (btn_left, "LEFT"), (btn_right, "RIGHT")]:
            pygame.draw.rect(screen, COLOR_BTN_BG, btn)
            pygame.draw.rect(screen, COLOR_PIXEL_DARK, btn, 3)
            draw_vector_arrow(screen, btn, dir_label, COLOR_PIXEL_DARK)

        if self.state in ["GAMEOVER", "WIN"]:
            self.draw_popup_overlay()

    def draw_popup_overlay(self):
        box_w, box_h = int(WIDTH * 0.85), int(HEIGHT * 0.25)
        box = pygame.Rect((WIDTH - box_w)//2, self.grid_y + (self.grid_h - box_h)//2, box_w, box_h)
        
        pygame.draw.rect(screen, COLOR_LCD_BG, box)
        pygame.draw.rect(screen, COLOR_PIXEL_DARK, box, 4)

        main_txt = "GAME OVER" if self.state == "GAMEOVER" else "VICTORY!"
        sub_txt = f"PUNTI: {self.score}"

        t1 = FONT_LARGE.render(main_txt, True, COLOR_PIXEL_DARK)
        t2 = FONT_MED.render(sub_txt, True, COLOR_PIXEL_DARK)
        t3 = FONT_SMALL.render("TOCCA PER CONTINUARE", True, COLOR_PIXEL_DARK)

        screen.blit(t1, (box.centerx - t1.get_width()//2, box.y + int(box_h * 0.18)))
        screen.blit(t2, (box.centerx - t2.get_width()//2, box.y + int(box_h * 0.48)))
        screen.blit(t3, (box.centerx - t3.get_width()//2, box.y + int(box_h * 0.78)))

    def check_cheat_code(self):
        clean_code = self.code_input.strip().lower()
        if clean_code == "little grid":
            self.cheat_little_grid = not self.cheat_little_grid
        elif clean_code in ["godmode", "godmod"]:
            self.cheat_godmode = not self.cheat_godmode
        self.code_input = ""


# --- LOOP PRINCIPALE ---
game = SnakeGame()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos

            if game.state == "MAIN_MENU":
                if game.main_play_btn.collidepoint(pos):
                    game.state = "MODE_MENU"

            elif game.state == "MODE_MENU":
                for rect, key in game.mode_buttons:
                    if rect.collidepoint(pos):
                        if key == "SECRET":
                            game.secret_click_count += 1
                            if game.secret_click_count >= 5:
                                game.secret_click_count = 0
                                game.state = "CODE_MENU"
                                break
                        else:
                            game.secret_click_count = 0
                        game.mode = key
                
                if game.start_play_btn.collidepoint(pos):
                    game.reset_game()
                    game.state = "PLAYING"
                
                elif game.btn_mode_back.collidepoint(pos):
                    game.state = "MAIN_MENU"

            elif game.state == "CODE_MENU":
                for rect, char in game.keyboard_buttons:
                    if rect.collidepoint(pos):
                        if char == 'DEL':
                            game.code_input = game.code_input[:-1]
                        elif char == 'SPACE':
                            game.code_input += " "
                        elif char == 'ENT':
                            game.check_cheat_code()
                        else:
                            if len(game.code_input) < 18:
                                game.code_input += char

                if game.btn_submit_code.collidepoint(pos):
                    game.check_cheat_code()

                elif game.btn_code_back.collidepoint(pos):
                    game.state = "MODE_MENU"

            elif game.state == "PLAYING":
                if btn_in_game_back.collidepoint(pos):
                    game.state = "MODE_MENU"
                elif btn_up.collidepoint(pos):
                    game.handle_input((0, -1))
                elif btn_down.collidepoint(pos):
                    game.handle_input((0, 1))
                elif btn_left.collidepoint(pos):
                    game.handle_input((-1, 0))
                elif btn_right.collidepoint(pos):
                    game.handle_input((1, 0))

            elif game.state in ["GAMEOVER", "WIN"]:
                game.state = "MODE_MENU"

    game.update()
    game.draw()
    clock.tick(game.current_fps)
