from pathlib import Path
import hashlib
import re
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / 'data/external/images'
OUTPUT = ROOT / 'data/external_metadata.csv'
EXTS = {'.png', '.jpg', '.jpeg'}


def main():
    if not INPUT.exists():
        raise FileNotFoundError(f'Создайте папку и скопируйте изображения: {INPUT}')
    files = sorted(p for p in INPUT.rglob('*') if p.is_file() and p.suffix.lower() in EXTS)
    if not files:
        raise RuntimeError(f'Нет PNG/JPEG в {INPUT}')
    previous = {}
    if OUTPUT.exists():
        old = pd.read_csv(OUTPUT, dtype=str).fillna('')
        previous = {row['image_path']: row for _, row in old.iterrows()}
    rows = []
    for i, path in enumerate(files, 1):
        rel = path.relative_to(ROOT).as_posix()
        match = re.search(r'(?i)\.pdf_page_(\d+)', path.name)
        source_pdf = path.name[:match.start() + 4] if match else ''
        page_number = int(match.group(1)) if match else None
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        row = dict(image_id=f'EXT{i:04d}', image_path=rel, original_filename=path.name,
                   source_pdf=source_pdf, source_page_number=page_number,
                   width=None, height=None, format='', mode='', file_size_kb=round(path.stat().st_size / 1024, 1),
                   sha256=digest, is_valid=False, error='', is_lab_report='', analysis_type='', laboratory='', language='')
        try:
            with Image.open(path) as im:
                im.verify()
            with Image.open(path) as im:
                row.update(width=im.width, height=im.height, format=im.format, mode=im.mode, is_valid=True)
        except Exception as e:
            row['error'] = str(e)[:200]
        if rel in previous:
            for key in ('is_lab_report', 'analysis_type', 'laboratory', 'language'):
                row[key] = previous[rel].get(key, '')
        rows.append(row)
    df = pd.DataFrame(rows)
    df['is_exact_duplicate'] = df.duplicated('sha256', keep='first')
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False, encoding='utf-8-sig')
    print(f'Файлов: {len(df)}, читаемых: {int(df.is_valid.sum())}, точных дублей: {int(df.is_exact_duplicate.sum())}')
    print(f'Метаданные: {OUTPUT}')

if __name__ == '__main__':
    main()
