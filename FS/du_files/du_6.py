import math
import time
import json
from random import randint
import threading

invoker=None

def f6(N):
#Automated code for global var:
 #fun_name: creaLista final fun name: f6 globalName: body_list destiny du: 1 global_fun_name: f1
#============================global vars automatic code=========================
	#body_list
	if not hasattr(f6, "body_list"):
		f6.body_list = None

	if not hasattr(f6, "ver_body_list"):
		f6.ver_body_list = 0
        
	aux_body_list,aux_ver = invoker(['du_1'],'f1',"'None',"+str(f6.ver_body_list))
	if aux_body_list != "None":
		f6.body_list = aux_body_list
	body_list=f6.body_list
	f6.ver_body_list= aux_ver
	ver_body_list= f6.ver_body_list
		#	global body_list#Aqui va el chorrazo de codigo
	X_MAX = 100
	Y_MAX = 100
	VX_MAX = 10
	VY_MAX = 10
	print("Construyendo la lista...")
	for i in range(N):	
		m = 10 #mass
		x = randint(-X_MAX,X_MAX)
		y = randint(-Y_MAX,Y_MAX)
		vx = randint(-VX_MAX,VX_MAX)
		vy = randint(-VY_MAX,VY_MAX)
		invoker(['du_1'], 'f1','"f1.body_list.append('+str((m,x,y,vx,vy))+')"'+' , '+str(ver_body_list))


	return json.dumps('cloudbook: done') 

def f4(single_body, iteration):
	threadf4 = threading.Thread(target= parallel_f4, daemon = False, args = (single_body, iteration))
	threadf4.start()
	return json.dumps("thread launched")

def parallel_f4(single_body, iteration):
#Automated code for global var:
 #fun_name: compute_body final fun name: parallel_f4 globalName: body_list destiny du: 1 global_fun_name: f1
#============================global vars automatic code=========================
	#body_list
	if not hasattr(parallel_f4, "body_list"):
		parallel_f4.body_list = None

	if not hasattr(parallel_f4, "ver_body_list"):
		parallel_f4.ver_body_list = 0
        
	aux_body_list,aux_ver = invoker(['du_1'],'f1',"'None',"+str(parallel_f4.ver_body_list))
	if aux_body_list != "None":
		parallel_f4.body_list = aux_body_list
	body_list=parallel_f4.body_list
	parallel_f4.ver_body_list= aux_ver
	ver_body_list= parallel_f4.ver_body_list
		#	global body_list#Aqui va el chorrazo de codigo
#Automated code for global var:
 #fun_name: compute_body final fun name: parallel_f4 globalName: body_new destiny du: 0 global_fun_name: f2
#============================global vars automatic code=========================
	#body_new
	if not hasattr(parallel_f4, "body_new"):
		parallel_f4.body_new = None

	if not hasattr(parallel_f4, "ver_body_new"):
		parallel_f4.ver_body_new = 0
        
	aux_body_new,aux_ver = invoker(['du_0'],'f2',"'None',"+str(parallel_f4.ver_body_new))
	if aux_body_new != "None":
		parallel_f4.body_new = aux_body_new
	body_new=parallel_f4.body_new
	parallel_f4.ver_body_new= aux_ver
	ver_body_new= parallel_f4.ver_body_new
		#	global body_new#Aqui va el chorrazo de codigo
	
	fx=0.0
	fy=0.0
	for i in body_list:
		#print("i",i)
		delta_f = invoker(['du_0'], 'f5',str(single_body)+','+ str(i))
		fx = fx+delta_f[0]
		fy = fy+delta_f[1]
	ax = fx/float(single_body[0])
	ay = fy/float(single_body[0])
	vx = float(single_body[3])+ax
	vy = float(single_body[4])+ay
	x = float(single_body[1])+vx
	y = float(single_body[2])+vy	
	
	new_single_body = (single_body[0],x,y,vx,vy)
	invoker(['du_0'], 'f2','"f2.body_new.append('+str(new_single_body)+')"'+' , '+str(ver_body_new))
	#print("Exit from computebody")


	return json.dumps('cloudbook: done') 

