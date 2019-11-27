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
	#print("projects_list:", projects_list)

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

	#print("PROJECTS:\n", projects)

def sigint_handler(*args):
	print("\n\nAll running agents on any project (if any) will be stopped...")
	kill_all_processes()
	print("\nExiting program...\n")
	os._exit(0)


def on_closing():
	if tk.messagebox.askokcancel("Quit", "Are you sure to close the program?\nAny running agent will be stopped."):
		sigint_handler()
	print("Program not exited. Everything is kept the same.\n")


def kill_all_processes():
	for proj in projects:
		for active_agent in projects[proj]["agent_pid_dict"].keys():
			active_proc = projects[proj]["agent_pid_dict"][active_agent]
			print("Killing process:", active_proc)
			kill_process(active_proc)
		projects[proj]["agent_pid_dict"] = {}


def kill_process(proc):
	if(platform.system()=="Windows"):
		# proc.send_signal(signal.CTRL_BREAK_EVENT)
		# proc.kill()
		kill_tree_command = "TASKKILL /F /T /PID "+str(proc.pid)
		os.system(kill_tree_command)	
	else:
		os.killpg(os.getpgid(proc.pid), signal.SIGTERM)



#####   GUI CLASSES   #####

# This tab class includes all the information related to the different agents that live in the machine (in a project).
class GeneralInfoTab (ttk.Frame):

	# Builds the layout and fills it.
	def __init__(self, *args, agents_info, project_name):
		super().__init__(*args)
		global projects

		self.agents_info = agents_info
		self.project_name = project_name

		title_bar = [" Agent ID ", " Grant ", " Status ", "", "", ""]
		h = int(len(self.agents_info)+1)
		w = 6

		self.label_welcome = ttk.Label(self)
		self.label_welcome["text"] = ("Welcome to CloudBook user interface. Your agents are:")
		self.label_welcome.grid(row=0, column=0, columnspan=w-3, padx=100, pady=10)

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
			proc = subprocess.Popen("py agent.py -agent_id " + agent_id + " -project_folder " + self.project_name, shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
		else:
			proc = subprocess.Popen("python3 agent.py "+ agent_id + " " + self.project_name, shell=True, preexec_fn=os.setsid)
		projects[self.project_name]["agent_pid_dict"][agent_id] = proc
		print("Active processes: ", projects[self.project_name]["agent_pid_dict"], "\n")
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

	def __init__(self, *args, agents_info, project_name):
		super().__init__(*args)
		self.is_agent_0 = BooleanVar()

		self.agents_info = agents_info
		self.project_name = project_name

		# Check if the project already has an agent_0
		self.has_agent_0 = False
		for i in self.agents_info:
			if self.agents_info[i]['AGENT_ID']=='agent_0':
				self.has_agent_0 = True

		# Configure the grid
		for col in range(5):
			Grid.columnconfigure(self, col, weight=1)
		for row in range(8):
			Grid.rowconfigure(self, row, weight=1)

		# Info labels
		self.label_info1 = ttk.Label(self, text="This tab allows you to create agents.")
		self.label_info1.grid(row=0, column=1, columnspan=3, sticky=E+W)

		self.label_info2 = ttk.Label(self, text="Note: you need one agent with id=0 in the project to be able to run it.")
		self.label_info2.grid(row=1, column=1, columnspan=3, sticky=E+W)

		ttk.Label(self, text="").grid(row=2, column=0, sticky=E+W) # Line separator

		# Grant label and combobox
		self.grant_label = ttk.Label(self, text="Grant Level")
		self.grant_label.grid(row=3, column=1, sticky=E+W)

		self.grant_combo = ttk.Combobox(self, state="readonly")
		self.grant_combo["values"] = ["HIGH", "MEDIUM", "LOW",]
		self.grant_combo.current(1)
		self.grant_combo.grid(row=3, column=2, sticky=E+W)

		# Fspath label, entry and button
		self.fspath_label = ttk.Label(self, text="Filesystem path")
		self.fspath_label.grid(row=4, column=1, sticky=E+W)

		self.fspath_entry = ttk.Entry(self)
		self.fspath_entry["state"] = (tk.DISABLED)
		self.fspath_entry.grid(row=4, column=2, sticky=E+W)

		self.fspath_button = ttk.Button(self, text="Select", command=self.browse_fspath)
		self.fspath_button.grid(row=4, column=3, sticky=E+W)

		# Agent with id=0 checkbutton
		self.checkbutton_agent_0 = ttk.Checkbutton(self, text="Create the agent with id=0.", \
			variable=self.is_agent_0, onvalue=True, offvalue=False)
		self.checkbutton_agent_0.grid(row=5, column=2, sticky=E+W)
		# This checkbox is disabled if there is already an agent_0
		if self.has_agent_0:
			self.checkbutton_agent_0["state"] = (tk.DISABLED)

		ttk.Label(self, text="").grid(row=6, column=0, sticky=E+W) # Line separator

		# Create agent button
		self.create_agent_button = ttk.Button(self, text="Create agent", command=self.create)
		self.create_agent_button.grid(row=7, column=2, sticky=E+W)
	
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
		print("Grant selected:", grant)
		fspath = self.fspath_entry.get()
		if fspath != "":
			print("Path to distributed filesystem:", fspath)
		else:
			print("Default path to distributed filesystem.")
		if self.is_agent_0.get():
			print("Creating agent with id=0.")
		agent.create_agent(grant=grant, project_name=self.project_name, fs=fspath, agent_0=self.is_agent_0.get())
		app.refresh()
	
	# This button launches a new gui to select the folder for the FS path. This parameter is optional.
	def browse_fspath(self):
		filename = filedialog.askdirectory()
		self.fspath_entry["state"] = (tk.NORMAL)
		self.fspath_entry.insert(0,filename)
		self.fspath_entry["state"] = ("readonly")
		print(filename)


# Tab that contains the information of a specific agent located in the machine.
# It also provides functionality to edit its parameters such as the FS, or the grant.
class AgentXTab(ttk.Frame):
	
	def __init__(self, *args, agent, project_name):
		super().__init__(*args)
		self.agent = agent
		self.project_name = project_name

		# Configure the grid
		for col in range(6):
			Grid.columnconfigure(self, col, weight=1)
		for row in range(5):
			Grid.rowconfigure(self, row, weight=1)

		# Agent name label
		self.label_name = ttk.Label(self, text=agent['AGENT_ID'], font=("Helvetica", 12, "bold"))
		self.label_name.grid(row=0, column=0, columnspan=6)

		# Info label
		self.label_info = ttk.Label(self, text="Edit agent info. Please, make sure the agent is stopped before any change.")
		self.label_info.grid(row=1, column=0, columnspan=6)

		# Grant label, value_label combobox and button
		self.grant_label = ttk.Label(self, text="Grant level:")
		self.grant_label.grid(row=2, column=1, sticky=E+W)

		self.grant_value_label = ttk.Label(self, text=agent['GRANT_LEVEL'])
		self.grant_value_label.grid(row=2, column=2, sticky=E+W)

		self.grant_combobox = ttk.Combobox(self, state="readonly")
		self.grant_combobox["values"] = ["HIGH", "MEDIUM", "LOW"]
		self.grant_combobox.current({"HIGH":0, "MEDIUM":1, "LOW":2}.get(agent['GRANT_LEVEL']))
		self.grant_combobox.grid(row=2, column=3, sticky=E+W)

		self.grant_button = ttk.Button(self, text='Edit', command=self.set_grant)
		self.grant_button.grid(row=2, column=4, sticky=E+W)

		# Fspath label, value_label, combobox and button
		self.fspath_label = ttk.Label(self, text="Filesystem Path:")
		self.fspath_label.grid(row=3, column=1, sticky=E+W)

		self.fspath_value_label = ttk.Label(self, text="..."+agent['DISTRIBUTED_FS'][-27:], width=30)
		self.fspath_value_label.grid(row=3, column=2, sticky=E+W)

		self.fspath_entry = ttk.Entry(self)
		self.fspath_entry["state"] = (tk.DISABLED)
		self.fspath_entry.grid(row=3, column=3, sticky=E+W)

		self.fspath_button = ttk.Button(self, text="Select", command=self.browse_fspath)
		self.fspath_button.grid(row=3, column=4, sticky=E+W)


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
		print("The new grant for agent " + self.agent['AGENT_ID'] + " is: " + switch(self.grant_combobox.current()))
		agent.edit_agent(agent_id=self.agent['AGENT_ID'], project_name=self.project_name, new_grant=switch(self.grant_combobox.current()))
		app.refresh()
		
	# Functionality of the browse button. Launches a folder selection gui to select the FS path. 
	def browse_fspath(self):
		new_fs_path = filedialog.askdirectory()
		self.fspath_entry["state"] = (tk.NORMAL)
		self.fspath_entry.insert(0,new_fs_path)
		self.fspath_entry["state"] = ("readonly")
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

	def __init__(self, root):
		super().__init__(root)
		root.title("CloudBook Agent GUI")

		self.notebook = ttk.Notebook(self)
		tk.Button(self, text="Refresh", command=self.refresh, width=10).grid(row=0, column=3, sticky=E+W)
		tk.Button(self, text="Stop all agents", command=self.stop_all_agents, width=10).grid(row=0, column=4, sticky=E+W)

		self.refresh()
	
	# Functionality for refresh button. Basically it rebuilds the framework.
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

		self.notebook.grid(row=2, column=0, columnspan=8, sticky=E+W)
		self.pack(expand=True, fill="both")

	# Functionality for Stop all processes button.
	def stop_all_agents(self):
		kill_all_processes()
		self.refresh()


#####   GUI MAIN   #####
if __name__ == '__main__':
	# If the system is Windows, set ID (arbitrary) to use icon also in the taskbar
	if(platform.system()=="Windows"):
		import ctypes
		ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Cloudbook_GUI')

	# Create tkinter and application
	root = tk.Tk()
	app = Application(root)

	# Set the icons to use
	icon_16x16 = PhotoImage(file='cloudbook_icon_16x16.gif')
	icon_full = PhotoImage(file='cloudbook_icon_full.gif')
	root.tk.call('wm', 'iconphoto', root._w, icon_full, icon_16x16)

	# Set handlers for Ctrl+C and closing operations
	root.protocol("WM_DELETE_WINDOW", on_closing)
	signal.signal(signal.SIGINT, sigint_handler)

	# Run the application forever (until closed)
	app.mainloop()
