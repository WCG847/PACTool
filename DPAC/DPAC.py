import struct
from DPAC.DPACExceptions import *
import traceback


class DPAC:
    def __init__(self, file_path):
        self.file_path = file_path
        self.magic_header = "DPAC"
        self.toc_count = 0
        self.raw_file_size = 0
        self.sector_size = 0
        self.toc = []
        self.toc_start = 0x800  # PAC_TOC sector start offset
        self.toc_end = 0x4000  # PAC_TOC sector end offset
        self.data_offset = 0x4000  # PAC_DATA sector start offset

    def read_uint32(self, file):
        value = struct.unpack("<I", file.read(4))[0]
        print(f"Read UINT32: 0x{value:X} at position: 0x{file.tell() - 4:X}")
        return value


    def read_uint16(self, file):
        """Reads a 2-byte unsigned integer from the file."""
        return struct.unpack("<H", file.read(2))[0]

    def read_raw_bytes(self, file, num_bytes):
        """Reads raw bytes from the file."""
        return file.read(num_bytes)

    def resolve_pointer(self, raw_pointer):
        """Resolves a folder or file pointer."""
        try:
            if raw_pointer == 0:  # Special case for 0x0, which points to 0x4000
                resolved_pointer = self.data_offset
            else:
                resolved_pointer = (
                    raw_pointer << 0x0B
                ) + self.data_offset  # Add PAC_DATA base offset

            # Debug: Log pointer resolution
            print(
                f"Resolving Pointer - Raw: 0x{raw_pointer:X}, Resolved: 0x{resolved_pointer:X}"
            )
            return resolved_pointer
        except Exception as e:
            raise FileSizeResolutionError(f"Failed to resolve pointer: {e}")

    def resolve_file_size(self, raw_size):
        """Resolves the raw file size."""
        try:
            return raw_size << 0x08  # Left shift by 8 bits
        except Exception as e:
            raise FileSizeResolutionError(f"Failed to resolve file size: {e}")

    def parse_header(self, file):
        """Parses the DPAC header."""
        file.seek(0)
        header = file.read(4).decode("latin-1")
        if header != self.magic_header:
            raise InvalidDPACFileError("Illegal Header.")

        # Read the raw TOC count once
        raw_toc_count = self.read_uint32(file)
        print(f"Raw TOC Count: 0x{raw_toc_count:X}")

        # Calculate small and big TOC counts from the same raw value
        self.toc_count = raw_toc_count >> 3
        self.big_toc_count = (raw_toc_count >> 2) - 6 if self.toc_count > 12 else self.toc_count

        # Debugging output to trace logic
        print(f"TOC Count: {self.toc_count}, Big TOC Count: {self.big_toc_count}")

        # Handle invalid cases
        if self.big_toc_count > 0xFFFF:  # Sanity check on big TOC count
            raise ValueError(f"Invalid Big TOC Count: {self.big_toc_count}")
        if self.toc_count <= 0:
            raise ZeroTOCCountError("TOC count is zero. No files or folders in the DPAC.")

        # Continue reading file size and sector size
        self.raw_file_size = self.read_uint32(file)
        self.sector_size = self.read_uint32(file)
        print(f"Raw File Size: {self.raw_file_size}, Sector Size: {self.sector_size}")

    def parse_toc(self, file):
        try:
            file.seek(self.toc_start)
            total_listings = 0  # Track total folder + file blocks parsed
            toc_limit = self.big_toc_count if self.toc_count > 12 else self.toc_count

            print(f"TOC Start: 0x{self.toc_start:X}, TOC End: 0x{self.toc_end:X}, TOC Limit: {toc_limit}")

            while file.tell() < self.toc_end and total_listings < toc_limit:
                current_offset = file.tell()

                # Parse folder block
                folder_name = file.read(4).decode("latin-1").rstrip("\x00")
                pac_file_in_folder_count = self.read_uint16(file)
                pac_folder_pointer = self.read_uint16(file)

                # Mask the file count and check numerical ID flag
                file_count = pac_file_in_folder_count & 0x7FFF
                use_numerical_ids = (pac_file_in_folder_count & 0x8000) != 0

                # Debug: Log folder info
                print(f"Parsing folder '{folder_name}' at offset 0x{current_offset:X}: file_count={file_count}, use_numerical_ids={use_numerical_ids}")

                if not folder_name.strip() and pac_folder_pointer == 0:
                    print(f"Stopping parsing: Empty folder block or padding at offset 0x{current_offset:X}")
                    break

                folder_pointer = self.resolve_pointer(pac_folder_pointer)
                if folder_pointer < self.data_offset or folder_pointer >= self.raw_file_size:
                    print(f"Skipping folder with invalid pointer at offset 0x{current_offset:X}")
                    continue

                folder = {
                    "folder_name": folder_name,
                    "file_count": file_count,
                    "folder_pointer": folder_pointer,
                    "files": [],
                }

                current_pointer = folder_pointer
                for _ in range(file_count):
                    if file.tell() >= self.toc_end or total_listings >= toc_limit:
                        print(f"Stopping parsing: Reached TOC limit at offset 0x{file.tell():X}")
                        break

                    if use_numerical_ids:
                        file_id_raw = self.read_raw_bytes(file, 2)
                        raw_size = self.read_uint16(file)

                        file_id = file_id_raw[::-1].hex().upper()
                        file_size = self.resolve_file_size(raw_size)

                        print(f"Numerical ID File Parsed - ID: {file_id}, Size: {file_size}")

                        folder["files"].append({
                            "file_name": file_id,
                            "file_pointer": current_pointer,
                            "file_size": file_size,
                        })

                        current_pointer += file_size
                        total_listings += 1
                    else:
                        file_name = file.read(4).decode("latin-1").rstrip("\x00")
                        raw_pointer = self.read_uint16(file)
                        raw_size = self.read_uint16(file)

                        if raw_pointer == 0 and raw_size == 0:
                            print(f"Skipping invalid file block at offset 0x{file.tell():X}")
                            continue

                        file_pointer = self.resolve_pointer(raw_pointer)
                        file_size = self.resolve_file_size(raw_size)

                        print(f"File Parsed - Name: {file_name}, Pointer: 0x{file_pointer:X}, Size: {file_size}")

                        folder["files"].append({
                            "file_name": file_name,
                            "file_pointer": file_pointer,
                            "file_size": file_size,
                        })

                        current_pointer += file_size
                        total_listings += 1

                if folder["file_count"] > 0:
                    self.toc.append(folder)

            if file.tell() >= self.toc_end:
                print(f"Parsing stopped correctly at TOC boundary 0x{self.toc_end:X}")

        except Exception as e:
            raise TOCParseError(f"Failed to parse TOC: {e}")

    def create_new_dpac(self, output_path, folder_structure):
        """
        Creates a new DPAC file at the given path.

        :param output_path: Path to the new DPAC file.
        :param folder_structure: List of folders, each containing a dict with folder name, file count, and file data.
        """
        try:
            with open(output_path, "wb") as dpac_file:
                # 1. Write the header
                self._write_header(dpac_file, folder_structure)
                print("Header written successfully.")

                # 2. Write the TOC
                toc_entries, folder_pointers = self._write_toc(dpac_file, folder_structure)
                print("TOC written successfully.")

                # 3. Write file data
                total_written_size = self._write_file_data(dpac_file, folder_structure, folder_pointers)
                print("File data written successfully.")

                # 4. Finalize the DPAC by updating total file length
                self._finalize_file(dpac_file, total_written_size)

        except Exception as e:
            print(f"Error in create_new_dpac: {e}")
            traceback.print_exc()
            raise

    def validate_folder_structure(folder_structure):
        """
        Validates the folder structure to ensure it conforms to expected format.
        """
        for folder in folder_structure:
            if "folder_name" not in folder or "files" not in folder:
                raise ValueError(f"Invalid folder structure: {folder}")
            if len(folder["folder_name"]) > 4:
                raise ValueError(
                    f"Folder name '{folder['folder_name']}' exceeds 4 characters."
                )
            for file in folder["files"]:
                if "file_name" not in file or "file_data" not in file:
                    raise ValueError(
                        f"Invalid file structure in folder '{folder['folder_name']}': {file}"
                    )
                if len(file["file_name"]) > 4:
                    raise ValueError(
                        f"File name '{file['file_name']}' exceeds 4 characters."
                    )

    def _write_header(self, file, folder_structure):
        """
        Writes the DPAC header to the file.
        """
        try:
            file.write(self.magic_header.encode("latin-1"))  # Magic header
            toc_count = sum(len(folder["files"]) + 1 for folder in folder_structure)  # Folder entries + files
            file.write(struct.pack("<I", toc_count << 3))  # TOC count (shifted left by 3)

            # Write placeholder for file size (will update later)
            file.write(struct.pack("<I", 0))  # Placeholder for total file length (UINT32)
            file.write(struct.pack("<I", 0x00000007))  # Default sector size
        
            print(f"Header written: TOC count = {toc_count}, sector size = 0x00000007")
        except Exception as e:
            print(f"Error in _write_header: {e}")
            raise


    def _write_toc(self, file, folder_structure):
        """
        Writes the TOC to the file, including folder and file metadata.
        """
        try:
            file.seek(self.toc_start)
            folder_pointers = {}
            toc_entries = 0  # Track total number of entries written (folders + files)

            current_folder_pointer = self.toc_start
            for folder in folder_structure:
                folder_name = folder["folder_name"].ljust(4, "\x00")[:4]
                file_count = len(folder.get("files", [])) << 1  # File count shifted left

                print(f"DEBUG: Writing TOC for folder '{folder_name.strip()}': file_count={file_count}")

                # Write folder metadata
                file.write(folder_name.encode("latin-1"))  # Folder name
                file.write(struct.pack("<H", file_count))  # File count
                folder_pointer_location = file.tell()  # Track location of folder pointer
                file.write(struct.pack("<H", 0))  # Placeholder for folder pointer

                folder_pointers[folder_name.strip()] = folder_pointer_location
                current_folder_pointer += 8  # Each TOC folder entry is 8 bytes

                # Write file metadata within the folder
                for f in folder.get("files", []):
                    file_name = f["file_name"].ljust(4, "\x00")[:4]
                    raw_pointer = 0  # Placeholder for file pointer
                    raw_size = len(f["file_data"]) >> 8  # File size shifted right

                    print(f"DEBUG: Writing file '{file_name.strip()}' metadata: pointer=0x{raw_pointer:X}, size={raw_size}")

                    file.write(file_name.encode("latin-1"))  # File name
                    pointer_location = file.tell()  # Track pointer location
                    file.write(struct.pack("<H", raw_pointer))  # Placeholder for pointer
                    file.write(struct.pack("<H", raw_size))  # File size

                    # Store pointer location for update in `_write_file_data`
                    f["pointer_location"] = pointer_location
                    toc_entries += 1

            print(f"DEBUG: TOC completed with {toc_entries} entries (folders + files).")
            return toc_entries, folder_pointers
        except Exception as e:
            print(f"ERROR in _write_toc: {e}")
            traceback.print_exc()
            raise


    def _write_file_data(self, file, folder_structure, folder_pointers):
        """
        Writes file data to the PAC_DATA section and updates pointers in the TOC.
        """
        try:
            file.seek(self.data_offset)  # Ensure starting at PAC_DATA
            current_pointer = self.data_offset
            total_written_size = 0  # Track total size written to PAC file

            for folder in folder_structure:
                print(f"DEBUG: Processing folder '{folder['folder_name']}' for file data")

                # Track the first file's pointer for the folder
                folder_first_file_pointer = None

                for f in folder["files"]:
                    file_name = f["file_name"].ljust(4, "\x00")[:4]
                    file_data = f["file_data"]
                    file_size = len(file_data)

                    print(f"DEBUG: Writing file '{file_name.strip()}' data at 0x{current_pointer:X}, size={file_size}")

                    # Write the file data at the current pointer
                    file.write(file_data)
                    total_written_size += file_size

                    # Calculate the raw pointer for the file
                    if current_pointer < self.data_offset:
                        raise ValueError(f"File pointer is out of bounds: {current_pointer:X}")
                    raw_pointer = (current_pointer - self.data_offset) >> 11  # Correct bitshift for UINT16
                    if not (0 <= raw_pointer <= 0xFFFF):  # Ensure within UINT16
                        raise ValueError(f"Pointer value out of UINT16 range: {raw_pointer}")

                    f["file_pointer"] = raw_pointer  # Store resolved pointer

                    # Update the file pointer in the TOC
                    file.seek(f["pointer_location"])  # Seek to pointer location in TOC
                    file.write(struct.pack("<H", raw_pointer))  # Update pointer
                    file.seek(current_pointer + file_size)  # Return to data section

                    # Track the first file pointer for the folder
                    if folder_first_file_pointer is None:
                        folder_first_file_pointer = raw_pointer

                    # Advance current pointer
                    current_pointer += file_size

                    # Calculate padding to align to 2048 bytes
                    alignment = 2048
                    padding_needed = (alignment - (current_pointer % alignment)) % alignment

                    if padding_needed > 0:
                        file.write(b"\x00" * padding_needed)
                        total_written_size += padding_needed
                        current_pointer += padding_needed

                # Update folder pointer in TOC with the first file's pointer
                if folder_first_file_pointer is not None:
                    folder_pointer_location = folder_pointers[folder["folder_name"]]
                    file.seek(folder_pointer_location + 6)  # Seek to folder pointer field
                    file.write(struct.pack("<H", folder_first_file_pointer))  # Update folder pointer

            print("DEBUG: File data section written successfully.")
            print(f"DEBUG: Total written size: {total_written_size / (1024 * 1024):.2f} MB")
            return total_written_size
        except Exception as e:
            print(f"ERROR in _write_file_data: {e}")
            traceback.print_exc()
            raise


    def _finalize_file(self, file, total_written_size):
        """
        Finalizes the DPAC file by writing the total file length at offset 0x08.
        """
        try:
            total_length = int(total_written_size)  # Ensure the size is an integer
            file.seek(8)  # Move to offset 0x08 in the file
            file.write(struct.pack("<I", total_length))  # Write total file size as UINT32

            print(f"Finalized DPAC file size: {total_length} bytes written at offset 0x08.")
        except Exception as e:
            print(f"Error in _finalize_file: {e}")
            raise


    def _finalize_toc(self, file, folder_pointers):
        """
        Updates folder pointers in the TOC.
        """
        try:
            file.seek(self.toc_start)
            for folder_name, pointer in folder_pointers.items():
                resolved_pointer = (pointer - self.data_offset) >> 0x0B

                print(
                    f"DEBUG: Finalizing TOC for folder '{folder_name}': pointer={pointer}, resolved_pointer={resolved_pointer}"
                )

                if not (0 <= resolved_pointer <= 65535):
                    raise ValueError(
                        f"Folder pointer out of range for '{folder_name}': {resolved_pointer}"
                    )

                if pointer < self.data_offset:
                    raise ValueError(f"Invalid pointer: {pointer}")

                # Update the placeholder pointer in TOC
                folder_entry_offset = self.toc_start + (4 + 2 + 2) * list(
                    folder_pointers
                ).index(folder_name)
                file.seek(folder_entry_offset + 6)  # Skip folder name and file count
                file.write(struct.pack("<H", resolved_pointer))

            print("DEBUG: TOC finalization completed successfully.")
        except Exception as e:
            print(f"ERROR in _finalize_toc: {e}")
            raise

    def load(self):
        """Loads and parses the DPAC file."""
        with open(self.file_path, "rb") as file:
            self.parse_header(file)
            self.parse_toc(file)