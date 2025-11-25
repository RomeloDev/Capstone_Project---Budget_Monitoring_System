"""
Django management command to retroactively convert budget realignment supporting documents to PDF.

This command finds all BudgetRealignmentSupportingDocument records that don't have a converted_pdf
and converts them based on their file type:
- Images (jpg, jpeg, png) -> converted using PIL
- Office documents (docx, doc, xlsx, xls) -> converted using LibreOffice

Usage:
    python manage.py convert_realignment_documents

Options:
    --dry-run : Show what would be converted without actually converting
    --force : Re-convert all documents even if they already have converted_pdf
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.files.base import ContentFile
from apps.budgets.models import BudgetRealignmentSupportingDocument
from PIL import Image
from io import BytesIO
import subprocess
import tempfile
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Retroactively convert budget realignment supporting documents to PDF'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be converted without actually converting',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-convert all documents even if they already have converted_pdf',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        self.stdout.write(self.style.SUCCESS('Starting document conversion process...'))
        self.stdout.write('')

        # Find documents that need conversion
        if force:
            documents = BudgetRealignmentSupportingDocument.objects.filter(
                is_signed_copy=False
            ).order_by('uploaded_at')
            self.stdout.write(f"Force mode: Processing ALL {documents.count()} supporting documents")
        else:
            documents = BudgetRealignmentSupportingDocument.objects.filter(
                converted_pdf__isnull=True,
                is_signed_copy=False
            ).order_by('uploaded_at')
            self.stdout.write(f"Found {documents.count()} documents without converted PDFs")

        if not documents.exists():
            self.stdout.write(self.style.SUCCESS('No documents need conversion. All done!'))
            return

        self.stdout.write('')

        # Statistics
        total = documents.count()
        converted = 0
        skipped = 0
        failed = 0

        for idx, doc in enumerate(documents, 1):
            file_name = doc.file_name
            file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ''

            self.stdout.write(f"[{idx}/{total}] Processing: {file_name}")

            # Check if file type is convertible
            if file_ext not in ['jpg', 'jpeg', 'png', 'docx', 'doc', 'xlsx', 'xls']:
                self.stdout.write(self.style.WARNING(f"  → Skipped (unsupported file type: {file_ext})"))
                skipped += 1
                continue

            # Check if document file exists
            if not doc.document or not doc.document.name:
                self.stdout.write(self.style.ERROR(f"  → Failed (no document file)"))
                failed += 1
                continue

            if dry_run:
                self.stdout.write(self.style.NOTICE(f"  → Would convert {file_ext.upper()} to PDF (dry-run)"))
                converted += 1
                continue

            # Perform conversion
            try:
                pdf_content = None

                # Image conversion
                if file_ext in ['jpg', 'jpeg', 'png']:
                    self.stdout.write(f"  → Converting image to PDF...")
                    pdf_content = self._convert_image_to_pdf(doc.document)

                # Office document conversion
                elif file_ext in ['docx', 'doc', 'xlsx', 'xls']:
                    self.stdout.write(f"  → Converting {file_ext.upper()} to PDF (using LibreOffice)...")
                    pdf_content = self._convert_office_to_pdf(doc.document, file_ext)

                if pdf_content:
                    # Save converted PDF
                    pdf_filename = f"{file_name.rsplit('.', 1)[0]}_converted.pdf"
                    doc.converted_pdf.save(pdf_filename, ContentFile(pdf_content), save=True)
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Successfully converted to PDF"))
                    converted += 1
                else:
                    self.stdout.write(self.style.ERROR(f"  ✗ Conversion failed (no output)"))
                    failed += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Conversion failed: {str(e)}"))
                logger.error(f"Failed to convert {file_name}: {str(e)}", exc_info=True)
                failed += 1

            self.stdout.write('')

        # Summary
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Conversion Summary:'))
        self.stdout.write(f"  Total documents processed: {total}")
        self.stdout.write(self.style.SUCCESS(f"  Successfully converted: {converted}"))
        if skipped > 0:
            self.stdout.write(self.style.WARNING(f"  Skipped (unsupported): {skipped}"))
        if failed > 0:
            self.stdout.write(self.style.ERROR(f"  Failed: {failed}"))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        if dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.NOTICE('This was a DRY RUN. No files were actually converted.'))
            self.stdout.write(self.style.NOTICE('Run without --dry-run to perform actual conversions.'))

    def _convert_image_to_pdf(self, image_file):
        """Convert image to PDF using PIL"""
        try:
            # Open image
            image_file.seek(0)
            img = Image.open(image_file)

            # Handle different image modes
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = rgb_img
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Convert to PDF
            pdf_buffer = BytesIO()
            img.save(pdf_buffer, format='PDF', resolution=100.0)
            pdf_buffer.seek(0)

            return pdf_buffer.read()

        except Exception as e:
            logger.error(f"Image to PDF conversion error: {str(e)}", exc_info=True)
            return None

    def _convert_office_to_pdf(self, office_file, file_ext):
        """Convert Office document to PDF using LibreOffice"""
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as temp_input:
                office_file.seek(0)
                for chunk in office_file.chunks():
                    temp_input.write(chunk)
                temp_input_path = temp_input.name

            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Set export filter based on file type
                    if file_ext in ['docx', 'doc']:
                        export_filter = 'pdf:writer_pdf_Export'
                    else:  # xlsx, xls
                        export_filter = 'pdf:calc_pdf_Export'

                    # Run LibreOffice conversion
                    cmd = [
                        r"C:\Program Files\LibreOffice\program\soffice.exe",
                        '--headless',
                        '--invisible',
                        '--nocrashreport',
                        '--convert-to', export_filter,
                        '--outdir', temp_dir,
                        temp_input_path
                    ]

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )

                    if result.returncode == 0:
                        # Find the converted PDF
                        pdf_files = list(Path(temp_dir).glob('*.pdf'))
                        if pdf_files:
                            with open(pdf_files[0], 'rb') as pdf_file:
                                return pdf_file.read()

                    return None

            finally:
                # Clean up temporary input file
                if os.path.exists(temp_input_path):
                    os.remove(temp_input_path)

        except Exception as e:
            logger.error(f"Office to PDF conversion error: {str(e)}", exc_info=True)
            return None
