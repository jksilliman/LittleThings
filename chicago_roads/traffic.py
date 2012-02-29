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
# FUCK COLORBLINDNESS
YELLOW = BLUE #(255, 255, 0) 


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

def stopped_car_at(length):
  c = Car()
  c.position = length
  c.speed = 0
  c.target_speed = 0
  return c

class Car(object):
  def __init__(self):
    self.position = 0
    self.speed = 0
    self.target_speed = 0
    self.road = None
    self.prev_road = None
    self.road_choice = None
    self.has_stopped = False # Keeps track of whether we have stopped at stop-sign
  
  def change_road(self, new_road):
    self.prev_road = self.road
    self.road = new_road

  def draw(self, surface):
    draw_square(surface, BLACK, self.screen_position(), CAR_RADIUS)

  def screen_position(self):
    return self.road.road_pos_to_screen(self.position)

  # Takes into account safety due to sudden deceleration of next car
  # other in front of self
  def time_to_crash(self, other):
    worst_speed = max(0, other.speed + DECELERATION*REACTION_TIME)
    if self.speed <= worst_speed:
      return float("inf")
    else:
      return (other.position - self.position) / (self.speed - worst_speed) 

  def time_to_intersection(self):
    if self.speed > 0:    
      return (self.road.length - self.position) / self.speed
    else:
      return float("inf")

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



  # HAVE SMARTER ROUTING
  def next_turn(self):
    return self.road_choice

  # No u-turns
  def allowed_road(self, r):
    uturn = (r.to_intersection == self.road.from_intersection)
    return (not uturn)

  def after_enter_road(self):
    self.has_stopped = False

    # Chooses the next turn to make, currently at random
    self.road_choice = None
    # Filter out roads we aren't allowed to turn onto
    road_choices = [r for r in self.road.to_intersection.out_roads if self.allowed_road(r)]
    if len(road_choices) > 0:
      self.road_choice = random.choice(road_choices)



  def hard_stop(self, position):
    self.position = position - CAR_LENGTH
    self.speed    = 0



class Road(object):
  def __init__(self):
    self.start = (0, 0)
    self.end = (0, 0)

    self.length = 0

    # Front = left, Back = right
    self.cars = deque()
    self.to_intersection = None
    self.from_intersection = None
  
  def last_car(self):
    if len(self.cars) == 0:
      return None
    return self.cars[-1]

  def road_pos_to_screen(self, pos):
    pos_x = pos/self.length * (self.end[0]-self.start[0]) + self.start[0]
    pos_y = pos/self.length * (self.end[1]-self.start[1]) + self.start[1]
    return (pos_x, pos_y)

  def set_line(self, start_at, end_at):
    self.start = start_at
    self.end = end_at
    self.length = sqrt((self.end[0] - self.start[0]) ** 2 + (self.end[1] - self.start[1]) ** 2) 

  def enter_car(self, car):
    self.cars.append(car)
    car.change_road(self)
    car.position = 0
    car.after_enter_road()

  def draw(self, surface):
    pygame.draw.line(surface, BLACK, t_int(self.start), t_int(self.end))
    for c in self.cars:
      c.draw(surface)

    # DRAW LIGHT
    if not self.to_intersection.always_green:
      if self in self.to_intersection.green_lights:
        self.draw_light(surface, GREEN)
      elif self in self.to_intersection.yellow_lights:
        self.draw_light(surface, YELLOW)
      elif self in self.to_intersection.red_lights:
        self.draw_light(surface, RED)
      elif self in self.to_intersection.stop_signs:
        self.draw_stop_sign(surface)

  # The standard position for drawing a light/sign icon
  # May have to deal better with light placement, based on direction of road
  def signal_pos(self):
    return self.road_pos_to_screen(self.length - CAR_LENGTH)

  def draw_stop_sign(self, surface):
    draw_circle(surface, RED, self.signal_pos(), 3)
  def draw_light(self, surface, color):
    draw_square(surface, color, self.signal_pos(), 3)

  def update(self, step):
    prev = None # Confusingly, prev is the next car in front of the current car (but the previous one to be processed)
    
    i = 0
    while i < len(self.cars):
      c = self.cars[i]
      
      # If we are at the front of the road and we cannot cross
      if prev == None and not self.to_intersection.can_cross(c):
        # Add an imaginary car to force cars to slow for intersection
        prev = stopped_car_at(self.length)

      # If we are in the front of this road 
      if prev == None and len(self.to_intersection.out_roads) > 0:
        next_road = c.next_turn()
        if next_road:
          next_car = next_road.last_car()
          
          if next_car:
            # Imaginary car in our current road coordinates to mock car on next road
            prev = Car()
            prev.speed = next_car.speed
            prev.position = self.length + next_car.position

      c.update(step, prev)

      # CAR COLLISION PREVENTION (HACK, CARS SHOULD SLOW DOWN)
      if prev and c.position > prev.position - CAR_LENGTH:
        # print "CAR COLLISION"
        c.hard_stop(prev.position)
      
      # END OF ROAD
      if c.position > self.length:
        if self.to_intersection.can_cross(c):
          # ENTER INTERSECTION
          self.cars.popleft()
          self.to_intersection.transfer_car(c)

          i -= 1
        else:
          # STOP AT INTERSECTION (HACK, CARS SHOULD SLOW DOWN)
          # print "LIGHT COLLISION"
          c.hard_stop(self.length)
      
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

    # A list of each road which approaches a <blank> at this intersection
    self.green_lights = []
    self.yellow_lights = []
    self.red_lights = []
    self.stop_signs = []

    self.green_light_length = 0
    self.yellow_light_length = 0
    self.current_light_length = 0

    self.always_green = False

  def add_in_road(self, road, green=False, stop=False):
    assert road.to_intersection == None
    road.to_intersection = self
    self.in_roads.append(road)
    if green:
      self.green_lights.append(road)
    elif stop:
      self.stop_signs.append(road)
    else:
      self.red_lights.append(road)

  def add_out_road(self, road):
    assert road.from_intersection == None
    road.from_intersection = self
    self.out_roads.append(road)

  def transfer_car(self, car):
    if self.destroy_car:
      return
    
    road = car.next_turn()
    assert road in self.out_roads

    next_car = road.last_car()
    if next_car:
      next_car_pos = next_car.position
    else:
      next_car_pos = float("inf")
    excess = car.position - car.road.length
    road.enter_car(car)
    car.position = min(excess, next_car_pos)

  # Can this car go through this intersection to where it wants to go?
  def can_cross(self, car):
    if (car.road in self.stop_signs) and (car.speed == 0 or car.has_stopped):
      car.has_stopped = True
      return True
    return (car.road in self.green_lights) or (car.road in self.yellow_lights and car.time_to_intersection() < (self.yellow_light_length - self.current_light_length)) 
  
  # Needs to manage green-light and create cars
  def update(self, step):
    if self.always_green:
      #self.green_lights = self.in_roads
      self.yellow_lights = []
      self.red_lights = []
    else:
      self.current_light_length += step
      if len(self.green_lights) > 0 and self.current_light_length > self.green_light_length:
        self.current_light_length = 0
        self.yellow_lights = self.green_lights
        self.green_lights = []

      if len(self.yellow_lights) > 0  and self.current_light_length > self.yellow_light_length:
        self.current_light_length = 0
        (self.red_lights, self.green_lights) = (self.yellow_lights, self.red_lights)
        self.yellow_lights = []


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



class World(object):
  def __init__(self):
    self.roads = []
    self.intersections = []
    self.size = (400, 400)    
    
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
      

def run_traffic(world):
  pygame.init()

  windowSurface = pygame.display.set_mode(world.size, 0, 32)
  pygame.display.set_caption('Traffic Simulator')

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



if __name__ == "__main__":
  world = World()

  # IN ROAD
  road1 = Road()
  road1.set_line((0, 210), (200, 210))
  world.roads.append(road1)

  # OUT ROAD
  road2 = Road()
  road2.set_line((200,210), (200, 400))
  world.roads.append(road2)

  # SECOND IN ROAD
  road3 = Road()
  road3.set_line((200, 100), (200, 200))
  world.roads.append(road3)

  # SECOND OUT ROAD
  road4 = Road()
  road4.set_line((210,210), (400, 210))
  world.roads.append(road4)

  # A SECOND SET OF ROADS

  # IN ROAD
  road5 = Road()
  road5.set_line((200, 200), (0, 200))
  world.roads.append(road5)

  # OUT ROAD
  road6 = Road()
  road6.set_line((210,400), (210, 210))
  world.roads.append(road6)

  # SECOND IN ROAD
  road7 = Road()
  road7.set_line((210, 200), (210, 100))
  world.roads.append(road7)

  # SECOND OUT ROAD
  road8 = Road()
  road8.set_line((400,200), (210, 200))
  world.roads.append(road8)



  # TRANSVERSE ACROSS TOP ROADS, GIVING THEM STOP SIGNS

  road9 = Road()
  road9.set_line((0, 100), (200, 100))
  world.roads.append(road9)

  road10 = Road()
  road10.set_line((210, 100), (400, 100))
  world.roads.append(road10)

  road11 = Road()
  road11.set_line((200, 0), (200, 100))
  world.roads.append(road11)

  road12 = Road()
  road12.set_line((210, 100), (210, 0))
  world.roads.append(road12)


  intersection = Intersection()
  intersection.create_car = True
  intersection.always_green = True
  intersection.new_cars_per_second = 1
  intersection.add_out_road(road9)
  world.intersections.append(intersection)

  intersection = Intersection()
  intersection.always_green = True
  intersection.destroy_car = True
  intersection.add_in_road(road10, green=True)
  world.intersections.append(intersection)

  intersection = Intersection()
  intersection.always_green = True
  intersection.add_in_road(road9, green=True)
  intersection.add_in_road(road7, stop=True)
  intersection.add_in_road(road11, stop=True)
  intersection.add_out_road(road10)
  intersection.add_out_road(road12)
  intersection.add_out_road(road3)
  world.intersections.append(intersection)


  intersection = Intersection()
  intersection.create_car = True
  intersection.destroy_car = True
  intersection.always_green = True
  intersection.new_cars_per_second = 1
  intersection.add_out_road(road1)
  intersection.add_in_road(road5, green=True)
  world.intersections.append(intersection)

  intersection = Intersection()
  intersection.create_car = True
  intersection.destroy_car = True
  intersection.always_green = True
  intersection.new_cars_per_second = 1
  intersection.add_out_road(road11)
  intersection.add_in_road(road12, green=True)
  world.intersections.append(intersection)

  intersection = Intersection()
  intersection.green_light_length = 10
  intersection.yellow_light_length = 3
  intersection.destroy_car = False
  intersection.add_in_road(road1, green=True)
  intersection.add_in_road(road3)
  intersection.add_in_road(road6)
  intersection.add_in_road(road8, green=True)
  intersection.add_out_road(road2)
  intersection.add_out_road(road4)
  intersection.add_out_road(road5)
  intersection.add_out_road(road7)
  world.intersections.append(intersection)

  intersection = Intersection()
  intersection.new_cars_per_second = 1
  intersection.create_car = True
  intersection.destroy_car = True
  intersection.always_green = True
  intersection.add_in_road(road2, green=True)
  intersection.add_out_road(road6)
  world.intersections.append(intersection)

  intersection = Intersection()
  intersection.new_cars_per_second = 1
  intersection.create_car = True
  intersection.destroy_car = True
  intersection.always_green = True
  intersection.add_in_road(road4, green=True)
  intersection.add_out_road(road8)
  world.intersections.append(intersection)

  run_traffic(world)

