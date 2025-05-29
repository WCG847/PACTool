from mmap import mmap
from struct import unpack, pack

class CFile:
	m_nSector = bytearray(512)
	m_CashEnt = bytearray(10240)
	m_FilePos = bytearray(16)
	m_HeadBuf = bytearray(65536)

