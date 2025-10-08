import random
import copy as cp
import time
from os import system

print("\nGuess 4 digit code or SUFFER THE CONSEQUENCES!!!! (1-6)")
print(" ○ = one element is in the code but in the wrong place\n ● = one element is in the code and in the correct place\n")

code = [random.randint(1,6) for _ in range(4)]
code_t = cp.deepcopy(code)
notWin = True
turn = 0
moves = [
    r"""
    o   
   /|\  
   / \  
  """, r"""
  \ o /  
    |    
   / \  
  """, r"""
   _ o 
    /\ 
   | \ 
  """, r"""
    
    ___\o
   /)  | 
  """, r"""
  __|  
     \o 
     ( \
  """, r"""
   \ /
    | 
   /o\
  """, r"""
       |__
     o/   
    / )   
  """, r"""
        
   o/__ 
   |  (\
  """,r"""
   o _
   /\ 
   / |
  """, r"""
  \ o /
    |  
   / \ 
  """
]
def dance():
    for step in moves:
        print(step)
        print("\nYou Win!!!")
        time.sleep(0.2)
        system('clear')


while turn < 12:
    print("Guess?:", end=' ')
    guess = input()
    code = cp.deepcopy(code_t)
    if(len([x for x in guess if x in '123456']) == 4):
        if(guess == code):
            print("you win!!!")
            break
        guess = [int(x) for x in guess]

        c = ''
        for i in range(4):
            if guess[i] == code[i]:
                code[i] = -1
                guess[i] = -99
                c+='●'
                

        print(code)
        for i in range(4):
            if guess[i] in code:
                c+='○'
                code[code.index(guess[i])] = -10
                guess[i] = -99
                print(code)

        print(f"\n{c}\n")

        turn += 1
        if(sum(code) == -4):
            print("you win!!! on turn", turn)
            notWin = False

            while True:
                dance()
            break
    
    else:
        print("\n>:( Invalid input; please enter 4 digits from 1-6\n")

    print("you loose ha ha")


        


