from flask import Blueprint, request, jsonify, current_app
from models.models import Document, ExtractedText, Project, Task, Decision, Risk, Dependency, Evidence, Activity
from database.db import db
from routes.auth_helpers import login_required, get_current_user
from services.ai_engine import AIEngine
from services.evidence_service import EvidenceService

analysis_bp = Blueprint('analysis', __name__, url_prefix='/api/analysis')

@analysis_bp.route('/<int:document_id>', methods=['POST'])
@login_required
def analyze_document(document_id):
    user = get_current_user()
    doc = Document.query.get(document_id)
    if not doc or doc.user_id != user.id:
        return jsonify({'error': 'Document not found or access denied.'}), 404

    project = Project.query.get(doc.project_id)
    extracted_records = ExtractedText.query.filter_by(document_id=doc.id).order_by(ExtractedText.page_number.asc()).all()

    if not extracted_records:
        return jsonify({'error': 'This document has no extracted text to analyze.'}), 400

    pages = [{
        'page_number': r.page_number,
        'text': r.full_text,
        'section': r.section_title
    } for r in extracted_records]

    try:
        engine = AIEngine(
            gemini_api_key=current_app.config.get('GEMINI_API_KEY'),
            openai_api_key=current_app.config.get('OPENAI_API_KEY')
        )
        result = engine.analyze_document_content(pages, project)

        # 1. Clean existing records associated with this document to avoid duplicates
        existing_tasks = Task.query.filter_by(document_id=doc.id).all()
        for t in existing_tasks:
            Evidence.query.filter_by(entity_type='task', entity_id=t.id).delete()
            db.session.delete(t)

        existing_decisions = Decision.query.filter_by(document_id=doc.id).all()
        for d in existing_decisions:
            Evidence.query.filter_by(entity_type='decision', entity_id=d.id).delete()
            db.session.delete(d)

        existing_risks = Risk.query.filter_by(document_id=doc.id).all()
        for r in existing_risks:
            Evidence.query.filter_by(entity_type='risk', entity_id=r.id).delete()
            db.session.delete(r)

        db.session.commit()

        # 2. Persist Tasks and link Evidence
        persisted_tasks = []
        for t_data in result.get('tasks', []):
            task = Task(
                project_id=project.id,
                document_id=doc.id,
                description=t_data.get('description'),
                responsible_person=t_data.get('responsible_person', 'Unassigned'),
                deadline=t_data.get('deadline'),
                status=t_data.get('status', 'Pending'),
                priority=t_data.get('priority', 'Medium'),
                verification_status='AI-Generated',
                confidence=t_data.get('confidence', 0.85)
            )
            db.session.add(task)
            db.session.flush()

            # Create evidence link
            EvidenceService.link_evidence(
                entity_type='task',
                entity_id=task.id,
                document_id=doc.id,
                original_text=t_data.get('evidence_text', task.description),
                page_number=t_data.get('page_number', 1),
                extraction_ref=t_data.get('extraction_ref', f"Page {t_data.get('page_number', 1)}"),
                confidence=task.confidence
            )
            persisted_tasks.append(task)

        # 3. Persist Decisions and link Evidence
        persisted_decisions = []
        for d_data in result.get('decisions', []):
            decision = Decision(
                project_id=project.id,
                document_id=doc.id,
                title=d_data.get('title'),
                description=d_data.get('description'),
                reason=d_data.get('reason'),
                decision_date=d_data.get('decision_date'),
                status=d_data.get('status', 'Approved'),
                verification_status='AI-Generated',
                confidence=d_data.get('confidence', 0.88)
            )
            db.session.add(decision)
            db.session.flush()

            # Create evidence link
            EvidenceService.link_evidence(
                entity_type='decision',
                entity_id=decision.id,
                document_id=doc.id,
                original_text=d_data.get('evidence_text', decision.description),
                page_number=d_data.get('page_number', 1),
                extraction_ref=d_data.get('extraction_ref', f"Page {d_data.get('page_number', 1)}"),
                confidence=decision.confidence
            )
            persisted_decisions.append(decision)

        # 4. Persist Risks and link Evidence
        for r_data in result.get('risks', []):
            risk = Risk(
                project_id=project.id,
                document_id=doc.id,
                description=r_data.get('description'),
                category=r_data.get('category', 'Technical'),
                severity=r_data.get('severity', 'Medium'),
                suggested_action=r_data.get('suggested_action'),
                verification_status='AI-Generated'
            )
            db.session.add(risk)
            db.session.flush()

            EvidenceService.link_evidence(
                entity_type='risk',
                entity_id=risk.id,
                document_id=doc.id,
                original_text=r_data.get('evidence_text', risk.description),
                page_number=r_data.get('page_number', 1),
                extraction_ref=r_data.get('extraction_ref', 'Risk Discovery'),
                confidence=0.85
            )

        # 5. Persist Dependencies if matching tasks exist
        for dep_data in result.get('dependencies', []):
            prereq_str = dep_data.get('prerequisite', '').lower()
            dependent_str = dep_data.get('dependent', '').lower()

            matched_prereq = next((t for t in persisted_tasks if any(word in t.description.lower() for word in prereq_str.split()[:3])), None)
            matched_dep = next((t for t in persisted_tasks if any(word in t.description.lower() for word in dependent_str.split()[:3])), None)

            if matched_prereq and matched_dep and matched_prereq.id != matched_dep.id:
                dep = Dependency(
                    project_id=project.id,
                    prerequisite_task_id=matched_prereq.id,
                    dependent_task_id=matched_dep.id,
                    description=dep_data.get('description'),
                    is_blocking=dep_data.get('is_blocking', True)
                )
                db.session.add(dep)

        doc.processing_status = 'Analysed'
        db.session.commit()

        # Log activity
        activity = Activity(
            project_id=project.id,
            user_id=user.id,
            user_name=user.full_name,
            activity_type='AI Analysis Completed',
            description=f"AI knowledge extraction performed on '{doc.original_filename}'. {len(persisted_tasks)} tasks and {len(persisted_decisions)} decisions extracted.",
            entity_type='document',
            entity_id=doc.id
        )
        db.session.add(activity)
        db.session.commit()

        return jsonify({
            'message': 'AI Knowledge extraction completed successfully.',
            'analysis': result,
            'summary': result.get('executive_summary'),
            'tasks_count': len(persisted_tasks),
            'decisions_count': len(persisted_decisions),
            'risks_count': len(result.get('risks', []))
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f"AI Analysis failed: {str(e)}"}), 500

@analysis_bp.route('/project/<int:project_id>', methods=['POST'])
@login_required
def analyze_project_documents(project_id):
    """
    Batch multi-document analysis for all documents in a project.
    """
    user = get_current_user()
    project = Project.query.filter_by(id=project_id, user_id=user.id).first()
    if not project:
        return jsonify({'error': 'Project not found or access denied.'}), 404

    docs = Document.query.filter_by(project_id=project.id).all()
    if not docs:
        return jsonify({'error': 'No documents found in this project to analyze.'}), 400

    all_pages = []
    for doc in docs:
        records = ExtractedText.query.filter_by(document_id=doc.id).order_by(ExtractedText.page_number.asc()).all()
        for r in records:
            all_pages.append({
                'page_number': r.page_number,
                'text': r.full_text,
                'section': f"{doc.original_filename} (p. {r.page_number})"
            })

    engine = AIEngine(
        gemini_api_key=current_app.config.get('GEMINI_API_KEY'),
        openai_api_key=current_app.config.get('OPENAI_API_KEY')
    )
    result = engine.analyze_document_content(all_pages, project)

    # Mark all documents as Analysed
    for d in docs:
        d.processing_status = 'Analysed'
    db.session.commit()

    return jsonify({
        'message': f"Batch AI analysis completed across {len(docs)} documents.",
        'analysis': result
    }), 200

@analysis_bp.route('/<int:project_id>', methods=['GET'])
@login_required
def get_project_analysis(project_id):
    user = get_current_user()
    project = Project.query.filter_by(id=project_id, user_id=user.id).first()
    if not project:
        return jsonify({'error': 'Project not found or access denied.'}), 404

    tasks = Task.query.filter_by(project_id=project.id).all()
    decisions = Decision.query.filter_by(project_id=project.id).all()
    risks = Risk.query.filter_by(project_id=project.id).all()
    dependencies = Dependency.query.filter_by(project_id=project.id).all()

    # Build analysis breakdown
    responsibilities = {}
    for t in tasks:
        owner = t.responsible_person or 'Unassigned'
        if owner not in responsibilities:
            responsibilities[owner] = []
        responsibilities[owner].append(t.description)

    deadlines = []
    for t in tasks:
        if t.deadline and t.deadline not in ('Not specified', 'Pending scheduling'):
            deadlines.append({
                'item': t.description,
                'deadline': t.deadline,
                'responsible': t.responsible_person,
                'status': t.status
            })

    # Missing info
    missing_info = []
    unassigned = [t for t in tasks if t.responsible_person == 'Unassigned']
    if unassigned:
        missing_info.append(f"{len(unassigned)} tasks require ownership assignment.")
    if not decisions:
        missing_info.append("No technical decisions currently documented.")

    return jsonify({
        'project': project.to_dict(),
        'tasks': [t.to_dict() for t in tasks],
        'decisions': [d.to_dict() for d in decisions],
        'risks': [r.to_dict() for r in risks],
        'dependencies': [dp.to_dict() for dp in dependencies],
        'responsibilities': responsibilities,
        'deadlines': deadlines,
        'missing_information': missing_info
    }), 200
