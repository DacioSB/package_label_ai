import customtkinter as ctk
import cv2
from PIL import Image
import os
import time
import logic_ocr
import logic_db

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Scan de Encomendas v1.0")
        self.geometry("1280x720")

        logic_db.init_db()
        
        self.grid_columnconfigure(0, weight=2) 
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        if not os.path.exists("images"):
            os.makedirs("images")

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

        self.frame_right = ctk.CTkFrame(self)
        self.frame_right.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")

        self.lbl_title = ctk.CTkLabel(self.frame_right, text="DADOS DO PACOTE", font=("Arial", 20, "bold"))
        self.lbl_title.pack(pady=20)

        self.create_input_field("Rastreio (Tracking):", "entry_tracking")
        self.create_input_field("Destinatário:", "entry_recipient")
        self.create_input_field("Remetente (Sender):", "entry_sender")
        self.create_input_field("Transportadora:", "entry_carrier")
        self.create_input_field("CEP:", "entry_cep")

        self.lbl_raw = ctk.CTkLabel(self.frame_right, text="Texto Bruto (OCR):", anchor="w")
        self.lbl_raw.pack(fill="x", padx=20, pady=(10, 0))
        
        self.txt_raw = ctk.CTkTextbox(self.frame_right, height=100)
        self.txt_raw.pack(fill="x", padx=20, pady=5)
        self.txt_raw.configure(cursor="xterm")

        self.btn_save = ctk.CTkButton(
            self.frame_right, 
            text="💾 SALVAR NO BANCO", 
            height=50,
            fg_color="#22C55E",
            hover_color="#15803D",
            font=("Arial", 15, "bold"),
            cursor="hand2",
            command=self.save_data
        )
        self.btn_save.pack(side="bottom", fill="x", padx=20, pady=20)
        
        self.lbl_status = ctk.CTkLabel(self.frame_right, text="Câmera ativa.", text_color="gray")
        self.lbl_status.pack(side="bottom", pady=5)

        self.cap = cv2.VideoCapture(0)
        self.width, self.height = 800, 600
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        self.is_frozen = False
        self.current_frame = None
        self.current_image_path = None

        self.update_camera()

    def create_input_field(self, label_text, attribute_name):
        lbl = ctk.CTkLabel(self.frame_right, text=label_text, anchor="w")
        lbl.pack(fill="x", padx=20, pady=(10, 0))
        entry = ctk.CTkEntry(self.frame_right, height=35)
        entry.pack(fill="x", padx=20, pady=5)
        entry.configure(cursor="xterm")
        setattr(self, attribute_name, entry)

    def fill_field(self, entry_widget, text):
        """Helper to safely insert text into an Entry widget"""
        entry_widget.delete(0, ctk.END)
        if text:
            entry_widget.insert(0, str(text))

    def update_camera(self):
        if not self.cap.isOpened():
            self.lbl_camera.configure(text="Camera not available")
            return
        if not self.is_frozen:
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = frame
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(cv2image)
                
                imgtk = ctk.CTkImage(light_image=img, dark_image=img, size=(self.width, self.height))
                
                self.lbl_camera.configure(image=imgtk, text="")
                self.lbl_camera.image = imgtk
        
        self.after(20, self.update_camera)

    def capture_image(self):
        if not self.is_frozen:
            self.is_frozen = True
            
            self.btn_capture.configure(text="⏳ LENDO...", fg_color="gray", state="disabled")
            self.lbl_status.configure(text="Processando OCR... Aguarde.", text_color="orange")
            self.update_idletasks()
            
            if self.current_frame is not None:
                filename = f"images/pkg_{int(time.time())}.jpg"
                cv2.imwrite(filename, self.current_frame)
                self.current_image_path = filename

                raw_text = logic_ocr.extract_text(filename)
                data = logic_ocr.parse_fields_strategy_a(raw_text)
                self.fill_field(self.entry_tracking, data.get("tracking", ""))
                self.fill_field(self.entry_recipient, data.get("recipient", ""))
                self.fill_field(self.entry_sender, data.get("sender", ""))
                self.fill_field(self.entry_carrier, data.get("carrier", ""))
                self.fill_field(self.entry_cep, data.get("cep", ""))

                self.txt_raw.delete("0.0", "end")
                self.txt_raw.insert("0.0", raw_text)
            
            self.btn_capture.configure(text="🔄 NOVA FOTO", fg_color="gray", hover_color="#4B5563", state=ctk.NORMAL)
            self.lbl_status.configure(text="OCR Concluído! Verifique/edite os dados.", text_color="green")
        else:
            self.is_frozen = False
            self.current_image_path = None

            self.fill_field(self.entry_tracking, "")
            self.fill_field(self.entry_recipient, "")
            self.fill_field(self.entry_sender, "")
            self.fill_field(self.entry_carrier, "")
            self.fill_field(self.entry_cep, "")
            self.txt_raw.delete("0.0", "end")
            
            self.btn_capture.configure(text="📸 CAPTURAR FOTO", fg_color="orange", hover_color="#D97706")
            self.lbl_status.configure(text="Câmera ativa. Aponte o pacote.", text_color="gray")

    def save_data(self):
        if not self.is_frozen or self.current_image_path is None:
            self.lbl_status.configure(text="⚠️ Erro: Capture uma foto primeiro!", text_color="red")
            return
        
        tracking = self.entry_tracking.get()
        recipient = self.entry_recipient.get()
        sender = self.entry_sender.get()
        carrier = self.entry_carrier.get()
        cep = self.entry_cep.get()
        
        try:
            raw_text = self.txt_raw.get("0.0", "end").strip()
        except:
            raw_text = self.txt_raw.get("1.0", "end").strip()

        print("\n--- INICIANDO SALVAMENTO ---")
        print(f"Rastreio: {tracking}")
        print(f"Destinatário: {recipient}")
        
        try:
            logic_db.insert_package(
                image_path=self.current_image_path,
                raw_ocr_text=raw_text,
                tracking_code=tracking,
                recipient_name=recipient,
                sender=sender,
                carrier=carrier,
                cep=cep
            )
            print("✅ Salvo no banco com sucesso!")
            
            # Unfreeze the camera and clear the form
            self.capture_image()
            
            # Force the status text to show success (must be AFTER capture_image)
            self.lbl_status.configure(text="✅ Pacote Salvo! Aponte o próximo.", text_color="green")
            
        except Exception as e:
            print(f"❌ ERRO GRAVE NO BANCO DE DADOS: {e}") 
            self.lbl_status.configure(text=f"❌ Erro: {str(e)[:30]}...", text_color="red")

if __name__ == "__main__":
    app = App()
    app.mainloop()