import os, random, string, json, platform
import loader


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
    #Random agent_id if it doesn't exist
	my_agent_ID= ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
	if config_dict["AGENT_ID"]=="0":
		config_dict["AGENT_ID"]=my_agent_ID
	else:
		my_agent_ID=config_dict["AGENT_ID"]
	my_circle_ID=config_dict["CIRCLE_ID"]
	loader.write_dictionary(config_dict, fs+"/config/config_agent.json")
	return (my_agent_ID, my_circle_ID)


#Edit Circle_ID --> to be completed when the circle manager is done
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



#Edit grant level of this agent
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


#Sets grant level of this agent
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
		while not os.path.exists(fs+"/distributed/agent_grant.json"):
			fo = open(path+"/agent_grant.json", 'w')
			fo.close()
		if os.stat(path+"/agent_grant.json").st_size==0:
			fo = open(path+"/agent_grant.json", 'w')
			data={}
			data[my_agent_ID]={}
			data[my_agent_ID]={}
			data[my_agent_ID]=level
			json_data=json.dumps(data)
			fo.write(json_data)	
			fo.close()
		# File not empty, so we open it to check if the agent has been already written on it.
		else:
			fr = open(path+"/agent_grant.json", 'r')
			directory = json.load(fr)
			if my_agent_ID in directory:
				directory[my_agent_ID]=level
				fo = open(path+"/agent_grant.json", 'w')
				directory= json.dumps(directory)
				fo.write(directory)
				fo.close()
				return
		# if agent not already written, we append it.
			fr = open(path+"/agent_grant.json", 'r')
			directory = json.load(fr)
			directory[my_agent_ID]={}
			directory[my_agent_ID]=level
			fo = open(path+"/agent_grant.json", 'w')
			directory= json.dumps(directory)
			fo.write(directory)
			fo.close()
		return

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
