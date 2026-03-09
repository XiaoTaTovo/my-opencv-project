import cv2
import time
from QRcode.recognize import process_qr
from Serial.communicate import SerialManager
from Line.line_track import process_line
def main():
    serial_manager = SerialManager(port='COM6', baudrate=115200)
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,240)
    print("📷 摄像头已启动，开始实时检测...")
    prev_frame_time=0
    last_qr_send_time=0
    last_line_send_time=0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("获取画面失败")
            break
        new_frame_time=time.time()
        fps=1/(new_frame_time-prev_frame_time)
        prev_frame_time=new_frame_time
        print(f"实时帧率:{int(fps)}")


        # --- 【未来添加巡线逻辑的地方】 ---
        # 以后你可以写一个 frame, line_error = process_line(frame)
        # 然后把 line_error 通过串口发出去

        # frame, line_error = process_line(frame)
        # print(f"识别到误差: {line_error}")
        # current_time = time.time()
        # serial_manager.send_line_error(line_error)
           




        # ---------------------------------
        frame, found_texts = process_qr(frame)
        has_valid_qr = False  # 🚩 新增：先定一个标志位，默认没找到,确定最高优先级
        for text in found_texts:
            if text in ['2', '3']:
                print(f"识别到二维码: {text}")
                if new_frame_time - last_qr_send_time > 0.5:
                    serial_manager.send_qr_data(text)
                    last_qr_send_time = new_frame_time
                has_valid_qr=True
                break
        if not has_valid_qr:
            # 如果没有找到有效的二维码，则处理线
            if(time.time()-last_qr_send_time>2):
                # 如果超过两秒没有发送过二维码
                frame,vision_cmd = process_line(frame)
                if vision_cmd==0:
                    print("正常巡线")
                    serial_manager.send_vision_cmd(vision_cmd)   

                else:
                    print(f"识别到特殊值:{vision_cmd}")
                    if new_frame_time - last_line_send_time > 2.0:
                        serial_manager.send_vision_cmd(vision_cmd)   
                        last_line_send_time=new_frame_time

        cv2.imshow("Robot Vision Main", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("🛑 收到退出指令，正在关闭系统...")
            break
    cap.release()
    cv2.destroyAllWindows()
    serial_manager.close()

if __name__ == "__main__":
    main()
        