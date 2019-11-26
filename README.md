# agent

Component in charge of executing the deployable units


### Requirements

Working only with Python 3.X
Requires (install with pip3): flask, pynat, urllib

###### Note: any extra library that has to be imported in the code to execute, must be installed previously in the machine (i.e. pygame)


### Features

Currently, the Agent is capable of performing the following tasks:
- Configure itself with the corresponding files: the project configuration file (./distributed/config.json) and its own (./agents/config_agent_XX.json).
- Stay idle until the deployer indicates the DUs to load (./distributed/cloudbook.json) and then load the required DUs overwriting their invoke function for an agent function that knows the IPs and ports  of the agents (obtained reading the file ./distributed/agents_grant.json) to be able to send requests to them.
- Launch an http server to allow receiving requests from other agents.
- Create a stats file periodically (./distributed/stats/stats_agent_XX.json) every AGENT_STATS_INTERVAL seconds.
- Create a grant file periodically (./distributed/agents_grant/agent_XX_grant.json) every AGENT_GRANT_INTERVAL seconds.
- Write alarm files (./distributed/WARNING and ./distributed/CRITICAL) when different errors are detected.
- Carry on redeployments when indicated by the deployer with the redeployment files (./distributed/HOT_REDEPLOY and ./distributed/COLD_REDEPLOY). This includes the reloading of the needed DUs and managing the state in order not to produce more alarms than necessary.


### How to use

There are two possibilities to launch agents. They can be launched through the GUI or one by one in a terminal/command line.

###### Note: the GUI method is the most recommended as the command line will leave open subprocesses otherwise (and those have to be closed manually)

- Launching agents with the GUI:

	`python gui.py`

	And follow the friendly instructions to create and launch agents.
 
- Launching agent with the terminal/command line:

	`python agent.py -agent_id <agent_id> -project_folder <project_folder>`  

	Example:  
	`python agent.py -agent_id agent_0 -project_folder NBody`  
  
