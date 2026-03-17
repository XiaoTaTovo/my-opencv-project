import cv2
import time
from QRcode.recognize import process_qr
from Serial.communicate import SerialManager
from Line.line_track import process_line
import threading  # 🚩 引入多线程库
def stm32_listener_thread(serial_manager):
    global qr_found, stm32_running_task
    ser = serial_manager.ser
    
    print("🎧 后台串口监听线程已启动...")
    while True:
        try:
            # 如果串口没打开，或者缓冲区没数据，就稍微歇一下，防止 CPU 满载
            if ser is None or not ser.is_open or ser.in_waiting < 6:
                time.sleep(0.01)
                continue
                
            # 寻找帧头 0xAA
            if ser.read(1)[0] == 0xAA:
                packet = ser.read(5) # 读取剩下的 5 个字节
                
                # 确保读全了，并且帧尾是 0xFF
                if len(packet) == 5 and packet[4] == 0xFF:
                    cmd_type = packet[0]
                    data_len = packet[1]
                    task_num = packet[2]
                    checksum = packet[3]
                    
                    # 校验和比对
                    if (cmd_type + data_len + task_num) & 0xFF == checksum:
                        if cmd_type == 0x04: # 收到 0x04 任务指令！
                            print(f"\n📢 [硬件通知] 收到单片机指令！目标任务: {task_num}")
                            stm32_running_task = task_num
                            
                            # 如果是任务 1 或 4，直接解除二维码封印，强制进入巡线！
                            if task_num in [1, 4]:
                                qr_found = True
                            elif task_num == 0:
                                # 收到 0，说明单片机按键停车了，我们可以重置状态
                                qr_found = False
        except Exception as e:
            # 遇到串口断开等错误，静默处理，不要让线程崩溃
            time.sleep(0.1)
def main():
    serial_manager = SerialManager(port='COM4', baudrate=115200)
    # 🚩 启动后台监听线程 (daemon=True 表示主程序退出时，这个线程自动跟着死掉)
    listener = threading.Thread(target=stm32_listener_thread, args=(serial_manager,), daemon=True)
    listener.start()
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    print("📷 摄像头已启动，开始实时检测...")
    
    prev_frame_time = 0  #上一帧的时间
    last_line_send_time = 0  #线处理的时间，用于控制发送频率
    last_vision_cmd = -1  #发给单片机的信息
    frame_counter = 0     
    
    # 🚩 这个变量是决定小车生死的钥匙！
    qr_found = False     #决定识别二维码与否 

    while True:
        ret, frame = cap.read()
        if not ret:
            print("获取画面失败")
            break
            
        frame_counter += 1  
        new_frame_time = time.time()
        fps = 1 / (new_frame_time - prev_frame_time)
        prev_frame_time = new_frame_time
        print(f"实时帧率:{int(fps)}") # 调试时可看，实车比赛建议注释掉省算力

        # ==========================================================
        # 阶段 1：起跑线准备 —— 全心全意找二维码
        # ==========================================================
        if not qr_found:
            # 此时车没动，我们不跑 process_line，只跑二维码识别
            frame, found_texts = process_qr(frame)
            # 🚩 核心修改：限定只解码 QRCODE，彻底消除警告，并极大节省 CPU 算力！
            for text in found_texts:
                if text in ['2', '3']:
                    print(f"🎯 识别到二维码: {text}，任务启动！")
                    serial_manager.send_qr_data(text) # 告诉单片机任务几
                    
                    qr_found = True # 🚩【核心】：找到了！永远关闭二维码模式！
                    last_vision_cmd = 0 # 初始化巡线状态
                    time.sleep(0.5) # 稍微停顿一下，让单片机消化指令
                    break # 跳出寻找循环，进入下一帧
                    
        # ==========================================================
        # 阶段 2：比赛进行中 —— 屏蔽二维码，疯狂巡线！
        # ==========================================================
        else:
            # 此时二维码模块彻底休眠！所有 CPU 算力都拿来算这行代码：
            frame, vision_cmd, line_error = process_line(frame)
            
            # 【动作A：发误差】高频发送！让单片机的 PID 时刻微调方向
            serial_manager.send_line_error(line_error)
            
            # 【动作B：发指令】状态突变时发送！告诉单片机到了 B、C、D 点
            if vision_cmd != last_vision_cmd:
                # 如果状态和上一帧不一样（比如刚从正常 0 踩到横线 100）
                if vision_cmd == 0:
                    print("✅ 离开路口，恢复正常巡线")
                elif vision_cmd == 100:
                    print("🛑 突发：踩到特殊横线/顶点！通知单片机变段！")
                elif vision_cmd == 101:
                    print("⚠️ 突发：丢失目标！")
                    
                # 状态突变，必须立刻通知单片机，零延迟！
                serial_manager.send_vision_cmd(vision_cmd)
                last_line_send_time = new_frame_time
                last_vision_cmd = vision_cmd  
                
            else:
                # 如果状态没变（比如一直踩在横线上 100，或者一直正常 0）
                if vision_cmd == 100:
                    # 持续踩在横线上：必须冷却！2秒内绝对不重复发送 100！
                    # 防止单片机的 task.c 瞬间把 B、C、D 点全跳过去了
                    if new_frame_time - last_line_send_time > 2.0:
                        serial_manager.send_vision_cmd(vision_cmd)
                        last_line_send_time = new_frame_time
                        
                elif vision_cmd == 101:
                    # 持续丢失中：1秒发一次 101 报警
                    if new_frame_time - last_line_send_time > 1.0:
                        serial_manager.send_vision_cmd(vision_cmd)
                        last_line_send_time = new_frame_time
                        
                # 注意：如果 vision_cmd == 0 (正常)，且没变，我们【不发送】0。
                # 因为正常巡线时，单片机只需要 error 就行了，没必要用 0 去塞满串口。

        # ----------------------------------------------------------
        # 画面显示 (实车比赛时，强烈建议把下面这两行也注释掉，帧率会飙升)
        cv2.imshow("Robot Vision Main", frame)
        key=cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("🛑 收到退出指令，正在关闭系统...")
            break
        # 🚩 【新增：上帝模式开关】按下键盘的 '1'，强制跳过二维码，进入巡线！
        elif key == ord('1'): 
            if not qr_found:
                print("🚀 [上帝模式] 强制跳过二维码，进入纯巡线模式！(用于测试任务1)")
                qr_found = True
                last_vision_cmd = 0

    cap.release()
    cv2.destroyAllWindows()
    serial_manager.close()

if __name__ == "__main__":
    main()
        