# 1. import all dependencies
from flask import Flask
import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

import datetime as dt

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect=True)
Measurement=Base.classes.measurement
Station=Base.classes.station

# 2. Create an app, being sure to pass __name__
app = Flask(__name__)


# 3. Define what to do when a user hits the index route
@app.route("/")
def home():
    print("Server received request for 'Home' page...")
    return (
        f"Welcome to my 'Home' page!<br>"
        f"Available Route:<br>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<code>&lt;start&gt;</code><br/>"
        f"/api/v1.0/<code>&lt;start&gt;<code>/<code>&lt;end&gt;</code><br/>"
        f"<br>start = input start date in yyyy-mm-dd format<br>"
        f"end = input end date in yyyy-mm-dd format"
    )


# 4. Convert the query results to a dictionary using date as the key and prcp as the value. Return the JSON representation of your dictionary.
@app.route("/api/v1.0/precipitation")
def precipitation():
    #open up session to extract 
    session = Session(engine)
    result1=session.query(Measurement.date, Measurement.prcp).all()
    session.close()
    #create a blank list that will be appended with the result of the above query
    precip_list = []
    for date, precip in result1:
        precip_dict={} #create a blank dictionary to be appended with the above items in a loop
        precip_dict['Date']=date #append the dictionary with the relevant data extracted from the loop
        precip_dict['Precipitation']=precip
        precip_list.append(precip_dict)

    return jsonify(precip_list)

# 5. Return a JSON list of stations from the station dataset.

@app.route("/api/v1.0/stations")
def stations():
    #open up session to extract 
    session = Session(engine)
    result2=session.query(Station.id, Station.station, Station.name, Station.latitude\
        , Station.longitude, Station.elevation).all()
    session.close()
    
    #create a blank list that will be appended with the result of the above query
    station_list = []
    #create a loop to extract all details recorded in the session query above
    for id, station, name,lat,long,elevation in result2:
        station_dict={} #create a blank dictionary to be appended with the above items in a loop
        station_dict['ID']=id #append the dictionary with the relevant data extracted from the loop
        station_dict['Station']=station
        station_dict['Name']=name
        station_dict['Latitude']=lat
        station_dict['Longitude']=long
        station_dict['Elevation']=elevation
        station_list.append(station_dict) #append the station list with the above dictionary

    return jsonify(station_list)

# 6. Query the dates and temperature observations of the most active station for the last year of data. 
# Return a JSON list of temperature observations (TOBS) for the previous year (student: I'm assuming this is requesting for data in the last 12 months since the last datapoint)

@app.route("/api/v1.0/tobs")
def tobs():
    #open up session to extract data from database
    session = Session(engine)
    #determine the active station
    station_count=session.query(Measurement.station,func.count(Measurement.station)).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).all()
    active_station=station_count[0][0] #station USC00519281 appears to be the most active station

    #extract the last date of last datapoint recorded for this station and determine the timepoint (being 365 days before date of final data entry)
    station_time=session.query(Measurement.date).filter(Measurement.station==active_station).order_by(Measurement.date.desc()).first()
    station_year=int(station_time[0][:4])
    station_month=int(station_time[0][5:7])
    station_date=int(station_time[0][8:11])
    timepoint2=dt.date(station_year,station_month, station_date)-dt.timedelta(days=365)
    result3=session.query(Measurement.date, Measurement.tobs).filter(Measurement.station==active_station).filter(Measurement.date>=timepoint2).all()
    session.close()

    #create a blank list that will be appended with the result of the above query
    tobs_list = []
    for date, tobs in result3:
        tobs_dict={} #create a blank dictionary to be appended with the above items in a loop
        tobs_dict['Date']=date #append the dictionary with the relevant data extracted from the loop
        tobs_dict['Tobs']=tobs
        tobs_list.append(tobs_dict)

    return jsonify(tobs_list)

# 7. Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range.
# When given the start only, calculate TMIN, TAVG, and TMAX for all dates greater than and equal to the start date.
# When given the start and the end date, calculate the TMIN, TAVG, and TMAX for dates between the start and end date inclusive.

@app.route("/api/v1.0/<start>")
def start_date(start):
    # Set start and end dates for date range
    startDate = dt.datetime.strptime(start, "%Y-%m-%d")
    endDate = dt.datetime.strptime("2017-08-23", "%Y-%m-%d")

    # Date range
    # Getting date range
    delta = endDate - startDate
    date_range = []
    for i in range(delta.days + 1): #delta.days returns number of days between endDate & startDate. 1 has been added at the end to include the end date
        date_range.append(startDate + dt.timedelta(days=i)) #this loop act as a counter to add 1 day from start date from each loop.

    # Converting the datetime into date alone which can be utilized with filter
    str_date_range = []
    for date in date_range:
        new_date = date.strftime("%Y-%m-%d")
        str_date_range.append(new_date)

    session = Session(engine)

    temp_avg = session.query(func.avg(Measurement.tobs)).filter(Measurement.date.in_(str_date_range)).scalar()
    temp_min = session.query(func.min(Measurement.tobs)).filter(Measurement.date.in_(str_date_range)).scalar()
    temp_max = session.query(func.max(Measurement.tobs)).filter(Measurement.date.in_(str_date_range)).scalar()

    session.close()

    temp_dict = {}
    temp_dict["Average Temperature"] = temp_avg
    temp_dict["Minimum Temperature"] = temp_min
    temp_dict["Maximum Temperature"] = temp_max

    return jsonify(temp_dict)

@app.route("/api/v1.0/<start>/<end>")
def date_2_var(start,end):
    # Set start and end dates for date range
    startDate = dt.datetime.strptime(start, "%Y-%m-%d")
    endDate = dt.datetime.strptime(end, "%Y-%m-%d")

    # Date range
    # Getting date range
    delta = endDate - startDate
    date_range = []
    for i in range(delta.days + 1): #delta.days returns number of days between endDate & startDate. 1 has been added at the end to be inclusive of the end date
        date_range.append(startDate + dt.timedelta(days=i)) #this loop act as a counter to add 1 day from start date from each loop.

    # Converting the datetime into date alone which can be utilized with filter
    str_date_range = []
    for date in date_range:
        new_date = date.strftime("%Y-%m-%d")
        str_date_range.append(new_date)

    session = Session(engine)

    temp_avg = session.query(func.avg(Measurement.tobs)).filter(Measurement.date.in_(str_date_range)).scalar()
    temp_min = session.query(func.min(Measurement.tobs)).filter(Measurement.date.in_(str_date_range)).scalar()
    temp_max = session.query(func.max(Measurement.tobs)).filter(Measurement.date.in_(str_date_range)).scalar()

    session.close()

    temp_dict = {}
    temp_dict["Average Temperature"] = temp_avg
    temp_dict["Minimum Temperature"] = temp_min
    temp_dict["Maximum Temperature"] = temp_max

    return jsonify(temp_dict)

if __name__ == "__main__":
    app.run(debug=True)