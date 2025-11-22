# bb_budget_monitoring_system/apps/admin_panel/supporting_doc_converter.py
"""
Supporting Document to PDF Converter
Converts Excel and Word files to PDF for browser preview
"""

import os
import subprocess
import tempfile
from django.core.files.base import ContentFile
from django.utils import timezone


def convert_supporting_document_to_pdf(doc_instance):
    """
    Convert Excel/Word supporting document to PDF for preview

    Args:
        doc_instance: DepartmentPRESupportingDocument instance

    Returns:
        str: URL of converted PDF or None if conversion failed
    """

    if not doc_instance.document:
        print("❌ No document file to convert")
        return None

    # Get file extension
    file_ext = doc_instance.get_file_extension()

    # Only convert Excel and Word files
    if file_ext not in ['xlsx', 'xls', 'docx', 'doc']:
        print(f"ℹ️ File type '{file_ext}' doesn't need conversion (not Excel/Word)")
        return None

    try:
        doc_path = doc_instance.document.path

        # Try conversion methods in order
        try:
            pdf_content = convert_with_libreoffice(doc_path)
            if pdf_content:
                return save_converted_pdf_to_model(doc_instance, pdf_content)
        except Exception as e:
            print(f"LibreOffice conversion failed: {e}")

        # Method 2: Win32com (Windows only)
        try:
            pdf_content = convert_with_win32com(doc_path, file_ext)
            if pdf_content:
                return save_converted_pdf_to_model(doc_instance, pdf_content)
        except Exception as e:
            print(f"Win32com conversion failed: {e}")

        print("❌ All conversion methods failed")
        return None

    except Exception as e:
        print(f"❌ Error converting supporting document: {str(e)}")
        return None


def convert_with_libreoffice(file_path):
    """
    Convert document to PDF using LibreOffice
    """
    import time

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            cmd = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                '--headless',
                '--invisible',
                '--nocrashreport',
                '--nodefault',
                '--nofirststartwizard',
                '--nolockcheck',
                '--nologo',
                '--norestore',
                '--convert-to', 'pdf',
                '--outdir', temp_dir,
                file_path
            ]

            print(f"Converting document with LibreOffice...")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                print(f"LibreOffice stderr: {result.stderr}")
                raise Exception(f"LibreOffice failed with return code {result.returncode}")

            # Get generated PDF
            pdf_filename = os.path.splitext(os.path.basename(file_path))[0] + '.pdf'
            pdf_path = os.path.join(temp_dir, pdf_filename)

            time.sleep(1)  # Wait for file to be written

            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                print(f"✅ PDF created: {pdf_path} ({file_size} bytes)")

                with open(pdf_path, 'rb') as f:
                    return f.read()
            else:
                files = os.listdir(temp_dir)
                print(f"Files in temp dir: {files}")
                raise Exception("PDF file not created")

        except FileNotFoundError:
            raise Exception("LibreOffice not installed")
        except subprocess.TimeoutExpired:
            raise Exception("Conversion timeout (>60s)")


def convert_with_win32com(file_path, file_ext):
    """
    Convert document to PDF using Windows COM (Excel/Word)
    """
    try:
        import win32com.client
        import tempfile

        pdf_path = tempfile.mktemp(suffix='.pdf')

        if file_ext in ['xlsx', 'xls']:
            # Excel conversion
            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False

            workbook = excel.Workbooks.Open(file_path)
            workbook.ExportAsFixedFormat(0, pdf_path)  # 0 = PDF format

            workbook.Close(False)
            excel.Quit()

        elif file_ext in ['docx', 'doc']:
            # Word conversion
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False

            doc = word.Documents.Open(file_path)
            doc.SaveAs(pdf_path, FileFormat=17)  # 17 = PDF format

            doc.Close()
            word.Quit()

        # Read PDF
        if os.path.exists(pdf_path):
            print(f"✅ PDF created with COM: {pdf_path}")
            with open(pdf_path, 'rb') as f:
                content = f.read()
            os.remove(pdf_path)
            return content
        else:
            raise Exception("PDF not created")

    except ImportError:
        raise Exception("pywin32 not installed or not on Windows")
    except Exception as e:
        raise Exception(f"Win32com conversion failed: {str(e)}")


def save_converted_pdf_to_model(doc_instance, pdf_content):
    """Save converted PDF to supporting document model"""
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
def convert_pre_supporting_doc(doc_instance):
    """
    Main function - Use this in your views
    Converts Excel/Word supporting documents to PDF for preview
    """
    return convert_supporting_document_to_pdf(doc_instance)
