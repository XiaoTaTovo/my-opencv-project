import cv2
from pyzbar.pyzbar import decode
from pyzbar.pyzbar import decode, ZBarSymbol  # 🚩 新增引入 ZBarSymbol

def process_qr(frame):
    # decoded_objects = decode(frame)
    # 🚩 核心修改：限定只解码 QRCODE，彻底消除警告，并极大节省 CPU 算力！
    decoded_objects = decode(frame, symbols=[ZBarSymbol.QRCODE])
    found_texts=[]
    for obj in decoded_objects:
        qr_text=obj.data.decode('utf-8')
        found_texts.append(qr_text)
        pts=obj.polygon
        if len(pts) == 4:
            pts=[(pts[i].x,pts[i].y)for i in range(4)]
            cv2.line(frame,pts[0],pts[1],(0,255,0),3)
            cv2.line(frame,pts[1],pts[2],(0,255,0),3)
            cv2.line(frame,pts[2],pts[3],(0,255,0),3)
            cv2.line(frame,pts[3],pts[0],(0,255,0),3)
        cv2.putText(frame,qr_text,(obj.rect.left,obj.rect.top-10),cv2.FONT_HERSHEY_SIMPLEX,0.9,(0,0,255),2)
    return frame,found_texts


