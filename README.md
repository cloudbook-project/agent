# CLOUDBOOK AGENT

The Cloudbook agent component runs in each of the machines of a project and it is in charge of executing the deployable units that the deployer assigned to it.


### Requirements

* Python 3.X
* Windows or Ubuntu (may work on other OS but only designed and tested for these ones)
* Python modules (you can install them with pip3):
	- tkinter (ususally auto-installed with Python 3.X in Windows)
	- flask
	- pynat
	- urllib

_Note: any extra library that has to be imported in the code to execute, must be installed previously in the machine (i.e. if you want to run a game that uses pygame you have to install it previousy in each agent machine)_


### Features

The Agent is capable of performing the following tasks:
- Configure itself with the corresponding files: the project configuration file (./distributed/config.json) and its own (./agents/config_agent_XX.json).
- Stay idle until the deployer indicates the DUs to load (./distributed/cloudbook.json) and then load the required DUs overwriting their invoke function for an agent function that knows the IPs and ports  of the agents (obtained reading the file ./distributed/agents_grant.json) to be able to send requests to them.
- Launch an http server to allow receiving requests from other agents.
- Create a stats file periodically (./distributed/stats/stats_agent_XX.json) every AGENT_STATS_INTERVAL seconds.
- Create a grant file periodically (./distributed/agents_grant/agent_XX_grant.json) every AGENT_GRANT_INTERVAL seconds.
- Write alarm files (./distributed/WARNING and ./distributed/CRITICAL) when different errors are detected.
- Carry on redeployments when indicated by the deployer with the redeployment files (./distributed/HOT_REDEPLOY and ./distributed/COLD_REDEPLOY). This includes the reloading of the needed DUs and managing the state in order not to produce more alarms than necessary.


### How to use

Despite the fact that the graphical interface has been developed thinking on the ease of use, some instructions and advices are included here in order to help those who do not know how cloudbook works.

* Launching the GUI:
	* Option A)
		1. Double-click the "gui.py" file.
	* Option B)
		1. Open a cmd or shell window.
		2. Navigate to the cloudbook agent folder (the cloned/downloaded repository)
		3. Type `python gui.py` and press enter.  (For more info type `gui.py -help`)

* Creating agents with the GUI:
	1. Select the project tab in which you want create the agent.
	2. Select the tab "Add agent".
	3. Click on the dropdown menu to select the grant level (the power you want to lend to the project).
	4. Click on the button "Select" to choose the folder to the distributed filesystem of the project. You should configure this filesystem before launching the agent to avoid problems.
	5. If you want to create the agent_0 (be careful, only the project owner should create it) tick the checkbox below. Note only one agent_0 can be created per project and machine.
	6. Finally click on the "Create agent" button.

* Launching/Stopping/Removing agents with the GUI:
	1. Select the project tab in which you want to launch/stop the agent.
	2. Select the tab "General info".
	3. Identify the agent you want to manipulate and click the corresponding button ("Launch", "Stop" or "Remove") on the same row. Note that an agent must be stopped to be able to be removed.

* Editing the properties of an agent with the GUI:
	1. Select the project tab in which you want to edit the agent properties.
	2. Select the tab "Agent X" where X corresponds to the row in which the agent is showed in the "General info" tab.
	3. As when creating the agent, select the new Grant and/or folder of the distributed filesystem. Note: it is possible to edit one or both parameters at the same time.
	4. Finally click on the "Save changes" button.

_Important note: the GUI is the most recommended method to control the agent for any action (create, launch, stop or delete)._


### ADVANCED USE (using the console)

It is possible to launch the GUI and the agent through a console command, which admits parameters to modify the default behaviour of these. Here is a small manual for this use. **This is only recommended for developers or advanced users**.

* The GUI has the following console syntax:
	`gui.py [-verbose] [-help|-syntax|-info]`
	Example: `gui.py -verbose`
	Options:
	* _Optional_:
		**-verbose**: This option will make the agents print cloudbook information.
		**-help, -syntax, -info**: this option will print this help and syntax info and terminate.


* The agent has the following console syntax:
	`agent.py -agent_id <agent_id> -project_folder <project_folder> [-verbose] [-help|-syntax|-info]`
	Example: `agent.py -agent_id agent_S4MY6ZGKQRT8RTVWLJZP -project_folder NBody -verbose`
	Options:
	* _Mandatory_:
		**-agent_id `<agent_id>`**: this option is used to specify the name of the agent to launch.
		**-project_folder `<project_folder>`**: this option is used to specify the name of the folder containing the agent.
	* _Optional_:
		**-verbose**: this option will make the agent print cloudbook information.
		**-help, -syntax, -info**: this option will print this help and syntax info and terminate.

_Note: the order of the options is not relevant in any of the programs._
_Note 2: unrecognized options will be ignored._
_Note 3: it is possible to do all tasks using the command line, though, this is not recommended because if the program leaves in abnormal conditions the agent may leave open subprocesses (which have to be closed manually with the task manager or similar)._
