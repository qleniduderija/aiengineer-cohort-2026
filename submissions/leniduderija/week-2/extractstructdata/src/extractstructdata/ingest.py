import requests
import trafilatura
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from .errors import IngestionError

USER_AGENT = "extractstructdata/0.1 (https://github.com/qleniduderija/aiengineer-cohort-2026; educational coursework project)"

def read_pdf(path):

    final_text = ''

    try:
        reader = PdfReader(path)
        for page in reader.pages:
            text = page.extract_text() or ""
            final_text += ' ' + text

        if not final_text.strip():
            raise IngestionError(f"No extractable text found in PDF: {path}")

        return final_text.strip()

    except FileNotFoundError as e:
        raise IngestionError(e) from e
    except PdfReadError as e:
        raise IngestionError(e) from e

def fetch_url(url):

    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()

        text = trafilatura.extract(response.text)

        if text is None:
            raise IngestionError(f"Could not extract article content from: {url}")

        return text

    except requests.exceptions.HTTPError as e:
        raise IngestionError(e) from e
    except requests.exceptions.Timeout as e:
        raise IngestionError(e) from e
    except requests.exceptions.ConnectionError as e:
        raise IngestionError(e) from e
