from pynat import get_ip_info #requires pip3 install pynat
import urllib.request, json, time, os #requires pip3 install urllib

# agents_ip contains a list of the external IPs that this agent knows.
agents_ip = {}

def getAgentsCache(configuration = None):
    return agents_ip

#Announces agent information to the IP Publisher test
def announceAgent(my_circle_ID, my_agent_ID, configuration = None):
	while(True):
		#It uses STUN to get information about the public IP
		topology, external_ip, ext_port = get_ip_info()
		#external_ip="localhost"
		#external_port = al puerto que abramos para que corra el agent (parece que 3000+loquesea)
		#url = "http://cloudbook-ip-publisher.eu-west-1.elasticbeanstalk.com/post?circle_id="+str(my_circle_ID)+"&agent_id="+str(my_agent_ID)+"&ip_addr="+str(external_ip)
		url = "http://localhost:3100/post?circle_id="+str(my_circle_ID)+"&agent_id="+str(my_agent_ID)+"&ip_addr="+str(external_ip)#+":"+external_port
		print (url)
		try:
			urllib.request.urlopen(url)
		except:
			print ("Error connecting with IP Publisher Server")
	time.sleep(45)
		

#Get IP from a certain agent. It will be saved in a local variable.
def getAgentIP(my_circle_ID, agent_id, configuration = None):
	if agent_id in agents_ip:
		return agents_ip[agent_id]
	else:
		#url = "http://cloudbook-ip-publisher.eu-west-1.elasticbeanstalk.com/getAgentIP?circle_id="+my_circle_ID+"&agent_id="+agent_id
		url = "http://localhost:3100/getAgentIP?circle_id="+my_circle_ID+"&agent_id="+agent_id
		with urllib.request.urlopen(url) as res:
			data = json.loads(res.read().decode())
			ff = list(data.keys())[0]
			agents_ip[agent_id]={}
			agents_ip[agent_id]=ff
			return agents_ip[agent_id]
		
