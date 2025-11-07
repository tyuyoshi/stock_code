"""Notification Service for Batch Job Results"""

import logging
import json
import smtplib
from datetime import datetime
from typing import Optional, Dict, Any, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, asdict
import requests
from enum import Enum

try:
    from ..core.config import settings
except ImportError:
    from core.config import settings

logger = logging.getLogger(__name__)


class NotificationLevel(Enum):
    """Notification severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class BatchJobResult:
    """Represents the result of a batch job execution"""
    job_name: str
    start_time: datetime
    end_time: datetime
    status: str  # "success", "partial_success", "failure"
    total_items: int
    successful_items: int
    failed_items: int
    error_messages: List[str]
    execution_time_seconds: float
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_items == 0:
            return 100.0
        return (self.successful_items / self.total_items) * 100.0


class NotificationService:
    """Service for sending notifications about batch job results"""
    
    def __init__(self):
        self.slack_webhook_url = getattr(settings, 'slack_webhook_url', None)
        self.email_enabled = getattr(settings, 'email_notifications_enabled', False)
        self.smtp_host = getattr(settings, 'smtp_host', None)
        self.smtp_port = getattr(settings, 'smtp_port', 587)
        self.smtp_username = getattr(settings, 'smtp_username', None)
        self.smtp_password = getattr(settings, 'smtp_password', None)
        self.notification_emails = getattr(settings, 'notification_emails', [])
    
    def notify_batch_result(self, result: BatchJobResult, level: NotificationLevel = NotificationLevel.INFO):
        """Send notification for batch job result"""
        try:
            # Determine notification level based on result
            if result.status == "failure":
                level = NotificationLevel.ERROR
            elif result.status == "partial_success" and result.success_rate < 80:
                level = NotificationLevel.WARNING
            elif result.status == "partial_success":
                level = NotificationLevel.INFO
            else:
                level = NotificationLevel.INFO
            
            # Send notifications
            if self.slack_webhook_url:
                self._send_slack_notification(result, level)
            
            if self.email_enabled and self.notification_emails:
                self._send_email_notification(result, level)
            
            logger.info(f"Notification sent for {result.job_name} with level {level.value}")
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    def _send_slack_notification(self, result: BatchJobResult, level: NotificationLevel):
        """Send Slack notification"""
        try:
            # Choose emoji and color based on level
            emoji_map = {
                NotificationLevel.INFO: "✅",
                NotificationLevel.WARNING: "⚠️",
                NotificationLevel.ERROR: "❌",
                NotificationLevel.CRITICAL: "🚨"
            }
            
            color_map = {
                NotificationLevel.INFO: "good",
                NotificationLevel.WARNING: "warning",
                NotificationLevel.ERROR: "danger",
                NotificationLevel.CRITICAL: "danger"
            }
            
            emoji = emoji_map.get(level, "ℹ️")
            color = color_map.get(level, "good")
            
            # Create Slack message
            title = f"{emoji} Stock Code - {result.job_name} Report"
            
            fields = [
                {"title": "Status", "value": result.status.title(), "short": True},
                {"title": "Success Rate", "value": f"{result.success_rate:.1f}%", "short": True},
                {"title": "Total Items", "value": str(result.total_items), "short": True},
                {"title": "Execution Time", "value": f"{result.execution_time_seconds:.1f}s", "short": True},
            ]
            
            if result.failed_items > 0:
                fields.append({
                    "title": "Failed Items", 
                    "value": str(result.failed_items), 
                    "short": True
                })
            
            # Add error messages if any
            if result.error_messages:
                error_text = "\n".join(result.error_messages[:5])  # Limit to 5 errors
                if len(result.error_messages) > 5:
                    error_text += f"\n... and {len(result.error_messages) - 5} more errors"
                fields.append({
                    "title": "Recent Errors",
                    "value": f"```{error_text}```",
                    "short": False
                })
            
            payload = {
                "attachments": [{
                    "color": color,
                    "title": title,
                    "fields": fields,
                    "footer": "Stock Code Scheduler",
                    "ts": int(result.end_time.timestamp())
                }]
            }
            
            response = requests.post(
                self.slack_webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.debug(f"Slack notification sent successfully for {result.job_name}")
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
    
    def _send_email_notification(self, result: BatchJobResult, level: NotificationLevel):
        """Send email notification"""
        try:
            if not self.smtp_host or not self.notification_emails:
                logger.warning("Email notification not configured properly")
                return
            
            # Create email content
            subject = f"Stock Code - {result.job_name} Report ({result.status.title()})"
            
            # Create HTML content
            html_content = self._create_email_html(result, level)
            
            # Create text content
            text_content = self._create_email_text(result)
            
            # Send email to each recipient
            for email in self.notification_emails:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = self.smtp_username
                msg['To'] = email
                
                # Add text and HTML parts
                msg.attach(MIMEText(text_content, 'plain'))
                msg.attach(MIMEText(html_content, 'html'))
                
                # Send email
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    if self.smtp_username and self.smtp_password:
                        server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
                
                logger.debug(f"Email notification sent to {email}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def _create_email_html(self, result: BatchJobResult, level: NotificationLevel) -> str:
        """Create HTML email content"""
        status_color = {
            "success": "#28a745",
            "partial_success": "#ffc107",
            "failure": "#dc3545"
        }.get(result.status, "#6c757d")
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <h2 style="color: {status_color};">Stock Code - {result.job_name} Report</h2>
            
            <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Status</td>
                    <td style="border: 1px solid #ddd; padding: 8px; color: {status_color};">{result.status.title()}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Start Time</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{result.start_time.strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">End Time</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{result.end_time.strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Execution Time</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{result.execution_time_seconds:.1f} seconds</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Total Items</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{result.total_items}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Successful</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{result.successful_items}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Failed</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{result.failed_items}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Success Rate</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{result.success_rate:.1f}%</td>
                </tr>
            </table>
        """
        
        if result.error_messages:
            html += """
            <h3 style="color: #dc3545;">Error Messages</h3>
            <ul>
            """
            for error in result.error_messages[:10]:  # Limit to 10 errors
                html += f"<li>{error}</li>"
            if len(result.error_messages) > 10:
                html += f"<li><em>... and {len(result.error_messages) - 10} more errors</em></li>"
            html += "</ul>"
        
        html += """
            <p style="margin-top: 30px; color: #6c757d; font-size: 12px;">
                This is an automated message from Stock Code Scheduler.
            </p>
        </body>
        </html>
        """
        
        return html
    
    def _create_email_text(self, result: BatchJobResult) -> str:
        """Create plain text email content"""
        text = f"""
Stock Code - {result.job_name} Report

Status: {result.status.title()}
Start Time: {result.start_time.strftime('%Y-%m-%d %H:%M:%S')}
End Time: {result.end_time.strftime('%Y-%m-%d %H:%M:%S')}
Execution Time: {result.execution_time_seconds:.1f} seconds

Results:
- Total Items: {result.total_items}
- Successful: {result.successful_items}
- Failed: {result.failed_items}
- Success Rate: {result.success_rate:.1f}%
"""
        
        if result.error_messages:
            text += "\nError Messages:\n"
            for i, error in enumerate(result.error_messages[:10], 1):
                text += f"{i}. {error}\n"
            if len(result.error_messages) > 10:
                text += f"... and {len(result.error_messages) - 10} more errors\n"
        
        text += "\n--\nThis is an automated message from Stock Code Scheduler."
        
        return text
    
    def send_test_notification(self):
        """Send a test notification to verify configuration"""
        test_result = BatchJobResult(
            job_name="Test Notification",
            start_time=datetime.now(),
            end_time=datetime.now(),
            status="success",
            total_items=1,
            successful_items=1,
            failed_items=0,
            error_messages=[],
            execution_time_seconds=0.1
        )
        
        self.notify_batch_result(test_result, NotificationLevel.INFO)
        logger.info("Test notification sent")


# Global instance
notification_service = NotificationService()


def notify_batch_result(result: BatchJobResult, level: NotificationLevel = NotificationLevel.INFO):
    """Convenience function to send batch result notification"""
    notification_service.notify_batch_result(result, level)


def send_test_notification():
    """Convenience function to send test notification"""
    notification_service.send_test_notification()


if __name__ == "__main__":
    # Test the notification service
    logging.basicConfig(level=logging.INFO)
    send_test_notification()