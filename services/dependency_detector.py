import re

class DependencyDetector:
    DEPENDENCY_PATTERNS = [
        r'([^.\n]+?)\s+(?:must be completed before|is required before|prerequisite for|blocks|is blocked by|depends on|after completing)\s+([^.\n]+)',
        r'(?:before|prior to)\s+([^,.\n]+?),\s*(?:must|ensure|we need to)\s+([^.\n]+)'
    ]

    @staticmethod
    def detect_dependencies(pages, extracted_tasks=None):
        """
        Detects dependencies between tasks and activities.
        Matches detected dependencies to task IDs if extracted_tasks are provided.
        """
        dependencies = []
        seen = set()

        for page in pages:
            text = page.get('text', '')
            for dp in DependencyDetector.DEPENDENCY_PATTERNS:
                matches = re.finditer(dp, text, re.I)
                for m in matches:
                    part_a = m.group(1).strip()
                    part_b = m.group(2).strip()

                    # Decide prerequisite vs dependent based on pattern wording
                    full_match = m.group(0).lower()
                    if 'is blocked by' in full_match or 'depends on' in full_match:
                        dependent = part_a
                        prereq = part_b
                    elif 'before' in full_match or 'prerequisite' in full_match or 'blocks' in full_match:
                        prereq = part_a
                        dependent = part_b
                    else:
                        prereq = part_a
                        dependent = part_b

                    # Clean prefix punctuation
                    prereq = re.sub(r'^(?:[-*•]|\d+[.)]|\s)+', '', prereq).strip()
                    dependent = re.sub(r'^(?:[-*•]|\d+[.)]|\s)+', '', dependent).strip()

                    key = f"{prereq.lower()} -> {dependent.lower()}"
                    if len(prereq) > 6 and len(dependent) > 6 and key not in seen:
                        seen.add(key)
                        dependencies.append({
                            'prerequisite': prereq,
                            'dependent': dependent,
                            'description': f"'{prereq}' is required before proceeding with '{dependent}'.",
                            'is_blocking': True,
                            'evidence_text': m.group(0),
                            'page_number': page.get('page_number', 1)
                        })

        # Match to task list if provided
        return dependencies
