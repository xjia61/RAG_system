from mcp.server.fastmcp import FastMCP

from google_tools import create_calendar_event, create_google_doc


mcp = FastMCP("Google Tools")


@mcp.tool()
def schedule_google_calendar_event(
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    timezone: str = "America/Chicago",
    attendee_email: str | None = None,
) -> dict:
    """
    Create a Google Calendar event.

    Example start_time:
    2026-05-12T09:00:00

    Example end_time:
    2026-05-12T09:30:00
    """

    return create_calendar_event(
        title=title,
        start_time=start_time,
        end_time=end_time,
        description=description,
        location=location,
        timezone=timezone,
        attendee_email=attendee_email,
    )


@mcp.tool()
def save_to_google_doc(
    title: str,
    body: str,
) -> dict:
    """
    Create a Google Doc and insert text into it.
    """

    return create_google_doc(
        title=title,
        body=body,
    )


if __name__ == "__main__":
    mcp.run()