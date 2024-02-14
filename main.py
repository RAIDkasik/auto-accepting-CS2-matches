from utils.grabbers.mss import Grabber
from utils.fps import FPS
from utils.controls.mouse.win32 import MouseControls
from utils.win32 import WinHelper
import keyboard
from utils.time import sleep
import cv2
import multiprocessing
import numpy as np
import pyautogui
from utils.nms import non_max_suppression_fast
# CONFIG
GAME_WINDOW_TITLE = "Counter-Strike 2"  # game window
ACTIVATION_HOTKEY = 68
_show_cv2 = True

# used by the script
game_window_rect = WinHelper.GetWindowRect(GAME_WINDOW_TITLE, (8, 30, 16, 39))  # cut the borders
_activated = False

def grab_process(q):
    grabber = Grabber()

    while True:
        img = grabber.get_image({"left": int(game_window_rect[0]), "top": int(game_window_rect[1])+50, "width": int(game_window_rect[2]), "height": int(game_window_rect[3])})

        if img is None:
            continue

        q.put_nowait(img)
        q.join()


def cv2_process(q):
    global _show_cv2, game_window_rect, _activated

    fps = FPS()
    font = cv2.FONT_HERSHEY_SIMPLEX

    while True:
        if not q.empty():
            img = q.get_nowait()
            q.task_done()

            hue_point = 65
            button_color = ((hue_point, 180, 180), (hue_point + 20, 255, 255)) # HSV
            min_target_size = (50, 50)
            max_target_size = (1000, 1000)

            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, np.array(button_color[0], dtype=np.uint8), np.array(button_color[1], dtype=np.uint8))
            contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            rectangles = []

            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if (w >= min_target_size[0] and h >= min_target_size[1]) and (w <= max_target_size[0] and h <= max_target_size[1]) and _activated:
                    rectangles.append((int(x), int(y), int(w), int(h)))
                    pyautogui.moveTo(int(x)+int(w)/2, int(y)+int(h)*1.5)
                    print(x, y, w, h)
                    pyautogui.click()
                    pyautogui.click()
                    break

            #output
            # masked_img = cv2.bitwise_and(img, img, mask=mask)
            #
            # if _show_cv2:
            #     masked_img = cv2.putText(masked_img, f"{fps():.2f}", (20, 120), font, 1.7, (0, 255, 0), 7, cv2.LINE_AA)
            #
            #     masked_img = cv2.resize(masked_img, (1280, 720))
            #     cv2.imshow("Output", masked_img)
            #     cv2.waitKey(1)


def switch_shoot_state():
    global _activated
    _activated = not _activated  # inverse value


keyboard.add_hotkey(ACTIVATION_HOTKEY, switch_shoot_state)


if __name__ == "__main__":

    q = multiprocessing.JoinableQueue()
    p1 = multiprocessing.Process(target=grab_process, args=(q,))
    p2 = multiprocessing.Process(target=cv2_process, args=(q,))

    p1.start()
    p2.start()



