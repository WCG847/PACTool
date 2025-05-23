from cfile import CFile
from struct import unpack, pack
from io import BytesIO

class CData(CFile):
	def __init__(self, wanted_path=r'\PAC\SE.PAC', vfsPath='/SND/BLT'):
		self.PAC = super().read(vfsPath, wanted_path)
		if self.PAC is None:
			raise ValueError("NO PAC!")
		self.SetAdr()

	def SetAdr(self):
		wantedHeader = 0x20434150
		GOTHEADER = unpack('<I', self.PAC.read(4))[0]
		if wantedHeader != GOTHEADER:
			raise ValueError("PAC IS PACKAGED WRONG")
		self.fileCount = unpack('<I', self.PAC.read(4))[0]

	def Search(self):  
		self.Entries = []  
		self.PAC.seek(8)  
		for i in range(self.fileCount):  
			gotID = unpack('<H', self.PAC.read(2))[0]  
			self.PAC.seek(2, 1)  
			size = unpack('<I', self.PAC.read(4))[0]  
			cp = self.PAC.tell()  
			TOCSize = (self.fileCount * 8) + 8 
			self.PAC.seek(TOCSize)
			if i < 1:
				POINTER = self.PAC.tell()
			else:
				POINTER = self.PAC.tell() + size
				self.PAC.seek(POINTER)

			self.Entries.append({  
				'INDEX': gotID,  
				'SIZE': size,
				'POINTER': POINTER
			})
		return self.Entries



