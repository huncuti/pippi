from flask import Flask, render_template, request, redirect, url_for, send_file, session
import pandas as pd
import io
import logging
import secrets
import threading
import time
import openpyxl
import os

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
logging.basicConfig(level=logging.DEBUG)

file_path = "/Users/ircase/Desktop/Medical devices review all in one.xlsx"
try:
    df = pd.read_excel(file_path)
except FileNotFoundError:
    logging.error(f"File not found: {file_path}")
    df = pd.DataFrame()
except Exception as e:
    logging.error(f"An error occurred while loading the file: {e}")
    df = pd.DataFrame()

current_product_index = 0
decisions = []
DECISIONS_FILE = 'data/decisions.xlsx'
os.makedirs('data', exist_ok=True)

def save_decisions_to_excel():
    global decisions
    if decisions:
        try:
            if os.path.exists(DECISIONS_FILE):
                workbook = openpyxl.load_workbook(DECISIONS_FILE)
                sheet = workbook.active
            else:
                workbook = openpyxl.Workbook()
                sheet = workbook.active
                sheet.append(['Product ID', 'Decision'])

            for decision in decisions:
                sheet.append([decision['Product ID'], decision['Decision']])

            workbook.save(DECISIONS_FILE)
            logging.debug("Decisions saved to Excel.")
            #Do not clear decisions here, as it is needed for the download function.
        except Exception as e:
            logging.error(f"Error saving decisions to Excel: {e}")

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
        try:
            product_id = df.iloc[current_product_index]['Product ID']
        except KeyError:
            logging.error("Product ID column not found in excel file.")
            product_id = "Product ID not found"

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

            decisions.append({'Product ID': product_id, 'Decision': decision})
            save_decisions_to_excel()
            current_product_index += 1
        else:
            current_product_index += 1
            return redirect(url_for('review'))

    try:
        product = df.iloc[current_product_index].to_dict()
        logging.debug(f'Sending product data: {product}')
    except IndexError:
        logging.debug('No more products, redirecting to library page')
        return redirect(url_for('library'))

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

@app.route('/download_data')
def download_data():
    df_export = df.copy()
    decision_map = {}
    for item in session.get('decided_yes', []) :
        decision_map[item['Device name']] = 'yes'
    for item in session.get('decided_no', []) :
        decision_map[item['Device name']] = 'no'
    for item in session.get('decided_maybe', []) :
        decision_map[item['Device name']] = 'maybe'

    if 'Device name' in df_export.columns:
        df_export['Decision'] = df_export['Device name'].map(decision_map)
    else:
        logging.error("Device name column not found in df_export.")
        df_export['Decision'] = "Device name column not found."
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df_export.to_excel(writer, sheet_name='Sheet1', index=False)
    writer._save()
    output.seek(0)

    logging.debug('Downloading data')
    return send_file(output, as_attachment=True, download_name='exported_data.xlsx')

if __name__ == '__main__':
    app.run(debug=True)
