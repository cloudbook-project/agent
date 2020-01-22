#####   IMPORTS   #####
import json



#####   FUNCTIONS   #####

# Returns the list of dus for the specified agent given the cloudbook dictionary
def load_cloudbook_agent_dus(my_agent_ID, cloudbook_dict_agents, configuration = None):
	du_list = []
	for du in cloudbook_dict_agents:
		for agent in cloudbook_dict_agents[du]:
			if agent==my_agent_ID:
				du_list.append(du)
	return du_list


# Returns a dictionary loaded from a json file
def load_dictionary(filename, configuration = None):
	with open(filename, 'r') as file:
		aux = json.load(file)
	return aux


# Writes a dictionary into a json file
def write_dictionary(data, filename, configuration = None):
	with open(filename, 'w') as file:
		json_data = json.dumps(data)
		file.write(json_data)
		file.close()
	