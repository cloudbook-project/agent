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
	print "llamada"
	return  "Hello"

@application.route("/invoke", methods=['GET','POST'])
def invoke():
	#Lo que llega es un json
	#miramos el campo nombre de funcion, nombre del modulo de funcion, si existe en la du_list, la invocamos
	#y si no, hay que invocar al agente que la contenga, consultando el cloudbook
	#llamando al modulo invoker.py
	
	#supongamos que procesamos el post y llega esto
	invoked_function="main()"
	#os.chdir('./du_files')
	#exec("import du_0")
	return eval("du_0."+invoked_function)




if __name__ == "__main__":
	du_list = []
	du_list = importer.load_cloudbook()
	importer.import_dus(du_list)
	#os.chdir("./du_files")
	#exec("import du_0")
	exec ("from du_files import du_0")
	print "hola"
	du_0.main()
	application.run(debug=True, host='0.0.0.0', port = 3000)
