#####   IMPORTS   #####
# Internet
from pynat import get_ip_info		# Requires pip3 install pynat
from flask import Flask, request	# Requires pip3 install flask
import urllib						# Requires pip3 install urllib
import socket

# Multi thread/process
import time
import threading, queue
from multiprocessing import Process, Queue

# System, files
import os, sys, platform
import loader				# In project directory
import logging

# Basic
import random, string, builtins



#####   GLOBAL VARIABLES   #####

# Identifier of this agent
my_agent_ID = None

# Identifier of the project that this agent belongs to
my_project_name = None

# Dictionary of agents 
cloudbook_dict_agents = {}

# List of deployable units that this agent has to load
du_list = []

# Dictionary of agent configuration
agent_config_dict = {}

# Dictionary of circle configuration
configjson_dict = {}

# Index in order to make the round robin assignation of invocation requests
round_robin_index = 0

# FIFO queue that passes stats to the stats file creator thread
mp_stats_queue = None

# FIFO queue that passes the changes of grant to the grant file creator thread
grant_queue = queue.Queue(maxsize=0)

# Global variable to store the general path to cloudbook, used to access all files and folders needed
if platform.system()=="Windows":
	cloudbook_path = os.environ['HOMEDRIVE'] + os.environ['HOMEPATH'] + os.sep + "cloudbook"
else:
	cloudbook_path = os.environ['HOME'] + os.sep + "cloudbook"

# Path to the project the agent belongs to
project_path = None

# Path to the distributed filesystem
fs_path = None

# Variable that contains the information from agents_grant.json (last read)
#Format:
# {
# 	"agent_0": {"GRANT": "LOW", "IP": "192.168.1.44", "PORT": 5000},
# 	"agent_G2UQXFV1O2NWTNRQY8GD": {"GRANT": "LOW", "IP": "192.168.1.44", "PORT": 5001},
# 	"agent_IGPAMITGCCPPYMTQ4BQA": {"GRANT": "LOW", "IP": "192.168.1.44", "PORT": 5002},
# 	"agent_OMRZ22CQB157H3POXG3A": {"GRANT": "LOW", "IP": "192.168.1.44", "PORT": 5003}
# }
agents_grant = {}

# Global variable with the list of deployable units that have already been loaded
loaded_du_list = []

# Number of times the cloudbook has changed and DUs have been (re)loaded
cloudbook_version = 0



#####   CONSTANTS   #####
CRIT_ERR_NO_ANSWER = "CLOUDBOOK CRITICAL ERROR: no agent could answer the remote invocation to a function in a critical DU. \
The DU state is lost and program is corrupt. Critical alarm created in the distributed filesystem in order that depployer's \
surveillance monitor knows that an invocation has failed. The Flask process will be stopped and restarted."
ERR_IP_NOT_FOUND = "ERROR: cannot find the ip and port for invoking the desired agent."
ERR_QUEUE_KEY_VALUE = "ERROR: there was a problem item obtained from the queue. Wrong key/value."
ERR_READ_WRITE = "ERROR: reading/writing not allowed or wrong path."
ERR_FLASK_PORT_IN_USE = "ERROR: this agent is using a port that was checked to be free but, due to race conditions, another \
agent did the same and started using it before."
ERR_DUS_NOT_EXIST = "ERROR: could not load the specified DU(s), because file(s) did not exist."
GEN_ERR_LAUNCHING_FLASK = "GENERIC ERROR: something went wrong when launching the flask thread."
GEN_ERR_LOADING_DUS = "GENERIC ERROR: something went wrong when loading DUs."
ERR_DUS_ALREADY_LOADED = "ERROR: a list of DU(s) has already been loaded."
ERR_NO_LAN = "ERROR: the local IP was not found. The device is not connected to internet nor any LAN."
ERR_NO_INTERNET = "ERROR: external IP or port not found. Either the device is not conected to the internet or the STUN server \
did not accept the request."
GEN_ERR_RESTARTING_FLASK = "GENERIC ERROR: something went wrong when restarting the flask process."
GEN_ERR_INIT_CHECK_FLASK = "GENERIC ERROR: something went wrong when initializing of checking that FlaskProcess was up and \
running correctly."
ERR_GET_PROJ_ID_REFUSED = "ERROR: conection refused when FlaskProcess was trying to check the id of the agent running on the \
requested port."
ERR_LOAD_CRIT_DU_CLOUDBOOK_RUNNING = "ERROR: cloudbook is already running and critical dus should not be loaded at this \
point in order to avoid unexpected behaviours due to global variables may have lost their state."



#####   OVERLOAD BUILT-IN FUNCTIONS   #####

# Print function overloaded in order to make it print the id before anything and keep track of the traces of each agent easier.
def print(*args, **kwargs):
	# If the print is just a separation, i.e.:  print()  keep it like that
	if len(args)==1 and len(kwargs)==0 and args[0]=='':
		builtins.print()
		return

	# If the agent ID has been already set
	if my_agent_ID is not None:
		if my_agent_ID == "agent_0": 	# For the agent_0 add dots to make it start at the same letter column in the console
			builtins.print(my_agent_ID + "...................:", *args, **kwargs)
		else:
			builtins.print(my_agent_ID + ":", *args, **kwargs)
	else: 	# For the case in which the ID is None, print it with the normal built-in
		builtins.print(*args, **kwargs)



#####   APPLICATION TO SEND AND RECEIVE FUNCTION REQUESTS   #####

application = Flask(__name__)

@application.route("/", methods=['GET', 'PUT', 'POST'])
def hello():
	print("Hello world")
	return "Hello"

@application.route("/get_project_agent_id", methods=['GET', 'PUT', 'POST'])
def get_project_agent_id():
	print("/get_project_agent_id route has been invoked.")
	return my_project_name + " - " + my_agent_ID

# @application.route('/quit')
# def flask_quit():
# 	func = request.environ.get('werkzeug.server.shutdown')
# 	print(request.environ)
# 	func()
# 	print("/quit route has been invoked.")
# 	return "Quitting..."

@application.route("/invoke", methods=['GET','POST'])
def invoke(configuration = None):
	'''
	This function receives petitions from other Agents or the run command
	This function is invoked through http like this: http://138.4.7.151:5000/invoke?invoked_function=du_0.main
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

	print("=====AGENT: /INVOKE=====")
	print("Thread ID:", threading.get_ident())
	invoked_data = ""
	print("REQUEST.form: ", request.form)
	invoked_function = request.args.get('invoked_function')
	try:
		invoker_function = request.args.get('invoker_function')
	except:
		invoker_function = None
	for i in request.form:
		invoked_data = i
	print("INVOKED DATA:", invoked_data)
	print("invoked_function:", invoked_function)

	# Separate du and function
	j = invoked_function.find(".")
	invoked_du = invoked_function[0:j]
	print("invoked_du:", invoked_du)
	print("du_list:", du_list)
	
	# Queue data stats
	stats_data = {}
	stats_data['invoked'] = invoked_function[j+1:] #only fun name without du
	stats_data['invoker'] = invoker_function
	mp_stats_queue.put(stats_data)

	# If the function belongs to the agent
	if invoked_du in du_list:
		while invoked_du not in loaded_du_list:
			print("The function belongs to the agent, but it has not been loaded yet.")
			time.sleep(1)
		if "%3d" in invoked_data:
			invoked_data = invoked_data.replace("%3d","=")
		try:
			resul = eval(invoked_function+"("+invoked_data+")")
		except:
			resul = eval(invoked_function+"('"+invoked_data+"')")
	else:
		print("This function does not belong to this agent.")
		resul = "none" #remote_invoke(invoked_du, invoked_function) Is this neccesary?
	print()
	return resul

def outgoing_invoke(invoked_du, invoked_function, invoked_data, invoker_function = None, configuration = None):
	global round_robin_index
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
				url='http://'+host+"/invoke?invoked_function="+remote_du+"."+invoked_function)
			Encode data (in the post of the https call)
		Launch the request
		Receive response
			TODO: Test better the decoding of the response, actually makes a try except block diferenciating if the function response a
				JSON object or other type like a string
		The function returns the data received as response (That data is the resul of the invoke function in the other agent)
	'''

	# Internal function to write alarms (files). Parameter is the importance level (the alarm file name)
	def write_alarm(alarm_name):
		(hot_redeploy, cold_redeploy) = check_redeploy_files()
		if not hot_redeploy and not cold_redeploy: 	# Only do something if there are no redeployment files
			possible_alarms = ["CRITICAL", "WARNING"]
			assert alarm_name in possible_alarms
			alarm_file_path = fs_path + os.sep + alarm_name
			open(alarm_file_path, 'a').close() 	# Create an alarm file if it does not exist
			print(alarm_name, " alarm file has been created.")
		else:
			print("Alarm not created due to the existence redeployment files.")


	print("=====AGENT: /REMOTE_INVOKE=====")
	print("Thread ID: ", threading.get_ident())

	# Invoked_du is a list of the DUs that implement the function, but due to latest implementations, it only contains one item
	remote_du = invoked_du[0]

	if remote_du in du_list and remote_du != 'du_default':
		print("local invocation: ",invoked_function)
		print(invoked_du, invoked_function, invoked_data)
		#res=eval(invoked_function)
		print("Hago eval de: "+ invoked_du[0]+"."+invoked_function+"("+invoked_data+")")
		if "%3d" in invoked_data:
			invoked_data = invoked_data.replace("%3d","=")
		res = eval(invoked_du[0]+"."+invoked_function+"("+invoked_data+")")
		print("Responde: ", res)

		# Queue data stats
		stats_data = {}
		stats_data['invoked'] = invoked_function
		stats_data['invoker'] = invoker_function
		mp_stats_queue.put(stats_data)

		try:
			return eval(res)
		except:
			return res

	# Get the possible agents to invoke
	global my_agent_ID
	list_agents = list(cloudbook_dict_agents.get(remote_du)) # Agents containing the DU that has the function to invoke

	# Get the version of the cloudbook in order to check for changes
	invocation_cloudbook_version = cloudbook_version

	invocation_agents_grant = agents_grant

	# Get the agents to invoke
	invocation_agents_list = list_agents[round_robin_index:len(list_agents)] + list_agents[0:round_robin_index]
	last_agent = invocation_agents_list[-1] 	# -1 indicates the last element of the list

	i = 0
	while i < len(list_agents):
		remote_agent = invocation_agents_list[i]
		print("The selected remote agent to invoke is: ", remote_agent, " from list ", list_agents, " rewritten as ", invocation_agents_list)

		# Update round robin index
		if len(list_agents) > 1:
			round_robin_index = (round_robin_index+1) % len(list_agents)
			print("round_robin_index = ", round_robin_index)
		try:
			desired_host_ip_port = invocation_agents_grant[remote_agent]['IP'] + ":" + str(invocation_agents_grant[remote_agent]['PORT'])
			print("Host ip and port: ", desired_host_ip_port)
		except Exception as e:
			print(ERR_IP_NOT_FOUND)
			raise e 	# This should never happen

		try:
			if invoker_function == None:
				url = 'http://'+desired_host_ip_port+"/invoke?invoked_function="+remote_du+"."+invoked_function
			else:
				url = 'http://'+desired_host_ip_port+"/invoke?invoked_function="+remote_du+"."+invoked_function+"&invoker_function="+invoker_function
			print(url)

			send_data = invoked_data.encode()
			print("Sending data: ",send_data)
			request_object = urllib.request.Request(url, send_data)
			print("Request launched: ", url)
			r = urllib.request.urlopen(request_object)
			break
		except:
			print("URL was not answered by " + remote_agent + " (IP:port --> " + desired_host_ip_port + ")")
			write_alarm("WARNING")

			if remote_agent == last_agent: 	# If all agents have been tested
				print("No agents available to execute the requested function.")
				if is_critical(remote_du): 	# If the du is critical
					print("The function that could not be invoked is in a critical du: ", remote_du + "." + invoked_function)
					write_alarm("CRITICAL")
					while True:
						time.sleep(1)
						print("This agent has detected a problem and will be automatically restarted.")
					# raise BaseException(CRIT_ERR_NO_ANSWER)
				else: 	# If the du is NOT critical
					print("The function that could not be invoked is in a NON-critical du: ", remote_du + "." + invoked_function)
					
					# Wait until new cloudbook version is charged
					while invocation_cloudbook_version == cloudbook_version:
						print("Waiting for redeployment to reallocate " + remote_du + " in an accessible agent.")
						time.sleep(1)
					
					# Refresh the variables after the hot redeployment in order to try again
					list_agents = list(cloudbook_dict_agents.get(remote_du))
					invocation_cloudbook_version = cloudbook_version
					invocation_agents_grant = agents_grant
					invocation_agents_list = list_agents[round_robin_index:len(list_agents)] + list_agents[0:round_robin_index]
					last_agent = invocation_agents_list[-1]
					i = 0
					print("Retrying with new cloudbook...")

			else: 	# If there are still agents to try
				print("Retrying...")
				i += 1
		# end_of_except
	# end_of_while
		
	# If the loop finishes with break, then a response has been received and this invocation and function finishes normally.
	print("Response received")

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
def create_agent(grant, project_name, fs=False, agent_0=False):

	# Check paths existence and create if they do not.
	if not os.path.exists(cloudbook_path):
		os.makedirs(cloudbook_path)
	
	poject_path = cloudbook_path + os.sep + project_name
	if not fs:
		fs = poject_path + os.sep + "distributed"
	if not os.path.exists(fs):
		os.makedirs(fs)

	# Create dictionary with the agent info
	agent_config_dict = {} # = {"AGENT_ID": "0", "GRANT_LEVEL": "MEDIUM", "DISTRIBUTED_FS": fs+"/distributed"}
	if agent_0:
		id_num = 0
	else:
		id_num = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
	agent_ID = "agent_" + str(id_num)
	agent_config_dict['AGENT_ID'] = agent_ID
	agent_config_dict['GRANT_LEVEL'] = grant
	agent_config_dict['DISTRIBUTED_FS'] = fs

	# Write dictionary in file
	config_file_path = poject_path + os.sep + "agents" + os.sep + "config_"+agent_ID+".json"
	loader.write_dictionary(agent_config_dict, config_file_path)

	print("\n---  NEW AGENT CREATED  ----------------------------------------------------------------------------")
	print("     Agent_id = ", id_num)
	print("     Grant    = ", grant)
	print("     FSPath   = ", fs)
	print("----------------------------------------------------------------------------------------------------\n")


# This function is used by the GUI. Modifies the the grant level and/or the FS of the current agent according to the parameters given.
def edit_agent(agent_id, project_name, new_grant='', new_fs=''):
	if new_grant=='' and new_fs=='':
		return

	config_agent_file_path = cloudbook_path + os.sep + project_name + os.sep + "agents" + os.sep + "config_"+agent_id+".json"
	config_dict = loader.load_dictionary(config_agent_file_path)

	if(new_grant!=''):
		config_dict["GRANT_LEVEL"] = new_grant
		grant_data = {}
		grant_data['grant'] = new_grant
		grant_queue.put(grant_data)

	if(new_fs!=''):
		config_dict["DISTRIBUTED_FS"] = new_fs

	loader.write_dictionary(config_dict, config_agent_file_path)


# This function launches the flask server in the port given as parameter.
def flaskThreaded(port, sock=None):
	port = int(port)
	print("Launching in port:", port)
	if sock:
		sock.close()
	application.run(debug=False, host="0.0.0.0", port=port, threaded=True)
	# import psutil
	# num_cores = psutil.cpu_count()
	# print("The number of cores of the machine is:", num_cores)
	# application.run(debug=False, host="0.0.0.0", port=port, threaded=False, processes=num_cores)
	# global first_launch
	# first_launch = False
	print("00000000000000000000000000000000000000000000000000000000000000000000000000")

# This function is used in a new process and coordinates the queues for loading data and the DUs to allow Flask execution.
# Espera para siempre mirando mp_agent2flask_queue cada 1 segundo:
# 	Si hay init_info:
# 		Carga la info
# 		Crea project_path
# 	Si hay launch:
# 		Se mira si es un lanzamiento normal o es por un cold redeploy
# 		Si es normal:
# 			Se busca un puerto disponible desde start_port_search en adelante
# 			Se crea el FlaskThread en el puerto disponible 
# 		Si no (es decir, es por un cold_redeploy):
# 			Se lanza el FlaskThread en el puerto start_port_search
# 		Se lanza el thread creado: FlaskThread (en el que se lanza la app que queda corriendo para atender las invocaciones desde otros agentes)
# 		Se hacen peticiones al puerto en el que se ha lanzado Flask hasta obtener respuesta
# 		Se compara el id y proyecto del agente con el que devuelve la peticion:
# 			Si es igual: se manda por mp_flask2agent_queue el dato {"flask_proc_ok":{"local_port": local_port}}
# 			Si es distinto: se manda por mp_flask2agent_queue el dato {"restart_flask_proc": ERR_FLASK_PORT_IN_USE}
# 	Si hay after_launch_info:
# 		Recarga diccionarios (cloudbook_dict_agents, agents_grant, du_list)
# 		Incializa cloudbook_version a 1
# 		Importa el código de las dus
# 		Añade cada du cargada a loaded_du_list
# 	Si hay hot_redeploy: 
# 		Recarga diccionarios (cloudbook_dict_agents, agents_grant)
# 		Aumenta cloudbook_version
def flaskProcessFunction(mp_agent2flask_queue, mp_flask2agent_queue, mp_stats_queue_param):
	print("Flask Process is now active")
	global mp_stats_queue
	mp_stats_queue = mp_stats_queue_param
	# NOT USED globals: configjson_dict, agent_config_dict, grant_queue
	# NOT MODIFIED globals: cloudbook_path, round_robin_index

	# Note: this global variables belong to other process
	# init_info vars:
	global my_agent_ID
	global my_project_name
	global fs_path
	global project_path
	start_port_search = 5000

	# launch vars:
	flask_thread = None

	# after_launch_info vars:
	global cloudbook_dict_agents
	global agents_grant
	global cloudbook_version
	global du_list
	global loaded_du_list

	# hot_redeploy vars:
	# global cloudbook_dict_agents
	# global agents_grant
	# global cloudbook_version

	# local_port = None
	# global first_launch
	# first_launch = True
	while True:
		while not mp_agent2flask_queue.empty():
			item = mp_agent2flask_queue.get()
			
			if "init_info" in item:
				try:
					my_agent_ID = item["init_info"]["my_agent_ID"]
					my_project_name = item["init_info"]["my_project_name"]
					fs_path = item["init_info"]["fs_path"]
					start_port_search = item["init_info"]["start_port_search"]

					project_path = cloudbook_path + os.sep + my_project_name
				except Exception as e:
					print(ERR_QUEUE_KEY_VALUE)
					raise e

			elif "launch" in item:
				try:
					launch = item["launch"]
					cold_redeploy = item["launch"]["cold_redeploy"]
				except Exception as e:
					print(ERR_QUEUE_KEY_VALUE)
					raise e
				try:
					if not cold_redeploy:
						(local_port, sock) = get_port_available(port=start_port_search)
						flask_thread = threading.Thread(target=flaskThreaded, args=[local_port, sock], daemon=True)
					else:
						local_port = start_port_search
						flask_thread = threading.Thread(target=flaskThreaded, args=[local_port], daemon=True)
					flask_thread.start()

					retrieved_project_id = None
					while not retrieved_project_id:
						try:
							retrieved_data = urllib.request.urlopen("http://localhost:"+str(local_port)+"/get_project_agent_id")
							retrieved_project_id = retrieved_data.read().decode('UTF-8')
						except Exception as e:
							print(ERR_GET_PROJ_ID_REFUSED)
							time.sleep(0.5)
							print("Retrying...")
					
					mp_queue_data = {}
					if my_project_name + " - " + my_agent_ID == retrieved_project_id:
						mp_queue_data["flask_proc_ok"] = {}
						mp_queue_data["flask_proc_ok"]["local_port"] = local_port
					else:
						print(ERR_FLASK_PORT_IN_USE) # This is the 2nd flask in the same port (race conditions)
						print("The flask process will be restarted automatically.")
						mp_queue_data["restart_flask_proc"] = ERR_FLASK_PORT_IN_USE
					mp_flask2agent_queue.put(mp_queue_data)
				except Exception as e:
					print(GEN_ERR_LAUNCHING_FLASK)
					raise e

			elif "after_launch_info" in item:
				if loaded_du_list:
					print(ERR_DUS_ALREADY_LOADED)
					raise Exception()
				try:
					cloudbook_dict_agents = item["after_launch_info"]["cloudbook_dict_agents"]
					agents_grant = item["after_launch_info"]["agents_grant"]
					cloudbook_version = 1

					du_list = item["after_launch_info"]["du_list"]
				except Exception as e:
					print(ERR_QUEUE_KEY_VALUE)
					raise e
				try:
					print("The list of DUs to load in this agent is:", du_list)
					sys.path.append(fs_path)
					du_files_path = fs_path + os.sep + "du_files"
					for du in du_list:
						print("  Trying to load", du)
						if is_critical(du) and cloudbook_is_running():
							print("  ", ERR_LOAD_CRIT_DU_CLOUDBOOK_RUNNING)
							print("  ", du, "has been skipped (not loaded)")
							break
						du_i_file_path = du_files_path + os.sep + du+".py"
						if not os.path.exists(du_i_file_path):
							print(ERR_DUS_NOT_EXIST)
							time.sleep(1)
						exec("global "+du, globals())
						exec("from du_files import "+du, globals())
						exec(du+".invoker=outgoing_invoke")
						print("  ", du, "successfully loaded")
						loaded_du_list.append(du)
					
					if all([du in loaded_du_list for du in du_list]):
						print("All DUs have been loaded successfully.")

				except Exception as e:
					print(GEN_ERR_LOADING_DUS)
					raise e

			elif "hot_redeploy" in item:
				try:
					cloudbook_dict_agents = item["hot_redeploy"]["cloudbook_dict_agents"]
					agents_grant = item["hot_redeploy"]["agents_grant"]

					cloudbook_version += 1
				except Exception as e:
					print(ERR_QUEUE_KEY_VALUE)
					raise e

			else:
				print(ERR_QUEUE_KEY_VALUE)

		time.sleep(1)


# Target function of the stats file creator thread. Implements the consumer of the producer/consumer model using mp_stats_queue.
def create_stats(t1):
	print("Stats creator thread started")
	time_start = time.monotonic()
	stats_dictionary = {}
	stats_file_path = project_path + os.sep + "distributed" + os.sep + "stats" + os.sep + "stats_"+my_agent_ID+".json"

	while True:
		current_time = time.monotonic()
		while not mp_stats_queue.empty():
			item = mp_stats_queue.get()
			#print("New stat: ", item)

			# Add data to dictionary
			try:
				invoker = item['invoker']
				invoked = item['invoked']
			except:
				print(ERR_QUEUE_KEY_VALUE, "Stats queue needs invoker/invoked keys.")

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

		# In case that it is time to create the stats file, add t1 to time_start and write the dictionary in the stats_agent_XX.json
		if current_time-time_start >= t1:
			time_start += t1
			loader.write_dictionary(stats_dictionary, stats_file_path)
			stats_dictionary = {}

		# Wait 1 second to look for more data in the queue
		time.sleep(1)


# This function passes the initial data to the FlaskProcess through the mp_queue, tells it to launch the FlaskThread and checks
# if it has worked correctly with no port collisions. If everything is ok, retrives the used local_port. If there is a problem
# (a port collision), restarts the FlaskProcess.
def init_flask_process_and_check_ok(cold_redeploy):
	global my_agent_ID, my_project_name, fs_path, start_port_search, mp_flask2agent_queue, mp_agent2flask_queue, flask_proc
	# Create the init_info_item for FlaskProcess
	# {"init_info": {"my_agent_ID": my_agent_ID, "my_project_name": my_project_name, "fs_path": fs_path, 
	#				"start_port_search": start_port_search}}
	init_info_item = {}
	init_info_item["init_info"] = {}
	init_info_item["init_info"]["my_agent_ID"] = my_agent_ID
	init_info_item["init_info"]["my_project_name"] = my_project_name
	init_info_item["init_info"]["fs_path"] = fs_path
	init_info_item["init_info"]["start_port_search"] = start_port_search

	# Create the launch_item for the FlaskProcess
	# {"launch": True}
	launch_item = {}
	launch_item["launch"] = {}
	launch_item["launch"]["cold_redeploy"] = cold_redeploy

	# If cold_redeploy, create virtual restart request from the flask proecess
	if cold_redeploy:
		mp_queue_data = {}
		mp_queue_data["restart_flask_proc"] = "Requested restart from deployer (cold redeploy)."
		mp_flask2agent_queue.put(mp_queue_data)
	# Else, pass the items to FlaskProcess through the agent2flask queue
	else:
		mp_agent2flask_queue.put(init_info_item)
		mp_agent2flask_queue.put(launch_item)

	# Check the FlaskProcess launched the FlaskThread correctly and there are no collisions on ports (and retrieve local_port).
	# If there is a port collision, restart the FlaskProcess
	flask_proc_ok = False
	while not flask_proc_ok:
		while not mp_flask2agent_queue.empty():
			item = mp_flask2agent_queue.get()

			if "flask_proc_ok" in item:
				try:
					local_port = item["flask_proc_ok"]["local_port"]
					flask_proc_ok = True
					break
				except Exception as e:
					print(ERR_QUEUE_KEY_VALUE)
					raise e

			elif "restart_flask_proc" in item:
				# try:
				# 	restart_reason = item["restart_flask_proc"]
				# 	print(restart_reason)
				# except Exception as e:
				# 	print(ERR_QUEUE_KEY_VALUE)
				# 	raise e
				try:
					print("Restarting the flask process...")
					# Create new mp_queues (so that they are clear)
					mp_agent2flask_queue = Queue()
					mp_flask2agent_queue = Queue()

					# Terminate and create a new FlaskProcess
					flask_proc.terminate()
					flask_proc = Process(target=flaskProcessFunction, args=(mp_agent2flask_queue, mp_flask2agent_queue, mp_stats_queue))
					flask_proc.start()

					# Pass initial info and launch
					mp_agent2flask_queue.put(init_info_item)
					mp_agent2flask_queue.put(launch_item)
					break

				except Exception as e:
					print(GEN_ERR_RESTARTING_FLASK)
					raise e

			else:
				print(ERR_QUEUE_KEY_VALUE)

		time.sleep(1)

	if local_port:
		# Next time the function is called, it will try to start in the same port as before
		start_port_search = local_port
		return local_port
	else:
		raise Exception(GEN_ERR_INIT_CHECK_FLASK)


# This function checks if the port passed as parameter is available or in use, trying to bind that port to a socket. Then, the socket is
# closed and the result (true/false) is returned.
# def check_port_available(port):
# 	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 	available = False
# 	try:
# 		sock.bind(("0.0.0.0", port))
# 		print("Port " + str(port) + " is available.")
# 		available = True
# 	except:
# 		print("Port " + str(port) + " is in use.")
# 	sock.close()
# 	return available


# This function finds the first port available strating from the port given as parameter onwards. Returns the port and the
# socket which is blocking the port for other applications (close it before attempting to run any application in that port).
def get_port_available(port):
	available = False
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	while not available:
		try:
			sock.bind(("0.0.0.0", port))
			print("Port " + str(port) + " is available.")
			available = True
		except:
			print("Port " + str(port) + " is in use.")
			sock.close()
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			port += 1
	return (port, sock)


# This function gets the local IP. In the case of multiple IPs, gets the default route.
def get_local_ip():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		# doesn't even have to be reachable
		s.connect(('10.255.255.255', 1))
		local_ip = s.getsockname()[0]
	except:
		local_ip = '127.0.0.1'
	finally:
		s.close()
	return local_ip


# This function gets the local IP if the lan_mode is set to True and the external IP and port if the lan_mode is set to False.
# The function raises an exception if it could not retrieve the requested data.
def get_port_and_ip(lan_mode=True):
	ip, port = None, None

	if lan_mode:
		ip = get_local_ip()
		if ip==None:
			raise Exception(ERR_NO_LAN)
	else:
		(_, ip, port) = get_ip_info() 
		if ip==None or port==None:
			raise Exception(ERR_NO_INTERNET)
	return (ip, port)


# This function checks if cloudbook is already running in order not to load critical DUs in cold redeploy
def cloudbook_is_running():
	running_file_path = fs_path + os.sep + "RUNNING"
	running = False
	if os.path.exists(running_file_path):
		#print("RUNNING file found.")
		running = True
	return running


# This function checks if there are any redeployment files
def check_redeploy_files():
	hot_redeploy_file_path = fs_path + os.sep + "HOT_REDEPLOY"
	cold_redeploy_file_path = fs_path + os.sep + "COLD_REDEPLOY"
	hot_redeploy = False
	cold_redeploy = False
	if os.path.exists(hot_redeploy_file_path):
		#print("HOT_REDEPLOY file found.")
		hot_redeploy = True
	if os.path.exists(cold_redeploy_file_path):
		#print("COLD_REDEPLOY file found.")
		cold_redeploy = True
	return (hot_redeploy, cold_redeploy)


# This function check if a du is critical
def is_critical(du):
	critical_dus_file_path = fs_path + os.sep + "critical_dus.json"
	critical_dus_dict = loader.load_dictionary(critical_dus_file_path)
	critical_dus = critical_dus_dict["critical_dus"]
	return du in critical_dus



#####   AGENT MAIN   #####
if __name__ == "__main__":
	print("Starting agent...")

	# Process parameters
	num_param = len(sys.argv)
	for i in range(1,len(sys.argv)):
		if sys.argv[i]=="-agent_id":
			print(sys.argv[i], sys.argv[i+1])
			agent_id = sys.argv[i+1]
			i=i+1
		if sys.argv[i]=="-project_folder":
			print(sys.argv[i], sys.argv[i+1])
			my_project_name = sys.argv[i+1]
			i=i+1
	
	# Check if the non-optional parameters have been set
	if not agent_id:
		print ("option -agent_id missing")
		sys.exit(1)
	if not my_project_name:
		print ("option -project_folder missing")
		sys.exit(1)

	# Load agent config file
	project_path = cloudbook_path + os.sep + my_project_name
	agent_config_dict = loader.load_dictionary(project_path + os.sep + "agents" + os.sep + "config_"+agent_id+".json")

	my_agent_ID = agent_config_dict["AGENT_ID"]
	fs_path = agent_config_dict["DISTRIBUTED_FS"]
	my_grant = agent_config_dict["GRANT_LEVEL"]

	# Load circle config file
	configjson_dict = loader.load_dictionary(fs_path + os.sep + "config.json")

	agent_stats_interval = configjson_dict['AGENT_STATS_INTERVAL']
	agent_grant_interval = configjson_dict['AGENT_GRANT_INTERVAL']
	lan_mode = configjson_dict['LAN']

	# Check if fs_path is not empty
	if fs_path=='':
		fs_path = poject_path + os.sep + "distributed"
		print("Path to distributed filesystem was not set in the agent, default will be used: ", fs_path)

	# Print settings
	settings_string = "\n"
	settings_string += "The agent has the following configuration:\n"
	settings_string += "  - ID: " + my_agent_ID + "\n"
	settings_string += "  - Project: " + my_project_name + "\n"
	settings_string += "  - Grant: " + my_grant + "\n"
	settings_string += "  - FSPath: " + fs_path + "\n"
	settings_string += "  - Stats creation period: " + str(agent_stats_interval) + "\n"
	settings_string += "  - Grant file creation period: " + str(agent_grant_interval) + "\n"
	if lan_mode:
		settings_string += "  - Lan mode: ON (using local ip and port)\n"
	else:
		settings_string += "  - Lan mode: OFF (using external ip and port)\n"
	print(settings_string)
	# print("The agent has the following configuration:\n")
	# print("  - ID:", my_agent_ID)
	# print("  - Project:", my_project_name)
	# print("  - Grant:", my_grant)
	# print("  - FSPath:", fs_path)
	# print("  - Stats creation period:", agent_stats_interval)
	# print("  - Grant file creation period:", agent_grant_interval)
	# if lan_mode:
	# 	print("  - Lan mode: ON (using local ip and port)")
	# else:
	# 	print("  - Lan mode: OFF (using external ip and port)")

	# Input/output queues for process communication
	mp_agent2flask_queue = Queue()
	mp_flask2agent_queue = Queue()
	mp_stats_queue = Queue()

	# Launch the FlaskProcess
	flask_proc = Process(target=flaskProcessFunction, args=(mp_agent2flask_queue, mp_flask2agent_queue, mp_stats_queue))
	flask_proc.start()

	# Launch the stats file creator thread
	threading.Thread(target=create_stats, args=(agent_stats_interval,)).start()

	# Set up the logger
	log = logging.getLogger('werkzeug')
	log.setLevel(logging.ERROR)

	# Try (up to 3 times) to get ip and port to share with the rest of cloudbook
	retrys = 3
	for i in range(retrys):
		try:
			(ip, port) = get_port_and_ip(lan_mode=lan_mode)
			break
		except Exception as e:
			print(e)
			if i!=retrys:
				time.sleep(1)
				print("Retrying...")
			else:
				raise e

	# Number where the search for a free port will begin
	start_port_search = 5000

	# Does not need arguments because this is the global name space, and all these variables can be accessed as globals
	local_port = init_flask_process_and_check_ok(cold_redeploy=False)

	# Update the port (from None to the local_port) in the case of a lan_mode is active
	if lan_mode:
		port = local_port

	# Create and fill dictionary with initial data
	grant_dictionary = {}
	grant_dictionary[my_agent_ID] = {}
	grant_dictionary[my_agent_ID]["GRANT"] = my_grant
	grant_dictionary[my_agent_ID]["IP"] = ip
	grant_dictionary[my_agent_ID]["PORT"] = port

	# Build the paths to the different files
	agent_X_grant_file_path = project_path + os.sep + "distributed" + os.sep + "agents_grant" + os.sep + my_agent_ID+"_grant.json"
	agents_grant_file_path = project_path + os.sep + "distributed" + os.sep + "agents_grant.json"
	cloudbookjson_file_path = fs_path + os.sep + "cloudbook.json"

	# Internal function to write the "agent_X_grant.json" file consumed by the deployer
	def write_agent_X_grant_file():
		#print("Grant file will be updated with: ", grant_dictionary)
		loader.write_dictionary(grant_dictionary, agent_X_grant_file_path)

	# Internal function to load the "agents_grant.json" file created by the deployer
	def read_agents_grant_file():
		global agents_grant
		agents_grant = loader.load_dictionary(agents_grant_file_path)
		#print("agents_grant.json has been read.\n agents_grant = ", agents_grant)

	# Internal function to load the "cloudbook.json" file created by the deployer
	def read_cloudbook_file(hot_redeploy=False):
		global cloudbook_dict_agents
		global du_list
		cloudbook_dict_agents = loader.load_dictionary(cloudbookjson_file_path)
		#print("cloudbook.json has been read.\n cloudbook_dict_agents = ", cloudbook_dict_agents)
		if not hot_redeploy:
			du_list = loader.load_cloudbook_agent_dus(my_agent_ID, cloudbook_dict_agents)

	# Get the cloudbook and the agents_grant (DUs and IP/port of each agent).
	while not du_list:
		try:
			write_agent_X_grant_file()
			while not os.path.exists(agents_grant_file_path) or not os.path.exists(cloudbookjson_file_path) or os.stat(cloudbookjson_file_path).st_size==0:
				print("Waiting for agents_grant.json and cloudbook.json")
				if not os.path.exists(agent_X_grant_file_path):
					print("My grant file was deleted! Creating it again...")
					write_agent_X_grant_file()
				time.sleep(1)
			read_agents_grant_file()
			read_cloudbook_file()
		except:
			print(ERR_READ_WRITE)
			time.sleep(1)
			print("Retrying...")

	print("My du_list: ", du_list)

	# Pass the after_launch_info to the FlaskProcess
	# {"after_launch_info": {"du_list": du_list, "cloudbook_dict_agents": cloudbook_dict_agents, "agents_grant": agents_grant}}
	after_launch_info_item = {}
	after_launch_info_item["after_launch_info"] = {}
	after_launch_info_item["after_launch_info"]["du_list"] = du_list
	after_launch_info_item["after_launch_info"]["cloudbook_dict_agents"] = cloudbook_dict_agents
	after_launch_info_item["after_launch_info"]["agents_grant"] = agents_grant
	mp_agent2flask_queue.put(after_launch_info_item)

	# Forever loop (check grant modifications, write grant_XX_file, check and handle redeploy requests)
	time_start = time.monotonic()
	grant = None
	while True:
		current_time = time.monotonic()

		# While there is data in the queue, analyze it
		while not grant_queue.empty():
			item = grant_queue.get()
			#print("Grant item retrieved from queue: ", item)
			try:
				item_grant = item['grant']
				if item_grant=='HIGH' or item_grant=='MEDIUM' or item_grant=='LOW':
					grant = item_grant
				else:
					print(ERR_QUEUE_KEY_VALUE, "Grant queue invalid value.")
			except:
				print(ERR_QUEUE_KEY_VALUE, "Grant queue invalid key.")

		# When the the interval time expires
		if current_time-time_start >= agent_grant_interval:
			time_start += agent_grant_interval

			# Check if there are redeployment files
			(hot_redeploy, cold_redeploy) = check_redeploy_files()
			if hot_redeploy:
				print("Executing HOT_REDEPLOY...")
				read_agents_grant_file()
				read_cloudbook_file(hot_redeploy=True)
				# Pass the init_info to the FlaskProcess
				# {"hot_redeploy": {"cloudbook_dict_agents": cloudbook_dict_agents, "agents_grant": agents_grant}}
				hot_redeploy_item = {}
				hot_redeploy_item["hot_redeploy"] = {}
				hot_redeploy_item["hot_redeploy"]["cloudbook_dict_agents"] = cloudbook_dict_agents
				hot_redeploy_item["hot_redeploy"]["agents_grant"] = agents_grant
				mp_agent2flask_queue.put(hot_redeploy_item)
				
				# ! - IMPROVEMENT: Check if the agent only has loaded the du_default and load more in hot redeploy???
			if cold_redeploy:
				print("Executing COLD_REDEPLOY...")
				flask_proc.terminate()
				local_port = init_flask_process_and_check_ok(cold_redeploy=True)

				# Update the port (from None to the local_port) in the case of a lan_mode is active
				if lan_mode:
					port = local_port
				grant_dictionary[my_agent_ID]["PORT"] = port

				# It is supposed that agents_grant.json and cloudbook.json already exists
				read_agents_grant_file()
				read_cloudbook_file()

				print("My new du_list: ", du_list)

				# Pass the after_launch_info to the FlaskProcess
				# {"after_launch_info": {"du_list": du_list, "cloudbook_dict_agents": cloudbook_dict_agents, "agents_grant": agents_grant}}
				after_launch_info_item = {}
				after_launch_info_item["after_launch_info"] = {}
				after_launch_info_item["after_launch_info"]["du_list"] = du_list
				after_launch_info_item["after_launch_info"]["cloudbook_dict_agents"] = cloudbook_dict_agents
				after_launch_info_item["after_launch_info"]["agents_grant"] = agents_grant
				mp_agent2flask_queue.put(after_launch_info_item)

			# Update dictionary with new data (grant)
			if grant!= None:
				grant_dictionary[my_agent_ID]["GRANT"] = grant

			# Update also IP/port ??? --> call get_ip_info() again and update if necessary
			#grant_dictionary[my_agent_ID]["IP"] = ip
			#grant_dictionary[my_agent_ID]["PORT"] = port

			# Write dictionary in "agent_X_grant.json" and read dictionary from "agents_grant.json"
			write_agent_X_grant_file()
			grant = None

		# Wait 1 second to look for more data in the queue
		time.sleep(1)

	print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")