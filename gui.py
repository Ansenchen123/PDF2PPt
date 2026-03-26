import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import os
import threading
from dotenv import load_dotenv, set_key
from main import convert_pdf_to_ppt
from pdf_utils import get_page_count

# Load env file path
ENV_PATH = ".env"

class PageRangeDialog(tk.Toplevel):
    def __init__(self, parent, total_pages):
        super().__init__(parent)
        self.title("Select Page Range")
        self.geometry("300x180")
        self.total_pages = total_pages
        self.result = None
        
        tk.Label(self, text=f"Total Pages: {total_pages}").pack(pady=10)
        
        frame = tk.Frame(self)
        frame.pack(pady=5)
        
        tk.Label(frame, text="From:").pack(side=tk.LEFT)
        self.start_entry = tk.Entry(frame, width=5)
        self.start_entry.insert(0, "1")
        self.start_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(frame, text="To:").pack(side=tk.LEFT)
        self.end_entry = tk.Entry(frame, width=5)
        self.end_entry.insert(0, str(total_pages))
        self.end_entry.pack(side=tk.LEFT, padx=5)
        
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Confirm", command=self.on_confirm).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=10)
        
        self.grab_set()
        self.wait_window()
        
    def on_confirm(self):
        try:
            s_val = self.start_entry.get().strip()
            e_val = self.end_entry.get().strip()
            
            if not s_val or not e_val:
                messagebox.showerror("Invalid Input", "Please enter valid integers")
                return

            s = int(s_val)
            e = int(e_val)
            
            if s < 1 or e > self.total_pages:
                messagebox.showerror("Invalid Input", f"Pages must be between 1 and {self.total_pages}")
                return
            if s > e:
                messagebox.showerror("Invalid Input", "Start page cannot be greater than end page")
                return
                
            self.result = (s, e)
            self.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid integers")

class PDF2PPTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF to PPT Converter (Gemini OCR)")
        self.root.geometry("600x350")
        
        # Grid config
        self.root.columnconfigure(1, weight=1)
        
        # Variables
        self.pdf_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.api_key = tk.StringVar()
        self.status = tk.StringVar(value="Ready")
        
        self.load_env()
        self.create_widgets()
        
    def load_env(self):
        if not os.path.exists(ENV_PATH):
            # Create empty .env if not exists
            with open(ENV_PATH, "w") as f:
                f.write("")
        
        load_dotenv(ENV_PATH, override=True)
        key = os.getenv("GEMINI_API_KEY")
        if key:
            self.api_key.set(key)
            
    def save_api_key(self):
        key = self.api_key.get().strip()
        if not key:
            messagebox.showwarning("Warning", "Please enter an API Key.")
            return
            
        try:
            # Check if .env exists again (double check)
            if not os.path.exists(ENV_PATH):
                with open(ENV_PATH, "w") as f:
                    f.write("")
            
            # Use dotenv set_key to update the file
            set_key(ENV_PATH, "GEMINI_API_KEY", key)
            messagebox.showinfo("Success", "API Key saved to .env file.")
            
            # Reload to current session
            os.environ["GEMINI_API_KEY"] = key
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save API Key: {e}")

    def browse_pdf(self):
        filename = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if filename:
            self.pdf_path.set(filename)
            # Default output directory to source directory if not set
            if not self.output_path.get():
                self.output_path.set(os.path.dirname(filename))

    def browse_output(self):
        dirname = filedialog.askdirectory()
        if dirname:
            self.output_path.set(dirname)

    def create_widgets(self):
        pad_x = 10
        pad_y = 5
        
        # Row 0: PDF Source
        tk.Label(self.root, text="Source PDF:").grid(row=0, column=0, sticky="e", padx=pad_x, pady=pad_y)
        tk.Entry(self.root, textvariable=self.pdf_path).grid(row=0, column=1, sticky="ew", padx=pad_x, pady=pad_y)
        tk.Button(self.root, text="Browse", command=self.browse_pdf).grid(row=0, column=2, padx=pad_x, pady=pad_y)
        
        # Row 1: Output PPT
        tk.Label(self.root, text="Output Folder:").grid(row=1, column=0, sticky="e", padx=pad_x, pady=pad_y)
        tk.Entry(self.root, textvariable=self.output_path).grid(row=1, column=1, sticky="ew", padx=pad_x, pady=pad_y)
        tk.Button(self.root, text="Browse", command=self.browse_output).grid(row=1, column=2, padx=pad_x, pady=pad_y)
        
        # Row 2: API Key
        tk.Label(self.root, text="API Key:").grid(row=2, column=0, sticky="e", padx=pad_x, pady=pad_y)
        tk.Entry(self.root, textvariable=self.api_key, show="*").grid(row=2, column=1, sticky="ew", padx=pad_x, pady=pad_y)
        tk.Button(self.root, text="Update Key", command=self.save_api_key).grid(row=2, column=2, padx=pad_x, pady=pad_y)
        
        # Row 3: Convert Button
        tk.Button(self.root, text="Start Conversion", command=self.start_conversion_flow, bg="#dddddd", height=2).grid(row=3, column=0, columnspan=3, sticky="ew", padx=pad_x, pady=20)
        
        # Row 4: Status
        tk.Label(self.root, textvariable=self.status, fg="blue").grid(row=4, column=0, columnspan=3, sticky="w", padx=pad_x, pady=pad_y)

    def start_conversion_flow(self):
        pdf = self.pdf_path.get().strip()
        if not pdf or not os.path.exists(pdf):
            messagebox.showwarning("Warning", "Please select a valid PDF file.")
            return

        try:
            total = get_page_count(pdf)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read PDF: {e}")
            return
            
        dlg = PageRangeDialog(self.root, total)
        if dlg.result:
            start_page, end_page = dlg.result
            t = threading.Thread(target=self.run_conversion, args=(start_page, end_page))
            t.start()
        
    def run_conversion(self, start_page, end_page):
        pdf = self.pdf_path.get().strip()
        out_dir = self.output_path.get().strip()
        key = self.api_key.get().strip()
        
        # Checks
        if not pdf:
            return
        if not out_dir:
            messagebox.showwarning("Warning", "Please specify an output directory.")
            return
        
        # Construct output filename
        base_name = os.path.splitext(os.path.basename(pdf))[0]
        out_file = os.path.join(out_dir, base_name + ".pptx")
            
        # Check API Key
        if not key:
            # Try load from env if empty in box (though box is init from env)
            env_key = os.getenv("GEMINI_API_KEY")
            if not env_key:
                messagebox.showwarning("Warning", "API Key is missing. Please enter it and click Update.")
                return
            key = env_key

        # Check Output File Lock
        if os.path.exists(out_file):
            try:
                # Try to rename to itself to check lock
                os.rename(out_file, out_file)
            except OSError:
                messagebox.showerror("Error", f"The output file '{os.path.basename(out_file)}' is currently open.\nPlease close it and try again.")
                return

        self.status.set(f"Starting conversion (Pages {start_page}-{end_page})...")
        
        try:
            convert_pdf_to_ppt(
                pdf, 
                out_file, 
                api_key=key, 
                start_page=start_page,
                end_page=end_page,
                callback=self.update_status
            )
            self.status.set(f"Completed! Saved to {os.path.basename(out_file)}")
            messagebox.showinfo("Success", "Conversion completed successfully!")
        except Exception as e:
            self.status.set("Completed with errors.")
            messagebox.showinfo("Conversion Status", f"{str(e)}")

    def update_status(self, current, total, message):
        self.status.set(message)
        self.root.update_idletasks()

if __name__ == "__main__":
    root = tk.Tk()
    app = PDF2PPTApp(root)
    root.mainloop()
