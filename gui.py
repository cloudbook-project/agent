import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import *
from tkinter import messagebox
import os, json
import subprocess, sys, os, signal, platform

import agent
import loader
import time

# Global variable to store information about all the agents of all the projects.
projects = {}


#This functions recovers the information about the different agents using their configuration files.
#Then the information is saved on a variable that will be used later.
def get_info():
    global projects         # Use the global variable projects
    global cloudbook_path   # Use the global variable cloudbook_path

    # Get the general path to cloudbook
    if(platform.system()=="Windows"):
        cloudbook_path = os.environ['HOMEDRIVE'] + os.environ['HOMEPATH'] + os.sep + "cloudbook"
        if not os.path.exists(cloudbook_path):
            os.makedirs(cloudbook_path)
    else:
        cloudbook_path = "/etc/cloudbook"
        if not os.path.exists(cloudbook_path):
            os.makedirs(cloudbook_path)

    # List with the folders inside "cloudbook/" folder. Each one represents a different project
    projects_list = next(os.walk(cloudbook_path))[1]

    # For each project, add its agents info in the global variable within the key with the same name of the project folder
    for proj in projects_list:
        projects[proj] = {}
        projects[proj]['agents_info'] = {}

        # The path to the config folder inside the project
        agents_path = cloudbook_path + os.sep + proj + os.sep + "agents"

        # List with the files inside "cloudbook/projectX/agents/" folder
        files = next(os.walk(agents_path))[2]

        # Cleaning. If file does not contain "config_" it is not an agent config file
        files = [file for file in files if 'config_' in file and ".json" in file]

        for file in files:
            projects[proj]['agents_info'][files.index(file)] = loader.load_dictionary(agents_path + os.sep + file)

    print("PROJECTS:\n", projects)

    return



# This tab class includes all the information related to the different agents that live in the machine (in a project).
class GeneralInfoTab (ttk.Frame):

    agent_pid_dict = {}
    agents_info = {}
    project_name = ""

    #Builds the layout and fills it.
    def __init__(self, *args, agents_info, project_name):
        super().__init__(*args)

        self.agents_info = agents_info
        self.project_name = project_name

        print("Active processes: ", self.agent_pid_dict, "\n")

        self.label_welcome = ttk.Label(self)
        self.label_welcome["text"] = ("Welcome to CloudBook user interface. Your agents are:")
        self.label_welcome.grid(row=0, column=0, columnspan=4, padx=100, pady=10)
        title_bar = [" Agent ID ", " Grant ", " Status ", "", "", ""]
        h = int(len(self.agents_info)+1)
        w = 6
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
                        if self.agents_info[i-1]['AGENT_ID'] in self.agent_pid_dict:
                            self.launch_button.config(state="disabled")
                        else:
                            self.launch_button.config(state="normal")
                    elif(j==w-2):
                        self.stop_button = ttk.Button(self, text="Stop", command=lambda r=i+2, c=j: self.stop(r, c))
                        self.stop_button.grid(column=j, row=i+2)
                        if self.agents_info[i-1]['AGENT_ID'] in self.agent_pid_dict:
                            self.stop_button.config(state="normal")
                        else:
                            self.stop_button.config(state="disabled")
                    elif(j==w-1):
                        self.remove_button = ttk.Button(self, text="Remove", command=lambda r=i+2, c=j: self.remove(r, c))
                        self.remove_button.grid(column=j, row=i+2)
                        if self.agents_info[i-1]['AGENT_ID'] in self.agent_pid_dict:
                            self.remove_button.config(state="disabled")
                        else:
                            self.remove_button.config(state="normal")
                    elif(j==w-4):
                        self.cell=ttk.Label(self)
                        if self.agents_info[i-1]['AGENT_ID'] in self.agent_pid_dict:
                            self.cell["foreground"] = "green"
                            self.cell["text"] = "RUNNING"
                        else:
                            self.cell["foreground"] = "red"
                            self.cell["text"] = "STOPPED"
                        self.cell.grid(row=i+2, column=j)
                    else:
                        agent_circle_and_grant = {k: self.agents_info[i-1][k] for k in ('AGENT_ID', 'GRANT_LEVEL')}
                        minidict = list(agent_circle_and_grant.values())
                        self.cell = ttk.Label(self)
                        self.cell["text"] = minidict[j]
                        self.cell.grid(row=i+2, column=j)


    #Functionality of the "Launch" button
    def launch(self, r, c):
        agent_id = self.agents_info[r-3]['AGENT_ID']
        print("Launching agent", agent_id)
        if(platform.system()=="Windows"):
        	proc = subprocess.Popen("py agent.py "+ agent_id + " " + self.project_name, shell=True ,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
        	proc = subprocess.Popen("python3 agent.py "+ agent_id + " " + self.project_name, shell=True, preexec_fn=os.setsid)
        self.agent_pid_dict[agent_id] = proc
        time.sleep(2)
        app.refresh()
        
    #Functionality of the "Stop" button.
    def stop(self, r, c):
        agent_id = self.agents_info[r-3]['AGENT_ID']
        print("Stopping agent", agent_id, self.agent_pid_dict[agent_id])
        if(platform.system()=="Windows"):
            self.agent_pid_dict[agent_id].send_signal(signal.CTRL_BREAK_EVENT)
            self.agent_pid_dict[agent_id].kill()
        else:
            os.killpg(os.getpgid(self.agent_pid_dict[agent_id].pid), signal.SIGTERM)
        del  self.agent_pid_dict[agent_id]
        print("Active processes: ", self.agent_pid_dict, "\n")
        app.refresh()

    #Functionality of the "Remove" button.
    def remove(self, r, c):
        agent_id = self.agents_info[r-3]['AGENT_ID']
        agents_path = cloudbook_path + os.sep + self.project_name + os.sep + "agents"   # Path to "cloudbook/projectX/agents/"
        config_agent_file_path = agents_path + os.sep + "config_" + agent_id + ".json"

        if agent_id in self.agent_pid_dict:
            print(agent_id + " is running! It must be stopped to be removed.")
            return
        if os.path.exists(config_agent_file_path):
            os.remove(config_agent_file_path)
        else:
            print("ERROR: could not find " + config_agent_file_path + ". Removal aborted.")
            return
        app.refresh()



# This tab includes the information and tools to create a new agent.
class AddAgentTab(ttk.Frame):

    agents_info = {}
    project_name = ""
    is_agent_0 = None

    def __init__(self, *args, agents_info, project_name):
        super().__init__(*args)
        self.is_agent_0 = BooleanVar()

        self.agents_info = agents_info
        self.project_name = project_name

        self.label_welcome = ttk.Label(self)
        self.label_welcome["text"] = ("Create a new agent and attachs to local default circle \'LOCAL\'. \n All you need is to write up the circle ID you want to create or attach to.")
        self.label_welcome.grid(column=0, row=1, columnspan=3)
        
        # self.circle_label = ttk.Label(self)
        # self.circle_label["text"]=("Circle ID")
        # self.circle_label.grid(column=0, row=2)
        # self.circle_entry = ttk.Entry(self, text="LOCAL")
        # self.circle_entry["state"]=(tk.DISABLED)
        # self.circle_entry.grid(column=1, row=2)
        # self.set_circle_button = ttk.Button(self, text="Set", command=self.set_circle_ID)
        # self.set_circle_button['state']='disable'
        # self.set_circle_button.grid(column=2, row=2)

        self.grant_label = ttk.Label(self)
        self.grant_label["text"] = ("Grant Level")
        self.grant_label.grid(column=0, row=3)
        self.grant_combo = ttk.Combobox(self)
        self.grant_combo = ttk.Combobox(self, state="readonly")
        self.grant_combo["values"] = ["HIGH", "MEDIUM", "LOW",]
        self.grant_combo.current(1)
        self.grant_combo.grid(column=1, row=3)

        ttk.Label(self, text="Filesystem path").grid(column=0, row=4)
        self.fspath = ttk.Entry(self)
        self.fspath["state"] = (tk.DISABLED)
        self.fspath.grid(column=1, row=4)
        self.browse_fs_path_button = ttk.Button(self, text="Select", command=self.browse_FS_path)
        self.browse_fs_path_button.grid(column=2, row=4)

        self.checkbutton_agent_0 = ttk.Checkbutton(self, text="Create the agent with id=0.", \
            variable=self.is_agent_0, onvalue=True, offvalue=False)
        self.checkbutton_agent_0.grid(column=0, row=5, columnspan=3)

        self.create_circle = ttk.Button(self, text="Create agent and attach", command=self.create)
        #self.attach_circle = ttk.Button(self, text="Attach circle", command=self.attach)
        self.create_circle.grid(column=1, row=7)
    
    def switch(self, index):
            switcher = {
                0: "HIGH",
                1: "MEDIUM",
                2: "LOW"
            }  
            return switcher.get(index, "No se ha seleccionado nada, se usará MEDIUM como valor por defecto.")
    
    #Functionality for create button. Recovers the already set information and
    #calls the create_local_agent function located in the agent.py software.
    def create(self):
        grant = self.switch(self.grant_combo.current())
        print("Grant selected: : ", grant)
        fspath = self.fspath.get()
        print("Path to distributed filesystem: ", fspath)
        if self.is_agent_0.get():
            print("Creating agent with id=0.")
        agent.create_agent(grant=grant, project_name=self.project_name, fs=fspath, agent_0=self.is_agent_0.get())
        app.refresh()
    
    #This button launches a new gui to select the folder for the FS path.
    #This parameter is optional.
    def browse_FS_path(self):
        filename = filedialog.askdirectory()
        self.fspath["state"] = (tk.NORMAL)
        self.fspath.insert(0,filename)
        self.fspath["state"] = ("readonly")
        print(filename)



# Tab that contains the information of a specific agent located in the machine.
# It also provides functionality to edit its parameters such as the FS, or the grant.
class AgentXTab(ttk.Frame):

    agent = []
    project_name = ""
    
    def __init__(self, *args, agent, project_name):
        super().__init__(*args)
        self.agent = agent
        self.project_name = project_name

        ttk.Label(self, text=agent['AGENT_ID'], font="bold").grid(column=2, row=0, columnspan=5)
        ttk.Label(self, text="Edit agent info. Please, make sure the agent is stopped before any change.").grid(column=1, row=1, columnspan=5)

        #ttk.Label(self, text="Circle ID:").grid(column=1, row=3, sticky='w')
        #ttk.Label(self, text=agent['CIRCLE_ID']).grid(column=3, row=3, sticky='w')
        # self.text = ttk.Entry(self, state="readonly")
        # self.text.grid(column=6, row=3)
        # self.edit_circle_id_button = ttk.Button(self, text='Edit', command=self.edit_circle_id)
        # self.edit_circle_id_button['state']='disable'
        # self.edit_circle_id_button.grid(column=8, row=3)

        ttk.Label(self, text="Grant level:").grid(column=1, row=4, sticky='w')
        ttk.Label(self, text=agent['GRANT_LEVEL']).grid(column=3, row=4, sticky='w')
        self.combo = ttk.Combobox(self, state="readonly")
        self.combo["values"] = ["HIGH", "MEDIUM", "LOW"]
        self.combo.current({"HIGH":0, "MEDIUM":1, "LOW":2}.get(agent['GRANT_LEVEL']))
        self.combo.grid(column=6, row=4)
        #self.combo.bind(set_grant)
        ttk.Button(self, text='Edit', command=self.set_grant).grid(column=8, row=4)

        ttk.Label(self, text="Filesystem Path:").grid(column=1, row=5, sticky='w')
        textfs = agent['DISTRIBUTED_FS']
        ttk.Label(self, text="..."+textfs[-27:]).grid(column=3, row=5, sticky='w')
        self.fspath = ttk.Entry(self)
        self.fspath["state"] = (tk.DISABLED)
        self.fspath.grid(column=6, row=5)
        self.browse_fs_path_button = ttk.Button(self, text="Select", command=self.browse_FS_path)
        self.browse_fs_path_button.grid(column=8, row=5)


    #To be added when the functionality is implemented.
    # def edit_circle_id(self):
    #     print("En el campo pone: " + self.text.get() + " del agente " + self.agent['AGENT_ID'])

    #Functionality to edit the agent grant. It calls to the "edit_agent()" function in the 
    # agent software.
    def set_grant(self):
        def switch(index):
            switcher = {
                0: "HIGH",
                1: "MEDIUM",
                2: "LOW"
            }  
            return switcher.get(index, "No grant selected.")
        print("The new grant for agent " + self.agent['AGENT_ID'] + " is: " + switch(self.combo.current()))
        agent.edit_agent(agent_id=self.agent['AGENT_ID'], project_name=self.project_name, new_grant=switch(self.combo.current()))
        app.refresh()
        
    #This button launches a new gui to select another folder for the FS path. 
    def browse_FS_path(self):
        new_fs_path = filedialog.askdirectory()
        self.fspath["state"] = (tk.NORMAL)
        self.fspath.insert(0,new_fs_path)
        self.fspath["state"] = ("readonly")
        print("The new path for the agent " + self.agent['AGENT_ID'] + " is: " + new_fs_path)
        agent.edit_agent(agent_id=self.agent['AGENT_ID'], project_name=self.project_name, new_fs=new_fs_path)



# Tab that represents a project. It conatins all the tabs refering to a project.
class ProjectTab(ttk.Frame):
    def __init__(self, *args, project_name):
        super().__init__(*args)

        agents_info = projects[project_name]['agents_info']

        self.notebook = ttk.Notebook(self)
        
        self.tab1 = GeneralInfoTab(self.notebook, agents_info=agents_info, project_name=project_name)
        self.notebook.add(self.tab1, text="General Info", padding=10)

        self.tab2 = AddAgentTab(self.notebook, agents_info=agents_info, project_name=project_name)
        self.notebook.add(self.tab2, text="Add Agents", padding=10)

        for info in agents_info:
            globals()['self.'+str(info)] = AgentXTab(self.notebook, agent=agents_info[info], project_name=project_name)
            self.notebook.add(globals()['self.'+str(info)], text="Agent "+str(info), padding=10)

        self.notebook.pack(expand=True, fill="both")
        self.pack(expand=True, fill="both")



# New tab reserved for future use.
# class Tab3(ttk.Frame):
#     def __init__(self, *args):
#         super().__init__(*args)



# Class to build the general framework of the GUI.
# Inside this object, the different tabs are constructed. It also includes a "Refresh" button.
class Application(ttk.Frame):

    def __init__(self, master):
        super().__init__(master)
        master.title("CloudBook Agent GUI")

        self.notebook = ttk.Notebook(self)

        #self.tabProject1 = ProjectTab(self.notebook)
        #self.notebook.add(self.tabProject1, text="Tab del project 1", padding=10)

        for project in projects:
            self.notebook.add(ProjectTab(self.notebook, project_name=project), text=project, padding=10)
        
        # self.tab1 = GeneralInfoTab(self.notebook)
        # self.notebook.add(self.tab1, text="General Info", padding=10)
        
        # self.tab2 = AddAgentTab(self.notebook)
        # self.notebook.add(self.tab2, text="Add Agents", padding=10)
        
        # for info in agents_info:
        #     globals()['self.'+str(info)] = AgentXTab(self.notebook, agent=agents_info[info])
        #     self.notebook.add(globals()['self.'+str(info)], text="Agent "+str(info), padding=10)

        #Refresh button created
        tk.Button(self, text="Refresh", command=self.refresh).pack()
        self.notebook.pack(expand=True, fill="both")
        self.pack(expand=True, fill="both")
    
    #Functionality for refresh button. Basically it rebuilds the framework.
    def refresh(self):
        get_info()
        # self.tab1.destroy()
        # self.tab2.destroy()
        self.notebook.destroy()
        self.notebook = ttk.Notebook(self)

        # self.tabProject1 = ProjectTab(self.notebook)
        # self.notebook.add(self.tabProject1, text="Tab del project 1", padding=10)
        for project in projects:
            self.notebook.add(ProjectTab(self.notebook, project_name=project), text=project, padding=10)


        # self.tab1 = GeneralInfoTab(self.notebook)
        # self.notebook.add(
        #     self.tab1, text="General Info", padding=10)
        
        # self.tab2 = AddAgentTab(self.notebook)
        # self.notebook.add(
        #     self.tab2, text="Add Agents", padding=10)
        
        # for info in agents_info:
        #     globals()['self.'+str(info)] = AgentXTab(self.notebook, agent=agents_info[info])
        #     self.notebook.add(
        #         globals()['self.'+str(info)], text="Agent "+str(info), padding=10)

        self.notebook.pack(expand=True, fill="both")
        self.pack(expand=True, fill="both")

def on_closing():
    if tk.messagebox.askokcancel("Quit", "Are you sure to exit the program?\nPlease, make sure no agents are running."):
        os._exit(0)


#Start application
get_info()
master = tk.Tk()
app = Application(master)
master.protocol("WM_DELETE_WINDOW", on_closing)
app.mainloop()
