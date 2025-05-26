from curses import nocbreak
from struct import unpack, pack
from mmap import mmap
from enum import Enum

class CFile:
	class eDevice(Enum):
		HOST = 0
		CD = 1

	def Start(self, device=eDevice.HOST):
		self.mem = mmap(-1, 4096)
		i = 0
		j = 0
		while i < 512:
			self.mem.seek(j)
			i += 8
			for _ in range(0x14, 0xF5, 0x20):
				self.mem.write(pack('I', 7))
				j += 256
				if i < 512:
					continue
				else:
					return self.mem


