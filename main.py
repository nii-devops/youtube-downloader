
from pytube import YouTube, Playlist
import os
from io import BytesIO
import io
#import zipfile
from datetime import date, datetime
from flask import Flask, render_template, redirect, url_for, flash, send_from_directory, send_file, Response, stream_with_context
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
# Import your forms from the forms.py
from forms import  RegisterForm, LoginForm, URLForm, PlaylistForm, ContactForm, AudioForm
import pathlib
# Import dotenv
from dotenv import load_dotenv
import smtplib


load_dotenv('.env')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI')

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


# Create a user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

# SMTP CREDENTIALS
gmail_smtp = ("smtp.gmail.com")
port = 587

my_email = os.getenv('MY_EMAIL')
email_password = os.getenv('EMAIL_PASSWORD')

# Flask-Bootstrap object to load forms
Bootstrap5(app)
CKEditor(app)

gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)


#######################
### DATABASE MODELS ###
########################

# Create User DB Table
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    # Create a relationship between User table and Downloaded File table
    downloaded_files = db.relationship('DownloadedFile', backref='user', lazy='dynamic')

    # Create a relationship between User table and Downloaded File table
    messages = db.relationship('Message', backref='user', lazy='dynamic')

    def __repr__(self):
        return f"User('{self.f_name}', '{self.l_name}', '{self.email}')"


NOW = datetime.now()

class DownloadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(1000), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=NOW.replace(microsecond=0))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(250), nullable=False)
    message = db.Column(db.String(1500), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)


with app.app_context():
    db.create_all()



##################################
# <===    ROUTES    ===> #########
# ################################

"""
@app.route('/', methods=['get', 'post'])
def home():
    form = URLForm()
    if form.validate_on_submit():
        try:
            url = form.url.data
            DOWNLOAD_PATH = (pathlib.Path.home()/"Downloads")

            # Create YouTube object
            yt = YouTube(url)

            # Get the highest resolution
            stream = yt.streams.get_highest_resolution()

            # Generate a filename for the download
            filename = f"{yt.title}.mp4"

            # Download the video (when hosting locally)
            stream.download(output_path=DOWNLOAD_PATH, filename=filename)

            flash(f"Downloaded '{filename}' Successfully!", category='success')

            # If user is authenticated, save the download record
            if current_user.is_authenticated:
                new_item = DownloadedFile(
                    filename=str(yt.title),
                    url=url,
                    user_id=current_user.id
                )
                db.session.add(new_item)
                db.session.commit()

            return redirect(url_for('home'))

        except Exception as err:
            flash(f"An error occurred: {err}", category='danger')
            return redirect(url_for('home'))

    return render_template('index.html', title='Home', form=form)

"""

@app.route('/', methods=['GET', 'POST'])
def home():
    form = URLForm()
    if form.validate_on_submit():
        try:
            url = form.url.data

            # Create YouTube object
            yt = YouTube(url)

            # Get the highest resolution
            stream = yt.streams.get_highest_resolution()

            # Generate a safe filename for the download
            safe_title = "".join([c for c in yt.title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            filename = f"{safe_title}.mp4"

            # Create a BytesIO object to store the video data
            buffer = io.BytesIO()

            # Download the video to the BytesIO object
            stream.stream_to_buffer(buffer)
            buffer.seek(0)

            # If user is authenticated, save the download record
            if current_user.is_authenticated:
                new_item = DownloadedFile(
                    filename=str(yt.title),
                    url=url,
                    user_id=current_user.id
                )
                db.session.add(new_item)
                db.session.commit()

            # Stream the file to the client
            return send_file(
                buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='video/mp4'
            )

        except Exception as err:
            flash(f"An error occurred: {err}", category='danger')
            return redirect(url_for('home'))

    return render_template('index.html', title='Home', form=form)



#
# @app.route('/', methods=['GET', 'POST'])
# def home():
#     form = URLForm()
#     if form.validate_on_submit():
#         try:
#             url = form.url.data
#
#             # Create YouTube object
#             yt = YouTube(url)
#
#             # Get the highest resolution
#             stream = yt.streams.get_highest_resolution()
#
#             # Create a BytesIO object to store the video content
#             buffer = BytesIO()
#             stream.stream_to_buffer(buffer)
#             buffer.seek(0)
#
#             # Generate a filename for the download
#             filename = f"{yt.title}.mp4"
#
#             # If user is authenticated, save the download record
#             if current_user.is_authenticated:
#                 new_item = DownloadedFile(
#                     filename=filename,
#                     url=url,
#                     user_id=current_user.id
#                 )
#                 db.session.add(new_item)
#                 db.session.commit()
#
#             # Stream the file to the client as an attachment
#             return send_file(
#                 buffer,
#                 as_attachment=True,
#                 download_name=filename,
#                 mimetype='video/mp4'
#             )
#
#         except Exception as err:
#             flash(f"An error occurred: {err}", category='danger')
#             return redirect(url_for('home'))
#
#     return render_template('index.html', title='Home', form=form)

"""


@app.route('/download-playlist', methods=['get', 'post'])
def download_playlist():
    form = PlaylistForm()
    if form.validate_on_submit():
        playlist_url = form.url.data
        DOWNLOAD_PATH = (pathlib.Path.home()/"Downloads")
        try:
            playlist = Playlist(playlist_url)

            # Download videos in playlist
            for video in playlist.videos:
                # Create a download stream object
                stream = video.streams.get_highest_resolution()
                # Download playlist into the output folder...
                stream.download(output_path=f"{DOWNLOAD_PATH}/{playlist.title}")
            flash(f"Downloaded '{playlist.title}' Successfully!", category='success')
            return redirect(url_for('home'))
        except Exception as err:
            flash(f"Error Downloading Playlist: {err}", category='danger')
    return render_template('playlist.html', title='Download Playlist', form=form)

"""

"""

@app.route('/download-playlist', methods=['GET', 'POST'])
def download_playlist():
    form = PlaylistForm()
    if form.validate_on_submit():
        playlist_url = form.url.data
        try:
            playlist = Playlist(playlist_url)

            def generate():
                with zipfile.ZipFile(io.BytesIO(), 'w') as zf:
                    for video in playlist.videos:
                        try:
                            stream = video.streams.get_highest_resolution()
                            video_file = io.BytesIO()
                            stream.stream_to_buffer(video_file)
                            video_file.seek(0)
                            
                            # Create a safe filename
                            safe_title = "".join([c for c in video.title if c.isalnum() or c in (' ', '-', '_')]).rstrip()
                            zf.writestr(f"{safe_title}.mp4", video_file.getvalue())
                        except Exception as e:
                            print(f"Error downloading video {video.title}: {str(e)}")
                    
                    zf.seek(0)
                    yield from zf

            response = Response(generate(), mimetype='application/zip')
            response.headers.set('Content-Disposition', 'attachment', filename=f'{playlist.title}.zip')
            return response

        except Exception as err:
            flash(f"Error Downloading Playlist: {err}", category='danger')
    return render_template('playlist.html', title='Download Playlist', form=form)

"""


@app.route('/download-playlist', methods=['GET', 'POST'])
def download_playlist():
    form = PlaylistForm()
    if form.validate_on_submit():
        playlist_url = form.url.data
        try:
            playlist = Playlist(playlist_url)

            def generate():
                for video in playlist.videos:
                    stream = video.streams.get_highest_resolution()
                    buffer = io.BytesIO()
                    stream.stream_to_buffer(buffer)
                    buffer.seek(0)
                    yield buffer.read()

            response = Response(stream_with_context(generate()), 
                                content_type='application/octet-stream')
            response.headers['Content-Disposition'] = f'attachment; filename="{playlist.title}.mp4"'
            return response

        except Exception as err:
            flash(f"Error Downloading Playlist: {err}", category='danger')
    return render_template('playlist.html', title='Download Playlist', form=form)


"""


@app.route('/download-audio', methods=['get', 'post'])
def download_audio():
    form = AudioForm()
    if form.validate_on_submit():
        url = form.url.data
        DOWNLOAD_PATH = (pathlib.Path.home()/"Downloads")
        try:
            yt = YouTube(url)

            # Filter audio stream and download the first one
            audio_stream = yt.streams.filter(only_audio=True, abr="128kbps").first()
            audio_stream.download(output_path=DOWNLOAD_PATH, filename=f"{yt.title}.mp3")

            flash(f"Downloaded {yt.title} Successfully!", category='success')
            return redirect(url_for('home'))
        except Exception as err:
            flash(f"Error Downloading Playlist: {err}", category='danger')
    return render_template('audio.html', title='Download Playlist', form=form)

"""



@app.route('/download-audio', methods=['GET', 'POST'])
def download_audio():
    form = AudioForm()
    if form.validate_on_submit():
        url = form.url.data
        try:
            yt = YouTube(url)

            # Filter audio stream and get the first one
            audio_stream = yt.streams.filter(only_audio=True, abr="256kbps").first()

            # Download the audio stream to a BytesIO object
            buffer = io.BytesIO()
            audio_stream.stream_to_buffer(buffer)
            buffer.seek(0)

            # Generate a safe filename
            safe_title = "".join([c for c in yt.title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            filename = f"{safe_title}.mp3"

            # Send the file as an attachment
            return send_file(
                buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='audio/mpeg'
            )

        except Exception as err:
            flash(f"Error Downloading Audio: {err}", category='danger')

    return render_template('audio.html', title='Download Audio', form=form)


@app.route('/my-downloads')
@login_required
def downloads():
    user_id = current_user.id
    result =db.session.execute(db.select(DownloadedFile).where(DownloadedFile.user_id==user_id))
    downloads = result.scalars().all()
    return render_template('my-downloads.html', title='My Downloads', downloads=downloads)


@app.route('/register', methods=['get', 'post'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email=form.email.data
        passwd = form.password.data
        new_user = User(
            firstname=form.firstname.data,
            lastname=form.lastname.data,
            email=email,
            password=generate_password_hash(passwd, method='scrypt', salt_length=16)
        )
        db.session.add(new_user)
        db.session.commit()
        flash(f"User with email '{email}' created successfully!", category='success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['get', 'post'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        passwd = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data)) 
        user = result.scalar()
        if user:
            email=user.email
            if check_password_hash(user.password, passwd):
                login_user(user)
                flash(f"Welcome {user.firstname} {user.lastname}", category='primary')
                return redirect(url_for('home'))
        flash(f"User with email {email} DOES NOT exist!", category='danger')  
        return redirect(url_for('register'))  
    return render_template('login.html', title='Login', form=form)



@app.route('/logout')
@login_required
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for('home'))


@app.route('/about-us')
def about():
    return render_template('about.html', title='About')


@app.route('/contact-us', methods=['get', 'post'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        title = form.title.data
        msge = form.message.data
        message = msge.replace('<p>',"").replace('</p>',"").replace('<br>',"").replace('</br>',"").replace('<br/>',"")

        #Add message to DB
        new_message = Message(
            name=name,
            email=email,
            title=title,
            message=message
        )
        db.session.add(new_message)
        db.session.commit()

        with smtplib.SMTP(gmail_smtp, port) as connection:
            connection.starttls()
            connection.login(user=my_email, password=email_password)
            connection.sendmail(from_addr=my_email,
                            to_addrs=email,
                            msg=f"Subject:Re: Enquiry Response for {title}"
                                f"\n\nHello {name}, \nWe have received your enquiry/message. \nOur staff will review and revert shortly.\nRegards... \n\nYT-DL Team")
        return redirect(url_for('home'))
    return render_template('contact.html', title='Contact Us', form=form)


if __name__ == "__main__":
    app.run(debug=True, port=8010)



