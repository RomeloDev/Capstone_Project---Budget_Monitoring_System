# bb_budget_monitoring_system/apps/admin_panel/signed_doc_converter.py
"""
Signed Document to PDF Converter
Converts image files (JPG, PNG) to PDF for browser preview
"""

import os
from PIL import Image
from django.core.files.base import ContentFile
from django.utils import timezone
import tempfile


def convert_image_to_pdf(doc_instance):
    """
    Convert image (JPG/PNG) to PDF for preview

    Args:
        doc_instance: PurchaseRequestApprovedDocument instance

    Returns:
        str: URL of converted PDF or None if conversion failed
    """

    if not doc_instance.document:
        print("❌ No document file to convert")
        return None

    # Get file extension
    file_ext = doc_instance.get_file_extension()

    # Only convert image files
    if file_ext not in ['jpg', 'jpeg', 'png']:
        print(f"ℹ️ File type '{file_ext}' doesn't need conversion (not an image)")
        return None

    try:
        # Get the image file path
        image_path = doc_instance.document.path

        # Convert image to PDF
        pdf_content = convert_image_with_pillow(image_path)

        if pdf_content:
            return save_converted_pdf_to_model(doc_instance, pdf_content)
        else:
            print("❌ Image to PDF conversion failed")
            return None

    except Exception as e:
        print(f"❌ Error converting signed document: {str(e)}")
        return None


def convert_image_with_pillow(image_path):
    """
    Convert image to PDF using Pillow (PIL)
    """
    try:
        # Open the image
        image = Image.open(image_path)

        # Convert RGBA to RGB if necessary (for PNG with transparency)
        if image.mode == 'RGBA':
            # Create a white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])  # Use alpha channel as mask
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')

        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name

        # Save as PDF
        image.save(temp_pdf_path, 'PDF', resolution=100.0)

        # Read PDF content
        with open(temp_pdf_path, 'rb') as f:
            pdf_content = f.read()

        # Clean up temporary file
        os.remove(temp_pdf_path)

        print(f"✅ Image converted to PDF successfully ({len(pdf_content)} bytes)")
        return pdf_content

    except Exception as e:
        print(f"❌ Pillow conversion failed: {str(e)}")
        return None


def save_converted_pdf_to_model(doc_instance, pdf_content):
    """Save converted PDF to signed document model"""
    try:
        # Generate filename
        original_name = os.path.splitext(doc_instance.file_name)[0]
        filename = f'{original_name}_converted_{timezone.now().strftime("%Y%m%d")}.pdf'

        doc_instance.converted_pdf.save(
            filename,
            ContentFile(pdf_content),
            save=True
        )

        print(f"✅ Converted PDF saved: {doc_instance.converted_pdf.url}")
        return doc_instance.converted_pdf.url

    except Exception as e:
        print(f"❌ Error saving converted PDF: {str(e)}")
        return None


# Main function to call
def convert_signed_document(doc_instance):
    """
    Main function - Use this in your views
    Converts image signed documents to PDF for preview
    """
    return convert_image_to_pdf(doc_instance)
