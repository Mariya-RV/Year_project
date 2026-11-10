from pathlib import Path

import fitz
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent

PDF_DIR = PROJECT_DIR / "data" / "raw_pdf"
IMAGES_DIR = PROJECT_DIR / "data" / "images"

METADATA_FILE = PROJECT_DIR / "data" / "metadata.csv"
PAGES_FILE = PROJECT_DIR / "data" / "pages.csv"

def prepare_dataset():

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    documents = []
    pages = []

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))

    for i, pdf_path in enumerate(pdf_files, start=1):

        document_id = f"D{i:03d}"

        document_folder = IMAGES_DIR / document_id
        document_folder.mkdir(exist_ok=True)

        with fitz.open(pdf_path) as pdf:

            total_pages = len(pdf)

            for page_index in range(total_pages):

                page = pdf[page_index]

                # 300 DPI для качественного распознавания
                pix = page.get_pixmap(
                    dpi=300,
                    colorspace=fitz.csRGB,
                    alpha=False
                )

                page_number = page_index + 1

                image_name = f"page_{page_number:03d}.jpg"

                image_path = document_folder / image_name

                pix.pil_save(
                    str(image_path),
                    format="JPEG",
                    quality=95
                )

                pages.append({
                    "document_id": document_id,
                    "page_number": page_number,
                    "total_pages": total_pages,
                    "image_path": str(
                        image_path.relative_to(PROJECT_DIR)
                    ),
                    "width": pix.width,
                    "height": pix.height,
                })

        documents.append({
            "document_id": document_id,
            "source_filename": pdf_path.name,
            "patient_id": "",
            "analysis_date": "",
            "laboratory": "",
            "analysis_type": "",
            "total_pages": total_pages,
        })

        print(
            f"{pdf_path.name} → "
            f"{document_id}: {total_pages} страниц"
        )

    pd.DataFrame(documents).to_csv(
        METADATA_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    pd.DataFrame(pages).to_csv(
        PAGES_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\nГотово!")
    print(f"Документов: {len(documents)}")
    print(f"Изображений: {len(pages)}")

if __name__ == "__main__":
    prepare_dataset()