from onboarding.models import SalaryAnnexureHistory

def log_salary_annexure_history(annexure, action, user=None, remarks=None):
    SalaryAnnexureHistory.objects.create(
        annexure=annexure,
        action=action,
        performed_by=user,
        remarks=remarks,
        snapshot=get_annexure_snapshot(annexure)
    )

def get_annexure_snapshot(annexure):
    return {
        "annexure": {
            "designation": annexure.designation,
            "effective_from": str(annexure.effective_from),
            "gross_monthly": str(annexure.gross_monthly),
            "ctc_annual": str(annexure.ctc_annual),
            "net_monthly": str(annexure.net_monthly),
            "status": annexure.status,
            "revision_count": annexure.revision_count,
            "notes": annexure.notes,
            "rejection_reason": annexure.rejection_reason,
        },
        "components": [
            {
                "name": c.name,
                "type": c.component_type,
                "monthly": str(c.monthly_amount),
                "annual": str(c.annual_amount),
                "statutory": c.is_statutory,
                "order": c.order,
            }
            for c in annexure.components.all()
        ]
    }
