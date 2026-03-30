"""
TUI configuration wizard for CCB Mail.

Uses textual for terminal UI.
"""

import sys
from typing import Optional

from i18n_runtime import t

# Check if textual is available
try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical
    from textual.widgets import (
        Button, Footer, Header, Input, Label,
        ListItem, ListView, Static, Select
    )
    from textual.screen import Screen
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

from mail.config import (
    MailConfig, AccountConfig, PollingConfig,
    ImapConfig, SmtpConfig, PROVIDER_PRESETS, load_config, save_config,
)
from mail.credentials import store_password, has_password
from mail.poller import ImapPoller
from mail.sender import SmtpSender
from mail.adapters.gmail import GmailAdapter
from mail.adapters.outlook import OutlookAdapter
from mail.adapters.qq import QQMailAdapter


ADAPTERS = {
    "gmail": GmailAdapter(),
    "outlook": OutlookAdapter(),
    "qq": QQMailAdapter(),
}


def run_simple_wizard() -> bool:
    """Run a simple text-based wizard (fallback when textual unavailable)."""
    print(f"\n=== {t('ccb.mail_tui.simple.title')} ===\n")

    # Load existing config
    config = load_config()

    # Step 1: Select provider
    print(t("ccb.mail_tui.simple.select_provider"))
    print(f"  1. {t('ccb.mail_tui.provider.gmail')}")
    print(f"  2. {t('ccb.mail_tui.provider.outlook')}")
    print(f"  3. {t('ccb.mail_tui.provider.qq')}")
    print(f"  4. {t('ccb.mail_tui.provider.custom')}")

    choice = input(f"\n{t('ccb.mail_tui.simple.prompt_provider_choice')} ").strip()
    provider_map = {"1": "gmail", "2": "outlook", "3": "qq", "4": "custom"}
    provider = provider_map.get(choice, "custom")

    # Show auth instructions
    if provider in ADAPTERS:
        adapter = ADAPTERS[provider]
        print(f"\n{adapter.get_auth_instructions()}\n")

    # Step 2: Enter email
    default_email = config.account.email or ""
    email = input(
        t("ccb.mail_tui.simple.prompt_email", default_email=default_email or "-")
    ).strip()
    if not email:
        email = default_email
    if not email:
        print(t("ccb.mail_tui.simple.error_email_required"))
        return False

    # Step 3: Enter password
    has_existing = has_password(email)
    if has_existing:
        print(t("ccb.mail_tui.simple.password_exists", email=email))
        change = input(f"{t('ccb.mail_tui.simple.prompt_change_password')} ").strip().lower()
        if change == "y":
            import getpass
            password = getpass.getpass(t("ccb.mail_tui.simple.prompt_app_password"))
            if password:
                store_password(email, password)
    else:
        import getpass
        password = getpass.getpass(t("ccb.mail_tui.simple.prompt_app_password"))
        if not password:
            print(t("ccb.mail_tui.simple.error_password_required"))
            return False
        store_password(email, password)

    # Step 4: Configure routing
    print(f"\n{t('ccb.mail_tui.simple.select_routing_mode')}")
    print(f"  1. {t('ccb.mail_tui.simple.routing_plus_alias')}")
    print(f"  2. {t('ccb.mail_tui.simple.routing_subject_prefix')}")

    route_choice = input(f"\n{t('ccb.mail_tui.simple.prompt_routing_choice')} ").strip()
    _routing_mode = "subject_prefix" if route_choice == "2" else "plus_alias"

    # Step 5: Default provider
    print(f"\n{t('ccb.mail_tui.simple.select_default_provider')}")
    print(f"  1. {t('ccb.provider.claude')}")
    print(f"  2. {t('ccb.provider.codex')}")
    print(f"  3. {t('ccb.provider.gemini')}")
    print(f"  4. {t('ccb.provider.opencode')}")
    print(f"  5. {t('ccb.provider.droid')}")

    default_choice = input(f"\n{t('ccb.mail_tui.simple.prompt_default_provider')} ").strip()
    default_map = {"1": "claude", "2": "codex", "3": "gemini", "4": "opencode", "5": "droid"}
    default_provider = default_map.get(default_choice, "claude")

    # Step 6: Allowed senders (whitelist)
    print(f"\n{t('ccb.mail_tui.simple.allowed_senders_title')}")
    print(f"  {t('ccb.mail_tui.simple.allowed_senders_desc_1')}")
    print(f"  {t('ccb.mail_tui.simple.allowed_senders_desc_2')}")
    allowed_input = input(f"\n{t('ccb.mail_tui.simple.prompt_allowed_senders')} ").strip()
    allowed_senders = [s.strip() for s in allowed_input.split(",") if s.strip()] if allowed_input else []

    # Step 7: Reply address
    print(f"\n{t('ccb.mail_tui.simple.reply_to_title')}")
    print(f"  {t('ccb.mail_tui.simple.reply_to_desc_1')}")
    print(f"  {t('ccb.mail_tui.simple.reply_to_desc_2')}")
    reply_to = input(f"\n{t('ccb.mail_tui.simple.prompt_reply_to')} ").strip()

    # Build config
    if provider in PROVIDER_PRESETS:
        config.account = AccountConfig.from_preset(provider, email)
    else:
        # Custom provider
        print(f"\n{t('ccb.mail_tui.simple.custom_imap_title')}")
        imap_host = input(t("ccb.mail_tui.simple.prompt_imap_host")).strip()
        imap_port = int(input(t("ccb.mail_tui.simple.prompt_imap_port")).strip() or "993")

        print(f"\n{t('ccb.mail_tui.simple.custom_smtp_title')}")
        smtp_host = input(t("ccb.mail_tui.simple.prompt_smtp_host")).strip()
        smtp_port = int(input(t("ccb.mail_tui.simple.prompt_smtp_port")).strip() or "587")

        config.account = AccountConfig(
            provider="custom",
            email=email,
            imap=ImapConfig(host=imap_host, port=imap_port, ssl=True),
            smtp=SmtpConfig(host=smtp_host, port=smtp_port, starttls=True),
        )

    config.account.email = email

    # V3 config no longer has RoutingConfig.
    # Keep setup inputs mapped to current fields:
    # - default provider stays explicit
    # - target_email acts as the authorized/reply address
    config.default_provider = default_provider
    if reply_to:
        config.target_email = reply_to
    elif allowed_senders:
        config.target_email = allowed_senders[0]

    # Step 8: Test connection
    print(f"\n{t('ccb.mail_tui.simple.testing_connection')}")

    poller = ImapPoller(config)
    imap_ok, imap_msg = poller.test_connection()
    print(t("ccb.mail_tui.simple.test_imap", message=imap_msg))

    sender = SmtpSender(config)
    smtp_ok, smtp_msg = sender.test_connection()
    print(t("ccb.mail_tui.simple.test_smtp", message=smtp_msg))

    if not (imap_ok and smtp_ok):
        save_anyway = input(f"\n{t('ccb.mail_tui.simple.prompt_save_anyway')} ").strip().lower()
        if save_anyway != "y":
            return False

    # Save config
    config.enabled = True
    save_config(config)
    print(f"\n{t('ccb.mail_tui.simple.config_saved')}")

    # Start service?
    start = input(f"\n{t('ccb.mail_tui.simple.prompt_start_service')} ").strip().lower()
    if start != "n":
        from mail.daemon import start_daemon
        print(t("ccb.mail_tui.simple.starting_daemon"))
        start_daemon(foreground=False)

    return True


# Textual TUI App (if available)
if TEXTUAL_AVAILABLE:
    class WelcomeScreen(Screen):
        """Welcome screen."""

        def compose(self) -> ComposeResult:
            yield Header()
            yield Container(
                Static(t("ccb.mail_tui.textual.welcome_title"), classes="title"),
                Static(
                    t("ccb.mail_tui.textual.welcome_description"),
                    classes="description",
                ),
                Static(
                    t("ccb.mail_tui.textual.welcome_features"),
                    classes="features",
                ),
                Horizontal(
                    Button(t("ccb.mail_tui.textual.button_continue"), id="continue", variant="primary"),
                    Button(t("ccb.mail_tui.textual.button_cancel"), id="cancel"),
                    classes="buttons",
                ),
                id="welcome",
            )
            yield Footer()

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "continue":
                self.app.push_screen("provider")
            else:
                self.app.exit()

    class ProviderScreen(Screen):
        """Provider selection screen."""

        def compose(self) -> ComposeResult:
            yield Header()
            yield Container(
                Static(t("ccb.mail_tui.textual.provider_title"), classes="title"),
                ListView(
                    ListItem(Label(t("ccb.mail_tui.provider.gmail")), id="gmail"),
                    ListItem(Label(t("ccb.mail_tui.provider.outlook")), id="outlook"),
                    ListItem(Label(t("ccb.mail_tui.provider.qq")), id="qq"),
                    ListItem(Label(t("ccb.mail_tui.provider.custom_server")), id="custom"),
                    id="provider-list",
                ),
                Horizontal(
                    Button(t("ccb.mail_tui.textual.button_back"), id="back"),
                    Button(t("ccb.mail_tui.textual.button_next"), id="next", variant="primary"),
                    classes="buttons",
                ),
                id="provider",
            )
            yield Footer()

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "back":
                self.app.pop_screen()
            elif event.button.id == "next":
                self.app.push_screen("account")

    class MailSetupApp(App):
        """Mail setup TUI application."""

        CSS = """
        .title {
            text-align: center;
            text-style: bold;
            margin: 1 0;
        }
        .description {
            margin: 1 2;
        }
        .features {
            margin: 1 2;
        }
        .buttons {
            margin: 2 0;
            align: center middle;
        }
        Button {
            margin: 0 1;
        }
        """

        SCREENS = {
            "welcome": WelcomeScreen,
            "provider": ProviderScreen,
        }

        def on_mount(self) -> None:
            self.push_screen("welcome")


def run_wizard() -> bool:
    """Run the mail setup wizard."""
    if TEXTUAL_AVAILABLE:
        try:
            app = MailSetupApp()
            app.run()
            return True
        except Exception as e:
            print(t("ccb.mail_tui.error_fallback", error=e))

    return run_simple_wizard()
