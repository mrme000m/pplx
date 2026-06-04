#!/usr/bin/env python3
"""
Perplexity Account Backup Tool

Downloads and organizes all Perplexity account data into a local backup directory.

Usage:
    python scripts/backup_perplexity.py [backup_dir]

Default backup directory: ./backup/

What it backs up:
    - User profile, settings, credits balance
    - All memories (with categories)
    - All spaces (metadata, links, skills, files, threads)
    - All conversation threads (metadata + messages)
    - Workflows and tasks
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _client():
    import sys
    from pathlib import Path
    # Allow running from scripts/ directory
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from pplx import PerplexityClient
    return PerplexityClient()


def safe_json_dump(data, path):
    """Write JSON to path, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def backup_profile(client, backup_dir):
    """Back up user profile, settings, and credits."""
    print("  Profile...")
    safe_json_dump(client.get_profile(), backup_dir / "profile.json")

    print("  Settings...")
    safe_json_dump(client.get_user_settings(), backup_dir / "settings.json")

    print("  Credits...")
    safe_json_dump(client.get_credits_balance(), backup_dir / "credits.json")


def backup_memories(client, backup_dir):
    """Back up all user memories with pagination."""
    print("  Memories...")
    memories_dir = backup_dir / "memories"
    memories_dir.mkdir(parents=True, exist_ok=True)

    all_memories = []
    offset = 0
    limit = 100
    while True:
        page = client.list_memories(query="", limit=limit, offset=offset)
        items = page.get("memories", [])
        if not items:
            break
        all_memories.extend(items)
        offset += len(items)
        if len(items) < limit:
            break

    safe_json_dump(
        {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total": len(all_memories),
            "memories": all_memories,
            "categories": page.get("available_categories", []),
        },
        memories_dir / "memories.json",
    )
    print(f"    Saved {len(all_memories)} memories")


def backup_threads(client, backup_dir):
    """Back up all conversation threads with full messages."""
    print("  Threads...")
    threads_dir = backup_dir / "threads"
    threads_dir.mkdir(parents=True, exist_ok=True)

    all_threads = []
    offset = 0
    limit = 100
    while True:
        page = client.list_threads(limit=limit, offset=offset)
        items = page if isinstance(page, list) else page.get("threads", [])
        if not items:
            break
        all_threads.extend(items)
        offset += len(items)
        if len(items) < limit:
            break

    # Save thread index
    safe_json_dump(
        {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total": len(all_threads),
            "threads": all_threads,
        },
        threads_dir / "index.json",
    )

    # Download full thread details for each
    for i, t in enumerate(all_threads, 1):
        slug = t.get("slug")
        if not slug:
            continue
        try:
            detail = client.get_thread(slug)
            safe_json_dump(detail, threads_dir / f"{slug}.json")
        except Exception as e:
            print(f"    Warning: failed to download thread {slug}: {e}")
        if i % 10 == 0:
            print(f"    Downloaded {i}/{len(all_threads)} threads...")

    print(f"    Saved {len(all_threads)} threads")


def backup_spaces(client, backup_dir):
    """Back up all spaces with metadata, links, skills, files, and threads."""
    print("  Spaces...")
    spaces_dir = backup_dir / "spaces"
    spaces_dir.mkdir(parents=True, exist_ok=True)

    all_spaces = []
    offset = 0
    limit = 100
    while True:
        page = client.list_spaces(limit=limit, offset=offset)
        items = page if isinstance(page, list) else page.get("spaces", [])
        if not items:
            break
        all_spaces.extend(items)
        offset += len(items)
        if len(items) < limit:
            break

    # Save space index
    safe_json_dump(
        {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total": len(all_spaces),
            "spaces": all_spaces,
        },
        spaces_dir / "index.json",
    )

    # Download per-space details
    for s in all_spaces:
        slug = s.get("slug", s.get("uuid", "unknown"))
        space_dir = spaces_dir / slug
        space_dir.mkdir(parents=True, exist_ok=True)

        # Metadata
        safe_json_dump(s, space_dir / "metadata.json")

        # Links (focused web URLs)
        try:
            links = client.list_space_links(slug)
            safe_json_dump(links, space_dir / "links.json")
        except Exception as e:
            print(f"    Warning: failed links for {slug}: {e}")

        # Skills
        try:
            uuid = s.get("uuid")
            if uuid:
                skills = client.list_space_skills(uuid)
                safe_json_dump(skills, space_dir / "skills.json")
        except Exception as e:
            print(f"    Warning: failed skills for {slug}: {e}")

        # Files
        try:
            uuid = s.get("uuid")
            if uuid:
                files = client.list_space_files(uuid)
                safe_json_dump(files, space_dir / "files.json")
        except Exception as e:
            print(f"    Warning: failed files for {slug}: {e}")

        # Threads in space
        try:
            space_threads = client.list_space_threads(slug)
            safe_json_dump(space_threads, space_dir / "threads.json")
        except Exception as e:
            print(f"    Warning: failed threads for {slug}: {e}")

    print(f"    Saved {len(all_spaces)} spaces")


def backup_workflows(client, backup_dir):
    """Back up available workflows."""
    print("  Workflows...")
    try:
        workflows = client.list_workflows()
        safe_json_dump(workflows, backup_dir / "workflows" / "workflows.json")
        categories = workflows.get("ranked_categories", [])
        print(f"    Saved {len(categories)} categories, {len(workflows.get('workflows', []))} workflows")
    except Exception as e:
        print(f"    Warning: failed workflows: {e}")


def backup_tasks(client, backup_dir):
    """Back up computer tasks (ASI workflows)."""
    print("  Tasks...")
    try:
        tasks = client.list_tasks()
        safe_json_dump(tasks, backup_dir / "tasks" / "tasks.json")
        count = len(tasks.get("tasks", []))
        print(f"    Saved {count} tasks")
    except Exception as e:
        print(f"    Warning: failed tasks: {e}")


def main():
    backup_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("backup")
    backup_dir = backup_dir.resolve()
    backup_dir.mkdir(parents=True, exist_ok=True)

    print(f"Perplexity Account Backup")
    print(f"Target: {backup_dir}")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print()

    client = _client()

    print("Backing up account data...")
    backup_profile(client, backup_dir)
    backup_memories(client, backup_dir)
    backup_threads(client, backup_dir)
    backup_spaces(client, backup_dir)
    backup_workflows(client, backup_dir)
    backup_tasks(client, backup_dir)

    # Write manifest
    manifest = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "backup_dir": str(backup_dir),
        "contents": {
            "profile.json": "User profile",
            "settings.json": "Account settings and limits",
            "credits.json": "Credits balance and billing",
            "memories/": "All user memories with categories",
            "threads/": "All conversation threads with messages",
            "spaces/": "All spaces with metadata, links, skills, files, threads",
            "workflows/": "Available workflow templates",
            "tasks/": "Computer tasks (ASI workflows)",
        },
    }
    safe_json_dump(manifest, backup_dir / "manifest.json")

    print()
    print(f"Done: {datetime.now(timezone.utc).isoformat()}")
    print(f"Backup saved to: {backup_dir}")


if __name__ == "__main__":
    main()
