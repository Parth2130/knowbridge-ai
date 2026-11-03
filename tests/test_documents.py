import io
import fitz
from docx import Document as DocxDocument

def test_upload_and_extract_txt(auth_client, sample_project):
    txt_content = b"Task: Setup PostgreSQL replication by 2026-11-20. Assigned to: Alex Chen.\nDecision: We decided to use RabbitMQ for queueing."
    data = {
        'project_id': str(sample_project),
        'file': (io.BytesIO(txt_content), 'test_runbook.txt')
    }
    res = auth_client.post('/api/documents/upload', data=data, content_type='multipart/form-data')
    assert res.status_code == 201
    doc = res.get_json()['document']
    assert doc['original_filename'] == 'test_runbook.txt'
    assert doc['processing_status'] == 'Extracted'

    # Verify extracted text preview
    doc_id = doc['id']
    view_res = auth_client.get(f'/api/documents/{doc_id}')
    assert view_res.status_code == 200
    assert 'PostgreSQL replication' in view_res.get_json()['document']['full_preview']

def test_upload_and_extract_pdf(auth_client, sample_project):
    # Generate in-memory PDF using PyMuPDF
    pdf_doc = fitz.open()
    page = pdf_doc.new_page()
    page.insert_text((50, 50), "Important Architectural Decision: Standardized on AWS RDS.\n• Task: Complete security review by Friday.")
    pdf_bytes = pdf_doc.tobytes()
    pdf_doc.close()

    data = {
        'project_id': str(sample_project),
        'file': (io.BytesIO(pdf_bytes), 'architecture.pdf')
    }
    res = auth_client.post('/api/documents/upload', data=data, content_type='multipart/form-data')
    assert res.status_code == 201
    assert res.get_json()['document']['file_type'] == 'PDF'

def test_upload_and_extract_docx(auth_client, sample_project):
    # Generate in-memory DOCX
    docx = DocxDocument()
    docx.add_heading("Sprint Handover", level=1)
    docx.add_paragraph("Action item: Deploy Redis Sentinel cluster. Assigned to: Sarah Jenkins.")
    docx_io = io.BytesIO()
    docx.save(docx_io)
    docx_io.seek(0)

    data = {
        'project_id': str(sample_project),
        'file': (docx_io, 'sprint.docx')
    }
    res = auth_client.post('/api/documents/upload', data=data, content_type='multipart/form-data')
    assert res.status_code == 201
    assert res.get_json()['document']['file_type'] == 'DOCX'

def test_reject_unsafe_file_format(auth_client, sample_project):
    data = {
        'project_id': str(sample_project),
        'file': (io.BytesIO(b"echo 'malicious'"), 'script.sh')
    }
    res = auth_client.post('/api/documents/upload', data=data, content_type='multipart/form-data')
    assert res.status_code == 400
    assert 'Invalid file format' in res.get_json()['error']
