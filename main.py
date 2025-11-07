"""rickroller-chatgpt-app

Exposes a widget that plays the Rick Astley video via CDN.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, List

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, ValidationError


# Define widget structure
@dataclass(frozen=True)
class RickWidget:
    identifier: str
    title: str
    template_uri: str
    invoking: str
    invoked: str
    html: str
    response_text: str


# Initialize FastMCP
mcp = FastMCP(
    name="rickroller-chatgpt-app",
    sse_path="/mcp",
    message_path="/mcp/messages",
    stateless_http=True,
)


# Widget definition: CDN video for Rick Astley
_RICK_IFRAME = (
    "<div style=\"display:flex;flex-direction:column;gap:12px;\">\n"
    "  <h2 style=\"margin:0;font-size:16px;\">Never Gonna Give You Up</h2>\n"
    "  <div style=\"position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:8px;\">\n"
    "    <video controls autoplay style=\"position:absolute;top:0;left:0;width:100%;height:100%;\" "
    "src=\"https://cdn-useast1.kapwing.com/static/templates/rick-roll-video-meme-template-video-1da252ec.mp4\"></video>\n"
    "  </div>\n"
    "</div>\n"
)

widgets: List[RickWidget] = [
    RickWidget(
        identifier="rick-roll",
        title="Rick Roll Player",
        template_uri="ui://widget/rick-roll.html",
        invoking="Loading the Rick Roll...",
        invoked="Enjoy the Rick Roll!",
        html=_RICK_IFRAME,
        response_text="Rick Roll widget ready",
    ),
]


# Lookups
WIDGETS_BY_ID: Dict[str, RickWidget] = {w.identifier: w for w in widgets}
WIDGETS_BY_URI: Dict[str, RickWidget] = {w.template_uri: w for w in widgets}


# Input schema
class RickToolInput(BaseModel):
    """Input for the rick-roll tool."""

    autoplay: bool = Field(default=False, description="Autoplay the video")

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


TOOL_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "autoplay": {"type": "boolean", "description": "Autoplay the video"},
    },
    "additionalProperties": False,
}


def _tool_meta(widget: RickWidget) -> Dict[str, Any]:
    return {
        "openai/outputTemplate": widget.template_uri,
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
        "annotations": {
            "destructiveHint": False,
            "openWorldHint": False,
            "readOnlyHint": True,
        },
    }


@mcp._mcp_server.list_tools()
async def _list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name=w.identifier,
            title=w.title,
            description="Plays the Rick Astley video in a widget",
            inputSchema=deepcopy(TOOL_INPUT_SCHEMA),
            _meta=_tool_meta(w),
        )
        for w in widgets
    ]


@mcp._mcp_server.list_resources()
async def _list_resources() -> List[types.Resource]:
    return [
        types.Resource(
            name=w.title,
            title=w.title,
            uri=w.template_uri,
            description="Rick Roll widget markup",
            mimeType="text/html+skybridge",
            _meta=_tool_meta(w),
        )
        for w in widgets
    ]


@mcp._mcp_server.list_resource_templates()
async def _list_resource_templates() -> List[types.ResourceTemplate]:
    return [
        types.ResourceTemplate(
            name=w.title,
            title=w.title,
            uriTemplate=w.template_uri,
            description="Rick Roll widget markup",
            mimeType="text/html+skybridge",
            _meta=_tool_meta(w),
        )
        for w in widgets
    ]


async def _handle_read_resource(req: types.ReadResourceRequest) -> types.ServerResult:
    widget = WIDGETS_BY_URI.get(str(req.params.uri))
    if widget is None:
        return types.ServerResult(
            types.ReadResourceResult(contents=[], _meta={"error": "Unknown resource"})
        )

    contents = [
        types.TextResourceContents(
            uri=widget.template_uri,
            mimeType="text/html+skybridge",
            text=widget.html,
            _meta=_tool_meta(widget),
        )
    ]
    return types.ServerResult(types.ReadResourceResult(contents=contents))


async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
    widget = WIDGETS_BY_ID.get(req.params.name)
    if widget is None:
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text="Unknown tool")],
                isError=True,
            )
        )

    args = req.params.arguments or {}
    try:
        payload = RickToolInput.model_validate(args)
    except ValidationError as exc:
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text=f"Validation error: {exc.errors()}")],
                isError=True,
            )
        )

    # HTML contains video with autoplay already enabled
    html = widget.html

    embedded = types.EmbeddedResource(
        type="resource",
        resource=types.TextResourceContents(
            uri=widget.template_uri,
            mimeType="text/html+skybridge",
            text=html,
            title=widget.title,
        ),
    )

    meta: Dict[str, Any] = {
        "openai.com/widget": embedded.model_dump(mode="json"),
        "openai/outputTemplate": widget.template_uri,
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
    }

    return types.ServerResult(
        types.CallToolResult(
            content=[types.TextContent(type="text", text=widget.response_text)],
            structuredContent={"autoplay": payload.autoplay},
            _meta=meta,
        )
    )


# Register handlers
mcp._mcp_server.request_handlers[types.CallToolRequest] = _call_tool_request
mcp._mcp_server.request_handlers[types.ReadResourceRequest] = _handle_read_resource


# FastAPI app with CORS
app = mcp.streamable_http_app()

try:
    from starlette.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )
except Exception:
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8080)

