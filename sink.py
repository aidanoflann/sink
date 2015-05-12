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

    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self.size, pygame.DOUBLEBUF | pygame.HWSURFACE)
        self._running = True

    # execute function,
    def on_execute(self):
        self.camera = Camera([self.centre[0], self.centre[1]])
        self.level = Level(random.randrange(0,350,10))
        self.level.on_execute()
        if self.on_init() == False:
            self._running = False
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
            if not self.gameover: theGame.level.player.jump(self.d_time)
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
        for thingy in self.level.thingy_array:
            thingy.move(d_time)
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
        background = pygame.Rect(0, 0, self.size[0], self.size[1])
        pygame.draw.rect(theGame._display_surf, self.level.background_colour, background, 0)
        #self._display_surf.fill(self.level.background_colour)
        self.level.player.render()
        for platform in self.level.platform_array:
            platform.render()
        for thingy in self.level.thingy_array:
            thingy.render()
        # draw the grav centre
        pygame.draw.circle(theGame._display_surf, (0,0,0), [int(theGame.camera.x_pos),
                                                            int(theGame.camera.y_pos)], int(math.ceil(self.camera.zoom*10)), 0)
        self.ui.render()
        pygame.display.flip()

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
        if not self.gameover and self.level.player.r_pos < math.ceil(self.camera.zoom*10)*0.25:
            self.level.player.r_pos, self.level. player.r_vel = 0,0
            self.level.player.colour = self.level.background_colour
            self.gameover = True
            self.camera.zoom = 2.
            for platform in self.level.platform_array:
                platform.r_vel = -300
                platform.w_vel *= 2

    def restart(self, player_rpos):
        # set the gameover state back to False in case it was True
        self.gameover = False
        # clear out the level's Platforms and Player
        self.level.cleanup()
        del self.level
        self.level = Level(player_rpos)
        self.level.on_execute()

    def endLevel(self):
        self.restart()

class Level():

    def __init__(self, player_wpos):
        self.background_colour = (250,250,250)
        self.platform_colour = (0,0,0)
        self.grav = -6000
        self.start_time = time.time()
        # pos, w_vel, size, colour
        self.platform_array = [Platform([250, 30], 150, [5, 360], self.platform_colour)]
        self.thingy_array = []
        self.num_slowdowns = 0
        self.slowdown_amount = 100
        self.speedup = 0
        self.player = Player([9000, player_wpos])
        for i in range(15): self.platform_array.append(self.create_platform(self.platform_array[-1]))

    # on execute is kept separate from __init__ as some variables rely on variables not yet initialised
    def on_execute(self):
        self.player.on_execute()
        #self.create_thingy()

    def cycle_platforms(self):
        # loop through the platforms, then delete/replace if any are at low enough r_pos
        for platform in self.platform_array:
            if platform.r_pos < 8:
                # if platform.has_thingy:
                #     theGame.level.thingy_array.remove(platform.thingy)
                #     del platform.thingy
                #     if not theGame.gameover:theGame.level.create_thingy()
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
                        w_vel,
                        [5, random.randrange(20,340,10)],
                        self.platform_colour)

    # update variables that need to be recalculated every loop
    def update(self, d_time):
        pass
        #self.speedup += self.speedup_rate*d_time

    def slowdown(self):
        self.speedup = 0

    def create_thingy(self):
        #determine a platform index which will be given a thingy
        platform_index = random.randrange(max(2,self.player.above_platform.index(False) + 1),
                                          min(len(self.platform_array), self.player.above_platform.index(False) + 5),1)
        self.thingy_array.append(Thingy(self.platform_array[platform_index]))
        self.platform_array[platform_index].has_thingy = True
        self.platform_array[platform_index].thingy = self.thingy_array[-1]
        del platform_index

class Platform():

    def __init__(self, pos, w_vel, size, colour):
        self.r_size, self.w_size = size[0], size[1]
        self.r_vel, self.w_vel = -30, w_vel
        self.r_pos, self.w_pos = pos
        self.w_vel0 = self.w_vel
        self.colour0 = colour
        self.colour = self.colour0
        self.has_thingy = False

    def render(self):
        if int(math.ceil(theGame.camera.zoom*self.r_size)) < theGame.camera.zoom*self.r_pos:
            # pygame.draw.arc(theGame._display_surf,
            #             self.colour,
            #             pygame.Rect(theGame.camera.x_pos-theGame.camera.zoom*self.r_pos,
            #                         theGame.camera.y_pos-theGame.camera.zoom*self.r_pos,
            #                         theGame.camera.zoom*2*self.r_pos,
            #                         theGame.camera.zoom*2*self.r_pos),
            #             (self.w_pos - self.w_size/2)*math.pi/180.,
            #             (self.w_pos + self.w_size/2)*math.pi/180.,
            #             int(math.ceil(theGame.camera.zoom*self.r_size)))
            d_w = [(x*5 - self.w_size/2 - self.w_pos)*math.pi/180. for x in range(self.w_size/5+1)]
            pointlist = [[theGame.camera.x_pos + theGame.camera.zoom*self.r_pos*math.cos(x),
                          theGame.camera.y_pos + theGame.camera.zoom*self.r_pos*math.sin(x)] for x in d_w]
            pointlist.reverse()
            pointlist += [[theGame.camera.x_pos + theGame.camera.zoom*(self.r_pos-theGame.camera.zoom*20)*math.cos(x),
                          theGame.camera.y_pos + theGame.camera.zoom*(self.r_pos-theGame.camera.zoom*20)*math.sin(x)] for x in d_w]
            pygame.draw.aalines(
                theGame._display_surf,
                self.colour,
                True,
                pointlist,
                True)
            del d_w, pointlist
        self.colour = self.colour0

    def move(self, d_time):
        # if not theGame.gameover: self.r_vel = -10*(theGame.level.player.r_pos/100.)**1.5
        self.w_vel = self.w_vel0 + math.copysign(theGame.level.speedup, self.w_vel0)
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
        self.update_pointlist()
        self.midair_timer = 0.
        self.holding_jump = False

    def update_pointlist(self):
        self.pointlist = [[theGame.camera.x_pos + theGame.camera.zoom*((self.r_pos+self.size/2.)*math.cos(self.w_pos*math.pi/180) + (self.size/sqrt_two)*math.cos(self.w_pos*math.pi/180-math.pi/4)),
                     theGame.camera.y_pos - theGame.camera.zoom*((self.r_pos+self.size/2.)*math.sin(self.w_pos*math.pi/180) + (self.size/sqrt_two)*math.sin(self.w_pos*math.pi/180-math.pi/4))],
                  [theGame.camera.x_pos + theGame.camera.zoom*((self.r_pos+self.size/2.)*math.cos(self.w_pos*math.pi/180) - (self.size/sqrt_two)*math.sin(self.w_pos*math.pi/180-math.pi/4)),
                     theGame.camera.y_pos - theGame.camera.zoom*((self.r_pos+self.size/2.)*math.sin(self.w_pos*math.pi/180) + (self.size/sqrt_two)*math.cos(self.w_pos*math.pi/180-math.pi/4))],
                  [theGame.camera.x_pos + theGame.camera.zoom*((self.r_pos+self.size/2.)*math.cos(self.w_pos*math.pi/180) - (self.size/sqrt_two)*math.cos(self.w_pos*math.pi/180-math.pi/4)),
                     theGame.camera.y_pos - theGame.camera.zoom*((self.r_pos+self.size/2.)*math.sin(self.w_pos*math.pi/180) - (self.size/sqrt_two)*math.sin(self.w_pos*math.pi/180-math.pi/4))],
                  [theGame.camera.x_pos + theGame.camera.zoom*((self.r_pos+self.size/2.)*math.cos(self.w_pos*math.pi/180) + (self.size/sqrt_two)*math.sin(self.w_pos*math.pi/180-math.pi/4)),
                     theGame.camera.y_pos - theGame.camera.zoom*((self.r_pos+self.size/2.)*math.sin(self.w_pos*math.pi/180) - (self.size/sqrt_two)*math.cos(self.w_pos*math.pi/180-math.pi/4))]]
    # on execute is kept separate from __init__ as some variables rely on variables not yet initialised

    def on_execute(self):
        self.above_platform = [(x.r_pos < abs(self.r_pos)) for x in theGame.level.platform_array]

    def render(self):
        pygame.draw.polygon(theGame._display_surf, self.colour, self.pointlist, 0)

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
                self.w_pos += self.platform.w_vel*d_time
                self.w_pos %= 360
                self.r_pos += self.platform.r_vel*d_time
            self.update_pointlist()
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

    #this function performs the collision if the player is in the right range of w_pos, and returns True if so
    def collision_check(self, platform):
        # first check if the platform has a thingy, and if so, if we're colliding with it
        if platform.has_thingy:
            if abs(((self.w_pos - platform.thingy.w_pos) + 180) % 360 - 180) < platform.thingy.w_size/2:
                theGame.level.slowdown()
                theGame.level.thingy_array.remove(platform.thingy)
                del platform.thingy
                platform.has_thingy = False
                if not theGame.gameover: theGame.level.create_thingy()
        # we already know that the Player has passed through the r_pos of the Platform, but need to check
        # if it is also within the range of angles of the Platform
        if abs(((self.w_pos - platform.w_pos) + 180) % 360 - 180) < platform.w_size/2:
            # pass in the platform being collided with and whether the collision was from above or below
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
        if not self.midair:
            if self.above_platform[-1] == True:
                self.r_vel = 8000
                self.midair = True
                self.midair_timer = time.time()
                theGame.level.grav = 0
                theGame.level_complete = True
            else:
                self.r_vel = 1000
                self.midair = True
                self.midair_timer = time.time()
                self.holding_jump = True


# Camera class, which determines the reference point from which everything should be rendered.
class Camera():

    def __init__(self, pos):
        self.pos = [self.x_pos, self.y_pos] = [pos[0], pos[1]]
        self.zoom = 1.5
        self.shake_cd = 0.

    def move(self, d_time):
        self.x_pos = theGame.centre[0] - theGame.camera.zoom*(theGame.level.player.r_pos*math.cos(theGame.level.player.w_pos*math.pi/180))/3
        self.y_pos = theGame.centre[1] + theGame.camera.zoom*(theGame.level.player.r_pos*math.sin(theGame.level.player.w_pos*math.pi/180))/3
        if not theGame.gameover:
            #max to avoid divide by zero
            self.zoom = 10./max(0.001, math.sqrt(abs(theGame.level.player.r_pos)))
        # elif theGame.gameover: self.zoom = 3

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

#For now, Thingys have been removed. I'll keep the class for the time being in case it's needed later
class Thingy():

    def __init__(self, platform):
        self.platform = platform
        self.colour = (0,200,0)
        self.w_size = 40
        self.r_size = 3
        self.pos = self.r_pos, self.w_pos = platform.r_pos, platform.w_pos + 180
        self.r = 10

    def move(self, d_time):
        self.w_pos += self.platform.w_vel*d_time
        self.w_pos %= 360
        self.r_pos += self.platform.r_vel*d_time

    def render(self):
        pygame.draw.arc(theGame._display_surf,
                        self.colour,
                        pygame.Rect(theGame.camera.x_pos-theGame.camera.zoom*self.r_pos,
                                    theGame.camera.y_pos-theGame.camera.zoom*self.r_pos,
                                    theGame.camera.zoom*2*self.r_pos,
                                    theGame.camera.zoom*2*self.r_pos),
                        (self.w_pos - self.w_size/2)*math.pi/180.,
                        (self.w_pos + self.w_size/2)*math.pi/180.,
                        int(math.ceil(theGame.camera.zoom*self.r_size)))


if __name__ == "__main__" :
    theGame = Game()
    theGame.on_execute()