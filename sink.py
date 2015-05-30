# -*- coding: utf-8 -*-
"""
@author: aidan
"""

import pygame
import time
import math
import random

#define the square root of 2, as it's used a lot
sqrt_two = math.sqrt(2)

class Game:

    def __init__(self):
        self._running = True
        self._display_surf = None
        self.size = self.width, self.height = 800, 600
        self.clock_time = time.time()
        self.d_time = 0.
        self._paused = False
        self.pause_time = 0.
        self.pause_time_total = 0.
        self.d_time = 0.
        self.time = time.time()
        self.centre = [self.size[0]/2., self.size[1]/2.]
        self.gameover = False
        self.frame_period = 1./150.
        self.frame_timer = 0.
        self.level_complete = False
        self.gravsize = 40.

    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self.size, pygame.DOUBLEBUF | pygame.HWSURFACE)
        self._running = True

    # execute function,
    def on_execute(self):
        self.camera = Camera([self.centre[0], self.centre[1]])
        if self.on_init() == False:
            self._running = False
        self.level = Level(random.randrange(0,350,10), ["core"])
        self.level.on_execute()
        self.ui = UI()
        # main loop, contains all events and renders
        while( self._running ):
            for event in pygame.event.get():
                self.on_event(event)
            self.frame_timer = time.time() - self.clock_time
            if self.frame_timer > self.frame_period:
                self.d_time, self.clock_time = time.time()-self.clock_time, time.time()
                if not self._paused:
                    self.on_loop(self.d_time)
                self.on_render()
                self.frame_timer -= self.frame_period
        self.on_cleanup()

    #  function to handle pygame.events, executed every loop when an event occurs
    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            pygame.draw.circle(self._display_surf, (100,100,100), pygame.mouse.get_pos(), 15, 0)
        if (event.type == pygame.KEYDOWN) and (event.key == pygame.K_SPACE):
            if not self.gameover:
                if not theGame.level.player.midair: theGame.level.player.jump(self.d_time)
            else: self.restart(90)
        if (event.type == pygame.KEYUP) and (event.key == pygame.K_SPACE):
            theGame.level.player.holding_jump = False
        if (event.type == pygame.KEYDOWN) and (event.key == pygame.K_x):
            self.pause()
        if (event.type == pygame.KEYDOWN) and (event.key == pygame.K_r):
            self.restart(random.randrange(0,350,10))
        if (event.type == pygame.KEYDOWN) and (event.key == pygame.K_f):
            pygame.display.toggle_fullscreen()
        if (event.type == pygame.KEYDOWN) and (event.key == pygame.K_s):
            self.level.slowdown()
    
    # loop function, executed every loop
    def on_loop(self, d_time):
        self.camera.move(d_time)
        for platform in self.level.platform_array:
            platform.move(d_time)
        self.level.player.move(d_time)
        self.camera.move(d_time)
        self.endgame()
        self.level.cycle_platforms()
        self.level.update(d_time)
        if self.level_complete and self.level.player.midair_timer < time.time() - 2:
            self.restart((self.level.player.w_pos + 180) % 360)
            self.level_complete = False

    # render function, executed every loop
    def on_render(self):

        self.level.draw_background()
        #for platform in theGame.level.platform_array:
        #    platform.erase()
        #self.level.player.erase()
        #self._display_surf.fill(self.level.background_colour)
        self.level.player.render()
        for platform in self.level.platform_array:
            platform.render()
        # draw the grav centre
        pygame.draw.circle(theGame._display_surf, (0,0,0), [int(theGame.camera.x_pos),
                                                            int(theGame.camera.y_pos)], int(math.ceil(self.camera.zoom*self.gravsize)), 0)
        self.ui.render()
        pygame.display.flip()
        #pygame.draw.circle(theGame._display_surf, theGame.level.background_colour, [int(theGame.camera.x_pos),
        #                                                    int(theGame.camera.y_pos)], int(math.ceil(self.camera.zoom*self.gravsize))+2, 0)

    # cleanup function, executed after final loop
    def on_cleanup(self):
        pygame.quit()

    # pause the game, ensuring the d_time is correctly determined afterward
    def pause(self):
        if not self._paused:
            self.pause_time = time.time()
        if self._paused:
            self.pause_time = time.time() - self.pause_time
            self.pause_time_total += self.pause_time
            self.clock_time = time.time()
            self.d_time = time.time() - self.clock_time - self.pause_time
        self._paused = not self._paused

    def endgame(self):
        if not self.gameover and self.level.player.r_pos + 25 < math.ceil(self.camera.zoom*self.gravsize):
            self.level.player.r_pos, self.level. player.r_vel = 0,0
            self.level.player.colour = self.level.background_colour
            self.gameover = True
            #self.camera.zoom = 1.
            for platform in self.level.platform_array:
                platform.r_vel = -300
                platform.w_vel *= 2

    def restart(self, player_rpos):
        # set the gameover state back to False in case it was True
        self.gameover = False
        # clear out the level's Platforms and Player
        self.level.cleanup()
        del self.level
        #if the game ended by the Plater finishing the level, initiate a new level of a different type
        if self.level_complete:
            self.level = Level(player_rpos, ["swing"])
        #if the game ended by the player reloading, dying etc., start the core level
        else:
            self.level = Level(player_rpos, ["slippy"])
        self.level.on_execute()

class LevelCore():

    def __init__(self, player_wpos):
        self.type = "core"
        self.min_wsize = 20
        self.background_colour = (250,250,250)
        self.spot_colour = (240, 240, 240)
        self.generate_background()
        self.platform_colour = (0,0,0)
        self.grav = -6000
        self.start_time = time.time()
        # pos, vel, size, colour
        self.platform_r_vel = -30
        self.platform_array = [Platform([250, 30], [self.platform_r_vel, 150], [5, 360], self.platform_colour)]
        self.speedup = 0
        self.player = Player([9000, player_wpos])
        for i in range(10): self.platform_array.append(self.create_platform(self.platform_array[-1]))

    # on execute is kept separate from __init__ as some variables rely on variables not yet initialised
    def on_execute(self):
        self.player.on_execute()

    def generate_background(self):
        self.background = pygame.Rect(0, 0, theGame.size[0], theGame.size[1])
        self.spot_array = []
        for i in range(100):
            self.spot_array.append([random.randrange(1,10000, 1), random.randrange(0,360, 1), random.randrange(5,500,5)])

    def draw_background(self):
        pygame.draw.rect(theGame._display_surf, self.background_colour, self.background, 0)
        for spot in self.spot_array:
            pygame.draw.circle(theGame._display_surf, self.spot_colour, [int(theGame.camera.x_pos + theGame.camera.zoom*spot[0]*math.cos(spot[1])),
                                                                         int(theGame.camera.y_pos - theGame.camera.zoom*spot[0]*math.sin(spot[1]))], int(theGame.camera.zoom*spot[2]))

    def cycle_platforms(self):
        # loop through the platforms, then delete/replace if any are at low enough r_pos
        for platform in self.platform_array:
            if platform.r_pos < platform.r_size + theGame.gravsize:
                self.platform_array.remove(platform)
                #if not theGame.gameover: self.platform_array.append(self.create_platform(self.platform_array[-1]))
                # update the player's above_platform array
                self.player.above_platform = [(x.r_pos < abs(self.player.r_pos)) for x in theGame.level.platform_array]

    def cleanup(self):
        for platform in self.platform_array:
            del platform
        del self.player

    def create_platform(self, previous_platform):
        w_vel = -math.copysign(random.randrange(50, 150, 25), previous_platform.w_vel)
        r_pos = previous_platform.r_pos + 100
        # pos, w_vel, size, colour
        return Platform([r_pos, (self.player.w_pos + 180)%360 - float(w_vel)*sqrt_two*math.sqrt((abs(float(self.player.r_pos) -float(r_pos)))/float(abs(self.grav)))],
                        [self.platform_r_vel, w_vel],
                        [5, random.randrange(self.min_wsize,340,10)],
                        self.platform_colour)

    # update function run every loop. To be used by different level types
    def update(self, d_time):
        pass


class Level(LevelCore):

    def __init__(self, player_wpos, type):
        LevelCore.__init__(self, player_wpos)
        #based on type, make relevant changes to the level.
        self.type = type

        if "heartbeat" in self.type:
            self.background_colour = (250,230,230)
            self.spot_colour = (240, 200, 200)
            self.platform_colour = (200,0,0)
            for platform in self.platform_array:
                platform.colour = self.platform_colour
                platform.r_pos += 100
            self.start_time = time.time()
            self.platform_period = 0.8

        if "swing" in self.type:
            self.background_colour = (230,250,230)
            self.spot_colour = (220, 240, 220)
            self.platform_colour = (0,200,0)
            for platform in self.platform_array:
                platform.colour = self.platform_colour
                platform.r_pos += 100
            self.start_time = time.time()
            self.platform_period = 1.5

        if "slippy" in self.type:
            self.background_colour = (230,200,230)
            self.spot_colour = (220,190,220)
            self.platform_colour = (100,0,100)
            for platform in self.platform_array:
                platform.colour = self.platform_colour
                platform.r_pos += 100
                platform.slippery = True
            self.start_time = time.time()
            self.platform_period = 1.5

    def update(self, d_time):
        if "heartbeat" in self.type:
            for platform in self.platform_array:
                cycle_time = math.sin(((time.time() - self.start_time )%self.platform_period)/self.platform_period*2*math.pi)
                if not theGame.gameover:
                    platform.r_vel = theGame.level.platform_r_vel + 50000*d_time*(cycle_time)

        if "swing" in self.type:
            for platform in self.platform_array:
                cycle_time = (time.time() - self.start_time )%self.platform_period
                if not theGame.gameover:
                    platform.w_vel = platform.w_vel0 + 10000*d_time*(cycle_time - self.platform_period/2.)

class Platform():

    def __init__(self, pos, vel, size, colour):
        self.r_size, self.w_size = size[0], size[1]
        self.r_vel, self.w_vel = vel[0], vel[1]
        self.r_pos, self.w_pos = pos
        self.w_vel0 = self.w_vel
        self.colour = colour
        self.pointlist = [[0,0],[0,0],[0,0]]
        self.slippery = False

    def render(self):
        if int(math.ceil(theGame.camera.zoom*self.r_size)) < theGame.camera.zoom*self.r_pos:
            d_w = [(x*5 - self.w_size/2 - self.w_pos)*math.pi/180. for x in range(self.w_size/5+1)]
            self.pointlist = [[theGame.camera.x_pos + theGame.camera.zoom*self.r_pos*math.cos(x),
                          theGame.camera.y_pos + theGame.camera.zoom*self.r_pos*math.sin(x)] for x in d_w]
            self.pointlist.reverse()
            self.pointlist += [[theGame.camera.x_pos + theGame.camera.zoom*(self.r_pos-theGame.camera.zoom*20)*math.cos(x),
                          theGame.camera.y_pos + theGame.camera.zoom*(self.r_pos-theGame.camera.zoom*20)*math.sin(x)] for x in d_w]
            pygame.draw.polygon(
                theGame._display_surf,
                self.colour,
                #True,
                self.pointlist,
                0)
            del d_w
        # self.colour = theGame.level.platform_colour

    def erase(self):
        pygame.draw.polygon(
            theGame._display_surf,
            theGame.level.background_colour,
            #True,
            self.pointlist,
            False
        )

    def move(self, d_time):
        # if not theGame.gameover: self.r_vel = -10*(theGame.level.player.r_pos/100.)**1.5
        #self.w_vel = self.w_vel0 + math.copysign(theGame.level.speedup, self.w_vel0)
        self.w_pos += self.w_vel*d_time
        self.w_pos %= 360
        self.r_pos += self.r_vel*d_time


class Player():

    def __init__(self, pos):
        self.size = 20
        self.r_pos, self.w_pos = pos[0],pos[1]
        self.r_vel, self.w_vel = 0,0
        self.r_acc, self.w_acc = 0,0
        self.colour = (0,100,255)
        self.midair = True
        self.midair_timer = 0.
        self.holding_jump = True
        self.trail_spawn_time = time.time()
        self.trail_period = 0.02
        self.update_pointlist()
        self.trail_list = [[self.x_centre, self.y_centre]]
        for x in range(70): self.trail_list.append([self.x_centre, self.y_centre])

    def update_pointlist(self):
        self.x_centre = (self.r_pos+self.size/2.)*math.cos(self.w_pos*math.pi/180)
        self.y_centre = (self.r_pos+self.size/2.)*math.sin(self.w_pos*math.pi/180)
        self.pointlist = [[theGame.camera.x_pos + theGame.camera.zoom*(self.x_centre + (self.size/sqrt_two)*math.cos(self.w_pos*math.pi/180-math.pi/4)),
                     theGame.camera.y_pos - theGame.camera.zoom*(self.y_centre + (self.size/sqrt_two)*math.sin(self.w_pos*math.pi/180-math.pi/4))],
                  [theGame.camera.x_pos + theGame.camera.zoom*(self.x_centre - (self.size/sqrt_two)*math.sin(self.w_pos*math.pi/180-math.pi/4)),
                     theGame.camera.y_pos - theGame.camera.zoom*(self.y_centre + (self.size/sqrt_two)*math.cos(self.w_pos*math.pi/180-math.pi/4))],
                  [theGame.camera.x_pos + theGame.camera.zoom*(self.x_centre - (self.size/sqrt_two)*math.cos(self.w_pos*math.pi/180-math.pi/4)),
                     theGame.camera.y_pos - theGame.camera.zoom*(self.y_centre - (self.size/sqrt_two)*math.sin(self.w_pos*math.pi/180-math.pi/4))],
                  [theGame.camera.x_pos + theGame.camera.zoom*(self.x_centre + (self.size/sqrt_two)*math.sin(self.w_pos*math.pi/180-math.pi/4)),
                     theGame.camera.y_pos - theGame.camera.zoom*(self.y_centre - (self.size/sqrt_two)*math.cos(self.w_pos*math.pi/180-math.pi/4))]]
        if (time.time() - self.trail_spawn_time - theGame.pause_time) > self.trail_period:
            self.trail_list.append([int(self.x_centre),
                                    int(self.y_centre)])
            self.trail_list.pop(0)
            self.trail_spawn_time += self.trail_period

    # on execute is kept separate from __init__ as some variables rely on variables not yet initialised
    def on_execute(self):
        self.above_platform = [(x.r_pos < abs(self.r_pos)) for x in theGame.level.platform_array]

    def render(self):
        self.update_pointlist()
        s = 5
        ds = 0.3
        pygame.draw.lines(theGame._display_surf,
                              (100,200, 255),
                              False,
                              [[theGame.camera.x_pos + theGame.camera.zoom*self.x_centre, theGame.camera.y_pos - theGame.camera.zoom*self.y_centre],
                               [theGame.camera.x_pos + theGame.camera.zoom*self.trail_list[-1][0], theGame.camera.y_pos - theGame.camera.zoom*self.trail_list[-1][1]]],
                              int(theGame.camera.zoom*(s + len(self.trail_list)*ds)))
        for i, trail_pos in enumerate(self.trail_list[:-2]):
            pygame.draw.lines(theGame._display_surf,
                              (100,200, 255),
                              False,
                              [[theGame.camera.x_pos + theGame.camera.zoom*trail_pos[0], theGame.camera.y_pos - theGame.camera.zoom*trail_pos[1]],
                               [theGame.camera.x_pos + theGame.camera.zoom*self.trail_list[i+1][0], theGame.camera.y_pos - theGame.camera.zoom*self.trail_list[i+1][1]]],
                              int(theGame.camera.zoom*s))
            s += ds
        del s, ds
        pygame.draw.polygon(theGame._display_surf, self.colour, self.pointlist, 0)

    def erase(self):
        pygame.draw.polygon(theGame._display_surf, theGame.level.background_colour, self.pointlist, 0)

    def move(self, d_time):
        if not theGame.gameover:
            if self.midair:
                if self.holding_jump and (time.time() - self.midair_timer) < 2:
                    self.r_acc = theGame.level.grav/2
                else:
                    self.r_acc = theGame.level.grav
                self.r_vel += self.r_acc*d_time
                self.r_pos += self.r_vel*d_time
            if not self.midair:
                self.platform.colour = self.colour
                if not self.platform.slippery: self.w_pos += self.platform.w_vel*d_time
                else: self.w_pos += self.platform.w_vel*d_time * 1.2
                self.w_pos %= 360
                self.r_pos += self.platform.r_vel*d_time
            # update the platform_above list. Note: this assumes the number of platforms in the list has been updated elsewhere
            above_platform_new = [(x.r_pos < abs(self.r_pos)) for x in theGame.level.platform_array]
            # if the array is different from the previous iteration, a collision may have occurred
            if not self.above_platform == above_platform_new:
                # note: this currently assumes the Player will only ever collide with one platform at a time
                # this will pass in the instance of the platform potentially being collided with to collision_check
                if not self.collision_check(theGame.level.platform_array[[i for i, j in enumerate(above_platform_new) if j != self.above_platform[i]][0]]):
                    self.above_platform = list(above_platform_new)
            else: self.above_platform = list(above_platform_new)
            del above_platform_new
            #if the platform is slippery, check if the player has slid off the edge of it
            if not self.midair:
                if self.platform.slippery:
                    if abs(((self.w_pos - self.platform.w_pos) + 180) % 360 - 180) > self.platform.w_size/2:
                        self.midair = True
                        self.w_pos += math.copysign(3, self.platform.w_vel)
                        self.platform.colour = theGame.level.platform_colour

    #this function performs the collision if the player is in the right range of w_pos, and returns True if so
    def collision_check(self, platform):
        # we already know that the Player has passed through the r_pos of the Platform, but need to check
        # if it is also within the range of angles of the Platform
        if abs(((self.w_pos - platform.w_pos) + 180) % 360 - 180) < platform.w_size/2:
            # pass in the platform being collided with and whether the collision was from above or below
            theGame.camera.shake_mag, theGame.camera.shake_dur = min(abs(self.r_vel/30.),60), 0.2
            theGame.camera.shake_start_time = time.time()
            theGame.camera._shaking = True
            self.collide(platform, self.r_pos < platform.r_pos)
            return True
        else:
            return False

    def collide(self, platform, above):
        self.platform = platform
        if above:
            self.r_vel = 0
            self.midair = False
            self.r_pos = platform.r_pos + 1
            self.above_platform = [(x.r_pos < abs(self.r_pos)) for x in theGame.level.platform_array]
        if not above:
            self.r_pos = platform.r_pos -1
            self.r_vel = -self.r_vel
            self.above_platform = [(x.r_pos < abs(self.r_pos)) for x in theGame.level.platform_array]

    def jump(self, d_time):
        #it has already been verified that player is NOT midair
        self.midair = True
        self.midair_timer = time.time()
        self.holding_jump = True
        #if the player is on the top platform, initiate level completion
        if self.above_platform[-1] == True:
            self.r_vel = 8000
            theGame.level.grav = 0
            theGame.level_complete = True
        #if the player is on a platform beneath the top one, perform a standard jump
        else:
            self.r_vel = 1000
        self.platform.colour = theGame.level.platform_colour


# Camera class, which determines the reference point from which everything should be rendered.
class Camera():

    def __init__(self, pos):
        self.pos = [self.x_pos, self.y_pos] = [pos[0], pos[1]]
        self.zoom = 1.5
        self.shake_cd = 0.
        self.shake_mag, self.shake_dur = 0., 0.
        self._shaking = False
        self.shake_time = 0.
        self.x_shake, self.y_shake = 0., 0.

    def move(self, d_time):
        self.x_pos = theGame.centre[0] - theGame.camera.zoom*(theGame.level.player.r_pos*math.cos(theGame.level.player.w_pos*math.pi/180))/3 + self.x_shake
        self.y_pos = theGame.centre[1] + theGame.camera.zoom*(theGame.level.player.r_pos*math.sin(theGame.level.player.w_pos*math.pi/180))/3 + self.y_shake
        if self._shaking: self.shake(d_time)
        if not theGame.gameover:
            #max to avoid divide by zero
            self.zoom = 10./max(0.001, math.sqrt(abs(theGame.level.player.r_pos)))
        # elif theGame.gameover: self.zoom = 3

    def shake(self, d_time):
        #shake the camera with magnitude mag for dur seconds
        if self.shake_time < self.shake_dur:
            self.x_shake = random.random() * self.shake_mag
            self.y_shake = random.random() * self.shake_mag
            self.shake_time += d_time
        else:
            self._shaking = False
            self.shake_time = 0
            self.x_shake, self.y_shake = 0., 0.

# ---------------------UI (user interface) class
class UI():
    def __init__(self):
        self.tech_font = pygame.font.SysFont("monospace", 15)
        self.fps_time = theGame.clock_time
        self.fps = 0
        self.fps_running = 0
    def redraw(self):
        pygame.draw.rect(theGame._display_surf, theGame.level.background_colour,
                         pygame.Rect(0.5*theGame.width, 0.9*theGame.height, 100,100),0)
    def render(self):
        self.render_fps()
        self.render_mousexy()
    def render_fps(self):
        if ( (theGame.clock_time - self.fps_time) > 1 ):
            self.fps_time = theGame.clock_time
            self.fps, self.fps_running = self.fps_running, 0
        fps = self.tech_font.render(str(self.fps)+" FPS", 1, (0,0,0))
        theGame._display_surf.blit(fps, (0.5*theGame.width, 0.9*theGame.height))
        del fps
        self.fps_running += 1
    def render_mousexy(self):
        pass

if __name__ == "__main__" :
    theGame = Game()
    theGame.on_execute()