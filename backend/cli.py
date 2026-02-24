"""
CLI commands for OCR Platform administration.

Usage:
    uv run python -m backend.cli <command> [args]

Commands:
    create-admin <username> <password>  Create a new admin user
    list-users                         List all users
    delete-user <username>             Delete a user by username
    change-password <username> <new>   Change user password
    set-admin <username> <true|false>  Toggle admin status
"""
import asyncio
import sys
from pathlib import Path
from tabulate import tabulate

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from auth import hash_password
from database import crud
from database.pool import connect


async def create_admin_user(username: str, password: str):
    """Create an admin user."""
    existing_user = await crud.get_user_by_username(username)
    if existing_user:
        print(f"✗ Error: User '{username}' already exists.")
        return False

    hashed = hash_password(password)
    user_id = await crud.create_user(username, hashed, is_admin=True)

    print(f"✓ Admin user created successfully!")
    print(f"  Username: {username}")
    print(f"  User ID: {user_id}")
    return True


async def create_demo_user(username: str, password: str):
    """Create a limited demo user (for testing)."""
    existing_user = await crud.get_user_by_username(username)
    if existing_user:
        print(f"✗ Error: User '{username}' already exists.")
        return False

    hashed = hash_password(password)
    user_id = await crud.create_user(username, hashed, is_admin=False, is_limited=True)

    print(f"✓ Demo user created successfully!")
    print(f"  Username: {username}")
    print(f"  Password: {password}")
    print(f"  User ID: {user_id}")
    print(f"  Limit: 5 requests/day")
    return True


async def create_demo_users(count: int = 5):
    """Create multiple demo users for testing."""
    import random
    import string
    
    created = []
    for i in range(1, count + 1):
        username = f"test{i}"
        # Generate random 6-char password
        password = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        hashed = hash_password(password)
        user_id = await crud.create_user(username, hashed, is_admin=False, is_limited=True)
        created.append((username, password, user_id))
    
    print(f"\n✓ Created {count} demo users:")
    print("-" * 40)
    for username, password, uid in created:
        print(f"  {username} / {password}")
    print("-" * 40)
    print("All users have: 5 requests/day limit")
    return True


async def list_all_users():
    """List all users."""
    users = await crud.list_users()

    if not users:
        print("No users found.")
        return True

    headers = ["ID", "Username", "Admin", "Created At"]
    rows = []
    for user in users:
        rows.append([
            user["id"],
            user["username"],
            "✓" if user["is_admin"] else "✗",
            user["created_at"]
        ])

    print("\n" + tabulate(rows, headers=headers, tablefmt="grid"))
    print(f"\nTotal: {len(users)} user(s)")
    return True


async def delete_user(username: str):
    """Delete a user by username."""
    user = await crud.get_user_by_username(username)
    if not user:
        print(f"✗ Error: User '{username}' not found.")
        return False

    try:
        async with connect() as db:
            await db.execute("DELETE FROM users WHERE username = ?", (username,))
            await db.commit()
        print(f"✓ User '{username}' deleted successfully.")
        return True
    except Exception as e:
        print(f"✗ Error deleting user: {e}")
        return False


async def change_password(username: str, new_password: str):
    """Change user password."""
    user = await crud.get_user_by_username(username)
    if not user:
        print(f"✗ Error: User '{username}' not found.")
        return False

    hashed = hash_password(new_password)

    try:
        async with connect() as db:
            await db.execute(
                "UPDATE users SET hashed_password = ? WHERE username = ?",
                (hashed, username)
            )
            await db.commit()
        print(f"✓ Password updated for user '{username}'.")
        return True
    except Exception as e:
        print(f"✗ Error updating password: {e}")
        return False


async def set_admin_status(username: str, is_admin_str: str):
    """Toggle admin status for a user."""
    user = await crud.get_user_by_username(username)
    if not user:
        print(f"✗ Error: User '{username}' not found.")
        return False

    is_admin = is_admin_str.lower() in ('true', '1', 'yes', 'y')

    try:
        async with connect() as db:
            await db.execute(
                "UPDATE users SET is_admin = ? WHERE username = ?",
                (is_admin, username)
            )
            await db.commit()
        status = "admin" if is_admin else "regular user"
        print(f"✓ User '{username}' is now a {status}.")
        return True
    except Exception as e:
        print(f"✗ Error updating user: {e}")
        return False


def print_help():
    """Print help message."""
    print("OCR Platform CLI")
    print("\nCommands:")
    print("  create-admin <username> <password>     Create a new admin user")
    print("  create-demo <username> <password>     Create a limited demo user")
    print("  create-demo-batch <count>             Create batch demo users (e.g., 5)")
    print("  list-users                             List all users")
    print("  delete-user <username>                 Delete a user")
    print("  change-password <username> <new>       Change user password")
    print("  set-admin <username> <true|false>      Set admin status")
    print("  set-limited <username> <true|false>   Set limited status")
    print("\nExamples:")
    print("  uv run python -m backend.cli create-admin admin1 securepass123")
    print("  uv run python -m backend.cli create-demo testuser1 pass123")
    print("  uv run python -m backend.cli create-demo-batch 10")
    print("  uv run python -m backend.cli list-users")
    print("  uv run python -m backend.cli change-password admin1 newpass456")


async def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    command = sys.argv[1]

    if command == "create-admin":
        if len(sys.argv) < 4:
            print("✗ Error: Username and password required.")
            print("Usage: python -m backend.cli create-admin <username> <password>")
            sys.exit(1)
        username = sys.argv[2]
        password = sys.argv[3]
        await create_admin_user(username, password)

    elif command == "list-users":
        await list_all_users()

    elif command == "delete-user":
        if len(sys.argv) < 3:
            print("✗ Error: Username required.")
            print("Usage: python -m backend.cli delete-user <username>")
            sys.exit(1)
        username = sys.argv[2]
        await delete_user(username)

    elif command == "change-password":
        if len(sys.argv) < 4:
            print("✗ Error: Username and new password required.")
            print("Usage: python -m backend.cli change-password <username> <new_password>")
            sys.exit(1)
        username = sys.argv[2]
        new_password = sys.argv[3]
        await change_password(username, new_password)

    elif command == "set-admin":
        if len(sys.argv) < 4:
            print("✗ Error: Username and status required.")
            print("Usage: python -m backend.cli set-admin <username> <true|false>")
            sys.exit(1)
        username = sys.argv[2]
        status = sys.argv[3]
        await set_admin_status(username, status)

    elif command == "create-demo":
        if len(sys.argv) < 4:
            print("✗ Error: Username and password required.")
            print("Usage: python -m backend.cli create-demo <username> <password>")
            sys.exit(1)
        username = sys.argv[2]
        password = sys.argv[3]
        await create_demo_user(username, password)

    elif command == "create-demo-batch":
        count = 5  # default
        if len(sys.argv) >= 3:
            try:
                count = int(sys.argv[2])
            except ValueError:
                print("✗ Error: Count must be a number.")
                sys.exit(1)
        await create_demo_users(count)

    elif command == "set-limited":
        if len(sys.argv) < 4:
            print("✗ Error: Username and status required.")
            print("Usage: python -m backend.cli set-limited <username> <true|false>")
            sys.exit(1)
        username = sys.argv[2]
        is_limited_str = sys.argv[3]
        is_limited = is_limited_str.lower() in ('true', '1', 'yes', 'y')
        
        user = await crud.get_user_by_username(username)
        if not user:
            print(f"✗ Error: User '{username}' not found.")
            sys.exit(1)
        
        async with connect() as db:
            await db.execute(
                "UPDATE users SET is_limited = ? WHERE username = ?",
                (is_limited, username)
            )
            await db.commit()
        
        status = "limited" if is_limited else "unlimited"
        print(f"✓ User '{username}' is now {status}.")

    else:
        print(f"✗ Error: Unknown command '{command}'")
        print_help()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
