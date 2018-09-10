import threading

invoker=None

def f0():
	invoker('du_1.f1()')
	f3()


	return 'cloudbook' 

def f3():
	print "dir2.file3.f3: Hello world"


	return 'cloudbook' 

def main():
	f0()
	return "cloudbook"

if __name__ == '__main__':
	f0()
			