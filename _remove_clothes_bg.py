"""쇼핑/옷 폴더 이미지 배경 제거 (rembg u2net 모델 사용).
- 결과: 같은 폴더에 .png로 저장
- 1px 가장자리 erode + content trim
"""
import os
from rembg import remove, new_session
from PIL import Image, ImageFilter
import numpy as np

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui', '쇼핑', '옷')
TRIM_MARGIN = 8


def post_process(rgba_img):
    """알파 채널 1px erode (가장자리 vignette 잔재 제거) + 부드럽게."""
    arr = np.array(rgba_img)
    if arr.shape[2] != 4:
        return rgba_img
    alpha = arr[:, :, 3]
    # alpha < 30: 완전 투명, alpha > 220: 완전 불투명, 그 사이는 보존
    alpha = np.where(alpha < 30, 0, np.where(alpha > 220, 255, alpha)).astype(np.uint8)
    # 부드러운 가장자리
    a_img = Image.fromarray(alpha, 'L').filter(ImageFilter.SMOOTH)
    arr[:, :, 3] = np.array(a_img)
    return Image.fromarray(arr, 'RGBA')


def trim_to_content(img, margin=TRIM_MARGIN):
    bbox = img.getbbox()
    if not bbox:
        return img
    left, top, right, bottom = bbox
    w, h = img.size
    left = max(0, left - margin)
    top = max(0, top - margin)
    right = min(w, right + margin)
    bottom = min(h, bottom + margin)
    return img.crop((left, top, right, bottom))


def main():
    session = new_session('u2net')
    files = sorted(f for f in os.listdir(SRC_DIR) if f.lower().endswith('.jpg'))
    for fn in files:
        src = os.path.join(SRC_DIR, fn)
        dst = os.path.join(SRC_DIR, os.path.splitext(fn)[0] + '.png')
        try:
            img = Image.open(src)
            out = remove(img, session=session)
            out = post_process(out)
            out = trim_to_content(out)
            out.save(dst, 'PNG', optimize=True)
            print(f'  OK {fn}: {out.size[0]}x{out.size[1]}')
        except Exception as e:
            print(f'  FAIL {fn}: {e}')


if __name__ == '__main__':
    main()
