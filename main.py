import pygame as pg
from math import degrees, atan2
from random import randint, uniform

"""Declarations"""
BACKGROUND = (127,127,127) 

WIDTH, HEIGHT = (800, 500)

FPS = 60

clock = pg.time.Clock()
screen = pg.display.set_mode((WIDTH, HEIGHT)) 
pg.display.set_caption('Bullet hell')

"""Functions"""
def draw():
    screen.fill(BACKGROUND) # draw Background
    enemy_group.draw(screen) # draw Enemy
    bullet_group.draw(screen) # draw Bullets
    player_group.draw(screen) # draw Player
    effect_group.draw(screen) # draw screen Effects

    #for player in player_group:
    #    if isinstance(player, Player) and player.focus: pg.draw.rect(screen, (0,255,255), player.hitbox) # draw Hitbox when focused
    #for enemy in enemy_group: pg.draw.rect(screen, (0,255,255), enemy.hitbox) # draw Enemy hitboxes (SUPER testing!)
    pg.display.flip() # Finally, flip display.

def update():
    for enemy in enemy_group: enemy.update()
    for i in player_group: i.update()
    for bullet in bullet_group: bullet.update()
    for effect in effect_group: effect.update()

def spritesheet(size, file_name, pos=(0, 0)):
    len_x, len_y = size
    rect_x, rect_y = pos
    sheet = pg.image.load(file_name).convert_alpha()
    sheet_rect = sheet.get_rect()
    sprites = []
    for _ in range(0, sheet_rect.height, size[1]):
        for _ in range(0, sheet_rect.width, size[0]):
            sheet.set_clip(pg.Rect(rect_x, rect_y, len_x, len_y))
            sprite = sheet.subsurface(sheet.get_clip())
            sprites.append(sprite)
            rect_x += len_x
        rect_y += len_y
        rect_x = 0
    return sprites

def rot_center(image, angle):
    orig_rect = image.get_rect()
    rot_image = pg.transform.rotate(image, angle)
    rot_rect = orig_rect.copy()
    rot_rect.center = rot_image.get_rect().center
    rot_image = rot_image.subsurface(rot_rect).copy()
    return rot_image

def spawn_player(*players):# Tween character up into view, spawn their orbs and then let them move.
    for player in players:
        for orb in player_group:
            if isinstance(orb, Orb) and orb.owner==player: orb.kill()
        for fx in effect_group:
            if fx.owner == player: fx.kill()
        player.lives-=1
        print(f"player spawned-- {player.lives+1} lives left")
        if player.lives<=-1: 
            player.kill()
            continue
        player.rect.x = randint(64,WIDTH-64)
        player.rect.y = HEIGHT
        player.mobile = False
        player.spawn_frame = randint(64,128)

def create_orbs(owner,amt,li,weight,color):
    for i in range(amt):
        orb = Orb(owner,li[i][0],li[i][1],weight[i],color[i])
        player_group.add(orb)

"""Classes"""
class Player(pg.sprite.Sprite):
    def __init__(self,character,x,y,lives,orb_data=[2, [(35,0),(-35,0)], [4,4], [2,2]],keybinds=[pg.K_a,pg.K_d,pg.K_w,pg.K_s,pg.K_j,pg.K_k]):
        pg.sprite.Sprite.__init__(self)
        self.character = character
        self.images = spritesheet((32,48), f'images/player/player_{character}.png')
        self.image = self.images[0]
        self.hitbox = pg.Rect((x,y),(6,6))
        self.rect = self.image.get_rect()
        self.rect.x,self.rect.y = x,y

        self.last_shot = pg.time.get_ticks()
        self.anim = "idle"
        self.frame = 0
        self.focus = False
        self.mobile = True

        self.orb_data = orb_data
        self.keybinds = keybinds
        self.lives = lives
        self.iframe = 0
        self.spawn_frame = 0
    def update(self):
        #Input
        keys = pg.key.get_pressed()
        left,right,up,down=keys[self.keybinds[0]],keys[self.keybinds[1]],keys[self.keybinds[2]],keys[self.keybinds[3]]
        self.shooting,self.focus=keys[self.keybinds[4]],keys[self.keybinds[5]]

        #Movement
        if self.mobile:
            self.rect.x += ((right-left)*4)/(self.focus+1)
            self.rect.y += ((down-up)*4)/(self.focus+1)
        else:
            if self.spawn_frame > 0: 
                self.spawn_frame-=1
                self.rect.y-=1
            else:
                self.iframe=120
                create_orbs(self,self.orb_data[0],self.orb_data[1],self.orb_data[2],self.orb_data[3])
                self.mobile = True

        self.centerx = self.image.get_width()/2
        self.hitbox = pg.Rect((self.rect.x+13,self.rect.y+18),(6,6))

        #Animation
        animations={
            "idle":[1,2,3,4,5,6,7,8],
            "left":[12,13,14,15,16],
            "right":[20,21,22,23,24]
        }
        
        if (left and right) or (self.mobile==False): self.anim = "idle"#Get correct animation
        elif left: self.anim = "left"
        elif right: self.anim = "right"
        else: self.anim = "idle"

        self.frame = ((self.frame + (1/4)) % len(animations[self.anim]))
        self.image = self.images[int(self.frame)+(animations[self.anim][0]-1)]

        self.image.set_alpha(255/(((self.iframe>0)or(self.spawn_frame>0))+1))

        #Focus
        for orb in player_group:
            if isinstance(orb, Orb) and orb.owner == self: # Change offx and offy of each orb.
                if self.focus: 
                    if not any(fx.type=="focus" and fx.owner==self for fx in effect_group):
                        focus_effect=Effect(self,"focus",self.hitbox.x,self.hitbox.y)
                        effect_group.add(focus_effect)

                    orb.offx = orb.offx_og/2
                    orb.offy = -40
                else: 
                    for fx in effect_group:
                        if fx.owner == self: fx.kill()
                    orb.offx,orb.offy = orb.offx_og,orb.offy_og
        
        #Shoot
        time_now = pg.time.get_ticks()
        if (not self.spawn_frame>0) and self.shooting and time_now - self.last_shot > 70: #J shoot, K focus
            bullet1 = Bullet(self,0,self.rect.centerx-12,self.rect.top,200)
            bullet2 = Bullet(self,0,self.rect.centerx+12,self.rect.top,200)
            bullet_group.add(bullet1,bullet2)
            self.last_shot = time_now

        #Collision with Enemies, bullets
        if self.iframe>0 and self.mobile:
            self.iframe-=1
        elif not self.spawn_frame>0: # Can be hit
            for enemy in enemy_group:
                if self.hitbox.colliderect(enemy.hitbox): #Respawn function
                    spawn_player(self)
            for bullet in bullet_group:
                if bullet.owner in enemy_group:
                    if self.hitbox.colliderect(bullet.image.get_rect()):
                        bullet.kill()
                        print("Enemy bullet")

class Enemy(pg.sprite.Sprite):
    def __init__(self,character,x,y,health,hitbox = (0,0,16,16)):
        pg.sprite.Sprite.__init__(self)
        self.images=spritesheet((64,80),f'images/enemies/{character}/main.png')
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.x,self.rect.y=0,0
        self.h0,self.h1,self.h2,self.h3=hitbox[0],hitbox[1],hitbox[2],hitbox[3]
        self.hitbox = pg.Rect(x+self.h0,y+self.h1,self.h2,self.h3)
        
        self.anim = "idle" # Make enemy have an idle animation.
        self.frame = 0
        self.character = character
        self.health = health

        self.followx,self.followy=x,y
        self.floaty=0
        self.floatdir=False
        self.move_timer=256
        self.last_shot = pg.time.get_ticks()
    def update(self):
        #Animation
        animations={
            "idle":([1,2,3,4], 1/12, 1/8),
            "special":([1,2,3,4,5,6,7,8,9,10,11,12])
        }

        self.frame = ((self.frame + animations[self.anim][1]) % len(animations[self.anim][0]))
        self.image = self.images[int(self.frame)+(animations[self.anim][0][0]-1)]

        #Movement
        xvel,yvel=(self.followx-self.rect.x)/10,((self.followy-self.rect.y)/10)+int(self.floaty)
        self.rect.x+=xvel
        self.rect.y+=yvel

        self.floaty+=animations[self.anim][2]*(self.floatdir*2-1)
        if self.floaty>3 or self.floaty<-3:
            self.floatdir = not self.floatdir

        if not self.move_timer>1: 
            self.move_timer=randint(128,512)
            self.followx,self.followy=randint(0,WIDTH-self.rect.w),randint(0,HEIGHT-self.rect.h-(HEIGHT/2))

        else: self.move_timer-=1

        #collision!
        self.hitbox = pg.Rect(self.rect.x+self.h0,self.rect.y+self.h1,self.h2,self.h3)
        for bullet in bullet_group:
            if bullet.owner in player_group:
                if self.hitbox.colliderect(bullet.rect):
                    bullet.kill()
                    self.health-=1
                    if self.health <=0: self.kill()
                    print(self.health)

        #Shooting!
        time_now = pg.time.get_ticks()
        if any(isinstance(player, Player) and not player.spawn_frame> 0 for player in player_group) and time_now - self.last_shot > 160:
            for player in player_group:
                if isinstance(player, Player):
                    angle=(player.centerx-self.rect.centerx,player.rect.y-self.rect.y)#Distance
                    bullet_group.add(Bullet(self,3,self.rect.centerx-5,self.rect.bottom,200,angle,1,True,48))
            self.last_shot = time_now

class Bullet(pg.sprite.Sprite):
    def __init__(self,owner,type,x,y,alpha=256,dir=(0,-1),speed=16,sheet=False,sheet_image=0):
        pg.sprite.Sprite.__init__(self)

        types=[
            ['images/bullets/player_bullet.png'], # 0: reimu bullet
            ['images/bullets/orb_bullet0.png'], # 1: unfocused orb bullet
            ['images/bullets/orb_bullet1.png'], # 2: focused orb bullet
            ['images/bullets/bulletsheet.png',(16,16)], # 2: focused orb bullet
        ]

        if sheet:
            self.images = spritesheet(types[type][1],types[type][0]) 
            self.image = self.images[sheet_image]
        else: self.image = pg.image.load(types[type][0])
        self.image.set_alpha(alpha)
        self.speed=speed = speed
        self.owner=owner

        self.pos = (x, y)
        self.dir = dir
        angle = degrees(atan2(-self.dir[1], self.dir[0]))

        self.image = pg.transform.rotate(self.image, angle)

    def update(self):
        self.pos = (self.pos[0]+self.dir[0]*self.speed,self.pos[1]+self.dir[1]*self.speed)
        self.rect = self.image.get_rect(center = self.pos)
        
        if self.rect.bottom < 0: self.kill()
        if self.rect.top > HEIGHT: self.kill()

class Orb(pg.sprite.Sprite):
    def __init__(self,owner,offx,offy,weight,color=0):
        pg.sprite.Sprite.__init__(self)
        images=spritesheet((15,15),'images/player/orb.png')
        self.image = images[color]
        self.image_og = self.image
        self.angle = 90
        self.rect = self.image.get_rect()

        self.offx_og,self.offy_og=offx,offy
        self.offx,self.offy = offx,offy

        self.last_shot = pg.time.get_ticks()
        self.owner = owner
        self.rect.x,self.rect.y = (owner.rect.x,owner.rect.y+20)
        self.weight = weight
    def update(self):
        #Rotate image
        self.angle-=(self.weight/4)%360
        rot_image = rot_center(self.image_og, self.angle)
        self.image = rot_image

        #Follow owner
        self.rect.x+=((self.owner.rect.centerx-(self.rect.w/self.weight))-self.weight-self.rect.x+self.offx)/self.weight
        self.rect.y+=(self.owner.rect.centery-self.rect.y+self.offy)/self.weight
        
        #shoot
        time_now = pg.time.get_ticks()
        if self.owner.shooting and time_now - self.last_shot > (120-(self.owner.focus*30)): #J shoot, K focus
            bullet1 = Bullet(self.owner,1+self.owner.focus,self.rect.centerx-6,self.rect.top-6,150,((-1+self.owner.focus)/32,-1))
            bullet2 = Bullet(self.owner,1+self.owner.focus,self.rect.centerx+6,self.rect.top-6,150,((1-self.owner.focus)/32,-1))
            bullet_group.add(bullet1,bullet2)
            self.last_shot = time_now

class Effect(pg.sprite.Sprite): #Make generic. Sorry
    def __init__(self,owner,type,x,y,size=(64,64)):
        pg.sprite.Sprite.__init__(self)
        self.images = spritesheet(size,f'images/effects/{type}.png')
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.x,self.rect.y=x,y
        self.owner = owner
        self.type = type

        if type=="focus": #I WAS LAZY. MAKE THIS BETTER LATER
            self.image_og = self.image
            self.angle = 90
            self.spindir=randint(0,1)*2-1
            self.spinspd=randint(1,32)/8
    def update(self):
        if self.type=="focus": #OUGHH SO LAZY
            #Rotate image
            self.angle+=(self.spinspd%360)*self.spindir
            rot_image = rot_center(self.image_og, self.angle)
            self.image = rot_image

            #Follow owner
            self.rect.x=self.owner.hitbox.x-(self.rect.w/2)+(self.owner.hitbox.w/2)
            self.rect.y=self.owner.hitbox.y-(self.rect.h/2)+(self.owner.hitbox.h/2)


"""Init"""
enemy_group = pg.sprite.Group()
effect_group = pg.sprite.Group()
player_group = pg.sprite.Group()
bullet_group = pg.sprite.Group()

player = Player("reimu",380,400,3)
player2 = Player("marisa",500,400,3,[2, [(35,0),(-35,0)], [4,4], [1,1]],[pg.K_LEFT,pg.K_RIGHT,pg.K_UP,pg.K_DOWN,pg.K_PERIOD,pg.K_SLASH])

player_group.add(player,player2)
spawn_player(player,player2)

nazrin=Enemy("nazrin",500,100,2000,(16,8,28,60))
enemy_group.add(nazrin)

"""Game loop"""
running = True
while running: 
    clock.tick(FPS)
    
    update()
    draw()
    for event in pg.event.get(): 
        if event.type == pg.QUIT: running = False