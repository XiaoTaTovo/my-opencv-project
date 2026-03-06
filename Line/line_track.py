import cv2

def process_line(frame):
    # 1. 截取与预处理
    roi = frame[300:480, :]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    ret, binary = cv2.threshold(gray,100, 255, cv2.THRESH_BINARY_INV )
    cv2.imshow("Binary View", binary)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 2. 找最大轮廓
    max_area = 0
    best_contour = None
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > max_area:
            max_area = area
            best_contour = cnt
            
    """ # 3. 计算偏差与可视化
    error = 0  # 设定默认偏差（防止丢线时报错） """
    # 3. 寻找特殊特征（替代原来的计算偏差）
    vision_cmd = 0  # 默认发送 0，代表正常，啥事没有
    
    # 保护层1：确保真的找到了至少一个轮廓
    if best_contour is not None:
        M = cv2.moments(best_contour)
        # 保护层2：确保面积不为 0
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"]) # 顺便算一下 y 坐标，为了画图
            
            # error = cx - 320 # 计算真实偏差
            # 获取这个最大轮廓的外接矩形
            x, y, w, h = cv2.boundingRect(best_contour)
            if(w>320):
                vision_cmd=100
            if(max_area<500):
                vision_cmd=101
            # --- 可视化部分（方便你在电脑上看效果） ---
            # cv2.drawContours：画出找到的轮廓边界（绿色）
            cv2.drawContours(roi, [best_contour], -1, (0, 255, 0), 2)
            # cv2.circle：在中心点 (cx, cy) 画一个实心圆点（红色）
            cv2.circle(roi, (cx, cy), 5, (0, 0, 255), -1) 
    else:
         vision_cmd=101      
    # 返回处理后的画面和算出的偏差值
    # return frame, error
    return frame,vision_cmd