from flask import Flask
from flask import request
from flask import jsonify
import json
from flask import abort, redirect, url_for
import loader, upnp, publisher_frontend, local_publisher, configure_agent
import os, sys, time, threading, logging, platform
from multiprocessing import Process
from pynat import get_ip_info #requires pip3 install pynat
import urllib # this import requires pip3 install urllib
import os
import queue
import socket


#####   GLOBAL VARIABLES   #####
# Identifier of this agent
my_agent_ID = "None"

# Identifier of the circle that this agent belongs to
my_circle_ID = "None"

# Dictionary of dus and location
cloudbook_dict_dus = {}

# Dictionary of agents 
cloudbook_dict_agents = {}

# List of deployable units loaded by this agent
du_list = []

# Dictionary of agent configuration
agent_config_dict = {}

# Dictionary of circle configuration
circle_config_dict = {}

# Global variable to define working mode
LOCAL_MODE = False

# All dus that contain the program
all_dus = []
# Index in order to make the round robin assignation of all_dus
parallel_du_index = 0

# For stats count
stats_dict = {}

# FIFO queue that passes stats to the stats_creator_thread
stats_queue = queue.Queue(maxsize=0) # infinite size

# Files and folders
if(platform.system()=="Windows"):
	path = os.environ['HOMEDRIVE'] + os.environ['HOMEPATH']+os.sep+"cloudbook"
else:
	path = "/etc/cloudbook/"



#####   APPLICATION TO SEND AND RECEIVE FUNCTION REQUESTS   #####

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
	global stats_dict
	global path

	print("=====AGENT: /INVOKE=====")
	print(threading.get_ident())
	print("===================Estadisticas por ahora", stats_dict, "para el fichero: stats_"+my_agent_ID+".txt")
	invoked_data = ""
	print("REQUEST.form: ", request.form)
	invoked_function = request.args.get('invoked_function')
	try:
		invoker_function = request.args.get('invoker_function')
	except:
		invoker_function = None
	for i in request.form:
		invoked_data = i
	print("INVOKED DATA: ", invoked_data)
	print ("invoked_function = "+invoked_function)

	# Separate du and function
	j = invoked_function.find(".")
	invoked_du = invoked_function[0:j]
	print("Yo soy", my_agent_ID)
	print ("invoked_du ", invoked_du)
	print("TEST: DU_LIST",du_list)
	
	# Queue data stats
	stats_data = {}
	stats_data['invoked'] = invoked_function[j+1:] #only fun name without du
	stats_data['invoker'] = invoker_function
	stats_queue.put(stats_data)

	# If the function belongs to the agent
	if invoked_du in du_list:
		resul = eval(invoked_function+"("+invoked_data+")")
	else:
		print ("this function does not belong to this agent")
		resul = "none" #remote_invoke(invoked_du, invoked_function) Is this neccesary?
	print ("\n")
	return resul

def outgoing_invoke(invoked_du, invoked_function, invoked_data, invoker_function = None, configuration = None):
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
		parallel_du_index = (parallel_du_index+1) % len(all_dus)
		invoked_du[0] = remote_du
		print("Llamada a funcion parallel, la du afortunada sera: ", remote_du)

	if remote_du == 'du_5000':
		#metemos las dus en una lista y hacemos un contador saturado sobre los indices de esa lista     
		remote_du = all_dus[parallel_du_index]
		parallel_du_index = (parallel_du_index+1) % len(all_dus)
		invoked_du[0] = remote_du
		print("Llamada a funcion recursiva, la du afortunada sera: ", remote_du)

	if remote_du in du_list:
		print ("local invocation: ",invoked_function)
		print(invoked_du, invoked_function, invoked_data)
		#res=eval(invoked_function)
		print("Hago eval de: "+ invoked_du[0]+"."+invoked_function+"("+invoked_data+")")
		res = eval(invoked_du[0]+"."+invoked_function+"("+invoked_data+")")
		print("Responde: ", res)

		# Queue data stats
		stats_data = {}
		stats_data['invoked'] = invoked_function
		stats_data['invoker'] = invoker_function
		stats_queue.put(stats_data)

		try:
			return eval(res)
		except:
			return res

	# Get the possible agents to invoke
	global my_agent_ID
	list_agents = cloudbook_dict_agents.get(remote_du)
	list_agents = list(list_agents) 

	# Get the machines to invoke
	remote_agent = list_agents[0] # several agents can have this remote DU. In order to test, get the first
	print ("remote agent", remote_agent)

	#host = remote ip+port
	
	host = local_publisher.getAgentIP(my_agent_ID, remote_agent)
	host = host["IP"]
	print("TEST: HOST: ",host)
	# Cache IPs --> Done by default in both local publisher and publisher frontend.
	
	# Choose du from de list of dus passed
	chosen_du = remote_du
	if invoker_function == None:
		url = 'http://'+host+"/invoke?invoked_function="+chosen_du+"."+invoked_function
	else:
		url = 'http://'+host+"/invoke?invoked_function="+chosen_du+"."+invoked_function+"&invoker_function="+invoker_function
	print (url)

	send_data = invoked_data.encode()
	print("Sending data: ",send_data)
	request_object = urllib.request.Request(url, send_data)
	print ("Request launched: ", url)
	r = urllib.request.urlopen(request_object)
	print ("Response received")

	try: 		# For functions that return some json
		data = r.read().decode()
		aux = eval(data)
	except: 	# For other data types
		data = r.read()
		aux = data
	return aux



#####   AGENT FUNCTIONS   #####

# This function is used by the GUI. Generates a new agent given the grant level and the FS (if provided)
# Checks the OS to adapt the path of the folders.
# Generates a default configuration file that is edited and adapted afterwards.
# NEED TO TEST IN LINUX. I think both editions of "path" variable can be deleted and you can write "global path" at the beginning of the function to edit the variable, (check: https://www.geeksforgeeks.org/global-local-variables-python/)
def create_LOCAL_agent(grant, fs=False):
	if(platform.system()=="Windows"):
		path = os.environ['HOMEDRIVE'] + os.environ['HOMEPATH']+"/cloudbook"
		if not os.path.exists(path):
			os.makedirs(path)
	else:
		fs = "/etc/cloudbook"
		path = "/etc/cloudbook"
		if not os.path.exists(path):
			os.makedirs(path)
	if not fs:
		fs = path+"/distributed"
	configure_agent.generate_default_config()
	agent_config_dict = loader.load_dictionary(path+"/config/config_.json")
	agent_config_dict["CIRCLE_ID"]="LOCAL"
	loader.write_dictionary(agent_config_dict, path+"/config/config_.json")
	(my_agent_ID, my_circle_ID) = configure_agent.createAgentID()
	print("Agent_ID: ",my_agent_ID)
	configure_agent.setFSPath(fs)
	print("FSPath hecho")
	configure_agent.setGrantLevel(grant, my_agent_ID)
	print("Vamos a renombrar")
	os.rename(path+"/config/config_.json", path+"/config/config_"+my_agent_ID+".json")


# This function is used by the GUI. Modifies the the grant level and/or the FS of the current agent according to the parameters given.
def edit_agent(agent_id, grant='', fs=''):
	if(grant!=''):
		configure_agent.editGrantLevel(grant, agent_id)
	if(fs!=''):
		configure_agent.editFSPath(fs, agent_id)
	return


# This function launches the flask server in the port given as parameter.
def flaskThreaded(port):
	port = int(port)
	print("Launched in port:", port)
	application.run(debug=False, host="0.0.0.0",port=port,threaded=True)
	print("00000000000000000000000000000000000000000000000000000000000000000000000000")


# Target function of the thread to create the stats. Implements the stats creation as a model producer/consumer with a queue of data
def create_stats(t1):
	print("Stats creator thread started")
	time_start = time.monotonic()
	stats_dictionary = {}

	while True:
		current_time = time.monotonic()
		while not stats_queue.empty():
			item = stats_queue.get()
			print("New stat: ", item)

			# Add data to dictionary
			try:
				invoker = item['invoker']
				invoked = item['invoked']
			except:
				print("There was a problem with the stat item obtained from the queue. Key invoker/invoked not present")

			try:
				if invoker != None:
					stats_dictionary[invoked][invoker] += 1 	# Add 1 to the existing dictionary entry
			except:
				if invoker != None:
					try: 
						stats_dictionary[invoked][invoker] = 1  # Key 'invoker' not in the 'invoked' dictionary --> create and set to 1
					except:
						stats_dictionary[invoked] = {} 			# Key 'invoked' not in the stats dictionary --> create it (empty)
						stats_dictionary[invoked][invoker] = 1 	# Create key 'invoker' in the 'invoked' dictionary and set it 1

			stats_queue.task_done()

		# In case that it is time to create the stats file, add t1 to time_start and write the dictionary in the stats_agent_XX.json
		if current_time-time_start >= t1:
			time_start += t1
			stats_file = "stats_"+my_agent_ID+".json"
			f_stats = open(path+os.sep+"distributed"+os.sep+"stats"+os.sep+stats_file,"w")
			f_stats.write(json.dumps(stats_dictionary))
			f_stats.close()
			stats_dictionary = {}

		# Wait 1 second to look for more data in the queue
		time.sleep(1)


# This function checks if the port passed as parameter is available or in use, trying to bind that port to a socket. Then, the socket is
# closed and the result (true/false) is returned.
def check_port_available(port):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	available = False
	try:
		sock.bind(("0.0.0.0", port))
		print("Port " + str(port) + " is available.")
		available = True
	except:
		print("Port " + str(port) + " is in use.")
	sock.close()
	return available



#####   AGENT MAIN   #####
if __name__ == "__main__":
	print("Starting agent...")

	if(platform.system()=="Windows"):
		fs = os.environ['HOMEDRIVE'] + os.environ['HOMEPATH']+os.sep+"cloudbook"
	else:
		fs = "/etc/cloudbook"

	# Load agent config file
	agent_id = sys.argv[1]
	agent_config_dict = loader.load_dictionary(fs+"/config/config_"+agent_id+".json")

	my_agent_ID = agent_config_dict["AGENT_ID"]
	my_circle_ID = agent_config_dict["CIRCLE_ID"]
	fs_path = agent_config_dict["DISTRIBUTED_FS"]
	my_grant = agent_config_dict["GRANT_LEVEL"]

	# Load circle config file
	circle_config_dict = loader.load_dictionary(fs+"/config/config.json")

	agent_stats_interval = circle_config_dict['circle_info']['AGENT_STATS_INTERVAL']
	agent_interval = circle_config_dict['circle_info']['AGENT_INTERVAL']
	lan_mode = circle_config_dict['circle_info']['LAN']

	print ("my_agent_ID="+my_agent_ID)

	print ("loading deployable units for agent "+my_agent_ID+"...")
	#cloudbook_dict_agents = loader.load_cloudbook_agents()

	# It will only contain info about agent_id : du_assigned (not IP)
	# Output file from DEPLOYER
	# It is necessary to wait until cloudbook.json exists
	while not os.path.exists(fs_path+'/cloudbook.json'):
		time.sleep(0.1)

	while(os.stat(fs_path+'/cloudbook.json').st_size==0):
		continue
	# Check file format
	cloudbook_dict_agents = loader.load_cloudbook(fs_path+'/cloudbook.json')
	
	# Load the DUs that belong to this agent.
	du_list = loader.load_cloudbook_agent_dus(my_agent_ID, cloudbook_dict_agents)
	print("My du_list: ", du_list)

	j = du_list[0].rfind('_')+1
	# num_du is the initial DU and will be used as offset for listen port
	num_du = du_list[0][j:]

	host = local_publisher.get_local_ip()
	print ("This host is ", host)

	# Check the first port available from 5000 (included) onwards
	local_port = 5000
	while not check_port_available(local_port):
		local_port += 1
	print("For the host " + host + ", the first port available from 5000 onwards is: ", local_port)

	# Get all dus
	for i in cloudbook_dict_agents:
		all_dus.append(i)

	sys.path.append(fs_path)
	'''for du in du_list:
		exec ("from du_files import "+du)
		exec(du+".invoker=outgoing_invoke")'''

	for du in du_list:
		print(du)
		while not os.path.exists(fs_path+"/du_files/"+du+".py"):
			time.sleep(0.1)
		##OJO CON ESTO QUE HAY QUE PROBARLO BIEN BIEN
		
		ruta = fs_path.replace(os.sep, "/")
		ruta = ruta + "/du_files"
		exec('sys.path.append('+"'"+ruta+"'"+')')
		exec ("from du_files import "+du)
		exec(du+".invoker=outgoing_invoke")# read file
		print(du+" charged")

	# Set up the logger
	log = logging.getLogger('werkzeug')
	log.setLevel(logging.ERROR)

	# Launch the stats creator thread
	threading.Thread(target=create_stats, args=(agent_stats_interval,)).start()

	# Laucnch the IP publisher thread
	threading.Thread(target=local_publisher.announceAgent, args=(my_circle_ID, my_agent_ID, local_port)).start()
	
	# Launch invoke listener thread
	#Process(target=flaskThreaded, args=(local_port,)).start()
	threading.Thread(target=flaskThreaded, args=[local_port]).start()
	#flaskThreaded(local_port)

	print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")