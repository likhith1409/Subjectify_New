from flask import Flask, render_template, request, send_from_directory, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# Define the directory where uploaded PDFs and thumbnail images will be stored
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure SQLAlchemy database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Ensure the UPLOAD_FOLDER directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    note_title = db.Column(db.String(100), nullable=False)
    contributor_name = db.Column(db.String(100), nullable=False)
    pdf_filename = db.Column(db.String(100), unique=True, nullable=False)
    thumbnail_filename = db.Column(db.String(100), unique=True, nullable=False)
    like_count = db.Column(db.Integer, default=0)  # Add this line to define the like_count column


# Create the database tables if they don't exist
with app.app_context():
    db.create_all()

# Routes...

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/note_suggestions')
def note_suggestions():
    search_query = request.args.get('query', '')  # Get the search query from the URL parameter 'query'
    if search_query:
        # Filter notes by title containing the search query
        notes = Note.query.filter(Note.note_title.ilike(f'%{search_query}%')).all()
        # Extract note titles for suggestions
        suggestions = [note.note_title for note in notes]
        return jsonify(suggestions)
    else:
        return jsonify([])  # If no query provided, return an empty list

@app.route('/about')
def info():
    return render_template('about.html')

@app.route('/pdfs')
def about():
    search_query = request.args.get('q', '')  # Get the search query from the URL parameter 'q'
    if search_query:
        notes = Note.query.filter(Note.note_title.ilike(f'%{search_query}%')).all()  # Filter notes by title
    else:
        notes = Note.query.all()
    
    # Get love counts for each note
    love_counts = {note.id: note.like_count for note in notes}
    
    return render_template('pdfs.html', notes=notes, love_counts=love_counts)

@app.route('/search', methods=['POST'])
def search():
    search_query = request.form['search-input']
    return redirect(url_for('about', q=search_query))

@app.route('/contribute', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Get form data
        note_title = request.form['note-title']
        contributor_name = request.form['contributor-name']
        pdf_file = request.files['pdf-upload']
        thumbnail_file = request.files['pdf-thumbnail']

        # Save the PDF file and thumbnail image
        if pdf_file and thumbnail_file:
            pdf_filename = secure_filename(pdf_file.filename)
            thumbnail_filename = secure_filename(thumbnail_file.filename)

            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
            thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_filename)

            # Create a new note instance
            new_note = Note(
                note_title=note_title,
                contributor_name=contributor_name,
                pdf_filename=pdf_filename,
                thumbnail_filename=thumbnail_filename
            )
            # Add the new note to the database session
            db.session.add(new_note)

            # Save the files
            pdf_file.save(pdf_path)
            thumbnail_file.save(thumbnail_path)

            # Commit changes to the database
            db.session.commit()

        # Redirect to the PDFs page after submission
        return redirect(url_for('about'))

    # If it's a GET request, just render the contribute page
    return render_template('contribute.html')

@app.route('/download/<filename>')
def download_pdf(filename):
    # Serve the PDF file for download
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/uploads/<filename>')
def uploaded_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/update_love_count', methods=['POST'])
def update_love_count():
    note_id = request.json['note_id']
    note = Note.query.get(note_id)
    if note:
        note.like_count += 1
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False})

if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host='192.168.1.14', port=5000, debug=True, threaded=True)



    


