import database_mock as db
from graph.state import SupportState

# Mapping intention -> fonction à appeler
ACTION_MAP = {
    "order_status": db.get_order_status,
    "return_refund": db.check_refund_eligibility,
}

def action_node(state: SupportState) -> SupportState:
    intent = state.get("intent")
    entities = state.get("action_result", {}).get("extracted_entities", {})
    order_id = entities.get("order_id")
    
    if not order_id:
        return {
            **state,
            "action_success": False,
            "needs_escalation": True,
            "escalation_reason": "no_order_id",
        }
    
    func = ACTION_MAP.get(intent)
    if not func:
        return {
            **state,
            "action_success": False,
            "needs_escalation": True,
            "escalation_reason": "no_action_for_intent",
        }
    
    result = func(order_id)
    
    if result is None:
        return {
            **state,
            "action_success": False,
            "action_result": None,
            "needs_escalation": True,
            "escalation_reason": "action_methode_no_data_returned",
        }

    # Handle not eligible case with specific reason from the function
    if isinstance(result, dict) and result.get("eligible") is False:
        reason = result.get("reason", "unknown_reason")
        
        return {
            **state,
            "action_success": False,
            "action_result": result,           # keep full info
            "needs_escalation": True,
            "escalation_reason": f"refund_not_eligible_{reason}",   # ← Much better!
        }

    # Success case
    return {
        **state,
        "action_success": True,
        "action_result": result,
        "needs_escalation": False,
    }
    