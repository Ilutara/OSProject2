import threading
import time
import random
from queue import Queue

num_tellers = 3
num_customers = 15

door_sem = threading.Semaphore(2)
manager_sem = threading.Semaphore(1)
safe_sem = threading.Semaphore(2)

bank_open = threading.Event()  
print_lock = threading.Lock()  # to make sure we print the events in the correct order
teller_ready_lock = threading.Lock()
teller_ready_count = 0

customer_events = {}
customer_teller_map = {}

customer_queue = Queue()

customers_served_lock = threading.Lock()
customers_served = 0

def print_log(thread_type, thread_id, other_type=None, other_id=None, message=""):
    with print_lock:
        if other_type and other_id is not None:
            print(f"{thread_type} {thread_id} [{other_type} {other_id}]: {message}")
        else:
            print(f"{thread_type} {thread_id}: {message}")

def teller_thread(teller_id):
    global teller_ready_count, customers_served
    
    with teller_ready_lock:
        teller_ready_count += 1
        print_log("Teller", teller_id, message="ready to serve")
        if teller_ready_count == num_tellers:
            bank_open.set()
    
    while True:
        with customers_served_lock:
            if customers_served >= num_customers:
                break
        
        try:
            customer_id = customer_queue.get(timeout=0.5)
        except:
            continue
        
        customer_teller_map[customer_id] = teller_id
        
        events = customer_events[customer_id]
        events['teller_ready'].set()
        
        safe_sem.acquire()
        time.sleep(random.uniform(0.010, 0.050))
        safe_sem.release()

        events['customer_left'].wait()
        events['customer_left'].clear()


def customer_thread(customer_id):
    global customers_served
    
    wait_time = random.uniform(0, 0.100)
    time.sleep(wait_time)
    
    bank_open.wait()
    
    door_sem.acquire()
    print_log("Customer", customer_id, message="enters bank through door")
    door_sem.release()
    
    print_log("Customer", customer_id, message="gets in line")
    
    customer_events[customer_id] = {
        'teller_ready': threading.Event(),
        'customer_left': threading.Event(),
    }
    
    customer_queue.put(customer_id)
    
    customer_events[customer_id]['teller_ready'].wait()
    customer_events[customer_id]['teller_ready'].clear()
    
    teller_id = customer_teller_map[customer_id]
    
    print_log("Customer", customer_id, "Teller", teller_id, "goes to teller")
    
    print_log("Customer", customer_id, "Teller", teller_id, "thanks teller and leaves")
    customer_events[customer_id]['customer_left'].set()
    
    print_log("Customer", customer_id, message="leaves bank through door")
    
    with customers_served_lock:
        customers_served += 1


def main():
    teller_threads = []
    for i in range(num_tellers):
        t = threading.Thread(target=teller_thread, args=(i,))
        t.start()
        teller_threads.append(t)
    
    customer_threads = []
    for i in range(num_customers):
        t = threading.Thread(target=customer_thread, args=(i,))
        t.start()
        customer_threads.append(t)
    
    for t in customer_threads:
        t.join()
    
    for t in teller_threads:
        t.join()
    
    print("DONE")

if __name__ == "__main__":
    main()
