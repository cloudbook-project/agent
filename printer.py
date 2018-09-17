
import requests # this import requires pip install requests
import loader
import sys

if __name__ == "__main__":

	cloudbook_dict_agents = loader.load_dictionary('./du_files/cloudbook_agents.json')
	host_du0 =cloudbook_dict_agents.get("agent_0").keys()[0]
	"""
	try :
		#text=raw_input()
	except:
		print "--"
	"""
	
	#with open(sys.stdin, 'r') as file:

	#for line in sys.stdin:
	while True	:
		print "hola"
		text= raw_input()
		#text=line#file.readline()
		print text
		url='http://'+host_du0+"/invoke?invoked_function=du_0.cloudbook_print('"+text+"')"
		#url='http://'+host_du0+'/invoke?invoked_function=du_0.cloudbook_print("hola")'
		print url
		r = requests.get(url)
		#print "request lanzada", url
		#print r.text
		
		
			
