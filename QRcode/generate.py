import qrcode
import cv2
import numpy as np
def make_and_show(data_str,filename):
    img=qrcode.make(data_str)
    img.save(filename) #保存二维码图片到本地文件
    print(f"生成并保存完毕:{filename}")
    img_cv=cv2.cvtColor(np.array(img).astype(np.uint8) * 255,cv2.COLOR_GRAY2BGR)
    # img_cv=np.array(img).astype(np.uint8) * 255
    cv2.imshow(f"QR:{data_str}",img_cv)

if __name__ == "__main__":
    make_and_show('2','qr_2.png')
    make_and_show('3','qr_3.png')
    cv2.waitKey()
    cv2.destroyAllWindows()