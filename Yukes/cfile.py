from struct import unpack, pack
from mmap import mmap
from platform import system
import os
from io import BytesIO

# Platform utility
def GetDevice():
	if system() != "Windows":
		raise EnvironmentError(f"This program cannot be run in {system()} mode")

class CFile:
	def Start(self):
		self.FileProp = mmap(-1, 65536)  # 64KB in-memory buffer
		self.fileEnt = 0
		self.writePos = 0
		self.END = 0

	def AddEnt(self, wantedPath=r'\PAC\SE.PAC', readMode=0):
		if readMode != 0:
			raise NotImplementedError("Only Read Mode 0 is supported.")

		DPAC = self.HostRead(wantedPath)
		if not DPAC:
			raise FileNotFoundError("PAC file not found.")

		DPAC.seek(4)
		SubSectorSize = unpack('<I', DPAC.read(4))[0]
		DPAC.seek(2048)
		SubSector = DPAC.read(SubSectorSize)

		self.FileProp.seek(self.writePos)
		self.FileProp.write(pack('B', 0xFF))
		self.FileProp.write(pack('B', self.fileEnt))
		self.writePos += 2

		self.FileProp.seek(self.writePos)
		self.FileProp.write(SubSector)
		self.writePos += SubSectorSize

		self.END = self.writePos
		self.FileProp.seek(self.writePos)
		self.FileProp.write(pack('<I', 0xFFFFFFFF))
		self.writePos += 4
		self.fileEnt += 1

	def Search(self, vfsPath='/SND/BLT'):
		if not hasattr(self, "END") or self.END == 0:
			raise RuntimeError("CFile structure not initialized. Call AddEnt() first.")

		Separator = '/'
		parts = vfsPath.split(Separator)
		if len(parts) != 3 or parts[0] != '' or parts[2].strip() == "":
			raise ValueError(f"Invalid vfsPath format: '{vfsPath}', expected '/XXXX/YYYY'")

		mainFolder = parts[1].ljust(4)
		File = parts[2].ljust(4)

		self.FileProp.seek(2)  # skip marker + fileEnt

		while self.FileProp.tell() < self.END:
			pos = self.FileProp.tell()
			peek = self.FileProp.read(4)
			if len(peek) < 4 or unpack('<I', peek)[0] == 0xFFFFFFFF:
				break
			self.FileProp.seek(pos)

			FolderName = self.FileProp.read(4).decode('latin1')
			print(f"At {pos:06X}: found folder '{FolderName}'")
			if FolderName != mainFolder:
				buffer = self.FileProp.read(2)
				if len(buffer) < 2:
					raise ValueError("Unexpected end while reading folder header")
				fileCount = unpack('<H', buffer)[0] & 0x0FFF
				folderSize = (fileCount << 2) + 8
				self.FileProp.seek(pos + folderSize)
				continue
			else:
				buffer = self.FileProp.read(2)
				if len(buffer) < 2:
					raise ValueError("Unexpected end while reading file count")
				fileCount = unpack('<H', buffer)[0] & 0x0FFF
				self.FileProp.seek(2, 1)
				break

		print(f"Looking for: '{File}'")
		for _ in range(fileCount):
			fileBytes = self.FileProp.read(4)
			if len(fileBytes) < 4:
				raise ValueError("Unexpected end while reading file name")

			fileName = unpack('4s', fileBytes)[0].decode('latin1').strip()
			print(f"At {self.FileProp.tell() - 4:06X}: found file '{fileName}'")
			if not fileName or not fileName.isprintable():
				self.FileProp.seek(8, 1)
				continue
			if fileName != File.strip():
				self.FileProp.seek(8, 1)
				continue
			else:
				logic = self.FileProp.read(2)
				size = self.FileProp.read(2)
				if len(logic) < 2 or len(size) < 2:
					raise ValueError("Unexpected end reading file metadata")
				logicalBase = unpack('<H', logic)[0]
				size = unpack('<H', size)[0]
				return logicalBase, size

		raise FileNotFoundError(f"{vfsPath} not found")

	def Read(self, vfsPath='/SND/BLT', wanted_path=r'\PAC\SE.PAC'):
		logicalBase, size = self.Search(vfsPath)
		resolvedSize = size << 8
		Base = (logicalBase << 11) + 0x4000
		DPAC = self.HostRead(wanted_path)
		DPAC.seek(Base)
		retrievedFile = DPAC.read(resolvedSize)
		DPAC.close()
		del DPAC
		return BytesIO(retrievedFile)

	def HostRead(self, wanted_path=r'\PAC\SE.PAC'):
		full_path = os.path.join("C:\\", wanted_path.strip("\\"))
		if os.path.exists(full_path):
			with open(full_path, "rb") as f:
				return BytesIO(f.read())
		else:
			raise FileNotFoundError(f"File not found: {full_path}")

	def ListVFS(self):
		if not hasattr(self, "END") or self.END == 0:
			raise RuntimeError("CFile structure not initialized. Call AddEnt() first.")

		vfs_paths = []
		self.FileProp.seek(2)

		while self.FileProp.tell() < self.END:
			pos = self.FileProp.tell()
			entry = self.FileProp.read(4)
			if len(entry) < 4 or unpack('<I', entry)[0] == 0xFFFFFFFF:
				break

			folderName = entry.decode('latin1', errors='ignore').strip()
			count_data = self.FileProp.read(2)
			if len(count_data) < 2:
				break
			fileCount = unpack('<H', count_data)[0] & 0x0FFF
			self.FileProp.seek(2, 1)

			for _ in range(fileCount):
				fileName = unpack('4s', self.FileProp.read(4))[0].decode('latin1', errors='ignore').strip()
				if fileName and fileName.isprintable():
					vfs_paths.append(f"/{folderName}/{fileName}")
				self.FileProp.seek(4, 1)

		return vfs_paths