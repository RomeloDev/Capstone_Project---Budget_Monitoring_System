"""
Document conversion utilities for PR approval
Converts uploaded Word/PDF documents to standardized PDFs using LibreOffice
"""
import os
import subprocess
import tempfile
import time
from django.core.files.base import ContentFile
from pathlib import Path


def convert_docx_to_pdf_libreoffice(docx_file):
    """
    Convert Word document to PDF using LibreOffice
    
    Args:
        docx_file: Django UploadedFile object (.docx or .doc)
    
    Returns:
        ContentFile: PDF file ready to save, or None if conversion fails
    """
    try:
        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded file to temp location
            temp_docx_path = os.path.join(temp_dir, 'input.docx')
            
            with open(temp_docx_path, 'wb') as temp_file:
                for chunk in docx_file.chunks():
                    temp_file.write(chunk)
            
            print(f"📝 Saved temp DOCX: {temp_docx_path}")
            
            # LibreOffice conversion command
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
                '--convert-to', 'pdf:writer_pdf_Export',  # Writer PDF export filter
                '--outdir', temp_dir,
                temp_docx_path
            ]
            
            print(f"🔄 Running LibreOffice conversion...")
            print(f"Command: {' '.join(cmd)}")
            
            # Run conversion
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                print(f"❌ LibreOffice stderr: {result.stderr}")
                print(f"❌ LibreOffice stdout: {result.stdout}")
                return None
            
            print(f"✅ LibreOffice stdout: {result.stdout}")
            
            # Wait for file to be written
            time.sleep(1)
            
            # Find generated PDF
            pdf_path = os.path.join(temp_dir, 'input.pdf')
            
            if not os.path.exists(pdf_path):
                # List all files to debug
                files = os.listdir(temp_dir)
                print(f"❌ PDF not found. Files in temp dir: {files}")
                return None
            
            file_size = os.path.getsize(pdf_path)
            print(f"✅ PDF created: {pdf_path} ({file_size} bytes)")
            
            # Read PDF content
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Create ContentFile with proper filename
            filename = docx_file.name.rsplit('.', 1)[0] + '.pdf'
            return ContentFile(pdf_content, name=filename)
            
    except FileNotFoundError:
        print("❌ LibreOffice not found at C:\\Program Files\\LibreOffice\\program\\soffice.exe")
        return None
    except subprocess.TimeoutExpired:
        print("❌ Conversion timeout (>60s)")
        return None
    except Exception as e:
        print(f"❌ Error converting DOCX to PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


def ensure_pdf(uploaded_file):
    """
    Ensure file is PDF. If it's DOCX, convert it using LibreOffice.
    
    Args:
        uploaded_file: Django UploadedFile object
    
    Returns:
        File: PDF file or None if conversion fails
    """
    if not uploaded_file:
        return None
    
    filename = uploaded_file.name.lower()
    
    # Already PDF - return as is
    if filename.endswith('.pdf'):
        print(f"✅ File is already PDF: {uploaded_file.name}")
        return uploaded_file
    
    # Try to convert DOCX/DOC to PDF
    elif filename.endswith(('.docx', '.doc')):
        print(f"🔄 Converting Word document to PDF: {uploaded_file.name}")
        pdf_file = convert_docx_to_pdf_libreoffice(uploaded_file)
        
        if pdf_file:
            print(f"✅ Conversion successful")
            return pdf_file
        else:
            print(f"❌ Conversion failed")
            return None
    
    # Other formats - not supported
    else:
        print(f"⚠️ Unsupported format: {filename}")
        return None


def convert_pr_documents_to_pdf(pr):
    """
    Convert all PR documents to PDF when partially approved
    Handles conversion failures gracefully
    
    Args:
        pr: PurchaseRequest object
    
    Returns:
        dict: Status of conversions
    """
    results = {
        'main_document': False,
        'main_document_format': None,
        'supporting_docs': [],
        'errors': [],
        'warnings': []
    }
    
    try:
        # Convert main PR document
        if pr.uploaded_document:
            original_name = pr.uploaded_document.name
            original_ext = original_name.split('.')[-1].lower()
            print(f"🔄 Processing main document: {original_name} (format: {original_ext})")
            
            converted_file = ensure_pdf(pr.uploaded_document)
            
            if converted_file:
                # Check if it's actually a PDF
                if converted_file.name.lower().endswith('.pdf'):
                    # Save the PDF
                    pr.partially_approved_pdf = converted_file
                    pr.save(update_fields=['partially_approved_pdf'])
                    results['main_document'] = True
                    results['main_document_format'] = 'PDF'
                    print(f"✅ Main document saved as PDF")
                else:
                    # This shouldn't happen, but handle it
                    results['main_document'] = False
                    results['main_document_format'] = f'Original ({original_ext})'
                    results['warnings'].append(
                        f"File returned is not a PDF: {converted_file.name}"
                    )
            else:
                # Conversion failed
                results['main_document'] = False
                results['main_document_format'] = f'Original ({original_ext})'
                results['warnings'].append(
                    f"Failed to convert main document. Please convert manually before printing."
                )
                print(f"⚠️ Main document conversion failed")
        
        # Convert supporting documents
        supporting_docs = pr.supporting_documents.filter(is_signed_copy=False)
        
        for doc in supporting_docs:
            original_name = doc.document.name
            original_ext = original_name.split('.')[-1].lower()
            print(f"🔄 Processing supporting doc: {doc.file_name} (format: {original_ext})")
            
            converted_file = ensure_pdf(doc.document)
            
            if converted_file and converted_file.name.lower().endswith('.pdf'):
                # Update document with PDF version
                doc.document = converted_file
                doc.save()
                results['supporting_docs'].append({
                    'name': doc.file_name,
                    'format': 'PDF',
                    'success': True
                })
                print(f"✅ Supporting doc converted: {doc.file_name}")
            else:
                results['supporting_docs'].append({
                    'name': doc.file_name,
                    'format': f'Original ({original_ext})',
                    'success': False
                })
                results['warnings'].append(
                    f"Failed to convert '{doc.file_name}'"
                )
                print(f"⚠️ Supporting doc conversion failed: {doc.file_name}")
        
        # Summary
        successful_conversions = (
            (1 if results['main_document'] else 0) +
            sum(1 for doc in results['supporting_docs'] if doc['success'])
        )
        total_docs = 1 + len(results['supporting_docs'])
        
        print(f"📊 Conversion summary: {successful_conversions}/{total_docs} documents converted successfully")
        
        return results

    except Exception as e:
        print(f"❌ Error in convert_pr_documents_to_pdf: {e}")
        import traceback
        traceback.print_exc()
        results['errors'].append(str(e))
        return results


def convert_ad_documents_to_pdf(ad):
    """
    Convert all AD documents to PDF when partially approved
    Handles conversion failures gracefully

    Args:
        ad: ActivityDesign object

    Returns:
        dict: Status of conversions
    """
    results = {
        'main_document': False,
        'main_document_format': None,
        'supporting_docs': [],
        'errors': [],
        'warnings': []
    }

    try:
        # Convert main AD document
        if ad.uploaded_document:
            original_name = ad.uploaded_document.name
            original_ext = original_name.split('.')[-1].lower()
            print(f"🔄 Processing main AD document: {original_name} (format: {original_ext})")

            converted_file = ensure_pdf(ad.uploaded_document)

            if converted_file:
                # Check if it's actually a PDF
                if converted_file.name.lower().endswith('.pdf'):
                    # Save the PDF
                    ad.partially_approved_pdf = converted_file
                    ad.save(update_fields=['partially_approved_pdf'])
                    results['main_document'] = True
                    results['main_document_format'] = 'PDF'
                    print(f"✅ Main AD document saved as PDF")
                else:
                    # This shouldn't happen, but handle it
                    results['main_document'] = False
                    results['main_document_format'] = f'Original ({original_ext})'
                    results['warnings'].append(
                        f"File returned is not a PDF: {converted_file.name}"
                    )
            else:
                # Conversion failed
                results['main_document'] = False
                results['main_document_format'] = f'Original ({original_ext})'
                results['warnings'].append(
                    f"Failed to convert main AD document. Please convert manually before printing."
                )
                print(f"⚠️ Main AD document conversion failed")

        # Convert supporting documents
        supporting_docs = ad.supporting_documents.filter(is_signed_copy=False)

        for doc in supporting_docs:
            original_name = doc.document.name
            original_ext = original_name.split('.')[-1].lower()
            print(f"🔄 Processing AD supporting doc: {doc.file_name} (format: {original_ext})")

            converted_file = ensure_pdf(doc.document)

            if converted_file and converted_file.name.lower().endswith('.pdf'):
                # Update document with PDF version
                doc.document = converted_file
                doc.save()
                results['supporting_docs'].append({
                    'name': doc.file_name,
                    'format': 'PDF',
                    'success': True
                })
                print(f"✅ AD supporting doc converted: {doc.file_name}")
            else:
                results['supporting_docs'].append({
                    'name': doc.file_name,
                    'format': f'Original ({original_ext})',
                    'success': False
                })
                results['warnings'].append(
                    f"Failed to convert '{doc.file_name}'"
                )
                print(f"⚠️ AD supporting doc conversion failed: {doc.file_name}")

        # Summary
        successful_conversions = (
            (1 if results['main_document'] else 0) +
            sum(1 for doc in results['supporting_docs'] if doc['success'])
        )
        total_docs = 1 + len(results['supporting_docs'])

        print(f"📊 AD Conversion summary: {successful_conversions}/{total_docs} documents converted successfully")

        return results

    except Exception as e:
        print(f"❌ Error in convert_ad_documents_to_pdf: {e}")
        import traceback
        traceback.print_exc()
        results['errors'].append(str(e))
        return results