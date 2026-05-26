# bgv/serializers.py

from rest_framework import serializers
from .models import CandidateBGV
from .services import VERIFICATION_NAMES


class CandidateBGVSerializer(serializers.ModelSerializer):

    candidate_name = serializers.CharField(
        source="candidate.candidate_name",
        read_only=True,
    )
    candidate_email = serializers.EmailField(
        source="candidate.candidate_email",
        read_only=True,
    )
    candidate_phone = serializers.CharField(
        source="candidate.candidate_phone",
        read_only=True,
    )
    job_title = serializers.CharField(
        source="candidate.job.job_title",
        read_only=True,
    )
    experience_years = serializers.DecimalField(
        source="candidate.experience_years",
        read_only=True,
        max_digits=4,
        decimal_places=1,
    )
    joining_date = serializers.DateField(
        source="candidate.joining_date",
        read_only=True,
    )

    # Enriched verification list: [{code, name}, ...]
    # Built from the verifications stored inside callback_payload, or from
    # the transient _verification_names attribute attached by initiate_bgv().
    verification_names = serializers.SerializerMethodField()

    def get_verification_names(self, obj):
        # We parse the verifications from either callback_payload or raw_initiation_payload
        payload = obj.callback_payload or {}
        verifications = (
            payload.get("verifications")
            or (payload.get("individual") or {}).get("verifications")
            or []
        )
        if not verifications:
            verifications = (obj.raw_initiation_payload or {}).get("verifications", [])
            
        ongrid_status = obj.ongrid_status or {}

        result = []
        seen = set()
        for v in verifications:
            code = v.get("code") if isinstance(v, dict) else str(v)
            if code and code not in seen:
                seen.add(code)
                
                # Fetch overall status for this specific verification (e.g., overallEDUVStatus)
                status_key = f"overall{code}Status"
                v_status = ongrid_status.get(status_key)
                
                # Fetch detailed states for this verification (e.g., eduvStates)
                states_key = f"{code.lower()}States"
                v_states = ongrid_status.get(states_key)
                
                latest_state = None
                if isinstance(v_states, list) and len(v_states) > 0:
                    latest_state = v_states[-1]  # Usually the last one is the most recent
                
                result.append({
                    "code": code,
                    "name": VERIFICATION_NAMES.get(code, code),
                    "status": v_status or "Initiated",
                    "details": latest_state,
                })
                
        # If there are transient verification names added during initiation,
        # merge them or fallback if verifications array is somehow empty.
        if hasattr(obj, "_verification_names") and not result:
            return [{"code": v["code"], "name": v["name"], "status": "Initiated", "details": None} for v in obj._verification_names]
            
        return result

    class Meta:
        model = CandidateBGV
        fields = [
            "id",
            "candidate",
            "candidate_name",
            "candidate_email",
            "candidate_phone",
            "job_title",
            "experience_years",
            "joining_date",
            "ongrid_individual_id",
            "status",
            "is_fresher",
            "bgv_scheduled_date",
            "report_url",
            "callback_payload",
            "raw_initiation_payload",
            "ongrid_status",
            "verification_names",
            "initiated_at",
            "completed_at",
            "remarks",
            # per-verification statuses
            "av_status", "bav_status", "cc_status", "ccrv_status", "cvv_status", 
            "dlv_status", "drg_status", "eduv_status", "efirc_status", "ehc_status", 
            "empv_status", "eref_status", "fmc_status", "gdc_status", "iaf_status", 
            "icav_status", "ipav_status", "ladv_status", "lapv_status", "lav_status", 
            "nsorc_status", "ofacc_status", "padv_status", "panv_status", "papv_status", 
            "pav_status", "pcc_status", "ppv_status", "prc_status", "pvlf_status", 
            "smc_status", "vidv_status", "xav_status",
        ]
        read_only_fields = [
            "id",
            "ongrid_individual_id",
            "status",
            "is_fresher",
            "bgv_scheduled_date",
            "report_url",
            "callback_payload",
            "raw_initiation_payload",
            "ongrid_status",
            "verification_names",
            "initiated_at",
            "completed_at",
            # per-verification statuses
            "av_status", "bav_status", "cc_status", "ccrv_status", "cvv_status", 
            "dlv_status", "drg_status", "eduv_status", "efirc_status", "ehc_status", 
            "empv_status", "eref_status", "fmc_status", "gdc_status", "iaf_status", 
            "icav_status", "ipav_status", "ladv_status", "lapv_status", "lav_status", 
            "nsorc_status", "ofacc_status", "padv_status", "panv_status", "papv_status", 
            "pav_status", "pcc_status", "ppv_status", "prc_status", "pvlf_status", 
            "smc_status", "vidv_status", "xav_status",
        ]