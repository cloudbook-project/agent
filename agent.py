from flask import Flask
from flask import request
from flask import abort, redirect, url_for
import loader
import os, sys, time, threading, logging, platform
from multiprocessing import Process
from pynat import get_ip_info #requires pip3 install pynat
import urllib # this import requires pip3 install urllib
import queue
import socket
import random, string
import builtins



#####   GLOBAL VARIABLES   #####

# Identifier of this agent
my_agent_ID = None

# Identifier of the project that this agent belongs to
my_project_name = None

# Dictionary of dus and location
#cloudbook_dict_dus = {}

# Dictionary of agents 
cloudbook_dict_agents = {}

# List of deployable units loaded by this agent
du_list = []

# Dictionary of agent configuration
agent_config_dict = {}

# Dictionary of circle configuration
configjson_dict = {}

# Global variable to define working mode
#LOCAL_MODE = False

# All dus that contain the program
all_dus = []

# Index in order to make the round robin assignation of invocation requests
round_robin_index = 0

# FIFO queue that passes stats to the stats file creator thread
stats_queue = queue.Queue(maxsize=0)

# FIFO queue that passes the changes of grant to the grant file creator thread
grant_queue = queue.Queue(maxsize=0)

# Global variable to store the general path to cloudbook, used to access all files and folders needed
if(platform.system()=="Windows"):
	cloudbook_path = os.environ['HOMEDRIVE'] + os.environ['HOMEPATH'] + os.sep + "cloudbook"
else:
	cloudbook_path = os.environ['HOME'] + os.sep + "cloudbook"

# Path to the project the agent belongs to
project_path = None

# Variable that contains the information from agents_grant.json (last read)
#Format:
# {
# 	"agent_0": {"GRANT": "LOW", "IP": "192.168.1.44", "PORT": 5000},
# 	"agent_G2UQXFV1O2NWTNRQY8GD": {"GRANT": "LOW", "IP": "192.168.1.44", "PORT": 5001},
# 	"agent_IGPAMITGCCPPYMTQ4BQA": {"GRANT": "LOW", "IP": "192.168.1.44", "PORT": 5002},
# 	"agent_OMRZ22CQB157H3POXG3A": {"GRANT": "LOW", "IP": "192.168.1.44", "PORT": 5003}
# }
agents_grant = {}

# Global boolean variable for the state of the dus that the agent has to load (True if they have been loaded, False otherwise)
dus_loaded = False

# Number of times the cloudbook has changed and DUs have been (re)loaded
cloudbook_version = 0



#####   CONSTANTS   #####
CRIT_ERR_NO_ANSWER = "CLOUDBOOK CRITICAL ERROR: no agent could answer the remote invokation to a function in a critical DU. \
The DU state is lost and program is corrupt. Critical alarm created in the distributed filesystem in order that depployer's \
surveillance monitor knows that an invokation has failed. BaseException raised in order to try to stop the program."
CRIT_ERR_IP_NOT_FOUND = "ERROR: cannot find the ip and port for invoking the desired agent."
ERR_QUEUE_KEY_VALUE = "ERROR: There was a problem item obtained from the queue. Wrong key/value."
ERR_READ_WRITE = "ERROR: reading/writing not allowed or wrong path."



#####   OVERLOAD BUILT-IN FUNCITONS   #####

# Print function overloaded in order to make it print the id before anything and then keep track of the traces of each agent.
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

	while not dus_loaded:
		print("Invoked but waiting for dus to be loaded.")
		time.sleep(1)

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
	stats_queue.put(stats_data)

	# If the function belongs to the agent
	if invoked_du in du_list:
		resul = eval(invoked_function+"("+invoked_data+")")
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
		possible_alarms = ["CRITICAL", "WARNING"]
		assert alarm_name in possible_alarms
		alarm_file_path = agent_config_dict["DISTRIBUTED_FS"] + os.sep + alarm_name
		open(alarm_file_path, 'a').close() 	# Create an alarm file if it does not exist
		print(alarm_name, " alarm file has been created.")


	print("=====AGENT: /REMOTE_INVOKE=====")
	print("Thread ID: ", threading.get_ident())

	# Invoked_du is a list of the DUs that implement the function, but due to latest implementations, it only contains one item
	remote_du = invoked_du[0]

	if remote_du in du_list and remote_du != 'du_default':
		print("local invocation: ",invoked_function)
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
			print(CRIT_ERR_IP_NOT_FOUND)
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
				if remote_du in critical_dus: 	# If the du is critical
					print("The function that could not be invoked is in a critical du: ", remote_du + "." + invoked_function)
					write_alarm("CRITICAL")
					# while True:
					# 	time.sleep(1)
					# 	print(This agent must be restarted. It is currently not possible to recover from this situation.")
					raise BaseException(CRIT_ERR_NO_ANSWER)
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
	global my_agent_ID
	global my_project_name
	global project_path

	my_project_name = project_name
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
	my_agent_ID = "agent_" + str(id_num)
	agent_config_dict['AGENT_ID'] = my_agent_ID
	agent_config_dict['GRANT_LEVEL'] = grant
	agent_config_dict['DISTRIBUTED_FS'] = fs

	# Write dictionary in file
	config_file_path = poject_path + os.sep + "agents" + os.sep + "config_"+my_agent_ID+".json"
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
def flaskThreaded(port):
	port = int(port)
	print("Launched in port:", port)
	application.run(debug=False, host="0.0.0.0",port=port,threaded=True)
	print("00000000000000000000000000000000000000000000000000000000000000000000000000")

# This function raises an error
def raise_error():
	raise BaseException("Exception solicitada por main del agente")


# Target function of the stats file creator thread. Implements the consumer of the producer/consumer model using stats_queue.
def create_stats(t1):
	print("Stats creator thread started")
	time_start = time.monotonic()
	stats_dictionary = {}
	stats_file_path = project_path + os.sep + "distributed" + os.sep + "stats" + os.sep + "stats_"+my_agent_ID+".json"

	while True:
		current_time = time.monotonic()
		while not stats_queue.empty():
			item = stats_queue.get()
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

			stats_queue.task_done()

		# In case that it is time to create the stats file, add t1 to time_start and write the dictionary in the stats_agent_XX.json
		if current_time-time_start >= t1:
			time_start += t1
			loader.write_dictionary(stats_dictionary, stats_file_path)
			stats_dictionary = {}

		# Wait 1 second to look for more data in the queue
		time.sleep(1)


# Target function of the grant file creator thread. Implements the consumer of the producer/consumer model using  grant_queue.
# If the internal port is given it is used with the local IP. Otherwise, external IP and port are used.
def create_grant(agent_grant_interval, init_grant, int_port=0, fs_path=''):
	print("Agent info (grant,ip,port) file creator thread starts execution")
	time_start = time.monotonic()

	# Get IPs and ports and verify they are correct
	(_, ext_ip, ext_port, int_ip) = get_ip_info(include_internal=True)
	while ext_ip==None or ext_port==None or int_ip==None:
		(_, ext_ip, ext_port, int_ip) = get_ip_info(include_internal=True)
	print("ext_ip, ext_port, int_ip, int_port:", ext_ip, ext_port, int_ip, int_port)

	# Create and fill dictionary with initial data
	grant_dictionary = {}
	grant_dictionary[my_agent_ID] = {}
	grant_dictionary[my_agent_ID]["GRANT"] = init_grant
	if int_port==0: 	# If no internal port is given, use externals
		grant_dictionary[my_agent_ID]["IP"] = ext_ip
		grant_dictionary[my_agent_ID]["PORT"] = ext_port
	else: 				# Use internal IP and port
		grant_dictionary[my_agent_ID]["IP"] = int_ip
		grant_dictionary[my_agent_ID]["PORT"] = int_port

	# Check if fs_path is not empty
	if fs_path=='':
		fs_path = poject_path + os.sep + "distributed"
		print("Path to distributed filesystem was not set in the agent, default will be used: ")

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
	def read_cloudbook_file():
		global cloudbook_dict_agents
		global all_dus
		cloudbook_dict_agents = loader.load_dictionary(cloudbookjson_file_path)
		#print("cloudbook.json has been read.\n cloudbook_dict_agents = ", cloudbook_dict_agents)

		# Get all dus
		all_dus = []
		for i in cloudbook_dict_agents:
			all_dus.append(i)

	# # Internal function to import the DUs in the agent
	# def import_DUs_into_agent():
	# 	global du_list

	# 	# Load the DUs that belong to this agent.
	# 	du_list = loader.load_cloudbook_agent_dus(my_agent_ID, cloudbook_dict_agents)
	# 	print("My du_list: ", du_list)

	# 	sys.path.append(fs_path)
	# 	'''for du in du_list:
	# 		exec ("from du_files import "+du)
	# 		exec(du+".invoker=outgoing_invoke")'''

	# 	du_files_path = fs_path + os.sep + "du_files"
	# 	UNIX_du_files_path = du_files_path.replace(os.sep, "/")
	# 	for du in du_list:
	# 		print(du)
	# 		du_i_file_path = du_files_path + os.sep + du+".py"
	# 		while not os.path.exists(du_i_file_path):
	# 			time.sleep(0.1)
	# 		##OJO CON ESTO QUE HAY QUE PROBARLO BIEN BIEN
	# 		exec('sys.path.append('+"'"+UNIX_du_files_path+"'"+')')
	# 		# exec("from du_files import "+du)
	# 		globals()[du] = __import__(du, fromlist=["du_files"])
	# 		globals()[du+'invoker'] = outgoing_invoke
	# 		#exec(du+".invoker=outgoing_invoke")# read file
	# 		print(du+" charged")
			
	# 		# exec('sys.path.append('+"'"+UNIX_du_files_path+"'"+')')
	# 		# print('sys.path.append('+"'"+UNIX_du_files_path+"'"+')')
	# 		# exec("from du_files import "+du)
	# 		# print("from du_files import "+du)
	# 		# exec(du+".invoker=outgoing_invoke")# read file
	# 		# print(du+".invoker=outgoing_invoke")# read file
	# 		# print(du+" charged")

	# # Deletes the previously imported DUs from the agent (if there was any)
	# # def delete_imported_DUs_from_agent():
	# # 	sys.path.append(fs_path)
	# # 	'''for du in du_list:
	# # 		exec ("from du_files import "+du)
	# # 		exec(du+".invoker=outgoing_invoke")'''

	# # 	du_files_path = fs_path + os.sep + "du_files"
	# # 	UNIX_du_files_path = du_files_path.replace(os.sep, "/")
	# # 	for du in du_list:
	# # 		print(du)
	# # 		du_i_file_path = du_files_path + os.sep + du+".py"
	# # 		while not os.path.exists(du_i_file_path):
	# # 			time.sleep(0.1)
	# # 		##OJO CON ESTO QUE HAY QUE PROBARLO BIEN BIEN
			
	# # 		exec('sys.path.append('+"'"+UNIX_du_files_path+"'"+')')
	# # 		exec("from du_files import "+du)
	# # 		exec(du+".invoker=outgoing_invoke")# read file
	# # 		print(du+" charged")

	# # Do the necessary writes and reads
	# print('agent_X_grant_file_path = ', agent_X_grant_file_path)
	# print('agents_grant_file_path = ', agents_grant_file_path)
	# print('cloudbookjson_file_path = ', cloudbookjson_file_path)
	# write_agent_X_grant_file()
	# while not os.path.exists(agents_grant_file_path) or not os.path.exists(cloudbookjson_file_path) or os.stat(cloudbookjson_file_path).st_size==0:
	# 	print("Waiting for agents_grant.json and cloudbook.json")
	# 	time.sleep(1)
	# read_agents_grant_file()
	# read_cloudbook_file()
	# import_DUs_into_agent()

	# grant = None
	# while True:
	# 	current_time = time.monotonic()

	# 	# While there is data in the queue, analyze it
	# 	while not grant_queue.empty():
	# 		item = grant_queue.get()
	# 		#print("Grant item retrieved from queue: ", item)
	# 		try:
	# 			item_grant = item['grant']
	# 			if item_grant=='HIGH' or item_grant=='MEDIUM' or item_grant=='LOW':
	# 				grant = item_grant
	# 			else:
	# 				print("ERROR: The grant obtained from the queue is not valid. Invalid value.")
	# 		except:
	# 			print("ERROR: There was a problem with the grant item obtained from the queue. Invalid key.")

	# 	# When the the interval time expires
	# 	if current_time-time_start >= agent_grant_interval:
	# 		time_start += agent_grant_interval

	# 		# Update dictionary with new data (grant)
	# 		if grant!= None:
	# 			grant_dictionary[my_agent_ID]["GRANT"] = grant
	# 			#print('Grant dict updated')

	# 		# Update also IP/port ??? --> call get_ip_info() again and update if necessary
	# 		#grant_dictionary[my_agent_ID]["IP"] = ip
	# 		#grant_dictionary[my_agent_ID]["PORT"] = port

	# 		# Write dictionary in "agent_X_grant.json" and read dictionary from "agents_grant.json"
	# 		write_agent_X_grant_file()
	# 		read_agents_grant_file()
	# 		grant = None

	# 	# Wait 1 second to look for more data in the queue
	# 	time.sleep(1)


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

	# Load agent config file
	agent_id = sys.argv[1]
	project_name = sys.argv[2]
	project_path = cloudbook_path + os.sep + project_name
	agent_config_dict = loader.load_dictionary(project_path + os.sep + "agents" + os.sep + "config_"+agent_id+".json")

	my_agent_ID = agent_config_dict["AGENT_ID"]
	fs_path = agent_config_dict["DISTRIBUTED_FS"]
	my_grant = agent_config_dict["GRANT_LEVEL"]

	# Load circle config file
	configjson_dict = loader.load_dictionary(fs_path + os.sep + "config.json")

	agent_stats_interval = configjson_dict['AGENT_STATS_INTERVAL']
	agent_grant_interval = configjson_dict['AGENT_GRANT_INTERVAL']
	lan_mode = configjson_dict['LAN']

	# Check lan mode is on or off to use internal or external ips and ports respectively
	if lan_mode:
		# Check the first port available from 5000 (included) onwards
		local_port = 5000
		while not check_port_available(local_port):
			local_port += 1
		print("Lan mode ON: the first port available from 5000 onwards is ", local_port)
	else:
		local_port = 0
		print("Lan mode OFF: using external ip and port.")

	# LAUNCH THREADS
	# Launch invoke listener thread
	#Process(target=flaskThreaded, args=(local_port,)).start()
	threading.Thread(target=flaskThreaded, args=[local_port]).start()
	#flaskThreaded(local_port)

	# Launch the stats file creator thread
	threading.Thread(target=create_stats, args=(agent_stats_interval,)).start()

	# Launch the grant file creator thread
	#threading.Thread(target=create_grant, args=(agent_grant_interval,my_grant,local_port,fs_path,)).start()
	##############################################################################################################
	##############################################################################################################
	##############################################################################################################
	init_grant = my_grant
	int_port = local_port
	##########################################
	print("Agent info (grant,ip,port) file creator thread starts execution.")
	time_start = time.monotonic()

	# Get IPs and ports and verify they are correct
	(_, ext_ip, ext_port, int_ip) = get_ip_info(include_internal=True)
	while ext_ip==None or ext_port==None or int_ip==None:
		(_, ext_ip, ext_port, int_ip) = get_ip_info(include_internal=True)
	print("ext_ip, ext_port, int_ip, int_port:", ext_ip, ext_port, int_ip, int_port)

	# Create and fill dictionary with initial data
	grant_dictionary = {}
	grant_dictionary[my_agent_ID] = {}
	grant_dictionary[my_agent_ID]["GRANT"] = init_grant
	if int_port==0: 	# If no internal port is given, use externals
		grant_dictionary[my_agent_ID]["IP"] = ext_ip
		grant_dictionary[my_agent_ID]["PORT"] = ext_port
	else: 				# Use internal IP and port
		grant_dictionary[my_agent_ID]["IP"] = int_ip
		grant_dictionary[my_agent_ID]["PORT"] = int_port

	# Check if fs_path is not empty
	if fs_path=='':
		fs_path = poject_path + os.sep + "distributed"
		print("Path to distributed filesystem was not set in the agent, default will be used: ", fs_path)

	agent_X_grant_file_path = project_path + os.sep + "distributed" + os.sep + "agents_grant" + os.sep + my_agent_ID+"_grant.json"
	agents_grant_file_path = project_path + os.sep + "distributed" + os.sep + "agents_grant.json"
	cloudbookjson_file_path = fs_path + os.sep + "cloudbook.json"
	hot_redeploy_file_path = fs_path + os.sep + "HOT_REDEPLOY"
	cold_redeploy_file_path = fs_path + os.sep + "COLD_REDEPLOY"

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
	def read_cloudbook_file(dict_only=False):
		global cloudbook_dict_agents
		global all_dus
		global du_list
		cloudbook_dict_agents = loader.load_dictionary(cloudbookjson_file_path)
		#print("cloudbook.json has been read.\n cloudbook_dict_agents = ", cloudbook_dict_agents)
		if not dict_only:
			du_list = loader.load_cloudbook_agent_dus(my_agent_ID, cloudbook_dict_agents)

			# Get all dus
			all_dus = []
			for i in cloudbook_dict_agents:
				all_dus.append(i)

	# # Internal function to import the DUs in the agent
	# def import_DUs_into_agent():
	# 	global du_list

	# 	# Load the DUs that belong to this agent.
	# 	du_list = loader.load_cloudbook_agent_dus(my_agent_ID, cloudbook_dict_agents)
	# 	print("My du_list: ", du_list)

	# 	sys.path.append(fs_path)
	# 	'''for du in du_list:
	# 		exec ("from du_files import "+du)
	# 		exec(du+".invoker=outgoing_invoke")'''

	# 	du_files_path = fs_path + os.sep + "du_files"
	# 	UNIX_du_files_path = du_files_path.replace(os.sep, "/")
	# 	for du in du_list:
	# 		print(du)
	# 		du_i_file_path = du_files_path + os.sep + du+".py"
	# 		while not os.path.exists(du_i_file_path):
	# 			time.sleep(0.1)
	# 		##OJO CON ESTO QUE HAY QUE PROBARLO BIEN BIEN
	# 		exec('sys.path.append('+"'"+UNIX_du_files_path+"'"+')')
	# 		# exec("from du_files import "+du)
	# 		globals()[du] = __import__(du, fromlist=["du_files"])
	# 		globals()[du+'.invoker'] = outgoing_invoke
	# 		#exec(du+".invoker=outgoing_invoke")# read file
	# 		print(du+" charged")
			
			# exec('sys.path.append('+"'"+UNIX_du_files_path+"'"+')')
			# print('sys.path.append('+"'"+UNIX_du_files_path+"'"+')')
			# exec("from du_files import "+du)
			# print("from du_files import "+du)
			# exec(du+".invoker=outgoing_invoke")# read file
			# print(du+".invoker=outgoing_invoke")# read file
			# print(du+" charged")

	# Deletes the previously imported DUs from the agent (if there was any)
	# def delete_imported_DUs_from_agent():
	# 	sys.path.append(fs_path)
	# 	'''for du in du_list:
	# 		exec ("from du_files import "+du)
	# 		exec(du+".invoker=outgoing_invoke")'''

	# 	du_files_path = fs_path + os.sep + "du_files"
	# 	UNIX_du_files_path = du_files_path.replace(os.sep, "/")
	# 	for du in du_list:
	# 		print(du)
	# 		du_i_file_path = du_files_path + os.sep + du+".py"
	# 		while not os.path.exists(du_i_file_path):
	# 			time.sleep(0.1)
	# 		##OJO CON ESTO QUE HAY QUE PROBARLO BIEN BIEN
			
	# 		exec('sys.path.append('+"'"+UNIX_du_files_path+"'"+')')
	# 		exec("from du_files import "+du)
	# 		exec(du+".invoker=outgoing_invoke")# read file
	# 		print(du+" charged")

	# Internal funciton to check if there are any redeployment files
	def find_redeploy_files():
		hot_redeploy = False
		cold_redeploy = False
		if os.path.exists(hot_redeploy_file_path):
			print("HOT_REDEPLOY file found.")
			hot_redeploy = True
		if os.path.exists(cold_redeploy_file_path):
			print("COLD_REDEPLOY file found.")
			cold_redeploy = True
		return (hot_redeploy, cold_redeploy)

	# # Internal funciton to check if there are any redeployment files
	# def find_redeploy_files():
	# 	hot_redeploy = False
	# 	cold_redeploy = False
	# 	if os.path.exists(hot_redeploy_file_path):
	# 		print(my_agent_ID, ": HOT_REDEPLOY file found.")
	# 		hot_redeploy = True


	# Load the DUs that belong to this agent.
	while not du_list:
		try:
			write_agent_X_grant_file()
			while not os.path.exists(agents_grant_file_path) or not os.path.exists(cloudbookjson_file_path) or os.stat(cloudbookjson_file_path).st_size==0:
				print("Waiting for agents_grant.json and cloudbook.json")
				if not os.path.exists(agent_X_grant_file_path):
					print("My grant file was deleted! Creating again...")
					write_agent_X_grant_file()
				time.sleep(1)
			read_agents_grant_file()
			read_cloudbook_file()
			time.sleep(1)
		except:
			print(ERR_READ_WRITE)
			time.sleep(1)

	print("My du_list: ", du_list)

	sys.path.append(fs_path)
	'''for du in du_list:
		exec ("from du_files import "+du)
		exec(du+".invoker=outgoing_invoke")'''

	du_files_path = fs_path + os.sep + "du_files"
	UNIX_du_files_path = du_files_path.replace(os.sep, "/")
	for du in du_list:
		print(du)
		du_i_file_path = du_files_path + os.sep + du+".py"
		while not os.path.exists(du_i_file_path):
			time.sleep(0.1)
		##OJO CON ESTO QUE HAY QUE PROBARLO BIEN BIEN
		#exec('sys.path.append('+"'"+UNIX_du_files_path+"'"+')')
		exec("from du_files import "+du)
		# globals()[du] = __import__(du, fromlist=["du_files"])
		# globals()[du+'invoker'] = outgoing_invoke
		exec(du+".invoker=outgoing_invoke")# read file
		print(du+" charged")
	
	dus_loaded = True
	cloudbook_version += 1

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

			# Update dictionary with new data (grant)
			if grant!= None:
				grant_dictionary[my_agent_ID]["GRANT"] = grant
				#print('Grant dict updated')

			# Update also IP/port ??? --> call get_ip_info() again and update if necessary
			#grant_dictionary[my_agent_ID]["IP"] = ip
			#grant_dictionary[my_agent_ID]["PORT"] = port

			# Write dictionary in "agent_X_grant.json" and read dictionary from "agents_grant.json"
			write_agent_X_grant_file()
			(hot_redeploy, cold_redeploy) = find_redeploy_files()
			if hot_redeploy:
				read_agents_grant_file()
				read_cloudbook_file(dict_only=True)
				cloudbook_version += 1
				# ! - IMPROVEMENT: Check if the agent only has loaded the du_default and load more in hot redeploy???
			if cold_redeploy:
				dus_loaded = False
				# Cleaning of loaded DUs
				for du in du_list:
					print(my_agent_ID + ": deleting " + du)
					exec("del " + du)

				read_agents_grant_file()
				read_cloudbook_file()
					
				for du in du_list:
					print(du)
					du_i_file_path = du_files_path + os.sep + du+".py"
					while not os.path.exists(du_i_file_path):
						time.sleep(0.1)
					exec("from du_files import "+du)
					exec(du+".invoker=outgoing_invoke")# read file
					print(du+" charged")
				dus_loaded = True
				cloudbook_version += 1
				print("My du_list: ", du_list)

			grant = None

		# Wait 1 second to look for more data in the queue
		time.sleep(1)

	##############################################################################################################
	##############################################################################################################
	##############################################################################################################


	# # LOAD DEPLOYABLE UNITS
	# print("Loading deployable units for agent " + my_agent_ID + "...")
	# #cloudbook_dict_agents = loader.load_cloudbook_agents()

	# # It will only contain info about agent_id : du_assigned (not IP)
	# # Output file from DEPLOYER
	# # It is necessary to wait until cloudbook.json exists
	# cloudbookjson_file_path = fs_path + os.sep + "cloudbook.json"
	# while not os.path.exists(cloudbookjson_file_path):
	# 	time.sleep(0.1)
	# while(os.stat(cloudbookjson_file_path).st_size==0):
	# 	continue

	# # Check file format
	# cloudbook_dict_agents = loader.load_cloudbook(cloudbookjson_file_path)
	
	# # Load the DUs that belong to this agent.
	# du_list = loader.load_cloudbook_agent_dus(my_agent_ID, cloudbook_dict_agents)
	# print("My du_list: ", du_list)

	# # Get all dus
	# for i in cloudbook_dict_agents:
	# 	all_dus.append(i)

	# sys.path.append(fs_path)
	# '''for du in du_list:
	# 	exec ("from du_files import "+du)
	# 	exec(du+".invoker=outgoing_invoke")'''

	# du_files_path = fs_path + os.sep + "du_files"
	# UNIX_du_files_path = du_files_path.replace(os.sep, "/")
	# for du in du_list:
	# 	print(du)
	# 	du_i_file_path = du_files_path + os.sep + du+".py"
	# 	while not os.path.exists(du_i_file_path):
	# 		time.sleep(0.1)
	# 	##OJO CON ESTO QUE HAY QUE PROBARLO BIEN BIEN
		
	# 	exec('sys.path.append('+"'"+UNIX_du_files_path+"'"+')')
	# 	exec ("from du_files import "+du)
	# 	exec(du+".invoker=outgoing_invoke")# read file
	# 	print(du+" charged")

	# Set up the logger
	log = logging.getLogger('werkzeug')
	log.setLevel(logging.ERROR)

	print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")