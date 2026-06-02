# Text Annotation Tool

A lightweight desktop GUI for labeling spans of text — built for creating
training data for NLP tasks (NER, span classification, token tagging). Pure
Python + Tkinter, no external services, no dependencies beyond the standard
library.

It was originally built to label job-advertisement text (skills, education,
positions, requirements) for an NLP pipeline, but nothing about it is
domain-specific — you supply your own documents, labels, and key bindings.

## Features

- Keyboard-driven labeling — bind any key to a label and color
- Adjustable context window around each string being labeled
- Manage **labels**, **key bindings**, and **contexts** through built-in dialogs
- Apply / remove labels in bulk
- Load and save annotation sessions to plain text files

## Requirements

- Python 3.x (Tkinter ships with most CPython installs; on Debian/Ubuntu:
  `sudo apt-get install python3-tk`)

## Usage

```bash
python annotator.py
```

Then use the menus to load a document set and a label/binding configuration.
See the [`examples/`](examples/) folder for the expected file formats:

| File | Purpose |
|------|---------|
| `sample_documents.txt` | The raw text records to annotate |
| `sample_labels`        | The list of label names |
| `sample_bindings`      | Key → label → foreground/background color mappings |
| `sample_contexts`      | Saved context configuration |

### Binding format

Each line maps a key to a label and two colors (foreground, background):

```
e	Education	white	red
h	Hard skills	red	green
p	Position	white	blue
```

## License

MIT — see [LICENSE](LICENSE).
