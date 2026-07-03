"""Terminal UI for agency-kit — browse missions, view deliverables, inspect stats.

All textual imports are deferred to launch() so this module is importable
without textual installed; errors surface only when `agency tui` is invoked.

Keyboard shortcuts
  1 / 2 / 3   Pipeline / Viewer / Analytics
  Enter        Open selected mission in Viewer
  r            Refresh mission list
  q            Quit

Install:  pip install -e "[tui]"
Run:      agency tui
"""

from __future__ import annotations

from collections import Counter


def launch() -> None:
    """Run the TUI. Raises ImportError if textual is not installed."""
    try:
        from textual.app import App, ComposeResult
        from textual.binding import Binding
        from textual.containers import ScrollableContainer
        from textual.widgets import (
            DataTable, Footer, Header, Markdown, Static, TabbedContent, TabPane,
        )
    except ImportError:
        raise ImportError('Textual not installed. Run:  pip install -e ".[tui]"')

    class AgencyTUI(App):
        """Agency-Kit mission browser — Pipeline / Viewer / Analytics."""

        TITLE = "Agency-Kit"
        SUB_TITLE = "Mission Browser"

        CSS = """
        Screen       { background: $background; }
        DataTable    { height: 1fr; }
        ScrollableContainer { height: 1fr; padding: 1 2; }
        """

        BINDINGS = [
            Binding("q", "quit", "Quit"),
            Binding("1", "show_pipeline", "Pipeline"),
            Binding("2", "show_viewer", "Viewer"),
            Binding("3", "show_analytics", "Analytics"),
            Binding("r", "refresh", "Refresh"),
        ]

        def __init__(self, missions: list) -> None:
            super().__init__()
            self._missions = missions

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            with TabbedContent(initial="pipeline"):
                with TabPane("Pipeline [1]", id="pipeline"):
                    yield DataTable(id="pipeline-table", cursor_type="row")
                with TabPane("Viewer [2]", id="viewer-pane"):
                    with ScrollableContainer():
                        yield Markdown(id="viewer")
                with TabPane("Analytics [3]", id="analytics-pane"):
                    with ScrollableContainer():
                        yield Static(id="analytics", markup=True)
            yield Footer()

        def on_mount(self) -> None:
            self._fill_pipeline()
            self._fill_analytics()
            self.query_one("#viewer", Markdown).update(
                "_Select a mission in the Pipeline tab and press **Enter** to open it here._"
            )

        def _fill_pipeline(self) -> None:
            table = self.query_one("#pipeline-table", DataTable)
            table.clear(columns=True)
            table.add_columns("MISSION ID", "GOAL", "ROUTE", "ITER", "VERDICT", "✓")
            for m in self._missions:
                mid = m.get("mission_id") or ""
                goal = (m.get("goal") or "")[:44]
                if len(m.get("goal", "")) > 44:
                    goal += "…"
                route = "→".join(m.get("route") or []) or "—"
                table.add_row(
                    mid[:34], goal, route,
                    str(m.get("iteration", 0)),
                    m.get("verdict", "—"),
                    "✓" if m.get("delivered") else "○",
                    key=mid,
                )

        def _fill_analytics(self) -> None:
            self.query_one("#analytics", Static).update(self._analytics_markup())

        def _analytics_markup(self) -> str:
            if not self._missions:
                return "[italic]No missions recorded yet.[/italic]"
            total = len(self._missions)
            delivered = sum(1 for m in self._missions if m.get("delivered"))
            verdicts = [
                m.get("verdict") for m in self._missions
                if m.get("verdict") and m.get("verdict") != "—"
            ]
            passes = sum(1 for v in verdicts if v == "PASS")
            vetoes = sum(1 for v in verdicts if v == "VETO")
            iters = [int(m.get("iteration") or 1) for m in self._missions]
            avg = sum(iters) / len(iters) if iters else 0
            dept_counts: Counter = Counter(
                d for m in self._missions for d in (m.get("route") or [])
            )
            lines = [
                "[bold cyan]Agency-Kit — Mission Analytics[/bold cyan]",
                "",
                f"[green]Total missions[/green]    {total}",
                f"[green]Delivered[/green]         {delivered}  "
                f"({100 * delivered // total if total else 0}%)",
                f"[green]Inspector PASS[/green]    {passes}",
                f"[yellow]Inspector VETO[/yellow]    {vetoes}",
                f"[cyan]Avg iterations[/cyan]    {avg:.1f}",
                "",
                "[bold]Department usage[/bold]",
            ]
            max_c = max(dept_counts.values(), default=1)
            for dept, count in dept_counts.most_common():
                bar = "█" * max(1, round(20 * count / max_c))
                lines.append(f"  [cyan]{dept:<12}[/cyan] {bar}  {count}×")
            return "\n".join(lines)

        def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
            mid = event.row_key.value
            if mid:
                self._load_viewer(mid)
                self.query_one(TabbedContent).active = "viewer-pane"

        def _load_viewer(self, mission_id: str) -> None:
            from agency_kit.store import missions_dir
            viewer = self.query_one("#viewer", Markdown)
            md_path = missions_dir() / mission_id / "deliverable.md"
            if not md_path.exists():
                viewer.update(f"_No deliverable found for mission `{mission_id}`._")
                return
            from agency_kit.store import strip_frontmatter
            content = strip_frontmatter(md_path.read_text(encoding="utf-8"))
            viewer.update(content)

        def action_show_pipeline(self) -> None:
            self.query_one(TabbedContent).active = "pipeline"

        def action_show_viewer(self) -> None:
            self.query_one(TabbedContent).active = "viewer-pane"

        def action_show_analytics(self) -> None:
            self.query_one(TabbedContent).active = "analytics-pane"

        def action_refresh(self) -> None:
            from agency_kit.store import list_missions
            self._missions = list_missions()
            self._fill_pipeline()
            self._fill_analytics()
            self.notify("Mission list refreshed.")

    from agency_kit.store import list_missions
    AgencyTUI(list_missions()).run()
