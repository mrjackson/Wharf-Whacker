#!/usr/bin/env python
import socket
import SocketServer
import scapy
import hashlib
from time import strftime, gmtime, sleep
from Queue import Queue
from threading import Thread
password = "1234"

class Worker(Thread):
  """Thread executing tasks from a given tasks queue"""
  def __init__(self, tasks):
    Thread.__init__(self)
    self.tasks = tasks #refer this worker to the shared Job Queue
    self.start()
  
  def run(self):
    while True:
      func, args, kargs = self.tasks.get()
      try: func(*args, **kargs)
      except Exception, e: print e
      self.tasks.task_done() #indicate the previous task has been processed
#Worker Class is ended here 

class ThreadPool:
  """Pool of threads consuming tasks from a queue"""
  def __init__(self, num_threads):
    self.tasks = Queue(num_threads)
    for _ in range(num_threads): Worker(self.tasks) #create a number of threads when initialize ThreadPool 

  def add_task(self, func, *args, **kargs):
    self.tasks.put((func, args, kargs)) #each task is a function pointer along with arguments
    
  def wait_completion(self):
    """Wait for completion of all the tasks in the queue"""
    self.tasks.join()
  
  def empty():
    return self.tasks.empty()   
#ThreadPool Class is ended here   


class WharfWhacker:
  def __init__(self,ipaddress,password,safe_ports,authentication_length,packet_type):
    self.password = password
    self.start_port = 0
    self.reserved_pool = ThreadPool(authentication_length*10+1)
    self.connection_sockets = []
    self.connections = dict()
    self.banlist = dict()
    self.safe_ports = safe_ports
    self.authentication_length = authentication_length
    self.packet_type = packet_type    
    self.keepgoing = True
    self.reserved_pool.add_task(self.new_ports)

    print "Ports Generated"
    print "Starting Scanner"
        
  def new_ports(self):
    while self.keepgoing:
      # This section is developing which ports to use.
      self.start_port = 0
      self.connections = dict()
      porthash = hashlib.sha512(password+strftime("%Y - %j - %d - %H - %M",gmtime())).hexdigest()
      self.set_initial_port(porthash)
      self.connections = dict()
      print strftime("%Y - %j - %d - %H - %M",gmtime())
      print self.start_port
      self.reserved_pool.add_task(self.stream_reader,self.start_port)
      sleep((60-int(strftime("%S"))))
      for sock in self.connection_sockets:
        sock.shutdown()
      self.connection_sockets = []
        
  def set_initial_port(self,porthash):
    x=0
    while self.start_port == 0 :
      temp_port = int(porthash[(x%512):((x+4)%512)],16)
      if temp_port > 1024 and temp_port not in self.safe_ports:
        self.start_port = temp_port
      x = x + 5

  def check_ports(self,ipaddress,port): 
    if ipaddress in self.connections:
      print self.connections[ipaddress]
      if self.connections[ipaddress][self.connections[ipaddress][0]] == port:
        self.connections[ipaddress][0] = self.connections[ipaddress][0] + 1
        if self.connections[ipaddress][0] >= self.authentication_length + 1:
          self.allow_ip(ipaddress)
          del self.connections[ipaddress]
      else:
        del self.connections[ipaddress]
        print "Connection Reset" + ipaddress
    else:
      if self.start_port==port:
        print "Session started, Creating secure ports"
        self.connections[ipaddress] = [1]
        self.generate_secure_ports(ipaddress)
        print "Secure Ports Created"
      else:
        if port not in self.safe_ports:
          print "Failcamp - banlisting"
          del self.connections[ipaddress]
          if ipdaddress in self.banlist:
            self.banlist[ipaddress] = self.banlist[ipaddress] + 1
          else:
            self.banlist[ipaddress] = 1

  def generate_secure_ports(self,ipaddress):
    #This is the function that you need to change to generate a list of ports to knock against
    porthash = hashlib.sha512(ipaddress + self.password+strftime("%Y - %j - %d - %H - %M",gmtime())).hexdigest()  
    x = 0
    while len(self.connections[ipaddress]) < self.authentication_length + 1 :
      temp_port = int(porthash[x:x+4],16)
      if temp_port > 1024:
        self.connections[ipaddress].append(temp_port)    
      x = x + 5
    for port in self.connections[ipaddress]:
      self.reserved_pool.add_task(self.stream_reader,port)
      
  def stream_reader(self,port):
    #This is the function that checks the packet stream for any possible connections
    self.connection_sockets.append(WharfServer(("172.16.2.128",port),InitialUDPHandler,self))
    self.connection_sockets[-1].serve_forever()

  def allow_ip(self,ipaddress):
    #Where the code goes for the IPTables crap
    print ipaddress + "confirmed!"
    
  def unset(self):
    self.keepgoing = False
#WharfWhacker Class is ended here    


class Whacker():
  def __init__(self,password,safe_ports,authentication_length,packet_type):
    self.password = password
    self.authentication_length = authentication_length
    self.packet_type = packet_type
    self.safe_ports = safe_ports
    self.ports = []
    self.ip_address = "172.16.2.128"
    self.generate_ports()
    
  def whack(self,target_ip):
    first = True
    for i in self.ports:
      print i
      s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      s.sendto("are those pants?",("172.16.2.128",i))
      if first:
        #We have to sleep here because most servers can't run the hashes for the ip's
        #AND open new sockets in the time before the next packet shows up.
        sleep(1)
        first = False

  def obtain_ip(self):
    self.ip_address = "172.16.2.128"
    
  def generate_ports(self):
    #generates the ports that it will be using.
    porthash = hashlib.sha512(password+strftime("%Y - %j - %d - %H - %M",gmtime())).hexdigest()
    x = 0
    while len(self.ports) < 1 :
      temp_port = int(porthash[x:x+4],16)
      if temp_port > 1024:
        self.ports.append(temp_port)
      x = x + 5
   
    porthash = hashlib.sha512(self.ip_address + password+strftime("%Y - %j - %d - %H - %M",gmtime())).hexdigest()  
    x=0
    while len(self.ports) < self.authentication_length + 1 :
      temp_port = int(porthash[x:x+4],16)
      if temp_port > 1024:
        self.ports.append(temp_port)
      x = x + 5      
#Whacker Class is ended here


class WharfServer(SocketServer.UDPServer):
  def __init__(self, address, handler, wharf):
    self.wharf = wharf
    SocketServer.UDPServer.__init__(self, address, handler)
# WharfServer Class is ended here

class InitialUDPHandler(SocketServer.BaseRequestHandler):
  def handle(self):
    data = self.request[0].strip()
    ip,port = self.request[1].getsockname()
    self.client_address
    self.server.wharf.check_ports(ip,port)
# InitialUDPHandler Class is eneded here


    
    

