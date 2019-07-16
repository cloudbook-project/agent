from pynat import get_ip_info #requires pip3 install pynat
import urllib.request, json, time, socket, platform, os, loader #requires pip3 install urllib

# agents_ip contains a list of the external IPs that this agent knows.
agents_ip = {}

#Caché including relation between agents and IPs
def getAgentsCache(configuration = None):
    return agents_ip

#This function is very important.
#It announces the IP address of the agent and writes it in the local_ip_info.json to be consulted by the rest of the agents.
def announceAgent(my_circle_ID, my_agent_ID, port, configuration = None):
    
    if(platform.system()=="Windows"):
        fs= os.environ['HOMEDRIVE'] + os.environ['HOMEPATH']+"/cloudbook"
        if not os.path.exists(fs):
            os.makedirs(fs)
    else:
        fs = "/etc/cloudbook"
        if not os.path.exists(fs):
            os.makedirs(fs)
	#load config file
    config_dict=loader.load_dictionary(fs+"/config/config_"+my_agent_ID+".json")
    path = config_dict["DISTRIBUTED_FS"]
    
    #while(True):
        # Getting local IP
    print("Announce Agent: ", my_agent_ID)
    internal_ip = get_local_ip()
    print(path+"/local_IP_info.json")
    #Checking if file is empty, if so, write the IP directly.
    if not os.path.exists(path+"/local_IP_info.json"):
        fo = open(path+"/local_IP_info.json", 'w')
        fo.close()
    if (os.stat(path+"/local_IP_info.json").st_size==0):
        fo = open(path+"/local_IP_info.json", 'w')
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
        fr = open(path+"/local_IP_info.json", 'r')
        directory = json.load(fr)
        if my_agent_ID in directory:
            directory[my_agent_ID]["IP"]=internal_ip+":"+str(port)
            fo = open(path+"/local_IP_info.json", 'w')
            directory= json.dumps(directory)
            fo.write(directory)
            fo.close()
            #continue
    # if agent not already written, we append it.
        fr = open(path+"/local_IP_info.json", 'r')
        directory = json.load(fr)
        directory[my_agent_ID]={}
        directory[my_agent_ID]["IP"]=internal_ip+":"+str(port)
        fo = open(path+"/local_IP_info.json", 'w')
        directory= json.dumps(directory)
        fo.write(directory)
        fo.close()
    #    continue
    #time.sleep(300)


#Get IP from a certain agent. It will be saved in a local variable.
#It is used to call remote dus by the remote_invoke()
def getAgentIP(my_agent_id, agent_id, configuration = None):
    #Check file "local_IP_info" and get agent_id
    if(platform.system()=="Windows"):
        fs= os.environ['HOMEDRIVE'] + os.environ['HOMEPATH']+"/cloudbook"
        if not os.path.exists(fs):
            os.makedirs(fs)
    else:
        fs = "/etc/cloudbook"
        if not os.path.exists(fs):
            os.makedirs(fs)
	#load config file
    config_dict=loader.load_dictionary(fs+"/config/config_"+my_agent_id+".json")
    path = config_dict["DISTRIBUTED_FS"]
    with open(path+'/local_IP_info.json', 'r') as file:
        data = json.load(file)
        #agents_ip[agent_id]={}
        #agents_ip[agent_id]=data[agent_id]
        return data[agent_id]

        

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
			