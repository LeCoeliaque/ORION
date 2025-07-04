import cv2
import numpy as np
import mediapipe as mp
import pygame
import time
import os
import sys
import math

class CameraManager:
    def __init__(self, transformation_matrix_path, width, height):
        self.width = width
        self.height = height
        self.cap = cv2.VideoCapture(1)
        
        # Set the camera resolution to match the camera's capabilities
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 745)

        self.M = np.load(transformation_matrix_path)
        
        # Initialize mediapipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(static_image_mode=False,
                                         max_num_hands=2,
                                         min_detection_confidence=0.3,  # Adjusted for faster performance
                                         min_tracking_confidence=0.3)  # Adjusted for faster performance


        self.mp_drawing = mp.solutions.drawing_utils

        self.frame = None
        self.results = None
        self.frame_count = 0

    def update(self):
        ret, frame = self.cap.read()  # Read the frame from the camera
        if not ret:
            print("Failed to capture frame")
            return False

        # Increment frame count
        self.frame_count += 1


        # Process every nth frame to reduce load
        if self.frame_count % 2 != 0:  # Process every second frame
            return True

        if not ret:
            print("Failed to capture frame")
            return False

        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Run inference for hand detection
        self.results = self.hands.process(rgb_frame)
        self.frame = frame
        return True

    def get_transformed_landmarks(self):
        if self.results and self.results.multi_hand_landmarks:
            transformed_landmarks = []
            for hand_landmarks in self.results.multi_hand_landmarks:
                # Extract landmark coordinates
                landmark_coords = []
                for landmark in hand_landmarks.landmark:
                    x = int(landmark.x * self.frame.shape[1])
                    y = int(landmark.y * self.frame.shape[0])
                    landmark_coords.append([x, y])
                
                landmark_coords = np.array(landmark_coords, dtype=np.float32)
          


                # Apply M transformation to landmark coordinates
                transformed_coords = cv2.perspectiveTransform(np.array([landmark_coords]), self.M)[0]
                
                # Clip coordinates to be within the screen bounds
                transformed_coords = np.clip(transformed_coords, [0, 0], [1280 - 1, 720 - 1])
             

                transformed_landmarks.append(transformed_coords)

            return transformed_landmarks
        return None

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()

    def display_output(self, output_image):
        # Scale the output image to fit the projector's resolution
        scaled_image = cv2.resize(output_image, (1280, 720))
        cv2.imshow("Final Image", scaled_image)
