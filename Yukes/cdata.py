from struct import unpack
from io import BytesIO
from cfile import CFile

class CData:
	PAC_MAGIC = 0x20434150  # "PAC " in little-endian

	def __init__(self, wanted_path, vfsPath=None):
		pacReader = CFile()
		pacReader.Start()

		if vfsPath:
			pacReader.AddEnt(wanted_path)
			self.PAC = pacReader.Read(vfsPath, wanted_path)
		else:
			self.PAC = pacReader.HostRead(wanted_path)

		if not self.PAC:
			raise ValueError("PAC data could not be loaded")

		self.SetAdr()

	def SetAdr(self):
		self.PAC.seek(0)
		magic_bytes = self.PAC.read(4)

		if len(magic_bytes) < 4:
			raise ValueError("File too short to be a PAC")

		gotHeader = unpack('<I', magic_bytes)[0]
		print(f"[CData] Header: {hex(gotHeader)}")

		if gotHeader != self.PAC_MAGIC:
			raise ValueError("Invalid PAC header")

		size_bytes = self.PAC.read(4)
		if len(size_bytes) < 4:
			raise ValueError("Missing PAC file count")

		self.fileCount = unpack('<I', size_bytes)[0]
		if self.fileCount > 100000:
			raise ValueError("Unrealistic file count, possible corruption")


	def ExtractEntries(self):
		self.PAC.seek(8)
		TOCSize = (self.fileCount * 8) + 8
		currentPointer = TOCSize
		self.Entries = []

		for _ in range(self.fileCount):
			gotID = unpack('<H', self.PAC.read(2))[0]
			self.PAC.seek(2, 1)  # Skip padding or unused bytes
			size = unpack('<I', self.PAC.read(4))[0]

			self.Entries.append({
				'INDEX': gotID,
				'SIZE': size,
				'POINTER': currentPointer
			})

			currentPointer += size

		return self.Entries
