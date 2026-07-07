from dataclasses import dataclass
 
# Intents that return a single student's own data.
OWN_DATA_INTENTS = {"get_result", "get_attendance", "retrieve_context"}
 
# Intents that reveal OTHER students' names/identities -- admin only.
ADMIN_ONLY_INTENTS = {"get_top_performers", "get_failed_students"}
 
# Intents that are aggregate-only (no individual names) -- open to everyone.
PUBLIC_INTENTS = {"get_class_average", "get_class_summary", "unknown"}
 
 
@dataclass
class AccessContext:
    role: str = "admin"          # "student" or "admin"
    own_reg_no: str | None = None  # required when role == "student"
 
 
class AccessDenied(Exception):
    pass
 
 
def check_access(intent: str, target_reg_no: str | None, context: AccessContext) -> None:
    """Raises AccessDenied if the context's role isn't allowed to see this.
    Does nothing (silently allows) otherwise."""
    if context.role == "admin":
        return  # admins can see everything
 
    # role == "student" from here on
    if intent in ADMIN_ONLY_INTENTS:
        raise AccessDenied(
            "This information (class rankings / list of other students) "
            "is only available to admin accounts."
        )
 
    if intent in OWN_DATA_INTENTS and target_reg_no:
        if not context.own_reg_no:
            raise AccessDenied(
                "Please log in with your register number to view a result."
            )
        if str(target_reg_no) != str(context.own_reg_no):
            raise AccessDenied(
                "You can only view your own result/attendance, not another "
                "student's."
            )
 
    # PUBLIC_INTENTS and own-data-with-matching-reg-no fall through as allowed
 