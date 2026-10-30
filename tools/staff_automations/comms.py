import os
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import aiohttp
from tools.base_tool import BaseTool
from tools.registry import tool_registry

@tool_registry.register
class SendEmailTool(BaseTool):
    name = "send_email"
    description = "Sends an email to a specified recipient with subject and body content."
    risk_level = "high"  # Requires user confirmation via permissions.yaml

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "recipient": {
                    "type": "string",
                    "description": "Email address of the recipient (e.g. 'colleague@example.com')"
                },
                "subject": {
                    "type": "string",
                    "description": "Subject line of the email"
                },
                "body": {
                    "type": "string",
                    "description": "Plain text or HTML body of the email"
                },
                "is_html": {
                    "type": "boolean",
                    "description": "Whether the body contains HTML markup",
                    "default": False
                }
            },
            "required": ["recipient", "subject", "body"]
        }

    async def execute(self, recipient: str, subject: str, body: str, is_html: bool = False, **kwargs) -> Dict[str, Any]:
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        sender_email = os.getenv("SENDER_EMAIL", "")
        sender_password = os.getenv("SENDER_PASSWORD", "")

        if not sender_email or not sender_password:
            # Simulated sending if credentials are not configured
            return {
                "status": "simulated",
                "message": f"[Simulated Mode] Email drafted and would be sent to '{recipient}'. (SMTP credentials not configured in .env)",
                "to": recipient,
                "subject": subject,
                "preview": body[:120] + ("..." if len(body) > 120 else "")
            }

        def _send_sync():
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = sender_email
            msg["To"] = recipient
            part = MIMEText(body, "html" if is_html else "plain")
            msg.attach(part)

            with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient, msg.as_string())

        try:
            await asyncio.to_thread(_send_sync)
            return {
                "status": "success",
                "message": f"Email successfully dispatched to {recipient}",
                "recipient": recipient,
                "subject": subject
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to send email: {str(e)}",
                "recipient": recipient
            }

@tool_registry.register
class SendNotificationTool(BaseTool):
    name = "send_notification"
    description = "Sends an alert or notification payload to an external webhook (Slack, Discord, or generic endpoint)."
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Text message content for the notification alert"
                },
                "webhook_url": {
                    "type": "string",
                    "description": "Optional webhook URL (defaults to configured SLACK_OR_DISCORD_WEBHOOK_URL)"
                }
            },
            "required": ["message"]
        }

    async def execute(self, message: str, webhook_url: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        target_url = webhook_url or os.getenv("SLACK_OR_DISCORD_WEBHOOK_URL", "")
        if not target_url:
            return {
                "status": "simulated",
                "message": f"[Simulated Alert] Notification: {message}",
                "channel": "console"
            }

        try:
            async with aiohttp.ClientSession() as session:
                payload = {"text": message, "content": message}
                async with session.post(target_url, json=payload, timeout=5) as resp:
                    if resp.status in (200, 204):
                        return {"status": "success", "message": "Notification dispatched successfully"}
                    return {"status": "error", "message": f"Webhook returned status {resp.status}"}
        except Exception as e:
            return {"status": "error", "message": f"Notification delivery failed: {str(e)}"}

