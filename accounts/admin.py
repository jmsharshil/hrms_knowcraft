from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Company, MagicLink


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'email']
    readonly_fields = ['id']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    autocomplete_fields = ['company', 'department', 'created_by']
    list_display = ['email', 'name', 'role', 'company', 'phone', 'pin_set', 'is_active', 'created_at','department']
    list_filter = ['role', 'is_active', 'pin_set', 'created_at', 'company','department']
    search_fields = ['email', 'name', 'company__name']
    readonly_fields = ['id', 'last_login']
    
    fieldsets = (
        (None, {'fields': ('email', 'pin', 'pin_set' ,'department')}),
        ('Personal Info', {'fields': ('name', 'role', 'company','phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
        ('Metadata', {'fields': ('id', 'created_by')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'role', 'company', 'is_active', 'is_staff','phone','department'),
        }),
    )
    
    ordering = ['-created_at']
    filter_horizontal = ('groups', 'user_permissions')
    actions = [
        'preview_weekly_report_html',
        'send_weekly_report_dry_run',
        'send_weekly_report_email',
    ]

    def preview_weekly_report_html(self, request, queryset):
        """Preview weekly recruitment report directly in browser without sending any emails."""
        from django.http import HttpResponse
        from django.contrib import messages
        from mrf.utils import dept_head_weekly_report_task

        target_ids = list(queryset.values_list('id', flat=True)) if queryset.exists() else None
        data = dept_head_weekly_report_task(dry_run=True, target_user_ids=target_ids, return_details=True)

        reports = data.get("reports", [])
        if not reports:
            self.message_user(
                request,
                "No active, open, non-private MRFs found for the selected user(s). No reports generated.",
                level=messages.WARNING
            )
            return None

        cards_html = []
        for idx, r in enumerate(reports, start=1):
            cc_display = ", ".join(r["cc_list"]) if r["cc_list"] else "<em>None</em>"
            cards_html.append(f"""
            <div style="background:#ffffff;border:1px solid #cbd5e1;border-radius:10px;margin-bottom:30px;box-shadow:0 4px 6px -1px rgba(0,0,0,0.1);overflow:hidden;">
              <div style="background:#f1f5f9;border-bottom:1px solid #cbd5e1;padding:14px 20px;">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
                  <div>
                    <span style="background:#2563eb;color:#fff;font-size:12px;font-weight:bold;padding:3px 10px;border-radius:12px;margin-right:8px;">Report #{idx}</span>
                    <strong style="font-size:16px;color:#0f172a;">To: {r['requester_name']} &lt;{r['requester_email']}&gt;</strong>
                  </div>
                  <div style="font-size:13px;color:#475569;">
                    <strong>MRFs:</strong> {r['mrf_count']} &nbsp;|&nbsp; <strong>Candidates:</strong> {r['candidate_count']}
                  </div>
                </div>
                <div style="margin-top:8px;font-size:13px;color:#334155;">
                  <strong>CC Approvers ({len(r['cc_list'])}):</strong> <span style="color:#0369a1;">{cc_display}</span>
                </div>
                <div style="margin-top:4px;font-size:13px;color:#334155;">
                  <strong>Subject:</strong> {r['subject']}
                </div>
              </div>
              <div style="padding:24px;background:#f8fafc;">
                <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,0.05);overflow-x:auto;">
                  {r['template']}
                </div>
              </div>
            </div>
            """)

        full_page = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <title>Weekly Recruitment Report — Dry Run Preview</title>
          <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background:#0f172a; margin:0; padding:20px; color:#1e293b; }}
            .container {{ max-width: 1040px; margin: 0 auto; }}
            .header-bar {{ background: #1e293b; color: #f8fafc; padding: 20px 24px; border-radius: 10px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); }}
            .badge-safe {{ background: #10b981; color: #ffffff; padding: 5px 12px; border-radius: 9999px; font-weight: bold; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; display: inline-block; }}
            .btn-back {{ background: #3b82f6; color: #ffffff; text-decoration: none; padding: 8px 16px; border-radius: 6px; font-size: 14px; font-weight: 500; transition: background 0.2s; }}
            .btn-back:hover {{ background: #2563eb; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header-bar">
              <div>
                <span class="badge-safe">🛡️ Dry Run Test Mode — No Emails Sent</span>
                <h1 style="margin: 10px 0 4px 0; font-size: 22px; color: #ffffff;">Weekly Recruitment Report Preview</h1>
                <p style="margin: 0; font-size: 14px; color: #94a3b8;">
                  Generated <strong>{len(reports)}</strong> report(s). None of these emails were dispatched.
                </p>
              </div>
            </div>
            {''.join(cards_html)}
          </div>
        </body>
        </html>
        """
        return HttpResponse(full_page)

    preview_weekly_report_html.short_description = "Preview weekly report in browser (HTML Preview - NO emails sent)"

    def send_weekly_report_dry_run(self, request, queryset):
        """Execute weekly report task in dry-run mode (summary message only, no emails sent)."""
        from django.contrib import messages
        from django.utils.safestring import mark_safe
        from mrf.utils import dept_head_weekly_report_task

        target_ids = list(queryset.values_list('id', flat=True)) if queryset.exists() else None
        data = dept_head_weekly_report_task(dry_run=True, target_user_ids=target_ids, return_details=True)

        reports = data.get("reports", [])
        count = data.get("sent_count", 0)

        if count == 0:
            self.message_user(
                request,
                "Dry run completed. No active, open, non-private MRFs found to report for the selected user(s).",
                level=messages.WARNING
            )
            return

        summary_lines = []
        for r in reports:
            cc_str = ", ".join(r["cc_list"]) if r["cc_list"] else "none"
            summary_lines.append(
                f"<li><strong>{r['requester_name']}</strong> ({r['requester_email']}): "
                f"{r['mrf_count']} MRF(s), {r['candidate_count']} candidate(s) | CC: <em>{cc_str}</em></li>"
            )

        html_msg = (
            f"<strong>[DRY RUN COMPLETE — NO EMAILS SENT]</strong><br>"
            f"Would send weekly reports to <strong>{count}</strong> department head/requester(s):"
            f"<ul style='margin-top:6px;margin-bottom:4px;'>{''.join(summary_lines)}</ul>"
        )
        self.message_user(request, mark_safe(html_msg), level=messages.SUCCESS)

    send_weekly_report_dry_run.short_description = "Dry run weekly report (Check summary in admin - NO emails sent)"

    def send_weekly_report_email(self, request, queryset):
        """Run weekly recruitment status report email task (LIVE SEND)."""
        from mrf.utils import dept_head_weekly_report_task
        target_ids = list(queryset.values_list('id', flat=True)) if queryset.exists() else None
        count = dept_head_weekly_report_task(dry_run=False, target_user_ids=target_ids)
        self.message_user(request, f"Weekly report task executed. LIVE emails sent to {count} requester(s).")

    send_weekly_report_email.short_description = "Send LIVE weekly report email (Real send to requesters & CC)"


@admin.register(MagicLink)
class MagicLinkAdmin(admin.ModelAdmin):
    autocomplete_fields = ['user']
    list_display = ['user', 'purpose', 'created_at', 'expires_at', 'used', 'is_valid_status']
    list_filter = ['purpose', 'used', 'created_at']
    search_fields = ['user__email', 'user__name', 'token']
    readonly_fields = ['id', 'token', 'used_at']
    
    def is_valid_status(self, obj):
        return obj.is_valid()
    is_valid_status.boolean = True
    is_valid_status.short_description = 'Valid'