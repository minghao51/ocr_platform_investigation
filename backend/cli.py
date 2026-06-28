"""
CLI commands for OCR Platform administration.

Usage:
    uv run -m backend.cli <command> [args]

Commands:
    create-admin <username> <password>  Create a new admin user
    list-users                         List all users
    delete-user <username>             Delete a user by username
    change-password <username> <new>   Change user password
    set-admin <username> <true|false>  Toggle admin status
    run-benchmark                      Run a benchmark against a provider/model
    list-benchmarks                    List past benchmark runs
    show-benchmark <id>                Show detailed results for a benchmark run
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
from config import get_settings


def _demo_limit_label() -> str:
    return f"{get_settings().demo_daily_request_limit} requests/day"


async def run_benchmark_cli():
    """Run a benchmark from CLI arguments."""
    import argparse

    from benchmarks.datasets import list_available_datasets

    available_datasets = list_available_datasets()

    parser = argparse.ArgumentParser(description="Run OCR benchmark")
    parser.add_argument(
        "--provider", required=True, help="Provider name (openrouter, gemini)"
    )
    parser.add_argument("--model", required=True, help="Model identifier")
    parser.add_argument(
        "--dataset",
        default="cord",
        choices=available_datasets,
        help=f"Dataset name (default: cord, available: {', '.join(available_datasets)})",
    )
    parser.add_argument(
        "--limit", type=int, default=20, help="Max samples to process (default: 20)"
    )
    parser.add_argument("--data-dir", default=None, help="Path to dataset directory")
    parser.add_argument(
        "--prompt",
        default="Extract all information from this document as JSON.",
        help="Prompt",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Max concurrent API calls (default: 5)",
    )
    args = parser.parse_args(sys.argv[2:])

    settings = get_settings()
    api_key = getattr(settings, f"{args.provider}_api_key")
    if not api_key:
        print(f"✗ Error: No API key configured for {args.provider}")
        print("  Set the appropriate env var (e.g. NEBIUS_API_KEY) in .env")
        sys.exit(1)

    from benchmarks.runner import run_benchmark

    print("Starting benchmark:")
    print(f"  Provider: {args.provider}")
    print(f"  Model: {args.model}")
    print(f"  Dataset: {args.dataset}")
    print(f"  Samples: {args.limit}")
    print(f"  Data dir: {args.data_dir or '(default)'}")
    print(f"  Concurrency: {args.concurrency}")
    print()

    summary = await run_benchmark(
        provider_name=args.provider,
        model=args.model,
        api_key=api_key,
        dataset=args.dataset,
        limit=args.limit,
        data_dir=args.data_dir,
        prompt=args.prompt,
        concurrency=args.concurrency,
    )

    print()
    print("=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    print(f"  Run ID: {summary['run_id']}")
    print(f"  Provider: {summary['provider']}")
    print(f"  Model: {summary['model']}")
    print(f"  Dataset: {summary['dataset']}")
    print(f"  Samples: {summary['sample_count']}")
    print(f"  Overall Accuracy: {summary['overall_accuracy']:.2%}")
    print(f"  Success Rate (>=50%): {summary['success_rate']:.2%}")
    print(f"  Avg Latency: {summary['avg_latency']:.1f}s")
    print(f"  Total Cost: ${summary['total_cost']:.4f}")
    print(
        f"  Total Tokens: {summary['total_prompt_tokens'] + summary['total_completion_tokens']}"
    )
    print(f"    Input: {summary['total_prompt_tokens']}")
    print(f"    Output: {summary['total_completion_tokens']}")
    print("=" * 60)


async def list_benchmarks_cli():
    """List past benchmark runs."""
    runs = await crud.list_benchmark_runs()

    if not runs:
        print("No benchmark runs found.")
        print(
            "Run: uv run -m backend.cli run-benchmark --provider <name> --model <name>"
        )
        return

    headers = [
        "ID",
        "Dataset",
        "Provider",
        "Model",
        "Samples",
        "Accuracy",
        "Latency",
        "Cost",
        "Date",
    ]
    rows = []
    for run in runs:
        rows.append(
            [
                run["id"],
                run["dataset"],
                run["provider"],
                run["model"],
                run["sample_count"],
                f"{run['overall_accuracy']:.2%}"
                if run["overall_accuracy"] is not None
                else "N/A",
                f"{run['avg_latency']:.1f}s"
                if run["avg_latency"] is not None
                else "N/A",
                f"${run['total_cost']:.4f}" if run["total_cost"] is not None else "N/A",
                run["started_at"][:19] if run["started_at"] else "N/A",
            ]
        )

    print("\n" + tabulate(rows, headers=headers, tablefmt="grid"))
    print(f"\nTotal: {len(runs)} run(s)")


async def show_benchmark_cli(run_id: int):
    """Show detailed results for a benchmark run."""
    run = await crud.get_benchmark_run(run_id)
    if not run:
        print(f"✗ Error: Benchmark run {run_id} not found.")
        return

    results = await crud.get_benchmark_results(run_id)

    print("=" * 70)
    print(f"BENCHMARK RUN #{run_id}")
    print("=" * 70)
    print(f"  Dataset: {run['dataset']}")
    print(f"  Provider: {run['provider']}")
    print(f"  Model: {run['model']}")
    print(f"  Samples: {run['sample_count']}")
    print(
        f"  Overall Accuracy: {run['overall_accuracy']:.2%}"
        if run["overall_accuracy"] is not None
        else "  Overall Accuracy: N/A"
    )
    print(
        f"  Avg Latency: {run['avg_latency']:.1f}s"
        if run["avg_latency"] is not None
        else "  Avg Latency: N/A"
    )
    print(
        f"  Total Cost: ${run['total_cost']:.4f}"
        if run["total_cost"] is not None
        else "  Total Cost: N/A"
    )
    print(f"  Started: {run['started_at']}")
    print(f"  Completed: {run['completed_at']}")
    print("=" * 70)

    if results:
        print("\nPer-sample results:")
        headers = ["#", "Accuracy", "Latency", "Cost", "Tokens", "Status"]
        rows = []
        for r in results:
            status = (
                "OK"
                if not r.get("error_message")
                else f"ERR: {r['error_message'][:30]}"
            )
            tokens = f"{r.get('prompt_tokens', 0)}/{r.get('completion_tokens', 0)}"
            rows.append(
                [
                    r["sample_index"] + 1,
                    f"{r['accuracy_score']:.2%}"
                    if r["accuracy_score"] is not None
                    else "N/A",
                    f"{r['latency']:.1f}s" if r["latency"] is not None else "N/A",
                    f"${r['cost']:.4f}" if r["cost"] is not None else "N/A",
                    tokens,
                    status,
                ]
            )
        print(tabulate(rows, headers=headers, tablefmt="grid"))


async def export_benchmark_cli():
    """Export benchmark results to markdown."""
    import argparse

    from benchmarks.datasets import list_available_datasets

    available_datasets = list_available_datasets()

    parser = argparse.ArgumentParser(description="Export benchmark results to markdown")
    parser.add_argument(
        "--dataset",
        default="cord",
        choices=available_datasets,
        help=f"Dataset name (default: cord, available: {', '.join(available_datasets)})",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output file path (prints to stdout if not specified)",
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Generate detailed report with per-sample analysis",
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=10,
        help="Minimum sample count for inclusion (default: 10)",
    )
    args = parser.parse_args(sys.argv[2:])

    from benchmarks.exporter import export_benchmark_results, export_detailed_comparison

    print(f"Exporting benchmark results for dataset: {args.dataset}")

    if args.detailed:
        markdown = await export_detailed_comparison(
            dataset=args.dataset,
            output_path=args.output,
        )
    else:
        markdown = await export_benchmark_results(
            dataset=args.dataset,
            output_path=args.output,
            min_samples=args.min_samples,
        )

    if args.output:
        print(f"✓ Results exported to: {args.output}")
    else:
        print("\n" + markdown)


async def create_admin_user(username: str, password: str):
    """Create an admin user."""
    existing_user = await crud.get_user_by_username(username)
    if existing_user:
        print(f"✗ Error: User '{username}' already exists.")
        return False

    hashed = hash_password(password)
    user_id = await crud.create_user(username, hashed, is_admin=True)

    print("✓ Admin user created successfully!")
    print(f"  Username: {username}")
    print(f"  User ID: {user_id}")
    return True


async def create_demo_user(username: str, password: str):
    """Create a limited demo user with a daily OCR cap."""
    existing_user = await crud.get_user_by_username(username)
    if existing_user:
        print(f"✗ Error: User '{username}' already exists.")
        return False

    hashed = hash_password(password)
    user_id = await crud.create_user(username, hashed, is_admin=False, is_limited=True)

    print("✓ Demo user created successfully!")
    print(f"  Username: {username}")
    print(f"  Password: {password}")
    print(f"  User ID: {user_id}")
    print(f"  Limit: {_demo_limit_label()}")
    return True


async def create_demo_users(count: int = 5):
    """Create multiple demo users for testing."""
    import random
    import string

    created = []
    for i in range(1, count + 1):
        username = f"test{i}"
        # Generate random 6-char password
        password = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))

        hashed = hash_password(password)
        user_id = await crud.create_user(
            username, hashed, is_admin=False, is_limited=True
        )
        created.append((username, password, user_id))

    print(f"\n✓ Created {count} demo users:")
    print("-" * 40)
    for username, password, uid in created:
        print(f"  {username} / {password}")
    print("-" * 40)
    print(f"All users have: {_demo_limit_label()} limit")
    return True


async def list_all_users():
    """List all users."""
    users = await crud.list_users()

    if not users:
        print("No users found.")
        return True

    headers = ["ID", "Username", "Admin", "Limited", "Usage Today", "Created At"]
    rows = []
    for user in users:
        rows.append(
            [
                user["id"],
                user["username"],
                "✓" if user["is_admin"] else "✗",
                "✓" if user["is_limited"] else "✗",
                user["daily_requests"] or 0,
                user["created_at"],
            ]
        )

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
                (hashed, username),
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

    is_admin = is_admin_str.lower() in ("true", "1", "yes", "y")

    try:
        async with connect() as db:
            await db.execute(
                "UPDATE users SET is_admin = ? WHERE username = ?", (is_admin, username)
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
    print("  run-benchmark --provider <name> --model <name>  Run benchmark")
    print("  list-benchmarks                    List past benchmark runs")
    print("  show-benchmark <id>                Show detailed benchmark results")
    print("  export-benchmark --dataset <name>   Export results to markdown")
    print("\nExamples:")
    print("  uv run -m backend.cli create-admin admin1 securepass123")
    print("  uv run -m backend.cli create-demo testuser1 pass123")
    print("  uv run -m backend.cli create-demo-batch 10")
    print("  uv run -m backend.cli list-users")
    print("  uv run -m backend.cli change-password admin1 newpass456")
    print(
        "  uv run -m backend.cli run-benchmark --provider openrouter --model google/gemini-3-flash-preview"
    )
    print("  uv run -m backend.cli list-benchmarks")
    print("  uv run -m backend.cli show-benchmark 1")
    print(
        "  uv run -m backend.cli export-benchmark --dataset cord -o docs/reference/benchmark-results-cord.md"
    )


async def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    command = sys.argv[1]

    if command == "create-admin":
        if len(sys.argv) < 4:
            print("✗ Error: Username and password required.")
            print("Usage: uv run -m backend.cli create-admin <username> <password>")
            sys.exit(1)
        username = sys.argv[2]
        password = sys.argv[3]
        await create_admin_user(username, password)

    elif command == "list-users":
        await list_all_users()

    elif command == "delete-user":
        if len(sys.argv) < 3:
            print("✗ Error: Username required.")
            print("Usage: uv run -m backend.cli delete-user <username>")
            sys.exit(1)
        username = sys.argv[2]
        await delete_user(username)

    elif command == "change-password":
        if len(sys.argv) < 4:
            print("✗ Error: Username and new password required.")
            print(
                "Usage: uv run -m backend.cli change-password <username> <new_password>"
            )
            sys.exit(1)
        username = sys.argv[2]
        new_password = sys.argv[3]
        await change_password(username, new_password)

    elif command == "set-admin":
        if len(sys.argv) < 4:
            print("✗ Error: Username and status required.")
            print("Usage: uv run -m backend.cli set-admin <username> <true|false>")
            sys.exit(1)
        username = sys.argv[2]
        status = sys.argv[3]
        await set_admin_status(username, status)

    elif command == "create-demo":
        if len(sys.argv) < 4:
            print("✗ Error: Username and password required.")
            print("Usage: uv run -m backend.cli create-demo <username> <password>")
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
            print("Usage: uv run -m backend.cli set-limited <username> <true|false>")
            sys.exit(1)
        username = sys.argv[2]
        is_limited_str = sys.argv[3]
        is_limited = is_limited_str.lower() in ("true", "1", "yes", "y")

        user = await crud.get_user_by_username(username)
        if not user:
            print(f"✗ Error: User '{username}' not found.")
            sys.exit(1)

        async with connect() as db:
            await db.execute(
                "UPDATE users SET is_limited = ? WHERE username = ?",
                (is_limited, username),
            )
            await db.commit()

        status = "limited" if is_limited else "unlimited"
        print(f"✓ User '{username}' is now {status}.")

    elif command == "run-benchmark":
        await run_benchmark_cli()

    elif command == "list-benchmarks":
        await list_benchmarks_cli()

    elif command == "show-benchmark":
        if len(sys.argv) < 3:
            print("✗ Error: Benchmark run ID required.")
            print("Usage: uv run -m backend.cli show-benchmark <id>")
            sys.exit(1)
        try:
            run_id = int(sys.argv[2])
        except ValueError:
            print("✗ Error: Run ID must be a number.")
            sys.exit(1)
        await show_benchmark_cli(run_id)

    elif command == "export-benchmark":
        await export_benchmark_cli()

    else:
        print(f"✗ Error: Unknown command '{command}'")
        print_help()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
