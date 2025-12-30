from typing import BinaryIO
from struct import unpack

class File:
	SECTOR_SIZE = 2048
	@staticmethod
	def read(file: BinaryIO):
		thing = {}
		toc_size, data_size = unpack('<2I', file.read(8))
		file.seek(File.SECTOR_SIZE)
		toc = memoryview(file.read(toc_size))
		file.seek(File.SECTOR_SIZE * 8)
		data = memoryview(file.read(data_size))
		try:
			while True:
				folder = toc[:4]
				toc = toc[4:]
				file_count, sector = toc.cast('H')[:2]
				toc = toc[4:]
				assert not file_count & 0x8000
				if file_count > 4095:
					raise MemoryError('"File is too large for the destination file system"')
				file_count //= 2
				for i in range(file_count):
					name = toc[:4]
					toc = toc[4:]
					sector, size = toc.cast('H')[:2]
					toc = toc[4:]
					offset = sector * File.SECTOR_SIZE
					raw_size  = size * 256
					payload = data[offset:offset+raw_size]
					folder_contents: dict = thing.setdefault(folder.tobytes(), {})
					file_contents = folder_contents.setdefault(name.tobytes(), {})
					file_contents['sector'] = sector
					file_contents['size'] = size
					file_contents['payload'] = payload
		except Exception as e:
			pass
		return thing