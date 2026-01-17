import argparse
from datetime import datetime
import sys

from app.infra.models.api_key_model import ApiKeyModel
from app.infra.session import get_session
from app.services.api_key_service import ALLOWED_API_KEY_ROLES, generate_api_key, hash_api_key


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a new API key")
    parser.add_argument("--name", required=True, help="Human-readable name for the key")
    parser.add_argument("--role", required=True, help="Role: admin, runner, or readonly")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    role = args.role.strip()
    if role not in ALLOWED_API_KEY_ROLES:
        print(
            f"Invalid role '{role}'. Expected one of: {', '.join(sorted(ALLOWED_API_KEY_ROLES))}.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    plain_key = generate_api_key()
    key_hash = hash_api_key(plain_key)

    with get_session() as session:
        api_key = ApiKeyModel(
            name=args.name.strip(),
            key_hash=key_hash,
            role=role,
            active=True,
            created_at=datetime.utcnow(),
        )
        session.add(api_key)
        session.commit()

    print(plain_key)


if __name__ == "__main__":
    main()
