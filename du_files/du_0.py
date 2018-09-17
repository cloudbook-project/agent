import threading

invoker=None

def f0():
	invoker('du_1.f1()')
	f3()


	return 'cloudbook: done' 

def f3():
	cloudbook_txt = "dir2.file3.f3: Hello world"

	cloudbook_print("'"+cloudbook_txt+"'")
	print "prueba"


	return 'cloudbook: done' 

def cloudbook_print(element):
	print element
	return "cloudbook: done"
	
def main():
	f0()
	return "cloudbook: done"

if __name__ == '__main__':
	f0()
			