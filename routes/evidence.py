from flask import Blueprint, jsonify
from models.models import Evidence, Task, Decision, Risk, Document
from routes.auth_helpers import login_required, get_current_user

evidence_bp = Blueprint('evidence', __name__, url_prefix='/api/evidence')

@evidence_bp.route('/<int:evidence_id>', methods=['GET'])
@login_required
def get_evidence(evidence_id):
    ev = Evidence.query.get(evidence_id)
    if not ev:
        return jsonify({'error': 'Evidence not found.', 'available': False}), 404

    result = ev.to_dict()
    result['available'] = True

    # Link related entity details
    if ev.entity_type == 'task':
        task = Task.query.get(ev.entity_id)
        result['entity_description'] = task.description if task else 'Unknown Task'
    elif ev.entity_type == 'decision':
        dec = Decision.query.get(ev.entity_id)
        result['entity_description'] = dec.title if dec else 'Unknown Decision'
    elif ev.entity_type == 'risk':
        r = Risk.query.get(ev.entity_id)
        result['entity_description'] = r.description if r else 'Unknown Risk'

    return jsonify({'available': True, 'evidence': result}), 200

@evidence_bp.route('/entity/<string:entity_type>/<int:entity_id>', methods=['GET'])
@login_required
def get_evidence_by_entity(entity_type, entity_id):
    ev = Evidence.query.filter_by(entity_type=entity_type.lower(), entity_id=entity_id).first()
    if not ev:
        return jsonify({
            'available': False,
            'message': 'Evidence unavailable for this item.'
        }), 200

    result = ev.to_dict()
    result['available'] = True

    if entity_type == 'task':
        task = Task.query.get(entity_id)
        result['entity_description'] = task.description if task else 'Task'
    elif entity_type == 'decision':
        dec = Decision.query.get(entity_id)
        result['entity_description'] = dec.title if dec else 'Decision'
    elif entity_type == 'risk':
        risk = Risk.query.get(entity_id)
        result['entity_description'] = risk.description if risk else 'Risk'

    return jsonify({'available': True, 'evidence': result}), 200
