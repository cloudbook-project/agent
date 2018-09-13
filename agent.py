from flask import Flask
from flask import request
from flask import jsonify
import json
from flask import abort, redirect, url_for
import loader
import os
import sys
import requests # this import requires pip install requests

# agent_ID of this agent. this is a global var
my_agent_ID="None"

# dictionary of dus and location
cloudbook_dict_dus={}

#dictionary of agents 
cloudbook_dict_agents={}

# list of Deployable units loaded by this agent
du_list=[]

# dictionary of config
config_dict={}


application = Flask(__name__)

@application.route("/", methods=['GET', 'PUT', 'POST'])
def hello():
	print "hello world"
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
		print "external invocation"
	else :
		print "internal invocation"

	print "invoked_function = "+invoked_function
	# check if invoked function belongs to this agent, otherwise will re-invoke to the right agent
	j=invoked_function.find(".")
	invoked_du= invoked_function[0:j]
	print "invoked_du ", invoked_du

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
		print "la funcion no pertenece a este agente"
		a = "none" #remote_invoke(invoked_du, invoked_function)

	print "function executed ok"
	print a
	return a

#def cosa(k):
#	print k
#	return "cloudbook"

#def remote_invoke(invoked_du, invoked_function):
def remote_invoke(invoked_function):
	print "ENTER in remote_invoke..."
	# get the remote du 
	j=invoked_function.find(".")
	remote_du= invoked_function[0:j]
	print "remote du = ", remote_du
    # get the possible agents to invoke
 	list_agents=cloudbook_dict_dus.get(remote_du)

    # get the machines to invoke
	remote_agent= list_agents[0] # several agents can have this remote DU. In order to test, get the first
	print "remote agent", remote_agent

	print "cloudbook_dict_agents = ", cloudbook_dict_agents

	machine_dict=cloudbook_dict_agents.get(remote_agent)

	print "machine_dict ", machine_dict

	host =machine_dict.keys()[0]
	print "el host obtenido es ", host

	#remote port
	j = remote_du.rfind('_')+1
	# num_du is the initial DU and will be used as offset for listen port
	num_remote_du = remote_du[j:]

	#host="127.0.0.1:3001"
	remote_port =3000+ int(num_remote_du)
	host = host+":"+str (remote_port)
	url='http://'+host+"/invoke?invoked_function="+invoked_function
	print url
	r = requests.get(url)
	print "request lanzada", url
	print r.text
	return r.text





if __name__ == "__main__":

	#load config file
	config_dict=loader.load_dictionary("./config.json")

	#extract args and get the agent ID
	print "Nume params: ", len(sys.argv)
	print "List of args: ", sys.argv


	i=0 # argument counter
	for arg in sys.argv:
		i=i+1
		if arg=="-agentID":
			my_agent_ID=sys.argv[i]

	print "my_agent_ID="+my_agent_ID

	#if no agent id at invocation, then use config file
	if my_agent_ID=="None":
		my_agent_ID=config_dict.get("AGENT_ID")

	print "loading deployable units for agent "+my_agent_ID+"..."
	
	

	#cloudbook_dict_agents = loader.load_cloudbook_agents()

	cloudbook_dict_agents = loader.load_dictionary('./du_files/cloudbook_agents.json')

	#cloudbook_dict_dus = loader.load_cloudbook_dus()
	cloudbook_dict_dus = loader.load_dictionary('./du_files/cloudbook_dus.json')
	du_list = loader.load_cloudbook_agent_dus("agent_"+my_agent_ID, cloudbook_dict_agents)
    

	#du_list=["du_0"] # fake
	
	j = du_list[0].rfind('_')+1
	# num_du is the initial DU and will be used as offset for listen port
	num_du = du_list[0][j:]
	
	
	#exec("import du_0")
	#du_0.invoker=cosa
	# du_files is the distributed directory containing all DU files
	for du in du_list:
		exec ("from du_files import "+du)
		#exec(du+".invoker=invoke")
		exec(du+".invoker=remote_invoke")
	#du_0.main()
	application.run(debug=True, host='0.0.0.0', port = 3000+int(num_du))
