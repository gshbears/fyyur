#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import sys
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from models import *
#from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models. - Moved to models.py  
#----------------------------------------------------------------------------#
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  print('venues')
  return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  
  data = []
  locations = Venue.query\
    .with_entities(Venue.city, Venue.state)\
    .distinct().order_by(Venue.city.asc())\
    .order_by(Venue.state.asc())

  for location in locations:
    venues = Venue.query\
      .filter_by(city=location.city, state=location.state)\
      .order_by(Venue.name.desc())

    venue_json = []
    for venue in venues:
      upcoming = Show.query\
        .filter_by(venue_id=venue.id)\
        .filter(Show.start_time>datetime.now())\
        .count()

      venue_json.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": upcoming
      })
    data.append({
      "city" : location.city,
      "state": location.state,
      "venues": venue_json
    }) 

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term=request.form.get('search_term', '')

  venues_found = Venue.query\
    .with_entities(Venue.id, Venue.name)\
    .filter(Venue.name.ilike(f'%{search_term}%'))\
    .all()
  
  data = []

  for venue in venues_found:
    upcoming = Show.query\
      .filter_by(venue_id=venue.id)\
      .filter(Show.start_time>datetime.now())\
      .count()

    data.append({
      "id": venue.id,
      "name": venue.name,
       "num_upcoming_shows": upcoming
    })

  response = {
    "count": len(data),
    "data": data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  pastshows_json = []
  upcoming_json = []
  selvenue = Venue.query.get(venue_id)
  
  past_shows = db.session.query(Show)\
    .join(Venue)\
    .filter(Show.venue_id==venue_id)\
    .filter(Show.start_time<datetime.now())\
    .all() 

  upcoming_shows = db.session.query(Show)\
    .join(Venue)\
    .filter(Show.venue_id==venue_id)\
    .filter(Show.start_time>datetime.now())\
    .all() 

  for show in past_shows:
    pastshows_json.append({
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    })

  for show in upcoming_shows:
    upcoming_json.append({
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    })
  data = {
    "id": selvenue.id,
    "name": selvenue.name,
    "genres": selvenue.genres,
    "address": selvenue.address,
    "city": selvenue.city,
    "state": selvenue.state,
    "phone": selvenue.phone,
    "website": selvenue.website,
    "facebook_link": selvenue.facebook_link,
    "seeking_talent": selvenue.seeking_talent,
    "seeking_description": selvenue.seeking_description,
    "image_link": selvenue.image_link,
    "past_shows": pastshows_json,
    "upcoming_shows": upcoming_json,
    "past_shows_count": len(pastshows_json),
    "upcoming_shows_count": len(upcoming_json),
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()

  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  error = False
  name=request.form['name']
  genres=request.form.getlist('genres')
  address=request.form['address']
  city=request.form['city']
  state=request.form['state']
  phone=request.form['phone']
  website=request.form['website_link']
  facebook_link=request.form['facebook_link']
  seeking_talent= True if 'seeking_talent' in request.form else False
  seeking_description=request.form['seeking_description']
  image_link=request.form['image_link']

  try:
      venue = Venue(
        name=name,
        genres=genres,
        address=address,
        city=city,
        state=state,
        phone=phone,
        website=website,
        facebook_link=facebook_link,
        seeking_talent=seeking_talent,
        seeking_description=seeking_description,
        image_link=image_link
        )
      db.session.add(venue)
      db.session.commit()

  except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()
  if error:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  else:
      flash('Venue ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>/delete', methods=['GET','DELETE'])
def delete_venue(venue_id):
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  error = False
  
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()
    print(sys.exc_info())

  if error:
      flash('An error occurred, Venue :' + venue_id + ' could not be removed.')
  else:
      flash('Venue ' + venue_id + ' was removed successfully!')
  
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = []
  artistlist = Artist.query\
    .with_entities(Artist.id, Artist.name)\
    .order_by(Artist.name.asc())

  for artist in artistlist:
    data.append({
      "id": artist.id,
      "name": artist.name
    })
  
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():

  search_term=request.form.get('search_term', '')

  artists_found = Artist.query\
    .with_entities(Artist.id, Artist.name)\
    .filter(Artist.name.ilike(f'%{search_term}%'))\
    .all()
  
  data = []

  for artist in artists_found:
    upcoming = Show.query\
      .filter_by(artist_id=artist.id)\
      .filter(Show.start_time>datetime.now())\
      .count()

    data.append({
      "id": artist.id,
      "name": artist.name,
       "num_upcoming_shows": upcoming
    })

  response = {
    "count": len(data),
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  pastshows_json = []
  upcoming_json = []
  selartist = Artist.query.get(artist_id)
  
  past_shows = db.session.query(Show)\
    .join(Venue)\
    .filter(Show.artist_id==artist_id)\
    .filter(Show.start_time<datetime.now())\
    .all() 

  upcoming_shows = db.session.query(Show)\
  .join(Venue)\
  .filter(Show.artist_id==artist_id)\
  .filter(Show.start_time>datetime.now())\
  .all() 

  for show in past_shows:
    pastshows_json.append({
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    })

  for show in upcoming_shows:
    upcoming_json.append({
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    })
  
  data = {
    "id": int(selartist.id),
    "name": selartist.name,
    "genres": selartist.genres,
    "city": selartist.city,
    "state": selartist.state,
    "phone": selartist.phone,
    "website": selartist.website,
    "facebook_link": selartist.facebook_link,
    "seeking_venue": selartist.seeking_venue,
    "seeking_description": selartist.seeking_description,
    "image_link": selartist.image_link,
    "past_shows": pastshows_json,
    "upcoming_shows": upcoming_json,
    "past_shows_count": len(pastshows_json),
    "upcoming_shows_count": len(upcoming_json),
  }
 
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  form.name.data=artist.name
  form.genres.data=artist.genres
  form.city.data=artist.city
  form.state.data=artist.state
  form.phone.data=artist.phone
  form.facebook_link.data=artist.facebook_link
  form.image_link.data=artist.image_link
  form.website_link.data=artist.website
  form.seeking_venue.data=artist.seeking_venue
  form.seeking_description.data=artist.seeking_description

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(meta={'csrf': False})
  artist = Artist.query.get(artist_id)
  error = False

  if form.validate_on_submit():
    try:

        artist.name=request.form['name']
        artist.genres=request.form.getlist('genres')
        artist.city=request.form['city']
        artist.state=request.form['state']
        artist.phone=request.form['phone']
        artist.website=request.form['website_link']
        artist.facebook_link=request.form['facebook_link']
        artist.seeking_venue= True if 'seeking_venue' in request.form else False
        artist.seeking_description=request.form['seeking_description']
        artist.image_link=request.form['image_link']

        db.session.commit()

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    else:
        flash('Artist ' + request.form['name'] + ' was updated successfully listed!')   
  else:
    for error in form.errors:
      for msg in form.errors[error]:
        flash(msg)

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  form.name.data=venue.name
  form.city.data=venue.city
  form.state.data=venue.state
  form.address.data=venue.address
  form.phone.data=venue.phone
  form.genres.data=venue.genres
  form.facebook_link.data=venue.facebook_link
  form.image_link.data=venue.image_link
  form.website_link.data=venue.website
  form.seeking_talent.data=venue.seeking_talent
  form.seeking_description.data=venue.seeking_description

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm(meta={'csrf': False})
  venue = Venue.query.get(venue_id)
  error = False

  if form.validate_on_submit():
    try:

        venue.name=request.form['name']
        venue.genres=request.form.getlist('genres')
        venue.city=request.form['city']
        venue.state=request.form['state']
        venue.phone=request.form['phone']
        venue.address=request.form['address']
        venue.website=request.form['website_link']
        venue.facebook_link=request.form['facebook_link']
        venue.seeking_talent= True if 'seeking_talent' in request.form else False
        venue.seeking_description=request.form['seeking_description']
        venue.image_link=request.form['image_link']

        db.session.commit()

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
      db.session.close()
    if error:
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
    else:
        flash('Venue ' + request.form['name'] + ' was updated successfully listed!')
  else:
    for error in form.errors:
      for msg in form.errors[error]:
        flash(msg)
  
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

  # called upon submitting the new artist listing form
  error = False
  name=request.form['name']
  genres=request.form.getlist('genres')
  city=request.form['city']
  state=request.form['state']
  phone=request.form['phone']
  website=request.form['website_link']
  facebook_link=request.form['facebook_link']
  seeking_venue= True if 'seeking_venue' in request.form else False
  seeking_description=request.form['seeking_description']
  image_link=request.form['image_link']

  try:
      artist = Artist(
        name=name,
        genres=genres,
        city=city,
        state=state,
        phone=phone,
        website=request.form['website_link'],
        facebook_link=facebook_link,
        seeking_venue=seeking_venue,
        seeking_description=seeking_description,
        image_link=image_link
        )
      db.session.add(artist)
      db.session.commit()
  except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()
  if error:
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  else:
      flash('Artist ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  shows_list = Show.query\
    .order_by(Show.venue_id.asc())\
    .all()

  data = []
  for show in shows_list:
    data.append({
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    })
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  error = False
  venue_id=request.form['venue_id']
  artist_id=request.form['artist_id']
  start_time=request.form['start_time']

  try:
      show = Show(
        venue_id=venue_id,
        artist_id=artist_id,
        start_time=start_time,
        )
      db.session.add(show)
      db.session.commit()
  except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()
  if error:
      flash('An error occurred. Show could not be listed.')
  else:
      flash('Show was successfully listed!')

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
