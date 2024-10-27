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
    _fields_ = [("hIcon", wintypes.HICON),
                ("iIcon", wintypes.INT),
                ("dwAttributes", wintypes.DWORD),
                ("szDisplayName", wintypes.CHAR * 260),
                ("szTypeName", wintypes.CHAR * 80)]

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
        with open(self.file_path, 'rb') as file:
            if file.read(4) != b'DPAC':
                raise ValueError("Invalid magic header for DPAC")

            # Read header
            folder_file_count = struct.unpack('<I', file.read(4))[0]
            total_file_size = struct.unpack('<I', file.read(4))[0]
            _footer_size = struct.unpack('<I', file.read(4))[0]  # Footer ignored here
            
            # Seek to TOC
            file.seek(self.TOC_OFFSET)
            folder_index = 0

            while folder_index < folder_file_count:
                # Read folder block
                folder_name = file.read(4).decode('ascii', errors='ignore').strip('\x00')
                file_count = struct.unpack('<I', file.read(4))[0]  # Number of files in folder
                folder = {'name': folder_name, 'files': []}

                for _ in range(file_count):
                    # Read file block sequentially
                    file_block = file.read(self.FILE_BLOCK_SIZE)
                    file_name = file_block[:4].decode('ascii', errors='ignore').strip('\x00')
                    pointer = struct.unpack('<I', file_block[4:])[0] >> 0x0B
                    file_length = struct.unpack('<H', file_block[6:8])[0]

                    # Read the file's data
                    current_pos = file.tell()
                    file.seek(self.DATA_OFFSET + pointer)
                    file_data = file.read(file_length)
                    file.seek(current_pos)  # Move back to TOC position
                    
                    folder['files'].append({'name': file_name, 'data': file_data})
                
                self.folders.append(folder)
                folder_index += 1

class EPAC:
    def __init__(self, file_path): self.file_path = file_path
    def load(self): print("Loading EPAC format...")

class EPK8:
    def __init__(self, file_path): self.file_path = file_path
    def load(self): print("Loading EPK8 format...")

class DPK8:
    def __init__(self, file_path): self.file_path = file_path
    def load(self): print("Loading DPK8 format...")

class HSPC:
    def __init__(self, file_path): self.file_path = file_path
    def load(self): print("Loading HSPC format...")

class PAC:
    def __init__(self, file_path): self.file_path = file_path
    def load(self): print("Loading PAC format...")

class PACH:
    def __init__(self, file_path): self.file_path = file_path
    def load(self): print("Loading PACH format...")

class SHDC:
    def __init__(self, file_path): self.file_path = file_path
    def load(self): print("Loading SHDC format...")

class PACTool:
    HEADER_MAP = {
        b'DPAC': DPAC,
        b'EPAC': EPAC,
        b'EPK8': EPK8,
        b'DPK8': DPK8,
        b'HSPC': HSPC,
        b'SHDC': SHDC,
        b'PAC ': PAC,
        b'PACH': PACH
    }

    @staticmethod
    def load_file(file_path):
        with open(file_path, 'rb') as file:
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
        self.tree.bind("<Button-3>", self.show_context_menu)  # Right-click for context menu

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
        file_path = filedialog.askopenfilename(filetypes=[("Yuke's Package Files", "*.pac")])
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
            folder_node = self.tree.insert(root_node, "end", text=folder['name'], open=True)
            for file_info in folder['files']:
                file_node = self.tree.insert(folder_node, "end", text=file_info['name'])
                self.add_icon(file_info['name'], file_node)

    def add_icon(self, file_name, tree_node):
        ext = os.path.splitext(file_name)[1]
        
        if ext not in self.icon_cache:
            dummy_file_path = os.path.join(os.path.expanduser("~"), f"dummy{ext}")
            with open(dummy_file_path, 'wb') as dummy_file:
                dummy_file.write(b'\0')
                
            shinfo = SHFILEINFO()
            flags = SHGFI_ICON | SHGFI_SMALLICON
            hicon = shell32.SHGetFileInfoW(dummy_file_path, 0, ctypes.byref(shinfo), ctypes.sizeof(shinfo), flags)
            
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
            ctypes.windll.gdi32.GetObjectW(hbitmap, ctypes.sizeof(bmp_info), ctypes.byref(bmp_info))
            bmp_data = ctypes.create_string_buffer(bmp_info.biSizeImage)
            ctypes.windll.gdi32.GetDIBits(user32.GetDC(0), hbitmap, 0, bmp_info.biHeight, bmp_data, ctypes.byref(bmp_info), 0)
            img = Image.frombuffer("RGBA", (bmp_info.biWidth, bmp_info.biHeight), bmp_data, "raw", "BGRA", 0, 1)
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
        tk.Button(btn_frame, text="OK", command=properties_window.destroy).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Cancel", command=properties_window.destroy).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Apply", command=lambda: self.apply_properties(name_entry, item_id)).grid(row=0, column=2, padx=5)

    def apply_properties(self, name_entry, item_id):
        new_name = name_entry.get()
        self.tree.item(item_id, text=new_name)

if __name__ == "__main__":
    root = tk.Tk()
    app = PACToolGUI(root)
    root.geometry("600x400")
    root.mainloop()