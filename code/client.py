#This is the client end of an application with the goal of providing accountability for a business.
#As an employee you would see incoming tasks that have been assigned to you.
#Once you complete a task you would checkoff that task and it would get moved over to completed tasks.
#On the server end they would also be able to see the completed tasks.

from tkinter import *
from socket import *
from queue import Queue
import threading
import time

#Queue that will contain either your username or completed tasks that need to be sent to the server.
sendQ = Queue()
kick = Queue()
#A list of items to populate the task listbox.
tasks = []
#A list of items to populate the completed task listbox.
completedTasks = []

#Prompt for user to enter a username to login with
class Login(Tk):

    def __init__(self):
        Tk.__init__(self)
        self.title("Login")
        self.grid()
        self.label = Label(self, text="Username:")
        self.label.grid(row=0, column=0)
        self.entry = Entry(self)
        self.entry.grid(row=0, column=1)
        self.button = Button(self, text="Login", command=openmw)
        self.button.grid(row=1, column=0)

#Main window shown after logging in.
class Window(Tk):

    def __init__(self, user):
        Tk.__init__(self)
        self.title("(" + user + ")")
        self.grid()
        self.tasks = TaskBox(self)
        self.tasks.grid(row=1, column=0, rowspan=3, padx=5, pady=5)
        self.tasks.updateList()
        self.checkButton = Button(self, text="Checkoff", command=checkoff)
        self.checkButton.grid(row=4, column=0)
        self.ctasks = cTaskBox(self)
        self.ctasks.updateList()
        self.ctasks.grid(row=5, column=0, rowspan=3, padx=5, pady=5)

        #This threads constantly check for incoming tasks or completed tasks that need to be sent to the server.
        sendC = threading.Thread(target=sendCompletedTask, args=())
        recvT = threading.Thread(target=recvTask, args=())
        sendC.daemon = True
        recvT.daemon = True
        sendC.start()
        recvT.start()


class TaskBox(Listbox):

    def __init__(self, master):
        Listbox.__init__(self, master, exportselection=0)

    #This method behaves like an infinite loop clearing itself and then
    #populating it self from a list.
    def updateList(self):
        global s
        print("updating task list")
        selectedIndex = self.curselection()
        self.delete(0, END)
        for t in tasks:
            self.insert(END, t)

        if not kick.empty():
            mw.destroy()

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

    def getSelection(self):
        return self.curselection()

class cTaskBox(Listbox):

    def __init__(self, master):
        Listbox.__init__(self, master, exportselection=0)

    #This method behaves like an infinite loop clearing itself and then
    #populating it self from a list.
    def updateList(self):
        global s
        print("updating task list")
        selectedIndex = self.curselection()
        self.delete(0, END)
        for t in completedTasks:
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

def checkoff():
    try:
        index = mw.tasks.getSelection()
        active = mw.tasks.get(index)
        for i,ut in enumerate(tasks):
                if ut == active:
                    tasks.pop(i)
        if active not in completedTasks:
            completedTasks.append(active)
            sendQ.put(active)

    except:
        print("Check off completed task error")

#This function runs on a thread
def sendCompletedTask():
    global s
    while True:
        while not sendQ.empty():
            ctask = sendQ.get()
            encodedctask = str.encode(ctask)
            s.send(encodedctask)

#This function runs on a thread.
def recvTask():
    global s
    while True:
        data = s.recv(2048)
        task = data.decode('utf-8')
        if task == "#Kick":
            s.close()
            kick.put(1)
        elif task != "#":
            tasks.append(task)
        else:
            print("Connection to server is valid")

#Function to connect to the server and open a window.
def openmw():
    global mw, l, s

    HOST = 'localhost'
    PORT = 5000

    s = socket(AF_INET, SOCK_STREAM)
    s.connect((HOST, PORT))
    user = "user: " + l.entry.get()
    sendQ.put(user)
    mw = Window(user)
    l.destroy()

def Main():
    global l
    l = Login()

if __name__ == '__main__':
    Main()
    mainloop()
