from numpy import datetime64, timedelta64, argmin, abs
from pandas import DatetimeIndex
from xarray import open_dataset
import datetime

url = 'https://cida.usgs.gov/thredds/dodsC/topowx?crs,lat[0:1:3249],lon[0:1:6999],tmax,time'
start = datetime64('2011-04-01T00:00:00.000000')
end = datetime64('2011-04-02T00:00:00.000000')
north = 46.983861873341404
south = 45.03706878134302
east = -111.48987830262621
west = -114.72694798862337


def get_tmax_data_subset():
    xray = open_dataset(url)

    # find index and value of bounds
    # 1/100 degree adds a small buffer for this 800 m res data
    north_ind = argmin(abs(xray.lat.values - (north + 1.)))
    south_ind = argmin(abs(xray.lat.values - (south - 1.)))
    west_ind = argmin(abs(xray.lon.values - (west - 1.)))
    east_ind = argmin(abs(xray.lon.values - (east + 1.)))

    north_val = xray.lat.values[north_ind]
    south_val = xray.lat.values[south_ind]
    west_val = xray.lon.values[west_ind]
    east_val = xray.lon.values[east_ind]

    subset = xray.loc[dict(time=slice(start, end),
                           lat=slice(north_val, south_val),
                           lon=slice(west_val, east_val))]

    date_ind = DatetimeIndex(['2018-04-01'], dtype='datetime64[ns]', freq='D')
    subset['time'] = date_ind

    try:
        arr = subset.tmax.values
        print('shape of array: {}'.format(arr.shape))
        return arr

    except MemoryError:
        time, time_1, lat, lon = subset['time'], subset['time_1'], subset['lat'], subset['lon']
        print('Memory Error')
        print('dim sizes: time {}, time_1 {}, lat {}, lon {}'.format(
            time.size, time_1.size,
            lat.size, lon.size))
        return None


def days_since_1948():
    now = datetime.datetime.now()
    start = datetime.datetime(1948, 1, 1)
    difference = now - start
    days = difference.days
    print('days since 1948: {}'.format(days))


if __name__ == '__main__':
    get_tmax_data_subset()
    # days_since_1948()
# ========================= EOF ====================================================================
