from mcp.server.fastmcp import FastMCP

from audio_tools import speak_text_to_audio_file


mcp = FastMCP("Audio Tools")


@mcp.tool()
def speak_text_to_audio(
    text: str,
    voice: str = "Samantha",
    rate: int = 180,
) -> dict:
    """
    Convert text into a local audio file.

    Args:
        text: Text to speak.
        voice: macOS voice name, for example Samantha, Alex, Daniel.
        rate: Speaking speed. Default is 180.
    """

    return speak_text_to_audio_file(
        text=text,
        voice=voice,
        rate=rate,
    )


if __name__ == "__main__":
    mcp.run()