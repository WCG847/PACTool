import struct as s


class CData:
	def __init__(self, _ct):
		self.PAC = open(_ct, "rb")
		self.ECount = None
		self.Size = None
		self.ID = None
		self.RVA = None
		self.Data_TBL = None
		self.FileEntries = []

	def _dt(self):
		self.PAC.close()
		self.PAC = None

	def __del__(self):
		self._dt()

	def SetAdr(self):
		Magic = 0x20434150  # "PAC "
		ActualMagic = s.unpack("<I", self.PAC.read(4))[0]
		if ActualMagic != Magic:
			return
		self.ECount = s.unpack("<I", self.PAC.read(4))[0]
		self.Data_TBL = (self.ECount << 3) + 8

	def Search(self):
		for i in range(self.ECount):
			self.ID = s.unpack("<H", self.PAC.read(2))[0]
			self.RVA = s.unpack("<H", self.PAC.read(2))[0]
			self.Size = s.unpack("<I", self.PAC.read(4))[0]
			self.FileEntries.append({"ID": self.ID, "RVA": self.RVA, "Size": self.Size})

	def GetData(self):
		self.PAC.seek(self.Data_TBL)
		for entry in self.FileEntries:
			self.PAC.seek(entry["RVA"])
			entry["Data"] = self.PAC.read(entry["Size"])

		return self.FileEntries