
from pytube import YouTube, Playlist
import os
from datetime import date, datetime
from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash, check_password_hash
# Import your forms from the forms.py
from forms import  RegisterForm, LoginForm, URLForm, PlaylistForm, ContactForm, AudioForm
from time import sleep
from typing import List
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


NOW = datetime.today().replace(microsecond=0)

class DownloadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(1000), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=NOW)

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

            # Download the video
            stream.download(output_path=DOWNLOAD_PATH)
            if current_user.is_authenticated:
                new_item = DownloadedFile(
                    filename=str(yt.title),
                    url=url,
                    user_id=current_user.id
                )
                db.session.add(new_item)
                db.session.commit()
            flash(f"Downloaded '{yt.title}' Successfully!", category='success')
            return redirect(url_for('home'))
        except Exception as err:
            flash(f"An error occurred: {err}", category='danger')

    return render_template('index.html', title='Home', form=form)


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
    login_user()
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
    app.run(debug=True)



