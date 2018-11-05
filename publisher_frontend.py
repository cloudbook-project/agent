from pynat import get_ip_info #requires pip3 install pynat
import urllib.request, json, time, socket, os #requires pip3 install urllib

# agents_ip contains a list of the external IPs that this agent knows.
agents_ip = {}

def getAgentsCache():
    return agents_ip

#Announces agent information to the IP Publisher test
def announceAgent(my_circle_ID, my_agent_ID, local_mode):
	while(True):
		if (not local_mode):
			#It uses STUN to get information about the public IP
			topology, external_ip, ext_port = get_ip_info()
			#external_ip="localhost"
			#external_port = al puerto que abramos para que corra el agent (parece que 3000+loquesea)
			url = "http://localhost:3100/post?circle_id="+str(my_circle_ID)+"&agent_id="+str(my_agent_ID)+"&ip_addr="+str(external_ip)#+":"+external_port
			print (url)
			try:
				urllib.request.urlopen(url)
			except:
				print ("Error connecting with IP Publisher Server")
		else:
			internal_ip = get_local_ip()

			#Checking if file is empty
			if os.stat("./cloudbook/local_IP_info.json").st_size==0:
				fo = open("./cloudbook/local_IP_info.json", 'w')
				data={}
				data[my_agent_ID]={}
				data[my_agent_ID]={}
				data[my_agent_ID]["IP"]=internal_ip
				json_data=json.dumps(data)
				fo.write(json_data)	
				fo.close()
			else:
				fr = open("./cloudbook/local_IP_info.json", 'r')
				directory = json.load(fr)
				if my_agent_ID in directory:
					directory[my_agent_ID]["IP"]=internal_ip
					fo = open("./cloudbook/local_IP_info.json", 'w')
					directory= json.dumps(directory)
					fo.write(directory)
					fo.close()
					return

				fr = open("./cloudbook/local_IP_info.json", 'r')
				directory = json.load(fr)
				directory[my_agent_ID]={}
				directory[my_agent_ID]["IP"]=internal_ip
				fo = open("./cloudbook/local_IP_info.json", 'w')
				directory= json.dumps(directory)
				fo.write(directory)
				fo.close()
			return
	time.sleep(45)
		

#Get IP from a certain agent. It will be saved in a local variable.
def getAgentIP(agent_id, local_mode):
	if(not local_mode):
		if agent_id in agents_ip:
			return agents_ip[agent_id]
		else:
			url = "http://localhost:3100/getAgentIP?circle_id=AAA&agent_id="+agent_id
			with urllib.request.urlopen(url) as res:
				data = json.loads(res.read().decode())
				ff = list(data.keys())[0]
				agents_ip[agent_id]={}
				agents_ip[agent_id]=ff
				return agents_ip[agent_id]
			return
	else:
		#Check file "local_IP_info" and get agent_id
		with open('./cloudbook/local_IP_info', 'r') as file:
			data = json.load(file)
			agents_ip[agent_id]={}
			agents_ip[agent_id]=data[agent_id]

#Returns real local IP address, doesn't matter how many interfaces have been set.
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # La IP que sea, no importa
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP
			