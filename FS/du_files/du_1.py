import math
import time
import json
from random import randint
import threading

invoker=None

def f1(op, old_ver):
	if not hasattr(f1, "body_list"):
		f1.body_list=[]
	if not hasattr(f1, "ver_body_list"):
		f1.ver_body_list= 1
	if not hasattr(f1, "lock_body_list"):
		f1.lock_body_list = threading.Lock()
	if op == "None":
		if old_ver == f1.ver_body_list:
			return json.dumps(("None", old_ver))
		else:
			return json.dumps((f1.body_list,f1.ver_body_list))
	else:
		try:
			f1.ver_body_list+=1
			return json.dumps((eval(op),f1.ver_body_list))
		except:
			#with lock_body_list:
			exec(op)
			f1.ver_body_list+=1
			return json.dumps(("done",f1.ver_body_list))
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


	invoker(['du_0'], 'cloudbook_th_counter',"'--'")

	return json.dumps('cloudbook: done') 

