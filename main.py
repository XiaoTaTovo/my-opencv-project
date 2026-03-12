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
    last_vision_cmd = -1  # 🚩【新增】：用于记录上一次发送的视觉指令，初始给个不存在的值
    frame_counter = 0  # 🚩【新增】：在 while 循环外，添加一个帧计数器
    while True:
        ret, frame = cap.read()
        if not ret:
            print("获取画面失败")
            break
        frame_counter += 1  # 🚩【新增】：每次循环，计数器加 1
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
        found_texts = [] # 🚩【新增】：给它一个默认的空列表。防止跳过二维码检测时报错
        if frame_counter % 3 == 0: 
        # 🚩【新增】：用 if 语句包裹，取余数。如果是 3，就是每 3 帧检测一次；如果是 5，就是每 5 帧检测一次。
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
            # 如果超过两秒没有发送过二维码，再处理巡线
            if (new_frame_time - last_qr_send_time > 2):
                frame, vision_cmd = process_line(frame)
                
                # 🚩 核心逻辑优化：状态一旦改变，立刻发送，保证主控第一时间响应零延迟！
                if vision_cmd != last_vision_cmd:
                    if vision_cmd == 0:
                        print("✅ 恢复正常巡线")
                    elif vision_cmd == 100:
                        print(f"🛑 突发：识别到特殊横线: {vision_cmd}")
                    elif vision_cmd == 101:
                        print(f"⚠️ 突发：丢失目标！: {vision_cmd}")
                        
                    serial_manager.send_vision_cmd(vision_cmd)
                    last_line_send_time = new_frame_time
                    last_vision_cmd = vision_cmd  # 更新当前状态
                    
                # 🚩 如果状态没变（处于持续状态中），再应用你写的频率限制
                else:
                    if vision_cmd == 0:
                        # 正常巡线持续中：降频到 20Hz 发送，防止撑爆 STM32 串口
                        if new_frame_time - last_line_send_time > 0.05: 
                            serial_manager.send_vision_cmd(vision_cmd)
                            last_line_send_time = new_frame_time
                            
                    elif vision_cmd == 101:
                        # 持续丢失目标中：10Hz 高频报警
                        if new_frame_time - last_line_send_time > 0.1:
                            serial_manager.send_vision_cmd(vision_cmd)
                            last_line_send_time = new_frame_time
                            
                    elif vision_cmd == 100:
                        # 持续踩在特殊横线上：2秒内绝对不重复发送，防止主控多次触发停止逻辑
                        if new_frame_time - last_line_send_time > 2.0:
                            serial_manager.send_vision_cmd(vision_cmd)
                            last_line_send_time = new_frame_time
        #到时候注释掉这四行
        cv2.imshow("Robot Vision Main", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("🛑 收到退出指令，正在关闭系统...")
            break
        #没错就是到这里
    cap.release()
    cv2.destroyAllWindows()
    serial_manager.close()

if __name__ == "__main__":
    main()
        