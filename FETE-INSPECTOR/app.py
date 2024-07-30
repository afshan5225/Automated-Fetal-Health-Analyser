import os
from flask import Flask, render_template, request
import spacy
import easyocr

app = Flask(__name__)

# Set the upload folder
app.config['UPLOAD_FOLDER'] = 'uploads'

# Load the spaCy model
nlp = spacy.load(r"C:\Users\USER\Desktop\FETE-INSPECTOR\model-best")

# Reference ranges for fetal health parameters
reference_ranges = {
    "First Trimester Scan Report": {
        "TRIMESTER": "First Trimester Scan Report",
        "LIQUOR": "Normal",
        "CARDIAC ACTIVITY": "present",
        "FETAL HEART BEAT": (110, 160),  # bpm
        "CROWN LUMP LENGTH": (43, 60),  # mm
        "BIPARIETAL DIAMETER": (17, 42),  # mm
        "HEAD CIRCUMFERENCE": (60, 80),  # mm
        "ABDOMINAL CIRCUMFERENCE": (50, 60),  # mm
    },
    "2/3 Trimester Scan Report": {
        "TRIMESTER": "2/3 Trimester Scan Report",
        "LIQUOR": "Normal",
        "CARDIAC ACTIVITY": "present",
        "FETAL HEART BEAT": (120, 180),  # Heartbeat range in beats per minute
        "CROWN LUMP LENGTH": (115, 400),  # Length in millimeters
        "BIPARIETAL DIAMETER": (45, 88),  # Diameter in millimeters
        "HEAD CIRCUMFERENCE": (160, 240),  # Circumference in millimeters
        "ABDOMINAL CIRCUMFERENCE": (110, 190),  # Circumference in millimeters
        "TRANSVERSE CEREBELLAR DIAMETER": (15, 25)  # Diameter in millimeters
}
}
# Function to reverse the entity dictionary
def reverse_dict(entity_dict):
    reversed_dict = {value: key for key, value in entity_dict.items()}
    return reversed_dict

# Function to assess fetal health condition
def assess_fetal_health(reversed_dict):
    trimester = reversed_dict.get("TRIMESTER")
    if trimester == "First Trimester Scan Report":
        ranges = reference_ranges["First Trimester Scan Report"]
    elif trimester == "2/3 Trimester Scan Report":
        ranges = reference_ranges["2/3 Trimester Scan Report"]
    else:
        return "Unknown trimester"

    in_range = True
    error_messages = []

    # Iterate over the keys and values of the reference ranges dictionary
    for label, reference_value in ranges.items():
        # Check if the extracted entity exists in the data
        if label in reversed_dict:
            entity = reversed_dict[label]
            # Convert entity to float if it's numeric
            try:
                entity = float(entity)
            except ValueError:
                pass  # Handle non-numeric values gracefully

            if isinstance(reference_value, tuple):  # Check if it's a range
                if not (reference_value[0] <= entity <= reference_value[1]):
                    in_range = False
                    error_messages.append(f"{label}: {entity} is out of range {reference_value}")
            else:  # Check if it's a string
                if entity != reference_value:
                    in_range = False
                    error_messages.append(f"{label}: {entity} is not {reference_value}")
        else:
            in_range = False
            error_messages.append(f"{label} is missing from the extracted data.")

    # Output the result
    if in_range:
        return "Fetus is in good condition"
    else:
        return "Fetus is not in good condition. Issues found: " + ", ".join(error_messages)

# Route for the home page
@app.route('/')
def home():
    return render_template('index.html')

# Route to handle image upload and process
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return render_template('index.html', message='No file part')
    
    file = request.files['file']
    if file.filename == '':
        return render_template('index.html', message='No image selected')

    if file:
        # Save the uploaded file to the UPLOAD_FOLDER
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        # Now the file should be saved in the UPLOAD_FOLDER
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        # Read uploaded image
        reader = easyocr.Reader(['en'])  # Adjust language(s) as needed
        extracted_text = extract_text_from_image(image_path, reader)
        doc = nlp(extracted_text)
        # Extract entities and their labels
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        entity_dict = {entity[0]: entity[1] for entity in entities}
        reversed_dict = reverse_dict(entity_dict)
        # Assess fetal health condition
        health_condition = assess_fetal_health(reversed_dict)
        return render_template('result.html', entities=entities, health_condition=health_condition)

# Function to extract text from image
def extract_text_from_image(image_path, reader):
    text = reader.readtext(image_path, detail=1)
    extracted_text = ""
    for line in text:
        extracted_text += line[1] + " "
    return extracted_text

if __name__ == '__main__':
    app.run(debug=True)
