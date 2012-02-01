module RandState where
import UCState
import System.Random

-- In order to generate pseudo-random numbers, need to pass around generator
--  state in State monad
type RandState a = State StdGen a

-- runRandom runs a RandState monad, given an initial random number generator
runRandom :: RandState a -> StdGen -> a
runRandom (State f) s = res
    where (res, state) = f s

withRandom = flip runRandom

-- rand is a helper function that generates a random instance of any
--  type in the Random class, using the RandState monad.
rand :: Random a => RandState a
rand = do
    gen <- get
    let (x, gen') = random gen
    put gen'
    return x

randR :: Random a => (a, a) -> RandState a
randR range = do
  gen <- get
  let (x, gen') = randomR range gen
  put gen'
  return x

randRs :: Random a => [(a, a)] -> RandState [a]
randRs ranges = mapM randR ranges


