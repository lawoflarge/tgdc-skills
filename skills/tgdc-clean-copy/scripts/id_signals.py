"""Find copies of identity documents on every page and image of the given files.

Input:  a TSV file with one "<id><TAB><absolute path>" per line (source files and
        extracted attachments or archive members).
Output: a CSV with one row per page or image: id, page, rotation, faces, white_share,
        text_chars, mrz_lines, mrz_valid, id_terms, hint.
        hint is P4 (identity document), review (possible identity document), or empty.
Stdout: counts only. Errors go to the log file by id, never with paths or content.

Usage:  python id_signals.py INPUT.tsv OUTPUT.csv LOGFILE [--dpi 150]
"""
import csv
import io
import re
import subprocess
import sys
import unicodedata
import zipfile
from pathlib import Path

import cv2
import numpy as np
import pymupdf

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp"}
OFFICE_EXT = {".docx", ".xlsx", ".pptx", ".odt", ".ods", ".odp"}
ID_TERMS = [
    "personalausweis", "reisepass", "aufenthaltstitel", "aufenthaltserlaubnis", "fuehrerschein",
    "bundesrepublik deutschland", "passport", "identity card", "driver's license", "driving licence",
    "residence permit", "carte nationale d'identite", "titre de sejour", "permis de conduire",
    "documento nacional de identidad", "pasaporte", "carteira de identidade", "republica federativa do brasil",
    "carteira nacional de habilitacao", "dowod osobisty", "rzeczpospolita polska", "paszport", "prawo jazdy",
    "identiteitskaart", "paspoort", "rijbewijs", "verblijfsvergunning",
]
CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
MRZ_LINE = re.compile(r"^[A-Z0-9<]{28,46}$")
WEIGHTS = (7, 3, 1)


def fold(text):
    text = text.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def check_digit(field):
    total = 0
    for i, ch in enumerate(field):
        if ch.isdigit():
            v = int(ch)
        elif ch.isalpha():
            v = ord(ch) - 55
        else:
            v = 0
        total += v * WEIGHTS[i % 3]
    return str(total % 10)


def mrz_valid(lines):
    """True if any document-number or date field of a TD1, TD2, or TD3 zone has a valid check digit."""
    def ok(field, digit):
        return len(field) > 0 and digit.isdigit() and check_digit(field) == digit and any(c.isdigit() for c in field)
    for line in lines:
        fixed = line.replace("O", "0") if sum(c.isdigit() for c in line) > len(line) / 3 else line
        candidates = [
            (line[5:14], line[14:15]),       # TD1 line 1, document number
            (fixed[0:6], fixed[6:7]),        # TD1 line 2, birth date
            (fixed[8:14], fixed[14:15]),     # TD1 line 2, expiry date
            (fixed[0:9], fixed[9:10]),       # TD2 and TD3 line 2, document number
            (fixed[13:19], fixed[19:20]),    # TD2 and TD3 line 2, birth date
            (fixed[21:27], fixed[27:28]),    # TD2 and TD3 line 2, expiry date
        ]
        if any(ok(f, d) for f, d in candidates):
            return True
    return False


def ocr(gray):
    ok, png = cv2.imencode(".png", gray)
    if not ok:
        return ""
    run = subprocess.run(["tesseract", "stdin", "stdout", "--psm", "6", "-l", "eng"],
                         input=png.tobytes(), capture_output=True, timeout=120)
    return run.stdout.decode("utf-8", "ignore")


def rotate(gray, angle):
    return {0: gray, 90: cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE),
            180: cv2.rotate(gray, cv2.ROTATE_180), 270: cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE)}[angle]


def faces(gray):
    h, w = gray.shape
    scale = 1000 / max(h, w) if max(h, w) > 1000 else 1.0
    small = cv2.resize(gray, (int(w * scale), int(h * scale))) if scale < 1 else gray
    found = CASCADE.detectMultiScale(small, scaleFactor=1.1, minNeighbors=6, minSize=(40, 40))
    return len(found)


def analyze(gray):
    """Return the strongest finding over the four orientations of one page image."""
    white = float((gray > 200).mean())
    best = None
    for angle in (0, 90, 270, 180):
        img = rotate(gray, angle)
        n_faces = faces(img)
        if angle and n_faces == 0 and best and best["text_chars"] >= 200:
            continue
        text = ocr(img)
        lines = [re.sub(r"\s", "", l).replace("«", "<").upper() for l in text.splitlines()]
        mrz = [l for l in lines if MRZ_LINE.match(l) and l.count("<") >= 2]
        terms = sum(1 for t in ID_TERMS if t in fold(text))
        row = {"rotation": angle, "faces": n_faces, "white_share": round(white, 2),
               "text_chars": len(re.sub(r"\s", "", text)), "mrz_lines": len(mrz),
               "mrz_valid": int(mrz_valid(mrz)), "id_terms": terms}
        score = row["mrz_valid"] * 4 + (row["mrz_lines"] > 0) * 2 + (row["faces"] > 0) * 2 + min(terms, 2)
        if best is None or score > best["_score"]:
            best = {**row, "_score": score}
        if row["mrz_valid"] and row["faces"]:
            break
    face, mrz_any, document_like = best["faces"] > 0, best["mrz_lines"] > 0, white > 0.45
    if best["mrz_valid"] or (face and (mrz_any or best["id_terms"])):
        best["hint"] = "P4"
    elif mrz_any or (face and document_like and best["text_chars"] < 400):
        best["hint"] = "review"
    else:
        best["hint"] = ""
    best.pop("_score")
    return best


def page_images(path, dpi):
    ext = path.suffix.lower()
    with open(path, "rb") as fh:
        head = fh.read(8)
    if head.startswith(b"%PDF-"):
        with pymupdf.open(path) as doc:
            if doc.needs_pass:
                return
            for i, page in enumerate(doc, start=1):
                pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
                yield f"p{i}", np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)
    elif ext in IMAGE_EXT:
        data = np.frombuffer(path.read_bytes(), np.uint8)
        ok, frames = cv2.imdecodemulti(data, cv2.IMREAD_GRAYSCALE)
        for i, frame in enumerate(frames if ok else [], start=1):
            yield f"img{i}", frame
    elif ext in OFFICE_EXT:
        with zipfile.ZipFile(path) as z:
            media = [n for n in z.namelist() if "/media/" in n or n.startswith("Pictures/")]
            for i, name in enumerate(media, start=1):
                img = cv2.imdecode(np.frombuffer(z.read(name), np.uint8), cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    yield f"media{i}", img


def main():
    src, out, log = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    dpi = int(sys.argv[sys.argv.index("--dpi") + 1]) if "--dpi" in sys.argv else 150
    counts = {"files": 0, "pages": 0, "P4_files": 0, "review_files": 0, "errors": 0}
    fields = ["id", "page", "rotation", "faces", "white_share", "text_chars", "mrz_lines", "mrz_valid", "id_terms", "hint"]
    with open(out, "w", newline="") as fo, open(log, "a") as lg:
        writer = csv.DictWriter(fo, fieldnames=fields)
        writer.writeheader()
        for line in src.read_text().splitlines():
            if "\t" not in line:
                continue
            fid, p = line.split("\t", 1)
            counts["files"] += 1
            hints = set()
            try:
                for page, gray in page_images(Path(p), dpi):
                    row = analyze(gray)
                    counts["pages"] += 1
                    hints.add(row["hint"])
                    writer.writerow({"id": fid, "page": page, **row})
            except Exception as exc:
                counts["errors"] += 1
                lg.write(f"{fid}\tid_signals\t{type(exc).__name__}\n")
            if "P4" in hints:
                counts["P4_files"] += 1
            elif "review" in hints:
                counts["review_files"] += 1
    print(" ".join(f"{k}={v}" for k, v in counts.items()))


if __name__ == "__main__":
    main()
