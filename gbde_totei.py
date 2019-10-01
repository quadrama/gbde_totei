#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This script can be used to extract a drama from gutenberg.spiegel.de and
convert it into a valid XML file in TEI-format.

example use:
  python gbde_totei.py "https://gutenberg.spiegel.de/buch/die-weber-9199/4" 5 "Hauptmann, Gerhart" "Die Weber" """

import os
import argparse
import requests
import lxml
import bs4

class GutenbergHtmlToTei:
    """main class to transform html input from gutenberg.spiegel.de into TEI output"""

    # set namespaces
    TEI = "{http://www.tei-c.org/ns/1.0}"
    XML = "{http://www.w3.org/XML/1998/namespace}"
    NSM = {None : "http://www.tei-c.org/ns/1.0"}

    def __init__(self, author_name, drama_title, act_trigger, scene_trigger):
        self.author_name = author_name
        self.drama_title = drama_title
        self.act_trigger = act_trigger
        self.scene_trigger = scene_trigger
        self.tei, self.tei_body = self.initialize_tei()
        self.current_speaker = None
        self.current_act_n = 0
        self.current_act = None
        self.current_scene_n = 0
        self.current_scene = None
        self.last_elem = None

    def initialize_tei(self):
        """initializes the output TEI with basic structure and metadata"""

        root = lxml.etree.Element(self.TEI+"TEI", nsmap = self.NSM)
        teiHeader = lxml.etree.SubElement(root, self.TEI+"teiHeader")
        fileDesc = lxml.etree.SubElement(teiHeader, self.TEI+"fileDesc")
        titleStmt = lxml.etree.SubElement(fileDesc, self.TEI+"titleStmt")
        title = lxml.etree.SubElement(titleStmt, self.TEI+"title")
        title.text = self.drama_title
        author = lxml.etree.SubElement(titleStmt, self.TEI+"author")
        author.text = self.author_name
        profileDesc = lxml.etree.SubElement(teiHeader, self.TEI+"profileDesc")
        langUsage = lxml.etree.SubElement(profileDesc, self.TEI+"langUsage")
        language = lxml.etree.SubElement(langUsage, self.TEI+"language")
        language.set("ident", "de")
        language.set("usage", "100")
        language.text = "German"
        particDesc = lxml.etree.SubElement(profileDesc, self.TEI+"particDesc")
        listPerson = lxml.etree.SubElement(particDesc, self.TEI+"listPerson")
        text = lxml.etree.SubElement(root, self.TEI+"text")
        body = lxml.etree.SubElement(text, self.TEI+"body")
        return root, body

    def parse_page(self, soup):
        """parses single html page"""

        div_body = soup.find("div", attrs={"id":"gutenb"})
        for elem in div_body.children:
            if elem.name == "p":
                self.parse_paragraph(elem)
            elif elem.name in ["h" + str(n) for n in range(1,7)]:
                heading = elem.getText()
                if self.act_trigger in heading:
                    self.add_act()
                elif self.scene_trigger in heading:
                    self.add_scene()

    def parse_paragraph(self, p):
        """internal, parses paragraphs"""

        if p.has_attr("class"):
            p_type = p.get("class")[0]
            if p_type == "vers":
                self.add_lines(p)
            elif p_type == "stage":
                self.add_stage(p)
        else:
            for elem in p.children:
                if isinstance(elem, bs4.Tag):
                    if elem.name == "span":
                        elem_type = elem.get("class")[0]
                        # stage direction
                        if elem_type == "stage":
                            self.add_stage(elem)
                        # speaker name
                        elif elem_type == "speaker":
                            self.add_speaker(elem)
                        # stage direction inside speech
                        elif elem_type == "regie":
                            self.add_stage(elem, speaker=True)
                # speaker text
                elif isinstance(elem, bs4.NavigableString):
                    self.add_speakerText(elem)

    def add_act(self):
        """internal, adds a new act to TEI output"""

        self.current_act = lxml.etree.SubElement(self.tei_body, self.TEI+"div",
                                                 type="act")
        self.current_scene = None
        self.last_elem = self.current_act


    def add_scene(self):
        """internal, adds a new scene to TEI output"""

        # if there are no acts
        if self.current_act is None:
            self.current_scene = lxml.etree.SubElement(self.tei_body,
                                                       self.TEI+"div",
                                                       type="scene")
        else:
            self.current_scene = lxml.etree.SubElement(self.current_act,
                                                       self.TEI+"div",
                                                       type="scene")
        self.last_elem = self.current_scene


    def add_speaker(self, speaker_elem):
        """internal, adds a new sp-element to TEI output"""

        speaker_surface = speaker_elem.getText()
        speaker_id =  "#" + speaker_surface.lower().strip(".").replace(" ", "_")
        # if there are no scenes
        if self.current_scene is None:
            self.current_speaker = lxml.etree.SubElement(self.current_act,
                                                         self.TEI+"sp",
                                                         who=speaker_id)
        else:
            self.current_speaker = lxml.etree.SubElement(self.current_scene,
                                                         self.TEI+"sp",
                                                         who=speaker_id)
        speaker_surface_elem = lxml.etree.SubElement(self.current_speaker,
                                                     self.TEI+"speaker")
        speaker_surface_elem.text = speaker_surface.strip(".")
        self.last_elem = speaker_surface_elem

    def add_speakerText(self, speaker_text):
        """adds speaker text that is structured in paragraphs to TEI output"""

        # because of html-inconsistencies, leading punctuation needs to be added
        # to the last stage element if present
        if (speaker_text.startswith(", ") or speaker_text.startswith(". ")
            or speaker_text.startswith(": ")):
            if self.last_elem.tag == self.TEI+"stage":
                self.last_elem.text += speaker_text[0]
            speaker_text = speaker_text[2:]
        speaker_text = speaker_text.replace("\n", "")
        if self.current_speaker is not None:
            if len(speaker_text.strip()) > 1:
                p_elem = lxml.etree.SubElement(self.current_speaker,
                                               self.TEI+"p")
                p_elem.text = speaker_text.strip()
                self.last_elem = p_elem
            # because of html-inconsistencies, single characters need to be
            # added to the last stage element if present
            elif (len(speaker_text.strip()) == 1
                  and self.last_elem.tag == self.TEI+"stage"):
                self.last_elem.text += speaker_text.strip()

    def add_stage(self, stage, speaker=False):
        """internal, adds a stage direction to TEI output"""

        if speaker:
            stage_elem = lxml.etree.SubElement(self.current_speaker,
                                               self.TEI+"stage")
        else:
            if self.current_scene is None:
                stage_elem = lxml.etree.SubElement(self.current_act,
                                                   self.TEI+"stage")
            else:
                stage_elem = lxml.etree.SubElement(self.current_scene,
                                                   self.TEI+"stage")
        stage_elem.text = stage.getText().replace("\n", "")
        self.last_elem = stage_elem

    def add_lines(self, p_elem):
        """internal, adds speaker text that is structured in verses"""

        lg_element = lxml.etree.SubElement(self.current_speaker,
                                           self.TEI+"lg")
        lines = [elem for elem in p_elem.children
                 if not isinstance(elem, bs4.Tag)]
        for line in lines:
            if line.startswith(", ") or line.startswith(". "):
                line = line[2:]
            l_element = lxml.etree.SubElement(lg_element, self.TEI+"l")
            l_element.text = line.replace("\n", "").strip()
        self.last_elem = lg_element

    def add_listPerson(self):
        """fills and adds the listPerson-element to TEI output"""

        listPerson = self.tei.find(".//" + self.TEI+"listPerson")
        speaker_set = sorted(set([tag.text for tag in self.tei_body.iter()
                                  if tag.tag == self.TEI+"speaker"]))
        for speaker in speaker_set:
            person = lxml.etree.SubElement(listPerson, self.TEI+"person")
            person.set(self.XML+"id",
                       speaker.lower().replace(" ", "_").strip("."))
            persName = lxml.etree.SubElement(person, self.TEI+"persName")
            persName.text = speaker

    def write_to_file(self, dir):
        """writes output lxml-object to .xml-file"""

        output_string = lxml.etree.tostring(self.tei,
                                       pretty_print=True,
                                       xml_declaration=True,
                                       encoding='UTF-8')
        filename = (self.author_name.split(", ")[0].lower() + "_"
                    + self.drama_title.replace(" ", "_").lower() + ".xml")
        with open(os.path.join(dir, filename), "wb") as fh:
            fh.write(output_string)

################################################################################
################################################################################

if __name__ == "__main__":

    # parse user input
    arg_parser = argparse.ArgumentParser(description=__doc__,
                                         formatter_class=argparse.RawTextHelpFormatter)
    arg_parser.add_argument("start_url",
                            help="link to the gutenbergde-webpage that contains the start of the drama text")
    arg_parser.add_argument("n_pages", type=int,
                            help="number of subsequent pages that need to be parsed")
    arg_parser.add_argument("author",
                            help="author name in the format 'Lastname, Firstname(s)' or 'Name'")
    arg_parser.add_argument("drama", help="drama title")
    arg_parser.add_argument("-d", "--dir", default=os.getcwd(),
                            help="directory where output is saved (default = current working directory)")
    arg_parser.add_argument("-at", "--act_trigger", default="Akt",
                            help="trigger word in heading that indicates a new act (default = 'Akt')")
    arg_parser.add_argument("-st", "--scene_trigger", default="Szene",
                            help="trigger word in heading that indicates a new scene (default = 'Szene')")
    args = arg_parser.parse_args()

    # initialize object and parse pages
    tei_output = GutenbergHtmlToTei(args.author, args.drama, args.act_trigger,
                                    args.scene_trigger)
    start_n = int(args.start_url[-1])
    for i in range(args.n_pages):
        current_url = args.start_url[:-1] + str(start_n + i)
        r = requests.get(current_url)
        soup = bs4.BeautifulSoup(r.text, features="lxml")
        tei_output.parse_page(soup)

    # finalize output and write to file
    tei_output.add_listPerson()
    tei_output.write_to_file(args.dir)
