from typing import Optional, cast

import Cryptodome.Cipher._mode_eax
import cv2
import numpy as np
from Cryptodome.Cipher import AES

EaxMode = Cryptodome.Cipher._mode_eax.EaxMode


class ImageEncoder:
    def __init__(self):
        self._encryption_key: Optional[bytes] = None
        self._compression: Optional[int] = None
        
    def set_encryption_key(self, key: Optional[bytes]):
        self._encryption_key = key
        
    def set_compression(self, compression_quality: Optional[int]):
        self._compression = compression_quality

    @property
    def compression(self) -> Optional[int]:
        return self._compression
        
    def encode(self, image: np.array) -> bytes:
        result: bytes
        if self._compression is not None:
            result = cv2.imencode(".jpg", image, (int(cv2.IMWRITE_JPEG_QUALITY), self._compression))[-1].tobytes()
        else:
            result = cv2.imencode(".jpg", image, (int(cv2.IMWRITE_JPEG_QUALITY), 100))[-1].tobytes()
  
        if self._encryption_key is not None:
            cipher: EaxMode = cast(EaxMode, AES.new(self._encryption_key, AES.MODE_EAX))
            ciphertext, tag = cipher.encrypt_and_digest(result)
            result = b"".join((b"\x01", cipher.nonce, tag, ciphertext))
        else:
            result = b"\x00" + result
        
        return result


class ImageDecoder:
    def __init__(self):
        self._encryption_key: Optional[bytes] = None
        
    def set_encryption_key(self, key: Optional[bytes]):
        self._encryption_key = key

    def decode(self, image: bytes) -> np.array:
        img_bytes: bytes = image[1:]
        
        if self._encryption_key is not None and image[0] == 1:
            nonce = image[1:17]
            tag = image[17:33]
            ciphertext = image[33:]
            cipher = cast(EaxMode, AES.new(self._encryption_key, AES.MODE_EAX, nonce))
            img_bytes = cipher.decrypt_and_verify(ciphertext, tag)
        
        return cv2.imdecode(np.frombuffer(img_bytes, np.uint8), 1)
