from flask import Flask
from flask import request
from flask import jsonify
import json
from flask import abort, redirect, url_for
import loader, publisher_frontend, upnp, local_publisher, configure_agent
import os, sys, time, threading, logging
from multiprocessing import Process
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
	global du_list
	global my_agent_ID

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
	print("Yo soy", my_agent_ID)
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
	global parallel_du_index
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
		invoked_du[0] = remote_du
		print("Llamada a funcion parallel, la du afortunada sera: ", remote_du)

	if remote_du in du_list:
		print ("local invocation: ",invoked_function)
		print(invoked_du, invoked_function, invoked_data)
		#res=eval(invoked_function)
		print("Hago eval de: "+ invoked_du[0]+"."+invoked_function+"("+invoked_data+")")
		res = eval(invoked_du[0]+"."+invoked_function+"("+invoked_data+")")
		print("Responde: "+ res)
		return eval(res)

    # get the possible agents to invoke
	global my_agent_ID
	list_agents=cloudbook_dict_agents.get(remote_du)
	list_agents = list(list_agents)	

    # get the machines to invoke
	remote_agent= list_agents[0] # several agents can have this remote DU. In order to test, get the first
	print ("remote agent", remote_agent)

	#host = remote ip+port
	
	host = local_publisher.getAgentIP(my_agent_ID, remote_agent)
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

#RUNS THE AGENT -> for the interface
def run_LOCAL_agent(agent_id):
	#load config file
	config_dict=loader.load_dictionary("./config_agent"+agent_id+".json")
	global my_agent_ID
	global my_circle_ID

	my_agent_ID=config_dict["AGENT_ID"]
	my_circle_ID=config_dict["CIRCLE_ID"]
	complete_path=config_dict["DISTRIBUTED_FS"]

	print ("my_agent_ID="+my_agent_ID)

	print ("loading deployable units for agent "+my_agent_ID+"...")
	#cloudbook_dict_agents = loader.load_cloudbook_agents()

	#It will only contain info about agent_id : du_assigned (not IP)
	#must be the output file from DEPLOYER
	#HERE WE MUST WAIT UNTIL THIS FILE EXISTS OR UPDATES: HOW TO DO THIS?
	while(os.stat(complete_path+'/cloudbook_agents.json').st_size==0):
		continue
	#Check file format :D
	global cloudbook_dict_agents
	cloudbook_dict_agents = loader.load_cloudbook(complete_path+'/cloudbook_agents.json')
	
	#Loads the DUs that belong to this agent.
	global du_list
	du_list = loader.load_cloudbook_agent_dus(my_agent_ID, cloudbook_dict_agents)
	print("MI DU LIST", du_list)
    
	#du_list=["du_0"] # fake
	
	j = du_list[0].rfind('_')+1
	# num_du is the initial DU and will be used as offset for listen port
	num_du = du_list[0][j:]

	host = local_publisher.get_local_ip()
	print ("this host is ", host)

	#Local port to be opened
	local_port=3000+int(num_du)
	print (host, local_port)

	#get all dus
	global all_dus
	for i in cloudbook_dict_agents:
		all_dus.append(i)

	for du in du_list:
		exec ("from FS/du_files import "+du)
		exec(du+".invoker=outgoing_invoke")

	log = logging.getLogger('werkzeug')
	log.setLevel(logging.ERROR)
	threading.Thread(target=local_publisher.announceAgent, args=(my_circle_ID, my_agent_ID, local_port)).start()
	#Process(target=flaskThreaded, args=(local_port,)).start()
	threading.Thread(target=flaskThreaded, args=[local_port]).start()
	#flaskThreaded(local_port)
	print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
	#prueba_interfaz.master.destroy()

####PREGUNTAR######
# CUANDO SE CREAN AGENTES SE COPIAN TODAS LAS CARPETAS O SOLO SE EDITAN LAS DEL FS Y EL CONFIG, TODAS EN EL MISMO SITIO??????
def create_LOCAL_agent(grant, fs):
	##generate default dict to be edited?????
	configure_agent.generate_default_config()
	config_dict=loader.load_dictionary("./config_agent.json")
	config_dict["CIRCLE_ID"]="LOCAL"
	loader.write_dictionary(config_dict, "./config_agent.json") #?????????????????
	(my_agent_ID, my_circle_ID) = configure_agent.createAgentID()
	configure_agent.setFSPath(fs)
	configure_agent.setGrantLevel(grant, my_agent_ID)
	os.rename("./config_agent.json", "./config_agent"+my_agent_ID+".json")

def edit_agent(agent_id, grant='', fs=''):
	
	if(grant!=''):
		configure_agent.editGrantLevel(grant, agent_id)
	if(fs!=''):
		configure_agent.editFSPath(fs, agent_id)
	return

#Mmmmmmm will it work? Nope, we just want to kill the associated agent
def STOP():
	sys.exit(0)

def flaskThreaded(port):
	port = int(port)
	print("Voy a lanzar en", port)
	application.run(debug=False, host="0.0.0.0",port=port,threaded=True)
	print("00000000000000000000000000000000000000000000000000000000000000000000000000")

if __name__ == "__main__":
	print("Al lio")
	#load config file
	agent_id = sys.argv[1]
	config_dict=loader.load_dictionary("./config_agent"+agent_id+".json")
	#global my_agent_ID
	#global my_circle_ID

	my_agent_ID=config_dict["AGENT_ID"]
	my_circle_ID=config_dict["CIRCLE_ID"]
	complete_path=config_dict["DISTRIBUTED_FS"]
	my_grant = config_dict["GRANT_LEVEL"]
	configure_agent.setGrantLevel(my_grant, my_agent_ID)

	print ("my_agent_ID="+my_agent_ID)

	print ("loading deployable units for agent "+my_agent_ID+"...")
	#cloudbook_dict_agents = loader.load_cloudbook_agents()

	#It will only contain info about agent_id : du_assigned (not IP)
	#must be the output file from DEPLOYER
	#HERE WE MUST WAIT UNTIL THIS FILE EXISTS OR UPDATES: HOW TO DO THIS?
	while not os.path.exists(complete_path+'/cloudbook_agents.json'):
			time.sleep(1)

	while(os.stat(complete_path+'/cloudbook_agents.json').st_size==0):
		continue
	#Check file format :D
	#global cloudbook_dict_agents
	cloudbook_dict_agents = loader.load_cloudbook(complete_path+'/cloudbook_agents.json')
	
	#Loads the DUs that belong to this agent.
	#global du_list
	du_list = loader.load_cloudbook_agent_dus(my_agent_ID, cloudbook_dict_agents)
	print("MI DU LIST", du_list)
    
	#du_list=["du_0"] # fake
	
	j = du_list[0].rfind('_')+1
	# num_du is the initial DU and will be used as offset for listen port
	num_du = du_list[0][j:]

	host = local_publisher.get_local_ip()
	print ("this host is ", host)

	#Local port to be opened
	local_port=3000+int(num_du)
	print (host, local_port)

	#get all dus
	#global all_dus
	for i in cloudbook_dict_agents:
		all_dus.append(i)

	sys.path.append(complete_path)
	'''for du in du_list:
		exec ("from du_files import "+du)
		exec(du+".invoker=outgoing_invoke")'''

	for du in du_list:
		while not os.path.exists("./FS/du_files/"+du+".py"):
			time.sleep(0.1)

		if os.path.isfile("./FS/du_files/"+du+".py"):
			exec ("from FS.du_files import "+du)
			exec(du+".invoker=outgoing_invoke")# read file
		print(du+" charged")

	log = logging.getLogger('werkzeug')
	log.setLevel(logging.ERROR)
	threading.Thread(target=local_publisher.announceAgent, args=(my_circle_ID, my_agent_ID, local_port)).start()
	#Process(target=flaskThreaded, args=(local_port,)).start()
	threading.Thread(target=flaskThreaded, args=[local_port]).start()
	#flaskThreaded(local_port)
	print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")