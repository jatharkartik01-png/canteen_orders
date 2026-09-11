from pydantic import EmailStr


async def send_reset_email(email: EmailStr, reset_url: str):
  """Mock email service that prints the password reset link directly to your

  terminal console. This bypasses institutional Google Workspace SMTP blocks.
  """
  print("\n" + "=" * 60)
  print(f"📧 [MOCK EMAIL SERVICE] Destination: {email}")
  print(f"🔗 PASSWORD RESET LINK:\n{reset_url}")
  print("=" * 60 + "\n")