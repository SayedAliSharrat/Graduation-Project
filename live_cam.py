import cv2
import face_recognition
import numpy as np
import sqlite3
from datetime import datetime, date
import os
import warnings
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading

# Suppress warnings
warnings.filterwarnings("ignore")

class FaceRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition Attendance System")
        self.root.geometry("1000x700")
        
        # Initialize variables
        self.KNOWN_FACES = []
        self.KNOWN_IDS = []
        self.detected_names = set()
        self.is_running = False
        self.video_capture = None
        self.current_frame = None
        self.status_var = tk.StringVar()
        self.blank_image = None
        
        # Create a blank image for when camera is stopped
        self.create_blank_image()
        
        # Load known faces
        self.load_known_faces()
        
        # Create GUI
        self.create_widgets()
        
        # Initialize results log
        self.log_message("=== Attendance System Initialized ===")
        self.log_message(f"Loaded {len(self.KNOWN_IDS)} known faces")
    
    def log_message(self, message):
        """Add timestamped message to the log."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.results_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.results_text.see(tk.END)
    
    def create_blank_image(self):
        """Create a blank black image for when camera is stopped."""
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        self.blank_image = ImageTk.PhotoImage(image=Image.fromarray(blank))
    
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Video feed frame
        video_frame = ttk.LabelFrame(main_frame, text="Camera Feed")
        video_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        self.video_label = ttk.Label(video_frame, image=self.blank_image)
        self.video_label.pack()
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        self.start_btn = ttk.Button(control_frame, text="Start Camera", command=self.start_camera)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="Stop Camera", command=self.stop_camera, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.process_btn = ttk.Button(control_frame, text="Process Attendance", command=self.process_attendance)
        self.process_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(control_frame, text="Clear Log", command=self.clear_log)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Attendance Log")
        results_frame.grid(row=0, column=1, rowspan=2, padx=5, pady=5, sticky="nsew")
        
        self.results_text = tk.Text(results_frame, height=20, width=40)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(results_frame, command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=scrollbar.set)
        
        # Status bar
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=0)
    
    def clear_log(self):
        """Clear the attendance log."""
        self.results_text.delete(1.0, tk.END)
        self.log_message("=== Log Cleared ===")
        self.update_status("Log cleared")
        
    def load_known_faces(self):
        """Load known faces from the images folder and encode them."""
        FOLDER_PATH = 'images'
        for filename in os.listdir(FOLDER_PATH):
            if filename.endswith(('.png', '.jpeg', '.jpg', '.gif')):
                image_path = os.path.join(FOLDER_PATH, filename)
                face_image = face_recognition.load_image_file(image_path)
                face_encodings = face_recognition.face_encodings(face_image)
                
                file_name, _ = os.path.splitext(filename)
                
                if face_encodings:
                    self.KNOWN_FACES.append(face_encodings[0])
                    self.KNOWN_IDS.append(file_name)
    
    def start_camera(self):
        """Start the camera feed."""
        if not self.is_running:
            self.video_capture = cv2.VideoCapture(0)
            if not self.video_capture.isOpened():
                messagebox.showerror("Error", "Could not open video device")
                return
                
            self.is_running = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.update_status("Camera started - Detecting faces...")
            self.log_message("Camera started")
            self.update_camera()
    
    def stop_camera(self):
        """Stop the camera feed and clear the display."""
        if self.is_running:
            self.is_running = False
            if self.video_capture:
                self.video_capture.release()
                self.video_capture = None
            
            # Clear the video display
            self.video_label.configure(image=self.blank_image)
            self.video_label.image = self.blank_image
            
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.update_status("Camera stopped")
            self.log_message("Camera stopped")
    
    def update_camera(self):
        """Update the camera feed in the GUI."""
        if self.is_running and self.video_capture:
            ret, frame = self.video_capture.read()
            if ret:
                # Process frame for face detection
                frame, names = self.detect_faces_in_frame(frame)
                self.detected_names.update(names)
                
                # Convert to RGB and resize for display
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (640, 480))
                
                # Convert to ImageTk format
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                
                # Update the label
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
                self.video_label.image = imgtk  # Keep reference
                
            # Schedule the next update
            self.root.after(10, self.update_camera)
    
    def detect_faces_in_frame(self, frame):
        """Detect and recognize faces in a given frame."""
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        small_frame_rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(small_frame_rgb, model="hog")
        face_encodings = face_recognition.face_encodings(small_frame_rgb, face_locations)

        detected_names = set()

        for face_encoding, face_location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(self.KNOWN_FACES, face_encoding, tolerance=0.5)
            name = "Unknown"

            if True in matches:
                match_index = matches.index(True)
                name = self.KNOWN_IDS[match_index]
                detected_names.add(name)

            top, right, bottom, left = [v * 4 for v in face_location]
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (127, 255, 0), 2)

        return frame, detected_names
    
    def process_attendance(self):
        """Process the detected faces and update the database."""
        if not self.detected_names:
            messagebox.showwarning("Warning", "No faces detected to process")
            return
        
        self.log_message("\n=== Processing Attendance ===")
        self.log_message(f"Detected Students: {', '.join(sorted(self.detected_names))}")
        
        # Update database in a separate thread
        threading.Thread(target=self.update_database, daemon=True).start()
        self.update_status("Processing attendance...")
    
    def update_database(self):
        """Update the SQLite database with detected names."""
        DATABASE_NAME = 'db.sqlite3'
        today = date.today()
        updated_students = []
        failed_students = []
        
        try:
            sqlite_connection = sqlite3.connect(DATABASE_NAME)
            cursor = sqlite_connection.cursor()
            
            # Make a copy of detected names to process
            names_to_process = self.detected_names.copy()
            
            for student_id in names_to_process:
                try:
                    # Check if record exists for today
                    cursor.execute("SELECT 1 FROM info_attendance WHERE student_id = ? AND date = ?", 
                                 (student_id, today))
                    exists = cursor.fetchone()
                    
                    if exists:
                        # Update existing record
                        cursor.execute("""UPDATE info_attendance 
                                        SET status = 1 
                                        WHERE student_id = ? AND date = ?""", 
                                     (student_id, today))
                        updated_students.append(student_id)
                        self.log_message(f"Updated attendance for {student_id}")
                    else:
                        # Insert new record
                        cursor.execute("""INSERT INTO info_attendance 
                                        (student_id, date, status) 
                                        VALUES (?, ?, 1)""", 
                                     (student_id, today))
                        updated_students.append(student_id)
                        self.log_message(f"Created new attendance record for {student_id}")
                    
                except sqlite3.Error as e:
                    failed_students.append(student_id)
                    self.log_message(f"Error processing {student_id}: {str(e)}")
            
            sqlite_connection.commit()
            
            # Log summary of updates
            if updated_students:
                self.log_message(f"\nSuccessfully updated {len(updated_students)} records:")
                for student in sorted(updated_students):
                    self.log_message(f"• {student}")
            
            if failed_students:
                self.log_message(f"\nFailed to update {len(failed_students)} records:")
                for student in sorted(failed_students):
                    self.log_message(f"• {student}")
            
            # Update status with summary
            status_msg = []
            if updated_students:
                status_msg.append(f"Updated {len(updated_students)}")
            if failed_students:
                status_msg.append(f"Failed {len(failed_students)}")
            
            self.update_status(", ".join(status_msg))
            
            # Clear detected faces after processing
            self.detected_names.clear()
            
        except sqlite3.Error as error:
            self.log_message(f"\nDatabase error: {error}")
            self.update_status("Database error")
        finally:
            if sqlite_connection:
                sqlite_connection.close()
    
    def update_status(self, message):
        """Update the status bar."""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def on_closing(self):
        """Handle window closing event."""
        self.stop_camera()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FaceRecognitionApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()