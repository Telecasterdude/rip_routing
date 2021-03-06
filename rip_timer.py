"""
rip_timer.py, Author: jbr185, 66360439, dwa110, 28749539
"""

import threading
import datetime
from time import sleep
from rip_sockets import send_routes_to_neighbours
from random import randint  



def create_triggered_update(router):
    """
    Creates a triggered update in a new thread but only if one is required 
    according to the RIP specification. Sometimes if a periodic update is close 
    """
    time_offset = randint(1, 5)
    current_time = datetime.datetime.now()
    
    #if there is already a triggered update waiting to go -- @@ should there be a buffer here in case the triggered update is just about to go?
    if router.next_triggered_update != None:
        print("Nothing to do")
        pass #andreas said to send everything in a triggered update, so there is nothing to do
        
    #if a periodic update would happen before our triggered update, then don't bother creating a triggered update
    elif router.next_periodic_update < current_time + datetime.timedelta(seconds=time_offset):
        print("Triggered update will go out with the periodic update")
        pass #all routes will be updated in the periodic update, so there is nothing to do
    
    #a triggered update must be created 1 to 5 seconds from now
    else:
        print("Triggered update will go out at", datetime.datetime.now() + datetime.timedelta(seconds=time_offset))
        router.next_triggered_update = datetime.datetime.now() + datetime.timedelta(seconds=time_offset)
        threading.Timer(time_offset, send_routes_to_neighbours, [router, router.routing_table.keys(), True]).start()




def rip_garbage_collection(router):
    """
    Looks through the routing table once per second looking for packets which 
    have timed out and packets which need to be garbage collected.
    """   
    #to minimise delays from computing, start new timer immediately
    timer = threading.Timer(1, rip_garbage_collection, [router])
    timer.start()
    
    is_triggered_update_nessesary = False
    router_ids_to_be_deleted = []
    current_time = datetime.datetime.now()
    for router_id in router.routing_table.keys():
        
        #check if the timeout timer has expired
        if router.routing_table[router_id].time <= current_time:
            
            #if timer has expired and there is no garbage collection timer, then add a garbage collection timer
            if router.routing_table[router_id].garbage_collection_time is None:
                router.routing_table[router_id].cost = 16
                router.routing_table[router_id].route_change_flag = True
                router.routing_table[router_id].garbage_collection_time = current_time + datetime.timedelta(seconds=router.update_time * 4) 
            
            #if there is an expired garbage collection timer, then delete the entry
            elif router.routing_table[router_id].garbage_collection_time <= current_time:
                #signal that this routing table entry needs to be deleted
                router_ids_to_be_deleted.append(router_id)
                
        #sometimes the timeout timer can be non-expired (hence the first if statement above does not trigger), 
        #but the garbage collection timer can be expired. This occurs when garbage collection timers are set from 
        #receiving an update that changes the metric to 16
        elif router.routing_table[router_id].garbage_collection_time is not None and router.routing_table[router_id].garbage_collection_time <= current_time:
            #signal that this routing table entry needs to be deleted
            router_ids_to_be_deleted.append(router_id)            
            
                
        #if the route has changed, then it now must be advertised in a triggered response
        if router.routing_table[router_id].route_change_flag:
            router.routing_table[router_id].route_change_flag = False
            is_triggered_update_nessesary = is_triggered_update_nessesary or True
            
    
    while router.is_routing_table_being_accessed:
        #print("Waiting for other processes to stop using routing table...")
        sleep(0.0001)
        
    #delete any routing_table entries that have been signaled for deletion
    for router_id in router_ids_to_be_deleted:
        del router.routing_table[router_id]
            
    if (is_triggered_update_nessesary):
        create_triggered_update(router)



def rip_update_timer(router):
    """
    A parallel process which sends out automatic routing table updates 
    to neighbouring routers every 30 seconds. Not all routers will receive the 
    same update due to the split horizon with poison reverse rules.
    """
    offset_time = randint(-5, 5)
    #to minimise delays from computing, start new timer immediately
    timer = threading.Timer(router.update_time+offset_time, rip_update_timer, [router])
    router.next_periodic_update = datetime.datetime.now() + datetime.timedelta(seconds=router.update_time+offset_time)
    timer.start()
    
    #it's possible for a router to get cutoff from everything because a router died, in that case no point doing periodic updates
    if (len(router.routing_table) != 0):
        router.is_routing_table_being_accessed = True
        send_routes_to_neighbours(router, router.routing_table.keys()) #send the entire routing_table to each neighbour
        router.is_routing_table_being_accessed = False
    
    
    
def start_background_timers(router):
    """
    Starts the RIP periodic update process and the RIP garbage collection 
    process.
    """
    rip_update_timer(router)
    rip_garbage_collection(router)
        
    