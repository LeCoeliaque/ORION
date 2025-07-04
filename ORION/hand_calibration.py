import cv2
import numpy as np
import mediapipe as mp

# Initialize mediapipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False,
                       max_num_hands=1,  # Assuming you touch the target with one hand
                       min_detection_confidence=0.5,
                       min_tracking_confidence=0.5)

mp_drawing = mp.solutions.drawing_utils

# Camera capture setup
camera_index = int(1)
cap = cv2.VideoCapture(camera_index)  # Use user-specified camera index

# Set the camera resolution to 1280x720
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)


# Verify the camera resolution
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"Camera resolution: {width}x{height}")  # Should print 1980x1020

# Define target points for calibration (projected positions)
target_points = [(100, 100), (1180, 100), (1180, 700), (100, 700)]  # Adjusted to fit within the screen


calibration_points = []

# Function to capture hand landmarks at target points
def capture_hand_landmarks():
    global calibration_points
    calibration_points.clear()
    for i, point in enumerate(target_points):
        while True:
            calibration_image = np.zeros((height, width, 3), dtype=np.uint8)
            cv2.circle(calibration_image, point, 20, (0, 0, 255), -1)
            cv2.putText(calibration_image, f'Point {i+1}', (point[0] + 30, point[1] - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            # Show the calibration image in full screen
            cv2.namedWindow("Calibration Targets", cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty("Calibration Targets", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            cv2.imshow("Calibration Targets", calibration_image)

            ret, frame = cap.read()
            if not ret:
                continue

            # Convert to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Run hand detection
            results = hands.process(rgb_frame)
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            cv2.imshow("Camera View", frame)

            # Wait for user to press Enter
            key = cv2.waitKey(1)
            if key == 13:  # Enter key
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # Assuming we use the index finger tip landmark (landmark 8)
                        x = int(hand_landmarks.landmark[8].x * frame.shape[1])
                        y = int(hand_landmarks.landmark[8].y * frame.shape[0])
                        calibration_points.append((x, y))
                        print(f"Captured hand landmark for Point {i+1} at: ({x}, {y})")
                        print(f"Current calibration points: {calibration_points}")  # Debugging statement
                        break
                else:
                    print("Error: No hand landmark detected. Please try again.")
                    print("Ensure your hand is visible and positioned correctly.")

                    continue
                break

# Capture hand landmarks at target points
capture_hand_landmarks()
cv2.destroyAllWindows()

# Ensure the captured points are in the correct order
if len(calibration_points) == 4:
    target_points_np = np.array(target_points, dtype=np.float32)
    calibration_points_np = np.array(calibration_points, dtype=np.float32)
    M, _ = cv2.findHomography(calibration_points_np, target_points_np)
    np.save("M.npy", M)
    print("Calibration successful. M matrix saved.")
    print("You can now use this calibration for hand tracking.")

else:
    print("Error: Not all calibration points were captured.")
    print("Please restart the calibration process.")
