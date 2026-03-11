import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import os

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Scan de Encomendas v1.0")
        self.geometry("1280x720")

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ===================================================
        # LEFT FRAME: CAMERA PREVIEW
        # ===================================================
        self.frame_left = ctk.CTkFrame(self)
        self.frame_left.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.lbl_camera = ctk.CTkLabel(
            self.frame_left,
            text="Iniciando Câmera...",
            font=("Arial", 20)
        )
        self.lbl_camera.place(relx=0.5, rely=0.5, anchor="center")

        self.btn_capture = ctk.CTkButton(
            self.frame_left, 
            text="📸 CAPTURAR FOTO", 
            height=50,
            font=("Arial", 16, "bold"),
            fg_color="orange",
            hover_color="#D97706",
            cursor="hand2",
            command=self.capture_image
        )
        self.btn_capture.pack(side="bottom", fill="x", padx=20, pady=20)

         # ===================================================
        # RIGHT FRAME: DATA FORM
        # ===================================================
        self.frame_right = ctk.CTkFrame(self)
        self.frame_right.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
        self.lbl_title = ctk.CTkLabel(
            self.frame_right, 
            text="DADOS DO PACOTE", 
            font=("Arial", 20, "bold")
        )
        self.lbl_title.pack(pady=20)

        self.create_input_field("Rastreio (Tracking):", "entry_tracking")
        self.create_input_field("Destinatário:", "entry_recipient")
        self.create_input_field("Remetente (Sender):", "entry_sender")
        self.create_input_field("Transportadora:", "entry_carrier")
        self.create_input_field("CEP:", "entry_cep")

        # --- Raw Text (For Debugging/Manual Check) ---
        self.lbl_raw = ctk.CTkLabel(self.frame_right, text="Texto Bruto (OCR):", anchor="w")
        self.lbl_raw.pack(fill="x", padx=20, pady=(10, 0))

        self.txt_raw = ctk.CTkTextbox(self.frame_right, height=100)
        self.txt_raw.pack(fill="x", padx=20, pady=5)
        self.txt_raw.configure(cursor="xterm")

        # Buttons
        self.btn_save = ctk.CTkButton(
            self.frame_right, 
            text="💾 SALVAR NO BANCO", 
            height=50,
            fg_color="#22C55E",   # Bright Green
            hover_color="#15803D", # Dark Green
            font=("Arial", 15, "bold"),
            cursor="hand2", # FIX: Mouse pointer
            command=self.save_data # Placeholder
        )
        self.btn_save.pack(side="bottom", fill="x", padx=20, pady=20)

        self.lbl_status = ctk.CTkLabel(self.frame_right, text="Pronto.", text_color="gray")
        self.lbl_status.pack(side="bottom", pady=5)

        # ===================================================
        # CAMERA SETUP
        # ===================================================
        #self.cap = cv2.VideoCapture(0)
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.width, self.height = 800, 600
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        self.update_camera()

    def create_input_field(self, label_text, attribute_name):
        """Helper to create Label + Entry pairs cleanly"""
        lbl = ctk.CTkLabel(self.frame_right, text=label_text, anchor="w")
        lbl.pack(fill="x", padx=20, pady=(10, 0))

        entry = ctk.CTkEntry(self.frame_right, height=35)
        entry.pack(fill="x", padx=20, pady=5)
        setattr(self, attribute_name, entry)
    
    def update_camera(self):
        """
        Reads a frame from OpenCV, converts to PhotoImage, 
        and updates the label. Runs every 20ms.
        """
        if not self.cap.isOpened():
            self.lbl_camera.configure(text="Camera not available")
            return
        ret, frame = self.cap.read()
        if ret:
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)

            # Convert to PIL Image
            img = Image.fromarray(cv2image)

            imgtk = ImageTk.PhotoImage(image=img)
            self.lbl_camera.configure(image=imgtk, text="")
            self.lbl_camera.image = imgtk
        self.after(20, self.update_camera)
    
    def capture_image(self):
        print("Click! (Logic coming in Task 4.1)")
    def save_data(self):
        print("Click! (Logic coming in Task 4.2)")


if __name__ == "__main__":
    app = App()
    app.mainloop()
