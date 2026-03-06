import qrcode

img = qrcode.make('Hello Gemini! 这是一个测试二维码')
img.save('test_qr.png')
print("二维码已生成！")