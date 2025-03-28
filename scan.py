"""Run a SonarQube scan."""

import argparse
import asyncio
import pathlib
import sys

import attrs
from pygls.client import JsonRPCClient

ARGS = None
ERRORS = False


class ResettableTimer:
    """Timer that can be reset."""

    def __init__(self, duration):
        self.duration = duration
        self.task = None
        self.done_event = asyncio.Event()

    async def start(self):
        """Start the timer."""
        self.done_event.clear()
        while True:
            try:
                await asyncio.sleep(self.duration)
                self.done_event.set()
                break
            except asyncio.CancelledError:
                continue

    def reset(self, new_duration=None):
        """Reset the timer."""
        if new_duration is not None:
            self.duration = new_duration
        if self.task and not self.task.done():
            self.task.cancel()
        self.task = asyncio.create_task(self.start())

    async def wait_for_end(self):
        """Wait for the timer to end."""
        await self.done_event.wait()


@attrs.define
class AnonymousMessage:
    """Anonymous message class."""

    method: str
    jsonrpc: str
    params: dict


@attrs.define
class NoParamsMessage:
    """NoParamsMessage message class."""

    method: str
    jsonrpc: str
    id: str


client = JsonRPCClient()


async def main():
    """Main function."""
    timer = ResettableTimer(60)
    orig_files = {}
    allrules = []
    rules = {}
    diagnostics = []

    @client.feature("sonarlint/isOpenInEditor")
    def sonarlint_is_open_in_editor(_):
        return True

    @client.feature("workspace/configuration")
    def workspace_configuration(_):
        if ARGS.command == "analyze" and ARGS.rules:
            for rule in ARGS.rules.split(","):
                rules[f"{rule}"] = {"level": "on"}
        else:
            for rule in allrules:
                rules[f"{rule}"] = {"level": "on"}
        if ARGS.command == "analyze" and ARGS.disable_rules:
            for rule in ARGS.disable_rules.split(","):
                rules[f"{rule}"] = {"level": "off"}
        return [{"rules": rules}]

    @client.feature("window/workDoneProgress/create")
    @client.feature("sonarlint/readyForTests")
    @client.feature("$/progress")
    @client.feature("window/logMessage")
    @client.feature("sonarlint/filterOutExcludedFiles")
    def ignore(_):  # ignore theses messages
        pass

    @client.feature("textDocument/publishDiagnostics")
    def publish_diagnostics(params):
        global ERRORS  # pylint: disable=global-statement
        for diag in params.diagnostics:
            file = orig_files[params.uri.replace("file://", "")]
            position = f"{diag.range.start.line+1}:{diag.range.start.character+1}"
            diagnostic = f"{file}:{position} - {diag.message} ({diag.code})"
            if diagnostic not in diagnostics:
                diagnostics.append(diagnostic)
                print(diagnostic)
            ERRORS = True
        timer.reset(2)

    if ARGS.debug:
        script_dir = pathlib.Path(__file__).parent.resolve()
        debug_args = [f"{script_dir}/proxy.js"]
    else:
        debug_args = []
    await client.start_io(
        *debug_args,
        ARGS.java,
        "-jar",
        ARGS.sonarlint_ls,
        "-stdio",
        "-analyzers",
        *ARGS.analyzers,
    )

    await client.protocol.send_request_async(
        "initialize",
        {
            "initializationOptions": {
                "productKey": "",
                "productVersion": "",
            },
        },
    )

    def send_anonymous_message(method, params):
        client.protocol._send_data(  # pylint: disable=protected-access
            AnonymousMessage(method=method, params=params, jsonrpc="2.0")
        )

    send_anonymous_message("initialized", {})
    send_anonymous_message("workspace/didChangeConfiguration", {})

    for i in await client.protocol.send_request_async("sonarlint/listAllRules"):
        for j in i:
            allrules.append(j.key)

    send_anonymous_message(
        "workspace/didChangeConfiguration",
        {"settings": {"sonarlint": {"rules": rules}}},
    )

    if ARGS.command == "list-rules":
        print(",".join(allrules))
    if ARGS.command == "analyze":
        for file in ARGS.files:
            tmpfile = f"/tmp/{file.replace('/', '_')}"
            orig_files[tmpfile] = file
            send_anonymous_message(
                "textDocument/didOpen",
                {
                    "textDocument": {
                        "uri": f"file://{tmpfile}",
                        "text": open(file, "r", encoding="utf-8").read(),
                        "languageId": "python",
                        "version": 1,
                    }
                },
            )
        await timer.wait_for_end()
    await client.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a SonarQube scan.")
    parser.add_argument("--debug", action="store_true", help="Debug lsp in a log file")
    parser.add_argument("--java", help="Specify the Java binary", default="java")
    parser.add_argument(
        "--sonarlint-ls", required=True, help="Specify the sonarlint-ls jar binary"
    )
    parser.add_argument(
        "--analyzers",
        required=True,
        nargs="+",
        help="Specify one or more Sonar analyzer jar binaries",
    )
    parser.add_argument("--nop", help="Do nothing", action="store_true")
    subparsers = parser.add_subparsers(
        title="commands", description="Available commands", dest="command"
    )
    list_rules_parser = subparsers.add_parser(
        "list-rules", help="List all rules (see https://sonarsource.github.io/rspec/)"
    )
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze the codebase with the specified analyzers"
    )
    analyze_parser.add_argument("--rules", help="Specify the rules to apply")
    analyze_parser.add_argument("--disable-rules", help="Specify the rules to disable")
    analyze_parser.add_argument("--files", nargs="+", help="List of files to process")
    ARGS = parser.parse_args()
    asyncio.run(main())
    if ERRORS:
        sys.exit(1)
