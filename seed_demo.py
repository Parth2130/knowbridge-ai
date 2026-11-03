import os
import fitz  # PyMuPDF
from docx import Document as DocxDocument
from app import create_app
from database.db import db
from models.models import (
    User, Project, Document, ExtractedText, Task, Decision,
    Risk, Dependency, Evidence, HandoverReport, ReportVersion,
    Approval, Acknowledgement, Activity
)
from services.report_generator import ReportGenerator
import json
from datetime import datetime

def generate_sample_documents(upload_folder):
    os.makedirs(upload_folder, exist_ok=True)
    
    # 1. Sample PDF: Cloud Infrastructure Migration & Handover Guide
    pdf_path = os.path.join(upload_folder, "demo_infrastructure_handover.pdf")
    doc = fitz.open()
    
    # Page 1
    page1 = doc.new_page()
    text_p1 = """KNOWBRIDGE AI — DEMO PROJECT HANDOVER SPECIFICATION
Project: Cloud Core Microservices Architecture Transition
Outgoing Engineer: Sarah Jenkins (Senior DevOps Architect)
Incoming Engineer: Alex Chen (Staff Platform Engineer)

1. Executive Architecture Summary
The Cloud Core platform provides mission-critical telemetry, billing aggregation, and user identity services across AWS and GCP multi-region deployments.
Over the past 6 months, we migrated our legacy monolithic payment processing service to an asynchronous event-driven Kubernetes architecture utilizing Apache Kafka.

2. Important Decisions
Decision: We decided to deploy RabbitMQ for internal queuing instead of AWS SQS because on-premise local dev simulation required offline capability without AWS cloud costs.
Decision: Selected PostgreSQL 16 with Citus extension for sharded transaction history due to strict ACID compliance requirements.
Decision: Approved the use of Terraform Cloud for automated state locking and branch-based deployment verification.

3. Action Items and Tasks
• Task: Complete database replication latency stress test before payment gateway migration. Assigned to: Alex Chen. Due by: 2026-11-20. Status: In Progress.
• Task: Rotate staging database master encryption keys and update HashiCorp Vault access policies. Assigned to: Sarah Jenkins. Due by: 2026-11-15. Status: Completed.
• Task: Implement automated rollback pipeline for Kubernetes cluster ingress controllers. Assigned to: Alex Chen. Due by: 2026-11-28. Status: Pending.
"""
    page1.insert_text((50, 60), text_p1, fontsize=10)

    # Page 2
    page2 = doc.new_page()
    text_p2 = """Cloud Core Microservices — Handover Guide (Page 2)

4. Identified Operational Risks
• Risk: 2 critical background worker queues lack designated secondary maintainers.
• Risk: Redis session cache does not have automated cluster failover configured in the Frankfurt EU region, presenting single point of failure risk.
• Risk: Third-party payment webhooks timeout when upstream banking network experiences latency spikes exceeding 4500ms.

5. Key Dependencies
• Database integration must be completed before payment gateway integration.
• HashiCorp Vault secrets sync is required before Kubernetes production deployment.
• Security penetration sign-off must be completed before client DNS cutover.

6. Missing Documentation Items
• Disaster recovery runbook for Frankfurt region Redis cache is missing documentation.
• Client SDK rate limiting quotas require final architectural approval.
"""
    page2.insert_text((50, 60), text_p2, fontsize=10)
    doc.save(pdf_path)
    doc.close()

    # 2. Sample DOCX: Runbook and Deployment Specifications
    docx_path = os.path.join(upload_folder, "demo_deployment_runbook.docx")
    docx = DocxDocument()
    docx.add_heading("Cloud Core Deployment & Operational Runbook", level=1)
    docx.add_paragraph("Author: Sarah Jenkins | Target: Alex Chen")
    docx.add_heading("1. Service Deployment Instructions", level=2)
    docx.add_paragraph("All production services are deployed via Helm charts stored in git repository core-infra-helm.")
    docx.add_paragraph("Decision: Adopted ArgoCD for GitOps continuous delivery due to zero-drift audit requirements.")
    docx.add_heading("2. Pending Operational Tasks", level=2)
    docx.add_paragraph("• Task: Verify ArgoCD health checks on core notification worker pods. Assigned to: Alex Chen. Due by: 2026-11-25. Status: Pending.")
    docx.add_paragraph("• Task: Archive deprecated v1 REST endpoints and update API gateway routes. Assigned to: Sarah Jenkins. Due by: 2026-11-18. Status: In Progress.")
    docx.add_heading("3. Security Audit & Key Procedures", level=2)
    docx.add_paragraph("• Risk: Old SSH bastion host credentials remain active on backup jumpbox. Rotate immediately.")
    docx.save(docx_path)

    # 3. Sample TXT: Team Transition Meeting Notes
    txt_path = os.path.join(upload_folder, "demo_transition_meeting_notes.txt")
    txt_content = """TRANSITION MEETING NOTES — SPRINT 42 HANDOVER
Date: 2026-11-01
Attendees: Sarah Jenkins (Outgoing), Alex Chen (Incoming), Marcus Vance (Engineering Director)

Key Discussion Points:
1. Sarah outlined all IAM roles and access tokens required for Google Cloud and AWS.
2. Alex accepted primary on-call rotation starting next Monday.
3. Decision: Team agreed to standardize microservice logging format to OpenTelemetry JSON schema by end of year.
4. Action item: Conduct live shadow deployment this Thursday during the staging release window. Assigned to: Alex Chen. Due by: 2026-11-12. Status: Pending.
5. Action item: Update onboarding wiki with updated VPN certificate generation steps. Assigned to: Sarah Jenkins. Due by: 2026-11-10. Status: Completed.
"""
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(txt_content)

    return [
        ("demo_infrastructure_handover.pdf", pdf_path, "pdf", 2),
        ("demo_deployment_runbook.docx", docx_path, "docx", 1),
        ("demo_transition_meeting_notes.txt", txt_path, "txt", 1)
    ]

def seed(drop=True, target_app=None):
    def _execute():
        if drop:
            print("[1/5] Dropping and re-creating clean database tables...")
            db.drop_all()
            db.create_all()
        else:
            print("[1/5] Initializing tables...")
            db.create_all()

        print("[2/5] Creating demo user accounts...")
        demo_user = User(
            full_name="Alex Chen",
            email="demo@knowbridge.ai",
            organisation="Acme Cloud Technologies",
            role="Project Manager"
        )
        demo_user.set_password("password123")
        db.session.add(demo_user)

        admin_user = User(
            full_name="Sarah Jenkins",
            email="sarah.jenkins@knowbridge.ai",
            organisation="Acme Cloud Technologies",
            role="Administrator"
        )
        admin_user.set_password("admin123")
        db.session.add(admin_user)
        db.session.commit()

        print("[3/5] Creating sample demo projects...")
        demo_project = Project(
            user_id=demo_user.id,
            name="Cloud Core Microservices Handover [DEMO]",
            description="Comprehensive engineering transition of multi-cloud infrastructure, Kafka streaming pipelines, and billing aggregation services.",
            category="Cloud Infrastructure",
            outgoing_member="Sarah Jenkins (Senior DevOps Architect)",
            incoming_member="Alex Chen (Staff Platform Engineer)",
            start_date="2026-10-15",
            deadline="2026-12-01",
            status="Active"
        )
        db.session.add(demo_project)

        project_2 = Project(
            user_id=demo_user.id,
            name="Customer Identity & IAM Migration",
            description="Migration of Auth0 authentication flows to self-hosted Ory Kratos and Hydra OAuth2 server.",
            category="Security & Identity",
            outgoing_member="Marcus Vance",
            incoming_member="Alex Chen",
            start_date="2026-11-01",
            deadline="2026-12-15",
            status="Active"
        )
        db.session.add(project_2)
        db.session.commit()

        print("[4/5] Generating real sample files and extracting documents...")
        upload_folder = app.config['UPLOAD_FOLDER']
        sample_files = generate_sample_documents(upload_folder)

        created_docs = []
        for orig_name, file_path, ftype, page_count in sample_files:
            file_size = os.path.getsize(file_path)
            doc_rec = Document(
                project_id=demo_project.id,
                user_id=demo_user.id,
                original_filename=orig_name,
                stored_filename=os.path.basename(file_path),
                file_path=file_path,
                file_type=ftype,
                file_size=file_size,
                processing_status='Analysed',
                page_count=page_count
            )
            db.session.add(doc_rec)
            db.session.flush()

            # Read text
            with open(file_path, 'rb') as f:
                content_bytes = f.read()

            extracted = ExtractedText(
                document_id=doc_rec.id,
                full_text=f"Sample extracted text for {orig_name}",
                page_number=1,
                section_title="Main Content"
            )
            db.session.add(extracted)
            created_docs.append(doc_rec)

        db.session.commit()

        print("[5/5] Seeding real extracted tasks, decisions, risks, dependencies, evidence, and report...")
        primary_doc = created_docs[0]

        # Tasks
        t1 = Task(
            project_id=demo_project.id,
            document_id=primary_doc.id,
            description="Complete database replication latency stress test before payment gateway migration",
            responsible_person="Alex Chen",
            deadline="2026-11-20",
            status="In Progress",
            priority="High",
            verification_status="Approved",
            confidence=0.94
        )
        t2 = Task(
            project_id=demo_project.id,
            document_id=primary_doc.id,
            description="Rotate staging database master encryption keys and update HashiCorp Vault policies",
            responsible_person="Sarah Jenkins",
            deadline="2026-11-15",
            status="Completed",
            priority="High",
            verification_status="Approved",
            confidence=0.96
        )
        t3 = Task(
            project_id=demo_project.id,
            document_id=primary_doc.id,
            description="Implement automated rollback pipeline for Kubernetes cluster ingress controllers",
            responsible_person="Alex Chen",
            deadline="2026-11-28",
            status="Pending",
            priority="Medium",
            verification_status="Approved",
            confidence=0.88
        )
        t4 = Task(
            project_id=demo_project.id,
            document_id=primary_doc.id,
            description="Verify ArgoCD health checks on core notification worker pods",
            responsible_person="Alex Chen",
            deadline="2026-11-25",
            status="Pending",
            priority="Low",
            verification_status="AI-Generated",
            confidence=0.85
        )
        t5 = Task(
            project_id=demo_project.id,
            document_id=primary_doc.id,
            description="Audit Frankfurt EU region Redis cluster backup automated failover scripts",
            responsible_person="Unassigned",
            deadline="Not specified",
            status="Pending",
            priority="High",
            verification_status="Under Review",
            confidence=0.79
        )
        db.session.add_all([t1, t2, t3, t4, t5])
        db.session.flush()

        # Evidence for tasks
        e1 = Evidence(
            entity_type='task',
            entity_id=t1.id,
            document_id=primary_doc.id,
            original_text="Complete database replication latency stress test before payment gateway migration. Assigned to: Alex Chen. Due by: 2026-11-20.",
            page_number=1,
            extraction_reference="Document Page 1, Section 3",
            confidence_score=0.94
        )
        e2 = Evidence(
            entity_type='task',
            entity_id=t2.id,
            document_id=primary_doc.id,
            original_text="Rotate staging database master encryption keys and update HashiCorp Vault access policies. Assigned to: Sarah Jenkins.",
            page_number=1,
            extraction_reference="Document Page 1, Section 3",
            confidence_score=0.96
        )
        db.session.add_all([e1, e2])

        # Decisions
        d1 = Decision(
            project_id=demo_project.id,
            document_id=primary_doc.id,
            title="Deploy RabbitMQ for internal queuing instead of AWS SQS",
            description="Project team decided to utilize RabbitMQ instead of AWS SQS for local development offline simulations.",
            reason="Required offline developer testing capability without incurring AWS cloud simulation overhead.",
            decision_date="2026-10-18",
            status="Approved",
            verification_status="Approved",
            confidence=0.92
        )
        d2 = Decision(
            project_id=demo_project.id,
            document_id=primary_doc.id,
            title="Selected PostgreSQL 16 with Citus extension for sharded transaction history",
            description="Adopted PostgreSQL with Citus for multi-tenant table horizontal partitioning.",
            reason="Strict ACID transactional compliance and automated cross-region shard distribution.",
            decision_date="2026-10-22",
            status="Approved",
            verification_status="Approved",
            confidence=0.95
        )
        d3 = Decision(
            project_id=demo_project.id,
            document_id=primary_doc.id,
            title="Adopted ArgoCD for GitOps continuous delivery",
            description="Declarative git-driven deployment configuration to replace manual Jenkins scripts.",
            reason="Eliminates configuration drift and satisfies SOC2 continuous deployment audit trails.",
            decision_date="2026-10-30",
            status="Approved",
            verification_status="Approved",
            confidence=0.90
        )
        db.session.add_all([d1, d2, d3])
        db.session.flush()

        # Evidence for decisions
        ed1 = Evidence(
            entity_type='decision',
            entity_id=d1.id,
            document_id=primary_doc.id,
            original_text="We decided to deploy RabbitMQ for internal queuing instead of AWS SQS because on-premise local dev simulation required offline capability without AWS cloud costs.",
            page_number=1,
            extraction_reference="Document Page 1, Section 2",
            confidence_score=0.92
        )
        db.session.add(ed1)

        # Risks
        r1 = Risk(
            project_id=demo_project.id,
            document_id=primary_doc.id,
            related_task_id=t5.id,
            description="Redis session cache does not have automated cluster failover configured in the Frankfurt EU region",
            category="Technical",
            severity="High",
            suggested_action="Deploy Redis Sentinel multi-AZ replica configuration before production client cutover.",
            verification_status="Approved"
        )
        r2 = Risk(
            project_id=demo_project.id,
            document_id=primary_doc.id,
            description="Old SSH bastion host credentials remain active on backup jumpbox",
            category="Security",
            severity="High",
            suggested_action="Decommission legacy jumpbox and rotate all remaining SSH public keys.",
            verification_status="Approved"
        )
        r3 = Risk(
            project_id=demo_project.id,
            document_id=primary_doc.id,
            description="1 identified task currently lacks an assigned technical owner",
            category="Resource",
            severity="Medium",
            suggested_action="Assign incoming engineer during formal transition sign-off.",
            verification_status="AI-Generated"
        )
        db.session.add_all([r1, r2, r3])

        # Dependencies
        dep1 = Dependency(
            project_id=demo_project.id,
            prerequisite_task_id=t1.id,
            dependent_task_id=t3.id,
            description="Database replication latency stress test must be completed before deploying ingress rollback pipeline.",
            is_blocking=True
        )
        db.session.add(dep1)

        # Activities for Timeline
        act1 = Activity(
            project_id=demo_project.id,
            user_id=demo_user.id,
            user_name="Sarah Jenkins",
            activity_type="Project Created",
            description="Project 'Cloud Core Microservices Handover [DEMO]' initialized.",
            entity_type="project",
            entity_id=demo_project.id
        )
        act2 = Activity(
            project_id=demo_project.id,
            user_id=demo_user.id,
            user_name="Sarah Jenkins",
            activity_type="Document Uploaded",
            description="Uploaded 'demo_infrastructure_handover.pdf' (2 pages).",
            entity_type="document",
            entity_id=primary_doc.id
        )
        act3 = Activity(
            project_id=demo_project.id,
            user_id=demo_user.id,
            user_name="System AI",
            activity_type="AI Analysis Completed",
            description="AI Knowledge extraction identified 5 tasks, 3 architectural decisions, and 3 risks.",
            entity_type="document",
            entity_id=primary_doc.id
        )
        act4 = Activity(
            project_id=demo_project.id,
            user_id=demo_user.id,
            user_name="Alex Chen",
            activity_type="Task Completed",
            description="Completed 'Rotate staging database master encryption keys'.",
            entity_type="task",
            entity_id=t2.id
        )
        db.session.add_all([act1, act2, act3, act4])
        db.session.commit()

        # Generate full Handover Report
        report_data = ReportGenerator.compile_report_data(demo_project.id, demo_user.id)
        report_json = json.dumps(report_data)

        report = HandoverReport(
            project_id=demo_project.id,
            user_id=demo_user.id,
            title="Comprehensive Knowledge Handover — Cloud Core Microservices",
            outgoing_member="Sarah Jenkins",
            incoming_member="Alex Chen",
            summary=report_data.get('5_project_summary'),
            status="Generated",
            current_version=1,
            content_json=report_json
        )
        db.session.add(report)
        db.session.flush()

        v1 = ReportVersion(
            report_id=report.id,
            version_number=1,
            content_json=report_json,
            modified_by_id=demo_user.id,
            modified_by_name="Alex Chen",
            change_summary="Initial system-generated knowledge handover report."
        )
        db.session.add(v1)

        # Pending Acknowledgement
        ack = Acknowledgement(
            report_id=report.id,
            project_id=demo_project.id,
            incoming_member_id=demo_user.id,
            incoming_member_name="Alex Chen",
            status="Awaiting Acknowledgement",
            comments="Pending final review meeting before digital signature."
        )
        db.session.add(ack)

        db.session.commit()
        print("\n=======================================================")
        print("  DEMO DATA SUCCESSFULLY SEEDED!                      ")
        print("  Demo Login:                                         ")
        print("    Email: demo@knowbridge.ai                         ")
        print("    Password: password123                             ")
        print("  Admin Login:                                        ")
        print("    Email: sarah.jenkins@knowbridge.ai                ")
        print("    Password: admin123                                ")
        print("=======================================================")

    if target_app:
        with target_app.app_context():
            _execute()
    else:
        app = create_app()
        with app.app_context():
            _execute()

if __name__ == '__main__':
    seed()
