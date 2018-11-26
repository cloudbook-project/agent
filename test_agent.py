import agent, configure_agent, loader
import sys, json, ast


# We suppose that the agent has a configuration file.

cloudbook = {"du_0": {"agent0", "agent1", "agent3"}, "du_1": {"agent0", "agent2", "agent5"}, "du_2": {"agent4", "agent6", "agent2"}, "du_3": {"agent7"}, "du_4": {"agent8", "agent9", "agent0"}}


with open("./cloudbook_agents.json", 'w') as file:
		
	file.write(str(cloudbook))
	file.close()

aux = {}
with open("./cloudbook_agents.json", "r") as file:
    
    txt = str(file.read())
    print(txt)
    aux = dict(ast.literal_eval(txt))
    #print (aux["du_0"])
    for du in aux:
        print (du)
        for agent in aux[du]:
            print(agent)
    