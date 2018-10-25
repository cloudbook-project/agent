import portforwardlib
from time import sleep


# This function opens an external port for TCP traffic in the machine that executes the function.
# It will open the same port in the internal and external parts for the default private IP of the device 
# in the default NAT (router) to which is connected.
# Returns TRUE if the process is successful.
def openPort(port):

	eport=port
	iport=port
	router=None
	lanip=None
	disable=False
	protocol="TCP"
	time=0
	description="Prueba 1 de UPnP con Python"
	verbose=True
	result = portforwardlib.forwardPort(eport, iport, router, lanip, disable, protocol, time, description, verbose)
	sleep(2)
	result = portforwardlib.forwardPort(eport, iport, router, lanip, disable, protocol, time, description, verbose)

	return result


# This function closes a certain external port for TCP in the default NAT for the machine that executes the command.
# Returns TRUE if the process is succesful.
def closePort(port):

	eport=port
	iport=None
	router=None
	lanip=None
	disable=True
	protocol="TCP"
	time=None
	description="Prueba 1 de UPnP con Python"
	verbose=True
	result = portforwardlib.forwardPort(eport, iport, router, lanip, disable, protocol, time, description, verbose)
	sleep(2)
	result = portforwardlib.forwardPort(eport, iport, router, lanip, disable, protocol, time, description, verbose)

	return result