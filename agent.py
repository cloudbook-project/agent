from flask import Flask
from flask import request
from flask import jsonify
import json
from flask import abort, redirect, url_for
import importer
import os

application = Flask(__name__)

@application.route("/", methods=['GET', 'PUT', 'POST'])
def hello():
	print "hello world"
	return  "Hello"

@application.route("/invoke", methods=['GET','POST'])
def invoke():
	#Lo que llega es un json
	#miramos el campo nombre de funcion, nombre del modulo de funcion, si existe en la du_list, la invocamos
	#y si no, hay que invocar al agente que la contenga, consultando el cloudbook
	#llamando al modulo invoker.py
	
	# example of invocation
	# http://localhost:3000/invoke?invoked_function=compute(56,77,5)
	invoked_function=request.args.get('invoked_function')

	# check if invoked function belongs to this agent, otherwise will re-invoke to the right agent
	# PENDIENTE DE PROGRAMAR

	print "invoked_function = "+invoked_function
	#supongamos que procesamos el post y llega esto
	# invoked_function="main()"
	#os.chdir('./du_files')
	#exec("import du_0")
	#return eval("du_0."+invoked_function)
	#return eval("du_0."+"main("+"cosa"+")")
	a= eval("du_0."+"main()")
	print "funcion terminada ok"
	print a
	return a

def cosa(k):
	print k
	return "cloudbook"




if __name__ == "__main__":
	du_list = []
	du_list = importer.load_cloudbook()
	importer.import_dus(du_list)

	du_list=["du_0"] # fake
	
	j = du_list[0].rfind('_')+1
	num_du = du_list[0][j:]
	# num_du is the initial DU and will be used as offset for listen port
	print num_du
	#os.chdir("./du_files")
	#exec("import du_0")
	# du_files is the distributed directory containing all DU files
	for du in du_list:
		exec ("from du_files import "+du)

	du_0.invoker=cosa
	print "hola"
	du_0.main()
	application.run(debug=True, host='0.0.0.0', port = 3000+int(num_du))
