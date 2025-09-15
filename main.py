# -*- coding: utf-8 -*-
# Module: default
# Author: Roman V. M., VincoNafta
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import json
import re
import sys
from datetime import datetime, timezone
from urllib.parse import parse_qsl
from urllib.parse import urlencode

import urllib3
import xbmc
import xbmcgui
import xbmcplugin
from bs4 import BeautifulSoup

_url = sys.argv[0]
_handle = int(sys.argv[1])

ALPHABET = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
            'L', 'M', 'N', 'O', 'P', 'R', 'S', 'T', 'U', 'V', 'Z']


def search(page):
    user_agent = {'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0"}

    http = urllib3.PoolManager(10, headers=user_agent)
    return http.request("GET", page)


def getActualRelation(program_dnes, now_utc):
    for p in program_dnes:
        p["zacatek_dt"] = datetime.fromisoformat(p["zacatek"])

    zacali = [p for p in program_dnes if p["zacatek_dt"] <= now_utc.astimezone(p["zacatek_dt"].tzinfo)]

    if zacali:
        posledny = max(zacali, key=lambda x: x["zacatek_dt"])
        zacatek = posledny["zacatek_dt"]

        return getDisplayName(posledny, zacatek)
    else:
        return "Koniec vysielania"


def getProgram(channel, json_data):
    program_dnes = json_data["program"][channel]
    now_utc = datetime.now(timezone.utc)
    displayed_programs_str = f"{getActualRelation(program_dnes, now_utc)}\n"
    for program in program_dnes:

        zacatek = datetime.fromisoformat(program["zacatek"])

        now_local = now_utc.astimezone(zacatek.tzinfo)

        if now_local < zacatek:
            displayedName = getDisplayName(program, zacatek)
            displayed_programs_str += f"{displayedName}\n"
    return displayed_programs_str


def getDisplayName(program, zacatek):
    name = program.get("nazev", "")
    cast = program.get("podnazev", "")
    displayedName = zacatek.strftime("%H.%M")
    if cast.strip() == "":
        displayedName += f" - {name}"
    else:
        displayedName += f" - {name} - {cast}"
    return displayedName


def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def getLiveIcon(channel_name, api_reference):
    return api_reference["logo"]["512"][str(channel_name)]


def list_categories():
    xbmcplugin.setPluginCategory(_handle, 'Televize Noe')
    xbmcplugin.setContent(_handle, 'videos')

    live_stream_api = json.loads(search("https://api.tvnoe.cz/live").data)

    for channel, stream in live_stream_api["stream"].items():
        epg_data = json.loads(search("https://api.tvnoe.cz/program").data)
        list_item = xbmcgui.ListItem(label=channel + " ŽIVĚ")
        list_item.setInfo('video', {'title': channel + " ŽIVĚ",
                                    'plot': getProgram(channel, epg_data),
                                    'mediatype': 'video'})

        list_item.setArt(
            {'thumb': getLiveIcon(channel, live_stream_api), 'icon': getLiveIcon(channel, live_stream_api)})
        url = get_url(action='play_stream', stream=stream)
        list_item.setProperty('IsPlayable', 'true')

        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    list_item = xbmcgui.ListItem(label="Videoteka A-Z")
    url = get_url(action='archive')
    list_item.setProperty('IsPlayable', 'false')
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle)


def list_archive():
    xbmcplugin.setPluginCategory(_handle, 'Videotéka A-Z')
    xbmcplugin.setContent(_handle, 'videos')

    for category in ALPHABET:
        list_item = xbmcgui.ListItem(label=category)
        list_item.setInfo('video', {'title': category,
                                    'mediatype': 'video'})
        url = get_url(action='listing', category=category)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)


def list_videos(start_character):
    xbmcplugin.setPluginCategory(_handle, start_character)
    xbmcplugin.setContent(_handle, 'videos')
    search_url = search("https://www.tvnoe.cz/videoteka/az/" + start_character).data
    raw_html = BeautifulSoup(search_url, "html.parser")
    shows = raw_html.find_all("div", class_="noe-porady-prehled-porad")
    for show in shows:
        show_name = \
            show.find("div", style="display:block; width: 100%;color: #424753;font-weight: bold;").text.split(":")[
                0].strip()
        show_image = show.find("div", style="margin-bottom: 1rem;")
        show_image = "https://www.tvnoe.cz" + show_image.img["src"]
        show_link = "https://www.tvnoe.cz/videoteka/hledej?search=" + show_name
        list_item = xbmcgui.ListItem(label=show_name)

        list_item.setInfo('video', {'title': show_name,
                                    'mediatype': 'video'})
        list_item.setArt({'thumb': show_image, 'icon': show_image, 'fanart': show_image})
        url = get_url(action='show_episodes', show_url=show_link)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)


def list_episodes(show_url):
    xbmcplugin.setPluginCategory(_handle, 'Epizody')
    xbmcplugin.setContent(_handle, 'videos')
    search_url = search(show_url).data
    raw_html = BeautifulSoup(search_url, "html.parser")
    searched_shows = raw_html.find("div", class_="noe-videoteka-prehled-porady")
    shows = searched_shows.find_all("a")
    for show in shows:
        show_name = show.find("div", style="display:block; width: 100%;color: #424753;font-weight: bold;").text
        show_image = show.find("div", style="margin-bottom: 1rem;")
        show_image = "https://www.tvnoe.cz" + show_image.img["src"]
        episode_url = "https://www.tvnoe.cz/" + show["href"]
        list_item = xbmcgui.ListItem(label=show_name)

        list_item.setInfo('video', {'title': show_name,
                                    'mediatype': 'video'})
        list_item.setArt({'thumb': show_image, 'icon': show_image, 'fanart': show_image})

        list_item.setProperty('IsPlayable', 'true')

        url = get_url(action='play', video=episode_url)
        is_folder = False
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)


def play_video(path):
    page_cn = search(path).data
    vp = BeautifulSoup(page_cn, "html.parser")
    v_raw_src = vp.find("div", class_="container craplayer")
    v_raw_src_html = v_raw_src.decode_contents()
    pattern = re.compile(r"src:\s*'([^']*\.m3u8)'")
    matches = pattern.findall(v_raw_src_html)
    play_item = xbmcgui.ListItem(path=matches[0])
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def play_stream(path):
    xbmc.log(path)
    play_item = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'listing':
            list_videos(params['category'])
        elif params['action'] == 'show_episodes':
            list_episodes(params['show_url'])
        elif params['action'] == 'play_stream':
            play_stream(params['stream'])
        elif params['action'] == 'archive':
            list_archive()
        elif params['action'] == 'play':
            play_video(params['video'])
        else:

            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        list_categories()


if __name__ == '__main__':
    router(sys.argv[2][1:])
