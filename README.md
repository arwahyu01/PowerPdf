# PowerPDF

A modern, interactive PDF workstation built with Python (Flask + PyPDF2 + ReportLab).  
Inspired by the iLovePDF menu structure — all processing happens in-memory, no files written to disk.

## Features

### Organize PDF
- **Merge** — gabungkan beberapa PDF menjadi satu
- **Split** — pisahkan halaman ke file terpisah
- **Extract Pages** — ekstrak halaman terpilih ke PDF baru
- **Page Editor** — reorder (drag & drop), rotate, delete, duplicate, insert, reverse

### Edit PDF
- **Crop** — potong area halaman dengan bounding box kustom
- **Page Numbers** — tambahkan nomor halaman ({n} of {N})
- **Text Watermark** — overlay teks diagonal di setiap halaman
- **Image Watermark** — overlay gambar semi-transparan
- **Redact** — sembunyikan konten dengan kotak hitam
- **Normalize** — seragamkan ukuran semua halaman

### Convert to PDF
- **JPG / PNG to PDF** — konversi gambar ke PDF

### PDF Security
- **Encrypt** — lindungi PDF dengan password
- **Decrypt** — buka proteksi password

### Metadata
- **View Info** — lihat title, author, subject, keywords, dll
- **Edit Metadata** — ubah informasi dokumen

## Tech Stack

| Library | Versi | Kegunaan |
|---|---|---|
| Flask | >= 3.0 | Web framework |
| PyPDF2 | >= 3.0 | Membaca/menulis PDF |
| reportlab | >= 4.0 | Generate overlay (page numbers, watermark) |
| pdf.js | 3.11.174 | Render thumbnail di browser |
| SortableJS | 1.15 | Drag and drop halaman |
| Bootstrap 5 | 5.3 | UI framework |

## Installation

```bash
pip install -r requirements.txt
python app.py
```

Buka `http://localhost:5000` di browser.

## Project Structure

```
PowerPDF/
├── app.py              # Flask routes (19 endpoints)
├── pdf_engine.py       # PDF processing engine (20 functions)
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html      # Single-page UI (1550+ lines)
└── ...
```

## Route Map

| Method | Route | Description |
|---|---|---|
| GET | `/` | Index page |
| POST | `/process` | Editor — reorder, rotate, delete, insert |
| POST | `/merge` | Merge PDFs |
| POST | `/split` | Split PDF by page selection |
| POST | `/extract` | Extract selected pages |
| POST | `/crop` | Crop pages |
| POST | `/pagenumbers` | Add page numbers |
| POST | `/watermark` | Text watermark |
| POST | `/watermark-image` | Image watermark |
| POST | `/compress` | Compress PDF |
| POST | `/jpg-to-pdf` | Images to PDF |
| POST | `/redact` | Redact content |
| POST | `/normalize` | Normalize page size |
| POST | `/bookmarks` | Add bookmarks |
| POST | `/metadata` | Read metadata |
| POST | `/metadata/edit` | Edit metadata |
| POST | `/encrypt` | Encrypt with password |
| POST | `/decrypt` | Decrypt / remove password |
| POST | `/validate` | Validate PDF |

## Deferred Features

Fitur berikut tidak diimplementasikan karena memerlukan external binaries atau cloud services:

- OCR PDF (membutuhkan Tesseract)
- Word / Excel / PowerPoint conversion (membutuhkan LibreOffice)
- PDF to JPG / Word / Excel (membutuhkan renderer)
- AI Summarizer & Translate (membutuhkan cloud API)
- PDF Signing with certificates
- Complex PDF forms editor
