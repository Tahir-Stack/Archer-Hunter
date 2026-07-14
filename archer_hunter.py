"""
Archer Hunter: The Last Kingdom
A complete arcade game using only Python's built-in Turtle Graphics.
No Pygame or third-party libraries needed. Run with: python archer_hunter_short.py

Controls: Up/Down = move | Space = shoot/confirm | I = instructions
          P = pause | R = restart | Q = quit
"""

import turtle
import random
import math
import sys

# ---------------- CONSTANTS ----------------
W, H = 1000, 600
LEFT, RIGHT, TOP, BOTTOM = -W // 2, W // 2, H // 2, -H // 2
GROUND_Y = -260
PLAYER_X = -450
PLAYER_MIN_Y, PLAYER_MAX_Y = -230, 230
ARROW_SPEED = 30
NUM_ENEMIES = 5
LIFE_START, MAX_LIVES = 3, 5
LEVEL_UP_SCORE, BOSS_SCORE = 100, 300
HS_FILE = "highscore.txt"

ENEMY_TYPES = {
    "Goblin": {"speed": 2.0, "score": 10, "shape": "triangle", "color": "green"},
    "Orc":    {"speed": 1.5, "score": 20, "shape": "square", "color": "saddlebrown"},
    "Wolf":   {"speed": 3.0, "score": 15, "shape": "circle", "color": "gray"},
}
POWERUPS = {"life": "pink", "double": "gold", "rapid": "cyan"}

# ---------------- GAME STATE ----------------
state = "START"           # START, INSTRUCTIONS, PLAYING, PAUSED, GAMEOVER
score = level = 0
lives = LIFE_START
high_score = 0
speed_mult = 1.0
arrow_active = False
boss = None
boss_hp = 0
next_level_score, next_boss_score = LEVEL_UP_SCORE, BOSS_SCORE
powerup = None
double_timer = rapid_timer = 0
enemies = []

# ---------------- SCREEN SETUP ----------------
screen = turtle.Screen()
screen.setup(W, H)
screen.title("Archer Hunter: The Last Kingdom")
screen.bgcolor("skyblue")
screen.tracer(0)

bg = turtle.Turtle(); bg.hideturtle(); bg.speed(0); bg.penup()
hud = turtle.Turtle(); hud.hideturtle(); hud.speed(0); hud.penup()
menu = turtle.Turtle(); menu.hideturtle(); menu.speed(0); menu.penup()

player = turtle.Turtle()
player.shape("triangle"); player.color("darkblue")
player.shapesize(1.2, 1.6); player.penup(); player.goto(PLAYER_X, 0)

arrow = turtle.Turtle()
arrow.shape("arrow"); arrow.color("black")
arrow.shapesize(0.5, 1.2); arrow.penup(); arrow.hideturtle()

# ---------------- HIGH SCORE FILE ----------------
def load_high_score():
    try:
        with open(HS_FILE) as f:
            return int(f.read().strip() or 0)
    except (FileNotFoundError, ValueError, OSError):
        return 0

def save_high_score(value):
    try:
        with open(HS_FILE, "w") as f:
            f.write(str(value))
    except OSError:
        pass

# ---------------- BACKGROUND ----------------
def draw_rect(t, x, y, w, h, color):
    t.penup(); t.goto(x, y); t.setheading(0); t.pendown()
    t.color(color); t.begin_fill()
    for _ in range(2):
        t.forward(w); t.left(90); t.forward(h); t.left(90)
    t.end_fill(); t.penup()

def draw_background():
    bg.clear()
    draw_rect(bg, LEFT, GROUND_Y, W, 40, "forestgreen")   # grass
    for x in (-470, -300, -130, 60, 250, 430):            # trees
        draw_rect(bg, x, GROUND_Y, 18, 55, "saddlebrown")
        bg.goto(x + 9, GROUND_Y + 55); bg.color("darkgreen")
        bg.pendown(); bg.begin_fill(); bg.circle(35); bg.end_fill(); bg.penup()
    screen.update()

# ---------------- HUD ----------------
def update_hud():
    hud.clear()
    hud.goto(LEFT + 20, TOP - 40)
    hud.write(f"Score: {score}   Level: {level}   Lives: {lives}   High Score: {high_score}",
              font=("Arial", 14, "bold"))
    tags = []
    if double_timer > 0: tags.append("DOUBLE SCORE")
    if rapid_timer > 0: tags.append("RAPID FIRE")
    if tags:
        hud.goto(LEFT + 20, TOP - 62)
        hud.write("  ".join(tags), font=("Arial", 12, "italic"))
    if boss is not None:
        bx, by = boss["turtle"].xcor() - 40, boss["turtle"].ycor() + 55
        draw_rect(hud, bx, by, 80, 8, "red")
        ratio = max(boss_hp, 0) / boss["max_hp"]
        if ratio > 0:
            draw_rect(hud, bx, by, 80 * ratio, 8, "lime")

# ---------------- PLAYER ----------------
def move_up():
    if state == "PLAYING":
        player.sety(min(player.ycor() + 25, PLAYER_MAX_Y))

def move_down():
    if state == "PLAYING":
        player.sety(max(player.ycor() - 25, PLAYER_MIN_Y))

# ---------------- ARROW ----------------
def shoot():
    global arrow_active
    if state != "PLAYING" or arrow_active:
        return
    arrow.goto(PLAYER_X + 25, player.ycor())
    arrow.showturtle()
    arrow_active = True

def reset_arrow():
    global arrow_active
    arrow.hideturtle(); arrow.goto(-2000, -2000)
    arrow_active = False

def move_arrow():
    if not arrow_active:
        return
    arrow.setx(arrow.xcor() + ARROW_SPEED)
    if arrow.xcor() > RIGHT:
        reset_arrow()
        if rapid_timer > 0:
            shoot()

# ---------------- ENEMIES ----------------
def make_enemy_turtle(kind):
    info = ENEMY_TYPES[kind]
    t = turtle.Turtle()
    t.shape(info["shape"]); t.color(info["color"])
    t.shapesize(1.3, 1.3); t.penup()
    return t

def random_spot():
    return random.randint(RIGHT - 150, RIGHT - 20), random.randint(PLAYER_MIN_Y, PLAYER_MAX_Y)

def spawn_enemy():
    kind = random.choice(list(ENEMY_TYPES))
    info = ENEMY_TYPES[kind]
    t = make_enemy_turtle(kind)
    x, y = random_spot()
    t.goto(x, y)
    return {"turtle": t, "type": kind, "speed": info["speed"], "value": info["score"]}

def init_enemies():
    global enemies
    for e in enemies:
        e["turtle"].hideturtle()
    enemies = [spawn_enemy() for _ in range(NUM_ENEMIES)]
    if state != "PLAYING":
        for e in enemies:
            e["turtle"].hideturtle()

def respawn(enemy):
    x, y = random_spot()
    enemy["turtle"].goto(x, y)
    if random.random() < 0.3:
        kind = random.choice(list(ENEMY_TYPES))
        info = ENEMY_TYPES[kind]
        enemy.update(type=kind, speed=info["speed"], value=info["score"])
        enemy["turtle"].shape(info["shape"]); enemy["turtle"].color(info["color"])

def lose_life():
    global lives
    lives -= 1
    if lives <= 0:
        lives = 0
        game_over()

def move_enemies():
    for e in enemies:
        e["turtle"].setx(e["turtle"].xcor() - e["speed"] * speed_mult)
        if e["turtle"].xcor() <= PLAYER_X + 15:
            lose_life()
            respawn(e)

# ---------------- BOSS ----------------
def spawn_boss():
    global boss, boss_hp
    t = turtle.Turtle()
    t.shape("circle"); t.color("purple"); t.shapesize(3, 3); t.penup()
    t.goto(RIGHT - 80, 0)
    boss_hp = 5 + level
    boss = {"turtle": t, "angle": 0.0, "max_hp": boss_hp}

def move_boss():
    if boss is None:
        return
    boss["angle"] += 0.05
    y = max(min(math.sin(boss["angle"]) * 150, PLAYER_MAX_Y), PLAYER_MIN_Y)
    boss["turtle"].sety(y)
    boss["turtle"].setx(boss["turtle"].xcor() - 0.3 * speed_mult)
    if boss["turtle"].xcor() <= PLAYER_X + 20:
        lose_life()
        boss["turtle"].goto(RIGHT - 80, 0)

def defeat_boss():
    global boss, boss_hp
    if boss:
        boss["turtle"].hideturtle()
    boss, boss_hp = None, 0

# ---------------- POWER-UPS ----------------
def maybe_spawn_powerup():
    global powerup
    if powerup is None and random.randint(1, 400) == 1:
        kind = random.choice(list(POWERUPS))
        t = turtle.Turtle()
        t.shape("circle"); t.color(POWERUPS[kind]); t.shapesize(1.1, 1.1); t.penup()
        t.goto(random.randint(0, RIGHT - 50), random.randint(PLAYER_MIN_Y, PLAYER_MAX_Y))
        powerup = {"turtle": t, "type": kind}

def move_powerup():
    global powerup
    if powerup is None:
        return
    powerup["turtle"].setx(powerup["turtle"].xcor() - 4)
    if powerup["turtle"].xcor() < LEFT:
        powerup["turtle"].hideturtle(); powerup = None

def apply_powerup(kind):
    global lives, double_timer, rapid_timer
    if kind == "life" and lives < MAX_LIVES:
        lives += 1
    elif kind == "double":
        double_timer = 400
    elif kind == "rapid":
        rapid_timer = 400

def tick_powerup_timers():
    global double_timer, rapid_timer
    if double_timer > 0: double_timer -= 1
    if rapid_timer > 0: rapid_timer -= 1

# ---------------- COLLISIONS ----------------
def dist(a, b):
    return math.hypot(a.xcor() - b.xcor(), a.ycor() - b.ycor())

def add_score(pts):
    global score
    score += pts * 2 if double_timer > 0 else pts

def explosion(x, y):
    boom = turtle.Turtle()
    boom.hideturtle(); boom.speed(0); boom.penup(); boom.goto(x, y)
    boom.shape("circle"); boom.color("orange"); boom.showturtle()
    grow(boom, 0)

def grow(boom, step):
    if step < 3:
        size = 0.5 + step * 0.5
        boom.shapesize(size, size)
        screen.ontimer(lambda: grow(boom, step + 1), 60)
    else:
        boom.hideturtle()

def check_collisions():
    global boss_hp, powerup
    if arrow_active:
        for e in enemies:
            if dist(arrow, e["turtle"]) < 28:
                add_score(e["value"])
                explosion(e["turtle"].xcor(), e["turtle"].ycor())
                respawn(e)
                reset_arrow()
                break
        if boss is not None and arrow_active and dist(arrow, boss["turtle"]) < 45:
            boss_hp -= 1
            explosion(boss["turtle"].xcor(), boss["turtle"].ycor())
            reset_arrow()
            if boss_hp <= 0:
                add_score(100)
                defeat_boss()
    if powerup is not None and dist(player, powerup["turtle"]) < 35:
        apply_powerup(powerup["type"])
        powerup["turtle"].hideturtle()
        powerup = None

# ---------------- LEVEL / BOSS TRIGGER ----------------
def check_level_up():
    global level, speed_mult, next_level_score
    if score >= next_level_score:
        level += 1
        speed_mult += 0.2
        next_level_score += LEVEL_UP_SCORE

def check_boss_trigger():
    global next_boss_score
    if score >= next_boss_score and boss is None:
        spawn_boss()
        next_boss_score += BOSS_SCORE

# ---------------- MENUS ----------------
def draw_start_screen():
    menu.clear()
    menu.goto(0, 120); menu.write("Archer Hunter: The Last Kingdom", align="center", font=("Arial", 26, "bold"))
    menu.goto(0, 60); menu.write("Defend the kingdom from Goblins, Orcs and Wolves.", align="center", font=("Arial", 14, "normal"))
    menu.goto(0, 0); menu.write("Press SPACE to Start", align="center", font=("Arial", 18, "bold"))
    menu.goto(0, -40); menu.write("Press I for Instructions", align="center", font=("Arial", 16, "normal"))
    menu.goto(0, -80); menu.write(f"High Score: {high_score}", align="center", font=("Arial", 14, "italic"))
    screen.update()

def draw_instructions():
    menu.clear()
    menu.goto(0, 150); menu.write("HOW TO PLAY", align="center", font=("Arial", 24, "bold"))
    lines = [
        "Up / Down Arrow  ->  Move your archer",
        "Spacebar         ->  Shoot an arrow",
        "P  ->  Pause / Resume     R  ->  Restart     Q  ->  Quit",
        "",
        "Every 100 points you level up and enemies get faster.",
        "Every 300 points a Boss appears!",
        "Grab power-ups: Extra Life, Double Score, Rapid Fire.",
        "You have 3 lives. Lose one if an enemy reaches you.",
    ]
    y = 100
    for line in lines:
        menu.goto(0, y); menu.write(line, align="center", font=("Arial", 13, "normal")); y -= 25
    menu.goto(0, y - 20); menu.write("Press SPACE to go back", align="center", font=("Arial", 14, "bold"))
    screen.update()

def draw_pause_screen():
    menu.clear()
    menu.goto(0, 20); menu.write("PAUSED", align="center", font=("Arial", 30, "bold"))
    menu.goto(0, -20); menu.write("P = Resume   R = Restart   Q = Quit", align="center", font=("Arial", 14, "normal"))
    screen.update()

def draw_game_over_screen():
    menu.clear()
    menu.goto(0, 60); menu.write("GAME OVER", align="center", font=("Arial", 32, "bold"))
    menu.goto(0, 0); menu.write(f"Final Score: {score}", align="center", font=("Arial", 18, "normal"))
    menu.goto(0, -40); menu.write(f"Highest Score: {high_score}", align="center", font=("Arial", 18, "normal"))
    menu.goto(0, -90); menu.write("Press R to Restart   |   Press Q to Quit", align="center", font=("Arial", 16, "bold"))
    screen.update()

# ---------------- STATE TRANSITIONS ----------------
def game_over():
    global state, high_score
    state = "GAMEOVER"
    if score > high_score:
        high_score = score
        save_high_score(high_score)
    reset_arrow()
    for e in enemies:
        e["turtle"].hideturtle()
    if boss:
        boss["turtle"].hideturtle()
    if powerup:
        powerup["turtle"].hideturtle()
    draw_game_over_screen()

def reset_game():
    global score, level, lives, speed_mult, next_level_score, next_boss_score
    global double_timer, rapid_timer, boss, boss_hp, powerup
    score, level, lives = 0, 1, LIFE_START
    speed_mult = 1.0
    next_level_score, next_boss_score = LEVEL_UP_SCORE, BOSS_SCORE
    double_timer = rapid_timer = 0
    if boss:
        boss["turtle"].hideturtle()
    boss, boss_hp = None, 0
    if powerup:
        powerup["turtle"].hideturtle()
    powerup = None
    player.goto(PLAYER_X, 0)
    reset_arrow()
    init_enemies()
    update_hud()

def start_game():
    global state
    state = "PLAYING"
    reset_game()
    menu.clear()
    screen.update()

def restart_game():
    global state
    if state in ("PAUSED", "GAMEOVER"):
        state = "PLAYING"
        reset_game()
        menu.clear()
        screen.update()

def toggle_pause():
    global state
    if state == "PLAYING":
        state = "PAUSED"
        draw_pause_screen()
    elif state == "PAUSED":
        state = "PLAYING"
        menu.clear()
        screen.update()

def quit_game():
    save_high_score(max(high_score, score))
    try:
        screen.bye()
    except turtle.Terminator:
        pass
    sys.exit(0)

def go_instructions():
    global state
    if state == "START":
        state = "INSTRUCTIONS"
        draw_instructions()

def handle_space():
    if state == "START":
        start_game()
    elif state == "INSTRUCTIONS":
        globals()["state"] = "START"
        draw_start_screen()
    elif state == "PLAYING":
        shoot()

# ---------------- CONTROLS ----------------
def setup_controls():
    screen.listen()
    screen.onkeypress(move_up, "Up")
    screen.onkeypress(move_down, "Down")
    screen.onkeypress(handle_space, "space")
    for k in ("i", "I"):
        screen.onkeypress(go_instructions, k)
    for k in ("p", "P"):
        screen.onkeypress(toggle_pause, k)
    for k in ("r", "R"):
        screen.onkeypress(restart_game, k)
    for k in ("q", "Q"):
        screen.onkeypress(quit_game, k)

# ---------------- MAIN LOOP ----------------
def game_loop():
    try:
        if state == "PLAYING":
            move_arrow()
            move_enemies()
            if boss is not None:
                move_boss()
            maybe_spawn_powerup()
            move_powerup()
            check_collisions()
            tick_powerup_timers()
            check_level_up()
            check_boss_trigger()
            update_hud()
        screen.update()
    except turtle.Terminator:
        return
    screen.ontimer(game_loop, 20)

def main():
    global high_score
    high_score = load_high_score()
    draw_background()
    init_enemies()
    update_hud()
    setup_controls()
    draw_start_screen()
    game_loop()
    turtle.done()

if __name__ == "__main__":
    try:
        main()
    except turtle.Terminator:
        pass
    except KeyboardInterrupt:
        save_high_score(high_score)
        sys.exit(0)

