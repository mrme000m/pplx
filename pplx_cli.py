#!/usr/bin/env python3
"""
PPLX CLI — Command-line interface for Perplexity AI.

Loads cookies securely from Bitwarden vault. No disk files needed.
Dynamically discovers available models from Perplexity API.

Usage:
    pplx search "What is rust?"
    pplx search "Quantum mechanics" --mode pro --model "GPT-5.4" --thinking
    pplx search "Research AGI" --mode deep_research
    pplx models                    # List available models
    pplx threads list
    pplx spaces list
"""

import argparse
import json
import sys
from pathlib import Path

__version__ = "0.1.0"


def _client():
    from pplx import PerplexityClient
    return PerplexityClient()


def _extract_answer(raw):
    """Extract readable answer from raw SSE response."""
    if not raw or not isinstance(raw, dict):
        return {"answer": None, "backend_uuid": None}

    text_obj = raw.get("text", {})
    if isinstance(text_obj, str):
        try:
            text_obj = json.loads(text_obj)
        except json.JSONDecodeError:
            text_obj = None

    answer = None
    if isinstance(text_obj, list):
        # Streaming format: list of step objects
        for step in text_obj:
            if not isinstance(step, dict):
                continue
            step_type = step.get("step_type", "")
            content = step.get("content", {})
            if step_type == "FINAL" and isinstance(content, dict):
                # The answer is JSON-encoded inside content.answer
                answer_json = content.get("answer", "")
                if isinstance(answer_json, str):
                    try:
                        parsed = json.loads(answer_json)
                        if isinstance(parsed, dict):
                            answer = parsed.get("answer")
                    except json.JSONDecodeError:
                        answer = answer_json
                elif isinstance(answer_json, dict):
                    answer = answer_json.get("answer")
            elif step_type == "SEARCH_RESULTS" and isinstance(content, dict) and not answer:
                results = content.get("web_results", [])
                if results and isinstance(results, list):
                    snippets = [r.get("snippet", "") for r in results if r.get("snippet")]
                    if snippets:
                        answer = "\n\n".join(snippets)
    elif isinstance(text_obj, dict):
        answer = text_obj.get("answer")

    return {
        "answer": answer,
        "backend_uuid": raw.get("backend_uuid"),
    }


def _print_json(result):
    """Print result as pretty JSON to stdout."""
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    print()


def _print_search_result(result, args):
    """Shared output logic for search and follow-up commands."""
    data = _extract_answer(result)
    if args.raw:
        _print_json(result)
    else:
        print(data["answer"] or "(No answer)")
        if data.get("backend_uuid") and args.verbose:
            print(f"\n[backend_uuid: {data['backend_uuid']}]")


# ---------------------------------------------------------------------------
# Command helpers — eliminate repetitive boilerplate
# ---------------------------------------------------------------------------

def _json_cmd(func):
    """Wrap a simple command: create client, call func(client, args), print JSON."""
    def wrapper(args):
        client = _client()
        result = func(client, args)
        _print_json(result)
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def _confirm_delete(resource_name, attr="uuid"):
    """Decorator for delete commands requiring confirmation."""
    def decorator(func):
        def wrapper(args):
            if not args.force:
                target = getattr(args, attr)
                ok = input(f"Delete {resource_name} {target}? [y/N] ")
                if ok.lower() not in ("y", "yes"):
                    print("Cancelled.")
                    return
            return func(args)
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator


def _raw_cmd(func):
    """Wrap a command with raw/formatted dual output."""
    def wrapper(args):
        client = _client()
        result = func(client, args)
        if args.raw:
            _print_json(result)
        else:
            return result
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def cmd_refresh_cookies(args):
    """Run the deterministic cookie refresh pipeline."""
    import subprocess
    import sys
    from pathlib import Path

    script = Path(__file__).resolve().parent / "scripts" / "refresh_cookies.py"
    if not script.exists():
        print(f"Error: refresh script not found: {script}", file=sys.stderr)
        sys.exit(1)

    cmd = [sys.executable, str(script)]
    if args.headless:
        cmd.append("--headless")

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def cmd_validate(args):
    """Check if the current Perplexity session is valid."""
    client = _client()
    result = client.validate_session()
    _print_json(result)
    sys.exit(0 if result.get("valid") else 1)


def cmd_search(args):
    client = _client()
    result = client.search(
        query=" ".join(args.query),
        mode=args.mode.replace("_", " "),
        model=args.model,
        thinking=args.thinking,
        sources=args.sources.split(",") if args.sources else ["web"],
        language=args.language,
        incognito=args.incognito,
    )
    _print_search_result(result, args)


def cmd_follow_up(args):
    client = _client()
    result = client.search(
        query=" ".join(args.query),
        mode=args.mode.replace("_", " "),
        model=args.model,
        thinking=args.thinking,
        follow_up={"backend_uuid": args.backend_uuid},
        language=args.language,
    )
    _print_search_result(result, args)


def cmd_models(args):
    """List dynamically discovered models."""
    client = _client()
    models = client.list_models()
    
    if args.raw:
        _print_json(models)
        return
    
    print("Available Models\n")
    print("=" * 50)
    
    for mode, model_list in models.items():
        if not model_list:
            continue
        print(f"\n{mode.upper()}:")
        print("-" * 30)
        for m in model_list:
            if m is None:
                print("  Default (auto-selected)")
            else:
                print(f"  • {m}")
    
    # Show model data if available
    if client._models_data and args.verbose:
        print("\n" + "=" * 50)
        print("MODEL DETAILS:")
        print("-" * 30)
        for key, info in client._models_data.get("models", {}).items():
            print(f"  {key}: {info.get('label')} [{info.get('provider')}] - {info.get('description')}")


@_json_cmd
def cmd_threads_list(client, args):
    return client.list_threads( limit=args.limit, offset=args.offset, search_term=args.search or "", ascending=args.ascending, )

@_json_cmd
def cmd_threads_recent(client, args):
    return client.list_recent_threads(exclude_asi=args.exclude_asi)

@_json_cmd
def cmd_threads_pinned(client, args):
    return client.list_pinned_threads()

@_json_cmd
def cmd_threads_get(client, args):
    return client.get_thread(args.slug)

@_confirm_delete("thread(s)", "context_uuids")
@_json_cmd
def cmd_threads_delete(client, args):
    uuids = args.context_uuids.split(",")
    return client.delete_threads(context_uuids=uuids)

@_json_cmd
def cmd_threads_rename(client, args):
    return client.rename_thread( context_uuid=args.context_uuid, title=args.title, )

@_json_cmd
def cmd_spaces_list(client, args):
    return client.list_spaces(limit=args.limit)

def cmd_spaces_get(args):
    client = _client()
    try:
        result = client.get_space(args.slug)
        _print_json(result)
    except Exception as e:
        msg = str(e)
        # Provide clearer error message for slug vs UUID confusion
        if "VIEW_COLLECTION_NOT_ALLOWED" in msg or "403" in msg or "404" in msg:
            print(f"Error: '{args.slug}' not found or access denied.", file=sys.stderr)
            print("\nTip: Space slugs must be the full unique identifier, not a partial name.", file=sys.stderr)
            print("      Use 'pplx spaces list' to see all spaces and their full slugs.", file=sys.stderr)
            sys.exit(1)
        raise


@_json_cmd
def cmd_spaces_create(client, args):
    return client.create_space( title=args.title, description=args.description, emoji=args.emoji, instructions=args.instructions, access=args.access, )

@_confirm_delete("space", "uuid")
@_json_cmd
def cmd_spaces_delete(client, args):
    return client.delete_space(args.uuid)

@_json_cmd
def cmd_spaces_edit(client, args):
    kwargs = {"uuid": args.uuid}
    if args.title is not None:
        kwargs["title"] = args.title
    if args.description is not None:
        kwargs["description"] = args.description
    if args.emoji is not None:
        kwargs["emoji"] = args.emoji
    if args.instructions is not None:
        kwargs["instructions"] = args.instructions
    if args.access is not None:
        kwargs["access"] = args.access
    if args.enable_web is not None:
        kwargs["enable_web_by_default"] = args.enable_web
    return client.edit_space(**kwargs)

@_json_cmd
def cmd_spaces_threads(client, args):
    return client.list_space_threads( slug=args.slug, limit=args.limit, offset=args.offset, )

@_json_cmd
def cmd_spaces_articles(client, args):
    return client.list_space_articles( slug=args.slug, limit=args.limit, offset=args.offset, )

@_json_cmd
def cmd_spaces_tasks(client, args):
    return client.get_space_tasks(args.uuid)

@_json_cmd
def cmd_spaces_files(client, args):
    return client.list_space_files( uuid=args.uuid, search_keyword=args.search or "", page_size=args.page_size, cursor=args.cursor, )

@_json_cmd
def cmd_spaces_upload(client, args):
    content = args.file.read_bytes()
    return client.upload_file_to_space(
        uuid=args.uuid,
        filename=args.file.name,
        file_content=content,
    )

@_json_cmd
def cmd_spaces_delete_files(client, args):
    uuids = args.file_uuids.split(",")
    return client.delete_space_files(args.uuid, uuids)

@_json_cmd
def cmd_spaces_upload_status(client, args):
    return client.get_upload_status(args.uuid)

@_json_cmd
def cmd_spaces_links(client, args):
    return client.list_space_links(slug=args.slug)

@_json_cmd
def cmd_spaces_links_add(client, args):
    return client.add_space_link(uuid=args.uuid, link=args.link)

@_json_cmd
def cmd_spaces_links_remove(client, args):
    return client.remove_space_link(uuid=args.uuid, link=args.link)

@_json_cmd
def cmd_spaces_add_thread(client, args):
    return client.upsert_thread_collection( context_uuid=args.context_uuid, new_collection_uuid=args.uuid, return_collection=args.return_collection, return_thread=args.return_thread, )

@_json_cmd
def cmd_spaces_landing(client, args):
    return client.list_spaces_v2( limit=args.limit, cursor=args.cursor, sections=args.sections, )

@_json_cmd
def cmd_spaces_pins(client, args):
    return client.list_user_pins()

@_json_cmd
def cmd_discover(client, args):
    return client.get_discover_feed(limit=args.limit, category=args.category)

@_json_cmd
def cmd_profile(client, args):
    return client.get_profile()

@_json_cmd
def cmd_credits(client, args):
    return client.get_credits_balance()

@_json_cmd
def cmd_spaces_recent(client, args):
    return client.list_recent_spaces()

@_json_cmd
def cmd_spaces_skills_add(client, args):
    content = args.file.read_bytes()
    return client.upload_skill_to_space(
        uuid=args.uuid,
        filename=args.file.name,
        file_content=content,
    )

@_json_cmd
def cmd_spaces_skills_list(client, args):
    return client.list_space_skills(uuid=args.uuid, limit=args.limit)

@_json_cmd
def cmd_spaces_skills_get(client, args):
    return client.get_skill(skill_id=args.skill_id)

@_confirm_delete("skill", "skill_id")
@_json_cmd
def cmd_spaces_skills_delete(client, args):
    return client.delete_skill(skill_id=args.skill_id)

@_json_cmd
def cmd_assets_list(client, args):
    return client.list_assets(limit=args.limit, collapse_versions=not args.versions)

@_json_cmd
def cmd_assets_pins(client, args):
    return client.list_pinned_assets(limit=args.limit)

@_json_cmd
def cmd_assets_shared(client, args):
    return client.list_shared_assets(limit=args.limit)

@_json_cmd
def cmd_assets_pin(client, args):
    return client.pin_asset(asset_id=args.asset_id)

@_json_cmd
def cmd_assets_unpin(client, args):
    return client.unpin_asset(asset_id=args.asset_id)

@_confirm_delete("asset", "asset_id")
@_json_cmd
def cmd_assets_delete(client, args):
    return client.delete_asset(asset_id=args.asset_id)

@_json_cmd
def cmd_assets_download(client, args):
    return client.download_asset(url=args.url, filename=args.filename)

@_json_cmd
def cmd_settings(client, args):
    return client.get_user_settings()

@_json_cmd
def cmd_spaces_writable(client, args):
    return client.list_writable_spaces()

@_json_cmd
def cmd_sources(client, args):
    return client.list_sources()

@_json_cmd
def cmd_sources_discover(client, args):
    return client.discover_sources()

@_json_cmd
def cmd_billing(client, args):
    return client.get_billing_info()

@_json_cmd
def cmd_tasks_list(client, args):
    return client.list_scheduled_tasks()

@_json_cmd
def cmd_tasks_create(client, args):
    return client.create_scheduled_task( task_name=args.name, prompt=" ".join(args.prompt), schedule={ "start_at": args.start_at, "rrule": args.rrule, "tzid": args.tzid, }, sources=args.sources.split(",") if args.sources else None, model_preference=args.model, )

@_confirm_delete("task", "task_id")
@_json_cmd
def cmd_tasks_delete(client, args):
    return client.delete_scheduled_task(task_id=args.task_id)

@_json_cmd
def cmd_finance_alert(client, args):
    return client.create_finance_alert( task_name=args.name, prompt=args.prompt, ticker=args.ticker, event_type=args.event_type, value_upper_bound=args.threshold, model_preference=args.model, )

@_json_cmd
def cmd_finance_quote(client, args):
    return client.get_finance_quote(symbol=args.symbol)

def cmd_spaces_search(args):
    client = _client()
    result = client.search_in_space(
        uuid=args.uuid,
        query=" ".join(args.query),
        mode=args.mode.replace("_", " "),
        model=args.model,
    )
    data = _extract_answer(result)
    if args.raw:
        _print_json(result)
    else:
        print(data["answer"] or "(No answer)")
        if data.get("backend_uuid") and args.verbose:
            print(f"\n[backend_uuid: {data['backend_uuid']}]")


@_json_cmd
def cmd_memories_list(client, args):
    return client.list_memories(query=args.search or "", limit=args.limit, offset=args.offset)

@_json_cmd
def cmd_memories_get(client, args):
    return client.get_memory(memory_key=args.key)

@_confirm_delete("memory", "key")
@_json_cmd
def cmd_memories_delete(client, args):
    return client.delete_memory(memory_key=args.key)

@_json_cmd
def cmd_tasks(client, args):
    return client.list_computer_tasks(limit=args.limit, offset=args.offset)

@_json_cmd
def cmd_workflows(client, args):
    return client.list_workflows()

@_json_cmd
def cmd_threads_share(client, args):
    return client.share_thread(slug=args.slug)

def cmd_rate_limits(args):
    client = _client()
    result = client.get_rate_limit_status()
    if args.raw:
        _print_json(result)
    else:
        # Handle new API response structure with "remaining_detail" and "modes"
        for key, info in result.items():
            if not isinstance(info, dict):
                continue
            
            # Try old format first (backward compatibility)
            if "remaining" in info:
                remaining = info.get("remaining", "?")
                limit = info.get("limit", "?")
                reset_at = info.get("reset_time", "?")
                print(f"  {key}: {remaining}/{limit} (resets {reset_at})")
            else:
                # New format with remaining_detail
                available = info.get("available", False)
                remaining_detail = info.get("remaining_detail", {})
                kind = remaining_detail.get("kind", "not_provided")
                
                if kind == "exact":
                    remaining = remaining_detail.get("remaining", "?")
                    limit = remaining_detail.get("limit", "?")
                    print(f"  {key}: {remaining}/{limit} (available: {available})")
                elif kind == "not_provided":
                    print(f"  {key}: Not provided (available: {available})")
                else:
                    print(f"  {key}: ?/? (available: {available})")


def cmd_notifications(args):
    client = _client()
    result = client.get_notification_count()
    if args.raw:
        _print_json(result)
    else:
        print(f"Unread notifications: {result.get('count', result)}")


def cmd_ai_profile(args):
    client = _client()
    result = client.get_ai_profile()
    if args.raw:
        _print_json(result)
    else:
        profile = result.get("profile", result)
        for key, val in profile.items():
            print(f"  {key}: {val}")


def cmd_status(args):
    client = _client()
    results = {}
    sections = args.sections.split(",") if args.sections else ["all"]

    if "all" in sections or "user" in sections:
        results["user_info"] = client.get_user_info()
    if "all" in sections or "rate" in sections:
        results["rate_limits"] = client.get_rate_limit_status()
    if "all" in sections or "asi" in sections:
        results["asi_access"] = client.get_asi_access()
    if "all" in sections or "notif" in sections:
        results["notifications"] = client.get_notification_count()

    if args.raw:
        _print_json(results)
    else:
        if "user_info" in results:
            u = results["user_info"]
            print("User Info:")
            print(f"  Enterprise: {u.get('is_enterprise')}, Student: {u.get('is_student')}")
            print(f"  Home host: {u.get('home_host', '?')}")
        if "rate_limits" in results:
            print("\nRate Limits:")
            for key, info in results["rate_limits"].items():
                if isinstance(info, dict):
                    # Try old format first (backward compatibility)
                    if "remaining" in info:
                        remaining = info.get("remaining", "?")
                        limit = info.get("limit", "?")
                        print(f"  {key}: {remaining}/{limit}")
                    else:
                        # New format with remaining_detail
                        available = info.get("available", False)
                        remaining_detail = info.get("remaining_detail", {})
                        kind = remaining_detail.get("kind", "not_provided")
                        
                        if kind == "exact":
                            remaining = remaining_detail.get("remaining", "?")
                            limit = remaining_detail.get("limit", "?")
                            print(f"  {key}: {remaining}/{limit} (available: {available})")
                        else:
                            print(f"  {key}: Not provided (available: {available})")
        if "asi_access" in results:
            a = results["asi_access"]
            print(f"\nASI Access: {a.get('has_access', a)}")
        if "notifications" in results:
            n = results["notifications"]
            print(f"\nUnread notifications: {n.get('count', n)}")


@_json_cmd
def cmd_spaces_pinned_threads(client, args):
    return client.get_space_pinned_threads(space_id=args.uuid, include_assets=not args.no_assets)

@_json_cmd
def cmd_spaces_memory_config(client, args):
    return client.get_space_memory_config(space_id=args.uuid)

@_json_cmd
def cmd_tasks_recurring(client, args):
    return client.list_recurring_tasks()

def build_parser():
    p = argparse.ArgumentParser(
        prog="pplx",
        description="PPLX — Perplexity AI CLI (Bitwarden-backed, dynamic models)",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command")

    # Shared search arguments
    search_parent = argparse.ArgumentParser(add_help=False)
    search_parent.add_argument(
        "--mode", default="auto",
        choices=["auto", "pro", "reasoning", "deep_research"],
        help="Search mode (default: auto)",
    )
    search_parent.add_argument(
        "--model", default=None,
        help="Model name (use 'pplx models' to see options)",
    )
    search_parent.add_argument(
        "--thinking", action="store_true",
        help="Enable thinking mode (uses reasoning variant of selected model)",
    )
    search_parent.add_argument("--language", default="en-US", help="Language code (ISO 639, e.g. en-US)")
    search_parent.add_argument("--raw", action="store_true", help="Output full raw JSON")
    search_parent.add_argument("-v", "--verbose", action="store_true")

    # search
    s = sub.add_parser("search", parents=[search_parent], help="Search the web")
    s.add_argument("query", nargs="+", help="Search query")
    s.add_argument("--sources", default="web", help="Sources: web,scholar,social")
    s.add_argument("--incognito", action="store_true")
    s.set_defaults(func=cmd_search)

    # follow-up
    f = sub.add_parser("follow-up", parents=[search_parent], help="Continue a conversation")
    f.add_argument("query", nargs="+")
    f.add_argument("backend_uuid", help="Thread UUID from previous search")
    f.set_defaults(func=cmd_follow_up)

    # models
    m = sub.add_parser("models", help="List available models (dynamically fetched)")
    m.add_argument("--raw", action="store_true", help="Output raw model data")
    m.add_argument("-v", "--verbose", action="store_true", help="Show full model details")
    m.set_defaults(func=cmd_models)

    # threads
    thr = sub.add_parser("threads", help="Manage conversation threads / history")
    thr_sub = thr.add_subparsers(dest="subcommand")
    
    thr_list = thr_sub.add_parser("list", help="List threads from history")
    thr_list.add_argument("-l", "--limit", type=int, default=20)
    thr_list.add_argument("-o", "--offset", type=int, default=0)
    thr_list.add_argument("-s", "--search", default="", help="Search term filter")
    thr_list.add_argument("--ascending", action="store_true", help="Oldest first")
    thr_list.set_defaults(func=cmd_threads_list)
    
    thr_recent = thr_sub.add_parser("recent", help="List recent threads")
    thr_recent.add_argument("--exclude-asi", action="store_true", help="Exclude ASI threads")
    thr_recent.set_defaults(func=cmd_threads_recent)
    
    thr_pinned = thr_sub.add_parser("pinned", help="List pinned threads")
    thr_pinned.set_defaults(func=cmd_threads_pinned)
    
    thr_get = thr_sub.add_parser("get", help="Get thread details by slug")
    thr_get.add_argument("slug")
    thr_get.set_defaults(func=cmd_threads_get)
    
    thr_delete = thr_sub.add_parser("delete", help="Delete thread(s) from history")
    thr_delete.add_argument("context_uuids", help="Comma-separated context_uuids")
    thr_delete.add_argument("--force", action="store_true", help="Skip confirmation")
    thr_delete.set_defaults(func=cmd_threads_delete)
    
    thr_rename = thr_sub.add_parser("rename", help="Rename a thread")
    thr_rename.add_argument("context_uuid", help="Thread context_uuid")
    thr_rename.add_argument("title", help="New title")
    thr_rename.set_defaults(func=cmd_threads_rename)

    thr_share = thr_sub.add_parser("share", help="Get share link for a thread")
    thr_share.add_argument("slug", help="Thread slug")
    thr_share.set_defaults(func=cmd_threads_share)

    # spaces
    sp = sub.add_parser("spaces", help="Manage spaces")
    sp_sub = sp.add_subparsers(dest="subcommand")

    sp_list = sp_sub.add_parser("list", help="List spaces (legacy)")
    sp_list.add_argument("-l", "--limit", type=int, default=30)
    sp_list.set_defaults(func=cmd_spaces_list)

    sp_landing = sp_sub.add_parser("landing", help="List spaces v2 (sectioned)")
    sp_landing.add_argument("-l", "--limit", type=int, default=30)
    sp_landing.add_argument("--cursor", default=None)
    sp_landing.add_argument("--sections", default=None)
    sp_landing.set_defaults(func=cmd_spaces_landing)

    sp_pins = sp_sub.add_parser("pins", help="List pinned spaces")
    sp_pins.set_defaults(func=cmd_spaces_pins)

    sp_recent = sp_sub.add_parser("recent", help="List recently accessed spaces")
    sp_recent.set_defaults(func=cmd_spaces_recent)

    sp_writable = sp_sub.add_parser("writable", help="List spaces you can write to")
    sp_writable.set_defaults(func=cmd_spaces_writable)

    sp_pinned_thr = sp_sub.add_parser("pinned-threads", help="List pinned threads in a space")
    sp_pinned_thr.add_argument("uuid", help="Space UUID")
    sp_pinned_thr.add_argument("--no-assets", action="store_true", help="Exclude asset info")
    sp_pinned_thr.set_defaults(func=cmd_spaces_pinned_threads)

    sp_mem_cfg = sp_sub.add_parser("memory-config", help="Get memory config for a space")
    sp_mem_cfg.add_argument("uuid", help="Space UUID")
    sp_mem_cfg.set_defaults(func=cmd_spaces_memory_config)

    sp_get = sp_sub.add_parser("get", help="Get space by slug")
    sp_get.add_argument("slug", help="Space slug (full unique identifier)")
    sp_get.set_defaults(func=cmd_spaces_get)

    sp_create = sp_sub.add_parser("create", help="Create a space")
    sp_create.add_argument("--title", required=True, help="Space title")
    sp_create.add_argument("--description", default="", help="Space description")
    sp_create.add_argument("--emoji", default="1f4c1", help="Emoji unicode code-point (default: 1f4c1)")
    sp_create.add_argument("--instructions", default="", help="System instructions for the Space")
    sp_create.add_argument("--access", type=int, default=1, choices=[1, 2], help="Access: 1=private, 2=public")
    sp_create.set_defaults(func=cmd_spaces_create)

    sp_edit = sp_sub.add_parser("edit", help="Edit a space")
    sp_edit.add_argument("uuid")
    sp_edit.add_argument("--title", default=None, help="New title (omit to keep current)")
    sp_edit.add_argument("--description", default=None, help="New description (omit to keep current)")
    sp_edit.add_argument("--emoji", default=None, help="New emoji unicode (omit to keep current)")
    sp_edit.add_argument("--instructions", default=None, help="New instructions (omit to keep current)")
    sp_edit.add_argument("--access", type=int, default=None, choices=[1, 2], help="Access level: 1=private, 2=public (omit to keep current)")
    sp_edit.add_argument("--enable-web", dest="enable_web", action="store_true", default=None, help="Enable web search by default")
    sp_edit.add_argument("--disable-web", dest="enable_web", action="store_false", default=None, help="Disable web search by default")
    sp_edit.set_defaults(func=cmd_spaces_edit)

    sp_del = sp_sub.add_parser("delete", help="Delete a space")
    sp_del.add_argument("uuid")
    sp_del.add_argument("--force", action="store_true")
    sp_del.set_defaults(func=cmd_spaces_delete)

    sp_threads = sp_sub.add_parser("threads", help="List threads in a space")
    sp_threads.add_argument("slug")
    sp_threads.add_argument("-l", "--limit", type=int, default=20)
    sp_threads.add_argument("-o", "--offset", type=int, default=0)
    sp_threads.set_defaults(func=cmd_spaces_threads)

    sp_articles = sp_sub.add_parser("articles", help="List articles in a space")
    sp_articles.add_argument("slug")
    sp_articles.add_argument("-l", "--limit", type=int, default=20)
    sp_articles.add_argument("-o", "--offset", type=int, default=0)
    sp_articles.set_defaults(func=cmd_spaces_articles)

    sp_tasks = sp_sub.add_parser("tasks", help="Get tasks in a space")
    sp_tasks.add_argument("uuid")
    sp_tasks.set_defaults(func=cmd_spaces_tasks)

    sp_files = sp_sub.add_parser("files", help="List files in a space")
    sp_files.add_argument("uuid")
    sp_files.add_argument("-s", "--search", default="")
    sp_files.add_argument("--page-size", type=int, default=20)
    sp_files.add_argument("--cursor", default=None)
    sp_files.set_defaults(func=cmd_spaces_files)

    sp_upload = sp_sub.add_parser("upload", help="Upload a file to a space")
    sp_upload.add_argument("uuid")
    sp_upload.add_argument("file", type=Path)
    sp_upload.set_defaults(func=cmd_spaces_upload)

    sp_del_files = sp_sub.add_parser("delete-files", help="Delete files from a space")
    sp_del_files.add_argument("uuid")
    sp_del_files.add_argument("file_uuids", help="Comma-separated file UUIDs")
    sp_del_files.set_defaults(func=cmd_spaces_delete_files)

    sp_up_status = sp_sub.add_parser("upload-status", help="Get upload status for a space")
    sp_up_status.add_argument("uuid")
    sp_up_status.set_defaults(func=cmd_spaces_upload_status)

    sp_add_thr = sp_sub.add_parser("add-thread", help="Add a thread to a space")
    sp_add_thr.add_argument("uuid", help="Space collection UUID")
    sp_add_thr.add_argument("context_uuid", help="Thread context UUID")
    sp_add_thr.add_argument("--return-collection", action="store_true")
    sp_add_thr.add_argument("--return-thread", action="store_true")
    sp_add_thr.set_defaults(func=cmd_spaces_add_thread)

    sp_search = sp_sub.add_parser("search", parents=[search_parent], help="Search within a space")
    sp_search.add_argument("uuid", help="Space collection UUID")
    sp_search.add_argument("query", nargs="+", help="Search query")
    sp_search.set_defaults(func=cmd_spaces_search)

    sp_links = sp_sub.add_parser("links", help="Manage focused web links for a space")
    sp_links_sub = sp_links.add_subparsers(dest="subcommand")

    sp_links_list = sp_links_sub.add_parser("list", help="List focused web links")
    sp_links_list.add_argument("slug", help="Space slug")
    sp_links_list.set_defaults(func=cmd_spaces_links)

    sp_links_add = sp_links_sub.add_parser("add", help="Add a focused web link")
    sp_links_add.add_argument("uuid", help="Space collection UUID")
    sp_links_add.add_argument("link", help="Domain to focus (e.g. docs.python.org)")
    sp_links_add.set_defaults(func=cmd_spaces_links_add)

    sp_links_rm = sp_links_sub.add_parser("remove", help="Remove a focused web link")
    sp_links_rm.add_argument("uuid", help="Space collection UUID")
    sp_links_rm.add_argument("link", help="Domain to remove")
    sp_links_rm.set_defaults(func=cmd_spaces_links_remove)

    sp_skills = sp_sub.add_parser("skills", help="Manage custom skills for a space")
    sp_skills_sub = sp_skills.add_subparsers(dest="subcommand")

    sp_skills_list = sp_skills_sub.add_parser("list", help="List skills in a space")
    sp_skills_list.add_argument("uuid", help="Space collection UUID")
    sp_skills_list.add_argument("-l", "--limit", type=int, default=20)
    sp_skills_list.set_defaults(func=cmd_spaces_skills_list)

    sp_skills_add = sp_skills_sub.add_parser("add", help="Upload a skill to a space")
    sp_skills_add.add_argument("uuid", help="Space collection UUID")
    sp_skills_add.add_argument("file", type=Path, help="Skill markdown file")
    sp_skills_add.set_defaults(func=cmd_spaces_skills_add)

    sp_skills_get = sp_skills_sub.add_parser("get", help="Get a skill by ID")
    sp_skills_get.add_argument("skill_id", help="Skill UUID")
    sp_skills_get.set_defaults(func=cmd_spaces_skills_get)

    sp_skills_del = sp_skills_sub.add_parser("delete", help="Delete a skill")
    sp_skills_del.add_argument("skill_id", help="Skill UUID")
    sp_skills_del.add_argument("--force", action="store_true", help="Skip confirmation")
    sp_skills_del.set_defaults(func=cmd_spaces_skills_delete)

    # assets
    ast = sub.add_parser("assets", help="Manage generated assets (reports, images, code)")
    ast_sub = ast.add_subparsers(dest="subcommand")

    ast_list = ast_sub.add_parser("list", help="List all assets")
    ast_list.add_argument("-l", "--limit", type=int, default=40)
    ast_list.add_argument("--versions", action="store_true", help="Show all versions")
    ast_list.set_defaults(func=cmd_assets_list)

    ast_pins = ast_sub.add_parser("pins", help="List pinned assets")
    ast_pins.add_argument("-l", "--limit", type=int, default=50)
    ast_pins.set_defaults(func=cmd_assets_pins)

    ast_shared = ast_sub.add_parser("shared", help="List assets shared with you")
    ast_shared.add_argument("-l", "--limit", type=int, default=40)
    ast_shared.set_defaults(func=cmd_assets_shared)

    ast_pin = ast_sub.add_parser("pin", help="Pin an asset")
    ast_pin.add_argument("asset_id", help="Asset UUID")
    ast_pin.set_defaults(func=cmd_assets_pin)

    ast_unpin = ast_sub.add_parser("unpin", help="Unpin an asset")
    ast_unpin.add_argument("asset_id", help="Asset UUID")
    ast_unpin.set_defaults(func=cmd_assets_unpin)

    ast_del = ast_sub.add_parser("delete", help="Delete an asset permanently")
    ast_del.add_argument("asset_id", help="Asset UUID")
    ast_del.add_argument("--force", action="store_true", help="Skip confirmation")
    ast_del.set_defaults(func=cmd_assets_delete)

    ast_dl = ast_sub.add_parser("download", help="Get download URL for an asset")
    ast_dl.add_argument("url", help="Asset location URL")
    ast_dl.add_argument("filename", help="Desired filename")
    ast_dl.set_defaults(func=cmd_assets_download)

    # sources
    src = sub.add_parser("sources", help="Manage data source connectors")
    src_sub = src.add_subparsers(dest="subcommand")

    src_list = src_sub.add_parser("list", help="List connected sources")
    src_list.set_defaults(func=cmd_sources)

    src_disc = src_sub.add_parser("discover", help="Discover available source connectors")
    src_disc.set_defaults(func=cmd_sources_discover)

    # tasks / alerts
    tsk = sub.add_parser("tasks", help="Manage scheduled tasks and alerts")
    tsk_sub = tsk.add_subparsers(dest="subcommand")

    tsk_list = tsk_sub.add_parser("list", help="List scheduled tasks")
    tsk_list.set_defaults(func=cmd_tasks_list)

    tsk_create = tsk_sub.add_parser("create", help="Create a scheduled task")
    tsk_create.add_argument("name", help="Task name")
    tsk_create.add_argument("prompt", nargs="+", help="Task prompt/query")
    tsk_create.add_argument("--start-at", required=True, help="Start datetime (ISO 8601)")
    tsk_create.add_argument("--rrule", required=True, help="Recurrence rule (e.g. FREQ=DAILY;BYHOUR=10;BYMINUTE=0)")
    tsk_create.add_argument("--tzid", default="UTC", help="Timezone (default: UTC)")
    tsk_create.add_argument("--sources", default="web", help="Comma-separated sources")
    tsk_create.add_argument("--model", default="pplx_pro", help="Model preference")
    tsk_create.set_defaults(func=cmd_tasks_create)

    tsk_del = tsk_sub.add_parser("delete", help="Delete a scheduled task")
    tsk_del.add_argument("task_id", help="Task ID")
    tsk_del.add_argument("--force", action="store_true", help="Skip confirmation")
    tsk_del.set_defaults(func=cmd_tasks_delete)

    tsk_recurring = tsk_sub.add_parser("recurring", help="List recurring tasks")
    tsk_recurring.set_defaults(func=cmd_tasks_recurring)

    # finance
    fin = sub.add_parser("finance", help="Finance quotes and alerts")
    fin_sub = fin.add_subparsers(dest="subcommand")

    fin_quote = fin_sub.add_parser("quote", help="Get quote for a ticker")
    fin_quote.add_argument("symbol", help="Ticker symbol (e.g. XAUUSD, AAPL)")
    fin_quote.set_defaults(func=cmd_finance_quote)

    fin_alert = fin_sub.add_parser("alert", help="Create a price alert")
    fin_alert.add_argument("name", help="Alert name")
    fin_alert.add_argument("ticker", help="Ticker symbol")
    fin_alert.add_argument("threshold", type=float, help="Price threshold")
    fin_alert.add_argument("--prompt", default="", help="Custom notification message")
    fin_alert.add_argument("--event-type", default="STOCK_PRICE_TARGET", help="Event type")
    fin_alert.add_argument("--model", default="turbo", help="Model preference")
    fin_alert.set_defaults(func=cmd_finance_alert)

    # billing
    bill = sub.add_parser("billing", help="Show subscription billing info")
    bill.set_defaults(func=cmd_billing)

    # discover
    d = sub.add_parser("discover", help="Browse discover feed")
    d.add_argument("--category")
    d.add_argument("-l", "--limit", type=int, default=10)
    d.set_defaults(func=cmd_discover)

    # profile
    pr = sub.add_parser("profile", help="Show user profile")
    pr.set_defaults(func=cmd_profile)

    # rate-limits
    rl = sub.add_parser("rate-limits", help="Show rate-limit status")
    rl.add_argument("--raw", action="store_true", help="Output raw JSON")
    rl.set_defaults(func=cmd_rate_limits)

    # notifications
    nf = sub.add_parser("notifications", help="Show unread notification count")
    nf.add_argument("--raw", action="store_true", help="Output raw JSON")
    nf.set_defaults(func=cmd_notifications)

    # ai-profile
    ap = sub.add_parser("ai-profile", help="Show AI profile settings")
    ap.add_argument("--raw", action="store_true", help="Output raw JSON")
    ap.set_defaults(func=cmd_ai_profile)

    # status (consolidated)
    sts = sub.add_parser("status", help="Show consolidated account status")
    sts.add_argument("--raw", action="store_true", help="Output raw JSON")
    sts.add_argument("--sections", default="all", help="Comma-separated: all,user,rate,asi,notif")
    sts.set_defaults(func=cmd_status)

    # credits
    cr = sub.add_parser("credits", help="Show credits balance and billing info")
    cr.set_defaults(func=cmd_credits)

    # settings
    st = sub.add_parser("settings", help="Show user account settings and limits")
    st.set_defaults(func=cmd_settings)

    # memories
    mem = sub.add_parser("memories", help="Manage Perplexity memories")
    mem_sub = mem.add_subparsers(dest="subcommand")

    mem_list = mem_sub.add_parser("list", help="List memories")
    mem_list.add_argument("-l", "--limit", type=int, default=20)
    mem_list.add_argument("-o", "--offset", type=int, default=0)
    mem_list.add_argument("-s", "--search", default="", help="Search filter")
    mem_list.set_defaults(func=cmd_memories_list)

    mem_get = mem_sub.add_parser("get", help="Get a specific memory")
    mem_get.add_argument("key", help="Memory key")
    mem_get.set_defaults(func=cmd_memories_get)

    mem_del = mem_sub.add_parser("delete", help="Delete a memory")
    mem_del.add_argument("key", help="Memory key to delete")
    mem_del.add_argument("--force", action="store_true", help="Skip confirmation")
    mem_del.set_defaults(func=cmd_memories_delete)

    # computer / ASI tasks
    asi_tsk = sub.add_parser("computer-tasks", help="List computer/ASI tasks")
    asi_tsk.add_argument("-l", "--limit", type=int, default=20)
    asi_tsk.add_argument("-o", "--offset", type=int, default=0)
    asi_tsk.set_defaults(func=cmd_tasks)

    # workflows
    wf = sub.add_parser("workflows", help="List available workflows")
    wf.set_defaults(func=cmd_workflows)

    # refresh-cookies
    rc = sub.add_parser(
        "refresh-cookies",
        help="Refresh Perplexity cookies via CloakBrowser CDP + Gmail OTP"
    )
    rc.add_argument(
        "--headless", action="store_true",
        help="Run CloakBrowser in headless mode (no GUI window)"
    )
    rc.set_defaults(func=cmd_refresh_cookies)

    # validate
    val = sub.add_parser(
        "validate",
        help="Check if the current Perplexity session is still valid"
    )
    val.set_defaults(func=cmd_validate)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help(sys.stderr)
        sys.exit(1)
    try:
        args.func(args)
    except KeyboardInterrupt:
        sys.exit(130)
    except RuntimeError as e:
        msg = str(e)
        if "cookies" in msg.lower() or "auth" in msg.lower() or "BWS" in msg:
            print(f"Auth Error: {msg}", file=sys.stderr)
            print("\nTo fix:", file=sys.stderr)
            print("  1. Set PERPLEXITY_COOKIES_PATH=/path/to/cookies.json", file=sys.stderr)
            print("  2. Or configure BWS: export BWS_ACCESS_TOKEN=...", file=sys.stderr)
            print("  3. Or run: python scripts/setup_bws_secret.py setup-cookies /path/to/cookies.json", file=sys.stderr)
        else:
            print(f"Error: {msg}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
