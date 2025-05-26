from tkinter import Tk, Text, BOTH, END

def assert_failed_gui(
   offender: str = 's_SystemConfig.nPacHeaderBufferSize > 0',
   source: str = 'cfile.cpp',
   line: int = 0xBF,
   function: str = None
):
   message = (
       "**************** Assertion Failed!! ****************\n"
       f" !!({offender})\n"
       f" file:{source} line:{line}, func : {function or '<unknown>'}"
   )

   root = Tk()
   root.title("ASSERT FAILED")

   text_box = Text(root, height=10, width=70, bg="black", fg="red", font=("Courier", 10, "bold"))
   text_box.pack(expand=True, fill=BOTH)
   text_box.insert(END, message)
   text_box.config(state='disabled')  # Prevent edits

   root.mainloop()

if __name__ == "__main__":
   assert_failed_gui()
