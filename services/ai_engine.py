import os
import json
import logging
import requests
from services.summarizer import Summarizer
from services.task_extractor import TaskExtractor
from services.decision_extractor import DecisionExtractor
from services.risk_detector import RiskDetector
from services.dependency_detector import DependencyDetector

logger = logging.getLogger(__name__)

class AIEngine:
    def __init__(self, gemini_api_key=None, openai_api_key=None):
        self.gemini_api_key = gemini_api_key or os.environ.get('GEMINI_API_KEY', '')
        self.openai_api_key = openai_api_key or os.environ.get('OPENAI_API_KEY', '')
        self.mode = "LLM (Gemini)" if self.gemini_api_key else ("LLM (OpenAI)" if self.openai_api_key else "Local Deterministic NLP Engine")

    def analyze_document_content(self, pages, project=None):
        """
        Main entry point for document analysis.
        Runs NLP extraction across pages and generates structured knowledge:
        - Summary
        - Decisions
        - Tasks
        - Responsibilities
        - Deadlines
        - Risks
        - Dependencies
        - Missing Information
        """
        full_text = "\n\n".join([p.get('text', '') for p in pages if p.get('text')])
        if not full_text.strip():
            raise ValueError("No text content could be extracted from the document for analysis.")

        project_name = project.name if project else None
        project_members = []
        if project:
            if project.outgoing_member:
                project_members.append(project.outgoing_member)
            if project.incoming_member:
                project_members.append(project.incoming_member)

        # If LLM key is configured, attempt LLM-enhanced extraction with fallback to local NLP
        if self.gemini_api_key:
            try:
                llm_result = self._call_gemini_api(full_text, project_name, project_members)
                if llm_result:
                    llm_result['engine_mode'] = 'Gemini LLM Provider (Cloud Enhanced)'
                    return llm_result
            except Exception as e:
                logger.warning(f"Gemini API call failed, falling back to Local NLP engine: {e}")

        # Run Local High-Precision NLP extraction
        return self._run_local_nlp(pages, full_text, project_name, project_members)

    def _run_local_nlp(self, pages, full_text, project_name, project_members):
        summary_data = Summarizer.generate_summary(full_text, project_name)
        tasks = TaskExtractor.extract_tasks(pages, project_members)
        decisions = DecisionExtractor.extract_decisions(pages)
        risks = RiskDetector.detect_risks(pages, tasks)
        dependencies = DependencyDetector.detect_dependencies(pages, tasks)

        # Responsibilities mapping
        responsibilities = {}
        for t in tasks:
            owner = t.get('responsible_person', 'Unassigned')
            if owner not in responsibilities:
                responsibilities[owner] = []
            responsibilities[owner].append(t.get('description'))

        # Deadlines list
        deadlines = []
        for t in tasks:
            if t.get('deadline') and t.get('deadline') not in ('Not specified', 'Pending scheduling'):
                deadlines.append({
                    'item': t.get('description'),
                    'deadline': t.get('deadline'),
                    'responsible': t.get('responsible_person'),
                    'status': t.get('status')
                })

        # Missing information detection
        missing_info = []
        if not decisions:
            missing_info.append("No explicit architectural or strategic decisions recorded in this document.")
        unassigned_count = len([t for t in tasks if t.get('responsible_person') == 'Unassigned'])
        if unassigned_count > 0:
            missing_info.append(f"{unassigned_count} identified tasks lack an assigned team member.")
        no_deadline_count = len([t for t in tasks if t.get('deadline') in ('Not specified', 'Pending scheduling', None)])
        if no_deadline_count > 0:
            missing_info.append(f"{no_deadline_count} tasks do not have target completion dates.")
        if not risks:
            missing_info.append("No explicit operational risks or security procedures identified.")

        return {
            'engine_mode': 'Local Deterministic NLP Engine (No External API Required)',
            'executive_summary': summary_data.get('executive_summary'),
            'key_highlights': summary_data.get('key_highlights'),
            'handover_readiness': summary_data.get('handover_readiness'),
            'decisions': decisions,
            'tasks': tasks,
            'responsibilities': responsibilities,
            'deadlines': deadlines,
            'risks': risks,
            'dependencies': dependencies,
            'missing_information': missing_info
        }

    def _call_gemini_api(self, text, project_name, project_members):
        """Calls Google Gemini API for structured extraction if key is present."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
        prompt = f"""
You are an expert technical knowledge handover analyst. Analyze this project handover document.
Project Name: {project_name or 'Unknown'}
Known Team Members: {', '.join(project_members) if project_members else 'None specified'}

Document text:
\"\"\"{text[:10000]}\"\"\"

Return ONLY a valid JSON object with the following schema:
{{
  "executive_summary": "Concise 3-sentence summary of the handover context",
  "key_highlights": ["point 1", "point 2", "point 3"],
  "handover_readiness": "High" or "Medium" or "Low",
  "decisions": [
    {{"title": "...", "description": "...", "reason": "...", "decision_date": "...", "status": "Approved", "confidence": 0.95, "evidence_text": "quote from doc", "page_number": 1}}
  ],
  "tasks": [
    {{"description": "...", "responsible_person": "...", "deadline": "...", "status": "Pending", "priority": "High/Medium/Low", "confidence": 0.9, "evidence_text": "quote from doc", "page_number": 1}}
  ],
  "risks": [
    {{"description": "...", "category": "Technical/Security/Timeline/Resource", "severity": "High/Medium/Low", "suggested_action": "...", "evidence_text": "quote", "page_number": 1}}
  ],
  "dependencies": [
    {{"prerequisite": "...", "dependent": "...", "description": "...", "is_blocking": true, "evidence_text": "quote", "page_number": 1}}
  ],
  "missing_information": ["missing item 1", "missing item 2"]
}}
"""
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
        }
        res = requests.post(url, headers=headers, json=payload, timeout=25)
        if res.status_code == 200:
            raw_text = res.json()['candidates'][0]['content']['parts'][0]['text']
            return json.loads(raw_text)
        return None
