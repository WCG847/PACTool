from struct import unpack, pack
from mmap import mmap
from platform import system
import os
from io import BytesIO

def GetDevice():
	if system() != "Windows":
		print(f"This program cannot be run in {system()} mode")
		exit(0x8000FFFF)

class CFile:
	def Start(self):
		self.FileProp = mmap(-1, 4096)
		self.fileEnt = 0

	def AddEnt(self, wantedPath=r'\PAC\SE.PAC', readMode=0):
		if readMode == 0:
			DPAC = self.HostRead(wantedPath)
		else:
			raise NotImplementedError("Read Mode 1 would've activated a CDROM read. But since we are not on a ISO file, this wouldn't apply.")
		DPAC.seek(0x04)
		SubSectorSize = unpack('<I', DPAC.read(4))[0]
		self.FileProp.write(pack('B', 255)) # start cache id
		self.FileProp.write(pack('B', self.fileEnt))
		self.FileProp.seek(4)
		DPAC.seek(2048)
		SubSector = DPAC.read(SubSectorSize)
		self.FileProp.write(SubSector)
		self.fileEnt += 1
		self.FileProp.seek(SubSectorSize, 1)
		self.FileProp.write(pack('I', 0xFFFFFFFF)) # end cache id

	def Search(self, vfsPath='/SND/BLT'):
		Separator = '/'
		mainFolder = vfsPath.split(Separator)[0]
		mainFolder = mainFolder.ljust(4)

		File = vfsPath.split(Separator)[1]
		File = File.ljust(4)
		CACHESTART = 255
		CACHEEND = 0xFFFFFFFF
		self.FileProp.seek(4)
		while True:
			Yes = self.FileProp.tell()
			FolderName = unpack('4s', self.FileProp.read(4))[0].decode('ascii')
			if FolderName != mainFolder:
				fileCount = unpack('<H', self.FileProp.read(2))[0] & 0x0FFF
				folderSize = (fileCount << 2) + 8
				self.FileProp.seek(Yes)
				self.FileProp.seek(folderSize, 1)
				continue
			else:
				self.FileProp.seek(8, 1)
				fileCount <<= 2
				self.FileProp.seek(fileCount, 1)
				EOF = self.FileProp.tell()
				break
		for i in range(EOF):
			fileName = unpack('4s', self.FileProp.read(4))[0].decode('ascii')
			if fileName != File:
				self.FileProp.seek(8, 1)
				continue
			else:
				logicalBase = unpack('<H', self.FileProp.read(2))[0] + 8
				size = unpack('<H', self.FileProp.read(2))[0]
				return logicalBase, size

	def CacheRead(self, vfsPath='/SND/BLT'):
		logicalBase, size = self.Search(vfsPath)
		return size

	def Read(self, vfsPath='/SND/BLT', wanted_path=r'\PAC\SE.PAC'):
		logicalBase, size = self.Search(vfsPath)
		resolvedSize = (size << 8)
		Base = (logicalBase << 0x0B) + 0x4000
		DPAC = self.HostRead(wanted_path)
		DPAC.seek(Base)
		retrievedFile = DPAC.read(resolvedSize)
		return BytesIO(retrievedFile)


	def HostRead(self, wanted_path=r'\PAC\SE.PAC'):
		full_path = os.path.join("C:\\", wanted_path.lstrip("\\"))
		if os.path.exists(full_path):
			with open(full_path, "rb") as f:
				DPAC = f.read()
			return BytesIO(DPAC)
		else:
			print("File not found:", full_path)
			return None
		
