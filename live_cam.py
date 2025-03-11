import cv2
import face_recognition
import numpy as np
import sqlite3
from datetime import date
import os
import warnings

# Suppress warnings (optional)
warnings.filterwarnings("ignore")

# Constants
FOLDER_PATH = 'images'
DATABASE_NAME = 'db.sqlite3'
KNOWN_FACES = []
KNOWN_IDS = []

def load_known_faces():
    """Load known faces from the images folder and encode them."""
    global KNOWN_FACES, KNOWN_IDS
    for filename in os.listdir(FOLDER_PATH):
        if filename.endswith(('.png', '.jpeg', '.jpg', '.gif')):
            image_path = os.path.join(FOLDER_PATH, filename)
            face_image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(face_image)
            
            # Separate file name and extension
            file_name, file_extension = os.path.splitext(filename)
            
            if face_encodings:
                KNOWN_FACES.append(face_encodings[0])
                KNOWN_IDS.append(file_name)  # Store only the file name without extension
            else:
                print(f"Warning: No face found in {filename}")

def detect_faces_in_frame(frame, known_faces, known_ids):
    """Detect and recognize faces in a given frame."""
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    small_frame_rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(small_frame_rgb, model="hog")
    face_encodings = face_recognition.face_encodings(small_frame_rgb, face_locations)

    detected_names = set()

    for face_encoding, face_location in zip(face_encodings, face_locations):
        matches = face_recognition.compare_faces(known_faces, face_encoding, tolerance=0.5)
        name = "Unknown"

        if True in matches:
            match_index = matches.index(True)
            name = known_ids[match_index]
            detected_names.add(name)

        top, right, bottom, left = [v * 4 for v in face_location]
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (127, 255, 0), 2)

    return frame, detected_names

def update_sqlite_table(detected_names):
    """Update the SQLite database with detected names."""
    try:
        sqlite_connection = sqlite3.connect(DATABASE_NAME)
        cursor = sqlite_connection.cursor()
        print("Connected to SQLite")

        today = date.today()
        print(f"Today's date: {today}")

        for student_id in detected_names:
            sql_update_query = """UPDATE info_attendance SET status = 1 WHERE student_id = ? AND date = ?"""
            cursor.execute(sql_update_query, (student_id, today))
            if cursor.rowcount > 0:
                print(f"Record updated successfully for student ID: {student_id}")
            else:
                print(f"No record found for student ID: {student_id} on date: {today}")
            sqlite_connection.commit()

    except sqlite3.Error as error:
        print("Failed to update SQLite table:", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("The SQLite connection is closed")

def main():
    """Main function to run the face detection and database update."""
    # Load known faces
    load_known_faces()
    print(f"Loaded {len(KNOWN_IDS)} known faces.")

    # Initialize the webcam
    video_capture = cv2.VideoCapture(0)
    frame_count = 0
    detected_names = set()

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Failed to capture frame.")
            break

        # Process every other frame
        if frame_count % 2 == 0:
            frame, names = detect_faces_in_frame(frame, KNOWN_FACES, KNOWN_IDS)
            detected_names.update(names)

        # Display the frame
        cv2.imshow("Video", frame)

        # Break the loop on 'q' key press
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

        frame_count += 1

    # Release resources
    video_capture.release()
    cv2.destroyAllWindows()

    # Print detected names
    print("Detected names:", detected_names)

    # Update the database
    update_sqlite_table(detected_names)

if __name__ == "__main__":
    main()