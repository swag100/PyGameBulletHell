import pygame as pg
from math import degrees, atan2
from random import randint

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

    # pg.draw.rect(screen, (0,255,255), player.hitbox) # draw Hitbox (testing!)
    #for enemy in enemy_group: pg.draw.rect(screen, (0,255,255), enemy.hitbox) # draw Enemy hitboxes (SUPER testing!)
    pg.display.flip() # Finally, flip display.

def update():
    for enemy in enemy_group: enemy.update()
    for i in player_group: i.update()
    for bullet in bullet_group: bullet.update()

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

def spawn_player(*players):# Tween character up into view, spawn their orbs and then let them move.
    for player in players:
        for orb in player_group:
            if isinstance(orb, Orb) and orb.owner==player: orb.kill()
        player.rect.x = randint(64,WIDTH-64)
        player.rect.y = HEIGHT
        player.mobile = False
        player.spawn_frame = 64

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
        self.hitbox = pg.Rect((x,y),(8,8))
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
            self.rect.x += ((right-left)*4)/(self.shooting+1)
            self.rect.y += ((down-up)*4)/(self.shooting+1)
        else:
            if self.spawn_frame > 0: 
                self.spawn_frame-=1
                self.rect.y-=1
            else:
                self.iframe=120
                create_orbs(self,self.orb_data[0],self.orb_data[1],self.orb_data[2],self.orb_data[3])
                self.mobile = True

        self.centerx = self.image.get_width()/2
        self.hitbox = pg.Rect((self.rect.x+10,self.rect.y+18),(8,8))

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
        self.image.set_alpha(255/((self.iframe>0)+1))

        #Focus
        for orb in player_group:
            if isinstance(orb, Orb) and orb.owner == self: # Change offx and offy of each orb.
                if self.focus: 
                    orb.offx = orb.offx_og/2
                    orb.offy = -40
                else: orb.offx,orb.offy = orb.offx_og,orb.offy_og
        
        #Shoot
        time_now = pg.time.get_ticks()
        if self.shooting and time_now - self.last_shot > 70: #J shoot, K focus
            bullet1 = Bullet(self,0,self.rect.centerx-12,self.rect.top,200)
            bullet2 = Bullet(self,0,self.rect.centerx+12,self.rect.top,200)
            bullet_group.add(bullet1,bullet2)
            self.last_shot = time_now

        #Collision with Enemies, bullets
        if self.iframe>0 and self.mobile:
            self.iframe-=1
        else:
            for enemy in enemy_group:
                if self.hitbox.colliderect(enemy.hitbox): #Respawn function
                    spawn_player(self)
            for bullet in bullet_group:
                if bullet.owner in enemy_group:
                    if self.hitbox.colliderect(bullet.rect):
                        bullet.kill()
                        print("Enemy bullet")

class Enemy(pg.sprite.Sprite):
    def __init__(self,character,x,y,health,hitbox = (0,0,16,16)):
        pg.sprite.Sprite.__init__(self)
        self.images=spritesheet((64,80),f'images/{character}/main.png')
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.x,self.rect.y=x,y
        self.hitbox = pg.Rect(x+hitbox[0],y+hitbox[1],hitbox[2],hitbox[3],)
        
        self.anim = "idle" # Make enemy have an idle animation.
        self.frame = 0
        self.character = character
        self.health = health
    def update(self):
        #Animation
        animations={
            "idle":[1],
            "special":[1,2,3,4,5,6,7,8,9,10,11,12]
        }

        self.frame = ((self.frame + (1/4)) % len(animations[self.anim]))
        self.image = self.images[int(self.frame)+(animations[self.anim][0]-1)]

        #collision!
        for bullet in bullet_group:
            if bullet.owner in player_group:
                if self.hitbox.colliderect(bullet.rect):
                    bullet.kill()
                    self.health-=1
                    print(self.health)

class Bullet(pg.sprite.Sprite):
    def __init__(self,owner,type,x,y,alpha=256,dir=(0,-5),speed=3):
        pg.sprite.Sprite.__init__(self)

        types=[
            ['images/bullets/player_bullet.png'], # 0: reimu bullet
            ['images/bullets/orb_bullet0.png'], # 1: unfocused orb bullet
            ['images/bullets/orb_bullet1.png'], # 2: focused orb bullet
        ]

        self.image = pg.image.load(types[type][0])
        self.image.set_alpha(alpha)
        self.speed=speed
        self.owner=owner

        self.pos = (x, y)
        self.dir = dir

        angle = degrees(atan2(-self.dir[1], self.dir[0]))

        self.image = pg.transform.rotate(self.image, angle)

    def update(self):
        self.pos = (self.pos[0]+self.dir[0]*self.speed,self.pos[1]+self.dir[1]*self.speed)
        self.rect = self.image.get_rect(center = self.pos)
        
        if self.rect.bottom < 0: self.kill()

class Orb(pg.sprite.Sprite):
    def __init__(self,owner,offx,offy,weight,color=0):
        pg.sprite.Sprite.__init__(self)
        images=spritesheet((16,16),'images/player/orb.png')
        self.image = images[color]
        self.rect = self.image.get_rect()

        self.offx_og,self.offy_og=offx,offy
        self.offx,self.offy = offx,offy

        self.last_shot = pg.time.get_ticks()
        self.owner = owner
        self.rect.x,self.rect.y = (owner.rect.x,owner.rect.y+20)
        self.weight = weight
    def update(self):
        self.rect.x+=((self.owner.rect.centerx-(self.rect.w/self.weight))+3-self.weight-self.rect.x+self.offx)/self.weight
        self.rect.y+=(self.owner.rect.centery-self.rect.y+self.offy)/self.weight
        
        #shoot
        time_now = pg.time.get_ticks()
        if self.owner.shooting and time_now - self.last_shot > (120-(self.owner.focus*30)): #J shoot, K focus
            bullet1 = Bullet(self.owner,1+self.owner.focus,self.rect.centerx-6,self.rect.top-6,150,((-1+self.owner.focus)/7,-5))
            bullet2 = Bullet(self.owner,1+self.owner.focus,self.rect.centerx+6,self.rect.top-6,150,((1-self.owner.focus)/7,-5))
            bullet_group.add(bullet1,bullet2)
            self.last_shot = time_now


"""Init"""
enemy_group = pg.sprite.Group()
player_group = pg.sprite.Group()
bullet_group = pg.sprite.Group()

player = Player("reimu",380,400,3)
player2 = Player("marisa",500,400,3,[2, [(35,0),(-35,0)], [4,4], [1,1]],[pg.K_LEFT,pg.K_RIGHT,pg.K_UP,pg.K_DOWN,pg.K_RSHIFT,pg.K_RCTRL])
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