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



#####   GLOBAL VARIABLES   #####

# Global variable to store information about all the agents of all the projects.
projects = {}

# Global variable to store the general path to cloudbook, used to access all files and folders needed
if(platform.system()=="Windows"):
	cloudbook_path = os.environ['HOMEDRIVE'] + os.environ['HOMEPATH'] + os.sep + "cloudbook"
else:
	cloudbook_path = os.environ['HOME'] + os.sep + "cloudbook"



#####   GUI FUNCTIONS   #####

# This function recovers the information about the different agents using their configuration files.
# Then the information is saved on a variable that will be used later.
def get_info():
	global projects         # Use the global variable projects
	global cloudbook_path   # Use the global variable cloudbook_path

	# Check the existence of the general path to cloudbook
	if not os.path.exists(cloudbook_path):
		os.makedirs(cloudbook_path)

	# List with the folders inside "cloudbook/" folder. Each one represents a different project
	projects_list = next(os.walk(cloudbook_path))[1]
	print("projects_list:", projects_list)

	# Clean the possible processes running in projects deleted
	deletable_projects = []
	for proj in projects:
		if proj not in projects_list:
			print("WARNING: project " + proj + " has been deleted. All running agents on that project (if any) will be stopped.")
			for active_agent in projects[proj]["agent_pid_dict"].keys():
				active_proc = projects[proj]["agent_pid_dict"][active_agent]
				print("Killing process:", active_proc)
				kill_process(active_proc)
			deletable_projects.append(proj)

	for deletable_project in deletable_projects:
		del projects[deletable_project]

	# For each project, add its agents info in the global variable within the key with the same name of the project folder
	for proj in projects_list:
		if proj not in projects:
			projects[proj] = {}
			projects[proj]['agent_pid_dict'] = {}
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


def on_closing():
	if tk.messagebox.askokcancel("Quit", "Are you sure to close the program?\nAny running agent will be stopped."):
		# Clean the possible processes running before exiting the program
		print("\n\nAll running agents on any project (if any) will be stopped...")
		for proj in projects:
			for active_agent in projects[proj]["agent_pid_dict"].keys():
				active_proc = projects[proj]["agent_pid_dict"][active_agent]
				print("Killing process:", active_proc)
				kill_process(active_proc)
		print("\nExiting program...\n")
		os._exit(0)
	print("Program not exited. Everything is kept the same.\n")


def kill_process(proc):
	if(platform.system()=="Windows"):
		proc.send_signal(signal.CTRL_BREAK_EVENT)
		proc.kill()
	else:
		os.killpg(os.getpgid(proc.pid), signal.SIGTERM)


#####   GUI CLASSES   #####

# This tab class includes all the information related to the different agents that live in the machine (in a project).
class GeneralInfoTab (ttk.Frame):

	agents_info = {}
	project_name = ""

	# Builds the layout and fills it.
	def __init__(self, *args, agents_info, project_name):
		super().__init__(*args)
		global projects

		self.agents_info = agents_info
		self.project_name = project_name

		print("Active processes: ", projects[project_name]["agent_pid_dict"], "\n")

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
						if self.agents_info[i-1]['AGENT_ID'] in projects[project_name]["agent_pid_dict"]:
							self.launch_button.config(state="disabled")
						else:
							self.launch_button.config(state="normal")
					elif(j==w-2):
						self.stop_button = ttk.Button(self, text="Stop", command=lambda r=i+2, c=j: self.stop(r, c))
						self.stop_button.grid(column=j, row=i+2)
						if self.agents_info[i-1]['AGENT_ID'] in projects[project_name]["agent_pid_dict"]:
							self.stop_button.config(state="normal")
						else:
							self.stop_button.config(state="disabled")
					elif(j==w-1):
						self.remove_button = ttk.Button(self, text="Remove", command=lambda r=i+2, c=j: self.remove(r, c))
						self.remove_button.grid(column=j, row=i+2)
						if self.agents_info[i-1]['AGENT_ID'] in projects[project_name]["agent_pid_dict"]:
							self.remove_button.config(state="disabled")
						else:
							self.remove_button.config(state="normal")
					elif(j==w-4):
						self.cell=ttk.Label(self)
						if self.agents_info[i-1]['AGENT_ID'] in projects[project_name]["agent_pid_dict"]:
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


	# Functionality of the "Launch" button
	def launch(self, r, c):
		global projects
		agent_id = self.agents_info[r-3]['AGENT_ID']
		print("Launching agent", agent_id)
		if(platform.system()=="Windows"):
			proc = subprocess.Popen("py agent.py "+ agent_id + " " + self.project_name, shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
		else:
			proc = subprocess.Popen("python3 agent.py "+ agent_id + " " + self.project_name, shell=True, preexec_fn=os.setsid)
		projects[self.project_name]["agent_pid_dict"][agent_id] = proc
		print("Active processes: ", projects[self.project_name]["agent_pid_dict"], "\n")
		time.sleep(2)
		app.refresh()
		
	# Functionality of the "Stop" button.
	def stop(self, r, c):
		global projects
		agent_id = self.agents_info[r-3]['AGENT_ID']
		print("Stopping agent", agent_id, projects[self.project_name]["agent_pid_dict"][agent_id])
		kill_process(projects[self.project_name]["agent_pid_dict"][agent_id])
		del projects[self.project_name]["agent_pid_dict"][agent_id]
		print("Active processes: ", projects[self.project_name]["agent_pid_dict"], "\n")
		app.refresh()

	# Functionality of the "Remove" button.
	def remove(self, r, c):
		global projects
		agent_id = self.agents_info[r-3]['AGENT_ID']
		agents_path = cloudbook_path + os.sep + self.project_name + os.sep + "agents"   # Path to "cloudbook/projectX/agents/"
		config_agent_file_path = agents_path + os.sep + "config_" + agent_id + ".json"

		if agent_id in projects[self.project_name]["agent_pid_dict"]:
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
	
	# Functionality for the grant combobox selection
	def switch(self, index):
		switcher = {
			0: "HIGH",
			1: "MEDIUM",
			2: "LOW"
		}
		return switcher.get(index, "No se ha seleccionado nada, se usará MEDIUM como valor por defecto.")
	
	# Functionality for create button. Recovers the already set information and calls the create_agent function from agent.py
	def create(self):
		grant = self.switch(self.grant_combo.current())
		print("Grant selected: : ", grant)
		fspath = self.fspath.get()
		print("Path to distributed filesystem: ", fspath)
		if self.is_agent_0.get():
			print("Creating agent with id=0.")
		agent.create_agent(grant=grant, project_name=self.project_name, fs=fspath, agent_0=self.is_agent_0.get())
		app.refresh()
	
	# This button launches a new gui to select the folder for the FS path. This parameter is optional.
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


	# To be added when the functionality is implemented.

	# Functionality to edit the agent grant. It calls "edit_agent()" function in agent.py.
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
		
	# Functionality of the browse button. Launches a folder selection gui to select the FS path. 
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

		self.tabs = {}

		self.tabs["GeneralInfoTab"] = GeneralInfoTab(self.notebook, agents_info=agents_info, project_name=project_name)
		self.notebook.add(self.tabs["GeneralInfoTab"], text="General Info", padding=10)

		self.tabs["AddAgentTab"] = AddAgentTab(self.notebook, agents_info=agents_info, project_name=project_name)
		self.notebook.add(self.tabs["AddAgentTab"], text="Add Agents", padding=10)

		self.tabs["AgentXTab"] = []
		for info in agents_info:
			# globals()['self.agents_info'+str(info)] = AgentXTab(self.notebook, agent=agents_info[info], project_name=project_name)
			# self.notebook.add(globals()['self.agents_info'+str(info)], text="Agent "+str(info), padding=10)
			self.tabs["AgentXTab"].append(None)
			self.tabs["AgentXTab"][info] = AgentXTab(self.notebook, agent=agents_info[info], project_name=project_name)
			self.notebook.add(self.tabs["AgentXTab"][info], text="Agent "+str(info), padding=10)

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
		tk.Button(self, text="Refresh", command=self.refresh).pack()

		self.refresh()
	
	#Functionality for refresh button. Basically it rebuilds the framework.
	def refresh(self):
		get_info()

		focused_tab = None
		try:
			focused_tab = self.notebook.tab(self.notebook.select(), "text")
		except Exception as e:
			pass
		self.notebook.destroy()
		self.notebook = ttk.Notebook(self)

		for project in projects:
			globals()['ProjectTab_'+project] = ProjectTab(self.notebook, project_name=project)
			self.notebook.add(globals()['ProjectTab_'+project], text=project, padding=10)
		
		if focused_tab is not None:
			try:
				self.notebook.select(globals()["ProjectTab_" + focused_tab])
			except:
				pass

		self.notebook.pack(expand=True, fill="both")
		self.pack(expand=True, fill="both")



#####   GUI MAIN   #####

# Start application
#get_info()
master = tk.Tk()
app = Application(master)
master.protocol("WM_DELETE_WINDOW", on_closing)

# Run the application forever (until closed)
app.mainloop()
