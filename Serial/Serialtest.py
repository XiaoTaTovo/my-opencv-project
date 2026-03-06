import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
for port in ports:
    print(f"找到串口: {port.device}")
print(1)