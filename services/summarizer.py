import re

class Summarizer:
    @staticmethod
    def generate_summary(text_content, project_name=None):
        """
        Generates an executive summary, key highlights, and readiness indicators
        from project document text.
        """
        if not text_content or not text_content.strip():
            return {
                'executive_summary': 'No document content available for summarisation.',
                'key_highlights': [],
                'handover_readiness': 'Low - Insufficient documentation'
            }

        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        sentences = []
        for line in lines:
            # Split into sentences
            splits = re.split(r'(?<=[.!?])\s+', line)
            for s in splits:
                s = s.strip()
                if len(s) > 20:
                    sentences.append(s)

        # Look for overview or objective statements
        highlight_keywords = [
            'overview', 'objective', 'architecture', 'implemented', 'deployed',
            'transition', 'handover', 'completed', 'scope', 'purpose', 'critical'
        ]
        
        selected_highlights = []
        for s in sentences:
            s_lower = s.lower()
            if any(k in s_lower for k in highlight_keywords):
                if len(s) < 180 and s not in selected_highlights:
                    selected_highlights.append(s)
            if len(selected_highlights) >= 5:
                break

        if not selected_highlights and sentences:
            selected_highlights = sentences[:3]

        # Generate readable executive summary
        proj_ref = f"for {project_name}" if project_name else ""
        intro = f"This handover documentation {proj_ref} captures critical architectural decisions, pending deliverables, and operational requirements."
        
        main_points = " ".join(sentences[:4]) if len(sentences) >= 4 else " ".join(sentences)
        exec_summary = f"{intro} {main_points}"
        if len(exec_summary) > 600:
            exec_summary = exec_summary[:597] + "..."

        # Calculate readiness based on content quality and coverage
        readiness = 'High - Comprehensive documentation available'
        if len(sentences) < 10:
            readiness = 'Medium - Preliminary handover notes'
        if len(sentences) < 4:
            readiness = 'Low - Incomplete project documentation'

        return {
            'executive_summary': exec_summary,
            'key_highlights': selected_highlights,
            'handover_readiness': readiness
        }
