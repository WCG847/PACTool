from struct import unpack
from mmap import mmap
from CData import CData

class CTim2:
	def __init__(self, mem):
		self.mem = mem

	def Read(self, PAC):
		self.PAC = CData(PAC)

