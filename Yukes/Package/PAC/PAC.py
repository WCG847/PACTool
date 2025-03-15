import struct as s
import decimal


def read_int24(file):
    """Read a 24-bit integer from a file and return it as an integer."""
    raw_bytes = file.read(3)  # Read 3 bytes
    if len(raw_bytes) < 3:  # Handle case where fewer than 3 bytes are read
        raise ValueError("Unexpected end of file while reading 24-bit integer.")
    return int.from_bytes(raw_bytes, byteorder="little", signed=False)


def format_size(size):
    """Convert a file size into a human-readable string."""
    if size < 0:
        return "Invalid size"

    if size < 1024:
        return f"{size} B"

    size = decimal.Decimal(size)
    units = ["KB", "MB", "GB", "TB", "PB", "EB"]

    for unit in units:
        size /= 1024
        if size < 1:
            return f"{(size * 1024):.0f} B"
        elif size < 10:
            return f"{size:.2f} {unit}"
        elif size < 100:
            return f"{size:.1f} {unit}"
        elif size < 1024:
            return f"{size:.0f} {unit}"

    return f"{size:.0f} {units[-1]}"


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
        self.FileEntries.clear()
        for i in range(self.ECount):
            ID = s.unpack("<H", self.PAC.read(2))[0]
            RVA = read_int24(self.PAC)
            Size = read_int24(self.PAC)
            ProperSize = format_size(Size)
            self.FileEntries.append({"ID": ID, "RVA": RVA, "RAWSize": Size, "FileSize": ProperSize})

    def GetData(self):
        self.PAC.seek(self.Data_TBL)
        for entry in self.FileEntries:
            actual_offset = self.Data_TBL + entry["RVA"]  # Fix: Adjust for relative addressing
            self.PAC.seek(actual_offset)  # Seek to the correct data location
            entry["Data"] = self.PAC.read(entry["RAWSize"])  # Read file contents

        return self.FileEntries
