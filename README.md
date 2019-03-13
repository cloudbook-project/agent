# agent
component in charge of execute deployable units  
Working only with Python 3.X  
Requires (install with pip3): flask, pynat, urllib  
  
It contains a friendly GUI. It is developed to run in a local environment:  
`python agent.py "AGENT_GRANT" "FS_PATH" CIRCLE_ID`  
CIRCLE_ID Can be LOCAL  
example:  
`python agent.py "HIGH" "./FS/" LOCAL`  
  
In order to start execution: `http://localhost/invoke?invoked_function=du_0.main'`


