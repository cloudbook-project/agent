import os, random, string, json
import loader

#load config file
config_dict=loader.load_dictionary("./config_agent.json")

#Creates an agent ID in case it hasn't been created before, and writes it in configuration file
def createAgentID():
    #Random agent_id if it doesn't exist
    my_agent_ID= ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
    if config_dict["AGENT_ID"]=="0":
    	config_dict["AGENT_ID"]=my_agent_ID
    else:
    	my_agent_ID=config_dict["AGENT_ID"]
    my_circle_ID=config_dict["CIRCLE_ID"]
    fo = open("config_agent.json", 'w')
    json_data=json.dumps(config_dict)
    fo.write(json_data)
    fo.close()
    return (my_agent_ID, my_circle_ID)


#Sets grant level of this agent
def setGrantLevel(level, my_agent_ID):
	if level in ("LOW", "MEDIUM", "HIGH"):
		config_dict["GRANT_LEVEL"]=level
		#Config has been set, now, lets write it in agents_grant.json
		#Checking if file is empty, if so, write the IP directly.
		if os.stat("./cloudbook/agent_grant.json").st_size==0:
			fo = open("./cloudbook/agent_grant.json", 'w')
			data={}
			data[my_agent_ID]={}
			data[my_agent_ID]={}
			data[my_agent_ID]=level
			json_data=json.dumps(data)
			fo.write(json_data)	
			fo.close()
		# File not empty, so we open it to check if the agent has been already written on it.
		else:
			fr = open("./cloudbook/agent_grant.json", 'r')
			directory = json.load(fr)
			if my_agent_ID in directory:
				directory[my_agent_ID]=level
				fo = open("./cloudbook/agent_grant.json", 'w')
				directory= json.dumps(directory)
				fo.write(directory)
				fo.close()
				return
		# if agent not already written, we append it.
			fr = open("./cloudbook/agent_grant.json", 'r')
			directory = json.load(fr)
			directory[my_agent_ID]={}
			directory[my_agent_ID]=level
			fo = open("./cloudbook/agent_grant.json", 'w')
			directory= json.dumps(directory)
			fo.write(directory)
			fo.close()
		return
