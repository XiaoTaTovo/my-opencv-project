import cv2

def process_line(frame):
    # 【新增实用功能 1：底层动态降维】
    # 树莓派算力有限，不管摄像头送进来多大的原图（如640x480），
    # 我们强行缩放成 320x240。这能让帧率暴涨 2-3 倍，且完全不影响巡线精度！
    frame = cv2.resize(frame, (320, 240))
    
    # 1. 自动获取宽高
    h, w = frame.shape[:2] 
    
    # 2. 截取下半部分 ROI (忽略远处的干扰背景)
    roi_start = int(h * 0.5)
    roi = frame[roi_start:h, :]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # ================= 【调试核心区 1】 =================
    threshold_value = 100 
    # ====================================================
    ret, binary = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY_INV)

    # 实车比赛时绝对不要 imshow，调试时可以解开
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
    error = 0            # 【融合新增】：偏差值，默认为0
    
    if best_contour is not None:
        # 面积过滤：如果最大面积太小，说明是噪点
        if max_area > 100: 
            rx, ry, rw, rh = cv2.boundingRect(best_contour)
            width_ratio = rw / w 
            
            # 比例判定：大于 0.55 (55%) 认为是遇到了特殊横线/路口
            if width_ratio > 0.55:
                vision_cmd = 100
                
            # 画出轮廓外接矩形（蓝色）
            cv2.rectangle(roi, (rx, ry), (rx+rw, ry+rh), (255, 0, 0), 2)
            
            # ================= 【融合核心区：计算偏差】 =================
            # 用图像矩求出黑线的真实物理重心
            M = cv2.moments(best_contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                # 计算偏差：黑线中心 x坐标 减去 屏幕中心(w/2)
                # 如果线在屏幕偏左，cx 较小，error 为负数
                # 如果线在屏幕偏右，cx 较大，error 为正数
                center_x = int(w / 2)
                error = cx - center_x
                
                # 画出质心红点
                cv2.circle(roi, (cx, cy), 5, (0, 0, 255), -1)
            # ==============================================================
        else:
            vision_cmd = 101 # 面积太小，视为丢失目标
    else:
         vision_cmd = 101    # 没找到任何有效轮廓
         
    # 5. 【现场调试数据面板】
    cv2.putText(frame, f"Thresh: {threshold_value}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    cv2.putText(frame, f"Max Area: {int(max_area)}", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    cv2.putText(frame, f"W-Ratio: {width_ratio:.2f}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    
    # 【新增】打印误差 Error，方便你校准
    cv2.putText(frame, f"Error: {error}", (10, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
    
    cmd_color = (0, 255, 0) if vision_cmd == 0 else (0, 0, 255)
    cv2.putText(frame, f"STM32 CMD: {vision_cmd}", (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, cmd_color, 2)
         
    return frame, vision_cmd, error