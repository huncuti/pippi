from flask import Flask, render_template, request, redirect, url_for, send_file, session
import pandas as pd
import io
import logging
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generate and use a secure secret key

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load the data
file_path = "/Users/ircase/Desktop/Medical devices review all in one.xlsx"
df = pd.read_excel(file_path)

# Initialize counters
current_product_index = 0
decisions = []

@app.route('/')
def index():
    logging.debug('Rendering index.html')
    return render_template('index.html')

@app.route('/review', methods=['GET', 'POST'])
def review():
    global current_product_index

    if 'decided_yes' not in session:
        session['decided_yes'] = []
    if 'decided_no' not in session:
        session['decided_no'] = []
    if 'decided_maybe' not in session:
        session['decided_maybe'] = []

    logging.debug('Entering review route')

    if request.method == 'POST':
        decision = request.form.get('decision')
        device_name = df.iloc[current_product_index]['Device name']

        logging.debug(f'Received decision: {decision} for device: {device_name}')

        if decision:
            session['decided_no'] = [d for d in session['decided_no'] if d['Device name'] != device_name]
            session['decided_maybe'] = [d for d in session['decided_maybe'] if d['Device name'] != device_name]
            session['decided_yes'] = [d for d in session['decided_yes'] if d['Device name'] != device_name]

            if decision == 'yes':
                session['decided_yes'].append({'Device name': device_name})
                print(f"Added '{device_name}' to 'yes' category. Session: {session['decided_yes']}")
            elif decision == 'no':
                session['decided_no'].append({'Device name': device_name})
                print(f"Added '{device_name}' to 'no' category. Session: {session['decided_no']}")
            elif decision == 'maybe':
                session['decided_maybe'].append({'Device name': device_name})
                print(f"Added '{device_name}' to 'maybe' category. Session: {session['decided_maybe']}")

            decisions.append({'Device name': device_name, 'Decision': decision})
            current_product_index += 1
        else:
            current_product_index += 1
            return redirect(url_for('review'))

    try:
        product = df.iloc[current_product_index].to_dict()
        logging.debug(f'Sending product data: {product}')
    except IndexError:
        logging.debug('No more products, redirecting to summary page')
        return redirect(url_for('summary'))

    return render_template('review.html', product=product, current_product_index=current_product_index)

@app.route('/change_decision/<string:direction>')
def change_decision(direction):
    global current_product_index

    logging.debug(f'Received change decision request: {direction}')

    if direction == 'previous' and current_product_index > 0:
        current_product_index -= 1
        logging.debug('Moving to previous product')
    elif direction == 'next' and current_product_index < len(df) - 1:
        current_product_index += 1
        logging.debug('Moving to next product')

    return redirect(url_for('review'))

@app.route('/summary')
def summary():
    logging.debug('Rendering summary page')
    return render_template('summary.html', decided_category_yes=session.get('decided_yes', []),
                           decided_category_no=session.get('decided_no', []),
                           decided_category_maybe=session.get('decided_maybe', []))

@app.route('/download_data')
def download_data():
    df_export = df.copy()
    df_export['Decision'] = df_export['Device name'].map({d['Device name']: d['Decision'] for d in decisions})

    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df_export.to_excel(writer, sheet_name='Sheet1', index=False)
    writer._save()
    output.seek(0)

    logging.debug('Downloading data')
    return send_file(output, as_attachment=True, download_name='exported_data.xlsx')

@app.route('/library')
def library():
    logging.debug('Rendering library page')
    print(f"Yes: {session.get('decided_yes', [])}")
    print(f"No: {session.get('decided_no', [])}")
    print(f"Maybe: {session.get('decided_maybe', [])}")

    return render_template('library.html',
                           decided_yes=session.get('decided_yes', []),
                           decided_no=session.get('decided_no', []),
                           decided_maybe=session.get('decided_maybe', []))

if __name__ == '__main__':
    app.run(debug=True)
