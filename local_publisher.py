from pynat import get_ip_info #requires pip3 install pynat
import urllib.request, json, time, socket, os #requires pip3 install urllib

# agents_ip contains a list of the external IPs that this agent knows.
agents_ip = {}

def getAgentsCache(configuration = None):
    return agents_ip


def announceAgent(my_circle_ID, my_agent_ID, port, configuration = None):
    while(True):
    	# Getting local IP
    	internal_ip = get_local_ip()
    	#Checking if file is empty, if so, write the IP directly.
    	if (os.stat("./FS/local_IP_info.json").st_size==0):
            fo = open("./FS/local_IP_info.json", 'w')
            data={}
            data[my_agent_ID]={}
            data[my_agent_ID]={}
            data[my_agent_ID]["IP"]=internal_ip+":"+str(port)
            print (data)
            json_data=json.dumps(data)
            fo.write(json_data)
            fo.close()
    	# File not empty, so we open it to check if the agent has been already written on it.
    	else:
    		fr = open("./FS/local_IP_info.json", 'r')
    		directory = json.load(fr)
    		if my_agent_ID in directory:
    			directory[my_agent_ID]["IP"]=internal_ip+":"+str(port)
    			fo = open("./FS/local_IP_info.json", 'w')
    			directory= json.dumps(directory)
    			fo.write(directory)
    			fo.close()
    			continue
    	# if agent not already written, we append it.
    		fr = open("./FS/local_IP_info.json", 'r')
    		directory = json.load(fr)
    		directory[my_agent_ID]={}
    		directory[my_agent_ID]["IP"]=internal_ip+":"+str(port)
    		fo = open("./FS/local_IP_info.json", 'w')
    		directory= json.dumps(directory)
    		fo.write(directory)
    		fo.close()
    	continue
    time.sleep(300)


#Get IP from a certain agent. It will be saved in a local variable.
def getAgentIP(agent_id, configuration = None):
    #Check file "local_IP_info" and get agent_id
		with open('./FS/local_IP_info.json', 'r') as file:
			data = json.load(file)
			agents_ip[agent_id]={}
			agents_ip[agent_id]=data[agent_id]

		

#Returns real local IP address, doesn't matter how many interfaces have been set.
def get_local_ip(configuration = None):
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
			