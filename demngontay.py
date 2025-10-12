# Tên file: demngontay.py (Phiên bản hiển thị text)

import cv2
import mediapipe as mp

class HandDetector:
    """
    Lớp để phát hiện bàn tay và đếm số ngón tay đang giơ.
    Sử dụng thư viện MediaPipe.
    - Chức năng:
        + Phát hiện tối đa 2 bàn tay.
        + Đếm chính xác số ngón tay cho cả tay trái và tay phải.
    """
    def __init__(self, static_mode=False, max_hands=2, detection_con=0.5, track_con=0.5):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=static_mode,
            max_num_hands=max_hands,
            min_detection_confidence=detection_con,
            min_tracking_confidence=track_con
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.tip_ids = [4, 8, 12, 16, 20]

    def find_hands(self, frame, draw=True):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(rgb_frame)

        if self.results.multi_hand_landmarks and draw:
            for hand_landmarks in self.results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
        return frame

    def get_landmarks(self, frame, hand_no=0):
        landmark_list = []
        if self.results.multi_hand_landmarks and len(self.results.multi_hand_landmarks) > hand_no:
            hand = self.results.multi_hand_landmarks[hand_no]
            for id, lm in enumerate(hand.landmark):
                h, w, c = frame.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                landmark_list.append([id, cx, cy])
        return landmark_list

    def count_fingers(self, landmarks, handedness):
        if len(landmarks) == 0:
            return 0
        fingers = []
        if handedness == 'Right':
            if landmarks[self.tip_ids[0]][1] < landmarks[self.tip_ids[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        else:
            if landmarks[self.tip_ids[0]][1] > landmarks[self.tip_ids[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)

        for id in range(1, 5):
            if landmarks[self.tip_ids[id]][2] < landmarks[self.tip_ids[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        return fingers.count(1)

# --- PHẦN CHẠY THỬ ĐÃ QUAY VỀ HIỂN THỊ BẰNG VĂN BẢN ---
def main():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("LỖI: KHÔNG THỂ MỞ WEBCAM.")
        return

    detector = HandDetector(max_hands=2)

    while True:
        success, frame = cap.read()
        if not success:
            break
        
        frame = cv2.flip(frame, 1)
        frame = detector.find_hands(frame)
        
        total_finger_count = 0
        if detector.results.multi_hand_landmarks:
            for i in range(len(detector.results.multi_hand_landmarks)):
                handedness = detector.results.multi_handedness[i].classification[0].label
                landmarks = detector.get_landmarks(frame, hand_no=i)
                if landmarks:
                    finger_count = detector.count_fingers(landmarks, handedness)
                    total_finger_count += finger_count
        
        # Hiển thị tổng số ngón tay bằng văn bản
        cv2.putText(frame, f'Tong so ngon: {total_finger_count}', (30, 70), 
                    cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)

        cv2.imshow("Hand Detector - Text Version", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()