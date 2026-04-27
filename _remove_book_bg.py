"""쇼핑/책 폴더 이미지 배경 제거.
- 검은 배경 → 어두운 픽셀 투명화
- 체크무늬(흰+회색) 배경 → 저채도 + 밝은 픽셀 투명화
- 결과: 같은 폴더에 .png로 저장
"""
import os
from PIL import Image, ImageChops, ImageFilter

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui', '쇼핑', '책')

TRIM_MARGIN = 8


def split_channels(img):
    rgba = img.convert('RGBA')
    r, g, b, _ = rgba.split()
    bright = ImageChops.lighter(ImageChops.lighter(r, g), b)
    dark = ImageChops.darker(ImageChops.darker(r, g), b)
    chroma = ImageChops.subtract(bright, dark)
    return rgba, bright, dark, chroma


def detect_bg_type(img):
    """4 모서리 + 16 샘플로 배경 판정. 'black' or 'checker'."""
    img = img.convert('RGB')
    w, h = img.size
    samples = []
    for x in [0, w // 8, w - 1 - w // 8, w - 1]:
        for y in [0, h // 8, h - 1 - h // 8, h - 1]:
            samples.append(img.getpixel((x, y)))
    avg_bright = sum(max(p) for p in samples) / len(samples)
    avg_chroma = sum((max(p) - min(p)) for p in samples) / len(samples)
    if avg_bright < 40:
        return 'black'
    if avg_bright > 170 and avg_chroma < 25:
        return 'checker'
    # fallback
    return 'black' if avg_bright < 100 else 'checker'


def remove_black(img):
    rgba, bright, _, _ = split_channels(img)
    # 어두운 픽셀(~0,0,0) → 투명. 22 이하 완전 투명, 55 이상 완전 불투명
    alpha = bright.point(
        lambda v: 0 if v <= 22 else (255 if v >= 55 else int(255 * (v - 22) / 33))
    )
    rgba.putalpha(alpha)
    return rgba


def remove_checker(img):
    rgba, bright, _, chroma = split_channels(img)
    # 채도 알파: 채도 8 이하 = 0, 28 이상 = 255 (책 색채는 채도 높음)
    chroma_alpha = chroma.point(
        lambda v: 0 if v <= 8 else (255 if v >= 28 else int(255 * (v - 8) / 20))
    )
    # 어둠 알파: 밝기 175 이상 = 0(=투명), 130 이하 = 255 (책 그림자/검은선)
    dark_alpha = bright.point(
        lambda v: 0 if v >= 175 else (255 if v <= 130 else int(255 * (175 - v) / 45))
    )
    alpha = ImageChops.lighter(chroma_alpha, dark_alpha)
    # 1px erode로 가장자리 밝은 흰끼 제거
    alpha = alpha.filter(ImageFilter.MinFilter(3))
    alpha = alpha.filter(ImageFilter.SMOOTH)
    rgba.putalpha(alpha)
    return rgba


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


def process_one(src_path, dst_path):
    img = Image.open(src_path)
    bg = detect_bg_type(img)
    if bg == 'black':
        out = remove_black(img)
    else:
        out = remove_checker(img)
    out = trim_to_content(out)
    out.save(dst_path, 'PNG', optimize=True)
    return bg, out.size


def main():
    files = [f for f in os.listdir(SRC_DIR) if f.lower().endswith('.jpg')]
    files.sort()
    for fn in files:
        src = os.path.join(SRC_DIR, fn)
        dst = os.path.join(SRC_DIR, os.path.splitext(fn)[0] + '.png')
        try:
            bg, size = process_one(src, dst)
            print(f'  OK {fn}: bg={bg}, out={size[0]}x{size[1]}')
        except Exception as e:
            print(f'  FAIL {fn}: {e}')


if __name__ == '__main__':
    main()
