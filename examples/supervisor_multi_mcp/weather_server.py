from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Weather Stdio Server")
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers, timeout=30.0)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

def format_alert(f: dict) -> str:
    p = f["properties"]
    return (
        f"\nEvent: {p.get('event', 'Unknown')}"
        f"\nArea: {p.get('areaDesc', 'Unknown')}"
        f"\nSeverity: {p.get('severity', 'Unknown')}"
        f"\nDescription: {p.get('description', 'No description')}"
        f"\nInstructions: {p.get('instruction', 'No instructions')}\n"
    )

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state (e.g. CA, NY)."""
    url = f"{NWS_API_BASE}/alerts/active/area/{state.upper()}"
    data = await make_nws_request(url)
    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."
    if not data["features"]:
        return "No active alerts for this state."
    alerts = [format_alert(f) for f in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location (lat, lon)."""
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)
    if (not points_data
        or "properties" not in points_data
        or "forecast" not in points_data["properties"]):
        return "Unable to fetch forecast data for this location."
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)
    if (not forecast_data
        or "properties" not in forecast_data
        or "periods" not in forecast_data["properties"]):
        return "Unable to fetch detailed forecast."
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:
        forecasts.append(
            f"\n{period['name']}:"
            f"\nTemperature: {period['temperature']}°{period['temperatureUnit']}"
            f"\nWind: {period['windSpeed']} {period['windDirection']}"
            f"\nForecast: {period['detailedForecast']}\n"
        )
    return "\n---\n".join(forecasts)

if __name__ == "__main__":
    mcp.run(transport='stdio')