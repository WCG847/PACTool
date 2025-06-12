from PyQt5.QtWidgets import (
	QApplication, QMainWindow, QWidget, QVBoxLayout,
	QPushButton, QFileDialog, QMessageBox, QHBoxLayout, QAbstractItemView, QTreeWidget,
	QTreeWidgetItem
)
import sys, os
from DPAC import DirectoryPackage

class DPACGUI(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("PACTool")
		self.resize(800, 600)

		self.dpac = DirectoryPackage()
		self.contents = []

		self.init_ui()

	def init_ui(self):
		main_widget = QWidget()
		self.setCentralWidget(main_widget)

		main_layout = QVBoxLayout()
		main_widget.setLayout(main_layout)

		# Top control buttons
		top_layout = QHBoxLayout()
		self.load_btn = QPushButton("Load DPAC")
		self.load_btn.clicked.connect(self.load_dpac)

		self.export_btn = QPushButton("Export Selected")
		self.export_btn.clicked.connect(self.export_selected)

		top_layout.addWidget(self.load_btn)
		top_layout.addWidget(self.export_btn)
		top_layout.addStretch()

		main_layout.addLayout(top_layout)

		# Tree view for contents
		self.tree = QTreeWidget()
		self.tree.setHeaderLabels(["File/Folder", "Size", "Offset"])
		self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.tree.setColumnWidth(0, 300)
		main_layout.addWidget(self.tree)

	def load_dpac(self):
		file_path, _ = QFileDialog.getOpenFileName(self, "Select DPAC File", "", "DPAC files (*.pac);;All files (*.*)")
		if not file_path:
			return

		try:
			self.dpac.Load(file_path)
			self.contents = self.dpac.Bin2Dict()
			self.display_contents()
		except Exception as e:
			QMessageBox.critical(self, "Error", f"Failed to load DPAC file:\n{str(e)}")

	def display_contents(self):
		self.tree.clear()
		for folder, file_count, entries in self.contents:
			folder_item = QTreeWidgetItem([folder])
			folder_item.setExpanded(True)
			for entry in entries:
				name_or_id = entry[0]
				size = str(entry[1])
				offset = str(entry[2])
				file_item = QTreeWidgetItem([name_or_id, size, offset])
				folder_item.addChild(file_item)
			self.tree.addTopLevelItem(folder_item)

	def export_selected(self):
		selected_items = self.tree.selectedItems()
		if not selected_items:
			QMessageBox.information(self, "Info", "No file selected.")
			return

		export_dir = QFileDialog.getExistingDirectory(self, "Select Export Directory")
		if not export_dir:
			return

		export_count = 0
		for item in selected_items:
			parent = item.parent()
			if not parent:
				continue  # Skip folders
			folder_name = parent.text(0)
			name = item.text(0)
			size = int(item.text(1))
			offset = int(item.text(2))

			self.dpac.Data.seek(offset)
			data = self.dpac.Data.read(size)

			out_folder = os.path.join(export_dir, folder_name)
			os.makedirs(out_folder, exist_ok=True)
			with open(os.path.join(out_folder, name), 'wb') as f:
				f.write(data)
			export_count += 1

		QMessageBox.information(self, "Success", f"Export completed. Files exported: {export_count}")

if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = DPACGUI()
	window.show()
	sys.exit(app.exec_())
