import struct as s

class AnchorFPK:
	def __init__(self, FPK):
		self.ECount = None
		self.FileName = None
		self.FolderName = None
		self.E = []
		self.PTR = None
		self.Size = None
		self.FPK = open(FPK, 'rb')

	def SetInfo(self):
		UNK1 = s.unpack("<H", self.FPK.read(2))[0]
		UNK2 = s.unpack("<H", self.FPK.read(2))[0]
		UNK3 = s.unpack("<H", self.FPK.read(2))[0]
		UNK4 = s.unpack("<H", self.FPK.read(2))[0]

		if UNK1 != 65535:
			return
		if UNK2 != 61441:
			return
		if UNK3 != 4135:
			return
		if UNK4 != 8193:
			return

