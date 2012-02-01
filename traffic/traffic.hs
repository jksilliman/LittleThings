module Main where
import Prelude hiding (length)
import Graphics.Gloss
import Graphics.Gloss.Interface.Simulate
import System.Random
import RandState

fps = 20
num_cars = 20
road_length = 800
max_speed = 20

road_x = -400
road_y = 0

main = do  
    gen <- getStdGen
    let sfp = (1.0 / (fromIntegral fps)) 
    simulate (InWindow "Traffic" (800, 600) (10, 10))
           black               -- background color
           fps                 -- number of steps per second
           (initial_road gen)  -- initial world
           render              -- function to convert world to a Picture
           (update_road sfp)   -- function to step the world one iteration


render road = Pictures $ map (render_car road) (cars road)
render_car road car = Color white
  $ Translate ((position car) + road_x) road_y
  $ Circle 3

data Car = Car {
  position :: Float,
  speed    :: Float
} deriving (Show)
data Road = Road {
  length :: Float,
  cars   :: [Car]
} deriving (Show)



-- evolve :: ViewPort -> Float -> World -> World
update_road timestep _ _ road = road { cars = map (update_car timestep road) (cars road) }
update_car timestep road car = car { position = wrap ((position car) + (speed car) * timestep) }
  where
    remainder x d = (x/d - (fromIntegral (floor (x/d))))*d
    wrap = \x -> remainder x (length road)

initial_road = populate_road empty_road num_cars

empty_road = Road {
  length = road_length,
  cars   = []
}

populate_road road num_cars gen = withRandom gen (do
    let car_data = randRs [(0, (length road)), (max_speed/2, (max_speed))]
    cars_data <- sequence (replicate num_cars car_data)
    let cars = map new_car cars_data
    return (road { cars = cars })
  )
  where 
    new_car [p, s] = Car { position = p, speed = s }



 
