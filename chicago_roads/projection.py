import math
import pygame, sys
from collections import defaultdict
from math import *
from traffic import *
import shapefile

# CONFIG
local_zips = ["60615", "60637"]
cars_per_second = .5
screen_width  = 700
screen_height = 700


# The data we are gathering
roads = []
intersections = defaultdict(list)
entrances     = defaultdict(bool) 
min_x, min_y, max_x, max_y = float("inf"),float("inf"),float("-inf"),float("-inf")

sf = shapefile.Reader("./Transportation")
NAME_COL = 4
ID_COL = 7
F_CROSS_COL = 34
T_CROSS_COL = 36
R_ZIP_COL = 29
L_ZIP_COL = 30

i = 0
while i < sf.numRecords:
  sr = sf.shapeRecord(i)
  shape = sr.shape
  record = sr.record
  
  #result = ""
  #t_pts = map(trans, shape.points)
  
  if record[R_ZIP_COL] in local_zips or record[L_ZIP_COL] in local_zips:
    
    roads.append(i)
    
    # We don't want to add intersections to deadends
    if not record[F_CROSS_COL] == 0:
      intersections[t_int(shape.points[0])].append(i)
    if not record[T_CROSS_COL] == 0:
      intersections[t_int(shape.points[-1])].append(i)
    
    # Figure out the zip-code bounding box
    min_x = min(min_x, shape.bbox[0])
    min_y = min(min_y, shape.bbox[1])
    max_x = max(max_x, shape.bbox[2])
    max_y = max(max_y, shape.bbox[3])
  else:
    # If this road is at a point we care about, but not in our zip codes, we have detected an edge point for our map. 
    # We will need these to create cars on later
    if not record[F_CROSS_COL] == 0:
      entrances[t_int(shape.points[0])] = True
    if not record[T_CROSS_COL] == 0:
      entrances[t_int(shape.points[-1])] = True
  i += 1




x_scale = float(screen_width)/(max_x-min_x)
y_scale = float(screen_height)/(max_y-min_y)
def scale(point):
  return ((point[0]-min_x)*x_scale, screen_height - (point[1]-min_y)*y_scale)

# Slightly-shifted points for the purpose of adding other-directional roads
shift_by = -5
def shift_line(p_from, p_to):
  dx = p_from[0] - p_to[0]
  dy = p_from[1] - p_to[1]
  
  angle = math.atan2((-1)*dx, dy)
  
  x_offset = shift_by*math.cos(angle)
  y_offset = shift_by*math.sin(angle)
  
  return [(p_to[0] + x_offset, p_to[1] + y_offset),(p_from[0] + x_offset, p_from[1] + y_offset)] 
  




intersections_dict = {}
world = World()
world.size = (screen_width, screen_height)

for point in intersections.keys():
  intersection = Intersection()
  intersection.always_green = True
  if entrances[t_int(point)]:
    intersection.create_car = True
    intersection.destroy_car = True
    intersection.new_cars_per_second = cars_per_second
  
  intersections_dict[t_int(point)] = intersection
  world.intersections.append(intersection)

for r_id in roads:
  scaled_points = map(scale, sf.shape(r_id).points)
  from_point, to_point = sf.shape(r_id).points[0], sf.shape(r_id).points[-1]
  
  from_intersection = intersections_dict.get(t_int(from_point))
  to_intersection   = intersections_dict.get(t_int(to_point))
    
  truncated_points = [scaled_points[0], scaled_points[-1]]
  shifted_points = shift_line(truncated_points[0], truncated_points[1])
  
  road1 = Road()
  road1.set_line(truncated_points[0], truncated_points[1])
  world.roads.append(road1)
  
  road2 = Road()
  road2.set_line(shifted_points[0], shifted_points[1])
  world.roads.append(road2)
  
  if not from_intersection:
    print "Missing intersection?"
    from_intersection = Intersection()
    world.intersections.append(from_intersection)
  
  from_intersection.add_in_road(road2, green=True)
  from_intersection.add_out_road(road1)
   
  if not to_intersection:
    print "Missing intersection?"
    to_intersection = Intersection()
    world.intersections.append(to_intersection)
    
  to_intersection.add_in_road(road1, green=True)
  to_intersection.add_out_road(road2)

run_traffic(world)

