import openpyxl
from openpyxl.drawing.image import Image as OpenpyxlImage
import os

# Load the template
wb = openpyxl.load_workbook('../excel_templates/Departmental-PRE.xlsx')
ws = wb.active

print("="*70)
print("EXTRACTING LOGOS from Departmental-PRE.xlsx")
print("="*70)

# Extract images
if hasattr(ws, '_images') and ws._images:
    print(f"\nFound {len(ws._images)} images")

    for idx, img in enumerate(ws._images, 1):
        # Save the image
        filename = f'logo_{idx}.png'
        filepath = os.path.join(os.path.dirname(__file__), filename)

        # Get image data
        if hasattr(img, '_data'):
            with open(filepath, 'wb') as f:
                f.write(img._data())
            print(f"\n[{idx}] Saved: {filename}")

            # Try to get anchor info
            try:
                if hasattr(img, 'anchor'):
                    anchor_obj = img.anchor
                    # Get the position info if available
                    if hasattr(anchor_obj, '_from'):
                        from_cell = anchor_obj._from
                        print(f"    Position: Column {from_cell.col}, Row {from_cell.row}")
                        print(f"    Offset: X={from_cell.colOff}, Y={from_cell.rowOff}")
            except:
                print(f"    Position: Unable to extract")

            # Get size
            if hasattr(img, 'width') and hasattr(img, 'height'):
                print(f"    Size: {img.width} x {img.height} pixels")

print("\n" + "="*70)
print("Images extracted! Check the sample_reports folder for logo_*.png files")
print("="*70)
