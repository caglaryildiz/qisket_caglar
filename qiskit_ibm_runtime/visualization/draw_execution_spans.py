# This code is part of Qiskit.
#
# (C) Copyright IBM 2024.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Functions to visualize :class:`~.ExecutionSpans` objects."""

from __future__ import annotations

from functools import partial
from itertools import cycle
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from ..execution_span import ExecutionSpan, ExecutionSpans
from .utils import plotly_module

if TYPE_CHECKING:
    from plotly.graph_objects import Figure as PlotlyFigure


HOVER_TEMPLATE = "<br>".join(
    [
        "<b>ExecutionSpans{id}[{idx}]</b>",
        "<b>&nbsp;&nbsp;&nbsp;Start:</b> {span.start:%Y-%m-%d %H:%M:%S.%f}",
        "<b>&nbsp;&nbsp;&nbsp;Stop:</b> {span.stop:%Y-%m-%d %H:%M:%S.%f}",
        "<b>&nbsp;&nbsp;&nbsp;Size:</b> {span.size}",
        "<b>&nbsp;&nbsp;&nbsp;Pub Indexes:</b> {idxs}",
    ]
)


def _get_idxs(span: ExecutionSpan, limit: int = 10) -> str:
    if len(idxs := span.pub_idxs) <= limit:
        return str(idxs)
    else:
        return f"[{', '.join(map(str, idxs[:limit]))}, ...]"


def _get_id(span: ExecutionSpan, multiple: bool) -> str:
    return f"<{hex(id(span))}>" if multiple else ""


def draw_execution_spans(
    *spans: ExecutionSpans,
    common_start: bool = False,
    normalize_y: bool = False,
    line_width: int = 4,
) -> PlotlyFigure:
    """Draw one or more :class:`~.ExecutionSpans` on a bar plot.

    Args:
        spans: One or more :class:`~.ExecutionSpans`.
        common_start: Whether to shift all collections of spans so that their first span's start is
            at :math:`t=0`.
        normalize_y: Whether to display the y-axis units as a percentage of work complete, rather
            than cumulative shots completed.
        line_width: The thickness of line segments.

    Returns:
        A plotly figure.
    """
    go = plotly_module(".graph_objects")
    colors = plotly_module(".colors").qualitative.Plotly

    fig = go.Figure()
    get_id = partial(_get_id, multiple=len(spans) > 1)

    for single_spans, color in zip(spans, cycle(colors)):
        if not single_spans:
            continue

        # sort the spans but remember their original order
        sorted_spans = sorted(enumerate(single_spans), key=lambda x: x[1])

        offset = timedelta()
        if common_start:
            first_start = sorted_spans[0][1].start.replace(tzinfo=None)
            offset = first_start - datetime(year=1970, month=1, day=1)

        total_size = sum(span.size for span in single_spans) if normalize_y else 1
        y_value = 0.0
        for idx, span in sorted_spans:
            y_value += span.size / total_size
            text = HOVER_TEMPLATE.format(span=span, idx=idx, idxs=_get_idxs(span), id=get_id(span))
            # Create a line representing each span as a Scatter trace
            fig.add_trace(
                go.Scatter(
                    x=[span.start - offset, span.stop - offset],
                    y=[y_value, y_value],
                    mode="lines",
                    line={"width": line_width, "color": color},
                    text=text,
                    hoverinfo="text",
                )
            )

    # Axis and layout settings
    fig.update_layout(
        xaxis={"title": "Time", "type": "date"},
        showlegend=False,
        margin={"l": 70, "r": 20, "t": 20, "b": 70},
    )

    if normalize_y:
        fig.update_yaxes(title="Completed Workload", tickformat=".0%")
    else:
        fig.update_yaxes(title="Shots Completed")

    if common_start:
        fig.update_xaxes(tickformat="%H:%M:%S.%f")

    return fig
