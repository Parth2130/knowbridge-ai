from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import db
import json

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    organisation = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='Project Manager')  # Administrator, Project Manager, Team Member
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = db.relationship('Project', backref='creator', cascade='all, delete-orphan', lazy=True)
    documents = db.relationship('Document', backref='uploader', cascade='all, delete-orphan', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'organisation': self.organisation,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), default='Engineering')
    outgoing_member = db.Column(db.String(120), nullable=False)
    incoming_member = db.Column(db.String(120), nullable=False)
    start_date = db.Column(db.String(50), nullable=True)
    deadline = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), default='Active')  # Active, Under Review, Completed, Archived
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Cascade relationships
    documents = db.relationship('Document', backref='project', cascade='all, delete-orphan', lazy=True)
    tasks = db.relationship('Task', backref='project', cascade='all, delete-orphan', lazy=True)
    decisions = db.relationship('Decision', backref='project', cascade='all, delete-orphan', lazy=True)
    risks = db.relationship('Risk', backref='project', cascade='all, delete-orphan', lazy=True)
    dependencies = db.relationship('Dependency', backref='project', cascade='all, delete-orphan', lazy=True)
    reports = db.relationship('HandoverReport', backref='project', cascade='all, delete-orphan', lazy=True)
    activities = db.relationship('Activity', backref='project', cascade='all, delete-orphan', lazy=True)
    acknowledgements = db.relationship('Acknowledgement', backref='project', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        total_tasks = len(self.tasks)
        completed_tasks = len([t for t in self.tasks if t.status == 'Completed'])
        progress = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'outgoing_member': self.outgoing_member,
            'incoming_member': self.incoming_member,
            'start_date': self.start_date,
            'deadline': self.deadline,
            'status': self.status,
            'document_count': len(self.documents),
            'task_count': total_tasks,
            'completed_task_count': completed_tasks,
            'progress': progress,
            'decision_count': len(self.decisions),
            'risk_count': len(self.risks),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else None
        }

class ProjectMember(db.Model):
    __tablename__ = 'project_members'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(50), default='Contributor')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)  # pdf, docx, txt
    file_size = db.Column(db.Integer, default=0)
    processing_status = db.Column(db.String(50), default='Uploaded')  # Uploaded, Extracted, Analysed, Failed
    page_count = db.Column(db.Integer, default=1)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    extracted_texts = db.relationship('ExtractedText', backref='document', cascade='all, delete-orphan', lazy=True)
    evidence_items = db.relationship('Evidence', backref='document', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'original_filename': self.original_filename,
            'file_type': self.file_type.upper(),
            'file_size': self.file_size,
            'file_size_formatted': f"{self.file_size / 1024:.1f} KB" if self.file_size < 1048576 else f"{self.file_size / 1048576:.2f} MB",
            'processing_status': self.processing_status,
            'page_count': self.page_count,
            'uploaded_at': self.uploaded_at.strftime('%Y-%m-%d %H:%M') if self.uploaded_at else None
        }

class ExtractedText(db.Model):
    __tablename__ = 'extracted_text'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    full_text = db.Column(db.Text, nullable=False)
    page_number = db.Column(db.Integer, default=1)
    section_title = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='SET NULL'), nullable=True)
    description = db.Column(db.Text, nullable=False)
    responsible_person = db.Column(db.String(120), default='Unassigned')
    deadline = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), default='Pending')  # Pending, In Progress, Completed, Blocked
    priority = db.Column(db.String(50), default='Medium')  # High, Medium, Low
    verification_status = db.Column(db.String(50), default='AI-Generated')  # AI-Generated, Under Review, Approved, Rejected
    confidence = db.Column(db.Float, default=0.85)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'document_id': self.document_id,
            'description': self.description,
            'responsible_person': self.responsible_person,
            'deadline': self.deadline,
            'status': self.status,
            'priority': self.priority,
            'verification_status': self.verification_status,
            'confidence': round(self.confidence, 2) if self.confidence else 0.85,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }

class Decision(db.Model):
    __tablename__ = 'decisions'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='SET NULL'), nullable=True)
    title = db.Column(db.String(250), nullable=False)
    description = db.Column(db.Text, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    decision_date = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), default='Approved')  # Approved, Under Review, Deprecated
    verification_status = db.Column(db.String(50), default='AI-Generated')  # AI-Generated, Under Review, Approved, Rejected
    confidence = db.Column(db.Float, default=0.88)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'document_id': self.document_id,
            'title': self.title,
            'description': self.description,
            'reason': self.reason,
            'decision_date': self.decision_date,
            'status': self.status,
            'verification_status': self.verification_status,
            'confidence': round(self.confidence, 2) if self.confidence else 0.88,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }

class Risk(db.Model):
    __tablename__ = 'risks'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='SET NULL'), nullable=True)
    related_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), default='Technical')  # Technical, Timeline, Resource, Security, Documentation
    severity = db.Column(db.String(50), default='Medium')  # High, Medium, Low
    suggested_action = db.Column(db.Text, nullable=True)
    verification_status = db.Column(db.String(50), default='AI-Generated')  # AI-Generated, Under Review, Approved, Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'document_id': self.document_id,
            'related_task_id': self.related_task_id,
            'description': self.description,
            'category': self.category,
            'severity': self.severity,
            'suggested_action': self.suggested_action,
            'verification_status': self.verification_status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }

class Dependency(db.Model):
    __tablename__ = 'dependencies'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    prerequisite_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    dependent_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    is_blocking = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    prerequisite_task = db.relationship('Task', foreign_keys=[prerequisite_task_id], backref='dependent_relations')
    dependent_task = db.relationship('Task', foreign_keys=[dependent_task_id], backref='prerequisite_relations')

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'prerequisite_task_id': self.prerequisite_task_id,
            'prerequisite_task_desc': self.prerequisite_task.description if self.prerequisite_task else None,
            'prerequisite_task_status': self.prerequisite_task.status if self.prerequisite_task else None,
            'dependent_task_id': self.dependent_task_id,
            'dependent_task_desc': self.dependent_task.description if self.dependent_task else None,
            'dependent_task_status': self.dependent_task.status if self.dependent_task else None,
            'description': self.description,
            'is_blocking': self.is_blocking,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }

class Evidence(db.Model):
    __tablename__ = 'evidence'
    
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False)  # task, decision, risk
    entity_id = db.Column(db.Integer, nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    original_text = db.Column(db.Text, nullable=False)
    page_number = db.Column(db.Integer, nullable=True)
    extraction_reference = db.Column(db.String(255), nullable=True)
    confidence_score = db.Column(db.Float, default=0.90)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'document_id': self.document_id,
            'document_name': self.document.original_filename if self.document else 'Unknown Document',
            'original_text': self.original_text,
            'page_number': self.page_number,
            'extraction_reference': self.extraction_reference,
            'confidence_score': round(self.confidence_score, 2) if self.confidence_score else 0.90,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }

class HandoverReport(db.Model):
    __tablename__ = 'handover_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    outgoing_member = db.Column(db.String(120), nullable=False)
    incoming_member = db.Column(db.String(120), nullable=False)
    summary = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='Generated')  # Draft, Generated, Approved, Acknowledged
    current_version = db.Column(db.Integer, default=1)
    content_json = db.Column(db.Text, nullable=False)  # Complete JSON snapshot of all 16 report sections
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    versions = db.relationship('ReportVersion', backref='report', cascade='all, delete-orphan', lazy=True)
    approvals = db.relationship('Approval', backref='report', cascade='all, delete-orphan', lazy=True)
    acknowledgements = db.relationship('Acknowledgement', backref='report', cascade='all, delete-orphan', lazy=True)

    def get_content(self):
        try:
            return json.loads(self.content_json)
        except Exception:
            return {}

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'user_id': self.user_id,
            'title': self.title,
            'outgoing_member': self.outgoing_member,
            'incoming_member': self.incoming_member,
            'summary': self.summary,
            'status': self.status,
            'current_version': self.current_version,
            'version_count': len(self.versions),
            'content': self.get_content(),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else None
        }

class ReportVersion(db.Model):
    __tablename__ = 'report_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('handover_reports.id', ondelete='CASCADE'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    content_json = db.Column(db.Text, nullable=False)
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    modified_by_name = db.Column(db.String(120), nullable=True)
    change_summary = db.Column(db.String(300), default='Updated report details')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'version_number': self.version_number,
            'modified_by_name': self.modified_by_name or 'System',
            'change_summary': self.change_summary,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }

class Approval(db.Model):
    __tablename__ = 'approvals'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('handover_reports.id', ondelete='CASCADE'), nullable=True)
    entity_type = db.Column(db.String(50), nullable=False)  # task, decision, risk, report
    entity_id = db.Column(db.Integer, nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    reviewer_name = db.Column(db.String(120), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # Approve, Reject, Edit
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'reviewer_name': self.reviewer_name,
            'action': self.action,
            'comments': self.comments,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }

class Acknowledgement(db.Model):
    __tablename__ = 'acknowledgements'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('handover_reports.id', ondelete='CASCADE'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    incoming_member_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    incoming_member_name = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(50), default='Awaiting Acknowledgement')  # Awaiting Acknowledgement, Acknowledged
    comments = db.Column(db.Text, nullable=True)
    signature_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'incoming_member_name': self.incoming_member_name,
            'status': self.status,
            'comments': self.comments,
            'signature_date': self.signature_date.strftime('%Y-%m-%d %H:%M') if self.signature_date else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }

class Activity(db.Model):
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    user_name = db.Column(db.String(120), nullable=False)
    activity_type = db.Column(db.String(100), nullable=False)  # Project Created, Document Uploaded, AI Analysis Completed, Task Added, Task Completed, Decision Recorded, Risk Identified, Report Generated, Report Approved, Handover Acknowledged
    description = db.Column(db.Text, nullable=False)
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'user_name': self.user_name,
            'activity_type': self.activity_type,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }
