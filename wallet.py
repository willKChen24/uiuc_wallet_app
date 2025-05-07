import threading

class Wallet:
    def __init__(self):
        """Initialize an empty wallet."""
        self.resources = {} #initialize an empty dict: {resource_name : resource_ct}
        self.lock = threading.Lock() #initialize the lock
        self.cv = threading.Condition(self.lock) #initialize condition variable
    
    def get(self, resource): #resource = resource_name (the key)
        """Returns the amount of a given `resource` in this wallet."""
        with self.lock:
            if resource not in self.resources: #if the resource has not been added to the wallet
                return 0 #indicate we have none of that resource
            else:
                return self.resources[resource] #return the value
    def change(self, resource, delta):            
        """
        Modifies the amount of a given `resource` in this wallet by `delta`.
        - If `delta` is negative, this function MUST NOT RETURN until the resource can be satisfied.
            (This function MUST BLOCK until the wallet has enough resources to satisfy the request.)
        - Returns the amount of resources in the wallet AFTER the change has been applied.
        """
        with self.cv: #use a condition variable here bc we need to check the CONDITION of having enough of certain resources
            if resource not in self.resources:
                self.resources[resource] = 0

            while delta < 0 and self.resources[resource] + delta < 0: #if delta is negative and if the current resource value will become negative
                self.cv.wait() #use wait() to block the thread's execution

            self.resources[resource] += delta #when delta is not negative, increment the value

            #IMPORTANT: after cv.wait(), we have to wake up the remaning threads with cv.notify_all() so that they can proceed one by one through the condition var
            self.cv.notify_all() #wake up the waiting threads that are blocked on the CV, tell them
            #that the condition has changed, and they can recheck the condition to determine if they can proceed through the code

            return self.resources[resource] #return the new amount
        
    def try_change(self, resource, delta):
        """
        Like change, but change would block
        this method instead leaves the resource unchanged and returns False.
        """
        with self.cv:
            if resource not in self.resources:
                self.resources[resource] = 0
        
            if delta < 0 and self.resources[resource] + delta < 0:
                return False
            else:
                self.resources[resource] += delta
                self.cv.notify_all() #notify the other threads that the resource amount has changed
                return self.resources[resource]

    def transaction(self, **delta): #**delta means any number of args can be put into this fxn for delta
        """
        Like calling change(key, value) for each key:value in `delta`, except:
        - All changes are made at once. If any change would block, the entire transaction blocks.
            Only continues once *all* the changes can be made as one atomic action.
        - Returns a dict of {resource:new_value} for all resources in the transaction.
        """
        with self.cv:
            #check: can we modify ALL of these resources?
            for resource in delta:
                if resource not in self.resources:
                    self.resources[resource] = 0
            while True:
                make_changes = True #we can change the values
                for resource, change_val in delta.items(): #.items gives tuples (key, value)
                    if change_val < 0 and self.resources[resource] + change_val < 0: # if we would get negative values
                        make_changes = False #we cannot make changes
                        break

                if make_changes: #otherwise, we can make changes to the values
                    break

                self.cv.wait() #wait for notification

            #atp we know ALL changes can be made to the vals,
            #so apply ALL changes at once
            new_resources = {} #make a new (empty) dict

            for resource, change_val in delta.items():
                self.resources[resource] += change_val #modify the orignal wallet by change_val
                new_resources = self.resources #set the new wallet equal to the modified original wallet
            self.cv.notify_all() #notify all waiting threads
            
            return new_resources
