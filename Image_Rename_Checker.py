import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".psb", ".webp"}

def choose_folder():
    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="Select the folder containing your completed images")
    root.destroy()
    return folder

def choose_txt():
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
        title="Select the Expected Return Files TXT",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    root.destroy()
    return path

def extract_expected_names(txt_path):
    expected = []
    seen = set()

    with open(txt_path, "r", encoding="utf-8-sig", errors="replace") as f:
        for line in f:
            # Expected lines look like:
            # 1. filename.ext
            # 2. filename.ext
            m = re.match(r"^\s*(\d+)\.\s+(.+?)\s*$", line)
            if not m:
                continue

            name = m.group(2).strip()

            # Only take numbered lines that actually look like file names.
            if "." not in name:
                continue

            key = name.casefold()
            if key not in seen:
                expected.append((int(m.group(1)), name))
                seen.add(key)

    expected.sort(key=lambda x: x[0])
    return expected

def scan_images(folder):
    found = {}
    for root, dirs, files in os.walk(folder):
        for filename in files:
            ext = Path(filename).suffix.casefold()
            if ext in IMAGE_EXTS:
                found.setdefault(filename.casefold(), []).append(
                    os.path.relpath(os.path.join(root, filename), folder)
                )
    return found

def main():
    txt_path = choose_txt()
    if not txt_path:
        return

    image_folder = choose_folder()
    if not image_folder:
        return

    expected = extract_expected_names(txt_path)

    if not expected:
        messagebox.showerror(
            "No expected filenames found",
            "The TXT file did not contain numbered filenames such as:\n1. image.jpg"
        )
        return

    found = scan_images(image_folder)

    matched = []
    missing = []
    duplicate_actual = []
    expected_keys = set()

    for number, name in expected:
        key = name.casefold()
        expected_keys.add(key)

        if key in found:
            matched.append((number, name, found[key]))
            if len(found[key]) > 1:
                duplicate_actual.append((number, name, found[key]))
        else:
            missing.append((number, name))

    extra = []
    for key, paths in found.items():
        if key not in expected_keys:
            extra.extend(paths)

    report_path = os.path.join(image_folder, "RENAME_CHECK_REPORT.txt")

    total_expected = len(expected)
    total_matched = len(matched)
    total_missing = len(missing)
    total_extra = len(extra)

    with open(report_path, "w", encoding="utf-8") as out:
        out.write("IMAGE RENAME CHECK REPORT\n")
        out.write("=" * 70 + "\n")
        out.write(f"Checked folder: {image_folder}\n")
        out.write(f"Expected TXT: {os.path.basename(txt_path)}\n")
        out.write(f"Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        out.write("SUMMARY\n")
        out.write("-" * 70 + "\n")
        out.write(f"Expected files : {total_expected}\n")
        out.write(f"Matched        : {total_matched}\n")
        out.write(f"Missing        : {total_missing}\n")
        out.write(f"Extra images   : {total_extra}\n")
        out.write(f"Duplicate same-name images in different folders: {len(duplicate_actual)}\n\n")

        out.write("1. MATCHED FILES\n")
        out.write("-" * 70 + "\n")
        if matched:
            for number, name, paths in matched:
                out.write(f"[{number:02d}] OK   {name}\n")
                for p in paths:
                    out.write(f"      -> {p}\n")
        else:
            out.write("None\n")

        out.write("\n2. MISSING FILES\n")
        out.write("-" * 70 + "\n")
        if missing:
            for number, name in missing:
                out.write(f"[{number:02d}] MISSING   {name}\n")
        else:
            out.write("None — all expected filenames were found.\n")

        out.write("\n3. EXTRA IMAGES\n")
        out.write("-" * 70 + "\n")
        if extra:
            for p in sorted(extra, key=str.casefold):
                out.write(f"EXTRA   {p}\n")
        else:
            out.write("None — no extra image files found.\n")

        out.write("\n4. DUPLICATE SAME-NAME IMAGES\n")
        out.write("-" * 70 + "\n")
        if duplicate_actual:
            for number, name, paths in duplicate_actual:
                out.write(f"[{number:02d}] {name}\n")
                for p in paths:
                    out.write(f"      -> {p}\n")
        else:
            out.write("None\n")

        out.write("\n5. EXPECTED ORDER CHECK (1-33 etc.)\n")
        out.write("-" * 70 + "\n")
        for number, name in expected:
            status = "OK" if name.casefold() in found else "MISSING"
            out.write(f"{number:02d} | {status:<7} | {name}\n")

    if total_missing == 0 and total_extra == 0 and not duplicate_actual:
        msg = (
            "CHECK COMPLETE\n\n"
            "All expected filenames were found.\n"
            "No extra images were found.\n"
            "No duplicate same-name images were found.\n\n"
            f"Report:\n{report_path}"
        )
    else:
        msg = (
            "CHECK COMPLETE\n\n"
            f"Matched: {total_matched}\n"
            f"Missing: {total_missing}\n"
            f"Extra: {total_extra}\n"
            f"Duplicate same-name images: {len(duplicate_actual)}\n\n"
            f"Full report saved here:\n{report_path}"
        )

    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Rename Check Finished", msg)
    root.destroy()

if __name__ == "__main__":
    main()
