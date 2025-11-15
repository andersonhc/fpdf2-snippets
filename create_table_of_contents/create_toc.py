"""Demonstrates how to build a Table of Contents for an existing PDF.

The script inspects the outline/bookmarks of an existing PDF, generates a TOC
page with FPDF, and finally merges the TOC at the beginning of the document.
Every function is meant to be as explicit as possible so it can be used as a
tutorial reference.
"""

from pathlib import Path
from io import BytesIO
from typing import Tuple

from fpdf import FPDF, TextStyle, XPos, YPos, Align
from pypdf import PdfReader, PdfWriter
from pypdf.generic import Destination

HERE = Path(__file__).resolve().parent

SOURCE_PDF = HERE / ".pdf"
DEFAULT_OUTPUT = HERE / "FinalWithTOC.pdf"
DEFAULT_SKIP_BOOKMARKS = 4


class CreateTOC:
    """
    Generate a PDF Table of Contents and prepend it to an existing file.
    The TOC entries are linked to the original document's bookmarks.
    """

    # You can customize the text styles used for different bookmark depths here.
    # ex. depth_0, depth_1, etc.
    # If there is no specific style for a depth, "default" is used.
    TOC_TEXT_STYLES = {
        "title": TextStyle(
            font_family="Helvetica",
            font_size_pt=18,
            color="#0000ff",
            font_style="B",
            b_margin=18,
        ),
        "depth_0": TextStyle(
            font_family="Helvetica",
            font_size_pt=12,
            font_style="B"
        ),
        "default": TextStyle(
            font_family="Helvetica",
            font_size_pt=12,
            font_style=""
        ),
    }

    def __init__(
        self, source_pdf: Path, destination_pdf: Path, skip_bookmarks: int = 4
    ):
        """Read the PDF, build the TOC, and write the merged document.
        Args:
            source_pdf: Path to the PDF that already contains bookmarks.
            destination_pdf: Where the merged output should be written.
            skip_bookmarks: Number of outline entries to skip;
        """
        source_pdf = Path(source_pdf)
        destination_pdf = Path(destination_pdf)

        self.reader = PdfReader(source_pdf)

        # Flatten the nested bookmark structure and drop the number set on skip_bookmarks.
        self.bookmarks = self.extract_bookmarks(self.reader.outline)[skip_bookmarks:]
        self.bookmarks.sort(key=lambda b: b["page"])

        # Start by assuming the TOC fits on a single page. We may have to
        # regenerate it with the updated count below.
        self.toc_pages = 1
        toc_pdf, number_of_pages = self.create_toc()
        if number_of_pages != self.toc_pages:
            self.toc_pages = number_of_pages
            toc_pdf, _ = self.create_toc()

        # Merge the TOC and original PDF into the destination file
        self.merge_pdfs(toc_pdf, destination_pdf)

    def extract_bookmarks(self, outlines, depth: int = 0):
        """Recursively flatten PyPDF's outline representation."""
        bookmarks = []
        for item in outlines:
            if isinstance(item, list):
                bookmarks.extend(self.extract_bookmarks(item, depth + 1))
            elif isinstance(item, Destination):
                title = item.title
                page_number = self.reader.get_destination_page_number(item)
                bookmarks.append(
                    {
                        "depth": depth,
                        "title": title,
                        "page": page_number,
                    }
                )
        return bookmarks

    def get_text_style(self, depth: int) -> TextStyle:
        """Return the appropriate text style for a given bookmark depth."""
        style = self.TOC_TEXT_STYLES.get(f"depth_{depth}", None)
        return style if style else self.TOC_TEXT_STYLES["default"]

    def create_toc(self) -> Tuple[BytesIO, int]:
        """Create the TOC PDF in memory and report how many pages it uses."""
        toc = FPDF()
        toc.add_page()

        with toc.use_text_style(self.TOC_TEXT_STYLES["title"]):
            toc.set_title("Table of Contents")
            toc.cell(0, 10, "Table of Contents", align="C")

        for bookmark in self.bookmarks:
            self.render_toc_item(toc, bookmark)

        number_of_pages = toc.page_no()
        # Output the TOC page to memory
        toc_buffer = BytesIO()
        toc.output(toc_buffer)
        toc_buffer.seek(0)
        return toc_buffer, number_of_pages

    def render_toc_item(self, toc: FPDF, item: dict):
        """Based on fpdf.outline.TableOfContents"""

        depth = item["depth"]
        item_name = item["title"]
        item_page_number = str(
            item["page"] + self.toc_pages + 1
        )  # FPDF uses 1-based page numbering
        text_style = self.get_text_style(depth)
        link_name = f'dest{item["page"]}'

        toc.add_link(name=link_name)

        level_indent = 7.5  # indentation level per depth
        line_spacing = 1.5

        # render the text on the left
        with toc.use_text_style(text_style):
            indent = depth * level_indent
            toc.set_x(toc.l_margin + indent)
            toc.multi_cell(
                w=toc.epw - indent,
                text=item_name,
                new_x=XPos.END,
                new_y=YPos.LAST,
                link=f"#{link_name}",
                align=Align.J,
                h=toc.font_size * line_spacing,
            )

            # fill in-between with dots
            clearance_margin = toc.c_margin * 2
            current_x = toc.get_x()
            page_label_length = toc.get_string_width(item_page_number)
            in_between_space = (
                toc.w - current_x - page_label_length - clearance_margin - toc.r_margin
            )
            if in_between_space < 0:
                # no space to render the page number - go to next line
                toc.ln()
                toc.set_x(toc.l_margin + indent)
                current_x = toc.get_x()
                in_between_space = toc.w - current_x - page_label_length - toc.r_margin
            in_between = ""
            if in_between_space > 0:
                while (
                    toc.get_string_width(in_between) + clearance_margin
                    < in_between_space
                ):
                    in_between += "."

                if len(in_between) > 1:
                    toc.multi_cell(
                        w=toc.w - current_x - toc.r_margin,
                        text=in_between[:-1],
                        new_x=XPos.END,
                        new_y=YPos.LAST,
                        link=f"#{link_name}",
                        align=Align.L,
                        h=toc.font_size * line_spacing,
                    )

            # render the page number on the right
            toc.set_x(current_x)
            toc.multi_cell(
                w=toc.w - current_x - toc.r_margin,
                text=item_page_number,
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
                link=f"#{link_name}",
                align=Align.R,
                h=toc.font_size * line_spacing,
            )

    def merge_pdfs(self, toc_buffer: BytesIO, destination_pdf: Path):
        """Prepend the TOC pages and recreate the bookmarks as named links."""
        toc_reader = PdfReader(toc_buffer)
        writer = PdfWriter()
        for toc_page in toc_reader.pages:
            writer.add_page(toc_page)

        # Append the original PDF after the newly created TOC.
        writer.append(self.reader)

        for bookmark in self.bookmarks:
            bookmark_page = bookmark["page"]
            destination_page = bookmark_page + self.toc_pages
            destination_name = f"dest{bookmark_page}"
            writer.add_named_destination(destination_name, page_number=destination_page)

        with open(destination_pdf, "wb") as out_file:
            writer.write(out_file)

        print("PDF GENERATED")


if __name__ == "__main__":
    CreateTOC(
        source_pdf=SOURCE_PDF,
        destination_pdf=DEFAULT_OUTPUT,
        skip_bookmarks=DEFAULT_SKIP_BOOKMARKS,
    )
