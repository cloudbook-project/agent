from flask import Flask
from flask import request
from flask import jsonify
import json
from flask import abort, redirect, url_for
import executor
import os

du_list = []

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
	return call_function(invoked_function)

@application.route("/load", methods=['GET','POST'])
def load_cloudbook():
	print "enter in load_cloudbook"
	du_list = ["du_0"]
	#aqui hay que resetear el web server para poder hacer los imports
	__main__
	#return du_list

def call_function(function):
	return eval("du_0."+function)

if __name__ == "__main__":
	for i in du_list:
		exec("from du_files import "+i)

	application.run(debug=True, host='0.0.0.0', port = 3000)
