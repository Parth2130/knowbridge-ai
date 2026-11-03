import re
from datetime import datetime

class TaskExtractor:
    # Pattern triggers for action items and tasks
    TASK_PATTERNS = [
        r'(?:todo|task|action item|must|should|needs to|pending|deliverable|deliver|implement|fix|deploy|migrate|review|prepare|integrate|configure|refactor)\b[:\s\-]+([^.\n;]+)',
        r'(?:assigned to|owner|responsible)[:\s]+([A-Za-z\s]+?)[,.\-\n]',
        r'(?:deadline|due date|by|target date)[:\s]+([A-Za-z0-9\s,\-]+?)(?=[.\n;]|$)'
    ]

    DATE_PATTERNS = [
        r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{1,2}(?:st|nd|rd|th)?,? \d{4}\b',
        r'\b\d{4}-\d{2}-\d{2}\b',
        r'\b\d{1,2}/\d{1,2}/\d{4}\b',
        r'\b(?:end of (?:q[1-4]|month|week|sprint|year))\b',
        r'\bby (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
        r'\bnext (?:week|sprint|month)\b'
    ]

    @staticmethod
    def extract_tasks(pages, project_members=None):
        """
        Scans pages or text chunks, identifies tasks, owners, deadlines, priority,
        and links evidence with page numbers and exact quotes.
        """
        extracted_tasks = []
        seen_descriptions = set()

        for page in pages:
            page_num = page.get('page_number', 1)
            text = page.get('text', '')
            lines = [l.strip() for l in text.split('\n') if l.strip()]

            for line in lines:
                lower_line = line.lower()
                
                # Check for bullet points or numbering or keywords
                is_task_line = (
                    re.match(r'^(?:[-*•]|\d+[.)])\s+', line) and
                    any(w in lower_line for w in ['todo', 'task', 'implement', 'fix', 'deploy', 'review', 'integrate', 'update', 'migrate', 'complete', 'test', 'ensure', 'verify', 'setup', 'add', 'create', 'refactor', 'resolve'])
                ) or any(prefix in lower_line for prefix in ['action item:', 'todo:', 'task:', 'pending task:', 'needs to', 'responsible for', 'must complete'])

                if is_task_line:
                    # Clean description
                    cleaned_desc = re.sub(r'^(?:[-*•]|\d+[.)]|\b(?:todo|task|action item):\s*)\s*', '', line, flags=re.I).strip()
                    if len(cleaned_desc) < 8 or cleaned_desc.lower() in seen_descriptions:
                        continue

                    # Extract owner
                    owner = 'Unassigned'
                    owner_match = re.search(r'\b(?:assigned to|owner|lead|poc|assigned|responsible)[:\s]+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)', line, re.I)
                    if owner_match:
                        owner = owner_match.group(1).strip()
                    elif project_members:
                        for m in project_members:
                            if m and m.lower() in lower_line:
                                owner = m
                                break

                    # Extract deadline
                    deadline = None
                    for dp in TaskExtractor.DATE_PATTERNS:
                        date_match = re.search(dp, line, re.I)
                        if date_match:
                            deadline = date_match.group(0).strip()
                            break

                    # Determine status
                    status = 'Pending'
                    if any(w in lower_line for w in ['done', 'completed', 'resolved', 'verified']):
                        status = 'Completed'
                    elif any(w in lower_line for w in ['in progress', 'ongoing', 'underway', 'wip']):
                        status = 'In Progress'
                    elif any(w in lower_line for w in ['blocked', 'blocking', 'on hold', 'delayed']):
                        status = 'Blocked'

                    # Determine priority
                    priority = 'Medium'
                    if any(w in lower_line for w in ['urgent', 'critical', 'high priority', 'immediately', 'blocker', 'asap']):
                        priority = 'High'
                    elif any(w in lower_line for w in ['low priority', 'minor', 'nice to have', 'optional']):
                        priority = 'Low'

                    seen_descriptions.add(cleaned_desc.lower())
                    extracted_tasks.append({
                        'description': cleaned_desc,
                        'responsible_person': owner,
                        'deadline': deadline or 'Not specified',
                        'status': status,
                        'priority': priority,
                        'confidence': 0.88 if owner != 'Unassigned' and deadline else 0.82,
                        'page_number': page_num,
                        'evidence_text': line,
                        'extraction_ref': f"Document Page {page_num}"
                    })

        # Fallback heuristic: If no formatted bullet tasks were found, scan sentences
        if not extracted_tasks:
            for page in pages:
                page_num = page.get('page_number', 1)
                text = page.get('text', '')
                sentences = re.split(r'(?<=[.!?])\s+', text)
                for s in sentences:
                    s_clean = s.strip()
                    s_lower = s_clean.lower()
                    if any(v in s_lower for v in ['must be completed', 'will be handled by', 'is scheduled to', 'remains to be done', 'needs to be deployed']):
                        if s_clean.lower() not in seen_descriptions and len(s_clean) > 15:
                            seen_descriptions.add(s_clean.lower())
                            extracted_tasks.append({
                                'description': s_clean,
                                'responsible_person': 'Unassigned',
                                'deadline': 'Pending scheduling',
                                'status': 'Pending',
                                'priority': 'Medium',
                                'confidence': 0.78,
                                'page_number': page_num,
                                'evidence_text': s_clean,
                                'extraction_ref': f"Document Page {page_num}"
                            })

        return extracted_tasks
