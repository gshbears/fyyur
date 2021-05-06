#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import sys
import json
import dateutil.parser
import babel
from flask import (
  Flask,
  render_template,
  request,
  Response,
  flash,
  redirect,
  url_for
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_wtf.csrf import CSRFProtect
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
csrf = CSRFProtect(app)
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
  form = VenueForm(request.form)

  error = False
  if form.validate():
    try:
        venue = Venue()
        form.populate_obj(venue)
        db.session.add(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
    else:
        flash('Venue ' + form.name.data + ' was successfully listed!')
        return render_template('pages/home.html')
  else:
    message = []
    for field, err in form.errors.items():
        message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))

  return render_template('forms/new_venue.html', form=form)

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

  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form)
  artist = Artist.query.get(artist_id)
  error = False

  if form.validate_on_submit():
    try:
        form.populate_obj(artist)
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
    
    return redirect(url_for('show_artist', artist_id=artist_id))
  
  else:
    message = []
    for field, err in form.errors.items():
        message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm(request.form)
  venue = Venue.query.get(venue_id)
  error = False

  if form.validate_on_submit():
    try:
        form.populate_obj(venue)
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
    
    return redirect(url_for('show_venue', venue_id=venue_id))
  
  else:
    message = []
    for field, err in form.errors.items():
        message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))

  return render_template('forms/edit_venue.html', form=form, venue=venue)

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  form = ArtistForm(request.form)

  error = False
  if form.validate():
    try:
        artist = Artist()
        form.populate_obj(artist)
        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
    else:
        flash('Venue ' + form.name.data + ' was successfully listed!')
        return render_template('pages/home.html')
  else:
    message = []
    for field, err in form.errors.items():
        message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))

  return render_template('forms/new_artist.html', form=form)
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
  form = ShowForm(request.form)

  error = False
  if form.validate():
    try:
        show = Show()
        form.populate_obj(show)
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
  else:
    message = []
    for field, err in form.errors.items():
        message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))

  return render_template('forms/new_show.html', form=form)

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
