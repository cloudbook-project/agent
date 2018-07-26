import subprocess
import os

def load_cloudbook():
	du_list = ["du_0"]
	for i in du_list:
		exec("from du_files import "+i)

def import_dus(du_list):
	#enter in distributed FS
	#subprocess.call('cd ud_files', shell=True)
	#subprocess.call('dir', shell=True)
	#os.chdir('./du_files')
	#subprocess.call('dir', shell=True)
	pass
		#exec("du_0.main()")

def call_function(function):
	exec("du_0."+function)
		