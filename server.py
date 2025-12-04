import os
import sys
import datetime
import time
import logging
import webbrowser
import threading
from flask import Flask, render_template, request
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
import textwrap
import pymysql


app = Flask(__name__)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'invoice_db')
DB_TABLE = os.getenv('DB_TABLE', 'invoices')

# Product prices dictionary
PRODUCT_PRICES = {
    'Pens': 0.10,
    'Counterbook': 1.05,
    'Erasers': 0.24,
    'Shoe Brush': 0.76,
    'Candies': 0.14
}

# Basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')




@app.route("/")
def main():
    # Render template if present, otherwise return a minimal fallback page
    try:
        return render_template("index.html")
    except Exception:
        logging.warning('Template index.html not found, returning fallback HTML')
        return ("<html><body><h1>Invoice Generator</h1>"
                "<p>Template not found. Use the form endpoint POST / to submit invoice data.</p></body></html>")



# createpdf function to create a Invoice PDF
def create_pdf(companynamepdf, companyaddresspdf, amountpdf, staxpdf, emailpdf, timestamppdf, canvas_module, datepdf, finalstaxpdf, productpdf):
    # Save invoice into a project-local INVOICE folder so it's cross-platform
    invoice_dir = os.path.join(APP_ROOT, 'INVOICE')
    os.makedirs(invoice_dir, exist_ok=True)
    filename = f"Invoice ({timestamppdf}).pdf"
    path = os.path.join(invoice_dir, filename)
    # Create a styled invoice with background, logo, item table and footer
    c = canvas_module.Canvas(path, pagesize=letter)
    width, height = letter
    margin = 50

    # Page background (light brown)
    bg_color = colors.HexColor('#D2B48C')  # tan/brown
    c.setFillColor(bg_color)
    c.rect(0, 0, width, height, stroke=0, fill=1)

    # Header bar (darker brown)
    header_height = 90
    header_color = colors.HexColor('#6B3E26')
    c.setFillColor(header_color)
    c.rect(margin, height - margin - header_height, width - 2 * margin, header_height, fill=1, stroke=0)

    # Logo (top-left) - look for logo.png or logo.jpg in project root
    logo_path_png = os.path.join(APP_ROOT, 'logo.png')
    logo_path_jpg = os.path.join(APP_ROOT, 'logo.jpg')
    logo_drawn = False
    try:
        if os.path.exists(logo_path_png):
            c.drawImage(logo_path_png, margin + 10, height - margin - 65, width=100, height=60, preserveAspectRatio=True, mask='auto')
            logo_drawn = True
        elif os.path.exists(logo_path_jpg):
            c.drawImage(logo_path_jpg, margin + 10, height - margin - 65, width=100, height=60, preserveAspectRatio=True, mask='auto')
            logo_drawn = True
    except Exception:
        logging.warning('Could not draw logo image')

    # Company name & address in header (if no logo we still show name)
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 18)
    name_x = margin + (120 if logo_drawn else 10)
    c.drawString(name_x, height - margin - 30, companynamepdf or 'Company Name')
    c.setFont('Helvetica', 8)
    addr_lines = (companyaddresspdf or '').split('\n')
    for i, line in enumerate(addr_lines[:3]):
        c.drawString(name_x, height - margin - 48 - (i * 10), line)

    # Invoice metadata on right
    c.setFont('Helvetica-Bold', 14)
    c.drawRightString(width - margin - 10, height - margin - 30, 'INVOICE')
    c.setFont('Helvetica', 9)
    c.drawRightString(width - margin - 10, height - margin - 48, f'Date: {datepdf}')
    c.drawRightString(width - margin - 10, height - margin - 64, f'Invoice #: {timestamppdf}')

    # Item table header
    table_top = height - margin - header_height - 30
    c.setFillColor(colors.black)
    c.setFont('Helvetica-Bold', 10)
    col_item_x = margin + 10
    col_qty_x = width - margin - 200
    col_unit_x = width - margin - 120
    col_total_x = width - margin
    c.drawString(col_item_x, table_top, 'Item/Description')
    c.drawRightString(col_qty_x + 20, table_top, 'Qty')
    c.drawRightString(col_unit_x + 40, table_top, 'Unit Price')
    c.drawRightString(col_total_x, table_top, 'Total')
    c.setLineWidth(0.8)
    c.line(margin, table_top - 4, width - margin, table_top - 4)

    # Item rows - this app only supports a single line currently; show product as description
    c.setFont('Helvetica', 10)
    y = table_top - 20
    # If product contains multiple lines, wrap naively
    product_text = str(productpdf or '')
    # show one line of product description
    c.drawString(col_item_x, y, product_text[:60])

    # Qty, unit price, total
    try:
        amt = float(amountpdf)
    except Exception:
        amt = 0.0
    qty = 1
    unit_price = amt
    line_total = round(qty * unit_price, 2)
    c.drawRightString(col_qty_x + 20, y, str(qty))
    c.drawRightString(col_unit_x + 40, y, f"{unit_price:,.2f}")
    c.drawRightString(col_total_x, y, f"{line_total:,.2f}")

    # Totals area (right side)
    try:
        stax = float(staxpdf)
    except Exception:
        stax = 0.0
    subtotal = round(line_total, 2)
    tax_amt = round(subtotal * (stax / 100.0), 2)
    try:
        final_amt = float(finalstaxpdf)
    except Exception:
        final_amt = round(subtotal + tax_amt, 2)

    totals_x = width - margin - 260
    totals_y = y - 10
    c.setFont('Helvetica', 10)
    c.drawString(totals_x + 10, totals_y + 40, 'Subtotal:')
    c.drawRightString(totals_x + 240, totals_y + 40, f"{subtotal:,.2f}")
    c.drawString(totals_x + 10, totals_y + 20, f'Service Tax ({stax:.0f}%):')
    c.drawRightString(totals_x + 240, totals_y + 20, f"{tax_amt:,.2f}")
    c.setFont('Helvetica-Bold', 12)
    c.drawString(totals_x + 10, totals_y, 'Total:')
    c.drawRightString(totals_x + 240, totals_y, f"{final_amt:,.2f}")

    # Thank you message + company address at bottom
    footer_y = margin + 40
    c.setFont('Helvetica-Bold', 12)
    c.setFillColor(colors.black)
    c.drawCentredString(width / 2, footer_y + 20, 'Thank you')
    c.setFont('Helvetica', 9)
    addr = companyaddresspdf or ''
    # Draw company address centered below thank you
    addr_lines = addr.split('\n') if addr else []
    for i, line in enumerate(addr_lines[:3]):
        c.drawCentredString(width / 2, footer_y - (i * 12), line)

    # Save
    c.save()
    logging.info('Created PDF: %s', path)
    return path


def create_pdf_pharma(companyname, companyaddress, amount, stax, email, timestamp, canvas_module, date, final_amount, products, quantities, amount_paid=None, change=None, customername=None, customerphone=None):
    """Create a modern, aesthetic booklet-style invoice PDF for e-commerce business.

    - Gradient header with professional colors
    - Clean white background with elegant borders
    - Dynamic company branding
    - Enhanced typography and spacing
    - Subtle watermark and visual elements
    - E-commerce specific elements like order confirmation
    """
    invoice_dir = os.path.join(APP_ROOT, 'INVOICE')
    os.makedirs(invoice_dir, exist_ok=True)
    filename = f"Invoice ({timestamp}).pdf"
    path = os.path.join(invoice_dir, filename)

    c = canvas_module.Canvas(path, pagesize=letter)
    width, height = letter
    margin = 50

    # Clean white background
    c.setFillColor(colors.white)
    c.rect(0, 0, width, height, stroke=0, fill=1)

    # Elegant border with rounded corners effect
    c.setStrokeColor(colors.HexColor('#E8F4F8'))
    c.setLineWidth(2)
    c.roundRect(margin/2, margin/2, width - margin, height - margin, 8, stroke=1, fill=0)

    # Modern gradient header (blue to green)
    header_h = 90
    # Blue gradient background
    c.setFillColor(colors.HexColor('#2563EB'))
    c.rect(margin, height - margin - header_h, width - 2 * margin, header_h, fill=1, stroke=0)
    # Green accent strip
    c.setFillColor(colors.HexColor('#10B981'))
    c.rect(margin, height - margin - header_h, width - 2 * margin, 8, fill=1, stroke=0)

    # Logo with better positioning
    logo_png = os.path.join(APP_ROOT, 'logo.png')
    logo_jpg = os.path.join(APP_ROOT, 'logo.jpg')
    logo_drawn = False
    try:
        if os.path.exists(logo_png):
            c.drawImage(logo_png, margin + 15, height - margin - header_h + 15, width=120, height=60, preserveAspectRatio=True, mask='auto')
            logo_drawn = True
        elif os.path.exists(logo_jpg):
            c.drawImage(logo_jpg, margin + 15, height - margin - header_h + 15, width=120, height=60, preserveAspectRatio=True, mask='auto')
            logo_drawn = True
    except Exception:
        logging.warning('Logo draw failed')

    # Dynamic company name and tagline
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 22)
    name_x = margin + (140 if logo_drawn else 15)
    company_display = companyname or 'Your E-commerce Store'
    c.drawString(name_x, height - margin - 35, company_display)
    c.setFont('Helvetica', 11)
    c.drawString(name_x, height - margin - 55, 'Premium Online Shopping Experience')

    # Invoice title with modern styling
    c.setFont('Helvetica-Bold', 18)
    c.setFillColor(colors.HexColor('#1F2937'))
    c.drawRightString(width - margin - 10, height - margin - 30, 'INVOICE')
    c.setFont('Helvetica', 10)
    c.setFillColor(colors.HexColor('#6B7280'))
    c.drawRightString(width - margin - 10, height - margin - 50, f'Date: {date}')
    c.drawRightString(width - margin - 10, height - margin - 68, f'Invoice #: {timestamp}')

    # Order confirmation note (e-commerce specific)
    c.setFillColor(colors.HexColor('#10B981'))
    c.setFont('Helvetica-Bold', 10)
    c.drawString(margin + 10, height - margin - header_h - 25, '✓ Order Confirmed - Thank you for your purchase!')

    # Enhanced Bill To section
    bill_box_y = height - margin - header_h - 50
    c.setFillColor(colors.HexColor('#F8FAFC'))
    c.roundRect(margin, bill_box_y - 70, width - 2 * margin - 220, 70, 5, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor('#E2E8F0'))
    c.setLineWidth(1)
    c.roundRect(margin, bill_box_y - 70, width - 2 * margin - 220, 70, 5, stroke=1, fill=0)

    c.setFillColor(colors.HexColor('#1F2937'))
    c.setFont('Helvetica-Bold', 11)
    c.drawString(margin + 12, bill_box_y - 20, 'Bill To:')
    c.setFont('Helvetica', 10)
    c.setFillColor(colors.HexColor('#374151'))
    c.drawString(margin + 12, bill_box_y - 38, customername or 'Customer Name')
    c.drawString(margin + 12, bill_box_y - 52, customerphone or 'Customer Phone')

    # Payment info box
    c.setFillColor(colors.HexColor('#F1F5F9'))
    c.roundRect(width - margin - 210, bill_box_y - 70, 210, 70, 5, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor('#CBD5E1'))
    c.roundRect(width - margin - 210, bill_box_y - 70, 210, 70, 5, stroke=1, fill=0)
    c.setFillColor(colors.HexColor('#475569'))
    c.setFont('Helvetica-Bold', 10)
    c.drawString(width - margin - 195, bill_box_y - 20, 'Payment Terms:')
    c.setFont('Helvetica', 9)
    c.drawString(width - margin - 195, bill_box_y - 38, 'Due upon receipt')
    c.drawString(width - margin - 195, bill_box_y - 52, 'Payment Method: Online')

    # Enhanced table with better styling
    table_top = bill_box_y - 140  # Added more space after bill box for better separation
    header_height = 28  # 1cm height for header box (28 points ≈ 1cm)
    gap_below_header = 4  # 0.15cm gap below header (4 points ≈ 0.15cm)
    row_h = 20

    # Table header with specific height (1cm)
    c.setFillColor(colors.HexColor('#E0F2FE'))
    c.roundRect(margin, table_top, width - 2 * margin, header_height, 3, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#0F172A'))
    c.setFont('Helvetica-Bold', 10)
    col_x = [margin + 10, margin + 280, margin + 360, width - margin - 70, width - margin]
    c.drawString(col_x[0], table_top + 8, 'Item / Description')
    c.drawRightString(col_x[1] + 30, table_top + 8, 'Qty')
    c.drawRightString(col_x[2] + 30, table_top + 8, 'Unit Price')
    c.drawRightString(col_x[3] + 30, table_top + 8, 'Line Total')

    # Item rows with alternating background - start after 0.5cm gap
    c.setFont('Helvetica', 10)
    row_top = table_top - header_height - gap_below_header
    line_height = 18

    current_y = row_top
    subtotal = 0.0

    if products and quantities:
        for idx, (prod, qty) in enumerate(zip(products, quantities)):
            description = prod.strip()
            wrapped_lines = textwrap.wrap(description, width=45)

            for i, wline in enumerate(wrapped_lines):
                # Alternating row colors
                if (idx + i) % 2 == 0:
                    c.setFillColor(colors.HexColor('#FAFAFA'))
                else:
                    c.setFillColor(colors.white)
                c.rect(margin, current_y - 6, width - 2 * margin, line_height + 4, fill=1, stroke=0)

                c.setFillColor(colors.HexColor('#1F2937'))
                c.drawString(col_x[0], current_y + 2, wline)

                if i == 0:
                    unit_price = PRODUCT_PRICES.get(prod, 0.0)
                    line_total = round(qty * unit_price, 2)
                    subtotal += line_total
                    c.drawRightString(col_x[1] + 30, current_y + 2, str(qty))
                    c.drawRightString(col_x[2] + 30, current_y + 2, f"${unit_price:,.2f}")
                    c.drawRightString(col_x[3] + 30, current_y + 2, f"${line_total:,.2f}")
                current_y -= line_height
    else:
        # Fallback for single product if no products/quantities provided
        description = (product or 'Premium Product').strip()
        wrapped_lines = textwrap.wrap(description, width=45)

        for i, wline in enumerate(wrapped_lines):
            # Alternating row colors
            if i % 2 == 0:
                c.setFillColor(colors.HexColor('#FAFAFA'))
            else:
                c.setFillColor(colors.white)
            c.rect(margin, current_y - 6, width - 2 * margin, line_height + 4, fill=1, stroke=0)

            c.setFillColor(colors.HexColor('#1F2937'))
            c.drawString(col_x[0], current_y + 2, wline)

            if i == 0:
                qty = 1
                try:
                    unit_price = float(amount)
                except Exception:
                    unit_price = 0.0
                line_total = round(qty * unit_price, 2)
                subtotal = line_total
                c.drawRightString(col_x[1] + 30, current_y + 2, str(qty))
                c.drawRightString(col_x[2] + 30, current_y + 2, f"${unit_price:,.2f}")
                c.drawRightString(col_x[3] + 30, current_y + 2, f"${line_total:,.2f}")
            current_y -= line_height

    # Table borders
    items_bottom = current_y + line_height
    c.setStrokeColor(colors.HexColor('#E2E8F0'))
    c.setLineWidth(0.8)
    c.roundRect(margin, table_top, width - 2 * margin, (table_top - items_bottom) + row_h + 6, 3, stroke=1, fill=0)

    # Enhanced totals section with more space
    try:
        staxf = float(stax)
    except Exception:
        staxf = 0.0
    tax_amt = round(subtotal * (staxf / 100.0), 2)
    try:
        total_amt = float(final_amount)
    except Exception:
        total_amt = round(subtotal + tax_amt, 2)

    totals_w = 240
    totals_h = 80
    totals_x = width - margin - totals_w
    totals_y = items_bottom - totals_h - 35  # Added more space after table

    # Totals box with gradient
    c.setFillColor(colors.HexColor('#F8FAFC'))
    c.roundRect(totals_x, totals_y, totals_w, totals_h, 5, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor('#CBD5E1'))
    c.roundRect(totals_x, totals_y, totals_w, totals_h, 5, stroke=1, fill=0)

    c.setFillColor(colors.HexColor('#374151'))
    c.setFont('Helvetica', 10)
    c.drawString(totals_x + 12, totals_y + 56, 'Subtotal:')
    c.drawRightString(totals_x + totals_w - 12, totals_y + 56, f"${subtotal:,.2f}")
    c.drawString(totals_x + 12, totals_y + 36, f'Tax ({staxf:.0f}%):')
    c.drawRightString(totals_x + totals_w - 12, totals_y + 36, f"${tax_amt:,.2f}")
    c.setFillColor(colors.HexColor('#10B981'))
    c.setFont('Helvetica-Bold', 12)
    c.drawString(totals_x + 12, totals_y + 12, 'Total:')
    c.drawRightString(totals_x + totals_w - 12, totals_y + 12, f"${total_amt:,.2f}")
    c.setFillColor(colors.HexColor('#374151'))
    c.setFont('Helvetica', 10)
    c.drawString(totals_x + 12, totals_y - 8, 'Amount Paid:')
    c.drawRightString(totals_x + totals_w - 12, totals_y - 8, f"${amount_paid:,.2f}")
    c.drawString(totals_x + 12, totals_y - 28, 'Change:')
    c.drawRightString(totals_x + totals_w - 12, totals_y - 28, f"${change:,.2f}")

    # Signature section with better styling
    sig_x = margin + 20
    sig_y = totals_y - 50
    c.setStrokeColor(colors.HexColor('#6B7280'))
    c.setLineWidth(1)
    c.line(sig_x, sig_y, sig_x + 200, sig_y)
    c.setFillColor(colors.HexColor('#6B7280'))
    c.setFont('Helvetica', 9)
    c.drawString(sig_x, sig_y - 15, 'Authorized Signature')

    # Enhanced footer with watermark effect
    footer_y = sig_y - 60

    # Subtle watermark with logo
    logo_path = os.path.join(APP_ROOT, '.webp')
    try:
        c.saveState()
        c.setFillAlpha(0.1)  # Low opacity for watermark effect
        c.translate(width/2, height/2)
        c.rotate(45)
        c.drawImage(logo_path, -100, -100, width=200, height=200, preserveAspectRatio=True, mask='auto')
        c.restoreState()
    except Exception:
        logging.warning('Could not draw watermark logo')

    # Thank you message
    c.setFillColor(colors.HexColor('#10B981'))
    c.setFont('Helvetica-Bold', 14)
    c.drawCentredString(width / 2, footer_y + 25, 'Thank you for shopping with us!')

    # Company address
    c.setFillColor(colors.HexColor('#6B7280'))
    c.setFont('Helvetica', 9)
    addr_lines = (companyaddress or '').split('\n') if companyaddress else []
    for i, line in enumerate(addr_lines[:3]):
        c.drawCentredString(width / 2, footer_y - (i * 12), line)

    # E-commerce footer note
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#9CA3AF'))
    c.drawCentredString(width / 2, footer_y - 50, 'For any queries, please contact our customer support team.')

    c.save()
    logging.info('Created enhanced e-commerce PDF: %s', path)
    return path


# addtodatabase function to add data to a mysql database
def addtodatabase(companynamedatabase, companyaddressdatabase, amountdatabase, emaildatabase, finalstaxdatabase, productdatabase, amount_paid=None, change=None):
    # Connect to the database
    # Skip DB insert if environment variables not set
    if not (DB_USER and DB_NAME and DB_TABLE):
        logging.warning('Database credentials/table not set in environment - skipping DB insert')
        return

    connection = pymysql.connect(host=DB_HOST,
                                 user=DB_USER,
                                 password=DB_PASSWORD,
                                 db=DB_NAME,
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    try:
        with connection.cursor() as cursor:
            # Create a new record
            sql = f"INSERT INTO `{DB_TABLE}` (`Company_Name`,`Company_Address`,`Email_ID`, `Amount`, Final_Amount, Product, Amount_Paid, Change) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (str(companynamedatabase), str(companyaddressdatabase), str(emaildatabase), str(amountdatabase), str(finalstaxdatabase), str(productdatabase), str(amount_paid), str(change)))
        connection.commit()
        logging.info('Inserted record into DB table %s', DB_TABLE)
    except Exception:
        logging.exception('Failed to insert into database')
    finally:
        connection.close()








@app.route("/", methods=["POST"])
def Create():
    target = os.path.join(APP_ROOT)
    # Use .get to avoid KeyError and validate inputs
    companyname = request.form.get('CompanyName', '').strip()
    companyaddress = request.form.get('CompanyAddress', '').strip()
    customername = request.form.get('CustomerName', '').strip()
    customerphone = request.form.get('CustomerPhone', '').strip()
    amount_raw = request.form.get('Amount', '0').strip()
    stax_raw = request.form.get('STax', '0').strip()
    date = time.strftime("%d/%m/%Y")

    # Collect products and quantities
    products = []
    quantities = []
    for i in range(1, 6):
        product = request.form.get(f'Product{i}', '').strip()
        quantity_raw = request.form.get(f'Quantity{i}', '0').strip()
        if product and quantity_raw:
            try:
                quantity = int(float(quantity_raw))
                if quantity > 0:
                    products.append(product)
                    quantities.append(quantity)
            except Exception:
                pass

    # Validate numeric values
    try:
        stax = float(stax_raw)
    except Exception:
        stax = 0.0

    # Get Amount Paid
    amount_paid_raw = request.form.get('AmountPaid', '0').strip()
    try:
        amount_paid = float(amount_paid_raw)
    except Exception:
        amount_paid = 0.0

    # Use a filename-safe timestamp (no colons) and place invoice in project INVOICE folder
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    os.makedirs(os.path.join(APP_ROOT, 'INVOICE'), exist_ok=True)

    # Calculate total amount based on products and fixed prices
    total_amount = 0.0
    for prod, qty in zip(products, quantities):
        price = PRODUCT_PRICES.get(prod, 0.0)
        total_amount += qty * price
    finalstax = total_amount + (total_amount * (stax / 100))

    # Calculate change
    change = amount_paid - finalstax

    try:
        # Use the pharmaceutical-styled invoice generator
        pdf_path = create_pdf_pharma(companyname, companyaddress, str(total_amount), str(stax), '', timestamp, canvas, date, str(finalstax), products, quantities, amount_paid, change, customername, customerphone)
        # For database, store a summary of products
        product_summary = ', '.join(products) if products else 'No products'
        try:
            addtodatabase(companyname, companyaddress, total_amount, '', finalstax, product_summary, amount_paid, change)
        except Exception as db_e:
            logging.warning('Database insertion failed: %s', str(db_e))
        message = f'Invoice created: {os.path.basename(pdf_path)}'
        logging.info(message)
        return render_template('index.html', message=message)
    except Exception as e:
        logging.exception('Error handling Create request')
        return render_template('index.html', error=str(e))


if __name__ == "__main__":
    # Configure where to open the browser. Use localhost so the browser can access the local server.
    HOST = '0.0.0.0'
    PORT = 8080
    URL = f"http://127.0.0.1:{PORT}/"
    DEBUG = True

    # Open the default web browser after a short delay so the server has time to start.
    def _open_browser_delayed():
        try:
            # Small sleep to allow the server to bind to the port
            time.sleep(1)
            webbrowser.open(URL)
            logging.info('Opened default browser to %s', URL)
        except Exception:
            logging.exception('Failed to open browser')

    # When Flask debug mode with reloader is enabled, the process is spawned twice.
    # Only open the browser in the reloader child process to avoid duplicates.
    if DEBUG and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # Parent process: do not open browser, just start server (the reloader will spawn the child)
        app.run(host=HOST, port=PORT, debug=DEBUG)
    else:
        # Child process or non-debug run: start a thread to open the browser and run the server.
        threading.Thread(target=_open_browser_delayed, daemon=True).start()
        app.run(host=HOST, port=PORT, debug=DEBUG)
