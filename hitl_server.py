"""
HITL Dashboard API Server
==========================
Flask-based backend serving the tactical HITL dashboard.
Provides REST API for the frontend to interact with the HITL Decision Engine.
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from hitl_engine import HITLDecisionEngine
import os

app = Flask(__name__, static_folder='dashboard', static_url_path='')
CORS(app)

# Global engine instance
engine = HITLDecisionEngine()
engine.operator_on_duty = "CPT. TRIPATHI"

# Pre-populate with initial detections and suggestions
initial_detections = engine.system_detect_targets()
engine.system_suggest_actions(initial_detections)
engine.auto_approve_safe_actions()


@app.route('/')
def serve_dashboard():
    return send_from_directory('dashboard', 'index.html')


@app.route('/api/state', methods=['GET'])
def get_state():
    """Return full system state for dashboard rendering."""
    return jsonify(engine.get_state_snapshot())


@app.route('/api/scan', methods=['POST'])
def new_scan():
    """Trigger a new AI detection scan."""
    global engine
    # Clear old pending that were already decided
    engine.pending_queue = [a for a in engine.pending_queue if a.approval_status == "PENDING"]
    detections = engine.system_detect_targets()
    suggestions = engine.system_suggest_actions(detections)
    engine.auto_approve_safe_actions()
    return jsonify({
        "status": "ok",
        "detections": len(detections),
        "suggestions": len(suggestions),
    })


@app.route('/api/approve/<action_id>', methods=['POST'])
def approve_action(action_id):
    data = request.json or {}
    success = engine.human_approve(
        action_id,
        operator=data.get("operator", engine.operator_on_duty),
        notes=data.get("notes", "")
    )
    if success:
        # Process this approved command immediately
        records = engine.process_approved_commands()
        return jsonify({"status": "approved", "commands_executed": len(records)})
    return jsonify({"status": "error", "message": "Action not found"}), 404


@app.route('/api/deny/<action_id>', methods=['POST'])
def deny_action(action_id):
    data = request.json or {}
    success = engine.human_deny(
        action_id,
        operator=data.get("operator", engine.operator_on_duty),
        notes=data.get("notes", "")
    )
    if success:
        return jsonify({"status": "denied"})
    return jsonify({"status": "error", "message": "Action not found"}), 404


@app.route('/api/override/<action_id>', methods=['POST'])
def override_action(action_id):
    data = request.json or {}
    new_type = data.get("new_action_type", "TRACK")
    result = engine.human_override(
        action_id,
        new_action_type=new_type,
        operator=data.get("operator", engine.operator_on_duty),
        notes=data.get("notes", "Override by operator")
    )
    if result:
        records = engine.process_approved_commands()
        return jsonify({"status": "overridden", "new_action": result.to_dict(), "commands_executed": len(records)})
    return jsonify({"status": "error", "message": "Action not found"}), 404


@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify([r.to_dict() for r in engine.command_history])


@app.route('/api/mode', methods=['POST'])
def set_mode():
    """Switch operational mode: MANUAL, ASSISTED, AUTONOMOUS."""
    data = request.json or {}
    mode = data.get("mode", "ASSISTED")
    reason = data.get("reason", "")
    result = engine.set_mode(mode, reason)
    return jsonify(result)


@app.route('/api/signal_loss', methods=['POST'])
def signal_loss():
    """Simulate signal loss — auto-switch to AUTONOMOUS mode."""
    result = engine.trigger_signal_loss()
    return jsonify(result)


@app.route('/api/signal_restore', methods=['POST'])
def signal_restore():
    """Restore signal — switch back to ASSISTED mode."""
    result = engine.restore_signal()
    return jsonify(result)


@app.route('/api/manual_command', methods=['POST'])
def manual_command():
    """
    🟢 MANUAL MODE: Human issues a direct command (no AI suggestion).
    The command is encrypted and sent directly.
    """
    data = request.json or {}
    action_type = data.get("action_type", "NAVIGATE")
    description = data.get("description", "Manual operator command")

    from hitl_engine import SuggestedAction, ApprovalStatus
    from datetime import datetime

    manual_action = SuggestedAction(
        action_type=action_type,
        description=f"[MANUAL] {description}",
        rationale="Direct operator command — Manual mode",
        urgency="HIGH",
        requires_human_approval=False,
        risk_assessment="OPERATOR ASSESSED — Manual control",
        confidence_score=1.0,
        approval_status=ApprovalStatus.APPROVED.value,
        approved_by=engine.operator_on_duty,
        approval_timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ai_recommendation=f"🟢 MANUAL MODE: Command issued directly by {engine.operator_on_duty}",
    )
    engine.pending_queue.append(manual_action)
    records = engine.process_approved_commands()
    return jsonify({"status": "executed", "commands_executed": len(records)})


@app.route('/api/reset', methods=['POST'])
def reset_system():
    """Reset the HITL engine to fresh state."""
    global engine
    engine = HITLDecisionEngine()
    engine.operator_on_duty = "CPT. TRIPATHI"
    detections = engine.system_detect_targets()
    engine.system_suggest_actions(detections)
    engine.auto_approve_safe_actions()
    return jsonify({"status": "reset"})


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  HITL TACTICAL DASHBOARD SERVER")
    print("  http://0.0.0.0:5000 (Available on all network interfaces)")
    print("=" * 60 + "\n")
    app.run(host='0.0.0.0', debug=True, port=5000)
