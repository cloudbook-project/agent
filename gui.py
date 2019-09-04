import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import os, json
import subprocess, sys, os, signal, platform

import agent
import loader

##########
## TODO ##
##########
# Add a way to identify agent_0 (the creator)
# With the information given before, create a tab ONLY for the main agent giving information about the circle
#   -> Information from local_ip_publisher and circle_info?

#This functions recovers the information about the different agents using their configuration files.
#Then the information is saved on a variable that will be used later.
agents_info = {}
def get_info():
    if(platform.system()=="Windows"):
        path = os.environ['HOMEDRIVE'] + os.environ['HOMEPATH']+"/cloudbook/config/"
        if not os.path.exists(path):
            os.makedirs(path)
    else:
        path = "/etc/cloudbook/config/"
        if not os.path.exists(path):
            os.makedirs(path)
    files = [i for i in os.listdir(path) if os.path.isfile(os.path.join(path,i)) and \
             'config_' in i]

    my_agents_info = {}
    for file in files:
        with open(path+file, 'r') as config:
            my_agents_info[files.index(file)] = json.load(config)
    global agents_info
    agents_info = my_agents_info
    print(agents_info)
    return path

#This is the first type of tab. It includes all the information related to the different agents that live in the machine.
#It provides with "launch" and "stop" buttons. The information about the different agents is readed from the get_info() function.
class GeneralInfoTab (ttk.Frame):

    agent_pid_dict = {}

    #Builds the layout and fills it.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        print("Active processes: ", self.agent_pid_dict, "\n")

        self.label_welcome = ttk.Label(self)
        self.label_welcome["text"] = ("Welcome to CloudBook user interface. Your agents are:")
        self.label_welcome.grid(row=0, column=0, columnspan=4, padx=100, pady=10)
        title_bar = [" Agent ID ", " Circle ID ", " Grant ", " Status ", "", "", ""]
        h = int(len(agents_info)+1)
        w = 7
        for i in range(h):
            for j in range(w):
                if(i==0):
                    self.cell = ttk.Label(self)
                    self.cell["text"] = title_bar[j]
                    self.cell["font"] = ("Helvetica", 12, "bold", "underline")
                    self.cell.grid(row=i+2, column=j)
                else:
                    if(j==w-3):
                        self.launch_button = ttk.Button(self, text="Launch", command=lambda r=i+2, c=j: self.launch(r, c))
                        self.launch_button.grid(column=j, row=i+2)
                    elif(j==w-2):
                        self.stop_button = ttk.Button(self, text="Stop", command=lambda r=i+2, c=j: self.stop(r, c))
                        self.stop_button.grid(column=j, row=i+2)
                    elif(j==w-1):
                        self.remove_button = ttk.Button(self, text="Remove", command=lambda r=i+2, c=j: self.remove(r, c))
                        self.remove_button.grid(column=j, row=i+2)
                    elif(j==w-4):
                        self.cell=ttk.Label(self)
                        if (list(agents_info[i-1].values()))[0] in self.agent_pid_dict.keys():
                            self.cell["foreground"] = "green"
                            self.cell["text"] = "RUNNING"
                        else:
                            self.cell["foreground"] = "red"
                            self.cell["text"] = "STOPPED"
                        self.cell.grid(row=i+2, column=j)
                    else:
                        agent_circle_and_grant = {k: agents_info[i-1][k] for k in ('AGENT_ID', 'CIRCLE_ID', 'GRANT_LEVEL')}
                        minidict = list(agent_circle_and_grant.values())
                        self.cell = ttk.Label(self)
                        self.cell["text"] = minidict[j]
                        self.cell.grid(row=i+2, column=j)


    #Functionality of the "Launch" button
    def launch(self, r, c):
        text = agents_info[r-3]['AGENT_ID']
        print("Launching agent", text)
        if(platform.system()=="Windows"):
        	proc = subprocess.Popen("py agent.py "+ text, shell=True ,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
        	proc = subprocess.Popen("python3 agent.py "+ text, shell=True, preexec_fn=os.setsid)
        self.agent_pid_dict[text]=proc
        print("-------------------------------------------------------------------------")
        print("Active processes: ", self.agent_pid_dict, "\n")
        
    #Functionality of the "Stop" button.
    def stop(self, r, c):
        text = agents_info[r-3]['AGENT_ID']
        print("Stopping agent", text, self.agent_pid_dict[text])
        if(platform.system()=="Windows"):
            self.agent_pid_dict[text].send_signal(signal.CTRL_BREAK_EVENT)
            self.agent_pid_dict[text].kill()
        else:
            os.killpg(os.getpgid(self.agent_pid_dict[text].pid), signal.SIGTERM)
        del  self.agent_pid_dict[text]
        print("Active processes: ", self.agent_pid_dict, "\n")

    #Functionality of the "Remove" button.
    def remove(self, r, c):
        path = get_info()
        agent_id = agents_info[r-3]['AGENT_ID']
        config_path = path + os.sep + "config_" + agent_id + ".json"
        if agent_id in self.agent_pid_dict:
            print(agent_id + " is running! It must be stopped to be removed.")
            return
        if os.path.exists(config_path):
            config_dict = loader.load_dictionary(config_path)
            grant_path = config_dict["DISTRIBUTED_FS"] + os.sep + "agents_grant.json"
            if os.path.exists(grant_path):
                grants_dict = loader.load_dictionary(grant_path)
                if agent_id=="agent_0" and len(grants_dict)>1:
                    print("You must remove all other agents before attempting to remove " + agent_id + ".")
                    return
                try:
                    grants_dict.pop(agent_id)
                except KeyError:
                    print("ERROR: could not delete ", agent_id, ". File " + grant_path + " does not contain information about the agent.")
                    return
                loader.write_dictionary(grants_dict, grant_path)
            else:
                print("ERROR: could not find " + grant_path + ". Removal aborted.")
                return
            os.remove(config_path)
        else:
            print("ERROR: could not find " + config_path + ". Removal aborted.")
        

#This tab is the one including the information to create a new agent.
#Some fields are disabled since they are not supported yet.
class AddAgentTab(ttk.Frame):
    
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
        self.set_circle_button = ttk.Button(self, text="Set", command=self.set_circle_ID)
        self.set_circle_button['state']='disable'
        self.set_circle_button.grid(column=4, row = 4)

        self.grant_label = ttk.Label(self)
        self.grant_label["text"] = ("Grant Level")
        self.grant_label.grid(column=0, row=6)
        self.grant_combo = ttk.Combobox(self)
        self.grant_combo = ttk.Combobox(self, state="readonly")
        self.grant_combo["values"] = ["HIGH", "MEDIUM", "LOW",]
        self.grant_combo.grid(column=2, row=6, columnspan=2)
        self.set_grant_button = ttk.Button(self, text="Set", command=self.set_grant)
        self.set_grant_button.grid(column=4, row=6)
        ttk.Label(self, text="Filesystem Path:").grid(column=0, row=7)
        self.fspath = ttk.Entry(self)
        #self.fspath.insert(0, "AQUI EL PATH")
        self.fspath["state"] = (tk.DISABLED)
        self.fspath.grid(column=1, row=7, columnspan=3)
        self.browse_fs_path_button = ttk.Button(self, text="Select", command=self.browse_FS_path)
        self.browse_fs_path_button.grid(column=4, row=7)

        self.create_circle = ttk.Button(self, text="Create agent and attach", command=self.create)
        #self.attach_circle = ttk.Button(self, text="Attach circle", command=self.attach)
        self.create_circle.grid(column=3, row=8)
        #self.attach_circle.grid(column=3, row=7)

    #Functionality for set Circle ID button
    def set_circle_ID(self):
        user_input = self.circle_entry.get()
        print(user_input)

    #Functionality for grant switch-case
    def set_grant(self):
        def switch(index):
            switcher = {
                0: "HIGH",
                1: "MEDIUM",
                2: "LOW"
            }  
            return switcher.get(index, "No option selected")
        print("Se ha seleccionado: " + switch(self.grant_combo.current()) )
    
    def switch(self, index):
            switcher = {
                0: "HIGH",
                1: "MEDIUM",
                2: "LOW"
            }  
            return switcher.get(index, "No se ha seleccionado nada")
    
    #Functionality for create button. Recovers the already set information and
    #calls the create_local_agent function located in the agent.py software.
    def create(self):
        print("Pulsado crear")
        grant = self.switch(self.grant_combo.current())
        print("GRANT: " + grant )
        fspath = self.fspath.get()
        print("FS: " + fspath)

        agent.create_LOCAL_agent(grant, fspath)
    
    #This button launches a new gui to select the folder for the FS path.
    #This parameter is optional.
    def browse_FS_path(self):
        filename = filedialog.askdirectory()
        self.fspath["state"] = (tk.NORMAL)
        self.fspath.insert(0,filename)
        self.fspath["state"] = ("readonly")
        print(filename)


# New tab reserved for future use.
class Tab3(ttk.Frame):
    def __init__(self, *args, var):
        super().__init__(*args)

# Tab that contains the information of a specific agent located in the machine.
# It algo provides functionality to edit its parameters such as the FS, or the grant.
# It contains disabled functions because its functionality will be included in the future.
class AgentXTab(ttk.Frame):

    agent = []
    path = ""
    
    def __init__(self, *args, var):
        super().__init__(*args)
        self.agent = var
        ttk.Label(self, text=var['AGENT_ID'], font="bold").grid(column=2, row=0, columnspan=5)
        ttk.Label(self, text="Edit agent info. Please, make sure the agent is stopped before any change.").grid(column=1, row=1, columnspan=5)

        ttk.Label(self, text="Circle ID:").grid(column=1, row=3, sticky='w')
        ttk.Label(self, text=var['CIRCLE_ID']).grid(column=3, row=3, sticky='w')
        self.text = ttk.Entry(self, state="readonly")
        self.text.grid(column=6, row=3)
        self.edit_circle_id_button = ttk.Button(self, text='Edit', command=self.edit_circle_id)
        self.edit_circle_id_button['state']='disable'
        self.edit_circle_id_button.grid(column=8, row=3)
        ttk.Label(self, text="Grant level:").grid(column=1, row=4, sticky='w')
        ttk.Label(self, text=var['GRANT_LEVEL']).grid(column=3, row=4, sticky='w')
        self.combo = ttk.Combobox(self, state="readonly")
        self.combo["values"]=["HIGH", "MEDIUM", "LOW"]
        self.combo.grid(column=6, row=4)
        ttk.Button(self, text='Edit', command=self.set_grant).grid(column=8, row=4)
        ttk.Label(self, text="Filesystem Path:").grid(column=1, row=5, sticky='w')
        textfs = var['DISTRIBUTED_FS']
        ttk.Label(self, text="..."+textfs[-27:]).grid(column=3, row=5, sticky='w')
        self.fspath = ttk.Entry(self)
        self.fspath["state"]=(tk.DISABLED)
        self.fspath.grid(column=6, row=5)
        self.browse_fs_path_button = ttk.Button(self, text="Select", command=self.browse_FS_path)
        self.browse_fs_path_button.grid(column=8, row=5)


    #To be added when the functionality is implemented.
    def edit_circle_id(self):
    
        print("En el campo pone: " + self.text.get() + " del agente " + self.agent['AGENT_ID'])

    #Functionality to edit the agent grant. It calls to the "edit_agent()" function in the 
    # agent software.
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
        
    #This button launches a new gui to select another folder for the FS path. 
    def browse_FS_path(self):
        filename = filedialog.askdirectory()
        self.fspath["state"] = (tk.NORMAL)
        self.fspath.insert(0,filename)
        self.fspath["state"] = ("readonly")
        print(filename + " del agente " + self.agent['AGENT_ID'])
        agent.edit_agent(self.agent['AGENT_ID'], fs=filename)
        

#Class to build the general framework of the GUI.
#Inside this object, the different tabs are constructed. It also includes de "Refresh" button.
class Application(ttk.Frame):

    #The different tabs are initialized.
    def __init__(self, master):
        super().__init__(master)
        master.title("CloudBook Agent GUI")

        self.notebook = ttk.Notebook(self)
        
        self.tab1 = GeneralInfoTab(self.notebook)
        self.notebook.add(
            self.tab1, text="General Info", padding=10)
        
        self.tab2 = AddAgentTab(self.notebook)
        self.notebook.add(
            self.tab2, text="Add Agents", padding=10)
        
        for info in agents_info:
            globals()['self.'+str(info)] = AgentXTab(self.notebook, var=agents_info[info])
            self.notebook.add(
                globals()['self.'+str(info)], text="Agent "+str(info), padding=10)

        #Refresh button created
        tk.Button(self, text="Refresh", command=self.refresh).pack()
        self.notebook.pack(expand=True, fill="both")
        self.pack(expand=True, fill="both")
    
    #Functionality for refresh button. Basically it rebuilds the framework.
    def refresh(self):
        get_info()
        self.tab1.destroy()
        self.tab2.destroy()
        self.notebook.destroy()
        self.notebook = ttk.Notebook(self)
        self.tab1 = GeneralInfoTab(self.notebook)
        self.notebook.add(
            self.tab1, text="General Info", padding=10)
        
        self.tab2 = AddAgentTab(self.notebook)
        self.notebook.add(
            self.tab2, text="Add Agents", padding=10)
        
        for info in agents_info:
            globals()['self.'+str(info)] = AgentXTab(self.notebook, var=agents_info[info])
            self.notebook.add(
                globals()['self.'+str(info)], text="Agent "+str(info), padding=10)

        self.notebook.pack(expand=True, fill="both")
        self.pack(expand=True, fill="both")


#Start application
get_info()
master = tk.Tk()
app = Application(master)
app.mainloop()
