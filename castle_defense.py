from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time

player_pos = [0, 0, 100]   # player starts near castle
player_angle = 0  # rotation of the gun in degrees (around Z-axis)

castle_hp = 100
castle_max_hp = 100
fovY = 120
camera_pos = (0, -600, 300)

# Camera Control
camera_angle = 0        # rotation around the center (left/right)
camera_height = 300     # height from the floor
camera_distance = 600   # distance from the center of the castle
first_person_mode = False

# Bullets
bullets = []  # list of active bullets
bullet_speed = 15
bullet_lifetime = 100  # max frames before disappearing

current_wave_side = None

# Enemy spawn timing
last_spawn_time = time.time()
spawn_interval = random.uniform(1.0, 3.0)

gold = 0

double_shot_mode = False

delayed_bullets = []  # store bullets to spawn late

game_over = False

flag_up = False
flag_time = 0
flag_duration = 10  # seconds

last_heal_time = 0

flag_uses = 0           # how many times flag has been raised
max_flag_uses = 5       # maximum allowed flag raises

def draw_background():
    # Gradient lawn (darker near castle, lighter outward)
    for i in range(3):
        color_intensity = 0.3 + 0.1 * i
        glColor3f(0.3 * color_intensity, 0.6 * color_intensity, 0.3 * color_intensity)
        size = 800 + i * 200
        glBegin(GL_QUADS)
        glVertex3f(-size, -size, 0)
        glVertex3f(size, -size, 0)
        glVertex3f(size, size, 0)
        glVertex3f(-size, size, 0)
        glEnd()

    # Dirt path leading to castle gate
    glPushMatrix()
    glColor3f(0.5, 0.35, 0.2)  # brown dirt
    glBegin(GL_QUADS)
    glVertex3f(-40, -800, 0)
    glVertex3f(40, -800, 0)
    glVertex3f(40, -150, 0)  # leads to gate (z axis)
    glVertex3f(-40, -150, 0)
    glEnd()
    glPopMatrix()

    # Bushes / Stones at edges
    bush_positions = [(-300, 400), (350, 300), (-350, -250), (250, -400)]
    for bx, by in bush_positions:
        glPushMatrix()
        glColor3f(0.1, 0.5, 0.1)  # dark green bush
        glTranslatef(bx, by, 10)
        glutSolidSphere(20, 10, 10)
        glPopMatrix()

    stone_positions = [(-200, 500), (400, -300), (0, -500)]
    for sx, sy in stone_positions:
        glPushMatrix()
        glColor3f(0.5, 0.5, 0.5)  # gray stone
        glTranslatef(sx, sy, 5)
        glutSolidCube(10)
        glPopMatrix()

def draw_castle():
    # Base walls
    glPushMatrix()
    glColor3f(0.6, 0.4, 0.2)  # brown
    glScalef(4, 4, 2)
    glTranslatef(0, 0, 25)
    glutSolidCube(50)
    
    # Outline for base
    glColor3f(0, 0, 0)  # black outline
    glutWireCube(50)
    glPopMatrix()

    # Terrace Railing
    glColor3f(0.2, 0.2, 0.2)  # dark gray railing
    # glColor3f(0.4, 0.3, 0.15)

    terrace_half = 50 * 4 / 2  # half the base width
    post_height = 40            # tall enough to prevent falling
    post_spacing = 15

    # Draw vertical posts along the edges
    for x in range(-int(terrace_half), int(terrace_half)+1, post_spacing):
        for y in [-int(terrace_half), int(terrace_half)]:
            glPushMatrix()
            glTranslatef(x, y, 50 + post_height/2)  # Z=top of base + half post
            glScalef(1, 1, post_height / 5)
            glutSolidCube(5)
            glPopMatrix()
    for y in range(-int(terrace_half), int(terrace_half)+1, post_spacing):
        for x in [-int(terrace_half), int(terrace_half)]:
            glPushMatrix()
            glTranslatef(x, y, 50 + post_height/2)
            glScalef(1, 1, post_height / 5)
            glutSolidCube(5)
            glPopMatrix()

    # Draw horizontal beams (top and bottom)
    beam_thickness = 2
    for z in [50 + 5, 50 + post_height - 5]:  # bottom and top beams
        glPushMatrix()
        glTranslatef(0, 0, z)
        glScalef(terrace_half*2, 2, beam_thickness)
        glutSolidCube(1)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(0, 0, z)
        glScalef(2, terrace_half*2, beam_thickness)
        glutSolidCube(1)
        glPopMatrix()
    
    # Towers with cone roofs
    for dx, dy in [(120,120), (-120,120), (120,-120), (-120,-120)]:
        glPushMatrix()
        glTranslatef(dx, dy, 0)
        glColor3f(0.5,0.5,0.5)
        gluCylinder(gluNewQuadric(), 25, 25, 100, 10, 10)
        glTranslatef(0,0,100)
        glColor3f(0.4,0.1,0.1)
        glutSolidCone(30, 50, 10, 10)
        glPopMatrix()

    # Front gate
    glPushMatrix()
    glTranslatef(0, -120, 0)
    glColor3f(0.3,0.2,0.1)
    glScalef(1.5, 0.5, 1.5)
    glutSolidCube(40)
    
    # Outline for gate
    glColor3f(0, 0, 0)
    glutWireCube(40)
    glPopMatrix()

    glColor3f(0.7, 0.6, 0.4)  # stone-brown

    terrace_size = 200
    parapet_height = 20
    merlon_height = 40
    merlon_width = 20
    spacing = 40

    # Parapet wall (continuous low wall)
    glPushMatrix()
    glTranslatef(0, 0, 100)
    glScalef(terrace_size, terrace_size, parapet_height)
    glutSolidCube(1)

    # Outline (just for distinction)
    glColor3f(0, 0, 0)
    glutWireCube(1)
    glPopMatrix()

    # Merlons along X edges
    for x in range(-terrace_size//2, terrace_size//2+1, spacing):
        for y in [-terrace_size//2, terrace_size//2]:
            glPushMatrix()
            glTranslatef(x, y, 100 + parapet_height)
            glScalef(merlon_width, 10, merlon_height)
            glColor3f(0.7, 0.6, 0.4)  # solid
            glutSolidCube(1)
            glColor3f(0, 0, 0)        # outline
            glutWireCube(1)
            glPopMatrix()

    # Merlons along Y edges
    for y in range(-terrace_size//2, terrace_size//2+1, spacing):
        for x in [-terrace_size//2, terrace_size//2]:
            glPushMatrix()
            glTranslatef(x, y, 100 + parapet_height)
            glScalef(10, merlon_width, merlon_height)
            glColor3f(0.7, 0.6, 0.4)  # solid
            glutSolidCube(1)
            glColor3f(0, 0, 0)        # outline
            glutWireCube(1)
            glPopMatrix()

    if flag_up:
        glPushMatrix()
        # Position on terrace 
        glTranslatef(0, 0, 150)  # base of pole at top of terrace

        # Draw pole
        glColor3f(0.6, 0.3, 0)  # brown
        glPushMatrix()
        glScalef(1, 1, 50)      # thin tall pole
        glutSolidCube(2)
        glPopMatrix()

        # Draw flag rectangle attached to top of pole
        glColor3f(1, 1, 1)      # white
        glPushMatrix()
        glTranslatef(1 + 10, 0, 50)  # z = half pole height + half flag height
        glScalef(20, 1, 10)      # flag size (width, depth, height)
        glutSolidCube(1)
        glPopMatrix()

        glPopMatrix()

def draw_player():
    glPushMatrix()
    
    # Adjust Z so player stands on terrace
    terrace_height = 100 + 20  # parapet base + half of parapet height
    player_base_height = 10    # half torso height
    glTranslatef(player_pos[0], player_pos[1], terrace_height + player_base_height)
    glRotatef(player_angle, 0, 0, 1)
    
    # Torso
    glPushMatrix()
    glColor3f(0, 0, 1)  # blue shirt
    glScalef(1, 0.6, 1.5)
    glutSolidCube(20)
    glPopMatrix()
    
    # Head
    glPushMatrix()
    glColor3f(1, 0.8, 0.6)  # skin color
    glTranslatef(0, 0, 18)  # above torso
    glutSolidSphere(6, 16, 16)
    glPopMatrix()

    # Hair
    glPushMatrix()
    glColor3f(0.2, 0.1, 0)  # dark brown hair
    glTranslatef(0, 0, 20)  # slightly above head
    glutSolidSphere(6.2, 16, 16)
    glPopMatrix()

    # Helmet
    glPushMatrix()
    glColor3f(0.3, 0.3, 0.3)  # metallic gray
    glTranslatef(0, 0, 22)  # slightly above hair
    glutSolidSphere(6.5, 16, 16)
    glPopMatrix()
 
    # Arms
    arm_radius = 2
    arm_length = 15
    glColor3f(0, 0, 1)
    
    # Left arm
    glPushMatrix()
    glTranslatef(-11, 0, 8)
    glRotatef(-20, 0, 1, 0)
    glRotatef(-45, 1, 0, 0)
    gluCylinder(gluNewQuadric(), arm_radius, arm_radius, arm_length, 12, 3)
    glPopMatrix()
    
    # Right arm
    glPushMatrix()
    glTranslatef(11, 0, 8)
    glRotatef(20, 0, 1, 0)
    glRotatef(-45, 1, 0, 0)
    gluCylinder(gluNewQuadric(), arm_radius, arm_radius, arm_length, 12, 3)
    glPopMatrix()
    
    # Legs
    leg_radius = 2.5
    leg_length = 18
    glColor3f(0.1, 0.1, 0.6)  # pants color

    # Left leg
    glPushMatrix()
    glTranslatef(-5, 0, -leg_length)  # move down from torso
    gluCylinder(gluNewQuadric(), leg_radius, leg_radius, leg_length, 12, 3)
    glPopMatrix()

    # Right leg
    glPushMatrix()
    glTranslatef(5, 0, -leg_length)
    gluCylinder(gluNewQuadric(), leg_radius, leg_radius, leg_length, 12, 3)
    glPopMatrix()

    # Gun 
    glPushMatrix()
    # Position roughly at midpoint between arms
    glTranslatef(0, 5, 10)  # slightly forward and up
    glRotatef(-90, 1, 0, 0)  # point forward
    # glRotatef(10, 0, 1, 0)   # slight tilt
    glRotatef(-10, 1, 0, 0)
    
    # Barrel
    glColor3f(0.1, 0.1, 0.1)
    gluCylinder(gluNewQuadric(), 1.2, 1.2, 18, 12, 3)
    
    # Stock (behind barrel)
    glPushMatrix()
    glTranslatef(0, 0, -5)
    glScalef(2, 1.5, 3)
    glColor3f(0.2, 0.2, 0.2)
    glutSolidCube(5)
    glPopMatrix()
    
    # Handle (below barrel)
    glPushMatrix()
    glTranslatef(0, -2, 5)
    glRotatef(30, 1, 0, 0)
    glScalef(1.2, 1, 3)
    glutSolidCube(3)
    glPopMatrix()
    
    glPopMatrix()  # end gun
    glPopMatrix()  # end player

class Bullet:
    def __init__(self, x, y, z, dx, dy, dz):
        self.pos = [x, y, z]
        self.dir = [dx, dy, dz]
        self.frames = 0  # track lifetime

    def update(self):
        self.pos[0] += self.dir[0] * bullet_speed
        self.pos[1] += self.dir[1] * bullet_speed
        self.pos[2] += self.dir[2] * bullet_speed
        self.frames += 1
        return self.frames < bullet_lifetime  # Returns True if the bullet hasn’t exceeded its maximum lifetime. If frames >= bullet_lifetime, the bullet is considered “dead” and should be removed.

    def draw(self):
        glPushMatrix()
        glColor3f(1, 1, 0)  # yellow bullet
        glTranslatef(*self.pos)
        glutSolidSphere(2, 8, 8)
        glPopMatrix()

class Enemy:
    def __init__(self, x, y, z=10, speed=0.02):  # set z above ground
        self.pos = [x, y, z]
        self.speed = speed
        self.size = 10  # for drawing
        self.alive = True

    def update(self):
        global flag_up

        if flag_up:
            return  # Enemy pauses when flag is up

        # Move toward castle center (0,0)
        dx = -self.pos[0]
        dy = -self.pos[1]
        distance = math.sqrt(dx*dx + dy*dy)
        if distance > 0:
            self.pos[0] += self.speed * dx / distance
            self.pos[1] += self.speed * dy / distance

        # Check if reached castle 
        if distance < 20:  # close enough to castle
            self.alive = False  # for now, just remove them

    def draw(self):
        glPushMatrix()
        glTranslatef(*self.pos)

        # Body
        glPushMatrix()
        glColor3f(0.8, 0, 0)  # red body
        glTranslatef(0, 0, 10)  # raise above ground
        glScalef(1, 1, 2)
        glutSolidCube(self.size)
        glPopMatrix()

        # Head
        glPushMatrix()
        glColor3f(1, 0.7, 0.6)  # skin/face color
        glTranslatef(0, 0, 25)
        glutSolidSphere(self.size/2, 12, 12)
        glPopMatrix()

        # Eyes 
        eye_offset = self.size/4
        glColor3f(0,0,0)
        for ex in [-eye_offset, eye_offset]:
            glPushMatrix()
            glTranslatef(ex, self.size/2 + 1, 25)
            glutSolidSphere(1.5, 8, 8)
            glPopMatrix()

        glPopMatrix()

enemies = []
spawn_distance = 400  # distance from castle

def spawn_enemy_wave(wave_size=5):
    spawn_distance = 500  # distance from castle center
    for i in range(wave_size):
        angle = random.uniform(0, 2*math.pi)
        x = spawn_distance * math.cos(angle)
        y = spawn_distance * math.sin(angle)
        z = 10  # slightly above ground for visibility
        enemies.append(Enemy(x, y, z))

def update_enemies():
    for e in enemies:
        # Move toward castle (0,0)
        dx = -e.pos[0]
        dy = -e.pos[1]
        dz = 0
        length = math.sqrt(dx*dx + dy*dy + dz*dz)
        if length != 0:
            dx, dy, dz = dx/length, dy/length, dz/length
        e.pos[0] += dx * e.speed
        e.pos[1] += dy * e.speed
        e.pos[2] += dz * e.speed

def setupCamera():
    global camera_angle, camera_height, camera_distance, first_person_mode
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    if first_person_mode:
        # First-person: camera at gun position
        cam_x, cam_y, cam_z = player_pos[0], player_pos[1]+25, player_pos[2]+15
        target_x, target_y, target_z = cam_x, cam_y + 50, cam_z
        up_x, up_y, up_z = 0, 0, 1
    else:
        # Third-person: orbiting camera
        cam_x = camera_distance * math.sin(math.radians(camera_angle))
        cam_y = -camera_distance * math.cos(math.radians(camera_angle))
        cam_z = camera_height
        target_x, target_y, target_z = 0, 0, 50  # look at castle terrace
        up_x, up_y, up_z = 0, 0, 1
    
    gluLookAt(cam_x, cam_y, cam_z, target_x, target_y, target_z, up_x, up_y, up_z)

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)

    setupCamera()

    # Draw Scene
    draw_background()

    draw_castle()
    draw_player()

    for b in bullets:
        b.draw()

    for e in enemies:
        e.draw()

    draw_text(10, 770, f"Castle HP: {castle_hp}/{castle_max_hp}")
    draw_text(10, 740, f"Gold: {gold}")
    draw_text(10, 710, f"Flags left: {max_flag_uses - flag_uses}")
    
    if game_over:
        draw_text(400, 400, "GAME OVER", font=GLUT_BITMAP_TIMES_ROMAN_24)

    glutSwapBuffers()

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

time_counter = 0 

def idle():
    global time_counter, enemies, bullets, castle_hp, last_spawn_time, spawn_interval, gold, game_over, flag_up, flag_time, last_heal_time

    if game_over:
        return  # skip rest of idle updates

    current_time = time.time()
    time_counter += 0.001  # increment manually each frame

    # Smooth day-night cycle
    factor = (math.sin(time_counter / 10) + 1) / 2  # oscillates 0 → 1 → 0
    r = 0.05 + factor * (0.6 - 0.05)
    g = 0.05 + factor * (0.8 - 0.05)
    b = 0.2 + factor * (1.0 - 0.2)
    
    glClearColor(r, g, b, 1.0)  # update sky color dynamically

    ready_bullets = [b for t, b in delayed_bullets if t <= current_time]
    for b in ready_bullets:
        bullets.append(b)

    # Keep only bullets still waiting
    delayed_bullets[:] = [(t, b) for t, b in delayed_bullets if t > current_time]

    # Spawn enemies
    if current_time - last_spawn_time > spawn_interval:
        last_spawn_time = current_time
        spawn_interval = random.uniform(1.0, 3.0)
        spawn_enemy_wave(1)

    # Update enemies
    updated_enemies = []
    for e in enemies:
        e.update()

        # Enemy reached castle
        dist_to_castle = math.sqrt(e.pos[0]**2 + e.pos[1]**2)
        if dist_to_castle < 125:
            castle_hp -= 10
            e.alive = False

        if castle_hp <= 0 and not game_over:
            game_over = True
            print("Game Over! The castle has fallen!")

        if e.alive:
            updated_enemies.append(e)
    enemies[:] = updated_enemies

    # Update bullets with auto-aim
    aim_angle_threshold = math.radians(40)  # auto-aim cone
    max_hit_distance = 800
    homing_strength = 0.2  # how fast bullet adjusts direction toward enemy

    bullets_to_keep = []

    for b in bullets:
        alive = b.update()
        if not alive:
            continue

        # Find nearest enemy within auto-aim cone
        nearest_enemy = None
        nearest_dist = max_hit_distance

        for e in enemies:
            # Vector from bullet to enemy
            ex, ey, ez = e.pos[0] - b.pos[0], e.pos[1] - b.pos[1], e.pos[2] - b.pos[2]
            enemy_dist = math.sqrt(ex*ex + ey*ey + ez*ez)
            if enemy_dist == 0:
                nearest_enemy = e
                break

            # Normalize enemy vector
            exn, eyn, ezn = ex/enemy_dist, ey/enemy_dist, ez/enemy_dist

            # Normalize bullet direction
            bx, by, bz = b.dir
            blen = math.sqrt(bx*bx + by*by + bz*bz)
            bx, by, bz = bx/blen, by/blen, bz/blen

            # Angle between bullet and enemy vector
            dot = exn*bx + eyn*by + ezn*bz
            angle = math.acos(max(-1, min(1, dot)))

            if angle < aim_angle_threshold and enemy_dist < nearest_dist:
                nearest_enemy = e
                nearest_dist = enemy_dist

        if nearest_enemy:
            # Adjust bullet direction slightly toward enemy (auto-aim)
            ex, ey, ez = nearest_enemy.pos[0] - b.pos[0], nearest_enemy.pos[1] - b.pos[1], nearest_enemy.pos[2] - b.pos[2]
            length = math.sqrt(ex*ex + ey*ey + ez*ez)
            if length != 0:
                ex, ey, ez = ex/length, ey/length, ez/length
                # Interpolate direction toward enemy
                b.dir[0] = (1 - homing_strength) * b.dir[0] + homing_strength * ex
                b.dir[1] = (1 - homing_strength) * b.dir[1] + homing_strength * ey
                b.dir[2] = (1 - homing_strength) * b.dir[2] + homing_strength * ez
                # Normalize
                blen = math.sqrt(b.dir[0]**2 + b.dir[1]**2 + b.dir[2]**2)
                b.dir[0] /= blen
                b.dir[1] /= blen
                b.dir[2] /= blen

            # Check if bullet is close enough to hit
            if nearest_dist < 15:
                if nearest_enemy in enemies:
                    enemies.remove(nearest_enemy)
                    gold += 1
                continue  # bullet disappears after hit

        bullets_to_keep.append(b)

    bullets[:] = bullets_to_keep

    if flag_up:
        current_time = time.time()
        # Heal 1 HP every second
        if current_time - last_heal_time >= 1:
            if castle_hp < castle_max_hp:
                castle_hp += 1
            last_heal_time += 1  # move to next second

    # Lower flag automatically 
    if flag_up and (time.time() - flag_time > flag_duration):
        flag_up = False

    glutPostRedisplay()

def keyboardListener(key, x, y):
    global fovY, player_pos, player_angle, castle_hp, gold, double_shot_mode, flag_up, flag_time, last_heal_time
    move_speed = 5  
    key = key.decode("utf-8")  # convert from bytes
    player_angle %= 360

    if key == 'w':
        rad = math.radians(player_angle)
        player_pos[0] += move_speed * math.sin(rad)
        player_pos[1] += move_speed * math.cos(rad)
    elif key == 's':
        rad = math.radians(player_angle)
        player_pos[0] -= move_speed * math.sin(rad)
        player_pos[1] -= move_speed * math.cos(rad)
    elif key == 'a':
        player_angle += 5   # rotate gun left
    elif key == 'd':
        player_angle -= 5   # rotate gun right

    elif key == 'z' or key == 'Z':  # zoom in
        fovY -= 5
        if fovY < 20:
            fovY = 20
    elif key == 'x' or key == 'X':  # zoom out
        fovY += 5
        if fovY > 120:
            fovY = 120

    elif key == 'g' or key == 'G':  # heal castle
        if gold >= 5 and castle_hp < castle_max_hp:
            # Compute max possible HP to restore
            max_restore = (gold // 5)
            hp_needed = castle_max_hp - castle_hp
            hp_to_add = min(max_restore, hp_needed)
            castle_hp += hp_to_add
            gold -= hp_to_add * 5

    elif key == 'f' or key == 'F':
        global flag_uses
        if flag_uses < max_flag_uses and not flag_up:  
            flag_up = True
            flag_time = time.time()
            last_heal_time = flag_time  # reset healing timer
            flag_uses += 1
        else:
            print(" No more flags available!") 

    # Keep player within terrace bounds
    player_half_width = 10      # half torso width
    railing_thickness = 5       # from glScalef
    margin = player_half_width + railing_thickness/2

    terrace_limit = 100 - margin
    player_pos[0] = max(-terrace_limit, min(terrace_limit, player_pos[0]))
    player_pos[1] = max(-terrace_limit, min(terrace_limit, player_pos[1]))

    glutPostRedisplay()

def specialKeyListener(key, x, y):
    global camera_angle, camera_height, player_pos
    move_speed = 5

    if first_person_mode:
        if key == GLUT_KEY_UP:
            player_pos[1] += move_speed
        elif key == GLUT_KEY_DOWN:
            player_pos[1] -= move_speed
        elif key == GLUT_KEY_LEFT:
            player_pos[0] -= move_speed
        elif key == GLUT_KEY_RIGHT:
            player_pos[0] += move_speed
    
    else:
    # Third-person camera
        if key == GLUT_KEY_UP:
            camera_height += 10
            if camera_height > 500: # cap max height
                camera_height = 500
        elif key == GLUT_KEY_DOWN:
            camera_height -= 10
            if camera_height < 50:  # cap min height
                camera_height = 50
        elif key == GLUT_KEY_LEFT:
            camera_angle -= 5
        elif key == GLUT_KEY_RIGHT:
            camera_angle += 5

    glutPostRedisplay()

def mouseListener(button, state, x, y):
    global first_person_mode, bullets, player_pos, player_angle

    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        first_person_mode = not first_person_mode
        glutPostRedisplay()

    elif button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        px, py, pz = player_pos

        # Local gun tip position
        gun_tip_local = [0, 5, 10 + 18]  # gun offset + barrel length

        # Step 1: rotate around X by -90° (barrel pointing forward)
        theta = math.radians(-90)
        x1 = gun_tip_local[0]
        y1 = gun_tip_local[1]*math.cos(theta) - gun_tip_local[2]*math.sin(theta)
        z1 = gun_tip_local[1]*math.sin(theta) + gun_tip_local[2]*math.cos(theta)

        # Step 2: rotate around X by -10° (gun tilt)
        theta2 = math.radians(-10)
        x2 = x1
        y2 = y1*math.cos(theta2) - z1*math.sin(theta2)
        z2 = y1*math.sin(theta2) + z1*math.cos(theta2)

        # Step 3: rotate around Z by player_angle
        angle_rad = math.radians(player_angle)
        x3 = x2*math.cos(angle_rad) - y2*math.sin(angle_rad)
        y3 = x2*math.sin(angle_rad) + y2*math.cos(angle_rad)
        z3 = z2

        # World position of muzzle
        muzzle_x = px + x3
        muzzle_y = py + y3
        muzzle_z = pz + z3

        # Compute bullet direction: start with local forward [0,0,1] and apply same rotations
        dx, dy, dz = 0,0,1

        # rotate -90° X
        dx1 = dx
        dy1 = dy*math.cos(theta) - dz*math.sin(theta)
        dz1 = dy*math.sin(theta) + dz*math.cos(theta)

        # rotate -10° X
        dx2 = dx1
        dy2 = dy1*math.cos(theta2) - dz1*math.sin(theta2)
        dz2 = dy1*math.sin(theta2) + dz1*math.cos(theta2)

        # rotate player_angle Z
        dx3 = dx2*math.cos(angle_rad) - dy2*math.sin(angle_rad)
        dy3 = dx2*math.sin(angle_rad) + dy2*math.cos(angle_rad)
        dz3 = dz2

        # Normalize
        length = math.sqrt(dx3*dx3 + dy3*dy3 + dz3*dz3)
        dx3 /= length
        dy3 /= length
        dz3 /= length

        # Determine number of bullets
        num_bullets = 1
        if double_shot_mode and gold >= 10:
            gold -= 10
            num_bullets = 2  # schedule second bullet

        for i in range(num_bullets):
            if i == 1:
                # Schedule second bullet after short interval
                delay = 0.2  # 0.2 seconds
                angle_offset = math.radians(5)
                cos_a = math.cos(angle_offset)
                sin_a = math.sin(angle_offset)
                dx_rot = dx3 * cos_a - dy3 * sin_a
                dy_rot = dx3 * sin_a + dy3 * cos_a
                dz_rot = dz3
                delayed_bullets.append((time.time() + delay, Bullet(muzzle_x, muzzle_y, muzzle_z, dx_rot, dy_rot, dz_rot)))
            else:
                bullets.append(Bullet(muzzle_x, muzzle_y, muzzle_z, dx3, dy3, dz3))

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)

    glutCreateWindow(b"Castle Defense Game")

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glEnable(GL_DEPTH_TEST)

    glutMainLoop()

if __name__ == "__main__":
    main()
