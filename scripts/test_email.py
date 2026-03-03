#!/usr/bin/env python3
"""
Test script for Remembra email system.

Tests all email templates and providers.

Usage:
    # Test with Resend (recommended)
    RESEND_API_KEY=your_key python scripts/test_email.py --provider resend --email test@example.com

    # Test with SMTP (Gmail)
    SMTP_USERNAME=user@gmail.com SMTP_PASSWORD=app_password python scripts/test_email.py --provider smtp --email test@example.com

    # Test all templates
    python scripts/test_email.py --provider resend --email test@example.com --all
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from remembra.cloud.email import EmailService, EmailProvider


async def test_welcome_email(service: EmailService, email: str) -> bool:
    """Test welcome email template."""
    print("\n📧 Testing welcome email...")
    result = await service.send_welcome_email(
        to=email,
        api_key="rem_test_1234567890abcdef",
        user_id="user_test123",
        plan="Free",
    )
    
    if result.success:
        print(f"  ✅ Welcome email sent successfully!")
        if result.message_id:
            print(f"  📨 Message ID: {result.message_id}")
        return True
    else:
        print(f"  ❌ Failed: {result.error}")
        return False


async def test_usage_warning_email(service: EmailService, email: str) -> bool:
    """Test usage warning email template."""
    print("\n⚠️  Testing usage warning email...")
    result = await service.send_usage_warning_email(
        to=email,
        usage_percent=85,
        current_usage=850,
        limit=1000,
        plan="Free",
    )
    
    if result.success:
        print(f"  ✅ Usage warning email sent successfully!")
        if result.message_id:
            print(f"  📨 Message ID: {result.message_id}")
        return True
    else:
        print(f"  ❌ Failed: {result.error}")
        return False


async def test_limit_exceeded_email(service: EmailService, email: str) -> bool:
    """Test limit exceeded email template."""
    print("\n🚨 Testing limit exceeded email...")
    result = await service.send_limit_exceeded_email(
        to=email,
        current_usage=1000,
        limit=1000,
        plan="Free",
    )
    
    if result.success:
        print(f"  ✅ Limit exceeded email sent successfully!")
        if result.message_id:
            print(f"  📨 Message ID: {result.message_id}")
        return True
    else:
        print(f"  ❌ Failed: {result.error}")
        return False


async def test_payment_receipt_email(service: EmailService, email: str) -> bool:
    """Test payment receipt email template."""
    print("\n💰 Testing payment receipt email...")
    result = await service.send_payment_receipt_email(
        to=email,
        amount="$49.00",
        invoice_url="https://invoice.stripe.com/i/test_123",
        plan="Pro",
        period_start="March 1, 2026",
        period_end="April 1, 2026",
    )
    
    if result.success:
        print(f"  ✅ Payment receipt email sent successfully!")
        if result.message_id:
            print(f"  📨 Message ID: {result.message_id}")
        return True
    else:
        print(f"  ❌ Failed: {result.error}")
        return False


async def test_subscription_cancelled_email(service: EmailService, email: str) -> bool:
    """Test subscription cancelled email template."""
    print("\n🔄 Testing subscription cancelled email...")
    result = await service.send_subscription_cancelled_email(
        to=email,
        plan="Pro",
        cancel_date="April 1, 2026",
    )
    
    if result.success:
        print(f"  ✅ Subscription cancelled email sent successfully!")
        if result.message_id:
            print(f"  📨 Message ID: {result.message_id}")
        return True
    else:
        print(f"  ❌ Failed: {result.error}")
        return False


async def main():
    parser = argparse.ArgumentParser(
        description="Test Remembra email system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--provider",
        choices=["resend", "smtp"],
        default="resend",
        help="Email provider to use (default: resend)",
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Email address to send test emails to",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Test all email templates (default: just welcome email)",
    )
    parser.add_argument(
        "--template",
        choices=["welcome", "usage_warning", "limit_exceeded", "payment_receipt", "subscription_cancelled"],
        help="Test a specific template",
    )
    
    args = parser.parse_args()
    
    # Create email service
    print(f"\n🚀 Initializing email service with {args.provider.upper()} provider...")
    try:
        provider = EmailProvider.RESEND if args.provider == "resend" else EmailProvider.SMTP
        service = EmailService.create(provider=provider)
        print(f"  ✅ Email service initialized")
    except Exception as e:
        print(f"  ❌ Failed to initialize email service: {e}")
        print(f"\n💡 Make sure you have the required environment variables set:")
        if args.provider == "resend":
            print(f"   - RESEND_API_KEY")
        else:
            print(f"   - SMTP_HOST (default: smtp.gmail.com)")
            print(f"   - SMTP_PORT (default: 587)")
            print(f"   - SMTP_USERNAME")
            print(f"   - SMTP_PASSWORD")
        return 1
    
    # Run tests
    print(f"\n📬 Sending test emails to: {args.email}")
    print(f"=" * 60)
    
    results = []
    
    if args.template == "welcome" or args.all or (not args.template and not args.all):
        results.append(await test_welcome_email(service, args.email))
    
    if args.template == "usage_warning" or args.all:
        results.append(await test_usage_warning_email(service, args.email))
    
    if args.template == "limit_exceeded" or args.all:
        results.append(await test_limit_exceeded_email(service, args.email))
    
    if args.template == "payment_receipt" or args.all:
        results.append(await test_payment_receipt_email(service, args.email))
    
    if args.template == "subscription_cancelled" or args.all:
        results.append(await test_subscription_cancelled_email(service, args.email))
    
    # Summary
    print(f"\n" + "=" * 60)
    success_count = sum(results)
    total_count = len(results)
    
    if success_count == total_count:
        print(f"✅ All {total_count} test(s) passed!")
        print(f"\n💡 Check {args.email} for the test emails")
        return 0
    else:
        print(f"❌ {total_count - success_count} of {total_count} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
