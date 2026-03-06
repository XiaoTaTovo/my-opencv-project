import serial
class SerialManager:
    def __init__(self,port='COM3',baudrate=115200):
        self.ser=None#初始化串口对象为None,self.让变量在函数运行结束后不被回收,让同一个类里的不同函数（比如 __init__、send、close）能共同操作同一个串口。
        try:
            self.ser = serial.Serial(port,baudrate,timeout=0.1)
            print(f"成功连接到串口 {port}")
        except Exception as e:
            print(f"无法连接到串口 {port},错误: {e}")
    def send_qr_data(self,qr_text):
        if self.ser is None or not self.ser.is_open:
            return
        try:
            data_content = int(qr_text)#将二维码内容转换为整数
        except ValueError:
            return
        header =0xAA#帧头
        cmd_type=0x02#指令类型(0x02表示二维码)
        data_len=0x01#数据长度
        checksum=(cmd_type+data_len+data_content)&0xFF#校验:&的逻辑是全1才为1,这样可以截断超过8位的数据,接收方要再算一遍
        tail=0xFF
        packet=bytes([header,cmd_type,data_len,data_content,checksum,tail])
        self.ser.write(packet)
        hex_str=' '.join([f'{b:02X}'for b in packet])
        print(f"发送串口数据: {hex_str}")
    def send_vision_cmd(self,vision_cmd):
        if self.ser is None or not self.ser.is_open:
            return
        
        header =0xAA#帧头
        cmd_type=0x01#指令类型(0x01表示任务类型)
        data_len=0x01#数据长度
        checksum=(cmd_type+data_len+vision_cmd)&0xFF#校验:&的逻辑是全1才为1,这样可以截断超过8位的数据,接收方要再算一遍
        tail=0xFF
        packet=bytes([header,cmd_type,data_len,vision_cmd,checksum,tail])
        self.ser.write(packet)
        hex_str=' '.join([f'{b:02X}'for b in packet])
        print(f"发送串口数据: {hex_str}")
    
    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("串口已关闭")















""" def send_line_error(self,error):
        if self.ser is None or not self.ser.is_open:
            return
        send_val = error + 100#告诉队友
        if(send_val>255):
            send_val=255
        if(send_val<0):
            send_val=0
        header =0xAA#帧头
        cmd_type=0x01#指令类型(0x01表示巡线误差)
        data_len=0x01#数据长度
        checksum=(cmd_type+data_len+send_val)&0xFF#校验:&的逻辑是全1才为1,这样可以截断超过8位的数据,接收方要再算一遍
        tail=0xFF
        packet=bytes([header,cmd_type,data_len,send_val,checksum,tail])
        self.ser.write(packet)
        hex_str=' '.join([f'{b:02X}'for b in packet])
        print(f"发送串口数据: {hex_str}") """
