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
            "basic_da": str(annexure.basic_da),
            "basket_allowances": str(annexure.basket_allowances),
            "hra": str(annexure.hra),
            "medical_allowance": str(annexure.medical_allowance),
            "leave_travel_allowance": str(annexure.leave_travel_allowance),
            "telephone_internet_allowance": str(annexure.telephone_internet_allowance),
            "books_periodicals": str(annexure.books_periodicals),
            "uniform_allowance": str(annexure.uniform_allowance),
            "driver_salary": str(annexure.driver_salary),
            "car_maintenance": str(annexure.car_maintenance),
            "meals_allowance": str(annexure.meals_allowance),
            "special_allowance": str(annexure.special_allowance),
            "children_education_allowance": str(annexure.children_education_allowance),
            "conveyance_allowance": str(annexure.conveyance_allowance),
            "employer_pf": str(annexure.employer_pf),
            "employer_insurance": str(annexure.employer_insurance),
            "employer_variable_component": str(annexure.employer_variable_component),
            "employer_gratuity": str(annexure.employer_gratuity),
            "employer_esic": str(annexure.employer_esic),
            "employer_total": str(annexure.employer_total),
            "employee_pf": str(annexure.employee_pf),
            "employee_pt": str(annexure.employee_pt),
            "employee_esic": str(annexure.employee_esic),
            "employee_total": str(annexure.employee_total),
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
