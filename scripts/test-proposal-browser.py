#!/usr/bin/env python3
"""Check the shared HTML starter or a served proposal. No product/provider calls.

Requires Playwright (Chromium) and pdftotext. Screenshots/PDFs are optional local
diagnostics, not golden images or proof of architectural correctness.
"""
import argparse
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import tempfile
from threading import Thread
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def serve(directory):
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, *_args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(directory)))
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/'
    finally:
        server.shutdown()
        server.server_close()
        worker.join()


def fixture():
    cells = ''.join(f'''<tr role="row"><td role="cell" data-label="Construct">Boundary{i}</td>
      <td role="cell" data-label="Reason">Preserve the authority boundary while moving the existing
      decision into one owner. A long declaration {"LongDeclaration" * 8} must remain readable.</td>
      <td role="cell" data-label="Evidence">Verify positive and negative cases before cutover.</td></tr>'''
      for i in range(8))
    disclosures = ''.join(f'''<details><summary>Evidence {i}</summary><div class="detail">
      <p>EvidenceMarker{i:02d} belongs in the printed artifact even when this disclosure is closed.</p>
      </div></details>''' for i in range(6))
    body = f'''<section id="decision" class="card"><h2>ShellPolicyCoordinator responsibility</h2><p>Approve characterization only.
      The later authority contract remains pending. Compare with a smaller consolidation before choosing it.</p></section>
      <section id="flow"><h2>Decision flow</h2><div class="grid"><div class="card"><h3>Current</h3>
      <div class="flow"><div class="step">Collect facts</div><div class="arrow">↓</div>
      <div class="step">Evaluate</div><div class="arrow">↓</div><div class="step">Return</div></div></div>
      <div class="card"><h3>Proposed</h3><div class="flow"><div class="step">Capture immutable facts</div>
      <div class="arrow">↓</div><div class="step">One decision</div><div class="arrow">↓</div>
      <div class="step">Host applies result</div></div></div></div></section>
      <section id="inventory"><h2>Responsibility inventory</h2><p>Inspect the cells on a narrow screen.</p>
      <div class="card table-scroll"><table class="stack-table" role="table"><thead role="rowgroup">
      <tr role="row"><th role="columnheader">Construct</th><th role="columnheader">Reason</th>
      <th role="columnheader">Evidence</th></tr></thead><tbody role="rowgroup">{cells}</tbody></table></div></section>
      <section id="evidence"><h2>Verification evidence</h2>{disclosures}
      <pre><code>verify --filter '{"BoundaryCase|" * 65}FinalCase'</code></pre></section>'''
    template = (ROOT / 'skills/simplify/assets/proposal.html').read_text()
    for key, value in {'title':'Proposal regression fixture', 'subtitle':'Synthetic data only.',
                       'status':'Not implementation approval', 'navigation':'<a href="#decision">Decision</a>',
                       'body':body}.items():
        template = template.replace('{{' + key + '}}', value)
    assert '{{' not in template
    return template


def check_layout(page):
    problems = page.evaluate('''() => {
      const bad = [];
      if (document.documentElement.scrollWidth > innerWidth + 1) bad.push('document overflow');
      for (const el of document.querySelectorAll('table,pre,.table-scroll')) {
        if (el.getBoundingClientRect().height && el.scrollWidth > el.clientWidth + 2)
          bad.push(el.tagName + ': hidden horizontal content');
      }
      for (const td of document.querySelectorAll('.stack-table td')) {
        if (!td.dataset.label) bad.push('missing mobile column label');
        const r = td.getBoundingClientRect();
        if (r.height && (r.left < -1 || r.right > innerWidth + 1)) bad.push('cell outside viewport');
      }
      return bad;
    }''')
    assert not problems, problems


def check_print(pdf, markers=()):
    result = subprocess.check_output(['pdftotext', '-bbox', str(pdf), '-'], text=True)
    root = ET.fromstring(result)
    pages = root.findall('.//{*}page')
    all_words = []
    for index, page in enumerate(pages):
        words = page.findall('.//{*}word')
        all_words.extend(w.text or '' for w in words)
        # A regression sentinel for stranded headings, not a target page count.
        if 0 < index < len(pages) - 1:
            assert len(words) >= 35, f'Nearly empty interior print page {index + 1}: {len(words)} words'
        width, height = float(page.get('width')), float(page.get('height'))
        for word in words:
            assert -1 <= float(word.get('xMin')) <= float(word.get('xMax')) <= width + 1, word.text
            assert -1 <= float(word.get('yMin')) <= float(word.get('yMax')) <= height + 1, word.text
    for marker in markers:
        assert marker in all_words, f'Print lost disclosure content: {marker}'
    return len(pages)


def audit(browser, url, output, markers=()):
    page = browser.new_page(viewport={'width':1440,'height':1000})
    errors, remote = [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
    origin = urlsplit(url).netloc
    page.on('request', lambda request: remote.append(request.url)
            if urlsplit(request.url).scheme in ('http','https') and urlsplit(request.url).netloc != origin else None)
    response = page.goto(url, wait_until='networkidle')
    assert response.status == 200
    assert page.locator('main').count() == 1 and page.locator('h1').count() == 1
    assert not page.eval_on_selector_all('a[href^="#"]',
        '(links)=>links.filter(a=>!document.getElementById(decodeURIComponent(a.hash.slice(1)))).map(a=>a.hash)')
    page.keyboard.press('Tab')
    assert page.locator('.skip').evaluate('(e)=>e===document.activeElement')
    page.keyboard.press('Enter')
    for item in page.locator('details').all():
        item.locator('summary').focus()
        page.keyboard.press('Enter')
        assert item.evaluate('(e)=>e.open')
        page.keyboard.press('Enter')
        assert not item.evaluate('(e)=>e.open')
    for width in (1440, 768, 390, 320):
        page.set_viewport_size({'width':width,'height':900})
        for expanded in (False, True):
            page.locator('details').evaluate_all('(items,open)=>items.forEach(e=>e.open=open)', expanded)
            check_layout(page)
            if not expanded:
                page.evaluate('window.scrollTo(0,0)')
                page.screenshot(path=str(output / f'initial-{width}.png'))
        page.screenshot(path=str(output / f'expanded-{width}.png'), full_page=True)
        if page.locator('table').count():
            page.locator('table').first.screenshot(path=str(output / f'table-{width}.png'))
    page.locator('details').evaluate_all('(items)=>items.forEach(e=>e.open=false)')
    page.set_viewport_size({'width':1440,'height':1000})
    page.emulate_media(media='print')
    assert page.locator('details .detail').evaluate_all('(items)=>items.every(e=>e.getBoundingClientRect().height>0)')
    pdf = output / 'proposal.pdf'
    page.pdf(path=str(pdf), format='A4', print_background=True)
    pages = check_print(pdf, markers)
    assert not errors, errors
    assert not remote, remote
    page.close()
    print(f'PASS: {url} — 4 widths, expanded/closed content, keyboard, anchors, {pages} print pages')


def negative_controls(browser, url, output):
    page = browser.new_page(viewport={'width':390,'height':900})
    page.goto(url)
    page.add_style_tag(content='pre {white-space:pre !important;}')
    try:
        check_layout(page)
    except AssertionError as error:
        assert 'hidden horizontal content' in str(error), error
    else:
        raise AssertionError('Checker accepted horizontally hidden commands')
    page.reload()
    page.emulate_media(media='print')
    page.add_style_tag(content='details .detail {display:none !important;}')
    pdf = output / 'deliberately-broken.pdf'
    page.pdf(path=str(pdf), format='A4')
    try:
        check_print(pdf, ['EvidenceMarker00'])
    except AssertionError as error:
        assert 'Print lost disclosure content' in str(error), error
    else:
        raise AssertionError('Checker accepted missing printed evidence')
    page.close()
    print('PASS: negative controls reject hidden commands and missing print evidence')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', help='Optional existing presentation URL; never starts a product application')
    parser.add_argument('--output-dir', type=Path, help='Keep screenshots/PDFs here; otherwise use a temporary directory')
    parser.add_argument('--browser-executable', help='Use an installed Chromium instead of Playwright Chromium')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='systematize-browser-') as tmp, sync_playwright() as p:
        directory = Path(tmp)
        output = args.output_dir or directory / 'diagnostics'
        output.mkdir(parents=True, exist_ok=True)
        browser = p.chromium.launch(**({'executable_path':args.browser_executable} if args.browser_executable else {}))
        try:
            if args.url:
                audit(browser, args.url, output)
            else:
                (directory / 'index.html').write_text(fixture())
                with serve(directory) as url:
                    audit(browser, url, output, [f'EvidenceMarker{i:02d}' for i in range(6)])
                    negative_controls(browser, url, output)
        finally:
            browser.close()


if __name__ == '__main__':
    main()
