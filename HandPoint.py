import time
import sys
import cv2
import numpy as np
import pyautogui
from mediapipe.python.solutions import drawing_utils as mp_drawing
from mediapipe.python.solutions import hands as mp_hands

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

screen_w, screen_h = pyautogui.size()
cam_w, cam_h = 640, 480

CAM_INDEX = 0


def open_camera(index):
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_h)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


cap = open_camera(CAM_INDEX)
if cap is None:
    sys.exit(f"Tidak bisa membuka kamera index {CAM_INDEX}. Cek koneksi atau ganti CAM_INDEX.")

smoothing_factor = 3.0
frame_reduction_x = 60
frame_reduction_y = 60

curr_x, curr_y = screen_w / 2, screen_h / 2
prev_x, prev_y = screen_w / 2, screen_h / 2

LEFT_CLOSE_THR = 0.28
LEFT_OPEN_THR = 0.42
RIGHT_CLOSE_THR = 0.28
RIGHT_OPEN_THR = 0.42

INTENT_HOLD_TIME = 0.12
CLICK_COOLDOWN = 0.35

last_left_click_time = 0.0
last_right_click_time = 0.0

left_state = "OPEN"
right_state = "OPEN"
left_intent_start = None
right_intent_start = None

BUF_SIZE = 4
left_dist_buffer = []
right_dist_buffer = []

# Kalibrasi palm size: rata-rata dari beberapa frame pertama biar gak noise
palm_calib_samples = []
PALM_CALIB_FRAMES = 20
palm_baseline = None

COLOR_BG = (30, 30, 30)
COLOR_ACCENT = (255, 0, 255)
COLOR_LEFT = (80, 220, 80)
COLOR_RIGHT = (80, 160, 255)
COLOR_SCROLL = (0, 230, 255)
COLOR_DIM = (110, 110, 110)
COLOR_WARN = (0, 165, 255)


def smooth_val(buffer, new_val, size):
    buffer.append(new_val)
    if len(buffer) > size:
        buffer.pop(0)
    return sum(buffer) / len(buffer)


def get_palm_size(lm):
    # rata-rata dua pasang landmark biar lebih stabil dibanding satu pasang
    d1 = np.hypot((lm[0].x - lm[9].x) * cam_w, (lm[0].y - lm[9].y) * cam_h)
    d2 = np.hypot((lm[0].x - lm[17].x) * cam_w, (lm[0].y - lm[17].y) * cam_h)
    return max((d1 + d2) / 2, 1e-6)


def fingers_open(lm):
    return (lm[8].y < lm[6].y and lm[12].y < lm[10].y and
            lm[16].y < lm[14].y and lm[20].y < lm[18].y)


def draw_indicator(frame, x, y, label, active, color):
    box_w, box_h = 100, 24
    bg = color if active else (60, 60, 60)
    txt = (10, 10, 10) if active else COLOR_DIM
    cv2.rectangle(frame, (x, y), (x + box_w, y + box_h), bg, -1)
    cv2.putText(frame, label, (x + 8, y + 17), cv2.FONT_HERSHEY_SIMPLEX, 0.45, txt, 1)


try:
    with mp_hands.Hands(
        model_complexity=0,
        min_detection_confidence=0.75,
        min_tracking_confidence=0.75,
        max_num_hands=1
    ) as hands:

        prev_frame_time = 0.0
        prev_y_scroll = 0
        consecutive_read_fails = 0
        MAX_READ_FAILS = 30

        while True:
            ret, frame = cap.read()
            if not ret:
                consecutive_read_fails += 1
                if consecutive_read_fails > MAX_READ_FAILS:
                    print("Kamera berhenti merespons, keluar.")
                    break
                continue
            consecutive_read_fails = 0

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False
            result = hands.process(rgb_frame)

            h, w = frame.shape[:2]

            cv2.rectangle(frame, (frame_reduction_x, frame_reduction_y),
                          (cam_w - frame_reduction_x, cam_h - frame_reduction_y),
                          COLOR_ACCENT, 1)

            mode_text = "NO HAND DETECTED"
            mode_color = COLOR_DIM
            left_active_now = False
            right_active_now = False
            scroll_active_now = False

            if result.multi_hand_landmarks:
                hand_landmarks = result.multi_hand_landmarks[0]
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(200, 200, 200), thickness=1, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(120, 120, 120), thickness=1)
                )

                lm = hand_landmarks.landmark
                thumb, index, middle, ring, pinky = lm[4], lm[8], lm[12], lm[16], lm[20]

                index_x, index_y = int(index.x * cam_w), int(index.y * cam_h)
                thumb_x, thumb_y = int(thumb.x * cam_w), int(thumb.y * cam_h)
                middle_x, middle_y = int(middle.x * cam_w), int(middle.y * cam_h)

                raw_palm = get_palm_size(lm)

                if palm_baseline is None:
                    palm_calib_samples.append(raw_palm)
                    if len(palm_calib_samples) >= PALM_CALIB_FRAMES:
                        palm_baseline = float(np.median(palm_calib_samples))
                    cv2.putText(frame, "Kalibrasi... tahan tangan di depan kamera",
                                (15, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_WARN, 1)

                palm_size = raw_palm
                all_open = fingers_open(lm)

                if not all_open:
                    target_x = np.interp(index_x, (frame_reduction_x, cam_w - frame_reduction_x), (0, screen_w))
                    target_y = np.interp(index_y, (frame_reduction_y, cam_h - frame_reduction_y), (0, screen_h))
                    target_x = np.clip(target_x, 0, screen_w - 1)
                    target_y = np.clip(target_y, 0, screen_h - 1)

                    curr_x = prev_x + (target_x - prev_x) / smoothing_factor
                    curr_y = prev_y + (target_y - prev_y) / smoothing_factor
                    pyautogui.moveTo(int(curr_x), int(curr_y), _pause=False)
                    prev_x, prev_y = curr_x, curr_y

                    cv2.circle(frame, (index_x, index_y), 12, COLOR_ACCENT, 2)
                    mode_text = "CURSOR MODE"
                    mode_color = COLOR_ACCENT

                if all_open:
                    mode_text = "SCROLL MODE"
                    mode_color = COLOR_SCROLL
                    scroll_active_now = True

                    base_y = int(lm[0].y * cam_h)
                    if prev_y_scroll == 0:
                        prev_y_scroll = base_y

                    scroll_dist = prev_y_scroll - base_y
                    if abs(scroll_dist) > 8:
                        pyautogui.scroll(int(scroll_dist * 3))
                        prev_y_scroll = base_y
                else:
                    prev_y_scroll = 0

                    middle_curled = middle.y > lm[10].y
                    raw_left = np.hypot(index_x - thumb_x, index_y - thumb_y) / palm_size
                    sm_left = smooth_val(left_dist_buffer, raw_left, BUF_SIZE)

                    now = time.time()

                    if left_state == "OPEN":
                        if sm_left < LEFT_CLOSE_THR and middle_curled:
                            left_state = "ARMING"
                            left_intent_start = now
                    elif left_state == "ARMING":
                        if sm_left >= LEFT_CLOSE_THR or not middle_curled:
                            left_state = "OPEN"
                        elif now - left_intent_start >= INTENT_HOLD_TIME:
                            if now - last_left_click_time > CLICK_COOLDOWN:
                                pyautogui.click()
                                last_left_click_time = now
                            left_state = "CLICKED"
                    elif left_state == "CLICKED":
                        if sm_left > LEFT_OPEN_THR:
                            left_state = "OPEN"

                    left_active_now = left_state in ("ARMING", "CLICKED")
                    if left_active_now:
                        cv2.circle(frame, (int((index_x + thumb_x) / 2), int((index_y + thumb_y) / 2)),
                                   14, COLOR_LEFT, cv2.FILLED)

                    index_curled = index.y > lm[6].y
                    raw_right = np.hypot(middle_x - thumb_x, middle_y - thumb_y) / palm_size
                    sm_right = smooth_val(right_dist_buffer, raw_right, BUF_SIZE)

                    if right_state == "OPEN":
                        if sm_right < RIGHT_CLOSE_THR and index_curled:
                            right_state = "ARMING"
                            right_intent_start = now
                    elif right_state == "ARMING":
                        if sm_right >= RIGHT_CLOSE_THR or not index_curled:
                            right_state = "OPEN"
                        elif now - right_intent_start >= INTENT_HOLD_TIME:
                            if now - last_right_click_time > CLICK_COOLDOWN:
                                pyautogui.rightClick()
                                last_right_click_time = now
                            right_state = "CLICKED"
                    elif right_state == "CLICKED":
                        if sm_right > RIGHT_OPEN_THR:
                            right_state = "OPEN"

                    right_active_now = right_state in ("ARMING", "CLICKED")
                    if right_active_now:
                        cv2.circle(frame, (int((middle_x + thumb_x) / 2), int((middle_y + thumb_y) / 2)),
                                   14, COLOR_RIGHT, cv2.FILLED)

                    if mode_text == "CURSOR MODE" and (left_active_now or right_active_now):
                        mode_text = "CLICK MODE"
                        mode_color = COLOR_LEFT if left_active_now else COLOR_RIGHT

            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, 55), COLOR_BG, -1)
            cv2.rectangle(overlay, (0, h - 40), (w, h), COLOR_BG, -1)
            cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

            cv2.putText(frame, mode_text, (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, mode_color, 2)

            new_frame_time = time.time()
            fps = 1 / (new_frame_time - prev_frame_time) if prev_frame_time else 0
            prev_frame_time = new_frame_time
            cv2.putText(frame, f"FPS {int(fps)}", (w - 95, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, COLOR_DIM, 1)

            draw_indicator(frame, 15, h - 32, "L-CLICK", left_active_now, COLOR_LEFT)
            draw_indicator(frame, 125, h - 32, "R-CLICK", right_active_now, COLOR_RIGHT)
            draw_indicator(frame, 235, h - 32, "SCROLL", scroll_active_now, COLOR_SCROLL)

            cv2.putText(frame, "Press ESC to exit", (w - 165, h - 14),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLOR_DIM, 1)

            cv2.imshow("Air Mouse Controller", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

except KeyboardInterrupt:
    pass
finally:
    cap.release()
    cv2.destroyAllWindows()
