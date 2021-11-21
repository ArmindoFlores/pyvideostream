import argparse
import hashlib
import logging
import threading
from getpass import getpass

import cv2

import videostream

WINNAME = "Video Display (Sender)"


def main():
    parser = argparse.ArgumentParser()
    parser.description = "Broadcast video over UDP"
    parser.add_argument(
        "--compression-quality", "-c", 
        type=int, 
        help="compression quality after JPEG encoding; defaults to 80", 
        default=80
    )
    parser.add_argument(
        "--encryption-key", "-e",
        action="store",
        const="",
        default=None,
        nargs="?",
        help="encrypt messages using this key; leave blank to prompt for the key"
    )
    parser.add_argument(
        "--no-gui", "-g",
        action="store_true",
        help="don't display the video being streamed"
    )
    
    args = parser.parse_args()
        
    encoder = videostream.ImageEncoder()
    encoder.set_compression(args.compression_quality)
    
    if args.encryption_key is not None:
        if args.encryption_key == "":
            args.encryption_key = getpass("Enter a password: ")
        encoder.set_encryption_key(hashlib.sha256(args.encryption_key.encode()).digest())
    
    cam = cv2.VideoCapture(0)
    if not args.no_gui:
        cv2.namedWindow(WINNAME)
    
    server = videostream.Server()
    server_thread = threading.Thread(target=server.start)
    server_thread.start()
    
    try:
        while True:
            ret, frame = cam.read()
            if not ret:
                break
            
            if not args.no_gui:
                cv2.imshow(WINNAME, frame)
            
            frame_data = encoder.encode(frame)
            server.add_frame(frame_data)
            
            if not args.no_gui:
                key = cv2.waitKey(1)
                if key % 256 == 27:
                    break
    except KeyboardInterrupt:
        pass
        
    server.stop()
    cam.release()
    if not args.no_gui:
        cv2.destroyAllWindows()
    server_thread.join()

if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s %(levelname)s - %(message)s",
        datefmt="[%d/%b/%Y %H:%M:%S]", level=logging.INFO
    )
    main()
