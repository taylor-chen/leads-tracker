"""Admin commands.

python -m app.cli create-user --email a@b.com --password secret123 --name "Jane Doe"
python -m app.cli seed   # creates SEED_ATTORNEY_* user if configured and missing
"""

import argparse
import logging
import sys

from app.core.config import get_settings
from app.core.errors import DomainError
from app.core.logging import configure_logging
from app.db.session import get_sessionmaker
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

logger = logging.getLogger("app.cli")


def create_user(email: str, password: str, name: str) -> None:
    """Create an attorney account. Raises `DomainError` on a bad password or duplicate email."""
    with get_sessionmaker()() as db:
        user = AuthService(db, get_settings()).create_user(
            email=email, password=password, full_name=name
        )
        logger.info("Created user %s", user.email)


def seed() -> None:
    """Create the SEED_ATTORNEY_* user if it's configured and doesn't exist yet. Idempotent."""
    settings = get_settings()
    if not (settings.seed_attorney_email and settings.seed_attorney_password):
        logger.info("No SEED_ATTORNEY_EMAIL/PASSWORD configured; skipping seed")
        return
    with get_sessionmaker()() as db:
        if UserRepository(db).get_by_email(settings.seed_attorney_email):
            logger.info("Seed user %s already exists", settings.seed_attorney_email)
            return
    create_user(
        settings.seed_attorney_email, settings.seed_attorney_password, settings.seed_attorney_name
    )


def main(argv: list[str] | None = None) -> int:
    """Parse `argv` and run the command. Returns the process exit code."""
    configure_logging(get_settings().log_level)
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    cu = sub.add_parser("create-user", help="Create an internal (attorney) user")
    cu.add_argument("--email", required=True)
    cu.add_argument("--password", required=True)
    cu.add_argument("--name", required=True)

    sub.add_parser("seed", help="Create the seed attorney user from env, if configured")

    args = parser.parse_args(argv)
    try:
        if args.command == "create-user":
            create_user(args.email, args.password, args.name)
        elif args.command == "seed":
            seed()
    except DomainError as exc:
        logger.error(exc.message)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
