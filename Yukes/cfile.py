from mmap import mmap
from struct import unpack, pack

class CFile:
	def __init__(self):
		self.Sector = bytearray(512)
		self.CacheEnt = bytearray(10240)
		self.FilePos = bytearray(16)
		self.HeadBuf = bytearray(65536)
		self.Queue = bytearray(0x4000)
		self.CurrentRequestReadID = 0xFFFFFFFF

	def Start(self, eDevice = 1):
		self.ReadDevice = eDevice
		a0 = pack('I', 7)              # Value to store
		a1 = 0                          # Loop control
		a2 = 0                          # Entry offset

		while a1 < 0x200:             
			base = a2                  
			for offset in [0x14, 0x34, 0x54, 0x74, 0x94, 0xB4, 0xD4, 0xF4]:
				dest = base + offset
				if dest + 4 <= len(self.Queue):
					self.Queue[dest:dest+4] = a0

			a1 += 0x8
			a2 += 0x100
		self.CacheMemPage = 9
		return self.CacheEnt

	def End(self):
		return