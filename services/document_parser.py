import os
import fitz  # PyMuPDF
from docx import Document as DocxDocument

class DocumentParser:
    @staticmethod
    def parse(file_path, file_type):
        """
        Parses document file and extracts text page-by-page or section-by-section.
        Returns a dict:
        {
            'pages': [{'page_number': 1, 'text': '...', 'section': '...'}],
            'full_text': '...',
            'page_count': int
        }
        """
        file_type = file_type.lower()
        if file_type == 'pdf':
            return DocumentParser._parse_pdf(file_path)
        elif file_type == 'docx':
            return DocumentParser._parse_docx(file_path)
        elif file_type == 'txt':
            return DocumentParser._parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    @staticmethod
    def _parse_pdf(file_path):
        doc = fitz.open(file_path)
        pages = []
        full_text_list = []
        
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_text = page.get_text("text").strip()
            pages.append({
                'page_number': page_idx + 1,
                'text': page_text,
                'section': f"Page {page_idx + 1}"
            })
            if page_text:
                full_text_list.append(page_text)
                
        doc.close()
        return {
            'pages': pages,
            'full_text': "\n\n".join(full_text_list),
            'page_count': max(1, len(pages))
        }

    @staticmethod
    def _parse_docx(file_path):
        doc = DocxDocument(file_path)
        pages = []
        full_text_list = []
        current_section = "Overview"
        current_chunk = []
        virtual_page = 1
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
                
            if para.style.name.startswith('Heading') or len(text) < 60 and text.isupper():
                if current_chunk:
                    pages.append({
                        'page_number': virtual_page,
                        'text': "\n".join(current_chunk),
                        'section': current_section
                    })
                    virtual_page += 1
                    current_chunk = []
                current_section = text
                
            current_chunk.append(text)
            full_text_list.append(text)
            
            # Divide into virtual pages every 2500 characters
            if sum(len(c) for c in current_chunk) > 2500:
                pages.append({
                    'page_number': virtual_page,
                    'text': "\n".join(current_chunk),
                    'section': current_section
                })
                virtual_page += 1
                current_chunk = []
                
        if current_chunk:
            pages.append({
                'page_number': virtual_page,
                'text': "\n".join(current_chunk),
                'section': current_section
            })

        # Also extract table text
        for table in doc.tables:
            table_lines = []
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    table_lines.append(" | ".join(row_cells))
            if table_lines:
                tbl_text = "\n".join(table_lines)
                full_text_list.append(tbl_text)
                pages.append({
                    'page_number': virtual_page,
                    'text': tbl_text,
                    'section': "Data Table"
                })
                virtual_page += 1

        return {
            'pages': pages if pages else [{'page_number': 1, 'text': '', 'section': 'Main'}],
            'full_text': "\n\n".join(full_text_list),
            'page_count': max(1, len(pages))
        }

    @staticmethod
    def _parse_txt(file_path):
        text = ""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                text = f.read()
                
        chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
        pages = []
        page_num = 1
        acc = []
        
        for chunk in chunks:
            acc.append(chunk)
            if sum(len(c) for c in acc) > 2000:
                pages.append({
                    'page_number': page_num,
                    'text': "\n\n".join(acc),
                    'section': f"Section {page_num}"
                })
                page_num += 1
                acc = []
                
        if acc:
            pages.append({
                'page_number': page_num,
                'text': "\n\n".join(acc),
                'section': f"Section {page_num}"
            })
            
        return {
            'pages': pages if pages else [{'page_number': 1, 'text': text, 'section': 'Main'}],
            'full_text': text,
            'page_count': max(1, len(pages))
        }
