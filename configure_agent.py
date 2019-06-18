import os, random, string, json, platform
import loader

#This function edits the filesystem path of an existing agent. It is used by the agent.
#It receives the new filesystem path and the agent ID to edit. It edits the configuration file of the given agent.
def editFSPath(path, my_agent_ID):
	#load config file
	if(platform.system()=="Windows"):
		fs= os.environ['HOMEDRIVE'] + os.environ['HOMEPATH']+"/cloudbook"
		if not os.path.exists(fs):
			os.makedirs(fs)
	else:
		fs = "/etc/cloudbook"
		if not os.path.exists(fs):
			os.makedirs(fs)
	config_dict=loader.load_dictionary(fs+"/config/config_agent"+my_agent_ID+".json")
	config_dict["DISTRIBUTED_FS"]=path
	loader.write_dictionary(config_dict, fs+"/config/config_agent"+my_agent_ID+".json")


#This function sets the filesystem path of a new agent. It is used by the agent when creating a new one.
#It receives the filesystem path to use and edits the auto-generated configuration file that will be for that agent.
def setFSPath(path):
	#load config file
	if(platform.system()=="Windows"):
		fs= os.environ['HOMEDRIVE'] + os.environ['HOMEPATH']+"/cloudbook"
		if not os.path.exists(fs):
			os.makedirs(fs)
	else:
		fs = "/etc/cloudbook"
		if not os.path.exists(fs):
			os.makedirs(fs)
	#load config file
	config_dict=loader.load_dictionary(fs+"/config/config_agent.json")
	config_dict["DISTRIBUTED_FS"]=path
	loader.write_dictionary(config_dict, fs+"/config/config_agent.json")


#Creates an agent ID in case it hasn't been created before, and writes it in configuration file
def createAgentID():
	#load config file
	if(platform.system()=="Windows"):
		fs= os.environ['HOMEDRIVE'] + os.environ['HOMEPATH']+"/cloudbook"
		if not os.path.exists(fs):
			os.makedirs(fs)
	else:
		fs = "/etc/cloudbook"
		if not os.path.exists(fs):
			os.makedirs(fs)
	#load config file
	config_dict=loader.load_dictionary(fs+"/config/config_agent.json")
	if(os.path.isfile(fs+"/distributed/agents_grant.json")):
    	#Random agent_id if it doesn't exist
		my_agent_ID= ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
	else:
		my_agent_ID="agent_0"
	if config_dict["AGENT_ID"]=="0":
		config_dict["AGENT_ID"]=my_agent_ID
	else:
		my_agent_ID=config_dict["AGENT_ID"]
	my_circle_ID=config_dict["CIRCLE_ID"]
	loader.write_dictionary(config_dict, fs+"/config/config_agent.json")
	return (my_agent_ID, my_circle_ID)


#Edit Circle_ID --> TODO: complete when the circle manager is done
def editCircleID(newCircleID, my_agent_ID):
	#load config file
	if(platform.system()=="Windows"):
		fs= os.environ['HOMEDRIVE'] + os.environ['HOMEPATH']+"/cloudbook"
		if not os.path.exists(fs):
			os.makedirs(fs)
	else:
		fs = "/etc/cloudbook"
		if not os.path.exists(fs):
			os.makedirs(fs)
	#load config file
	config_dict=loader.load_dictionary(fs+"/config/config_agent"+my_agent_ID+".json")
	config_dict["CIRCLE_ID"]=newCircleID
	loader.write_dictionary(config_dict, fs+"/config/config_agent"+my_agent_ID+".json")



#This function edits the grant of a certain agent. It is used by the agent.
#It receives the new agent grant level and the ID of the agent to edit and rewrites the configuration file.
def editGrantLevel(level, my_agent_ID):
	#load config file
	if(platform.system()=="Windows"):
		fs= os.environ['HOMEDRIVE'] + os.environ['HOMEPATH']+"/cloudbook"
		if not os.path.exists(fs):
			os.makedirs(fs)
	else:
		fs = "/etc/cloudbook"
		if not os.path.exists(fs):
			os.makedirs(fs)
	config_dict=loader.load_dictionary(fs+"/config/config_agent"+my_agent_ID+".json")
	path=config_dict["DISTRIBUTED_FS"]
	if level in ("LOW", "MEDIUM", "HIGH"):
		config_dict["GRANT_LEVEL"]=level
		loader.write_dictionary(config_dict, fs+"/config/config_agent"+my_agent_ID+".json")
		fr = open(path+"/agents_grant.json", 'r')
		directory = json.load(fr)
		directory[my_agent_ID]=level
		fo = open(path+"/agents_grant.json", 'w')
		directory= json.dumps(directory)
		fo.write(directory)
		fo.close()
		return


#This function sets the grant of a new agent. It is used by the agent when creating a new one.
#It receives the grant level of the agent and edits the auto-generated configuration file that will be for that agent.
def setGrantLevel(level, my_agent_ID):
	if(platform.system()=="Windows"):
		fs= os.environ['HOMEDRIVE'] + os.environ['HOMEPATH']+"/cloudbook"
		if not os.path.exists(fs):
			os.makedirs(fs)
	else:
		fs = "/etc/cloudbook"
		if not os.path.exists(fs):
			os.makedirs(fs)
	#load config file
	config_dict=loader.load_dictionary(fs+"/config/config_agent.json")
	path=config_dict["DISTRIBUTED_FS"]
	if level in ("LOW", "MEDIUM", "HIGH"):
		config_dict["GRANT_LEVEL"]=level
		#Config has been set, now, lets write it in agents_grant.json
		#Checking if file is empty, if so, write the IP directly.
		while not os.path.exists(fs+"/distributed/agents_grant.json"):
			fo = open(path+"/agents_grant.json", 'w')
			fo.close()
		if os.stat(path+"/agents_grant.json").st_size==0:
			fo = open(path+"/agents_grant.json", 'w')
			data={}
			data[my_agent_ID]={}
			data[my_agent_ID]={}
			data[my_agent_ID]=level
			json_data=json.dumps(data)
			fo.write(json_data)	
			fo.close()
		# File not empty, so we open it to check if the agent has been already written on it.
		else:
			fr = open(path+"/agents_grant.json", 'r')
			directory = json.load(fr)
			if my_agent_ID in directory:
				directory[my_agent_ID]=level
				fo = open(path+"/agents_grant.json", 'w')
				directory= json.dumps(directory)
				fo.write(directory)
				fo.close()
				return
		# if agent not already written, we append it.
			fr = open(path+"/agents_grant.json", 'r')
			directory = json.load(fr)
			directory[my_agent_ID]={}
			directory[my_agent_ID]=level
			fo = open(path+"/agents_grant.json", 'w')
			directory= json.dumps(directory)
			fo.write(directory)
			fo.close()
		return

#This function auto-generates the configuration file when creating a new agent. 
#It uses default configuration that will be changed if needed.
def generate_default_config():
	if(platform.system()=="Windows"):
		fs= os.environ['HOMEDRIVE'] + os.environ['HOMEPATH']+"/cloudbook"
		if not os.path.exists(fs):
			os.makedirs(fs)
	else:
		fs = "/etc/cloudbook"
		if not os.path.exists(fs):
			os.makedirs(fs)

	default={"AGENT_ID": "0", "DISTRIBUTED_FS": fs+"/distributed", "CIRCLE_ID": "LOCAL", "GRANT_LEVEL": "MEDIUM"}
	if os.path.isfile(fs+"/config/config_agent.json"):
		open(fs+"/config_agent.json", 'w').close()
	else:
		fo = open(fs+"/config/config_agent.json", 'w')
		default=json.dumps(default)
		fo.write(default)
		fo.close()
		return
