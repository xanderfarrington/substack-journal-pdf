from playwright.sync_api import sync_playwright


def html_to_pdf(html: str, output_path: str):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.set_content(html, wait_until="networkidle")

        page.pdf(
            path=output_path,
            format="Letter",
            print_background=True,
            margin={
                "top": "0.6in",
                "right": "0.65in",
                "bottom": "0.65in",
                "left": "0.65in",
            },
            display_header_footer=True,
            header_template="<div></div>",
            footer_template="""
                <div style="font-size:8px; width:100%; text-align:center; color:#777;">
                    <span class="pageNumber"></span>
                </div>
            """,
        )

        browser.close()
