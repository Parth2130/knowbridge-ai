import os
import uuid
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from models.models import Document, ExtractedText, Project, Activity
from database.db import db
from routes.auth_helpers import login_required, get_current_user
from services.document_parser import DocumentParser

documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@documents_bp.route('', methods=['GET'])
@login_required
def list_documents():
    user = get_current_user()
    project_id = request.args.get('project_id', type=int)
    file_type = request.args.get('file_type', '').strip().lower()
    search = request.args.get('search', '').strip().lower()

    user_projects = Project.query.filter_by(user_id=user.id).all()
    project_ids = [p.id for p in user_projects]

    if not project_ids:
        return jsonify({'documents': []}), 200

    query = Document.query.filter(Document.project_id.in_(project_ids))

    if project_id and project_id in project_ids:
        query = query.filter_by(project_id=project_id)
    if file_type and file_type != 'all':
        query = query.filter_by(file_type=file_type)
    if search:
        query = query.filter(Document.original_filename.ilike(f'%{search}%'))

    documents = query.order_by(Document.uploaded_at.desc()).all()
    return jsonify({'documents': [d.to_dict() for d in documents]}), 200

@documents_bp.route('/upload', methods=['POST'])
@login_required
def upload_document():
    user = get_current_user()

    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request.'}), 400

    file = request.files['file']
    project_id = request.form.get('project_id', type=int)

    if not file or file.filename == '':
        return jsonify({'error': 'No selected file.'}), 400

    if not project_id:
        return jsonify({'error': 'Please select a project for this document.'}), 400

    project = Project.query.filter_by(id=project_id, user_id=user.id).first()
    if not project:
        return jsonify({'error': 'Project not found or access denied.'}), 404

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file format. Only PDF, DOCX, and TXT files are accepted.'}), 400

    orig_filename = secure_filename(file.filename)
    extension = orig_filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}_{orig_filename}"

    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    saved_path = os.path.join(upload_folder, unique_filename)

    file.save(saved_path)
    file_size = os.path.getsize(saved_path)

    # Create document record
    doc = Document(
        project_id=project.id,
        user_id=user.id,
        original_filename=orig_filename,
        stored_filename=unique_filename,
        file_path=saved_path,
        file_type=extension,
        file_size=file_size,
        processing_status='Uploaded'
    )
    db.session.add(doc)
    db.session.commit()

    # Extract text immediately
    try:
        parsed_result = DocumentParser.parse(saved_path, extension)
        pages = parsed_result.get('pages', [])
        doc.page_count = parsed_result.get('page_count', 1)

        for p in pages:
            ex = ExtractedText(
                document_id=doc.id,
                full_text=p.get('text', ''),
                page_number=p.get('page_number', 1),
                section_title=p.get('section', 'General')
            )
            db.session.add(ex)

        doc.processing_status = 'Extracted'
        db.session.commit()

        # Log activity
        activity = Activity(
            project_id=project.id,
            user_id=user.id,
            user_name=user.full_name,
            activity_type='Document Uploaded',
            description=f"Document '{orig_filename}' uploaded and text extracted ({doc.page_count} pages).",
            entity_type='document',
            entity_id=doc.id
        )
        db.session.add(activity)
        db.session.commit()

        return jsonify({
            'message': f"Document '{orig_filename}' uploaded and text extracted successfully.",
            'document': doc.to_dict()
        }), 201

    except Exception as e:
        doc.processing_status = 'Failed'
        db.session.commit()
        return jsonify({'error': f"Failed to extract document text: {str(e)}"}), 500

@documents_bp.route('/<int:doc_id>', methods=['GET'])
@login_required
def get_document(doc_id):
    user = get_current_user()
    doc = Document.query.get(doc_id)
    if not doc or doc.user_id != user.id:
        return jsonify({'error': 'Document not found or access denied.'}), 404

    # Include extracted pages text for preview
    extracted = ExtractedText.query.filter_by(document_id=doc.id).order_by(ExtractedText.page_number.asc()).all()
    pages_data = [{
        'page_number': e.page_number,
        'section_title': e.section_title,
        'text': e.full_text
    } for e in extracted]

    doc_data = doc.to_dict()
    doc_data['pages'] = pages_data
    doc_data['full_preview'] = "\n\n".join([p['text'] for p in pages_data])

    return jsonify({'document': doc_data}), 200

@documents_bp.route('/<int:doc_id>/download', methods=['GET'])
@login_required
def download_document(doc_id):
    user = get_current_user()
    doc = Document.query.get(doc_id)
    if not doc or doc.user_id != user.id:
        return jsonify({'error': 'Document not found or access denied.'}), 404

    if not os.path.exists(doc.file_path):
        return jsonify({'error': 'The requested file could not be found on disk.'}), 404

    return send_file(
        doc.file_path,
        as_attachment=True,
        download_name=doc.original_filename
    )

@documents_bp.route('/<int:doc_id>', methods=['DELETE'])
@login_required
def delete_document(doc_id):
    user = get_current_user()
    doc = Document.query.get(doc_id)
    if not doc or doc.user_id != user.id:
        return jsonify({'error': 'Document not found or access denied.'}), 404

    filename = doc.original_filename
    # Delete file from disk
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except OSError:
            pass

    db.session.delete(doc)
    db.session.commit()

    return jsonify({'message': f"Document '{filename}' deleted successfully."}), 200
