import re
from bs4 import BeautifulSoup
import requests
import time
import tinysoundfont

# The api calls are done according to this project: https://github.com/victor-cortez/Library-of-Babel-Python-API

SHORT_PAUSE: float = 0.15
NOTE_DURATION: float = 0.15


def browse(hexagon, wall, shelf, volume, title=""):
    # The title is expandable, in the inputs of the fuction you can see very easily what you need
    # Just formatting the volume variable to fulfill the protocol the site wants
    if int(volume) <= 9:
        volume = "0" + volume
    form = {"hex": hexagon, "wall": wall, "shelf": shelf,
            "volume": volume, "page": "", "title": title}
    url = "https://libraryofbabel.info/download.cgi"
    text = requests.post(url, data=form)
    # Cleaning the raw text, so "content" turns into the pure book
    content = text.text[len(title) + 2::].rsplit("\n", 4)[0]
    return content


class SearchResult:
    def __init__(self, title, hexagon, wall, shelf, volume):
        self.title = title
        self.hexagon = hexagon
        self.wall = wall
        self.shelf = shelf
        self.volume = volume

    def __repr__(self) -> str:
        return f"Book named {self.title}, on wall {self.wall}, on shelf {self.shelf}, in volume {self.volume}. On hexagon {self.hexagon}"


def process_search_result(result):
    title = result.find("b").text
    info = result.find("a", {"class": "intext"})["onclick"]
    data_points = re.findall(r"'(\w+)'", info)
    if len(data_points) != 5:
        raise Exception("Unexpected book address format")
    hexagon, wall, shelf, volume = data_points[0:4]
    return SearchResult(title, hexagon, wall, shelf, volume,)


def search(book_text):
    form = {"find": book_text, "method": "t"}
    url = "https://libraryofbabel.info/search.cgi"
    text = requests.post(url, data=form)
    content_soup = BeautifulSoup(text.text, features="html.parser")
    search_raw_results = content_soup.find_all(
        "pre", {"class": "textsearch", "style": "text-align: left"})
    return [process_search_result(raw_result) for raw_result in search_raw_results]

# Function to convert the input string into notes


def string_to_notes(input_string):
    notes = []
    for char in input_string:
        char = char.lower()
        if char.isalpha():
            # Map lowercase letters to piano notes dynamically
            note_index = ord(char) - ord('a')  # Map 'a' to 0, 'b' to 1, etc.
            notes.append(int(note_index/25 * 42 + 42))
        elif char == ' ':
            # Add a short pause
            notes.append(None)
        elif char == ',':
            # Add a longer pause
            notes.append(None)
            notes.append(None)
        elif char == '.':
            # Add a real longer pause
            notes.append(None)
            notes.append(None)
            notes.append(None)
    return notes

# Play the composition


def play_composition(composition):
    for note in composition:
        if note is None:
            time.sleep(SHORT_PAUSE)
        else:
            synth.noteon(0, note, 127)
            time.sleep(NOTE_DURATION)
            synth.noteoff(0, note)


def get_compo_text(title: str):
    # Get the composition text from https://libraryofbabel.info/
    result: SearchResult = search(title)[0]
    return result, browse(result.hexagon, result.wall, result.shelf, result.volume, title=result.title)


def play(title: str, first_page, last_page):
    # Get the composition text
    compo_infos, composition_string = get_compo_text(title)
    composition_string = composition_string[(first_page-1)*3200:last_page*3200]
    print(compo_infos)
    print()
    print()
    print(
        f"Playing {compo_infos.title.title()} from the babel library", end="")
    print(f" from page {first_page} to page {last_page}." if first_page !=
          last_page else f" on page {first_page}.")
    # Convert string to notes
    composition_notes = string_to_notes(composition_string)
    # Play the composition
    play_composition(composition_notes)


if __name__ == '__main__':
    # Load syth
    synth = tinysoundfont.Synth()
    sfid = synth.sfload("FluidR3_GM.sf2")
    synth.program_select(0, sfid, 0, 0)
    synth.start()

    # Getting query data
    title = input("Enter title (under 26 char): ")
    assert len(title) <= 26, "Title is too long"
    first_page = int(input("Fisrt page to play (1-410): "))
    assert 1 <= first_page <= 410, "Invalid page"
    last_page = int(input("Last page to play (1-410): "))
    assert 1 <= first_page <= last_page <= 410, "Invalid page"

    # Playing the composition
    play(title, first_page, last_page)

    # Unloading synth
    synth.stop
