import json
import subprocess
import os

def load_cloudbook(my_agent_ID):
	with open('./du_files/cloudbook_agents.json', 'r') as file:
		agents = json.load(file)

	
	my_agent_dict={}
	for key in agents:
		if (key==my_agent_ID):
			print "-->",agents.get(key)
			my_agent_dict=agents.get(key)

	du_list=[]
	for key, value in my_agent_dict.items():
		du_list=value
		
	print du_list
	print "du_list to load: "+str(du_list)
	return du_list
	#return ["du_0"]

def import_dus(du_list):
	#enter in distributed FS
	#subprocess.call('cd ud_files', shell=True)
	#subprocess.call('dir', shell=True)
	#os.chdir('./du_files')
	#subprocess.call('dir', shell=True)
	for i in du_list:
		#exec("from du_files import "+i)
		#exec("import "+i)
		pass