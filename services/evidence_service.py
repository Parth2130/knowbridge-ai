from models.models import Evidence, Document
from database.db import db

class EvidenceService:
    @staticmethod
    def link_evidence(entity_type, entity_id, document_id, original_text, page_number=None, extraction_ref=None, confidence=0.88):
        """
        Creates or updates an evidence record associated with a task, decision, or risk.
        """
        if not original_text or not original_text.strip():
            return None

        evidence = Evidence(
            entity_type=entity_type,
            entity_id=entity_id,
            document_id=document_id,
            original_text=original_text.strip(),
            page_number=page_number,
            extraction_reference=extraction_ref or f"Document {document_id}",
            confidence_score=confidence
        )
        db.session.add(evidence)
        db.session.commit()
        return evidence

    @staticmethod
    def get_evidence_for_entity(entity_type, entity_id):
        """
        Fetches evidence for a specific entity (task, decision, risk).
        """
        evidence_item = Evidence.query.filter_by(entity_type=entity_type, entity_id=entity_id).first()
        if evidence_item:
            return evidence_item.to_dict()
        return None
