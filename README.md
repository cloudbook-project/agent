# agent
component in charge of execute deployable units
Working only with Python 3.X
Requires:
  pip3 install flask
  pip3 install pynat
  pip3 install urllib

Format as tool (command usage):
`python agent.py "AGENT_GRANT" "FS_PATH" CIRCLE_ID`
CIRCLE_ID Can be LOCAL
example:
`python agent.py "HIGH" "./FS/" LOCAL`

In order to start execution: `http://localhost/invoke?invoked_function=du_0.main'`


