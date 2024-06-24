
from pytube import YouTube, Playlist
import os
from datetime import date, datetime
from flask import Flask, abort, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey, desc
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
# Import your forms from the forms.py
from forms import  RegisterForm, LoginForm, URLForm, PlaylistForm
from time import sleep
from typing import List
import pathlib

#from tkinter.filedialog import askdirectory

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Asm_Vsnhjnk354fdncsdnknsjbcac'

app.config['SQLALCHEM_DATABASE_URI'] = 'sqlite:///downloads.db'

Bootstrap5(app)




@app.route('/', methods=['get', 'post'])
def home():
    form = URLForm()
    if form.validate_on_submit():
        try:
            url = form.url.data
            DOWNLOAD_PATH = (pathlib.Path.home()/"Downloads")
            #DOWNLOAD_PATH = str(pathlib.Path.home()/ "Downloads").replace("\\", "/")

            # Create YouTube object
            yt = YouTube(url)

            # Get the highest resolution
            stream = yt.streams.get_highest_resolution()

            # Download the video
            flash(f"Downloading '{yt.title}' ...", category='warning')
            sleep(3)
            stream.download(output_path=DOWNLOAD_PATH)
            flash(f"Downloaded '{yt.title}' Successfully!")

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
                flash(f"Downloaded '{playlist.title}' Successfully!")
        except Exception as err:
            flash(f"Error Downloading Playlist: {err}", category='danger')
    return render_template('playlist.html', title='Download Playlist', form=form)


if __name__ == "__main__":
    app.run(debug=True)



