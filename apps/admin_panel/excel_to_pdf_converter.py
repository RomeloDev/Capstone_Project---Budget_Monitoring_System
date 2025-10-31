# bb_budget_monitoring_system/apps/admin_panel/excel_to_pdf_converter.py
"""
Better Excel to PDF Converter
Fixes LibreOffice conversion issues for complex Excel files
"""

import os
import subprocess
import tempfile
from django.core.files.base import ContentFile
from django.utils import timezone


def convert_excel_to_pdf_improved(pre):
    """
    Convert Excel to PDF using improved LibreOffice method
    with better parameters for complex files
    """
    
    if not pre.uploaded_excel_file:
        print("❌ No Excel file to convert")
        return None
    
    try:
        excel_path = pre.uploaded_excel_file.path
        
        # Method 1: LibreOffice with better parameters (Try this first)
        try:
            pdf_content = convert_with_libreoffice_improved(excel_path)
            if pdf_content:
                return save_pdf_to_model(pre, pdf_content)
        except Exception as e:
            print(f"LibreOffice improved method failed: {e}")
        
        # Method 2: Use unoconv (wrapper around LibreOffice)
        try:
            pdf_content = convert_with_unoconv(excel_path)
            if pdf_content:
                return save_pdf_to_model(pre, pdf_content)
        except Exception as e:
            print(f"Unoconv method failed: {e}")
        
        # Method 3: Use win32com (Windows only - if on Windows server)
        try:
            pdf_content = convert_with_win32com(excel_path)
            if pdf_content:
                return save_pdf_to_model(pre, pdf_content)
        except Exception as e:
            print(f"Win32com method failed: {e}")
        
        print("❌ All conversion methods failed")
        return None
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def convert_with_libreoffice_improved(excel_path):
    """
    Improved LibreOffice conversion with better parameters
    """
    import tempfile
    import time
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Better LibreOffice command with more options
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
                '--convert-to', 'pdf:calc_pdf_Export',  # Specify calc PDF export filter
                '--outdir', temp_dir,
                excel_path
            ]
            
            print(f"Running LibreOffice conversion...")
            print(f"Command: {' '.join(cmd)}")
            
            # Run with longer timeout
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=60  # Increased timeout
            )
            
            if result.returncode != 0:
                print(f"LibreOffice stderr: {result.stderr}")
                raise Exception(f"LibreOffice failed with return code {result.returncode}")
            
            print(f"LibreOffice stdout: {result.stdout}")
            
            # Get generated PDF
            pdf_filename = os.path.splitext(os.path.basename(excel_path))[0] + '.pdf'
            pdf_path = os.path.join(temp_dir, pdf_filename)
            
            # Wait a bit for file to be written
            time.sleep(1)
            
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                print(f"✅ PDF created: {pdf_path} ({file_size} bytes)")
                
                with open(pdf_path, 'rb') as f:
                    return f.read()
            else:
                # List files in temp dir to debug
                files = os.listdir(temp_dir)
                print(f"Files in temp dir: {files}")
                raise Exception("PDF file not created")
                
        except FileNotFoundError:
            raise Exception("LibreOffice not installed. Install: sudo apt-get install libreoffice")
        except subprocess.TimeoutExpired:
            raise Exception("Conversion timeout (>60s). File may be too large.")


def convert_with_unoconv(excel_path):
    """
    Convert using unoconv (better than raw LibreOffice)
    Install: sudo apt-get install unoconv
    """
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            pdf_filename = os.path.splitext(os.path.basename(excel_path))[0] + '.pdf'
            pdf_path = os.path.join(temp_dir, pdf_filename)
            
            cmd = [
                'unoconv',
                '-f', 'pdf',
                '-o', pdf_path,
                excel_path
            ]
            
            print(f"Running unoconv conversion...")
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            
            if result.returncode != 0:
                raise Exception(f"Unoconv failed: {result.stderr.decode()}")
            
            if os.path.exists(pdf_path):
                print(f"✅ PDF created with unoconv: {pdf_path}")
                with open(pdf_path, 'rb') as f:
                    return f.read()
            else:
                raise Exception("PDF not created by unoconv")
                
        except FileNotFoundError:
            raise Exception("Unoconv not installed. Install: sudo apt-get install unoconv")


def convert_with_win32com(excel_path):
    """
    Convert using win32com (Windows only)
    Install: pip install pywin32
    """
    try:
        import win32com.client
        import tempfile
        
        # Start Excel application
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        
        # Open workbook
        workbook = excel.Workbooks.Open(excel_path)
        
        # Generate PDF path
        pdf_path = tempfile.mktemp(suffix='.pdf')
        
        # Export to PDF
        workbook.ExportAsFixedFormat(0, pdf_path)  # 0 = PDF format
        
        # Close
        workbook.Close(False)
        excel.Quit()
        
        # Read PDF
        if os.path.exists(pdf_path):
            print(f"✅ PDF created with Excel COM: {pdf_path}")
            with open(pdf_path, 'rb') as f:
                content = f.read()
            os.remove(pdf_path)  # Clean up
            return content
        else:
            raise Exception("PDF not created")
            
    except ImportError:
        raise Exception("pywin32 not installed or not on Windows")
    except Exception as e:
        raise Exception(f"Win32com conversion failed: {str(e)}")


def save_pdf_to_model(pre, pdf_content):
    """Save PDF to model"""
    try:
        filename = f'PRE_{str(pre.id)[:8].upper()}_{timezone.now().strftime("%Y%m%d")}.pdf'
        
        pre.partially_approved_pdf.save(
            filename,
            ContentFile(pdf_content),
            save=True
        )
        
        print(f"✅ PDF saved to model: {pre.partially_approved_pdf.url}")
        return pre.partially_approved_pdf.url
        
    except Exception as e:
        print(f"❌ Error saving PDF: {str(e)}")
        return None


# Main function to call
def generate_pre_pdf_from_excel(pre):
    """
    Main function - Use this in your views
    """
    return convert_excel_to_pdf_improved(pre)


# ==============================================================
# ALTERNATIVE: Manual Upload Approach (If conversion fails)
# ==============================================================

def enable_manual_pdf_upload(pre, uploaded_pdf_file):
    """
    Fallback: Allow admin to manually convert and upload PDF
    
    Usage in admin view:
        if request.FILES.get('manual_pdf'):
            pdf_file = request.FILES['manual_pdf']
            enable_manual_pdf_upload(pre, pdf_file)
    """
    try:
        filename = f'PRE_{str(pre.id)[:8].upper()}_Manual.pdf'
        
        pre.partially_approved_pdf.save(
            filename,
            uploaded_pdf_file,
            save=True
        )
        
        print(f"✅ Manual PDF uploaded: {pre.partially_approved_pdf.url}")
        return pre.partially_approved_pdf.url
        
    except Exception as e:
        print(f"❌ Error uploading manual PDF: {str(e)}")
        return None