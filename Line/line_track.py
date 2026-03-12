import cv2

def process_line(frame):
    # 1. 自动获取宽高
    h, w = frame.shape[:2] 
    
    # 2. 截取下半部分 ROI (忽略远处的干扰背景)
    roi_start = int(h * 0.5)
    roi = frame[roi_start:h, :]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # ================= 【调试核心区 1】 =================
    # 比赛现场光线变化时，优先修改这个数字！
    threshold_value = 100 
    # ====================================================
    ret, binary = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY_INV)

    # 强烈建议：现场调参时，解除下面这行注释。
    # 看着弹出的黑白画面调 threshold_value，直到黑线变成完整的白块，且没有大量噪点。
    # cv2.imshow("Binary View", binary)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 3. 找最大轮廓
    max_area = 0
    best_contour = None
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > max_area:
            max_area = area
            best_contour = cnt
            
    # 4. 状态判定逻辑 (准备发送给 STM32 主控的指令)
    vision_cmd = 0       # 默认指令：正常
    width_ratio = 0.0    # 宽度比例初始值
    
    if best_contour is not None:
        # 面积过滤：如果最大面积太小，说明是噪点，直接当做没看到线
        if max_area > 100: 
            # rx, ry 是左上角坐标，rw 是宽，rh 是高
            rx, ry, rw, rh = cv2.boundingRect(best_contour)
            
            # 核心：计算当前黑色轮廓的宽度，占整个屏幕宽度的百分之多少
            width_ratio = rw / w 
            
            # ================= 【调试核心区 2】 =================
            # 比例判定：大于 0.75 (75%) 认为是遇到了特殊横线/停止线
            if width_ratio > 0.55:
                vision_cmd = 100
                
            # 在画面上画出轮廓外接矩形（蓝色），方便肉眼确认它框得准不准
            cv2.rectangle(roi, (rx, ry), (rx+rw, ry+rh), (255, 0, 0), 2)
        else:
            vision_cmd = 101 # 面积太小，视为丢失目标
    else:
         vision_cmd = 101    # 没找到任何有效轮廓
         
    # 5. 【现场调试数据面板】（打印在画面左上角）
    # 现场推车时，看着这几个数值变化来微调 threshold_value 和 0.75 那个判断条件
    cv2.putText(frame, f"Thresh: {threshold_value}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    cv2.putText(frame, f"Max Area: {int(max_area)}", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    cv2.putText(frame, f"W-Ratio: {width_ratio:.2f}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    
    # 用不同的颜色显示当前下发的指令，0为绿色，其余为红色预警
    cmd_color = (0, 255, 0) if vision_cmd == 0 else (0, 0, 255)
    cv2.putText(frame, f"STM32 CMD: {vision_cmd}", (10, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.7, cmd_color, 2)
         
    return frame, vision_cmd