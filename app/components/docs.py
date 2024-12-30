import json
from typing import cast

import discord
from discord.app_commands import Choice, autocomplete
from github.ContentFile import ContentFile

from app.components.entity_mentions import REPOSITORIES
from app.setup import bot
from app.utils import SERVER_ONLY

URL_TEMPLATE = "https://ghostty.org/docs/{section}{page}"

SECTIONS = {
    "action": "config/keybind/reference#",
    "help": "help/",
    "install": "install/",
    "vt": "vt/",
    "option": "config/reference#",
}

WEBSITE_PATHS = {
    "nav": "docs/nav.json",
    "option": "docs/config/reference.mdx",
    "action": "docs/config/keybind/reference.mdx",
}


def refresh_sitemap() -> None:
    # Reading vt/, install/, help/ subpages by checking nav.json
    raw = cast(ContentFile, REPOSITORIES["web"].get_contents(WEBSITE_PATHS["nav"]))
    nav = json.loads(raw.decoded_content)["items"]
    for entry in nav:
        if entry["type"] != "folder":
            continue
        sitemap[entry["path"].strip("/")] = list(
            filter(None, (item["path"].strip("/") for item in entry["children"]))
        )

    # Reading config references by parsing headings in .mdx files
    for key, path in WEBSITE_PATHS.items():
        if key == "nav":
            continue
        raw = cast(ContentFile, REPOSITORIES["web"].get_contents(path))
        sitemap[key] = [
            line.removeprefix(b"## ").strip(b"`").decode()
            for line in raw.decoded_content.splitlines()
            if line.startswith(b"## ")
        ]
    # Special case for /config/keybind/sequence
    sitemap["action"].append("trigger-sequences")


sitemap: dict[str, list[str]] = {}
refresh_sitemap()


async def section_autocomplete(
    _: discord.Interaction, current: str
) -> list[Choice[str]]:
    return [
        Choice(name=name, value=name)
        for name in SECTIONS
        if current.casefold() in name.casefold()
    ]


async def page_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[Choice[str]]:
    if not (interaction.data and (options := interaction.data.get("options"))):
        return []
    section = next(
        cast(str, opt["value"]) for opt in options if opt["name"] == "section"
    )
    return [
        Choice(name=name, value=name)
        for name in sitemap.get(section, [])
        if current.casefold() in name.casefold()
    ][:25]  # Discord only allows 25 options for autocomplete


@bot.tree.command(name="docs", description="Link a documentation page.")
@autocomplete(section=section_autocomplete, page=page_autocomplete)
@SERVER_ONLY
async def docs(interaction: discord.Interaction, section: str, page: str) -> None:
    if section not in SECTIONS:
        await interaction.response.send_message(
            f"Invalid section {section!r}", ephemeral=True
        )
        return
    if page not in sitemap.get(section, []):
        await interaction.response.send_message(
            f"Invalid page {page!r}", ephemeral=True
        )
        return

    section_path = SECTIONS[section]
    # Special case for /config/keybind/sequence
    if (section, page) == ("action", "trigger-sequences"):
        section_path, page = "config/keybind/", "sequence"

    await interaction.response.send_message(
        URL_TEMPLATE.format(section=section_path, page=page)
    )
