import struct
import os

class MPQ:
    def __init__(self, file_path):
        self.file_path = file_path
        self.magic_offset = 0x00
        self.toc_count_offset = 0x0C
        self.toc_offset = 0x10

    def read_file(self):
        """
        Opens and reads the binary file for processing.
        """
        try:
            with open(self.file_path, "rb") as file:
                self.data = file.read()
        except FileNotFoundError:
            raise Exception(f"File '{self.file_path}' not found.")
        except IOError:
            raise Exception(f"Failed to read file '{self.file_path}'.")

    def check_magic(self):
        """
        Checks for the magic bytes "MPQ" at offset 0x00.
        """
        magic = self.data[self.magic_offset:self.magic_offset + 3]
        if magic != b"MPQ":
            raise ValueError(f"Invalid magic bytes: {magic.decode(errors='ignore')} (Expected: 'MPQ')")

    def parse_toc(self):
        """
        Parses the Table of Contents to retrieve file pointers and assign names.
        """
        # Read MPQ_TOC_COUNT (UINT32) from offset 0x0C
        mpq_toc_count = struct.unpack_from(">I", self.data, self.toc_count_offset)[0]
        print(f"MPQ_TOC_COUNT: {mpq_toc_count}")

        # Read the TOC entries starting at offset 0x10
        toc_start = self.toc_offset
        file_pointers = []

        for i in range(mpq_toc_count):
            pointer = struct.unpack_from(">I", self.data, toc_start + (i * 4))[0]
            file_pointers.append(pointer)

        return file_pointers

    def extract_files(self, file_pointers, output_dir="extracted_files"):
        """
        Extracts files based on the file pointers and saves them with padded filenames.
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for i, pointer in enumerate(file_pointers):
            # Define the file name as a 4-character padded decimal (e.g., "0001")
            file_name = f"{i:04}.bin"
            file_path = os.path.join(output_dir, file_name)

            # Ensure the pointer is within bounds
            if pointer >= len(self.data):
                raise ValueError(f"File pointer {pointer} out of bounds for file {file_name}")

            # Determine the size of the file by checking the next pointer
            start = pointer
            if i + 1 > len(file_pointers):
                end = file_pointers[i + 1]
            else:
                end = len(self.data)  # Last file goes to the end of the data

            # Extract the file content
            file_content = self.data[start:end]

            # Write to the output file
            with open(file_path, "wb") as output_file:
                output_file.write(file_content)

            print(f"Extracted {file_name} from offset {start} to {end}")