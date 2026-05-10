from ultralytics import YOLO
import cv2 
import time
import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

sys.path.append(PARENT_DIR)

from backend.adaAPI import start_mqtt, publish_data


"""
Ý tưởng:
1. nếu đang cooldown → skip

2. detect YOLO → lấy boxes

3. với mỗi box:
    - crop ảnh
    - check front-face
    - match với obj cũ hoặc tạo mới

4. xoá obj cũ (mất >1s)

5. duyệt từng obj:
    nếu:
        now - start_time ≥ 5s
        AND front_count đủ
    → FEED
    → cập nhật last_feed_time
    → break
"""

COOLDOWN_TIME = 10 # thời gian cooldown sau mỗi lần feed (10s)


start_mqtt()
model = YOLO("yolov8n.pt")
model_pose = YOLO("models/check_pose.pt") 
# model_pose = YOLO("yolov8n-pose.pt") 
class obj_pet:
    def __init__(self, x,y, start_time):
        self.x = x
        self.y = y
        self.start_time = start_time
        self.front_count = 0
        self.last_seen = time.time()
        self.img = None # ảnh crop của pet để check chính diện sau này

    def update(self, x,y,img):
        self.x = x
        self.y = y
        self.img = img
        self.last_seen = time.time()





def feed_food(type_pet ):
    print(f">>> ĐANG CHO {type_pet} ĂN<<<")
    if type_pet == "dog":
        publish_data("feed-dog", 1)
    else:
        publish_data("feed-cat", 1)
    
    print("chờ 10s")
    
    
def check_pose(img):
    print(">>> ĐANG KIỂM TRA PET <<<")
    result_pose = model_pose(img, conf=0.5, verbose=False)
    
    img_debug = result_pose[0].plot()
    img_debug_resized = cv2.resize(img_debug, (300, 300))
    cv2.imshow("Debug - Check pose", img_debug_resized)
    
    if len(result_pose[0].boxes) > 0:
        print("T")
        return True
    
    print("F")
    return False 


def match_obj_pet(obj_pet_list, x_center, y_center):
    print(f">>> MATCH OBJ PET: {len(obj_pet_list)} obj đang theo dõi <<<")
    for obj in obj_pet_list:
        # nếu trùng với obj cũ (cùng pet)
        if  (x_center - obj.x)**2 + (y_center - obj.y)**2 < 200**2: # nếu center mới gần center cũ (cùng pet) 
            return obj
    print(">>> KHÔNG TRÙNG VỚI OBJ NÀO, TẠO MỚI <<<")
    return None



#sec: thời gian chạy camera 
#ratio: tỉ lệ diện tích box so với diện tích frame để xác định có vào vùng cho ăn hay không
def runCamera(sec:int = 5,ratio:float = 0.35):
    cam = cv2.VideoCapture(0)
    
    just_feed = False # cờ báo hiệu vừa mới feed xong
    obj_pet_list = [] # danh sách các obj pet đang theo dõi (có thể có nhiều pet cùng lúc)
    last_detection_time = 0
    
    while cam.isOpened():
        ret, frame = cam.read()
        if not ret:
            print("Không thể đọc khung hình từ camera.")
            break
        
        if cv2.waitKey(1) == ord('q'):
            break
        
        result = model(frame,classes=[15,16],conf = 0.5,verbose=False)
        f = result[0].plot()        

        # pet_detected_in_zone = False # Cờ báo hiệu frame hiện tại có pet ở gần không
        
        #dien tich frame goc
        h_frame, w_frame, _ = frame.shape
        area_frame = h_frame * w_frame
        if not just_feed :
            boxes = result[0].boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int,box.xyxy[0])
                area_box = (y2 - y1) * (x2 - x1)
                cls = box.cls[0]
                print(f"Phát hiện đối tượng: {model.names[int(cls)]} ")
                
                # Nếu diện tích box lớn hơn 40% diện tích frame thì là nó đã vào vùng cho ăn
                print(f"Tỉ lệ: {area_box/area_frame:.2f}")
                if area_box / area_frame > ratio:
                    
                    x_center = (x1 + x2) // 2
                    y_center = (y1 + y2) // 2
                    img = frame[y1:y2, x1:x2]
                    obj = match_obj_pet(obj_pet_list, x_center, y_center)
                    if not obj: # nếu không trùng với obj nào thì tạo mới
                        obj = obj_pet(x_center, y_center, time.time())
                        obj_pet_list.append(obj)
                        print(f"new pet và số lượng pet đang theo dõi: {len(obj_pet_list)}")
                    else:
                        obj.update(x_center, y_center,img) 
                        now = time.time()
                        print(f"Đã theo dõi pet {model.names[int(cls)]} được {now - obj.start_time:.2f} giây")
                        if now - obj.start_time >= sec: 
                            if check_pose(img):
                                feed_food(model.names[int(cls)]) 
                                last_detection_time = now 
                                just_feed = True 
                                obj.start_time = now 
                                

                                    

        #check và xoá obj cũ 
        obj_pet_list = [obj for obj in obj_pet_list if time.time() - obj.last_seen <=3] # chỉ giữ lại những obj được phát hiện trong 10s gần nhất
        
        #check cooldown
        if just_feed and time.time() - last_detection_time >= COOLDOWN_TIME:
            just_feed = False 
        
        cv2.imshow("Camera", f)    
                    
    cam.release()
    cv2.destroyAllWindows()
    
runCamera()