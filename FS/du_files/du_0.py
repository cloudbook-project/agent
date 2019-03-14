import math
import time
import json
from random import randint
import threading

invoker=None

def f0():
	invoker(['du_6'], 'f6',str(4))
#Automated code for global var:
 #fun_name: main final fun name: f0 globalName: body_list destiny du: 1 global_fun_name: f1
#============================global vars automatic code=========================
	#body_list
	if not hasattr(f0, "body_list"):
		f0.body_list = None

	if not hasattr(f0, "ver_body_list"):
		f0.ver_body_list = 0
        
	aux_body_list,aux_ver = invoker(['du_1'],'f1',"'None',"+str(f0.ver_body_list))
	if aux_body_list != "None":
		f0.body_list = aux_body_list
	body_list=f0.body_list
	f0.ver_body_list= aux_ver
	ver_body_list= f0.ver_body_list
		#	global body_list#Aqui va el chorrazo de codigo
#Automated code for global var:
 #fun_name: main final fun name: f0 globalName: body_new destiny du: 0 global_fun_name: f2
#============================global vars automatic code=========================
	#body_new
	if not hasattr(f0, "body_new"):
		f0.body_new = None

	if not hasattr(f0, "ver_body_new"):
		f0.ver_body_new = 0
        
	aux_body_new,aux_ver = invoker(['du_0'],'f2',"'None',"+str(f0.ver_body_new))
	if aux_body_new != "None":
		f0.body_new = aux_body_new
	body_new=f0.body_new
	f0.ver_body_new= aux_ver
	ver_body_new= f0.ver_body_new
		#	global body_new#Aqui va el chorrazo de codigo
#Automated code for global var:
 #fun_name: main final fun name: f0 globalName: CONST_N destiny du: 3 global_fun_name: f3
#============================global vars automatic code=========================
	#CONST_N
	if not hasattr(f0, "CONST_N"):
		f0.CONST_N = None

	if not hasattr(f0, "ver_CONST_N"):
		f0.ver_CONST_N = 0
        
	aux_CONST_N,aux_ver = invoker(['du_3'],'f3',"'None',"+str(f0.ver_CONST_N))
	if aux_CONST_N != "None":
		f0.CONST_N = aux_CONST_N
	CONST_N=f0.CONST_N
	f0.ver_CONST_N= aux_ver
	ver_CONST_N= f0.ver_CONST_N
		#	global CONST_N#Aqui va el chorrazo de codigo
	N = CONST_N
	MAX_ITERATIONS = 10	
	#invoker(['du_6'], 'f6',str(N))
	for j in range(MAX_ITERATIONS):
		print("starting iteration", j)
		for i in body_list:
			#__NONBLOCKING__
			invoker(['du_10000'], 'f4',str(i)+','+ str(j))
		#aux = body_list
		print(body_list)
		print(body_new)
		invoker(['du_1'], 'f1','"f1.body_list%3d'+str(body_new)+' ", '+str(ver_body_list))#[0] = body_new
		f2('f2.body_new=[]', str(ver_body_new))# = []
		print("iteration ", j, " executed")

	print(body_list)
	print(body_new)

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
		delta_f = json.loads(f5(single_body,i))
		fx = fx+delta_f[0]
		fy = fy+delta_f[1]
	ax = fx/float(single_body[0])
	ay = fy/float(single_body[0])
	vx = float(single_body[3])+ax
	vy = float(single_body[4])+ay
	x = float(single_body[1])+vx
	y = float(single_body[2])+vy	
	
	new_single_body = (single_body[0],x,y,vx,vy)
	f2('f2.body_new.append('+str(new_single_body)+')', str(ver_body_new))#
	#print("Exit from computebody")


	return json.dumps('cloudbook: done') 

def f5(bodyA, bodyB):
	m1 = bodyA[0]
	x1 = bodyA[1]
	y1 = bodyA[2]
	vx1 = bodyA[3]
	vy1 = bodyA[4]
	m2 = bodyB[0]
	x2 = bodyB[1]
	y2 = bodyB[2]
	vx2 = bodyB[3]
	vy2 = bodyB[4]
	dx = math.sqrt((x1-x2)**2)
	if dx != 0:
		fx = (m1*m2)/(dx**2)
	else:
		fx=0
	if x2<x1:
		fx = -fx
	dy = math.sqrt((y1-y2)**2)
	if dy!=0:
		fy = (m1*m2)/(dy**2)
	else:
		fy=0
	if y2<y1:
		fy = -fy
	return json.dumps((fx,fy))


	return json.dumps('cloudbook: done') 

def f2(op, old_ver):
	if not hasattr(f2, "body_new"):
		f2.body_new=[]
	if not hasattr(f2, "ver_body_new"):
		f2.ver_body_new= 1
	if not hasattr(f2, "lock_body_new"):
		f2.lock_body_new = threading.Lock()
	if op == "None":
		if old_ver == f2.ver_body_new:
			return json.dumps(("None", old_ver))
		else:
			return json.dumps((f2.body_new,f2.ver_body_new))
	else:
		try:
			f2.ver_body_new+=1
			return json.dumps((eval(op),f2.ver_body_new))
		except:
			#with lock_body_new:
			exec(op)
			f2.ver_body_new+=1
			return json.dumps(("done",f2.ver_body_new))
	return json.dumps('cloudbook: done') 

def cloudbook_print(element):
	print (element)
	return "cloudbook: done"
	
def main():
	f0()
	return "cloudbook: done"

if __name__ == '__main__':
	f0()
			