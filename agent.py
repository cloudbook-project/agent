from flask import Flask
from flask import request
from flask import jsonify
import json
from flask import abort, redirect, url_for
import loader, publisher_frontend, upnp, local_publisher, configure_agent
import os, sys, time, threading, logging
from pynat import get_ip_info #requires pip3 install pynat
import urllib # this import requires pip3 install urllib

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

#All dus that contain the program
all_dus=[]
#index in order to make the round robin assignation of all_dus
parallel_du_index = 0


application = Flask(__name__)

@application.route("/", methods=['GET', 'PUT', 'POST'])
def hello():
	print ("hello world")
	return  "Hello"

@application.route("/invoke", methods=['GET','POST'])
def invoke(configuration = None):
	'''
	This function receives petitions from other Agents or the run command
	This function is invoked through http like this: http://138.4.7.151:3000/invoke?invoked_function=du_0.main
	The invocation contains:
		-GET: the invoked function
		-POST: the invoked data
	This function:
		Gets the atributes invoked function and data
		Gets the du and the function name
		Evaluate the function if the du belong to the agent
			Check: This always happens.
		Returns the result of the evaluation
	'''
	print("=====AGENT: /INVOKE=====")
	print(threading.get_ident())
	
	invoked_data = ""
	print("REQUEST.form: ", request.form)
	invoked_function=request.args.get('invoked_function')
	for i in request.form:
		invoked_data = i
	print("INVOKED DATA: ", invoked_data)
	print ("invoked_function = "+invoked_function)

	# separate du and function
	j=invoked_function.find(".")
	invoked_du= invoked_function[0:j]
	print ("invoked_du ", invoked_du)
	print("TEST: DU_LIST",du_list)
	#if the function belongs to the agent
	if invoked_du in du_list:
		resul = eval(invoked_function+"("+invoked_data+")")
	else:
		print ("this function does not belong to this agent")
		resul = "none" #remote_invoke(invoked_du, invoked_function) Is this neccesary?
	print ("\n")
	return resul

def outgoing_invoke(invoked_du, invoked_function, invoked_data, configuration = None):
	'''
	This function is the one that calls the functions that do not belong to the agent's dus
	This is because the exec(du+".invoker=remote_invoke") statement in the main process of every agent
		being invoker an object generated in every du+
	The invocation contains its variables in the invocation inside the du (example: invoker(['du_1'],'compute_body',str(i)+','+str(j)))
	This function:
		Gets the du to which the function belongs
			If its in a du that belongs to the agent, it will resolv the function locally. Check: This never happens
		Check the list of agents in order to get the agent to invoke (this could be many)
		Build the call
			Gets the host (TODO: Cache the ip)
			Build the url (in order the invoke function from the other agent understands it: 
				url='http://'+host+"/invoke?invoked_function="+chosen_du+"."+invoked_function)
			Encode data (in the post of the https call)
		Launch the request
		Receive response
			TODO: Test better the decoding of the response, actually makes a try except block diferenciating if the function response a
				JSON object or other type like a string
		The function returns the data received as response (That data is the resul of the invoke function in the other agent)
	'''
	print("=====AGENT: /REMOTE_INVOKE=====")
	print(threading.get_ident())

	remote_du = invoked_du[0] #TODO: Random between remote dus, if invoked fun is idempotent, it can result into multiple invocations
	print ("remote du = ", remote_du)
	###Round Robin: Circular planification
	if remote_du == 'du_10000':
		#metemos las dus en una lista y hacemos un contador saturado sobre los indices de esa lista		
		remote_du = all_dus[parallel_du_index]
		parallel_du_index=(parallel_du_index+1) % len(all_dus)

	if remote_du in du_list:
		print ("local invocation: ",invoked_function)
		res=eval(invoked_function)
		return res

    # get the possible agents to invoke
	list_agents=cloudbook_dict_agents.get(remote_du)
	list_agents = list(list_agents)	

    # get the machines to invoke
	remote_agent= list_agents[0] # several agents can have this remote DU. In order to test, get the first
	print ("remote agent", remote_agent)

	#host = remote ip+port
	
	host = local_publisher.getAgentIP(remote_agent)
	host = host["IP"]
	print("TEST: HOST: ",host)
	#Cachear ips --> Done by default in both local publisher and publisher frontend.
	
	#lets choose the du from de list of dus passed
	chosen_du = remote_du
	url='http://'+host+"/invoke?invoked_function="+chosen_du+"."+invoked_function
	print (url)

	send_data = invoked_data.encode()
	print("mandamos: ",send_data)
	request_object = urllib.request.Request(url, send_data)
	print ("request launched", url)
	r = urllib.request.urlopen(request_object)
	print ("response received")

	try:#Para funciones que devuelven algo en json
		data = r.read().decode()
		aux = eval(data)
	except:#Para otros tipos de datos
		data = r.read()
		aux = data

	return aux

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
		complete_path = sys.argv[2]
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
	while(os.stat(complete_path+'/cloudbook_agents.json').st_size==0):
		continue
	#Check file format :D
	cloudbook_dict_agents = loader.load_cloudbook(complete_path+'/cloudbook_agents.json')
	
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

	#get all dus
	for i in cloudbook_dict_agents:
		all_dus.append(i)

	#Pending: check if previous port is closed.
	if (not LOCAL_MODE):
		while(upnp.openPort(local_port)):
			continue

	# du_files is the distributed directory containing all DU files
	for du in du_list:
		exec ("from du_files import "+du)
		exec(du+".invoker=outgoing_invoke")

	log = logging.getLogger('werkzeug')
	log.setLevel(logging.ERROR)
	if (not LOCAL_MODE):
		threading.Thread(target=publisher_frontend.announceAgent, args=(my_circle_ID, my_agent_ID)).start()
	else:
		threading.Thread(target=local_publisher.announceAgent, args=(my_circle_ID, my_agent_ID, local_port)).start()
	application.run(debug=False, host="0.0.0.0",port=local_port,threaded=True)