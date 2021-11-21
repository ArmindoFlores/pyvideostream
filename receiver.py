import argparse
import hashlib
import logging
import threading
from getpass import getpass

import cv2

import videostream

WINNAME = "Video Display (Receiver)"


def main():
    parser = argparse.ArgumentParser()
    parser.description = "Receive video broadcast over UDP"
    parser.add_argument(
        "--encryption-key", "-e",
        action="store",
        const="",
        default=None,
        nargs="?",
        help="decrypt messages using this key; leave blank to prompt for the key"
    )
    
    args = parser.parse_args()
    
    decoder = videostream.ImageDecoder()
    
    if args.encryption_key is not None:
        if args.encryption_key == "":
            args.encryption_key = getpass("Enter a password: ")
        decoder.set_encryption_key(hashlib.sha256(args.encryption_key.encode()).digest())
    
    cv2.namedWindow(WINNAME)
    
    frame = None
    error = None
    lock = threading.Lock()
    
    def cb(framedata):
        nonlocal frame, lock, error
        try:
            data = decoder.decode(framedata)
            lock.acquire()
            frame = data
            lock.release()
        except ValueError as e:
            error = e
    
    client = videostream.Client()
    client.set_on_receive_callback(cb)
    client_thread = threading.Thread(target=client.start)
    client_thread.start()
    
    frame = None
    while True: 
        if error is not None:
            logging.error(error)
            break
            
        lock.acquire()      
        if frame is not None:
            cv2.imshow(WINNAME, frame)
        lock.release()
        
        key = cv2.waitKey(1)
        if key % 256 == 27:
            break
        
    client.stop()
    cv2.destroyAllWindows()
    client_thread.join()

if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s %(levelname)s - %(message)s",
        datefmt="[%d/%b/%Y %H:%M:%S]", level=logging.INFO
    )
    main()
