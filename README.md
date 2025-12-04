# Python PDF Invoice Generator with Database Connection and Email Support

This is a Flask-based web application that generates professional PDF invoices for e-commerce businesses. It includes database connectivity for storing invoice data and supports email notifications.

## Features

- **Web Interface**: User-friendly web form for entering invoice details
- **PDF Generation**: Creates styled PDF invoices using ReportLab
- **Database Integration**: Stores invoice data in MySQL database
- **Product Management**: Supports multiple products with fixed pricing
- **Tax Calculation**: Automatic service tax calculation
- **Payment Tracking**: Tracks amount paid and calculates change
- **Modern Design**: Clean, professional invoice layout
- **Cross-platform**: Works on Windows, macOS, and Linux

## Requirements

- Python 3.6+
- MySQL database
- Web browser

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd "Python Invoice Generator with Database Connection"
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up MySQL database:
   - Create a database named `invoice_db`
   - Create a table named `invoices` with the following structure:
     ```sql
     CREATE TABLE invoices (
         id INT AUTO_INCREMENT PRIMARY KEY,
         Company_Name VARCHAR(255),
         Company_Address TEXT,
         Email_ID VARCHAR(255),
         Amount DECIMAL(10,2),
         Final_Amount DECIMAL(10,2),
         Product TEXT,
         Amount_Paid DECIMAL(10,2),
         Change DECIMAL(10,2)
     );
     ```

4. Configure environment variables (optional):
   - `DB_HOST`: Database host (default: localhost)
   - `DB_USER`: Database username (default: root)
   - `DB_PASSWORD`: Database password (default: empty)
   - `DB_NAME`: Database name (default: invoice_db)
   - `DB_TABLE`: Table name (default: invoices)

## Usage

1. Run the application:
   ```
   python server.py
   ```

2. Open your web browser and navigate to `http://127.0.0.1:8080/`

3. Fill out the invoice form:
   - Enter company name and address
   - Enter customer name and phone
   - Select products and quantities
   - Enter service tax percentage
   - Enter amount paid

4. Click "Submit" to generate the invoice

5. The PDF invoice will be saved in the `INVOICE/` folder

## Project Structure

```
Python Invoice Generator with Database Connection/
├── server.py              # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── templates/
│   └── index.html         # Web interface template
├── INVOICE/               # Generated PDF invoices
└── static/                # Static files (CSS, JS, images)
```

## Dependencies

- **Flask**: Web framework
- **ReportLab**: PDF generation library
- **PyMySQL**: MySQL database connector

## Product Pricing

The application includes fixed pricing for the following products:
- Pens: $0.10
- Counterbook: $1.05
- Erasers: $0.24
- Shoe Brush: $0.76
- Candies: $0.14

## Database Schema

The `invoices` table stores the following information:
- Company name and address
- Customer email
- Invoice amount and final amount (including tax)
- Product details
- Amount paid and change

## Customization

### Adding New Products

To add new products, update the `PRODUCT_PRICES` dictionary in `server.py`:

```python
PRODUCT_PRICES = {
    'Pens': 0.10,
    'Counterbook': 1.05,
    'Erasers': 0.24,
    'Shoe Brush': 0.76,
    'Candies': 0.14,
    'New Product': 2.50  # Add new product here
}
```

### Modifying Invoice Layout

The PDF layout can be customized by modifying the `create_pdf_pharma()` function in `server.py`. This function uses ReportLab to draw the invoice elements.

### Changing Database Configuration

Update the database configuration variables at the top of `server.py` or use environment variables.

## Troubleshooting

### Database Connection Issues

- Ensure MySQL is running
- Check database credentials
- Verify table structure matches the schema

### PDF Generation Errors

- Ensure ReportLab is installed correctly
- Check file permissions for the INVOICE folder
- Verify all required fields are filled in the form

### Web Interface Not Loading

- Check that Flask is running on the correct port
- Ensure no other applications are using port 8080
- Try accessing via `http://localhost:8080/`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Please check the license file for details.

## Support

For issues or questions, please create an issue in the GitHub repository.
