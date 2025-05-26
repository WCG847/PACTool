from cfile import CFile

def InitDevice():
	mem = CFile().Start(CFile.eDevice.HOST)
	return mem