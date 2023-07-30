import torch
import cv2
from multiprocessing import Process, Pipe

class Panoram:
    def __init__(self, output_port, type_panorama):
        self.output_port = output_port
        self.type_panorama = type_panorama
        self.process_2 = Process(target=self.rcv_frame, args=(), daemon=False)
        self.process_2.start()


    def take_strip_w(self, img):
        height, width, _ = img.shape
        half_w = int(width / 1000)
        return img[0:, 0: half_w + 1]

    def take_strip_h(self, img):
        height, width, _ = img.shape
        half_h = int(height / 1000)
        return img[0: half_h + 1, 0:]


    def stitch(self, img, strip, axis=1):
        return torch.cat((img, strip), axis)

    def image_show_result(self, img):
        cv2.imwrite("panorama.jpg", img.numpy())
        cv2.imshow("frame", img.numpy())
        cv2.waitKey(1)



    def rcv_frame(self):
        img = None
        fra = self.output_port.recv()

        if self.type_panorama == "horizontal":
            img = self.take_strip_w(torch.from_numpy(fra))
        if self.type_panorama == "vertical":
            img = self.take_strip_h(torch.from_numpy(fra))

        while True:
            if self.type_panorama == "horizontal":
                frame = self.output_port.recv()
                img_stitch = self.take_strip_w(frame)
                img = self.stitch(img, img_stitch, axis=1)

            if self.type_panorama == "vertical":
                frame = self.output_port.recv()
                img_stitch = self.take_strip_h(frame)
                img = self.stitch(img, img_stitch, axis=0)

            self.image_show_result(img)





class CAMERA:
    def __init__(self, inp_port, num_cam, frame_gluing):
        self.inp_port, self.num_cam,  self.frame_gluing = inp_port, num_cam, frame_gluing
        self.process_1 = Process(target=self.put_image, args=(), daemon=False)
        self.process_1.start()

    def put_image(self):
        cap = cv2.VideoCapture(self.num_cam)
        ret, img = cap.read()
        self.inp_port.send(img)
        c = 0
        while (cap.isOpened()) and c <= self.frame_gluing:
            ret, frame = cap.read()
            c += 1
            if ret:
                self.inp_port.send(torch.from_numpy(frame))

        self.inp_port.close()



if __name__ == "__main__":
    inp_port, out_port = Pipe()
    frame_gluing, num_cam, type_panorama = 100, 0, "horizontal"
    cam = CAMERA(inp_port, num_cam, frame_gluing)
    panoram = Panoram(out_port, type_panorama)
