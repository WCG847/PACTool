import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from DPAC.DPAC import DPAC
from Utilities.PACUtilities import *
from MPQ.MPQ import MPQ


class PACToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PACTool")

        # Create menu bar
        self.menu_bar = tk.Menu(self.root)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Open", command=self.open_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.root.config(menu=self.menu_bar)

        # Add "Tools" menu
        self.tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.tools_menu.add_command(label="Mass Extract", command=self.mass_extract)
        # Create menu with a DPAC submenu
        self.create_menu = tk.Menu(self.tools_menu, tearoff=0)
        self.create_menu.add_command(label="DPAC", command=self.create_dpac)
        
        # Add "Create" option in the tools menu, which now has a submenu for DPAC
        self.tools_menu.add_cascade(label="Create", menu=self.create_menu)
        self.menu_bar.add_cascade(label="Tools", menu=self.tools_menu)

        # Create Treeview widget
        self.tree_frame = ttk.Frame(self.root)
        self.tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        # Scrollbars
        self.tree_scroll_y = ttk.Scrollbar(self.tree_frame, orient="vertical")
        self.tree_scroll_y.pack(side="right", fill="y")

        self.tree_scroll_x = ttk.Scrollbar(self.tree_frame, orient="horizontal")
        self.tree_scroll_x.pack(side="bottom", fill="x")

        self.tree = ttk.Treeview(
            self.tree_frame, columns=("Offset", "Size"), show="tree headings",
            yscrollcommand=self.tree_scroll_y.set, xscrollcommand=self.tree_scroll_x.set
        )
        self.tree.heading("#0", text="Name", command=lambda: self.sort_column("#0"))
        self.tree.heading("Offset", text="Offset", command=lambda: self.sort_column("Offset"))
        self.tree.heading("Size", text="Size", command=lambda: self.sort_column("Size"))
        
        self.tree.column("#0", width=300, anchor="w")
        self.tree.column("Offset", width=100, anchor="center")
        self.tree.column("Size", width=100, anchor="center")

        self.tree.pack(fill="both", expand=True)

        # Configure scrollbars to work with treeview
        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)

        # DPAC parser instance
        self.dpac = None
        self.mpq = None

    def mass_extract(self):
        """Mass extract file content to a folder hierarchy."""
        if self.dpac and self.dpac.toc:
            self.extract_dpac()
        elif self.mpq:
            self.extract_mpq()
        else:
            messagebox.showwarning("Warning", "No data available to extract.")

    def extract_dpac(self):
        """Mass extract DPAC files."""
        output_dir = filedialog.askdirectory(title="Select Output Folder")
        if not output_dir:
            return

        try:
            mass_extract(self.dpac, output_dir)
            messagebox.showinfo("Mass Extract", f"Extraction completed successfully to {output_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract files:\n{e}")

    def extract_mpq(self):
        """Mass extract MPQ files."""
        output_dir = filedialog.askdirectory(title="Select Output Folder")
        if not output_dir:
            return

        try:
            self.mpq.extract_files(self.mpq.parse_toc(), output_dir)
            messagebox.showinfo("Mass Extract", f"Extraction completed successfully to {output_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract files:\n{e}")

    def create_dpac(self):
        """Create a new DPAC file from a folder."""
        # Prompt user to select an input folder
        input_folder = filedialog.askdirectory(
            title="Select Folder to Pack"
        )
        if not input_folder:
            return

        # Prompt user to save the DPAC file
        output_path = filedialog.asksaveasfilename(
            title="Save DPAC File As",
            filetypes=[("Yuke's Data Package Files", "*.pac"), ("All Files", "*.*")],
            defaultextension=".pac",
        )
        if not output_path:
            return

        try:
            # Generate folder structure metadata
            folder_structure = self.build_folder_structure(input_folder)
            if not folder_structure:
                messagebox.showwarning("Warning", "No valid files found in the selected folder.")
                return

            # Create DPAC file
            dpac = DPAC(output_path)
            dpac.create_new_dpac(output_path, folder_structure)
            messagebox.showinfo("Create DPAC", f"DPAC file created successfully: {output_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create DPAC file:\n{e}")


    def build_folder_structure(self, root_folder):
        """
        Walks through the input folder and builds the folder structure for DPAC creation.

        :param root_folder: The root folder to pack.
        :return: A list of dictionaries representing the folder structure.
        """
        folder_structure = []
        total_size = 0  # Track total size of all files

        try:
            for dirpath, dirnames, filenames in os.walk(root_folder):
                # Use the folder name relative to the root folder
                folder_name = os.path.relpath(dirpath, root_folder).replace("\\", "/")  # Normalize slashes

                # If the folder is the root folder, use its actual name
                if folder_name == ".":
                    folder_name = os.path.basename(root_folder)  # Use actual name, e.g., "AUTO"

                # Truncate folder name to 4 characters, padded with nulls
                truncated_folder_name = folder_name[:4].ljust(4, "\x00")

                print(f"Processing folder: {truncated_folder_name}")  # Debug: Log folder name
                folder = {"folder_name": truncated_folder_name, "files": []}

                for filename in filenames:
                    # Truncate file name to 4 characters
                    truncated_filename = filename[:4].ljust(4, "\x00")

                    file_path = os.path.join(dirpath, filename)
                    print(f"Found file: {truncated_filename} in {truncated_folder_name}")  # Debug: Log file discovery

                    with open(file_path, "rb") as f:
                        file_data = f.read()

                    # Validate file size
                    file_size = len(file_data)
                    if file_size >= (1 << 24):  # Max size per file based on DPAC spec
                        raise ValueError(f"File '{filename}' in folder '{folder_name}' exceeds max size.")

                    # Update total size
                    total_size += file_size
                    if total_size > 80 * 1024 * 1024:  # 80 MB limit
                        raise ValueError("Total PAC file size exceeds 80 MB limit.")

                    folder["files"].append({"file_name": truncated_filename, "file_data": file_data})

                # Only add the folder if it contains files
                if folder["files"]:
                    folder_structure.append(folder)

            # Validate total TOC entries
            total_toc_entries = sum(len(folder["files"]) + 1 for folder in folder_structure)  # Folder + files
            if total_toc_entries > 65535:
                raise ValueError(f"Too many entries in TOC. Max allowed: 65535.")

            print(f"Total PAC file size: {total_size / (1024 * 1024):.2f} MB")  # Debug: Log total size
            return folder_structure

        except Exception as e:
            print(f"Error in build_folder_structure: {e}")
            raise



    def open_file(self):
        """Open a file and determine its type by magic bytes."""
        file_path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[("Yuke's Material Package Files", "*.mpc"),
                       ("Yuke's Material Package Files", "*.mpq"),
                       ("Yuke's Data Package Files", "*.pac"),
                       ("All Files", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "rb") as f:
                magic = f.read(4)  # Note: DPAC expects 4 bytes, MPQ expects 3 bytes
                print(f"Magic bytes: {magic}")  # Debugging output
            if magic[:4] == b"DPAC":  # Ensure full DPAC magic is checked
                self.load_dpac(file_path)
            elif magic[:3] == b"MPQ":  # MPQ only checks first 3 bytes
                self.load_mpq(file_path)
            else:
                messagebox.showwarning("Unknown Format", "File type not recognized.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file:\n{e}")

    def load_dpac(self, file_path):
        """Load and display DPAC structure."""
        try:
            self.dpac = DPAC(file_path)
            self.dpac.load()
            self.display_dpac_structure()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse DPAC file:\n{e}")

    def load_mpq(self, file_path):
        """Load and display MPQ structure."""
        try:
            self.mpq = MPQ(file_path)
            self.mpq.read_file()
            self.mpq.check_magic()
            file_pointers = self.mpq.parse_toc()
            self.display_mpq_structure(file_pointers)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse MPQ file:\n{e}")

    def display_dpac_structure(self):
        self.tree.delete(*self.tree.get_children())
        for folder in self.dpac.toc:
            folder_node = self.tree.insert("", "end", text=folder["folder_name"], values=("", ""), open=False)
            for file in folder["files"]:
                offset = f"0x{file['file_pointer']:08X}"
                size = format_size(file["file_size"])
                self.tree.insert(folder_node, "end", text=file["file_name"], values=(offset, size))

    def display_mpq_structure(self, file_pointers):
        self.tree.delete(*self.tree.get_children())
        for i, pointer in enumerate(file_pointers):
            file_name = f"{i:04}.bin"
            offset = f"0x{pointer:08X}"
            size = "Unknown"
            self.tree.insert("", "end", text=file_name, values=(offset, size))


    def sort_column(self, col):
        """Sort treeview by a column."""
        data = [(self.tree.item(item)["values"], item) for item in self.tree.get_children()]
        data.sort(key=lambda x: x[0][col] if isinstance(x[0][col], str) else 0)
        for index, (values, item) in enumerate(data):
            self.tree.item(item, values=values)

if __name__ == "__main__":
    root = tk.Tk()
    app = PACToolGUI(root)
    root.resizable(True, True)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = int(screen_width * 0.8)
    window_height = int(screen_height * 0.8)
    root.geometry(f"{window_width}x{window_height}")
    root.mainloop()
