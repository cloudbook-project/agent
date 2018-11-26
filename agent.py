#PENDING:
# remote invoke, support new du_list, change cloudbook_agents by cloudbook_directory, support invocation labels

from flask import Flask
from flask import request
from flask import jsonify
import json
from flask import abort, redirect, url_for
import loader, publisher_frontend, upnp, local_publisher, configure_agent
import os, sys, time, threading, logging
import urllib.request # this import requires pip3 install urllib
from pynat import get_ip_info #requires pip3 install pynat

# agent_ID of this agent. this is a global var
my_agent_ID="None"

# circle_ID of this agent. this is a global var
my_circle_ID = "None"

# dictionary of dus and location
cloudbook_dict_dus={}

#dictionary of agents 
cloudbook_dict_agents={}

# list of Deployable units loaded by this agent
du_list=[]

# dictionary of config
config_dict={}

#Global variable to define working mode
LOCAL_MODE = False


application = Flask(__name__)

@application.route("/", methods=['GET', 'PUT', 'POST'])
def hello():
	print ("hello world")
	return  "Hello"

@application.route("/invoke", methods=['GET','POST'])
def invoke(invoked_function="none"):
	#Lo que llega es un json
	#miramos el campo nombre de funcion, nombre del modulo de funcion, si existe en la du_list, la invocamos
	#y si no, hay que invocar al agente que la contenga, consultando el cloudbook
	#llamando al modulo invoker.py
	
	# example of invocation
	# http://localhost:3000/invoke?invoked_function=compute(56,77,5)
	
	if invoked_function=="none":
		invoked_function=request.args.get('invoked_function')
		print ("external invocation")
	else :
		print ("internal invocation")

	print ("invoked_function = "+invoked_function)
	# check if invoked function belongs to this agent, otherwise will re-invoke to the right agent
	j=invoked_function.find(".")
	invoked_du= invoked_function[0:j]
	print ("invoked_du ", invoked_du)

	if invoked_du in du_list:
		a= eval(invoked_function)
		#supongamos que procesamos el post y llega esto
		# invoked_function="main()"
		#os.chdir('./du_files')
		#exec("import du_0")
		#return eval("du_0."+invoked_function)
		#return eval("du_0."+"main("+"cosa"+")")
		#a= eval("du_0."+"main()")
		#if invoked_function belongs to this agent, then it can be evaluated
		#a= eval(invoked_function)
	else:
		print ("this function does not belong to this agent")
		a = "none" #remote_invoke(invoked_du, invoked_function)

	#print "function executed ok"
	#print a
	print ("\n")
	#stdout.flush()
	return a

#def cosa(k):
#	print k
#	return "cloudbook"
################################################ To be updated #######################################
#def remote_invoke(invoked_du, invoked_function):
def remote_invoke(invoked_function):
	print ("ENTER in remote_invoke...")
	# get the remote du 
	j=invoked_function.find(".")
	remote_du= invoked_function[0:j]
	print ("remote du = ", remote_du)

	if remote_du in du_list:
		#this is not remote
		print ("local invocation: ",invoked_function[j+1:])
		res=eval(invoked_function[j+1:])
		return res

    # get the possible agents to invoke
	list_agents=cloudbook_dict_agents.get(remote_du)

    # get the machines to invoke
	remote_agent= list_agents[0] # several agents can have this remote DU. In order to test, get the first
	print ("remote agent", remote_agent)

	print ("cloudbook_dict_agents = ", cloudbook_dict_agents)

	machine_dict=cloudbook_dict_agents.get(remote_agent)

	print ("machine_dict ", machine_dict)

	host =machine_dict.keys()[0]
	print ("host to invoke is ", host)
	"""
	#remote port
	j = remote_du.rfind('_')+1
	# num_du is the initial DU and will be used as offset for listen port
	num_remote_du = remote_du[j:]

	#host="127.0.0.1:3001"
	remote_port =3000+ int(num_remote_du)
	host = host+":"+str (remote_port)
	"""

	url='http://'+host+"/invoke?invoked_function="+invoked_function
	print (url)
	r = urllib.request.urlopen(url)
	print ("request launched", url)
	print (r.text)
	print ("\n")
	#stdout.flush()
	return r.text


if __name__ == "__main__":

	#load config file
	config_dict=loader.load_dictionary("./config_agent.json")

	#extract args and get the agent ID
	#py agent.py GRANT_LEVEL FS_PATH CIRCLE_NAME
	print(sys.argv)
	if(len(sys.argv) > 1):
	
		LOCAL_MODE = True
		config_dict["CIRCLE_ID"]=sys.argv[3]
		loader.write_dictionary(config_dict, "./config_agent.json")
		config_dict=loader.load_dictionary("./config_agent.json")
		(my_agent_ID, my_circle_ID) = configure_agent.createAgentID()
		configure_agent.setFSPath(sys.argv[2])
		configure_agent.setGrantLevel(sys.argv[1], my_agent_ID)
	else:
		###THINGS FOR SERVICE_MODE#####
		LOCAL_MODE = False
		(my_agent_ID, my_circle_ID) = configure_agent.createAgentID()
		#configure_agent.setGrantLevel("LO QUE SEA", my_agent_ID)


	print ("my_agent_ID="+my_agent_ID)

	print ("loading deployable units for agent "+my_agent_ID+"...")
	#cloudbook_dict_agents = loader.load_cloudbook_agents()

	#It will only contain info about agent_id : du_assigned (not IP)
	#must be the output file from DEPLOYER
	#HERE WE MUST WAIT UNTIL THIS FILE EXISTS OR UPDATES: HOW TO DO THIS?
	while(os.stat("./FS/cloudbook_agents.json").st_size==0):
		continue
	#Check file format :D
	cloudbook_dict_agents = loader.load_cloudbook('./FS/cloudbook_agents.json')
	
	#Loads the DUs that belong to this agent.
	du_list = loader.load_cloudbook_agent_dus(my_agent_ID, cloudbook_dict_agents)
	print(du_list)
    
	#du_list=["du_0"] # fake
	
	j = du_list[0].rfind('_')+1
	# num_du is the initial DU and will be used as offset for listen port
	num_du = du_list[0][j:]
	if (not LOCAL_MODE):
		topology, external_ip, ext_port = get_ip_info()
		host = external_ip
	else:
		host = local_publisher.get_local_ip()
	print ("this host is ", host)

	#Local port to be opened
	local_port=3000+int(num_du)
	print (host, local_port)

	#Pending: check if previous port is closed.
	if (not LOCAL_MODE):
		while(upnp.openPort(local_port)):
			continue

	
	#exec("import du_0")
	#du_0.invoker=cosa
	# du_files is the distributed directory containing all DU files
	#for du in du_list:
	#	exec ("from du_files import "+du)
	#	#exec(du+".invoker=invoke")
	#	exec(du+".invoker=remote_invoke")
		
		#exec('du_0.invoker("du_0.hello()")')		
	#du_0.main()

	log = logging.getLogger('werkzeug')
	log.setLevel(logging.ERROR)
	if (not LOCAL_MODE):
		threading.Thread(target=publisher_frontend.announceAgent, args=(my_circle_ID, my_agent_ID)).start()
	else:
		threading.Thread(target=local_publisher.announceAgent, args=(my_circle_ID, my_agent_ID, local_port)).start()
	application.run(debug=False, host="0.0.0.0",port=local_port,threaded=True)
