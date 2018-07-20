import subprocess
import os

def load_cloudbook():
	return ["du_0"]

def import_dus(du_list):
	#enter in distributed FS
	#subprocess.call('cd ud_files', shell=True)
	#subprocess.call('dir', shell=True)
	#os.chdir('./du_files')
	#subprocess.call('dir', shell=True)
	for i in du_list:
		#exec("from du_files import "+i)
		#exec("import "+i)
		pass