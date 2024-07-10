from fpdf import FPDF

lorem_ipsum = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed efficitur sem lectus, in tincidunt lectus suscipit id.

Suspendisse id dignissim nisl, in commodo justo. Donec cursus interdum euismod. Nullam eget urna libero. Donec dictum sodales urna, ac pellentesque ex pellentesque non.

Cras et tellus et augue egestas tincidunt. Aenean elit nisl, volutpat vitae dictum vitae, consequat at risus"""

pdf = FPDF()

pdf.add_page()

# write the big title
pdf.set_font("Times", "B", 50)
pdf.cell(w=pdf.epw, text="HEADLINE", align="c", new_x="LEFT", new_y="NEXT")

pdf.set_font("Times", "B", 30)
pdf.cell(
    w=pdf.epw,
    text="SUBTITLE HERE",
    align="c",
    new_x="LEFT",
    new_y="NEXT",
)

# the first article takes 2/3 of the page from here.
# save the "y" position to write the second article
articles_start = pdf.get_y()
article_width = pdf.epw * 2 / 3 - 2

# first article - image + headline + text in 2 columns
pdf.image(name="just-chillin.jpeg", w=article_width)

pdf.set_font("Times", "B", 20)
pdf.multi_cell(text="This is the first article's headline", w=article_width, align="c")

pdf.set_font("Times", "", 14)
with pdf.text_columns(
    text=lorem_ipsum,
    text_align="J",
    ncols=2,
    r_margin=(pdf.epw - article_width + pdf.r_margin),
    gutter=1,
) as cols:
    cols.write(lorem_ipsum)

# second article - 1/3 of the page
article_width = pdf.epw * 1 / 3
article_x_pos = (pdf.epw * 2 / 3) + pdf.l_margin

pdf.set_xy(x=article_x_pos, y=articles_start)

pdf.image(name="hiding.jpg", w=article_width)

pdf.set_font("Times", "B", 20)
pdf.set_x(article_x_pos)
pdf.multi_cell(text="This is the second article's headline", w=article_width, align="c")

pdf.set_font("Times", "", 14)
pdf.set_x(article_x_pos)
with pdf.text_columns(
    text=lorem_ipsum, text_align="J", ncols=1, l_margin=article_x_pos, gutter=1
) as cols:
    cols.write(lorem_ipsum)

# write output file
pdf.output("newspaper.pdf")
