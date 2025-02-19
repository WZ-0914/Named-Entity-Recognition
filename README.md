# Named Entity Recognition (NER)

## Overview

Named Entity Recognition (NER) is a fundamental task in Natural Language Processing (NLP) that identifies and classifies named entities in text. Named entities typically include persons, organizations, locations, times, and quantities.

### Example:

#### Unannotated text:

```
Alex moved to Los Angeles to work for Universal Studios.
```

#### Annotated output:

```
[PER Alex] moved to [LOC Los Angeles] to work for [ORG Universal Studios].
```

In this example, "Alex" is recognized as a person, "Los Angeles" as a location, and "Universal Studios" as an organization.

## Dataset

This project utilizes the **CoNLL-2003** dataset, which was released as part of the CoNLL-2003 shared task on language-independent named entity recognition.

### Dataset Details:

- **Source:** Reuters Corpus (August 1996 - August 1997)
- **Tagging Method:** Tagged and chunked using the MBT tagger
- **Annotation:** Manually annotated at the University of Antwerp
- **Entity Categories:**
  - **PER**: Person names (e.g., "Alex")
  - **ORG**: Organizations (e.g., "Universal Studios")
  - **LOC**: Locations (e.g., "Los Angeles")
  - **MISC**: Miscellaneous (e.g., nationalities, events)

## BIO Tagging Scheme

The dataset follows the **BIO tagging scheme**, where:

- `B-TYPE`: Beginning of an entity (e.g., `B-PER` for "Alex")
- `I-TYPE`: Inside an entity (e.g., `I-LOC` for "Los Angeles")
- `O`: Not part of an entity

### Example Annotation:

#### Unannotated Text:

```
U.N. official Ekeus heads for Baghdad.
```

#### BIO Tagged Format:

```
B-ORG U.N. O official B-PER Ekeus O heads O for B-LOC Baghdad O.
```

Here, "U.N." is an organization, "Ekeus" is a person, and "Baghdad" is a location.

## Usage

1. Clone the repository:
   ```sh
   git clone https://github.com/your-repo-name.git
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Run the NER model:
   ```sh
   python ner_model.py
   ```

## Acknowledgments

- The **CoNLL-2003** dataset is widely used for NER research.
- The **BIO tagging scheme** follows Ramshaw and Marcus (1995).

##
