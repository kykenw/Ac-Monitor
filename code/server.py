#This is the server end of an application with the goal of providing accountability for a business.
#This application allows you to create tasks, view individuals as they log in, and assign tasks to those individuals.

import socket
from tkinter import *
from queue import Queue
import threading
import random
import time

#queues to update tkinter listboxes
users = Queue()
tasks = Queue()
#queue to remove clients from the clientlist
logout = Queue()

#lists created to hold client objects and threads
clientList = []
threadlist = []

loggedinUsers = []

#generate random jobs for demonstration and testing
jobs = ["Paint room", "Clean room", "Clean restroom", "Clean lobby"]

for x in range(100):
    tasks.put(random.choice(jobs) + " #" + str(x))

#client objects are created for every connection made
#this object contains multiple variables, queues, and lists
class client(object):
    def __init__(self, conn, addr):
        self.name = ''
        self.conn = conn
        self.addr = addr
        self.assignedQ = Queue()
        self.sendQ = Queue()
        self.completed = Queue()
        self.alist = []
        self.clist = []

    def send(self):
        while True:
            while not self.sendQ.empty():
                try:
                    item = self.sendQ.get()
                    encodeditem = str.encode(item)
                    self.conn.send(encodeditem)
                    print(item + " sent!")
                except:
                    logout.put(self.addr)

    def recv(self):
        while True:
            try:
                data = self.conn.recv(2048)
                completedtask = data.decode('utf-8')
                if not data:
                    continue
                if completedtask.startswith("user:"):
                    name = completedtask.replace("user: ", "")
                    if name not in loggedinUsers:
                        self.setName(name)
                        users.put(name)
                    else:
                        self.sendQ.put("Someone is ")
                        time.sleep(1)
                        self.sendQ.put("already ")
                        time.sleep(1)
                        self.sendQ.put("logged in ")
                        time.sleep(1)
                        self.sendQ.put("as ")
                        time.sleep(1)
                        self.sendQ.put(name)
                        time.sleep(1)
                        self.sendQ.put("Try again... ")
                        time.sleep(1)
                        self.sendQ.put("#Kick")
                        for y, client in enumerate(clientList):
                            if client.getAddr() == self.getAddr():
                                clientList.pop(y)


                else:
                    self.completed.put(completedtask)
                    print("Completed " + "(" + completedtask + ")")
            except:
                logout.put(self.addr)

    def completedEmpty(self):
        return self.completed.empty()


    def sendT(self, task):
        self.sendQ.put(task)

    def close(self):
        self.conn.close()

    def assign(self, item):
        self.alist.append(item)

    def getalist(self):
        return self.alist

    def setName(self, name):
        self.name = name

    def getName(self):
        return self.name

    def getConn(self):
        return self.conn

    def getAddr(self):
        return self.addr

    def get(self):
        return self.assignedQ.get()

    def assignedEmpty(self):
        return self.assignedQ.empty()

    def put(self, item):
        self.assignedQ.put(item)

#userBox shows users that are logged in
class userBox(Listbox):

    def __init__(self, parent):
        Listbox.__init__(self, parent, exportselection=0)

    def updateList(self):
        print("updating user list")
        selectedIndex = self.curselection()
        self.delete(0, END)
        while not users.empty():
            u = users.get()
            loggedinUsers.append(u)

        while not logout.empty():
            address = logout.get()

            for x, client in enumerate(clientList):
                if client.getAddr() == address:
                    ru = client.getName()
                    clientList.pop(x)
                    for utask in client.alist:
                        lb2.insert(0, utask)
                    for i, u in enumerate(loggedinUsers):
                        if u == ru:
                            loggedinUsers.pop(i)

        print(str(len(clientList)) + " users logged in")



        for n,user in enumerate(loggedinUsers):

            self.insert(END, user)

        try:
            self.select_set(selectedIndex)
            self.event_generate("<<ListboxSelect>>")
            self.activate(selectedIndex)
        except:
            if self.size() > 0:
                self.select_set(0)
                self.event_generate("<<ListboxSelect>>")
                self.activate(0)

        checkConnections()

        self.after(2000, self.updateList)

#taskBox holds a list of assignments that can be assigned to employees
class taskBox(Listbox):

    def __init__(self, parent):
        Listbox.__init__(self, parent, exportselection=0)

    def updateList(self):
        print("updating task list")
        selectedIndex = self.curselection()
        while not tasks.empty():
            t = tasks.get()
            self.insert(END, t)

        try:
            self.select_set(selectedIndex)
            self.event_generate("<<ListboxSelect>>")
            self.activate(selectedIndex)
            self.see(selectedIndex)
        except:
            if self.size() > 0:
                self.select_set(0)
                self.event_generate("<<ListboxSelect>>")
                self.activate(0)

        self.after(2000, self.updateList)

#assignedBox hold assignments the user still needs to complete
class assignedBox(Listbox):

    def __init__(self, parent):
        Listbox.__init__(self, parent, exportselection=0)

    def updateList(self):
        print("updating assigned list")
        selectedIndex = self.curselection()
        u = lb1.get(ACTIVE)
        self.delete(0, END)
        for client in clientList:
            if client.getName() == u:
                while not client.assignedEmpty():
                    t = client.get()
                    client.assign(t)
                for item in client.getalist():
                    self.insert(END, item)

        try:
            self.select_set(selectedIndex)
            self.event_generate("<<ListboxSelect>>")
            self.activate(selectedIndex)
            self.see(selectedIndex)
        except:
            if self.size() > 0:
                self.select_set(0)
                self.event_generate("<<ListboxSelect>>")
                self.activate(0)




        self.after(2000, self.updateList)

#completedBox holds assignments that a user has finished
class completedBox(Listbox):

    def __init__(self, parent):
        Listbox.__init__(self, parent, exportselection=0)

    def updateList(self):

        print("updating completed task list")
        selectedIndex = self.curselection()
        u = lb1.get(ACTIVE)
        self.delete(0, END)
        for client in clientList:
            if client.getName() == u:
                while not client.completedEmpty():
                    t = client.completed.get()
                    client.clist.append(t)
                for item in client.clist:
                    self.insert(END, item)
                    for x, it in enumerate(client.alist):
                        if it == item:
                            client.alist.pop(x)

        try:
            self.select_set(selectedIndex)
            self.event_generate("<<ListboxSelect>>")
            self.activate(selectedIndex)
            self.see(selectedIndex)
        except:
            if self.size() > 0:
                self.select_set(0)
                self.event_generate("<<ListboxSelect>>")
                self.activate(0)

        self.after(2000, self.updateList)

#Function to check who is still logged in.
def checkConnections():
    for client in clientList:
            client.sendT("#")

#Function to get selected task from taskBox and move it to assignedBox
def assignTask():
    if lb1.size() > 0:
        t = lb2.get(ACTIVE)
        lb2.delete(ACTIVE)
        u = lb1.get(ACTIVE)
        for client in clientList:
            if client.getName() == u:
                client.put(t)
                client.sendT(t)

    if lb2.size() > 0:
                lb2.select_set(0)
                lb2.event_generate("<<ListboxSelect>>")
                lb2.activate(0)

#Kick user out
def kick():
    u = lb1.get(ACTIVE)
    for client in clientList:
        print(client.getName() == u)
        print("'" + client.getName() + "' and '" + u + "'")
        if client.getName() == u:
            print("Kicking " + u)
            client.sendT("#Kick")
            logout.put(client.getAddr)


#Function to add tasks to the taskBox
def createTask():
    task = njob.get()
    if task != "":
        check = []
        for x in range(lb2.size()):
            check.append(lb2.get(x))
        if task not in check:
            lb2.insert(0, task)
            njob.delete(0, END)


#Function to create a socket
def createSocket():
    print("createSocket()")
    try:
        global host
        global port
        global s
        host = ''
        port = 5000
        s = socket.socket()
    except socket.error as e:
        print("Error when creating socket " + str(e))

#Function to bind socket to an address
def bindSocket():
    print("bindSocket()")
    try:
        global host
        global port
        global s
        s.bind((host, port))
        s.listen(5)
    except socket.error as e:
        print("Error when binding socket " + str(e))
        time.sleep(5)
        bindSocket()

#Function to clear all clients
def clearConnections():
    print("clearing connections")
    for c in clientList:
        c.close()
    del clientList[::]

#Function that runs in an infinite loop on its own thread to constantly check for connections
def acceptConnections():
    print("acceptingConnections")
    while True:
        try:
            conn, addr = s.accept()

            s.setblocking(1)

            c = client(conn, addr)

            clientList.append(c)

            send = threading.Thread(target=c.send, args=())

            send.daemon = True

            send.start()

            threadlist.append(send)

            recv = threading.Thread(target=c.recv, args=())

            recv.daemon = True

            recv.start()

            threadlist.append(recv)

            print("Connection to IP " + addr[0])


        except:
            print("Error accepting connections")


    s.close()
    root.destroy()

#This code creates the window listboxes, labels, etc.
root = Tk()
root.title("Server")
emplbl = Label(root, text="Employees")
emplbl.grid(row=0, column=0)
kickbtn = Button(root, text="Kick", command=kick)
kickbtn.grid(row=0, column=1)
lb1 = userBox(root)
lb1.grid(row=1, column=0, rowspan=3, columnspan=3, padx=5, pady=5)
lb1.updateList()
assignbtn = Button(root, text="Assign", command=assignTask)
assignbtn.grid(row=4, column=0, columnspan=3, padx=5, pady=5)
tasklbl = Label(root, text="Tasks")
tasklbl.grid(row=5, column=0, columnspan=3)
lb2 = taskBox(root)
lb2.grid(row=6, column=0, rowspan=3, columnspan=3, padx=5, pady=5)
lb2.updateList()
assignedlbl = Label(root, text="Tasks assigned")
assignedlbl.grid(row=0, column=4, columnspan=3)
lb3 = assignedBox(root)
lb3.grid(row=1, column=4, rowspan=3, columnspan=3, padx=5, pady=5)
lb3.updateList()
clbl = Label(root, text="Completed Tasks")
clbl.grid(row=5, column=4, columnspan=3)
lb4 = completedBox(root)
lb4.grid(row=6, column=4, rowspan=3, columnspan=3, padx=5, pady=5)
lb4.updateList()
njob = Entry(root, width=12)
njob.grid(row=10, column=0, padx=5, pady=5)
createbtn = Button(root, text="Create", command=createTask)
createbtn.grid(row=10, column=1)
createSocket()
bindSocket()

#Thread to constantly check for clients trying to connect.
server = threading.Thread(target=acceptConnections, args=() )
server.start()
threadlist.append(server)
mainloop()
