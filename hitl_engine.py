"""
Human-in-the-Loop (HITL) Command Authorization Engine
======================================================

Architecture:
    AI → Suggests Action
            ↓
    Human → Verifies & Approves
            ↓
    System → Encrypts + Sends Command
            ↓
    Drone → Executes

System Responsibilities:
    [OK] Detect objects (enemy, vehicle, weapon)
    [OK] Suggest actions
    [OK] Navigate autonomously
    [OK] Detect threats

Human Responsibilities:
    👨‍✈️ Approve commands
    👨‍✈️ Override system
    👨‍✈️ Final decision (especially critical actions)

3 Operational Modes:
    🟢 MANUAL     — Human controls everything
    🟡 ASSISTED   — System suggests, Human approves (BEST / DEFAULT)
    🔴 AUTONOMOUS — Used only if: Signal lost, Emergency
"""

import time
import json
import uuid
import random
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


# ============================================================
#  ENUMERATIONS
# ============================================================

class ThreatLevel(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class ActionType(Enum):
    ENGAGE = "ENGAGE"            # Lethal action (ALWAYS requires human approval)
    TRACK = "TRACK"              # Follow target
    EVADE = "EVADE"              # Defensive maneuver
    RECON = "RECON"              # Reconnaissance scan
    NAVIGATE = "NAVIGATE"        # Waypoint navigation
    RTB = "RTB"                  # Return to base
    LAND = "LAND"                # Emergency land
    ALERT = "ALERT"              # Send alert to command
    CLASSIFY = "CLASSIFY"        # Re-classify target
    COUNTERMEASURE = "COUNTERMEASURE"  # Deploy countermeasure


class OperationalMode(Enum):
    MANUAL = "MANUAL"           # 🟢 Human controls everything
    ASSISTED = "ASSISTED"       # 🟡 AI suggests, Human approves (DEFAULT)
    AUTONOMOUS = "AUTONOMOUS"   # 🔴 Only on signal loss / emergency


class ApprovalStatus(Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    OVERRIDDEN = "OVERRIDDEN"
    AUTO_APPROVED = "AUTO_APPROVED"   # Low-risk actions auto-approved
    AUTO_EXECUTED = "AUTO_EXECUTED"   # 🔴 Autonomous mode — no human
    EXPIRED = "EXPIRED"


class DetectionClass(Enum):
    COMBATANT = "COMBATANT"
    WEAPON_SYSTEM = "WEAPON_SYSTEM"
    VEHICLE_ARMOR = "VEHICLE_ARMOR"
    VEHICLE_LIGHT = "VEHICLE_LIGHT"
    STRUCTURE = "STRUCTURE"
    CIVILIAN = "CIVILIAN"
    UNKNOWN = "UNKNOWN"


# ============================================================
#  DATA MODELS
# ============================================================

@dataclass
class Detection:
    """Represents a single detection from the sensor system."""
    detection_id: str = field(default_factory=lambda: f"DET-{uuid.uuid4().hex[:6].upper()}")
    target_class: str = "UNKNOWN"
    confidence: float = 0.0
    threat_level: str = "NONE"
    range_m: int = 0
    bearing_deg: int = 0
    temperature: str = "N/A"
    gps_lat: float = 0.0
    gps_lon: float = 0.0
    velocity_kmh: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self):
        return asdict(self)


@dataclass
class SuggestedAction:
    """Generated action suggestion requiring human approval."""
    action_id: str = field(default_factory=lambda: f"ACT-{uuid.uuid4().hex[:6].upper()}")
    action_type: str = "RECON"
    target_detection_id: str = ""
    description: str = ""
    rationale: str = ""
    urgency: str = "MEDIUM"       # CRITICAL, HIGH, MEDIUM, LOW
    requires_human_approval: bool = True
    risk_assessment: str = ""
    estimated_collateral: str = "NONE"
    confidence_score: float = 0.0
    approval_status: str = "PENDING"
    approved_by: str = ""
    approval_timestamp: str = ""
    system_recommendation: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self):
        return asdict(self)


@dataclass
class CommandRecord:
    """Full audit trail of a command from suggestion to execution."""
    command_id: str = field(default_factory=lambda: f"CMD-{uuid.uuid4().hex[:8].upper()}")
    action: SuggestedAction = None
    detections: List[Detection] = field(default_factory=list)
    human_decision: str = "PENDING"
    human_notes: str = ""
    encrypted: bool = False
    transmitted: bool = False
    executed: bool = False
    execution_result: str = ""
    pipeline_log: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self):
        d = asdict(self)
        return d


# ============================================================
#  HITL DECISION ENGINE
# ============================================================

class HITLDecisionEngine:
    """
    Core decision engine implementing the Human-in-the-Loop paradigm.

    3 Operational Modes:
        🟢 MANUAL     — Human controls everything (no AI suggestions)
        🟡 ASSISTED   — AI suggests, Human approves (DEFAULT / BEST)
        🔴 AUTONOMOUS — AI decides autonomously (signal loss / emergency ONLY)

    Pipeline:
        1. System detects threats and generates suggestions
        2. Suggestions are queued for human review (Assisted) or auto-executed (Autonomous)
        3. Human operator approves, denies, or overrides (Assisted/Manual)
        4. Approved commands are encrypted and transmitted
        5. Full audit trail maintained
    """

    # Actions that ALWAYS require human approval in ASSISTED mode (lethal/critical)
    CRITICAL_ACTIONS = {
        ActionType.ENGAGE.value,
        ActionType.COUNTERMEASURE.value,
    }

    # Actions that can be auto-approved in ASSISTED mode if urgency is LOW
    AUTO_APPROVE_ACTIONS = {
        ActionType.RECON.value,
        ActionType.CLASSIFY.value,
        ActionType.ALERT.value,
    }

    # Risk matrix: (threat_level, action_type) → risk score (0-100)
    RISK_MATRIX = {
        ("CRITICAL", "ENGAGE"): 95,
        ("CRITICAL", "TRACK"): 60,
        ("CRITICAL", "EVADE"): 40,
        ("HIGH", "ENGAGE"): 85,
        ("HIGH", "TRACK"): 45,
        ("HIGH", "EVADE"): 30,
        ("MEDIUM", "ENGAGE"): 70,
        ("MEDIUM", "TRACK"): 25,
        ("LOW", "RECON"): 10,
        ("LOW", "CLASSIFY"): 5,
        ("NONE", "NAVIGATE"): 5,
    }

    # Autonomous mode: allowed auto-execute actions (non-lethal only, for safety)
    # Even in AUTONOMOUS mode, ENGAGE is restricted to EVADE/RTB for safety
    AUTONOMOUS_SAFE_ACTIONS = {
        ActionType.TRACK.value,
        ActionType.EVADE.value,
        ActionType.RECON.value,
        ActionType.RTB.value,
        ActionType.LAND.value,
        ActionType.ALERT.value,
        ActionType.CLASSIFY.value,
        ActionType.NAVIGATE.value,
    }

    def __init__(self):
        self.pending_queue: List[SuggestedAction] = []
        self.command_history: List[CommandRecord] = []
        self.active_detections: List[Detection] = []
        self.operator_on_duty: str = "OPERATOR-ALPHA"
        self.session_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._action_counter = 0
        self.mode: str = OperationalMode.ASSISTED.value  # 🟡 Default mode
        self.mode_reason: str = "Normal operations — Operator on station"
        self.signal_status: str = "CONNECTED"  # CONNECTED, DEGRADED, LOST
        # ── Packet Stats ──
        self.packets_transmitted: int = 0
        self.packets_received: int = 0

    # ── AI LAYER: Detection & Suggestion ─────────────────────────

    def system_detect_targets(self) -> List[Detection]:
        """
        Simulate processing detection from sensor feed.
        In production, this would interface with the OnboardSensors module.
        Returns a list of detections.
        """
        detection_scenarios = [
            {
                "target_class": "COMBATANT",
                "confidence": round(random.uniform(0.82, 0.97), 2),
                "threat_level": "HIGH",
                "range_m": random.randint(200, 500),
                "bearing_deg": random.randint(0, 359),
                "temperature": "36.8C",
                "velocity_kmh": round(random.uniform(0, 8), 1),
            },
            {
                "target_class": "VEHICLE_ARMOR",
                "confidence": round(random.uniform(0.88, 0.99), 2),
                "threat_level": "HIGH",
                "range_m": random.randint(300, 800),
                "bearing_deg": random.randint(0, 359),
                "temperature": "91.3C",
                "velocity_kmh": round(random.uniform(0, 45), 1),
            },
            {
                "target_class": "WEAPON_SYSTEM",
                "confidence": round(random.uniform(0.79, 0.95), 2),
                "threat_level": "CRITICAL",
                "range_m": random.randint(150, 400),
                "bearing_deg": random.randint(0, 359),
                "temperature": "42.1C",
                "velocity_kmh": 0.0,
            },
            {
                "target_class": "CIVILIAN",
                "confidence": round(random.uniform(0.71, 0.88), 2),
                "threat_level": "NONE",
                "range_m": random.randint(100, 300),
                "bearing_deg": random.randint(0, 359),
                "temperature": "37.0C",
                "velocity_kmh": round(random.uniform(0, 5), 1),
            },
        ]

        # Randomly select 2-4 detections
        num_detections = random.randint(2, 4)
        selected = random.sample(detection_scenarios, min(num_detections, len(detection_scenarios)))

        detections = []
        for s in selected:
            det = Detection(
                target_class=s["target_class"],
                confidence=s["confidence"],
                threat_level=s["threat_level"],
                range_m=s["range_m"],
                bearing_deg=s["bearing_deg"],
                temperature=s["temperature"],
                gps_lat=round(28.5 + random.uniform(0, 0.1), 5),
                gps_lon=round(77.2 + random.uniform(0, 0.1), 5),
                velocity_kmh=s["velocity_kmh"],
            )
            detections.append(det)

        self.active_detections = detections
        return detections

    def system_suggest_actions(self, detections: List[Detection]) -> List[SuggestedAction]:
        """
        System analyzes detections and suggests appropriate actions.
        Behavior depends on current operational mode:
            🟢 MANUAL     — No suggestions generated (human issues commands directly)
            🟡 ASSISTED   — System generates suggestions, critical ones require human approval
            🔴 AUTONOMOUS — System generates and auto-executes safe actions
        """
        suggestions = []

        # 🟢 MANUAL: AI does NOT suggest — human drives everything
        if self.mode == OperationalMode.MANUAL.value:
            return suggestions

        for det in detections:
            action = self._generate_suggestion(det)
            if action:
                # 🔴 AUTONOMOUS: Auto-execute safe actions, downgrade lethal to EVADE/RTB
                if self.mode == OperationalMode.AUTONOMOUS.value:
                    action = self._apply_autonomous_policy(action)

                suggestions.append(action)
                self.pending_queue.append(action)

        return suggestions

    def _apply_autonomous_policy(self, action: SuggestedAction) -> SuggestedAction:
        """
        In AUTONOMOUS mode (signal lost / emergency):
        - Safe actions (TRACK, EVADE, RECON, RTB) → auto-execute immediately
        - Lethal actions (ENGAGE, COUNTERMEASURE) → downgraded to EVADE + RTB
        - No lethal action is EVER executed without a human
        """
        if action.action_type in self.AUTONOMOUS_SAFE_ACTIONS:
            # Auto-execute safe actions
            action.requires_human_approval = False
            action.approval_status = ApprovalStatus.AUTO_EXECUTED.value
            action.approved_by = "AUTONOMOUS_SYSTEM"
            action.approval_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            action.system_recommendation = (
                f"🔴 AUTONOMOUS MODE: {action.action_type} auto-executed. "
                f"Reason: {self.mode_reason}"
            )
        else:
            # Lethal actions → downgrade to EVADE for safety
            original = action.action_type
            action.action_type = ActionType.EVADE.value
            action.requires_human_approval = False
            action.approval_status = ApprovalStatus.AUTO_EXECUTED.value
            action.approved_by = "AUTONOMOUS_SYSTEM"
            action.approval_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            action.description = (
                f"[AUTO-DOWNGRADED] {original} → EVADE. "
                f"Lethal action prohibited without human authorization."
            )
            action.system_recommendation = (
                f"🔴 AUTONOMOUS SAFETY: {original} downgraded to EVADE. "
                f"Lethal actions require human operator. Returning to base."
            )
            action.risk_assessment = f"DOWNGRADED — Original {original} too risky for autonomous execution"
        return action

    def _generate_suggestion(self, detection: Detection) -> Optional[SuggestedAction]:
        """Generate an action suggestion based on detection classification."""
        self._action_counter += 1

        if detection.target_class == "COMBATANT":
            if detection.threat_level == "CRITICAL" or detection.range_m < 250:
                return SuggestedAction(
                    action_type=ActionType.ENGAGE.value,
                    target_detection_id=detection.detection_id,
                    description=f"Engage hostile combatant at {detection.range_m}m, bearing {detection.bearing_deg}°",
                    rationale=f"Armed hostile detected at close range with {detection.confidence:.0%} confidence. "
                              f"Target shows aggressive posture. Thermal sig: {detection.temperature}.",
                    urgency="HIGH",
                    requires_human_approval=True,  # ALWAYS for ENGAGE
                    risk_assessment="HIGH — Lethal action requires positive target identification",
                    estimated_collateral="LOW — Open terrain, no civilian signatures nearby",
                    confidence_score=detection.confidence,
                    system_recommendation="RECOMMEND ENGAGE — Target confirmed hostile. Approval required.",
                )
            else:
                return SuggestedAction(
                    action_type=ActionType.TRACK.value,
                    target_detection_id=detection.detection_id,
                    description=f"Track combatant at {detection.range_m}m bearing {detection.bearing_deg}°",
                    rationale=f"Combatant detected at medium range. Maintaining surveillance. "
                              f"Conf: {detection.confidence:.0%}",
                    urgency="MEDIUM",
                    requires_human_approval=True,
                    risk_assessment="MEDIUM — Non-lethal but may compromise drone position",
                    estimated_collateral="NONE",
                    confidence_score=detection.confidence,
                    system_recommendation="RECOMMEND TRACK — Monitor target movement pattern.",
                )

        elif detection.target_class == "WEAPON_SYSTEM":
            return SuggestedAction(
                action_type=ActionType.COUNTERMEASURE.value,
                target_detection_id=detection.detection_id,
                description=f"Deploy countermeasure against weapon system at {detection.range_m}m",
                rationale=f"Active weapon system detected (Metallic IR signature). "
                          f"Thermal: {detection.temperature}. Potential threat to drone.",
                urgency="CRITICAL",
                requires_human_approval=True,  # ALWAYS for COUNTERMEASURE
                risk_assessment="CRITICAL — Weapon system may target drone or friendly forces",
                estimated_collateral="MEDIUM — Blast radius assessment pending",
                confidence_score=detection.confidence,
                system_recommendation="URGENT: RECOMMEND COUNTERMEASURE — Active threat to platform.",
            )

        elif detection.target_class == "VEHICLE_ARMOR":
            return SuggestedAction(
                action_type=ActionType.TRACK.value,
                target_detection_id=detection.detection_id,
                description=f"Track armored vehicle at {detection.range_m}m, speed {detection.velocity_kmh}km/h",
                rationale=f"Armored vehicle moving through sector. Engine thermal: {detection.temperature}. "
                          f"Monitoring trajectory for threat assessment.",
                urgency="HIGH",
                requires_human_approval=True,
                risk_assessment="HIGH — Armored asset may indicate larger force movement",
                estimated_collateral="NONE",
                confidence_score=detection.confidence,
                system_recommendation="RECOMMEND TRACK — Vehicle convoy analysis in progress.",
            )

        elif detection.target_class == "CIVILIAN":
            return SuggestedAction(
                action_type=ActionType.CLASSIFY.value,
                target_detection_id=detection.detection_id,
                description=f"Re-classify potential civilian at {detection.range_m}m",
                rationale=f"Non-combatant signature detected. Confidence: {detection.confidence:.0%}. "
                          f"Marking as civilian. NO offensive action recommended.",
                urgency="LOW",
                requires_human_approval=False,  # Safe to auto-classify
                risk_assessment="LOW — Civilian identification, defensive posture only",
                estimated_collateral="NONE — No action taken",
                confidence_score=detection.confidence,
                system_recommendation="AUTO-CLASSIFY: CIVILIAN — No engagement authorized.",
            )

        elif detection.target_class == "STRUCTURE":
            return SuggestedAction(
                action_type=ActionType.RECON.value,
                target_detection_id=detection.detection_id,
                description=f"Detailed reconnaissance of structure at {detection.range_m}m",
                rationale=f"Structure detected. Assessing for hostile occupation. "
                          f"Thermal scan indicates {detection.temperature}.",
                urgency="LOW",
                requires_human_approval=False,
                risk_assessment="LOW — Passive observation only",
                estimated_collateral="NONE",
                confidence_score=detection.confidence,
                system_recommendation="AUTO-APPROVE: RECON — Passive scan, no risk.",
            )

        return None

    # ── HUMAN LAYER: Approval & Override ──────────────────────────

    def human_approve(self, action_id: str, operator: str = None, notes: str = "") -> bool:
        """Human operator approves a suggested action."""
        action = self._find_pending_action(action_id)
        if not action:
            return False

        action.approval_status = ApprovalStatus.APPROVED.value
        action.approved_by = operator or self.operator_on_duty
        action.approval_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return True

    def human_deny(self, action_id: str, operator: str = None, notes: str = "") -> bool:
        """Human operator denies a suggested action."""
        action = self._find_pending_action(action_id)
        if not action:
            return False

        action.approval_status = ApprovalStatus.DENIED.value
        action.approved_by = operator or self.operator_on_duty

        return True

    def human_override(self, action_id: str, new_action_type: str,
                       operator: str = None, notes: str = "") -> Optional[SuggestedAction]:
        """Human operator overrides the AI suggestion with a different action."""
        action = self._find_pending_action(action_id)
        if not action:
            return None

        action.approval_status = ApprovalStatus.OVERRIDDEN.value
        action.approved_by = operator or self.operator_on_duty
        action.approval_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create new action with human's chosen type
        override_action = SuggestedAction(
            action_type=new_action_type,
            target_detection_id=action.target_detection_id,
            description=f"[HUMAN OVERRIDE] {notes or action.description}",
            rationale=f"Operator override of system suggestion. Original: {action.action_type} → New: {new_action_type}",
            urgency=action.urgency,
            requires_human_approval=False,  # Already approved by override
            risk_assessment=f"OPERATOR ASSESSED — {notes}",
            confidence_score=action.confidence_score,
            approval_status=ApprovalStatus.APPROVED.value,
            approved_by=operator or self.operator_on_duty,
            approval_timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            system_recommendation=f"OVERRIDDEN by {operator or self.operator_on_duty}",
        )

        self.pending_queue.append(override_action)
        return override_action

    def auto_approve_safe_actions(self):
        """Auto-approve low-risk actions that don't require human intervention."""
        for action in self.pending_queue:
            if (action.approval_status == ApprovalStatus.PENDING.value
                    and not action.requires_human_approval
                    and action.action_type in self.AUTO_APPROVE_ACTIONS):
                action.approval_status = ApprovalStatus.AUTO_APPROVED.value
                action.approved_by = "AI_AUTO"
                action.approval_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── MODE SWITCHING ──────────────────────────────────────────

    def set_mode(self, mode: str, reason: str = "") -> Dict[str, str]:
        """
        Switch operational mode.
        🟢 MANUAL     — Human controls everything
        🟡 ASSISTED   — AI suggests, Human approves (default)
        🔴 AUTONOMOUS — Emergency / signal loss ONLY
        """
        old_mode = self.mode
        self.mode = mode

        if mode == OperationalMode.MANUAL.value:
            self.mode_reason = reason or "Operator assumed full manual control"
            self.signal_status = "CONNECTED"
        elif mode == OperationalMode.ASSISTED.value:
            self.mode_reason = reason or "Normal operations — AI assists, Human decides"
            self.signal_status = "CONNECTED"
        elif mode == OperationalMode.AUTONOMOUS.value:
            self.mode_reason = reason or "EMERGENCY: Signal lost or critical threat"
            self.signal_status = "LOST"
            # ── AUTONOMOUS: Clear ALL previous state ──
            self._execute_emergency_fallback()
        else:
            self.mode = old_mode
            return {"status": "error", "message": f"Invalid mode: {mode}"}

        return {
            "status": "ok",
            "old_mode": old_mode,
            "new_mode": self.mode,
            "reason": self.mode_reason,
        }

    def _execute_emergency_fallback(self):
        """
        🔴 AUTONOMOUS EMERGENCY FALLBACK
        Clears all previous state and immediately executes:
        1. EVADE — Defensive maneuver to avoid threats
        2. RTB — Return to base
        This is what happens when signal is lost — drone abandons mission.
        """
        # Wipe all previous state
        self.pending_queue.clear()
        self.active_detections.clear()
        self.command_history.clear()

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ── Step 1: EVADE — immediate evasive action ──
        evade_action = SuggestedAction(
            action_type=ActionType.EVADE.value,
            description="🔴 EMERGENCY EVASIVE MANEUVER — Signal lost, executing defensive protocol",
            rationale="Ground station link severed. Immediate evasive action to avoid hostile detection.",
            urgency="CRITICAL",
            requires_human_approval=False,
            risk_assessment="CRITICAL — No human oversight available",
            estimated_collateral="NONE — Defensive only",
            confidence_score=1.0,
            approval_status=ApprovalStatus.AUTO_EXECUTED.value,
            approved_by="AI_AUTONOMOUS",
            approval_timestamp=ts,
            system_recommendation="🔴 AUTONOMOUS FALLBACK: Evasive maneuver initiated. No human link.",
        )

        # ── Step 2: RTB — return to base ──
        rtb_action = SuggestedAction(
            action_type=ActionType.RTB.value,
            description="🔴 RETURN TO BASE — Autonomous navigation to home coordinates",
            rationale="Signal lost. Mission aborted. Drone navigating autonomously to base coordinates. "
                      "All lethal actions suspended until human link restored.",
            urgency="CRITICAL",
            requires_human_approval=False,
            risk_assessment="CRITICAL — Autonomous navigation, no human oversight",
            estimated_collateral="NONE — Non-offensive return",
            confidence_score=1.0,
            approval_status=ApprovalStatus.AUTO_EXECUTED.value,
            approved_by="AI_AUTONOMOUS",
            approval_timestamp=ts,
            system_recommendation="🔴 AUTONOMOUS FALLBACK: RTB initiated. All weapons safed. Awaiting signal restore.",
        )

        # Process both commands through encryption pipeline
        for action in [evade_action, rtb_action]:
            record = CommandRecord(
                action=action,
                human_decision=ApprovalStatus.AUTO_EXECUTED.value,
            )
            record.pipeline_log.append(f"[{self._timestamp()}] ⚠️ SIGNAL LOST — Autonomous fallback")
            record.pipeline_log.append(f"[{self._timestamp()}] System executing emergency {action.action_type}")
            record.pipeline_log.append(f"[{self._timestamp()}] ML-DSA signing with onboard keys...")
            record.pipeline_log.append(f"[{self._timestamp()}] AES-GCM encryption applied")
            record.pipeline_log.append(f"[{self._timestamp()}] Direct execution — no transmission needed")
            record.pipeline_log.append(f"[{self._timestamp()}] Executing: {action.action_type}")
            record.encrypted = True
            record.transmitted = False  # No transmission — signal is lost
            record.executed = True
            record.execution_result = f"🔴 EMERGENCY {action.action_type} executed — Autonomous mode"
            self.command_history.append(record)

    def trigger_signal_loss(self) -> Dict[str, str]:
        """Simulate signal loss — auto-switch to AUTONOMOUS mode."""
        self.signal_status = "LOST"
        return self.set_mode(
            OperationalMode.AUTONOMOUS.value,
            "CRITICAL: Ground station link lost — autonomous fallback engaged"
        )

    def restore_signal(self) -> Dict[str, str]:
        """Signal restored — switch back to ASSISTED mode with fresh scan."""
        self.signal_status = "CONNECTED"
        result = self.set_mode(
            OperationalMode.ASSISTED.value,
            "Signal restored — returning to assisted operations"
        )
        # Fresh scan after restoring
        detections = self.ai_detect_targets()
        self.ai_suggest_actions(detections)
        self.auto_approve_safe_actions()
        return result

    # ── SYSTEM LAYER: Encrypt & Transmit ──────────────────────────

    def process_approved_commands(self) -> List[CommandRecord]:
        """
        Process all approved actions through the encryption pipeline.
        Returns command records for execution.
        """
        approved_statuses = {
            ApprovalStatus.APPROVED.value,
            ApprovalStatus.AUTO_APPROVED.value,
            ApprovalStatus.AUTO_EXECUTED.value,
        }

        records = []
        for action in self.pending_queue:
            if action.approval_status in approved_statuses:
                record = CommandRecord(
                    action=action,
                    detections=[d for d in self.active_detections
                                if d.detection_id == action.target_detection_id],
                    human_decision=action.approval_status,
                )

                # Simulate encryption pipeline
                record.pipeline_log.append(f"[{self._timestamp()}] Command queued for encryption")
                record.pipeline_log.append(f"[{self._timestamp()}] ML-DSA signing command payload...")
                record.pipeline_log.append(f"[{self._timestamp()}] AES-GCM encryption applied")
                record.encrypted = True

                record.pipeline_log.append(f"[{self._timestamp()}] Transmitting over secure channel...")
                record.transmitted = True
                self.packets_transmitted += 1

                record.pipeline_log.append(f"[{self._timestamp()}] Drone acknowledged receipt")
                self.packets_received += 1
                record.pipeline_log.append(f"[{self._timestamp()}] Executing: {action.action_type}")
                record.executed = True
                record.execution_result = f"Action {action.action_type} executed successfully"

                records.append(record)
                self.command_history.append(record)

        # Clear processed actions from pending queue
        self.pending_queue = [
            a for a in self.pending_queue
            if a.approval_status not in approved_statuses
        ]

        return records

    # ── UTILITIES ──────────────────────────────────────────────────

    def _find_pending_action(self, action_id: str) -> Optional[SuggestedAction]:
        for action in self.pending_queue:
            if action.action_id == action_id:
                return action
        return None

    def _timestamp(self) -> str:
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def get_telemetry_snapshot(self) -> Dict[str, Any]:
        """Generate simulated real-time telemetry for all security modules."""
        import random
        import time
        from datetime import datetime
        
        # ── Heartbeat Calculation ──
        # Calculate background packets based on session duration
        session_dt = datetime.now() - datetime.strptime(self.session_start, "%Y-%m-%d %H:%M:%S")
        seconds_elapsed = session_dt.total_seconds()
        
        # Telemetry pulses: ~5 packets per second (ingress/egress)
        heartbeat_sent = int(seconds_elapsed * 5.2)
        heartbeat_received = int(seconds_elapsed * 5.1) # Small loss simulated
        
        total_sent = self.packets_transmitted + heartbeat_sent
        total_received = self.packets_received + heartbeat_received
        
        # ── QKD Telemetry ──
        qkd_status = "SECURE" if self.signal_status == "CONNECTED" else "DISCONNECTED"
        if self.signal_status == "DEGRADED": qkd_status = "ATTEMPTING_RECOH"
        
        # ── Navigation / Anti-Spoofing Telemetry ──
        base_lat, base_lon = 28.5241, 77.1825
        curr_lat = base_lat + random.uniform(-0.02, 0.02)
        curr_lon = base_lon + random.uniform(-0.02, 0.02)
        
        # ── FHSS / Comms Telemetry ──
        freqs = [902.5, 915.0, 921.2, 928.7, 935.1, 942.3, 949.8]
        current_freq = random.choice(freqs)
        
        return {
            "qkd": {
                "status": qkd_status,
                "pulse_rate_mhz": round(random.uniform(75.0, 82.0), 1) if qkd_status == "SECURE" else 0.0,
                "qber_percent": round(random.uniform(0.5, 2.8), 2) if qkd_status == "SECURE" else 0.0
            },
            "fhss": {
                "current_freq_mhz": current_freq,
                "hop_rate_hz": 200,
                "jamming_detected": self.signal_status == "DEGRADED"
            },
            "packets": {
                "transmitted": total_sent,
                "received": total_received
            },
            "nav": {
                "gps_lat": round(curr_lat, 6),
                "gps_lon": round(curr_lon, 6),
                "gps_alt_m": round(random.uniform(120.0, 150.0), 1)
            }
        }

    def get_state_snapshot(self) -> Dict[str, Any]:
        """Return the full state for the dashboard."""
        return {
            "operator": self.operator_on_duty,
            "session_start": self.session_start,
            "mode": self.mode,
            "mode_reason": self.mode_reason,
            "signal_status": self.signal_status,
            "active_detections": [d.to_dict() for d in self.active_detections],
            "pending_actions": [a.to_dict() for a in self.pending_queue],
            "command_history": [r.to_dict() for r in self.command_history],
            "telemetry": self.get_telemetry_snapshot(),
            "stats": {
                "total_detections": len(self.active_detections),
                "pending_approvals": sum(
                    1 for a in self.pending_queue
                    if a.approval_status == ApprovalStatus.PENDING.value
                ),
                "approved": sum(
                    1 for r in self.command_history
                    if r.human_decision in (
                        ApprovalStatus.APPROVED.value,
                        ApprovalStatus.AUTO_APPROVED.value,
                        ApprovalStatus.AUTO_EXECUTED.value,
                    )
                ),
                "denied": sum(
                    1 for a in self.pending_queue
                    if a.approval_status == ApprovalStatus.DENIED.value
                ),
                "overridden": sum(
                    1 for a in self.pending_queue
                    if a.approval_status == ApprovalStatus.OVERRIDDEN.value
                ),
            }
        }


# ============================================================
#  CONSOLE DEMO (Standalone test)
# ============================================================

def run_hitl_demo():
    """Run a full HITL demo in the console."""
    print("=" * 70)
    print("  HUMAN-IN-THE-LOOP (HITL) COMMAND AUTHORIZATION SYSTEM")
    print("  Post-Quantum Secure Drone Communication")
    print("=" * 70)

    engine = HITLDecisionEngine()
    engine.operator_on_duty = "CPT. TRIPATHI"

    # ── Phase 1: AI Detection ──
    print("\n" + "─" * 60)
    print("  PHASE 1: AI DETECTION (Autonomous)")
    print("─" * 60)
    detections = engine.system_detect_targets()

    print(f"\n[AI Vision] {len(detections)} target(s) detected:")
    for det in detections:
        print(f"  [{det.detection_id}] {det.target_class} | Conf: {det.confidence:.0%} | "
              f"Range: {det.range_m}m | Threat: {det.threat_level}")

    # ── Phase 2: AI Suggestions ──
    print("\n" + "─" * 60)
    print("  PHASE 2: AI ACTION SUGGESTIONS")
    print("─" * 60)
    suggestions = engine.system_suggest_actions(detections)

    for s in suggestions:
        marker = "[!]" if s.requires_human_approval else "[OK]"
        print(f"\n  {marker} [{s.action_id}] {s.action_type}")
        print(f"      Target: {s.target_detection_id}")
        print(f"      {s.description}")
        print(f"      AI Says: {s.system_recommendation}")
        print(f"      Risk: {s.risk_assessment}")
        if s.requires_human_approval:
            print(f"      [!] REQUIRES HUMAN APPROVAL")

    # ── Phase 3: Auto-approve safe actions ──
    engine.auto_approve_safe_actions()

    # ── Phase 4: Human Decisions ──
    print("\n" + "─" * 60)
    print("  PHASE 3: HUMAN OPERATOR DECISIONS")
    print("─" * 60)

    for s in suggestions:
        if s.approval_status == "PENDING":
            print(f"\n  ┌─ PENDING: [{s.action_id}] {s.action_type} → {s.description[:60]}...")
            print(f"  │  AI Recommendation: {s.system_recommendation}")
            response = input(f"  └─ OPERATOR: Approve? (y=approve / n=deny / o=override): ").strip().lower()

            if response == 'y':
                engine.human_approve(s.action_id, notes="Approved by operator")
                print(f"     [OK] APPROVED by {engine.operator_on_duty}")
            elif response == 'o':
                override_type = input(f"     Override to action type (TRACK/EVADE/RTB/RECON): ").strip().upper()
                engine.human_override(s.action_id, override_type, notes="Operator override")
                print(f"     [HOP] OVERRIDDEN to {override_type}")
            else:
                engine.human_deny(s.action_id, notes="Denied by operator")
                print(f"     [X] DENIED by {engine.operator_on_duty}")
        else:
            print(f"\n  [OK] AUTO-APPROVED: [{s.action_id}] {s.action_type} — {s.description[:60]}")

    # ── Phase 5: Encrypt & Execute ──
    print("\n" + "─" * 60)
    print("  PHASE 4: SYSTEM ENCRYPT + TRANSMIT + EXECUTE")
    print("─" * 60)

    records = engine.process_approved_commands()

    for rec in records:
        print(f"\n  Command: {rec.command_id}")
        for log in rec.pipeline_log:
            print(f"    {log}")
        print(f"  Result: {rec.execution_result}")

    if not records:
        print("\n  [No approved commands to execute]")

    print("\n" + "=" * 70)
    print("  HITL PIPELINE COMPLETE")
    print("=" * 70)

    return engine


if __name__ == "__main__":
    run_hitl_demo()
