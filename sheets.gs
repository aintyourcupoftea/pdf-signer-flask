function onEdit(e) {
  var sheet = e.source.getActiveSheet();
  var range = e.range;
  
  // Check if the edited cell is in column C (3rd column)
  if (range.getColumn() == 3) {
    var status = range.getValue();
    
    // Proceed if status is "Completed"
    if (status === "Completed") {
      var row = range.getRow();
      var pdfLink = sheet.getRange(row, 2).getValue();  // Column B

      // Extract the file ID from the link
      var pdfFileId = extractFileId(pdfLink);
      
      if (pdfFileId) {
        try {
          callFlaskAPI(pdfFileId, row); // Pass the row number to callFlaskAPI
        } catch (error) {
          Logger.log('API call failed: ' + error.message);
        }
      } else {
        Logger.log('Invalid PDF link in column D at row ' + row);
      }
    }
  }
}

function extractFileId(link) {
  var match = link.match(/[-\w]{25,}/);
  return match ? match[0] : null;
}

function callFlaskAPI(pdfFileId, row) {
  var url = 'https://pdf-signer-flask.onrender.com/api/sign_pdf';
  var signatureImageId = '1QvXKknBph2fScddG5osQK-4dABCSCj0a';  // Replace with your signature image ID

  var pdfFile = DriveApp.getFileById(pdfFileId);
  var signatureImage = DriveApp.getFileById(signatureImageId);

  var formData = {
    'pdf_file': pdfFile.getBlob(),
    'signature_image': signatureImage.getBlob()
  };
  
  var options = {
    'method': 'post',
    'payload': formData
  };

  var response = UrlFetchApp.fetch(url, options);
  if (response.getResponseCode() !== 200) {
    throw new Error('Failed to sign PDF: ' + response.getContentText());
  }
  
  var signedBlob = response.getBlob();
  saveSignedPdf(pdfFile, signedBlob, row); // Pass the row number to saveSignedPdf
}

function saveSignedPdf(originalPdfFile, signedBlob, row) {
  var originalPdfName = originalPdfFile.getName();
  var signedPdfName = originalPdfName.replace(/\.pdf$/, "_signed.pdf");

  var parentFolder = originalPdfFile.getParents().next();

  // Create or get the "Signed PDFs" folder
  var signedPdfsFolder;
  var signedPdfsFolders = parentFolder.getFoldersByName("Signed PDFs");
  if (signedPdfsFolders.hasNext()) {
    signedPdfsFolder = signedPdfsFolders.next();
  } else {
    signedPdfsFolder = parentFolder.createFolder("Signed PDFs");
  }

  // Save the signed PDF in the "Signed PDFs" folder
  var signedPdf = signedPdfsFolder.createFile(signedBlob).setName(signedPdfName);

  // Get the URL of the signed PDF
  var signedPdfUrl = signedPdf.getUrl();

  // Get the sheet
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();

  // Paste the signed PDF URL in column D of the same row
  sheet.getRange(row, 4).setValue(signedPdfUrl);

  Logger.log('Signed PDF file created with ID: ' + signedPdf.getId());
}

