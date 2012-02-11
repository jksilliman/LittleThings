import time
import random
import math
import pygame, sys

from math import *
from pygame.locals import *
from collections import deque


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

CAR_RADIUS = 2.0 # Graphical
CAR_LENGTH = 6.0 # Simulatory

REACTION_TIME = 0.5 # Can this be combined with SAFETY_TIME?
SAFETY_TIME = 1
DECELERATION = -20
ACCELERATION = 5

FPS = 30.0
SFP = 1.0/FPS

# For antialiased-ish circles
def draw_circle(surface, color, center, radius):
  points = []
  for i in xrange(0, 10):
    points.append((center[0] + radius*math.cos(i*2.0*math.pi/10.0),  center[1] + radius*math.sin(i*2.0*math.pi/10.0)))

  pygame.draw.polygon(surface, color, points)


def draw_square(surface, color, center, half_side):
  pygame.draw.rect(surface, color, (center[0] - half_side, center[1] - half_side, half_side*2, half_side*2))

def t_int(tup):
  return (int(tup[0]), int(tup[1]))


class Car(object):
  def __init__(self):
    self.position = 0
    self.speed = 0
    self.target_speed = 0
    self.road = None

  def draw(self, surface):
    pos_x = self.position/self.road.length * (self.road.end[0]-self.road.start[0]) + self.road.start[0]
    pos_y = self.position/self.road.length * (self.road.end[1]-self.road.start[1]) + self.road.start[1]
    draw_square(surface, BLACK, (pos_x, pos_y), CAR_RADIUS)


  # Takes into account safety due to sudden deceleration of next car
  # other in front of self
  def time_to_crash(self, other):
    worst_speed = max(0, other.speed + DECELERATION*REACTION_TIME)
    if self.speed <= worst_speed:
      return float("inf")
    else:
      return (other.position - self.position) / (self.speed - worst_speed) 

  def update(self, step, next_car):
    
    if self.target_speed < self.speed: 
      dv = DECELERATION
    elif next_car and SAFETY_TIME > self.time_to_crash(next_car):
      dv = DECELERATION
    elif self.target_speed > self.speed:
      dv = ACCELERATION
    else:
      dv = 0

    self.speed = max(0, step*dv + self.speed)

    self.position += step*self.speed


class Road(object):
  def __init__(self):
    self.start = (0, 0)
    self.end = (0, 0)

    self.length = 0

    # Front = left, Back = right
    self.cars = deque()
    self.intersection = None
  
  def last_car(self):
    if len(self.cars) == 0:
      return None
    return self.cars[-1]

  def set_line(self, start_at, end_at):
    self.start = start_at
    self.end = end_at
    self.length = sqrt((self.end[0] - self.start[0]) ** 2 + (self.end[1] - self.start[1]) ** 2) 

  def enter_car(self, car):
    self.cars.append(car)
    car.road = self
    car.position = 0

  def draw(self, surface):
    pygame.draw.line(surface, BLACK, t_int(self.start), t_int(self.end))
    for c in self.cars:
      c.draw(surface)

    # DRAW LIGHT
    if self in self.intersection.green_lights:
      self.draw_light(surface, GREEN)
    elif self in self.intersection.yellow_lights:
      self.draw_light(surface, YELLOW)
    else:
      self.draw_light(surface, RED)


  def draw_light(self, surface, color):
    # May have to deal better with light placement, based on direction of road
    draw_square(surface, color, (self.end[0]-10,self.end[1]-10), 3)

  def update(self, step):
    prev = None # Confusingly, prev is the next car in front of the current car (but the previous one to be processed)
    
    i = 0
    while i < len(self.cars):
      c = self.cars[i]
      
      # If we are at the front of the road and we cannot cross
      if prev == None and self.intersection and not self.intersection.can_cross(self, None):
        # Add an imaginary car to force cars to slow for intersection
        prev = Car()
        prev.position = self.length
        prev.speed = 0
        prev.target_speed = 0

      # If we are in the front of this road 
      if prev == None and len(self.intersection.out_roads) > 0:
        # ROUTING
        next_road = self.intersection.out_roads[0]
        next_car = next_road.last_car()
        
        if next_car:
          # Imaginary car in our current road coordinates to mock car on next road
          prev = Car()
          prev.speed = next_car.speed
          prev.position = self.length + next_car.position

      c.update(step, prev)

      # CAR COLLISION PREVENTION
      if prev and c.position > prev.position - CAR_LENGTH:    # Minor collision
        c.position = prev.position - CAR_LENGTH
        c.speed    = 0
      
      # END OF ROAD
      if c.position > self.length:

        if self.intersection and self.intersection.can_cross(self, None):
          # ENTER INTERSECTION
          
          self.cars.popleft()
          i -= 1
          self.intersection.transfer_car(c)

        else:
          # STOP AT INTERSECTION
          c.position = self.length - CAR_LENGTH
          c.speed = 0
      
      if c.road == self:
        prev = c
      else:
        prev = None
      i += 1
    

class Intersection(object):
  def __init__(self):
    self.create_car = False  # Is this intersection a creator or destroyer of cars?
    self.new_cars_per_second = 0
    self.destroy_car = False

    self.in_roads = []
    self.out_roads = []

    self.green_lights = []
    self.yellow_lights = []
    # RED LIGHT IS IMPLICIT

  def transfer_car(self, car):
    if self.destroy_car:
      return
    
    road = self.out_roads[0] # NEED TO ROUTE
    if road:
      next_car = road.last_car()
      if next_car:
        next_car_pos = next_car.position
      else:
        next_car_pos = float("inf")
      excess = car.position - car.road.length
      road.enter_car(car)
      car.position = min(excess, next_car_pos)

  # Is any road open?
  def can_cross(self, from_road, to_road):
    return (from_road in self.green_lights) # and to_road not backed up
            

  # Needs to manage green-light and create cars
  def update(self, step):
    if self.create_car:
      car_prob = self.new_cars_per_second * step 
      # Is this probability any good mathematically?
      if car_prob > random.random():
        new_car_road = random.choice(self.out_roads)
        new_car = Car()
        new_car.speed = random.randrange(20, 40)
        new_car.target_speed = new_car.speed
        new_car_road.enter_car(new_car)

  def draw(self, surface):
    pass

# RED/GREEN (No yellow yet!)
class BasicLight(Intersection):
  def __init__(self):
    Intersection.__init__(self)
    self.green_light_length = 0
    self.current_light_length = 0

  def update(self, step):
    Intersection.update(self,step)
    self.current_light_length += step
    if self.current_light_length > self.green_light_length:
      self.current_light_length = 0
      if len(self.in_roads) == 1: # We just want to turn light on and off
        if len(self.green_lights) == 1:
          self.green_lights = []
        else:
          self.green_lights = [self.in_roads[0]]




class World(object):
  def __init__(self):
    self.roads = []
    self.intersections = []

  def update(self, step):
    for r in self.roads:
      r.update(step)
    for i in self.intersections:
      i.update(step)

  def draw(self, surface):
    for r in self.roads:
      r.draw(surface)
    for i in self.intersections:
      i.draw(surface)
      


pygame.init()

windowSurface = pygame.display.set_mode((400, 400), 0, 32)
pygame.display.set_caption('Traffic Simulator')

world = World()

road1 = Road()
road1.set_line((0, 200), (200, 200))
world.roads.append(road1)

road2 = Road()
road2.set_line((200,200), (200, 400))
world.roads.append(road2)

intersection = Intersection()
intersection.create_car = True
intersection.new_cars_per_second = 1
intersection.out_roads.append(road1)
world.intersections.append(intersection)

intersection = BasicLight()
intersection.green_light_length = 10
intersection.destroy_car = False
intersection.in_roads = [road1]
intersection.out_roads = [road2]
road1.intersection = intersection
world.intersections.append(intersection)

intersection = Intersection()
intersection.destroy_car = True
intersection.in_roads = [road2]
intersection.green_lights = [road2]
road2.intersection = intersection
world.intersections.append(intersection)


while True:
  for event in pygame.event.get():
    if event.type == QUIT:
      pygame.quit()
      sys.exit()
  windowSurface.fill(WHITE)
  world.update(SFP)
  world.draw(windowSurface)
  pygame.display.update()

  time.sleep(SFP)
