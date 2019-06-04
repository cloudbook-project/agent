# agent
Component in charge of execute deployable units  
Working only with Python 3.X  
Requires (install with pip3): flask, pynat, urllib

Right now it is developed to run in a local environment It can be launched in two modes: through the GUI or by command line.

- Launching agents with the GUI:

	`python gui.py`

	And follow the friendly instructions to create and launch agents.
 
- Launching agent with the command line:

	`python agent.py "AGENT_GRANT" "FS_PATH" "CIRCLE_ID"`  

	CIRCLE_ID can be LOCAL  
	example:  
	`python agent.py "HIGH" "./FS/" LOCAL`  
  
When the agents are launched and the DUs have been loaded the execution can be started with:
`http://localhost/invoke?invoked_function=du_0.main'`


