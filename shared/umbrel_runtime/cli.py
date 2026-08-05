from __future__ import annotations

import argparse
import json
from pathlib import Path

from .runtime import UmbrelRuntime


def print_json(payload) -> None:
    print(
        json.dumps(
            payload,
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only Seymour Umbrel runtime diagnostics."
        )
    )

    parser.add_argument(
        "--data-directory",
        type=Path,
    )
    parser.add_argument(
        "--app-store-root",
        type=Path,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser(
        "apps",
    )

    show = subparsers.add_parser(
        "show",
    )
    show.add_argument(
        "app_id",
    )
    show.add_argument(
        "--health-host",
    )
    show.add_argument(
        "--health-port",
        type=int,
    )

    logs = subparsers.add_parser(
        "logs",
    )
    logs.add_argument(
        "app_id",
    )
    logs.add_argument(
        "--tail",
        type=int,
        default=100,
    )

    args = parser.parse_args()

    runtime = UmbrelRuntime(
        data_directory=args.data_directory,
        app_store_root=args.app_store_root,
    )

    if args.command == "apps":
        source = runtime.list_source_apps()
        installed = runtime.list_installed_apps()

        print_json(
            {
                "sourceApps": source,
                "installedApps": installed,
                "sourceCount": len(source),
                "installedCount": len(installed),
                "dockerAvailable": (
                    runtime.docker_available()
                ),
            }
        )
        return

    if args.command == "show":
        result = runtime.inspect_app(
            args.app_id,
            health_host=args.health_host,
            health_port=args.health_port,
        )
        print_json(
            result.to_dict()
        )
        return

    if args.command == "logs":
        print_json(
            {
                "appId": args.app_id,
                "logs": runtime.collect_logs(
                    args.app_id,
                    tail=args.tail,
                ),
            }
        )
        return


if __name__ == "__main__":
    main()
