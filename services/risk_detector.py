import re

class RiskDetector:
    RISK_TRIGGERS = [
        ('risk', 'Technical'),
        ('vulnerability', 'Security'),
        ('bottleneck', 'Technical'),
        ('single point of failure', 'Technical'),
        ('outage', 'Technical'),
        ('delay', 'Timeline'),
        ('overdue', 'Timeline'),
        ('untested', 'Technical'),
        ('deprecated', 'Technical'),
        ('credential', 'Security'),
        ('password in code', 'Security'),
        ('api key exposed', 'Security'),
        ('unknown owner', 'Resource'),
        ('unassigned', 'Resource'),
        ('missing documentation', 'Documentation'),
        ('undocumented', 'Documentation'),
        ('no backup', 'Security'),
        ('licensing issue', 'Legal')
    ]

    @staticmethod
    def detect_risks(pages, tasks=None):
        """
        Detects explicit project risks from document text, plus implicit structural
        risks like missing task owners or missing deadlines.
        """
        risks = []
        seen = set()

        # 1. Structural risks from tasks
        if tasks:
            unassigned_tasks = [t for t in tasks if t.get('responsible_person') in ('Unassigned', None, '')]
            if unassigned_tasks:
                desc = f"{len(unassigned_tasks)} critical tasks have no designated owner assigned."
                if desc not in seen:
                    seen.add(desc)
                    risks.append({
                        'description': desc,
                        'category': 'Resource',
                        'severity': 'High' if len(unassigned_tasks) > 2 else 'Medium',
                        'suggested_action': 'Assign incoming team members to unowned tasks during the handover meeting.',
                        'page_number': unassigned_tasks[0].get('page_number', 1),
                        'evidence_text': unassigned_tasks[0].get('evidence_text', 'Task list evaluation'),
                        'extraction_ref': 'Structural Task Audit'
                    })

            no_deadline_tasks = [t for t in tasks if t.get('deadline') in ('Not specified', 'Pending scheduling', None, '')]
            if no_deadline_tasks:
                desc = f"{len(no_deadline_tasks)} tasks lack explicit completion deadlines."
                if desc not in seen:
                    seen.add(desc)
                    risks.append({
                        'description': desc,
                        'category': 'Timeline',
                        'severity': 'Medium',
                        'suggested_action': 'Establish milestone dates with incoming team lead to prevent project slip.',
                        'page_number': no_deadline_tasks[0].get('page_number', 1),
                        'evidence_text': no_deadline_tasks[0].get('evidence_text', 'Task schedule review'),
                        'extraction_ref': 'Timeline Audit'
                    })

        # 2. Text-derived explicit risks
        for page in pages:
            page_num = page.get('page_number', 1)
            text = page.get('text', '')
            lines = [l.strip() for l in text.split('\n') if l.strip()]

            for line in lines:
                lower = line.lower()
                for keyword, default_cat in RiskDetector.RISK_TRIGGERS:
                    if keyword in lower:
                        # Clean line
                        cleaned = re.sub(r'^(?:[-*•]|\d+[.)]|\b(?:risk|warning|caution|concern):\s*)\s*', '', line, flags=re.I).strip()
                        if len(cleaned) < 15 or cleaned.lower() in seen:
                            continue

                        # Determine severity
                        severity = 'Medium'
                        if any(w in lower for w in ['critical', 'high risk', 'blocker', 'severe', 'immediate attention', 'data loss', 'security breach']):
                            severity = 'High'
                        elif any(w in lower for w in ['minor', 'low risk', 'cosmetic', 'low impact']):
                            severity = 'Low'

                        # Suggested action
                        action = "Conduct an immediate review and verify mitigation protocol with the outgoing engineer."
                        if default_cat == 'Security':
                            action = "Rotate secrets, verify access credentials, and audit permission policies."
                        elif default_cat == 'Timeline':
                            action = "Adjust sprint milestones and reallocate technical resources to address the delay."
                        elif default_cat == 'Documentation':
                            action = "Schedule knowledge transfer session to document undocumented architecture."

                        seen.add(cleaned.lower())
                        risks.append({
                            'description': cleaned,
                            'category': default_cat,
                            'severity': severity,
                            'suggested_action': action,
                            'page_number': page_num,
                            'evidence_text': line,
                            'extraction_ref': f"Document Page {page_num}"
                        })
                        break

        return risks
