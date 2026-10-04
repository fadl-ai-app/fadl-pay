"""
FADL PAY — Merchant RBAC Core

Step 1E:
Server-side role and permission engine.

Route enforcement is intentionally handled
as a separate step.
"""

ROLE_PERMISSIONS = {
    "owner": frozenset({
        "merchant.read",
        "merchant.manage",
        "transactions.read",
        "transactions.manage",
        "financial_admin.read",
        "reports.read",
        "api_credentials.read",
        "api_credentials.manage",
        "webhook.read",
        "webhook.manage",
        "authentication.read",
        "authentication.manage",
    }),
}


def normalize_role(role):
    value = (role or "owner").strip().lower()
    return value or "owner"


def has_permission(role, permission):
    canonical_role = normalize_role(role)

    return permission in ROLE_PERMISSIONS.get(
        canonical_role,
        frozenset(),
    )


def require_permission(role, permission):
    if not has_permission(role, permission):
        raise PermissionError(
            f"Permission denied: role={normalize_role(role)!r}, "
            f"permission={permission!r}"
        )


def permissions_for_role(role):
    return ROLE_PERMISSIONS.get(
        normalize_role(role),
        frozenset(),
    )
