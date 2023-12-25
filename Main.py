import subprocess
import cv2
import threading
import pyautogui
from plyer import notification
import speech_recognition as sr
import psutil
from cvzone.HandTrackingModule import HandDetector
from cvzone.ClassificationModule import Classifier
import numpy as np
import math
import time
import json
import mediapipe as mp
import pyautogui
import math
from enum import IntEnum
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from google.protobuf.json_format import MessageToDict
import screen_brightness_control as sbcontrol
import tkinter
from tkinter import *
from PIL import ImageTk, Image




global er,imgflg

er = 1


def startpr():
    global er
    a = 4
    if a == 4:

        while True:
            if er==1:
                gest_fun()
                if key == 7:
                    gest_task2()
                else:
                    gest_task()
            else:
                break

def runprg():
    global er
    er = 1
    startpr()
def stop():
    global er
    er = 5

with open('links.json', 'r') as c:
    links = json.load(c)["Links"]

# from watchpoints import watch

root = Tk()
root.configure(bg="#162349")
root.geometry('1000x800')
root.wm_attributes("-topmost", True)
root.resizable(False,False)
heading_label = Label(root, text="“Hand Gesture Controlled System”", font=("Comic Sans MS", 22,"bold"),bg="#162349",fg="white")
heading_label.pack(side=TOP, pady=30)



image_label = Label(root,bg="#162349")
image_label.place(x=300,y=130)

win_label = Label(root, text="       Gesture", font=("Comic Sans MS", 16,"bold"),bg="#162349",fg="white")
win_label.place(x=20,y=100)






b1 = Button(root, text="Start", bd=0, bg="#0071c5", fg="white", font=("Helvetica", 16),command=runprg)
b1.configure(borderwidth=0, relief="flat", highlightthickness=0, pady=10, padx=20,
                     activebackground="#005ca9", activeforeground="white")
b1.place(x=550, y=650)



b2 = Button(root, text="Stop", bd=0, bg="#0071c5", fg="white", font=("Helvetica", 16),command=stop)
b2.configure(borderwidth=0, relief="flat", highlightthickness=0, pady=10, padx=20,
                     activebackground="#005ca9", activeforeground="white")
b2.place(x=700, y=650)



def scoll(scfg):

    # Create a canvas widget to display images
    canvas = Canvas(root, bg="#162349", width=230, height=400, highlightthickness=0)
    canvas.place(x=30, y=150)

    # Create a frame to hold the images on the canvas
    image_frame = Frame(canvas, bg="#162349")
    canvas.create_window((0, 0), window=image_frame, anchor='nw')

    # Add the images to the image frame
    img_paths = ["call.png","ILY.png", "punch.png", "ROCK ON.png", "PEACE.png", "NICE.png", "Thumbs UP.png", "gun.png", "Thumbs DOWN.png", "C.png"]
    image_labels = []
    for i, img_path in enumerate(img_paths):
        if scfg==1:
            img = Image.open("System/"+img_path)
        elif scfg==2:
            img = Image.open("APP/"+img_path)
        img_tk = ImageTk.PhotoImage(img)
        label = Label(image_frame, image=img_tk)
        label.image = img_tk
        label.pack(side=TOP, pady=5, padx=5)
        image_labels.append(label)

    # Configure the canvas to be scrollable
    v_scrollbar = Scrollbar(root, orient='vertical', command=canvas.yview, bg='#162349', bd=0)
    v_scrollbar.place(x=260, y=150, height=400)
    canvas.config(yscrollcommand=v_scrollbar.set)

    # Update the scroll region
    canvas.update_idletasks()
    canvas.config(scrollregion=canvas.bbox('all'))


scoll(1)



cap = cv2.VideoCapture(0)
detector = HandDetector(maxHands=1)
classifier = Classifier("Model/keras_model.h5", "Model/labels.txt")

offset = 20
imgSize = 300

folder = "Data/nice"
counter = 0
micr=0
key = 0
checker = 0
labels = ["call", "ILY", "nice", "peace", "punch", "spiderman", "thumbsup", "thumbsdown", "C", "gun"]
mouse=0
last_gesture = None
start_time = None
same_gesture_count = 0

imgOutput = None
success = None
img = None

gesture1 = ''

def myfun():
    pyautogui.FAILSAFE = False
    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands

    # Gesture Encodings
    class Gest(IntEnum):
        # Binary Encoded
        FIST = 0
        PINKY = 1
        RING = 2
        MID = 4
        LAST3 = 7
        INDEX = 8
        FIRST2 = 12
        LAST4 = 15
        THUMB = 16
        PALM = 31

        # Extra Mappings
        V_GEST = 33
        TWO_FINGER_CLOSED = 34
        PINCH_MAJOR = 35
        PINCH_MINOR = 36

    # Multi-handedness Labels
    class HLabel(IntEnum):
        MINOR = 0
        MAJOR = 1

    # Convert Mediapipe Landmarks to recognizable Gestures
    class HandRecog:

        def __init__(self, hand_label):
            self.finger = 0
            self.ori_gesture = Gest.PALM
            self.prev_gesture = Gest.PALM
            self.frame_count = 0
            self.hand_result = None
            self.hand_label = hand_label

        def update_hand_result(self, hand_result):
            self.hand_result = hand_result

        def get_signed_dist(self, point):
            sign = -1
            if self.hand_result.landmark[point[0]].y < self.hand_result.landmark[point[1]].y:
                sign = 1
            dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x) ** 2
            dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y) ** 2
            dist = math.sqrt(dist)
            return dist * sign

        def get_dist(self, point):
            dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x) ** 2
            dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y) ** 2
            dist = math.sqrt(dist)
            return dist

        def get_dz(self, point):
            return abs(self.hand_result.landmark[point[0]].z - self.hand_result.landmark[point[1]].z)

        # Function to find Gesture Encoding using current finger_state.
        # Finger_state: 1 if finger is open, else 0
        def set_finger_state(self):
            if self.hand_result == None:
                return

            points = [[8, 5, 0], [12, 9, 0], [16, 13, 0], [20, 17, 0]]
            self.finger = 0
            self.finger = self.finger | 0  # thumb
            for idx, point in enumerate(points):

                dist = self.get_signed_dist(point[:2])
                dist2 = self.get_signed_dist(point[1:])

                try:
                    ratio = round(dist / dist2, 1)
                except:
                    ratio = round(dist1 / 0.01, 1)

                self.finger = self.finger << 1
                if ratio > 0.5:
                    self.finger = self.finger | 1

        # Handling Fluctations due to noise
        def get_gesture(self):
            if self.hand_result == None:
                return Gest.PALM

            current_gesture = Gest.PALM
            if self.finger in [Gest.LAST3, Gest.LAST4] and self.get_dist([8, 4]) < 0.05:
                if self.hand_label == HLabel.MINOR:
                    current_gesture = Gest.PINCH_MINOR
                else:
                    current_gesture = Gest.PINCH_MAJOR

            elif Gest.FIRST2 == self.finger:
                point = [[8, 12], [5, 9]]
                dist1 = self.get_dist(point[0])
                dist2 = self.get_dist(point[1])
                ratio = dist1 / dist2
                if ratio > 1.7:
                    current_gesture = Gest.V_GEST
                else:
                    if self.get_dz([8, 12]) < 0.1:
                        current_gesture = Gest.TWO_FINGER_CLOSED
                    else:
                        current_gesture = Gest.MID

            else:
                current_gesture = self.finger

            if current_gesture == self.prev_gesture:
                self.frame_count += 1
            else:
                self.frame_count = 0

            self.prev_gesture = current_gesture

            if self.frame_count > 4:
                self.ori_gesture = current_gesture
            return self.ori_gesture

    # Executes commands according to detected gestures
    class Controller:
        tx_old = 0
        ty_old = 0
        trial = True
        flag = False
        grabflag = False
        pinchmajorflag = False
        pinchminorflag = False
        pinchstartxcoord = None
        pinchstartycoord = None
        pinchdirectionflag = None
        prevpinchlv = 0
        pinchlv = 0
        framecount = 0
        prev_hand = None
        pinch_threshold = 0.3

        def getpinchylv(hand_result):
            dist = round((Controller.pinchstartycoord - hand_result.landmark[8].y) * 10, 1)
            return dist

        def getpinchxlv(hand_result):
            dist = round((hand_result.landmark[8].x - Controller.pinchstartxcoord) * 10, 1)
            return dist

        def changesystembrightness():
            currentBrightnessLv = sbcontrol.get_brightness() / 100.0
            currentBrightnessLv += Controller.pinchlv / 50.0
            if currentBrightnessLv > 1.0:
                currentBrightnessLv = 1.0
            elif currentBrightnessLv < 0.0:
                currentBrightnessLv = 0.0
            sbcontrol.fade_brightness(int(100 * currentBrightnessLv), start=sbcontrol.get_brightness())

        def changesystemvolume():
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            currentVolumeLv = volume.GetMasterVolumeLevelScalar()
            currentVolumeLv += Controller.pinchlv / 50.0
            if currentVolumeLv > 1.0:
                currentVolumeLv = 1.0
            elif currentVolumeLv < 0.0:
                currentVolumeLv = 0.0
            volume.SetMasterVolumeLevelScalar(currentVolumeLv, None)

        def scrollVertical():
            pyautogui.scroll(120 if Controller.pinchlv > 0.0 else -120)

        def scrollHorizontal():
            pyautogui.keyDown('shift')
            pyautogui.keyDown('ctrl')
            pyautogui.scroll(-120 if Controller.pinchlv > 0.0 else 120)
            pyautogui.keyUp('ctrl')
            pyautogui.keyUp('shift')

        # Locate Hand to get Cursor Position
        # Stabilize cursor by Dampening
        def get_position(hand_result):
            point = 9
            position = [hand_result.landmark[point].x, hand_result.landmark[point].y]
            sx, sy = pyautogui.size()
            x_old, y_old = pyautogui.position()
            x = int(position[0] * sx)
            y = int(position[1] * sy)
            if Controller.prev_hand is None:
                Controller.prev_hand = x, y
            delta_x = x - Controller.prev_hand[0]
            delta_y = y - Controller.prev_hand[1]

            distsq = delta_x ** 2 + delta_y ** 2
            ratio = 1
            Controller.prev_hand = [x, y]

            if distsq <= 25:
                ratio = 0
            elif distsq <= 900:
                ratio = 0.07 * (distsq ** (1 / 2))
            else:
                ratio = 2.1
            x, y = x_old + delta_x * ratio, y_old + delta_y * ratio
            return (x, y)

        def pinch_control_init(hand_result):
            Controller.pinchstartxcoord = hand_result.landmark[8].x
            Controller.pinchstartycoord = hand_result.landmark[8].y
            Controller.pinchlv = 0
            Controller.prevpinchlv = 0
            Controller.framecount = 0

        # Hold final position for 5 frames to change status
        def pinch_control(hand_result, controlHorizontal, controlVertical):
            if Controller.framecount == 5:
                Controller.framecount = 0
                Controller.pinchlv = Controller.prevpinchlv

                if Controller.pinchdirectionflag == True:
                    controlHorizontal()  # x

                elif Controller.pinchdirectionflag == False:
                    controlVertical()  # y

            lvx = Controller.getpinchxlv(hand_result)
            lvy = Controller.getpinchylv(hand_result)

            if abs(lvy) > abs(lvx) and abs(lvy) > Controller.pinch_threshold:
                Controller.pinchdirectionflag = False
                if abs(Controller.prevpinchlv - lvy) < Controller.pinch_threshold:
                    Controller.framecount += 1
                else:
                    Controller.prevpinchlv = lvy
                    Controller.framecount = 0

            elif abs(lvx) > Controller.pinch_threshold:
                Controller.pinchdirectionflag = True
                if abs(Controller.prevpinchlv - lvx) < Controller.pinch_threshold:
                    Controller.framecount += 1
                else:
                    Controller.prevpinchlv = lvx
                    Controller.framecount = 0

        def handle_controls(gesture, hand_result):
            x, y = None, None
            if gesture != Gest.PALM:
                x, y = Controller.get_position(hand_result)

            # flag reset
            if gesture != Gest.FIST and Controller.grabflag:
                Controller.grabflag = False
                pyautogui.mouseUp(button="left")

            if gesture != Gest.PINCH_MAJOR and Controller.pinchmajorflag:
                Controller.pinchmajorflag = False

            if gesture != Gest.PINCH_MINOR and Controller.pinchminorflag:
                Controller.pinchminorflag = False

            # implementation
            if gesture == Gest.V_GEST:
                Controller.flag = True
                pyautogui.moveTo(x, y, duration=0.1)

            elif gesture == Gest.FIST:
                global gesture1
                gesture1 = 'FIST'
                if not Controller.grabflag:
                    Controller.grabflag = True

                #     pyautogui.mouseDown(button="left")
                # pyautogui.moveTo(x, y, duration=0.1)

            elif gesture == Gest.MID and Controller.flag:
                pyautogui.click()
                Controller.flag = False

            elif gesture == Gest.INDEX and Controller.flag:
                pyautogui.click(button='right')
                Controller.flag = False

            elif gesture == Gest.TWO_FINGER_CLOSED and Controller.flag:
                pyautogui.doubleClick()
                Controller.flag = False

            elif gesture == Gest.PINCH_MINOR:
                if Controller.pinchminorflag == False:
                    Controller.pinch_control_init(hand_result)
                    Controller.pinchminorflag = True

                Controller.pinch_control(hand_result, Controller.scrollHorizontal, Controller.scrollVertical)

            elif gesture == Gest.PINCH_MAJOR:
                if Controller.pinchmajorflag == False:
                    Controller.pinch_control_init(hand_result)
                    Controller.pinchmajorflag = True

                Controller.pinch_control(hand_result, Controller.changesystembrightness, Controller.changesystemvolume)

    '''
    ----------------------------------------  Main Class  ----------------------------------------
        Entry point of Gesture Controller
    '''

    class GestureController:
        gc_mode = 0

        CAM_HEIGHT = None
        CAM_WIDTH = None
        hr_major = None  # Right Hand by default
        hr_minor = None  # Left hand by default
        dom_hand = True
        global cap
        def __init__(self):
            global cap
            GestureController.gc_mode = 1
            # self.cap = cap
            # GestureController.cap = cv2.VideoCapture(0)
            GestureController.CAM_HEIGHT = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            GestureController.CAM_WIDTH = cap.get(cv2.CAP_PROP_FRAME_WIDTH)

        def classify_hands(results):
            left, right = None, None
            try:
                handedness_dict = MessageToDict(results.multi_handedness[0])
                if handedness_dict['classification'][0]['label'] == 'Right':
                    right = results.multi_hand_landmarks[0]
                else:
                    left = results.multi_hand_landmarks[0]
            except:
                pass

            try:
                handedness_dict = MessageToDict(results.multi_handedness[1])
                if handedness_dict['classification'][0]['label'] == 'Right':
                    right = results.multi_hand_landmarks[1]
                else:
                    left = results.multi_hand_landmarks[1]
            except:
                pass

            if GestureController.dom_hand == True:
                GestureController.hr_major = right
                GestureController.hr_minor = left
            else:
                GestureController.hr_major = left
                GestureController.hr_minor = right

        def start(self):
            global cap
            handmajor = HandRecog(HLabel.MAJOR)
            handminor = HandRecog(HLabel.MINOR)
            global success, img , gesture1
            with mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
                while cap.isOpened() and GestureController.gc_mode:
                    success, img = cap.read()
                    if gesture1 == 'FIST':
                        gesture1 = ''
                        return
                    if not success:
                        print("Ignoring empty camera frame.")
                        continue

                    img = cv2.cvtColor(cv2.flip(img, 1), cv2.COLOR_BGR2RGB)
                    img.flags.writeable = False
                    results = hands.process(img)

                    img.flags.writeable = True
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                    if results.multi_hand_landmarks:
                        GestureController.classify_hands(results)
                        handmajor.update_hand_result(GestureController.hr_major)
                        handminor.update_hand_result(GestureController.hr_minor)

                        handmajor.set_finger_state()
                        handminor.set_finger_state()
                        gest_name = handminor.get_gesture()

                        if gest_name == Gest.PINCH_MINOR:
                            Controller.handle_controls(gest_name, handminor.hand_result)

                        else:
                            gest_name = handmajor.get_gesture()
                            Controller.handle_controls(gest_name, handmajor.hand_result)

                        for hand_landmarks in results.multi_hand_landmarks:
                            mp_drawing.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS, mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=5, circle_radius=1),mp_drawing.DrawingSpec(color=(128, 0, 128), thickness=5))
                    else:
                        Controller.prev_hand = None
                    img_tk = PhotoImage(data=cv2.imencode('.png', img)[1].tobytes())

                    # Update the label with the new image
                    image_label.config(image=img_tk)

                    # Store a reference to the PhotoImage object to prevent it from being garbage collected
                    image_label.image = img_tk

                    # Update the GUI
                    root.update()
                    cv2.waitKey(1)
                    # cv2.imshow('Output', img)
                    if cv2.waitKey(5) & 0xFF == 13:
                        break
            cap.release()
            cv2.destroyAllWindows()

    # uncomment to run directly
    gc1 = GestureController()
    gc1.start()


def typeW():

            notification.notify(title="Mic On", message="Speak Now")
            r = sr.Recognizer()

            with sr.Microphone() as source:
                audio = r.listen(source, timeout=5, phrase_time_limit=5)



            try:
                text = r.recognize_google(audio)
                pyautogui.typewrite(text)
                pyautogui.typewrite(" ")

            except:
                pass
                notification.notify(title="Something went wrong", message="Pardon please..")




def gest_task():
    global checker, key,mouse
    if checker != key:

        print(checker, " ", key)
        checker = key
        if key == 1:
            if links['Brave'] not in (p.name() for p in psutil.process_iter()):
                subprocess.Popen(links['Brave'])

        elif key == 2:
            if links['Exel'] not in (p.name() for p in psutil.process_iter()):
                subprocess.Popen(links['Exel'])


        elif key == 3:
            if links['Ppt'] not in (p.name() for p in psutil.process_iter()):
                subprocess.Popen(links['Ppt'])
            # time.sleep(5)

        elif key == 5:
            if links['Word'] not in (p.name() for p in psutil.process_iter()):
                subprocess.Popen(links['Word'])

        elif key == 6:
            if links['notepad'] not in (p.name() for p in psutil.process_iter()):
                subprocess.Popen(links['notepad'])
        elif key == 7:
            pass
        elif key == 8:
            pass
        elif key == 9:
            command = ''
            subprocess.Popen(['cmd', '/K', command], creationflags=subprocess.CREATE_NEW_CONSOLE)
        elif key == 10:
            if links['File'] not in (p.name() for p in psutil.process_iter()):
                subprocess.Popen(links['File'])
    if mouse==4:
        myfun()
        mouse=0


def gest_task2():
    global checker, key
    global micr,mouse
    notification.notify(title="Locked", message="Sceen Locked")
    scoll(2)
    # Add the images to the image frame

    while True:
        if micr==2:
            typeW()
            micr=0
        if mouse==4:
            myfun()
            mouse=0
        if checker != key:
            print(checker, " ", key)
            checker = key
            if key == 1:
                pyautogui.hotkey('ctrl','s')
            elif key == 5:
               pyautogui.hotkey('ctrl','n')
            elif key == 3:
               pyautogui.hotkey('ctrl','b')
            elif key == 6:
               pyautogui.hotkey('ctrl','j')
            elif key == 9:
               pyautogui.hotkey('ctrl', 'e')
            elif key == 10:
                pyautogui.hotkey('ctrl', 'p')

            elif key == 8:
                notification.notify(title="UnLocked", message="Sceen UnLocked")
                scoll(1)
                break
            else:
                pass


        gest_fun()
    print("Outtttttt")


def gest_fun():
    # print("In main")
    try:
        global start_time, last_gesture, same_gesture_count, key, checker , img , success,micr,mouse
        success, img = cap.read()
        imgOutput = img.copy()
        hands, img = detector.findHands(img)
        try:
            if hands:
                hand = hands[0]
                x, y, w, h = hand['bbox']

                imgWhite = np.ones((imgSize, imgSize, 3), np.uint8) * 255
                imgCrop = img[y - offset:y + h + offset, x - offset:x + w + offset]

                imgCropShape = imgCrop.shape

                aspectRatio = h / w

                if aspectRatio > 1:
                    k = imgSize / h
                    wCal = math.ceil(k * w)
                    imgResize = cv2.resize(imgCrop, (wCal, imgSize))
                    imgResizeShape = imgResize.shape
                    wGap = math.ceil((imgSize - wCal) / 2)
                    imgWhite[:, wGap:wCal + wGap] = imgResize
                    prediction, index = classifier.getPrediction(imgWhite, draw=False)
                    print(prediction, index)

                else:
                    k = imgSize / w
                    hCal = math.ceil(k * h)
                    imgResize = cv2.resize(imgCrop, (imgSize, hCal))
                    imgResizeShape = imgResize.shape
                    hGap = math.ceil((imgSize - hCal) / 2)
                    imgWhite[hGap:hCal + hGap, :] = imgResize
                    prediction, index = classifier.getPrediction(imgWhite, draw=False)

                if not start_time:
                    start_time = time.time()

                cv2.rectangle(imgOutput, (x - offset, y - offset - 50),
                              (x - offset + len(labels[index])*50, y - offset - 50 + 50), (255, 0, 255), cv2.FILLED)
                cv2.putText(imgOutput, labels[index], (x, y - 26), cv2.FONT_HERSHEY_COMPLEX, 1.7, (255, 255, 255), 2)
                cv2.rectangle(imgOutput, (x - offset, y - offset),
                              (x + w + offset, y + h + offset), (255, 0, 255), 4)

                # cv2.imshow("ImageCrop", imgCrop)
                # cv2.imshow("ImageWhite", imgWhite)

                gesture = labels[index]

                if gesture == last_gesture:
                    same_gesture_count += 1
                else:
                    last_gesture = gesture
                    same_gesture_count = 0
                    start_time = time.time()

                if same_gesture_count >= 3 and time.time() - start_time >= 3:
                    if last_gesture == 'call':
                        key = 1
                    elif last_gesture == 'ILY':
                        key = 2
                        micr = 2
                    elif last_gesture == 'nice':
                        key = 3
                    elif last_gesture == 'peace':
                        key = 4
                        mouse = 4
                    elif last_gesture == 'punch':
                        key = 5
                    elif last_gesture == 'spiderman':
                        key = 6

                    elif last_gesture == 'thumbsup':
                        key = 7
                    elif last_gesture == 'thumbsdown':
                        key = 8
                    elif last_gesture == 'C':
                        key = 9
                    elif last_gesture == 'gun':
                        key = 10

            # gesture_rec()
            # cv2.imshow("Output", imgOutput)
            img_tk = PhotoImage(data=cv2.imencode('.png', imgOutput)[1].tobytes())

            # Update the label with the new image
            image_label.config(image=img_tk)

            # Store a reference to the PhotoImage object to prevent it from being garbage collected
            image_label.image = img_tk

            # Update the GUI
            root.update()
            cv2.waitKey(1)
        except:
            pass
    except:
        pass




def start():
    a = 4





    if a == 4:

        while True:
            gest_fun()
            if key == 7:
                 gest_task2()
            else:
                gest_task()




root.mainloop()

cap.release()
cv2.destroyAllWindows()









