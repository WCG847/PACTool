import os
import re
from CData import CData
from mmap import mmap
from ctim2 import CTim2

def HostRead(root_folder, rex):
	for root, dirs, files in os.walk(root_folder):
		for f in files:
			if rex.search(f):
				return os.path.join(root, f)

class CBootUpLoader:
	def Start(self):
		self.FirstDataRead()

	def FirstDataRead(self):
		ROOT = os.path.join('PAC')
		FILENAME = re.compile(r'^STARTUP\.PAC$', re.IGNORECASE)
		STARTUP = HostRead(ROOT, FILENAME)
		if STARTUP is None:
			raise ValueError(f'Not found {ROOT}{FILENAME}')
		self.PAC = CData(STARTUP)
		mem = mmap(-1, 0xA0)
		self.TIM2 = CTim2(mem)
		self.TIM2.read(self.PAC.file)


