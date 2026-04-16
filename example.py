import threading
import random

wait = [None, threading.Semaphore(1), threading.Semaphore(0)]

gameOver = False
value = 0
maxVal = random.randint(7,20)

print("Max Val: ", end='')
print(maxVal)

def customer(i):
    global value
    global gameOver
    while value < maxVal:
      wait[i].acquire()
      if gameOver:
          return
      if value == 0:
          value += 1
      elif 2*value > maxVal:
          value += 1
      else:
          value *= 2
      print("Customer ", end='')
      print(i, end='')
      print(": ", end='')
      print(value)
      if value >= maxVal:
          gameOver = True
      wait[i%2+1].release() 

t1 = threading.Thread(target=customer, args=(1,))
t2 = threading.Thread(target=customer, args=(2,))

t1.start()
t2.start()

t1.join()
t2.join()
