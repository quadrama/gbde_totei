# gbde_totei

gbde_totei is a python script to parse drama texts from [Projekt Gutenberg-
DE](https://gutenberg.spiegel.de/), put them into TEI format and locally save
the output TEI-XML file. TEI files created with this script *roughly* comply to
the general structure of the
[GerDraCor German Drama Corpus](https://github.com/quadrama/gerdracor), at
least so that they can be loaded and analyzed with the `loadDramaTEI`-function
of the R-library [DramaAnalysis](https://github.com/quadrama/DramaAnalysis).
Please be aware that the script is in an early stage of development and errors
are likely to occur for some dramas, as the html-structure of Projekt
Gutenberg-DE can suffer from inconsistencies. You are welcome to open issues
for any occuring errors.

## Requirements & Installation

No installation is needed -- you can simply run the script after cloning this
repository. It requires Python 3 with the packages *beatifulsoup4*, *lxml* and
*requests* installed. These requirements can be installed with pip from within
the repository folder (after cloning it) like so:
```bash
pip install -r requirements.txt
```
## Usage

Run `python gbde_totei.py -h` from the repository folder to show the following
help message:
```
usage: gbde_totei.py [-h] [-d DIR] [-at ACT_TRIGGER] [-st SCENE_TRIGGER]
                     start_url n_pages author drama

This script can be used to extract a drama from gutenberg.spiegel.de and
convert it into a valid XML file in TEI-format.

example use:
  python gbde_totei.py 'https://gutenberg.spiegel.de/buch/die-weber-9199/4' 5 'Hauptmann, Gerhart' 'Die Weber'

positional arguments:
  start_url             link to the gutenbergde-webpage that contains the start of the drama text
  n_pages               number of subsequent pages that need to be parsed
  author                author name in the format 'Lastname, Firstname(s)' or 'Name'
  drama                 drama title

optional arguments:
  -h, --help            show this help message and exit
  -d DIR, --dir DIR     directory where output is saved (default = current working directory)
  -at ACT_TRIGGER, --act_trigger ACT_TRIGGER
                        trigger word in heading that indicates a new act (default = 'Akt')
  -st SCENE_TRIGGER, --scene_trigger SCENE_TRIGGER
                        trigger word in heading that indicates a new scene (default = 'Szene')
```

## License
[GNU GPLv3](https://choosealicense.com/licenses/gpl-3.0/)
