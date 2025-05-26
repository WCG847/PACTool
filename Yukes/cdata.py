from struct import unpack
from cfile import CFile

DPAC = CFile()

class CData:
	def __init__(self, file):
		if file is None:
			self.file = DPAC.CacheRead()
		self.file = file

		self.SetAdr()

	def SetAdr(self):
		HEADER = 0x20434150
		GOT = unpack('<I', self.file.read(4))[0]
		if HEADER != GOT:
			return False
		return

	def GetExSize(self):

