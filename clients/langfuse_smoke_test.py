import os
import sys
import argparse
from langfuse import Langfuse


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Send a simple smoke-test trace to a Langfuse deployment.\n"
        "Provide --host, --public-key, --secret-key or set env vars LANGFUSE_HOST, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY."
    )
    parser.add_argument("--host", default=os.getenv("LANGFUSE_HOST"), help="Langfuse base URL, e.g. http://<alb-dns>")
    parser.add_argument(
        "--public-key",
        dest="public_key",
        default=os.getenv("LANGFUSE_PUBLIC_KEY"),
        help="Langfuse public key (or set LANGFUSE_PUBLIC_KEY)",
    )
    parser.add_argument(
        "--secret-key",
        dest="secret_key",
        default=os.getenv("LANGFUSE_SECRET_KEY"),
        help="Langfuse secret key (or set LANGFUSE_SECRET_KEY)",
    )

    args = parser.parse_args()

    missing = [
        name for name, val in [("--host", args.host), ("--public-key", args.public_key), ("--secret-key", args.secret_key)] if not val
    ]
    if missing:
        print(f"Missing required arguments: {' '.join(missing)}", file=sys.stderr)
        parser.print_help(sys.stderr)
        return 2

    try:
        lf = Langfuse(host=args.host, public_key=args.public_key, secret_key=args.secret_key)
        # Optional connectivity check (adds latency; avoid in production paths)
        try:
            if lf.auth_check():
                print("Auth check: OK")
            else:
                print("Auth check: FAILED", file=sys.stderr)
        except Exception:
            # If auth_check is unavailable or fails, continue with the span attempt
            pass

        # SDK v3: create a span for a quick smoke test
        with lf.start_as_current_span(name="smoke-test", input={"hello": "world"}) as root_span:
            # Attach some attributes to the trace
            try:
                root_span.update_trace(tags=["smoke", "sdk-py"], session_id="manual-test")
            except Exception:
                # update_trace is optional; ignore if not available in current SDK version
                pass
            # Update span output
            try:
                root_span.update(output={"ok": True})
            except Exception:
                pass

        # Ensure buffered events are sent
        lf.flush()
        print(f"OK: sent span 'smoke-test' to {args.host}")
        return 0
    except Exception as e:
        print(f"ERROR: failed to send trace: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
