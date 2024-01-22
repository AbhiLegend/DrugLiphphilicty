from flask import Flask, request, jsonify
from rdkit import Chem
from rdkit.Chem import AllChem, Draw
import numpy as np
import openvino.runtime as ov
import io
import os
import uuid

app = Flask(__name__)

# Load OpenVINO model
model_path = 'lipophilicity_openvino.xml'
core = ov.Core()
compiled_model = core.compile_model(model_path, "CPU")

# Global counter for image numbering
image_counter = 0

images_dir = os.path.join(os.getcwd(), 'images')
if not os.path.exists(images_dir):
    os.makedirs(images_dir)

def smiles_to_fp(smiles, n_bits=2048):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=n_bits)
    return np.array(fp)

def mol_to_image_file(mol):
    global image_counter
    if mol:
        image_counter += 1
        filename = f"molecule_{image_counter}.png"
        filepath = os.path.join(images_dir, filename)  # Use the images_dir path
        Draw.MolToFile(mol, filepath)
        return filepath
    return None

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    smiles = data.get('smiles')
    if not smiles:
        return jsonify({'error': 'No SMILES string provided'})

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return jsonify({'error': 'Invalid SMILES string'})

    fp = smiles_to_fp(smiles)
    if fp is None:
        return jsonify({'error': 'Could not generate fingerprint'})

    input_tensor = np.array([fp], dtype=np.float32)
    try:
        ov_input_tensor = ov.Tensor(input_tensor)
        result = compiled_model([ov_input_tensor])[0]
        prediction = result[0][0]
        prediction = float(prediction)  # Convert to native Python float
    except Exception as e:
        return jsonify({'error': f'Model inference failed: {str(e)}'})

    image_path = mol_to_image_file(mol)
    response = {'prediction': prediction}
    if image_path:
        response['image_path'] = image_path
    else:
        response['error'] = 'Failed to generate molecule image'

    return jsonify(response)

if __name__ == '__main__':
    # Make sure the 'images' directory exists
    if not os.path.exists('images'):
        os.makedirs('images')

    app.run(debug=True, port=5000)
