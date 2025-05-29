from mmap import mmap
from struct import unpack, pack

class CFile:
	def __init__(self):
		self.Sector = bytearray(512)
		self.CacheEnt = bytearray(10240)
		self.FilePos = bytearray(16)
		self.HeadBuf = bytearray(65536)
		self.Queue = bytearray(0x4000)

	def Start(self, eDevice = 1):
		self.ReadDevice = eDevice

