from struct import unpack
from io import BytesIO

def AlignTo2048(file):
	cp = file.tell()
	nextptr = (cp + 2047) &~2047
	return nextptr

def FixSize(val):
	val <<= 8
	return val

def FixOffset(val):
	val = (val << 11) + 0x4000
	return val

def ResolveIndices(file):
	val = unpack('>H', file.read(2))[0]
	ID = str(val)
	return ID

def ISOSeek(file, val):
	return file.seek(val * 2048)

def Enforce4x2(name):
	if len(name) < 4:
		raise ValueError(f'{name} is below 4')

class DirectoryPackage:
	def Load(self, path):
		with open(path, 'rb') as DPAC:
			DPAC.seek(4)
			SubSectorSize, DataSize, SectorCount = unpack('<3I', DPAC.read(12))
			ISOSeek(DPAC, 1)
			TOC = DPAC.read(SubSectorSize)
			NextSector = SectorCount + 1 # we consumed sector 0
			ISOSeek(DPAC, NextSector)
			Data = DPAC.read(DataSize)
			self.Data = BytesIO(Data)
			self.TOC = BytesIO(TOC)

	def Close(self):
		self.Data.close()
		self.TOC.close()

	def Bin2Dict(self):
		yes = len(self.TOC.getbuffer())
		self.Contents = []
		while 0 < yes:
			FolderName = unpack('4s', self.TOC.read(4))[0].decode('ascii').rstrip('\x20')
			yes -= 4
			if (var := unpack('<2B', self.TOC.read(2)))[0] == 0x80: # compare first tuple
				yes -= 2
				fileCount = (var[1]) // 2 # keep second tuple
				print(f"Folder: {FolderName}, Files: {fileCount}")
				Base = unpack('<H', self.TOC.read(2))[0]
				yes -= 2
				PTR = FixOffset(Base)
				self.Data.seek(PTR)
				Entry = []
				for i in range(fileCount):
					Index = ResolveIndices(self.TOC)
					yes -= 2
					Size = unpack('<H', self.TOC.read(2))[0]
					yes -= 2
					PTR = self.Data.tell()
					Size = FixSize(Size)
					data = self.Data.read(Size)
					data = BytesIO(data)
					Next = AlignTo2048(self.Data)
					Entry.append((Index, Size, PTR))
				self.Contents.append((FolderName, fileCount, Entry))
			else:
				self.TOC.seek(-2, 1)
				fileCount = unpack('<H', self.TOC.read(2))[0] // 2
				print(f"Folder: {FolderName}, Files: {fileCount}")

				yes -= 2
				Base = unpack('<H', self.TOC.read(2))[0]
				yes -= 2
				PTR = FixOffset(Base)
				self.Data.seek(PTR)
				Entry = []
				for i in range(fileCount):
					Name = unpack('4s', self.TOC.read(4))[0].decode('ascii').rstrip('\x20')
					yes -= 4
					Offset, Size = unpack('<2H', self.TOC.read(4))
					yes -= 4
					PTR = FixOffset(Offset)
					Size = FixSize(Size)
					self.Data.seek(PTR)
					data = self.Data.read(Size)
					Entry.append((Name, Size, PTR))
					print(f"Got {Entry}")
				self.Contents.append((FolderName, fileCount, Entry))
		return self.Contents



