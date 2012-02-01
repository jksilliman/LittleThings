{- 
 - Simplified implementation of the State monad.  The real implementation
 - is in the Control.Monad.State module: using that is recommended for real 
 - programs.
 -}
module UCState where

data State s a = State { runState :: s -> (a, s) }

instance Monad (State s)
    where
        {-
         - return lifts a function x up into the state monad, turning it into
         -  a state function that just passes through the state it receives
         -}
        return x = State ( \s -> (x, s) )
        
        {- 
         - The >>= combinator combines two functions p and f, and 
         -  gives back a new function (Note: p is originally wrapped in the 
         -  State monad)
         -
         - p: a function that takes the initial state (from right at the start
         - of the monad chain), and gives back a new state and value, 
         - corresponding to the result of the chain up until this >>=
         - f: a function representing the rest of the chain of >>='s
         -}
        (State p) >>= f = State ( \initState -> 
                                  let (res, newState) = p initState
                                      (State g) = f res
                                  in g newState )

-- Get the state
get :: State s s  
get = State ( \s -> (s, s) )

-- Update the state
put :: s -> State s ()
put s = State ( \_ -> ((), s))

