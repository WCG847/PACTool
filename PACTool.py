import os
import struct
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
from PIL import Image, ImageTk

# Constants for shell32.dll icon handling
SHGFI_ICON = 0x000000100
SHGFI_SMALLICON = 0x000000001


# Struct for ctypes use with SHFILEINFO
class SHFILEINFO(ctypes.Structure):
    _fields_ = [
        ("hIcon", wintypes.HICON),
        ("iIcon", wintypes.INT),
        ("dwAttributes", wintypes.DWORD),
        ("szDisplayName", wintypes.CHAR * 260),
        ("szTypeName", wintypes.CHAR * 80),
    ]


shell32 = ctypes.windll.shell32
user32 = ctypes.windll.user32


class DPAC:
    TOC_OFFSET = 0x800
    DATA_OFFSET = 0x4000
    FOLDER_BLOCK_SIZE = 0x08
    FILE_BLOCK_SIZE = 0x08

    def __init__(self, file_path):
        self.file_path = file_path
        self.folders = []

    def load(self):
        with open(self.file_path, "rb") as file:
            if file.read(4) != b"DPAC":
                raise ValueError("Invalid magic header for DPAC")

            # Calculate actual TOC entry count
            folder_file_count = struct.unpack("<I", file.read(4))[0]
            toc_entry_count = folder_file_count >> 3
            print(
                f"Adjusted TOC entry count (folders and files combined): {toc_entry_count}"
            )

            total_file_size = struct.unpack("<I", file.read(4))[0]
            _footer_size = struct.unpack("<I", file.read(4))[0]  # Footer ignored here

            # Seek to TOC offset
            file.seek(self.TOC_OFFSET)

            entries_parsed = 0
            while entries_parsed < toc_entry_count:
                folder_name = (
                    file.read(4).decode("latin-1", errors="ignore").strip("\x00")
                )
                raw_file_count = struct.unpack("<H", file.read(2))[0]
                file_count = raw_file_count >> 1
                folder_pointer = struct.unpack("<H", file.read(2))[0]

                # Skip empty entries
                if not folder_name and file_count == 0:
                    print("Empty entry detected; skipping.")
                    entries_parsed += 1
                    continue

                print(
                    f"Parsing folder '{folder_name}' with {file_count} files (raw count: {raw_file_count}) at pointer {folder_pointer}"
                )

                folder = {"name": folder_name, "files": []}
                for file_idx in range(file_count):
                    current_pos = file.tell()
                    file_block = file.read(self.FILE_BLOCK_SIZE)
                    if len(file_block) < self.FILE_BLOCK_SIZE:
                        print(
                            f"Incomplete file block detected in folder '{folder_name}'; stopping parsing."
                        )
                        break

                    file_name = (
                        file_block[:4].decode("latin-1", errors="ignore").strip("\x00")
                    )
                    raw_file_pointer = struct.unpack("<H", file_block[4:6])[0]
                    file_pointer = (raw_file_pointer << 0x0B) + self.DATA_OFFSET
                    file_length = struct.unpack("<H", file_block[6:8])[0] << 0x08

                    if raw_file_pointer == 0 and file_length == 0:
                        print(
                            f"Detected placeholder entry in '{folder_name}'; skipping this file."
                        )
                        continue

                    print(
                        f"File: {file_name}, Pointer: {file_pointer}, Length: {file_length}"
                    )
                    file.seek(file_pointer)
                    file_data = file.read(file_length)
                    file.seek(current_pos + self.FILE_BLOCK_SIZE)

                    folder["files"].append({"name": file_name, "data": file_data})
                    entries_parsed += 1

                self.folders.append(folder)

                if entries_parsed >= toc_entry_count:
                    print(
                        f"Reached end of TOC entries: {entries_parsed}/{toc_entry_count}"
                    )
                    break


class EPAC:
    def __init__(self, file_path):
        self.file_path = file_path

    def load(self):
        print("Loading EPAC format...")


class EPK8:
    TOC_OFFSET = 0x800
    DATA_OFFSET = 0x4000
    FOLDER_BLOCK_SIZE = 0x0C
    FILE_BLOCK_SIZE = 0x10

    def __init__(self, file_path):
        self.file_path = file_path
        self.folders = []

    def load(self):
        with open(self.file_path, "rb") as file:
            if file.read(4) != b"EPK8":
                raise ValueError("Invalid magic header for EPK8")

            # Calculate actual TOC entry count
            folder_file_count = struct.unpack("<I", file.read(4))[0]
            toc_entry_count = (folder_file_count >> 4) + 1
            print(
                f"Adjusted TOC entry count (folders and files combined): {toc_entry_count}"
            )

            total_file_size = struct.unpack("<I", file.read(4))[0]
            _footer_size = struct.unpack("<I", file.read(4))[0]  # Footer ignored here

            # Seek to TOC offset
            file.seek(self.TOC_OFFSET)

            entries_parsed = 0
            while entries_parsed < toc_entry_count:
                # Read exactly 12 bytes for each folder entry
                folder_entry = file.read(self.FOLDER_BLOCK_SIZE)
                if len(folder_entry) < self.FOLDER_BLOCK_SIZE:
                    print("Incomplete folder entry detected; stopping parsing.")
                    break

                # Parse fields from the 12-byte folder entry
                folder_name = (
                    folder_entry[:4].decode("latin-1", errors="ignore").strip("\x00")
                )
                raw_file_count = struct.unpack("<H", folder_entry[4:6])[0]
                file_count = raw_file_count >> 2
                folder_pointer = struct.unpack("<H", folder_entry[6:8])[0]
                UNK1 = struct.unpack("<I", folder_entry[8:12])[0]  # 4 bytes for UNK1

                # Debug print to check values
                print(
                    f"Parsing folder '{folder_name}', file count: {file_count}, pointer: {folder_pointer}, UNK1: {UNK1}"
                )

                # Skip empty entries
                if not folder_name and file_count == 0:
                    print("Empty entry detected; skipping.")
                    entries_parsed += 1
                    continue

                folder = {"name": folder_name, "files": []}
                for file_idx in range(file_count):
                    current_pos = file.tell()
                    file_block = file.read(self.FILE_BLOCK_SIZE)
                    if len(file_block) < self.FILE_BLOCK_SIZE:
                        print(
                            f"Incomplete file block detected in folder '{folder_name}'; stopping parsing."
                        )
                        break

                    # Parse file details from the 16-byte file block
                    file_name = (
                        file_block[:8].decode("latin-1", errors="ignore").strip("\x00")
                    )
                    raw_file_pointer = struct.unpack("<I", file_block[8:12])[0]
                    file_pointer = (raw_file_pointer << 0x0B) + self.DATA_OFFSET
                    file_length = struct.unpack("<I", file_block[12:16])[0] << 0x08

                    if raw_file_pointer == 0 and file_length == 0:
                        print(
                            f"Detected placeholder entry in '{folder_name}'; skipping this file."
                        )
                        continue

                    print(
                        f"File: {file_name}, Pointer: {file_pointer}, Length: {file_length}"
                    )
                    file.seek(file_pointer)
                    file_data = file.read(file_length)
                    file.seek(current_pos + self.FILE_BLOCK_SIZE)

                    folder["files"].append({"name": file_name, "data": file_data})
                    entries_parsed += 1

                self.folders.append(folder)

                if entries_parsed >= toc_entry_count:
                    print(
                        f"Reached end of TOC entries: {entries_parsed}/{toc_entry_count}"
                    )
                    break


class DPK8:
    def __init__(self, file_path):
        self.file_path = file_path

    def load(self):
        print("Loading DPK8 format...")


class HSPC:
    def __init__(self, file_path):
        self.file_path = file_path

    def load(self):
        print("Loading HSPC format...")


class PAC:
    def __init__(self, file_path):
        self.file_path = file_path

    def load(self):
        print("Loading PAC format...")


class PACH:
    def __init__(self, file_path):
        self.file_path = file_path

    def load(self):
        print("Loading PACH format...")


class SHDC:
    def __init__(self, file_path):
        self.file_path = file_path

    def load(self):
        print("Loading SHDC format...")

class MPQ:
    TOC_OFFSET = 0x0C

    def __init__(self, file_path):
        self.file_path = file_path
        self.folders = []

    def load(self):
        with open(self.file_path, "rb") as file:
            if file.read(3) != b"MPQ":
                raise ValueError("Invalid magic header for MPQ")

            # Seek to TOC offset
            file.seek(self.TOC_OFFSET)

            entries_parsed = 0
            while entries_parsed < file_count:
                file_count = struct.unpack(">I", file.read(4))[0]


                # Skip empty entries
                if file_count == 0:
                    print("Empty entry detected; skipping.")
                    entries_parsed += 1
                    continue

                print(
                    f"{file_count} files"
                )


class PACTool:
    HEADER_MAP = {
        b"DPAC": DPAC,
        b"EPAC": EPAC,
        b"EPK8": EPK8,
        b"DPK8": DPK8,
        b"HSPC": HSPC,
        b"SHDC": SHDC,
        b"PAC ": PAC,
        b"PACH": PACH,
        b"MPQ": MPQ,
    }

    @staticmethod
    def load_file(file_path):
        with open(file_path, "rb") as file:
            magic_header = file.read(4)

        loader_class = PACTool.HEADER_MAP.get(magic_header)
        if not loader_class:
            raise ValueError("Unknown magic header: {}.".format(magic_header))

        loader = loader_class(file_path)
        loader.load()
        return loader


class PACToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PACTool")
        self.icon_cache = {}

        self.create_menu()
        self.create_treeview()
        self.create_context_menu()

    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_pac_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menu_bar)

    def create_treeview(self):
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(frame)
        self.tree.heading("#0", text="File Structure", anchor="w")
        self.tree.bind(
            "<Button-3>", self.show_context_menu
        )  # Right-click for context menu

        # Add scrollbars
        vscroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        hscroll = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)

        vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        hscroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Properties", command=self.show_properties)

    def show_context_menu(self, event):
        # Show the context menu at the mouse position
        self.context_menu.post(event.x_root, event.y_root)
        self.selected_item = self.tree.identify_row(event.y)

    def open_pac_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Yuke's Package Files", "*.pac"), ("Yuke's Package Files", "*.mpq")]
        )
        if file_path:
            for item in self.tree.get_children():
                self.tree.delete(item)

            try:
                pac_loader = PACTool.load_file(file_path)
                self.display_pac_structure(pac_loader)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load PAC file: {e}")

    def display_pac_structure(self, pac_loader):
        root_node = self.tree.insert("", "end", text="Root", open=True)
        for folder in pac_loader.folders:
            folder_name = folder.get("name", "Unknown")
            if not folder_name:
                print("Skipped empty folder entry.")
                continue

            folder_node = self.tree.insert(
                root_node, "end", text=folder_name, open=True
            )
            for file_info in folder["files"]:
                file_name = file_info.get("name", "Unnamed")
                file_node = self.tree.insert(folder_node, "end", text=file_name)
                self.add_icon(file_name, file_node)

    def add_icon(self, file_name, tree_node):
        ext = os.path.splitext(file_name)[1]

        if ext not in self.icon_cache:
            dummy_file_path = os.path.join(os.path.expanduser("~"), f"dummy{ext}")
            with open(dummy_file_path, "wb") as dummy_file:
                dummy_file.write(b"\0")

            shinfo = SHFILEINFO()
            flags = SHGFI_ICON | SHGFI_SMALLICON
            hicon = shell32.SHGetFileInfoW(
                dummy_file_path, 0, ctypes.byref(shinfo), ctypes.sizeof(shinfo), flags
            )

            if hicon:
                icon = self.convert_hicon_to_photoimage(shinfo.hIcon)
                self.icon_cache[ext] = icon
            os.remove(dummy_file_path)

        if ext in self.icon_cache:
            icon = self.icon_cache[ext]
            self.tree.item(tree_node, image=icon)

    def convert_hicon_to_photoimage(self, hicon):
        hbitmap = user32.CopyImage(hicon, 0, 0, 0, 0x00000008)  # Copy hicon as bitmap
        if hbitmap:
            bmp_info = ctypes.wintypes.BITMAPINFOHEADER()
            ctypes.windll.gdi32.GetObjectW(
                hbitmap, ctypes.sizeof(bmp_info), ctypes.byref(bmp_info)
            )
            bmp_data = ctypes.create_string_buffer(bmp_info.biSizeImage)
            ctypes.windll.gdi32.GetDIBits(
                user32.GetDC(0),
                hbitmap,
                0,
                bmp_info.biHeight,
                bmp_data,
                ctypes.byref(bmp_info),
                0,
            )
            img = Image.frombuffer(
                "RGBA",
                (bmp_info.biWidth, bmp_info.biHeight),
                bmp_data,
                "raw",
                "BGRA",
                0,
                1,
            )
            photo_image = ImageTk.PhotoImage(img)
            return photo_image

    def show_properties(self):
        item_id = self.selected_item
        if not item_id:
            return

        item_text = self.tree.item(item_id, "text")

        # Create a properties window
        properties_window = tk.Toplevel(self.root)
        properties_window.title(f"Properties - {item_text}")

        # Name (editable)
        tk.Label(properties_window, text="Name:").grid(row=0, column=0, sticky="w")
        name_entry = tk.Entry(properties_window)
        name_entry.insert(0, item_text)
        name_entry.grid(row=0, column=1, sticky="w")

        # Size (read-only)
        tk.Label(properties_window, text="Size:").grid(row=1, column=0, sticky="w")
        size_entry = tk.Entry(properties_window, state="readonly")
        size_entry.insert(0, f"{len(item_text)} bytes")
        size_entry.grid(row=1, column=1, sticky="w")

        # Buttons
        btn_frame = tk.Frame(properties_window)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="OK", command=properties_window.destroy).grid(
            row=0, column=0, padx=5
        )
        tk.Button(btn_frame, text="Cancel", command=properties_window.destroy).grid(
            row=0, column=1, padx=5
        )
        tk.Button(
            btn_frame,
            text="Apply",
            command=lambda: self.apply_properties(name_entry, item_id),
        ).grid(row=0, column=2, padx=5)

    def apply_properties(self, name_entry, item_id):
        new_name = name_entry.get()
        self.tree.item(item_id, text=new_name)


if __name__ == "__main__":
    root = tk.Tk()
    app = PACToolGUI(root)
    root.geometry("600x400")
    root.mainloop()
