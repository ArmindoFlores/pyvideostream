import hashlib
import logging
import threading

import cv2

import videostream

WINNAME = "Video Display (Sender)"


def main():
    encoder = videostream.ImageEncoder()
    encoder.set_compression(75)
    encoder.set_encryption_key(hashlib.sha256(b"mys1mp!3p4s5w0rd").digest())
    
    cam = cv2.VideoCapture(0)
    cv2.namedWindow(WINNAME)
    
    server = videostream.Server()
    server_thread = threading.Thread(target=server.start)
    server_thread.start()
    
    while True:
        ret, frame = cam.read()
        if not ret:
            break
        
        cv2.imshow(WINNAME, frame)
        
        frame_data = encoder.encode(frame)
        server.add_frame(frame_data)
        
        key = cv2.waitKey(1)
        if key % 256 == 27:
            break
        
    server.stop()
    cam.release()
    cv2.destroyAllWindows()
    server_thread.join()

if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s %(levelname)s - %(message)s",
        datefmt="[%d/%b/%Y %H:%M:%S]", level=logging.INFO
    )
    main()
