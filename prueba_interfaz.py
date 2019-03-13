import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import os, json
import subprocess, sys, os, signal

import agent

##########
## TODO ##
##########
# Add "status" section in config_agent file with two possible values: ONLINE/OFFLINE
# Add a way to identify agent_0 (the creator)
# With the information given before, create a tab ONLY for the main agent giving information about the circle
#   -> Information from local_ip_publisher and circle_info?

agents_info = {}
def get_info():
    path = './'
    files = [i for i in os.listdir(path) if os.path.isfile(os.path.join(path,i)) and \
             'config_agent' in i]

    my_agents_info={}
    for file in files:
        with open("./"+file, 'r') as config:
            my_agents_info[files.index(file)]=json.load(config)
    global agents_info
    agents_info=my_agents_info
    print(agents_info)


class Tab1 (ttk.Frame):

    agent_pid_dict = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.label_welcome = ttk.Label(self)
        self.label_welcome["text"] = ("Welcome to CloudBook user interface. Your agents are:")
        self.label_welcome.grid(row=0, column=0, columnspan=4, padx=100, pady=10)
        title_bar = [" Agent ID ", " Circle ID ", " Grant ", " Status ", "", ""]
        h=int(len(agents_info)+1)
        w=6
        z=0
        for i in range(h):
            for j in range(w):
                if(i==0):
                    self.cell=ttk.Label(self)
                    self.cell["text"]=title_bar[j]
                    self.cell["font"]=("Helvetica", 12, "bold", "underline")
                    self.cell.grid(row=i+2, column=j)
                else:
                    if(j==4):
                        
                        self.launch_button = ttk.Button(self, text="Launch", command=lambda r=i+2, c=j: self.launch(r, c))
                        self.launch_button.grid(column=j, row=i+2)
                    elif(j==5):
                        self.stop_button = ttk.Button(self, text="Stop", command=lambda r=i+2, c=j: self.stop(r, c))
                        self.stop_button.grid(column=j, row=i+2)
                    else:
                        minidict=list(agents_info[i-1].values())
                        if(minidict[j]==agents_info[i-1]['DISTRIBUTED_FS']):
                            z=1
                            continue
                        self.cell=ttk.Label(self)
                        self.cell["text"]=minidict[j]
                        if(j>0):
                            j=j-1
                        self.cell.grid(row=i+2, column=j)


    def launch(self, r, c):
        text = agents_info[r-3]['AGENT_ID']
        print("Launching agent", text)
        proc = subprocess.Popen("C:/Users/albercam/AppData/Local/Programs/Python/Python37-32/python.exe agent.py "+ text, shell=True ,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        self.agent_pid_dict[text]=proc
        print("-------------------------------------------------------------------------")
        
    
    def stop(self, r, c):
        text = agents_info[r-3]['AGENT_ID']
        print("Stopping agent", text, self.agent_pid_dict[text])
        self.agent_pid_dict[text].send_signal(signal.CTRL_BREAK_EVENT)
        self.agent_pid_dict[text].kill()
        del  self.agent_pid_dict[text]
        


class Tab2(ttk.Frame):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.label_welcome = ttk.Label(self)
        self.label_welcome["text"] = ("Create a new agent and attachs to local default circle \'LOCAL\'. \n All you need is to write up the circle ID you want to create or attach to.")
        self.label_welcome.grid(column=0, row=1, columnspan=4)
        
        self.circle_label = ttk.Label(self)
        self.circle_label["text"]=("Circle ID")
        self.circle_label.grid(column=0, row=4)
        self.circle_entry = ttk.Entry(self, text="LOCAL")
        self.circle_entry["state"]=(tk.DISABLED)
        self.circle_entry.grid(column=2, row=4, columnspan=2)
        self.set_circle_button = ttk.Button(self, text="Set", command=self.buttonset)
        self.set_circle_button['state']='disable'
        self.set_circle_button.grid(column=4, row = 4)

        self.grant_label = ttk.Label(self)
        self.grant_label["text"]=("Grant Level")
        self.grant_label.grid(column=0, row=6)
        self.grant_combo = ttk.Combobox(self)
        self.grant_combo = ttk.Combobox(self, state="readonly")
        self.grant_combo["values"] = ["HIGH", "MEDIUM", "LOW",]
        self.grant_combo.grid(column=2, row=6, columnspan=2)
        self.set_grant_button = ttk.Button(self, text="Set", command=self.set_grant)
        self.set_grant_button.grid(column=4, row = 6)
        ttk.Label(self, text="Filesystem Path:").grid(column=0, row=7)
        self.fspath=ttk.Entry(self)
        #self.fspath.insert(0, "AQUI EL PATH")
        self.fspath["state"]=(tk.DISABLED)
        self.fspath.grid(column=1, row=7, columnspan=3)
        self.bwButton = ttk.Button(self, text="Select", command=self.browse_button)
        self.bwButton.grid(column=4, row=7)

        self.create_circle = ttk.Button(self, text="Create agent and attach", command=self.create)
        #self.attach_circle = ttk.Button(self, text="Attach circle", command=self.attach)
        self.create_circle.grid(column=3, row=8)
        #self.attach_circle.grid(column=3, row=7)

    
    def buttonset(self):
        user_input=self.circle_entry.get()
        print(user_input)

    def set_grant(self):
        def switch(index):
            switcher = {
                0: "HIGH",
                1: "MEDIUM",
                2: "LOW"
            }  
            return switcher.get(index, "No se ha seleccionado nada")
        print("Se ha seleccionado: " + switch(self.grant_combo.current()) )
    
    def switch(self, index):
            switcher = {
                0: "HIGH",
                1: "MEDIUM",
                2: "LOW"
            }  
            return switcher.get(index, "No se ha seleccionado nada")
    
    def create(self):
        print("Pulsado crear")
        grant = self.switch(self.grant_combo.current())
        print("GRANT: " + grant )
        fspath = self.fspath.get()
        print("FS: " + fspath)

        agent.create_LOCAL_agent(grant, fspath)
    
    
    def browse_button(self):
        filename = filedialog.askdirectory()
        self.fspath["state"]=(tk.NORMAL)
        self.fspath.insert(0,filename)
        self.fspath["state"]=("readonly")
        print(filename)
        
class Tab3(ttk.Frame):
    def __init__(self, *args, var):
        super().__init__(*args)

class TabX(ttk.Frame):

    agent = []
    path = ""
    
    def __init__(self, *args, var):
        super().__init__(*args)
        self.agent=var
        ttk.Label(self, text="Agent "+ var['AGENT_ID'], font="bold").grid(column=2, row=0, columnspan=5)
        ttk.Label(self, text="Edit agent info. Please, make sure the agent is stopped before any change.").grid(column=1, row=1, columnspan=5)

        ttk.Label(self, text="Circle ID:").grid(column=1, row=3, sticky='w')
        ttk.Label(self, text=var['CIRCLE_ID']).grid(column=3, row=3, sticky='w')
        self.texto=ttk.Entry(self, state="readonly")
        self.texto.grid(column=6, row=3)
        self.botonEditar = ttk.Button(self, text='Edit', command=self.edit_circle_id)
        self.botonEditar['state']='disable'
        self.botonEditar.grid(column=8, row=3)
        ttk.Label(self, text="Grant level:").grid(column=1, row=4, sticky='w')
        ttk.Label(self, text=var['GRANT_LEVEL']).grid(column=3, row=4, sticky='w')
        self.combo=ttk.Combobox(self, state="readonly")
        self.combo["values"]=["HIGH", "MEDIUM", "LOW"]
        self.combo.grid(column=6, row=4)
        ttk.Button(self, text='Edit', command=self.set_grant).grid(column=8, row=4)
        ttk.Label(self, text="Filesystem Path:").grid(column=1, row=5, sticky='w')
        textfs=var['DISTRIBUTED_FS']
        ttk.Label(self, text="..."+textfs[-27:]).grid(column=3, row=5, sticky='w')
        self.fspath=ttk.Entry(self)
        self.fspath["state"]=(tk.DISABLED)
        self.fspath.grid(column=6, row=5)
        self.bwButton = ttk.Button(self, text="Select", command=self.browse_button)
        self.bwButton.grid(column=8, row=5)


    def edit_circle_id(self):
    
        print("En el campo pone: " +self.texto.get()+" del agente " + self.agent['AGENT_ID'])

    def set_grant(self):
        def switch(index):
            switcher = {
                0: "HIGH",
                1: "MEDIUM",
                2: "LOW"
            }  
            return switcher.get(index, "No se ha seleccionado nada")
        print("Se ha seleccionado: " + switch(self.combo.current())+" del agente " + self.agent['AGENT_ID'])
        agent.edit_agent(self.agent['AGENT_ID'], grant=switch(self.combo.current()))
        

    def browse_button(self):
        filename = filedialog.askdirectory()
        self.fspath["state"]=(tk.NORMAL)
        self.fspath.insert(0,filename)
        self.fspath["state"]=("readonly")
        print(filename+" del agente " + self.agent['AGENT_ID'])
        agent.edit_agent(self.agent['AGENT_ID'], fs=filename)
        


class Application(ttk.Frame):

    def __init__(self, master):
        super().__init__(master)
        master.title("CloudBook Agent GUI")

        self.notebook = ttk.Notebook(self)
        
        self.tab1 = Tab1(self.notebook)
        self.notebook.add(
            self.tab1, text="General Info", padding=10)
        
        self.tab2 = Tab2(self.notebook)
        self.notebook.add(
            self.tab2, text="Add Agents", padding=10)
        
        for info in agents_info:
            globals()['self.'+str(info)] = TabX(self.notebook, var=agents_info[info])
            self.notebook.add(
                globals()['self.'+str(info)], text="Agent "+ str(info), padding=10)

        tk.Button(self, text="Refresh", command=self.refresh).pack()
        self.notebook.pack(expand=True, fill="both")
        self.pack(expand=True, fill="both")
    
    def refresh(self):
        get_info()
        self.tab1.destroy()
        self.tab2.destroy()
        self.notebook.destroy()
        self.notebook = ttk.Notebook(self)
        self.tab1 = Tab1(self.notebook)
        self.notebook.add(
            self.tab1, text="General Info", padding=10)
        
        self.tab2 = Tab2(self.notebook)
        self.notebook.add(
            self.tab2, text="Add Agents", padding=10)
        
        for info in agents_info:
            globals()['self.'+str(info)] = TabX(self.notebook, var=agents_info[info])
            self.notebook.add(
                globals()['self.'+str(info)], text="Agent "+ str(info), padding=10)

        self.notebook.pack(expand=True, fill="both")
        self.pack(expand=True, fill="both")

   



get_info()
master = tk.Tk()
app = Application(master)
app.mainloop()