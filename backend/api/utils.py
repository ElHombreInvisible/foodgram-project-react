import platform
from io import BytesIO

import pdfkit


def create_pdf(html_page):
    if platform.system() == 'Windows':
        path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    else:
        config = None
    html = html_page.content.decode()
    pdf = pdfkit.from_string(html, configuration=config,
                             options={"enable-local-file-access": ""})
    return BytesIO(pdf)
