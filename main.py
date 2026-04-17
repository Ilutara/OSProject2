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

def log(thread_type, thread_id, other_type=None, other_id=None, message=""):
    with print_lock:
        if other_type and other_id is not None:
            print(f"{thread_type} {thread_id} [{other_type} {other_id}]: {message}")
        else:
            print(f"{thread_type} {thread_id}: {message}")

def teller_thread(teller_id):
    global teller_ready_count, customers_served
    
    with teller_ready_lock:
        teller_ready_count += 1
        log("Teller", teller_id, message="ready to serve")
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
        
        events['transaction_given'].wait()
        events['transaction_given'].clear()

        transaction_type = events['transaction_type']

        if transaction_type == "WITHDRAWAL":
            log("Teller", teller_id, "Customer", customer_id, "goes to the manager")
            manager_sem.acquire()
            log("Teller", teller_id, "Customer", customer_id, "getting permission from manager")
            time.sleep(random.uniform(0.005, 0.030))
            log("Teller", teller_id, "Customer", customer_id, "got permission from manager")
            manager_sem.release()


        log("Teller", teller_id, "Customer", customer_id, "goes to the safe")
        safe_sem.acquire()
        log("Teller", teller_id, "Customer", customer_id, "enters safe")
        time.sleep(random.uniform(0.010, 0.050))
        log("Teller", teller_id, "Customer", customer_id, f"completes {transaction_type.lower()} in safe")
        log("Teller", teller_id, "Customer", customer_id, "leaves safe")
        safe_sem.release()

        log("Teller", teller_id, "Customer", customer_id, "informs customer transaction is complete")
        events['transaction_complete'].set()

        events['customer_left'].wait()
        events['customer_left'].clear()


def customer_thread(customer_id):
    global customers_served

    transaction_type = random.choice(["DEPOSIT", "WITHDRAWAL"])
    log("Customer", customer_id, message=f"decides to make a {transaction_type.lower()}")    

    wait_time = random.uniform(0, 0.100)
    time.sleep(wait_time)
    
    bank_open.wait()
    
    door_sem.acquire()
    log("Customer", customer_id, message="enters through door")
    door_sem.release()
    
    log("Customer", customer_id, message="is in line")
    
    customer_events[customer_id] = {
        'teller_ready': threading.Event(),
        'customer_left': threading.Event(),
        'transaction_type': transaction_type,
        'transaction_given': threading.Event(),
        'transaction_complete': threading.Event()
    }
    
    customer_queue.put(customer_id)
    
    customer_events[customer_id]['teller_ready'].wait()
    customer_events[customer_id]['teller_ready'].clear()
    
    teller_id = customer_teller_map[customer_id]
    
    log("Customer", customer_id, "Teller", teller_id, "goes to teller")
    log("Customer", customer_id, "Teller", teller_id, f"requests {transaction_type.lower()}")
    
    customer_events[customer_id]['transaction_given'].set()

    customer_events[customer_id]['transaction_complete'].wait()
    customer_events[customer_id]['transaction_complete'].clear()

    log("Customer", customer_id, "Teller", teller_id, "thanks teller and leaves")
    customer_events[customer_id]['customer_left'].set()
    
    log("Customer", customer_id, message="leaves through door")
    
    with customers_served_lock:
        customers_served += 1


def main():
    teller_threads = []

    print("START")
    print("There are {num_tellers} tellers and {num_customers} customers")

    for i in range(num_tellers):
        t = threading.Thread(target=teller_thread, args=(i,))
        t.start()
        teller_threads.append(t)
    
    bank_open.wait()
    print("Bank open!")

    customer_threads = []
    for i in range(num_customers):
        t = threading.Thread(target=customer_thread, args=(i,))
        t.start()
        customer_threads.append(t)
    
    for t in customer_threads:
        t.join()
    
    for t in teller_threads:
        t.join()
    
    print("\nBank is now closed")
    print(f"All {num_customers} customers have been served.")
    print("DONE")

if __name__ == "__main__":
    main()
