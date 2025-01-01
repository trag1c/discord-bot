from __future__ import annotations

import json
from typing import NotRequired, TypedDict, cast

import discord
from discord.app_commands import Choice, autocomplete
from github.ContentFile import ContentFile

from app.components.entity_mentions import REPOSITORIES
from app.setup import bot
from app.utils import SERVER_ONLY

URL_TEMPLATE = "https://ghostty.org/docs/{section}{page}"

SECTIONS = {
    "action": "config/keybind/reference#",
    "config": "config/",
    "help": "help/",
    "install": "install/",
    "keybind": "config/keybind/",
    "option": "config/reference#",
    "vt-concepts": "vt/concepts/",
    "vt-control": "vt/control/",
    "vt-csi": "vt/csi/",
    "vt-esc": "vt/esc/",
    "vt": "vt/",
}

WEBSITE_PATHS = {
    "nav": "docs/nav.json",
    "option": "docs/config/reference.mdx",
    "action": "docs/config/keybind/reference.mdx",
}


class Entry(TypedDict):
    type: str
    path: str
    title: str
    children: NotRequired[list[Entry]]


def _load_children(
    sitemap: dict[str, list[str]], path: str, children: list[Entry]
) -> None:
    sitemap[path] = []
    for item in children:
        sitemap[path].append((page := item["path"].lstrip("/")) or "overview")
        if item["type"] == "folder":
            _load_children(sitemap, f"{path}-{page}", item.get("children", []))


def refresh_sitemap() -> None:
    # Reading vt/, install/, help/, config/,
    # config/keybind/ subpages by reading nav.json
    raw = cast(ContentFile, REPOSITORIES["web"].get_contents(WEBSITE_PATHS["nav"]))
    nav: list[Entry] = json.loads(raw.decoded_content)["items"]
    for entry in nav:
        if entry["type"] != "folder":
            continue
        _load_children(sitemap, entry["path"].lstrip("/"), entry.get("children", []))

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

    # Manual adjustments
    sitemap["install"].remove("release-notes")
    sitemap["keybind"] = sitemap.pop("config-keybind")
    del sitemap["install-release-notes"]
    for vt_section in (s for s in SECTIONS if s.startswith("vt-")):
        sitemap["vt"].remove(vt_section.removeprefix("vt-"))


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
        (cast(str, opt["value"]) for opt in options if opt["name"] == "section"),
        None,
    )
    if section is None:
        return []
    return [
        Choice(name=name, value=name)
        for name in sitemap.get(section, [])
        if current.casefold() in name.casefold()
    ][:25]  # Discord only allows 25 options for autocomplete


@bot.tree.command(name="docs", description="Link a documentation page.")
@autocomplete(section=section_autocomplete, page=page_autocomplete)
@SERVER_ONLY
async def docs(
    interaction: discord.Interaction, section: str, page: str, message: str = ""
) -> None:
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
    page = page if page != "overview" else ""

    await interaction.response.send_message(
        f"{message}\n{URL_TEMPLATE.format(section=section_path, page=page)}"
    )
