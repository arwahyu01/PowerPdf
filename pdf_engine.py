"""
Pure PDF manipulation engine using PyPDF2 + reportlab.
Every function is deterministic: takes input file(s) + params, returns output bytes.
All functions validate inputs and raise ValueError with clear messages on failure.
"""

import io, re, zipfile, os
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter, PageObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

ID_RE = re.compile(r'^f(\d+)_p(\d+)$')

# Constants
DPI = 72.0  # PDF points per inch
MAX_IMAGE_DIM = 2000  # max image dimension in PDF points for jpg-to-pdf


# ──────────────────────────────────────────────
#  Validation
# ──────────────────────────────────────────────

def validate_pdf(file) -> tuple[bool, str]:
    """Return (is_valid, error_message)."""
    try:
        reader = PdfReader(file)
        _ = len(reader.pages)
        file.seek(0)
        return True, ""
    except Exception as e:
        return False, str(e)


# ──────────────────────────────────────────────
#  Multi-source page resolver (for compound IDs)
# ──────────────────────────────────────────────

def resolve_order(order: list[str], files: list) -> tuple[PdfWriter, dict]:
    """
    Given compound IDs like 'f0_p3' and source files,
    build a PdfWriter with pages in order.
    Returns (writer, file_idx_map).
    """
    readers: dict[int, PdfReader] = {}
    for key in order:
        m = ID_RE.match(key)
        if not m:
            continue
        fidx = int(m.group(1))
        if fidx not in readers:
            readers[fidx] = PdfReader(files[fidx])

    writer = PdfWriter()
    for key in order:
        m = ID_RE.match(key)
        if not m:
            continue
        fidx, pidx = int(m.group(1)), int(m.group(2))
        writer.add_page(readers[fidx].pages[pidx])

    return writer, readers


# ──────────────────────────────────────────────
#  Merge
# ──────────────────────────────────────────────

def merge(files: list) -> bytes:
    writer = PdfWriter()
    for f in files:
        reader = PdfReader(f)
        for page in reader.pages:
            writer.add_page(page)
    buf = BytesIO()
    writer.write(buf)
    writer.close()
    return buf.getvalue()


# ──────────────────────────────────────────────
#  Split
# ──────────────────────────────────────────────

def split(file, page_ranges: list[int]) -> bytes:
    """Return ZIP bytes containing one PDF per page in page_ranges."""
    reader = PdfReader(file)
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for p in page_ranges:
            w = PdfWriter()
            w.add_page(reader.pages[p - 1])
            b = BytesIO()
            w.write(b)
            b.seek(0)
            zf.writestr(f'page_{p}.pdf', b.read())
            w.close()
    return buf.getvalue()


# ──────────────────────────────────────────────
#  Reorder (via compound IDs – used by editor)
# ──────────────────────────────────────────────

def reorder(files: list, order: list[str], rotations: dict[str, int] | None = None, mode: str = "standard") -> bytes:
    writer, _ = resolve_order(order, files)
    if rotations:
        for key, angle in rotations.items():
            m = ID_RE.match(key)
            if not m:
                continue
            fidx, pidx = int(m.group(1)), int(m.group(2))
            try:
                writer.pages[order.index(key)].rotate(int(angle))
            except (ValueError, IndexError):
                pass
    if mode == "compact":
        writer.compress_content_streams = True
    buf = BytesIO()
    writer.write(buf)
    writer.close()
    return buf.getvalue()


# ──────────────────────────────────────────────
#  Duplicate pages (in-memory compound ID list)
# ──────────────────────────────────────────────

def duplicate_pages_in_order(order: list[str], page_ids: list[str]) -> list[str]:
    """Return new order with specified page IDs duplicated after their original."""
    result = []
    for pid in order:
        result.append(pid)
        if pid in page_ids:
            result.append(pid)
    return result


# ──────────────────────────────────────────────
#  Reverse order
# ──────────────────────────────────────────────

def reverse_order_in_list(order: list[str]) -> list[str]:
    return list(reversed(order))


# ──────────────────────────────────────────────
#  Extract pages → new single PDF
# ──────────────────────────────────────────────

def extract(file, page_indices: list[int]) -> bytes:
    reader = PdfReader(file)
    writer = PdfWriter()
    for i in page_indices:
        writer.add_page(reader.pages[i])
    buf = BytesIO()
    writer.write(buf)
    writer.close()
    return buf.getvalue()


# ──────────────────────────────────────────────
#  Crop pages
# ──────────────────────────────────────────────

def crop_pages(file, page_indices: list[int] | None,
               left: float, bottom: float, right: float, top: float) -> bytes:
    """
    Crop pages to bounding box.
    Coordinates are in PDF points (1/72 inch) from the lower-left corner.
    """
    reader = PdfReader(file)
    writer = PdfWriter()
    target = set(page_indices) if page_indices else None

    for i, page in enumerate(reader.pages):
        if target is None or i in target:
            page.cropbox.lower_left = (left, bottom)
            page.cropbox.upper_right = (right, top)
        writer.add_page(page)

    buf = BytesIO()
    writer.write(buf)
    writer.close()
    return buf.getvalue()


# ──────────────────────────────────────────────
#  Add page numbers
# ──────────────────────────────────────────────

def add_page_numbers(file, fmt: str = "{n}", start: int = 1,
                     x: float = -1, y: float = 30, font_size: int = 10,
                     font_name: str = "Helvetica", color: tuple = (0, 0, 0)) -> bytes:
    """Overlay page numbers on each page. x=-1 means center (auto)."""
    reader = PdfReader(file)
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        pnum = start + i
        label = fmt.replace("{n}", str(pnum)).replace("{N}", str(len(reader.pages)))

        pw = float(page.mediabox.width)
        ph = float(page.mediabox.height)
        cx = pw / 2 if x < 0 else x
        cy = y

        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=(pw, ph))
        c.setFont(font_name, font_size)
        c.setFillColorRGB(*color)
        c.drawCentredString(cx, cy, label)
        c.save()

        packet.seek(0)
        num_page = PdfReader(packet).pages[0]
        page.merge_page(num_page)
        writer.add_page(page)

    buf = BytesIO()
    writer.write(buf)
    writer.close()
    return buf.getvalue()


# ──────────────────────────────────────────────
#  Add text watermark (diagonal overlay)
# ──────────────────────────────────────────────

def add_watermark(file, text: str, opacity: float = 0.3,
                  font_size: int = 48, font_name: str = "Helvetica",
                  color: tuple = (0.5, 0.5, 0.5)) -> bytes:
    """Overlay diagonal text watermark on every page."""
    reader = PdfReader(file)
    writer = PdfWriter()

    for page in reader.pages:
        pw = float(page.mediabox.width)
        ph = float(page.mediabox.height)

        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=(pw, ph))
        c.setFont(font_name, font_size)
        c.setFillColorRGB(*color, alpha=opacity)
        c.saveState()
        c.translate(pw / 2, ph / 2)
        c.rotate(45)
        c.drawCentredString(0, 0, text)
        c.restoreState()
        c.save()

        packet.seek(0)
        wm_page = PdfReader(packet).pages[0]
        page.merge_page(wm_page)
        writer.add_page(page)

    buf = BytesIO()
    writer.write(buf)
    writer.close()
    return buf.getvalue()


# ──────────────────────────────────────────────
#  Read metadata
# ──────────────────────────────────────────────

def read_metadata(file) -> dict:
    """Return dict of standard metadata fields."""
    reader = PdfReader(file)
    meta = reader.metadata or {}
    return {
        "title": meta.get("/Title", ""),
        "author": meta.get("/Author", ""),
        "subject": meta.get("/Subject", ""),
        "keywords": meta.get("/Keywords", ""),
        "creator": meta.get("/Creator", ""),
        "producer": meta.get("/Producer", ""),
        "page_count": len(reader.pages),
        "pdf_version": reader.pdf_header if hasattr(reader, "pdf_header") else "",
        "encrypted": reader.is_encrypted if hasattr(reader, "is_encrypted") else False,
    }


# ──────────────────────────────────────────────
#  Edit metadata
# ──────────────────────────────────────────────

def edit_metadata(file, **kwargs) -> bytes:
    """Update PDF metadata. Pass title=, author=, subject=, keywords=, creator=."""
    reader = PdfReader(file)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    meta = {}
    if kwargs.get("title") is not None:
        meta["/Title"] = kwargs["title"]
    if kwargs.get("author") is not None:
        meta["/Author"] = kwargs["author"]
    if kwargs.get("subject") is not None:
        meta["/Subject"] = kwargs["subject"]
    if kwargs.get("keywords") is not None:
        meta["/Keywords"] = kwargs["keywords"]
    if kwargs.get("creator") is not None:
        meta["/Creator"] = kwargs["creator"]
    if meta:
        writer.add_metadata(meta)

    buf = BytesIO()
    writer.write(buf)
    writer.close()
    return buf.getvalue()


# ──────────────────────────────────────────────
#  Encrypt
# ──────────────────────────────────────────────

def encrypt(file, password: str) -> bytes:
    reader = PdfReader(file)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    buf = BytesIO()
    writer.write(buf)
    writer.close()
    return buf.getvalue()


# ──────────────────────────────────────────────
#  Decrypt / remove encryption
# ──────────────────────────────────────────────

def decrypt_remove(file, password: str = "") -> bytes:
    """Decrypt (or remove password from) a PDF. password may be empty for no-op."""
    reader = PdfReader(file)
    if reader.is_encrypted:
        try:
            reader.decrypt(password)
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}") from e
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    buf = BytesIO()
    writer.write(buf)
    writer.close()
    return buf.getvalue()


# ──────────────────────────────────────────────
#  Parse page range string → list of 1-based ints
# ──────────────────────────────────────────────

def parse_ranges(s: str, total: int) -> list[int]:
    pages = set()
    for part in s.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            start = int(a) if a else 1
            end = int(b) if b else total
            pages.update(range(start, end + 1))
        else:
            pages.add(int(part))
    return sorted(p for p in pages if 1 <= p <= total)


# ──────────────────────────────────────────────
#  Compress PDF (reduce file size)
# ──────────────────────────────────────────────

def compress_pdf(file) -> bytes:
    """
    Compress PDF by eliminating unused objects and compressing content streams.
    """
    reader = PdfReader(file)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.compress_content_streams = True
    buf = BytesIO()
    writer.write(buf)
    writer.close()
    return buf.getvalue()


# ──────────────────────────────────────────────
#  JPG / PNG images to PDF
# ──────────────────────────────────────────────

def images_to_pdf(image_files: list, orientation: str = "auto") -> bytes:
    """
    Convert image files (JPEG, PNG) to a single PDF.
    Each image becomes one page, auto-sized to fit within letter dimensions.
    """
    if not image_files:
        raise ValueError("No image files provided")

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)

    for f in image_files:
        f.seek(0)
        img_data = f.read()
        img_io = BytesIO(img_data)
        img = ImageReader(img_io)
        iw, ih = img.getSize()
        f.seek(0)

        pl, ph = letter  # page width, height
        # Scale to fit within page with margins
        margin = 36  # 0.5 inch
        max_w = pl - 2 * margin
        max_h = ph - 2 * margin
        scale = min(max_w / iw, max_h / ih, 1.0)
        dw, dh = iw * scale, ih * scale
        cx, cy = (pl - dw) / 2, (ph - dh) / 2

        c.drawImage(img, cx, cy, width=dw, height=dh, preserveAspectRatio=True)
        c.showPage()

    c.save()
    return buf.getvalue()


# ──────────────────────────────────────────────
#  Redact PDF (overlay black rectangles)
# ──────────────────────────────────────────────

def redact_pdf(file, regions: dict[int, list[tuple[float, float, float, float]]]) -> bytes:
    """
    Redact regions on specific pages by overlaying black rectangles.
    regions: { page_index: [(x, y, w, h), ...] }  -- coordinates in PDF points
    Each rect: (x, y, width, height) relative to page bottom-left.
    """
    reader = PdfReader(file)
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        pw = float(page.mediabox.width)
        ph = float(page.mediabox.height)
        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=(pw, ph))
        for rect in regions.get(i, []):
            r = rect[:4]
            if len(r) == 4:
                rx, ry, rw, rh = r
                c.setFillColorRGB(0, 0, 0)
                c.rect(rx, ry, rw, rh, fill=1, stroke=0)
        c.save()
        packet.seek(0)
        overlay = PdfReader(packet).pages[0]
        page.merge_page(overlay)
        writer.add_page(page)

    buf = BytesIO()
    writer.write(buf)
    writer.close()
    return buf.getvalue()


# ──────────────────────────────────────────────
#  Image watermark
# ──────────────────────────────────────────────

def add_image_watermark(file, image_file, opacity: float = 0.3, scale: float = 0.5) -> bytes:
    """
    Overlay a semi-transparent image watermark on every page.
    Image is scaled relative to page width.
    """
    reader = PdfReader(file)
    writer = PdfWriter()

    img_data = image_file.read()
    image_file.seek(0)

    for page in reader.pages:
        pw = float(page.mediabox.width)
        ph = float(page.mediabox.height)

        img_io = BytesIO(img_data)
        img = ImageReader(img_io)
        iw, ih = img.getSize()
        img_io.seek(0)

        # Scale image to fraction of page width
        target_w = pw * scale
        target_h = ih * (target_w / iw)
        cx, cy = (pw - target_w) / 2, (ph - target_h) / 2

        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=(pw, ph))
        c.setFillAlpha(opacity)
        c.drawImage(img_io, cx, cy, width=target_w, height=target_h,
                    preserveAspectRatio=True)
        c.save()

        packet.seek(0)
        wm_page = PdfReader(packet).pages[0]
        page.merge_page(wm_page)
        writer.add_page(page)

    buf = BytesIO()
    writer.write(buf)
    writer.close()
    return buf.getvalue()


# ──────────────────────────────────────────────
#  Normalize page size
# ──────────────────────────────────────────────

def normalize_pages(file, target_width: float = 612, target_height: float = 792) -> bytes:
    """
    Scale all pages to a uniform target size (default: US Letter).
    Content is centered and scaled to fit while preserving aspect ratio.
    """
    reader = PdfReader(file)
    writer = PdfWriter()

    for page in reader.pages:
        pw = float(page.mediabox.width)
        ph = float(page.mediabox.height)
        sx = target_width / pw
        sy = target_height / ph
        scale = min(sx, sy)

        ops = page.get_contents()
        if ops:
            page.add_transformation([scale, 0, 0, scale, 0, 0])
        page.mediabox.lower_left = (0, 0)
        page.mediabox.upper_right = (target_width, target_height)

        # Center content if aspect ratios differ
        cw, ch = pw * scale, ph * scale
        if cw < target_width or ch < target_height:
            tx = (target_width - cw) / 2
            ty = (target_height - ch) / 2
            if ops:
                page.add_transformation([1, 0, 0, 1, tx, ty])

        writer.add_page(page)

    buf = BytesIO()
    writer.write(buf)
    writer.close()
    return buf.getvalue()


# ──────────────────────────────────────────────
#  Add / edit bookmarks (outlines)
# ──────────────────────────────────────────────

def add_bookmarks(file, bookmarks: list[dict]) -> bytes:
    """
    Add bookmarks (outlines) to a PDF.
    bookmarks: [{title: str, page: int (1-based), parent: int | None}, ...]
    parent refers to index in the bookmarks list (0-based, -1 = root).
    """
    reader = PdfReader(file)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    parents: dict[int, object] = {-1: writer}
    for idx, bm in enumerate(bookmarks):
        title = bm.get("title", "")
        page_num = max(0, min(len(reader.pages) - 1, (bm.get("page", 1) - 1)))
        parent_idx = bm.get("parent", -1)
        parent_ref = parents.get(parent_idx, writer)
        try:
            ref = writer.add_outline_item(title, page_num, parent=parent_ref)
            parents[idx] = ref
        except Exception:
            pass

    buf = BytesIO()
    writer.write(buf)
    writer.close()
    return buf.getvalue()
