from typing import Literal

from mcp.server.fastmcp import FastMCP

from chart_tools import create_chart_file


mcp = FastMCP("Chart Tools")


@mcp.tool()
def draw_chart(
    title: str,
    data: dict[str, float],
    chart_type: Literal["bar", "line", "pie"] = "bar",
    x_label: str = "Category",
    y_label: str = "Value",
) -> dict:
    """
    Draw a chart from structured data and save it as a PNG file.

    Example:
    title = "Tumor Cases"
    data = {"Tumor A": 12, "Tumor B": 8, "Tumor C": 15}
    chart_type = "bar"
    """

    return create_chart_file(
        title=title,
        data=data,
        chart_type=chart_type,
        x_label=x_label,
        y_label=y_label,
    )


@mcp.tool()
def draw_bar_chart(
    title: str,
    data: dict[str, float],
    x_label: str = "Category",
    y_label: str = "Value",
) -> dict:
    """
    Draw a bar chart.
    """

    return create_chart_file(
        title=title,
        data=data,
        chart_type="bar",
        x_label=x_label,
        y_label=y_label,
    )


@mcp.tool()
def draw_line_chart(
    title: str,
    data: dict[str, float],
    x_label: str = "X",
    y_label: str = "Y",
) -> dict:
    """
    Draw a line chart.
    """

    return create_chart_file(
        title=title,
        data=data,
        chart_type="line",
        x_label=x_label,
        y_label=y_label,
    )


if __name__ == "__main__":
    mcp.run()