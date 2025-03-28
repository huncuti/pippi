const express = require('express');
const multer = require('multer');
const xlsx = require('xlsx');
const path = require('path');
const app = express();
const port = 3000;

// Set up the public folder for static files
app.use(express.static('public'));

// Set up Multer for file uploads
const upload = multer({ dest: 'uploads/' });

// Handle file uploads
app.post('/upload', upload.single('excelFile'), (req, res) => {
  try {
    const filePath = req.file.path;
    const workbook = xlsx.readFile(filePath);
    const sheetNames = workbook.SheetNames;
    const data = xlsx.utils.sheet_to_json(workbook.Sheets[sheetNames[0]]);

    // For testing purposes, let's redirect to the review page with dummy data
    res.redirect('/review');
  } catch (error) {
    console.error(error);
    res.status(500).send('Error processing the uploaded file.');
  }
});

// Add this route for testing the review form
app.get('/review', (req, res) => {
  // Dummy product data
  const products = [
    { base: 'Base1', deviceName: 'Device1', productGroup: 'Group1', reasonForRecall: 'Reason1' },
    { base: 'Base2', deviceName: 'Device2', productGroup: 'Group2', reasonForRecall: 'Reason2' },
    { base: 'Base3', deviceName: 'Device3', productGroup: 'Group3', reasonForRecall: 'Reason3' }
    // Add more dummy data as needed
  ];

  res.send(products);
});

// Start the server
app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});

