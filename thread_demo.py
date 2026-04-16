import threading

# Shared Data
gLock = threading.Semaphore(1)
gCount = 0

def threadcode(id):
    global gCount # I want to change the value of gCount
    gLock.acquire()
    print("Thread " + str(id) + " has count " + str(gCount))
    gCount = gCount+1
    gLock.release()

# Create threads
threads = []
for i in range(0,5):
    threads.append(threading.Thread(target=threadcode,args=(i,)))
    threads[i].start()

# Wait for threads
for i in range(0,5):
    threads[i].join()
