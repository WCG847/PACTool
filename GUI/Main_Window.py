import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinterdnd2 import TkinterDnD
import os
import sys
import win32api
import winreg
from Yukes.Package.PAC.PAC import CData

class PACTool:
    def __init__(self, root):
        self.root = root
        self.root.title("PACTool")
        self.root.geometry("1280x720")
        self.root.resizable(True, True)

        # Menu
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        self.menubar.add_command(label="Open", command=self.Open)
        self.menubar.add_command(label="Extract", command=self.Extract)
        self.menubar.add_command(label="Exit", command=self.Exit)

        # Drag and Drop Bindings
        self.root.dnd_accept = True
        self.root.drop_target_register('DND_Files')
        self.root.dnd_bind("<<Drop>>", self.DropFile)

        # Labels
        self.PACLabel = tk.Label(self.root, text="No PAC file loaded")
        self.PACLabel.pack()

        self.PACSizeLabel = tk.Label(self.root, text="Size: N/A")
        self.PACSizeLabel.pack()

        self.PACEntriesLabel = tk.Label(self.root, text="Entries: N/A")
        self.PACEntriesLabel.pack()

        # File List
        self.FileList = ttk.Treeview(self.root, columns=("ID", "FileSize"), show="headings")
        self.FileList.heading("ID", text="ID")
        self.FileList.heading("FileSize", text="Size")
        self.FileList.pack(expand=True, fill="both")

    def Open(self):
        self.PAC = filedialog.askopenfilename(filetypes=[("Yuke's Package Files", "*.pac")])
        if self.PAC:
            try:
                self.Data = CData(self.PAC)
                self.Data.SetAdr()
                self.Data.Search()
                self.Data.GetData()  # <-- Ensure file data is loaded

                if not self.Data.FileEntries:
                    messagebox.showerror("Error", "No valid entries found in PAC file.")
                    return

                self.FileList.delete(*self.FileList.get_children())
                for entry in self.Data.FileEntries:
                    self.FileList.insert("", "end", values=(entry["ID"], entry["FileSize"]))

                self.PACLabel.config(text=os.path.basename(self.PAC))
                self.PACSizeLabel.config(text=f"Size: {os.path.getsize(self.PAC)} bytes")
                self.PACEntriesLabel.config(text=f"Entries: {len(self.Data.FileEntries)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to parse PAC file: {e}")


    def Extract(self):
        if not hasattr(self, "Data") or not self.Data.FileEntries:
            messagebox.showerror("Error", "No PAC file loaded or invalid data.")
            return

        output_folder = filedialog.askdirectory(title="Select Output Folder")
        if not output_folder:
            return

        try:
            for entry in self.Data.FileEntries:
                FileName = os.path.join(output_folder, f"{entry['ID']}.bin")
                with open(FileName, "wb") as File:
                    File.write(entry["Data"])
            messagebox.showinfo("PACTool", "Extraction complete!")
        except Exception as e:
            messagebox.showerror("Error", f"Extraction failed: {e}")

    def DropFile(self, event):
        file_path = event.data.strip()
        if os.path.isfile(file_path) and file_path.endswith(".pac"):
            self.PAC = file_path
            self.Open()

    def Exit(self):
        self.root.quit()

    @staticmethod
    def WindowsRegistrySetup():
        try:
            # Get the full path of the script (or .exe if bundled)
            app_path = os.path.abspath(sys.argv[0])

            # Root registry keys for file association
            pac_extension_key = r"Software\Classes\.pac"
            pac_association_key = r"Software\Classes\PACToolFile"
            pac_shell_key = r"Software\Classes\PACToolFile\shell\open\command"
            pac_context_menu_key = r"Software\Classes\*\shell\Open with PACTool"

            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, pac_extension_key) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "PACToolFile")

            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, pac_association_key) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "PACTool PAC File")
                winreg.SetValueEx(key, "FriendlyTypeName", 0, winreg.REG_SZ, "Yuke's PAC Archive")

            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, pac_shell_key) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{app_path}" "%1"')

            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, pac_context_menu_key) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Open with PACTool")
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f'"{app_path}"')

            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, pac_context_menu_key + r"\command") as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{app_path}" "%1"')

            messagebox.showinfo("Registry Setup", "PACTool has been registered in the Windows Registry!")
    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to modify registry: {e}")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = PACTool(root)
    root.mainloop()
