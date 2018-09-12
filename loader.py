import json
import subprocess
import os

def load_cloudbook_agent_dus(my_agent_ID, cloudbook_dict_agents):
	# this function loads the list of deployable units belonging to certain agent ID
	#with open('./du_files/cloudbook_agents.json', 'r') as file:
	#	cloudbook_dict_agents = json.load(file)
	
	my_agent_dict={}
	for key in cloudbook_dict_agents:
		if (key==my_agent_ID):
			print "-->",cloudbook_dict_agents.get(key)
			my_agent_dict=cloudbook_dict_agents.get(key)

	du_list=[]
	for key, value in my_agent_dict.items():
		du_list=value

	print du_list
	print "du_list to load: "+str(du_list)
	return du_list
	#return ["du_0"]

def load_cloudbook_dus():
	# this function loads the list of dus and their machines
	with open('./du_files/cloudbook_dus.json', 'r') as file:
		dus = json.load(file)

	print "--- dus location loaded ---"
	print dus
	return dus

def load_cloudbook_agents():
	# this function loads the list of dus and their machines
	with open('./du_files/cloudbook_agents.json', 'r') as file:
		cloudbook_dict_agents = json.load(file)

	return cloudbook_dict_agents
