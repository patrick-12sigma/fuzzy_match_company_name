from uszipcode import SearchEngine

# calc distantce
# TODO: cache results as a table for faster lookup
def get_coord(int_zip):
    search = SearchEngine()
    zipcode = search.by_zipcode(int_zip)
    return dict(lat=zipcode.lat, lng=zipcode.lng)


def get_dist_by_zip(int_zip1, int_zip2):
    """Get distance in miles between the geo-center of two zipcodes"""
    int_zip1, int_zip2 = int(int_zip1), int(int_zip2)
    if int_zip1 == int_zip2:
        return 0
    search = SearchEngine()
    zipcode1 = search.by_zipcode(int_zip1)
    dist = zipcode1.dist_from(**get_coord(int_zip=int_zip2))
    return dist


def get_dist_by_city_state(city1=None, state1=None, city2=None, state2=None):
    if state1.lower() == state2.lower() and city1.lower() == city2.lower():
        return 0
    search = SearchEngine()
    int_zip1_list = sorted([x.zipcode for x in search.by_city_and_state(city=city1, state=state1)])
    int_zip2_list = sorted([x.zipcode for x in search.by_city_and_state(city=city2, state=state2)])
    # randomly select 1 zip
    # print('using zip {} and {}'.format(int_zip1_list[0], int_zip2_list[0]))
    dist = get_dist_by_zip(int_zip1_list[0], int_zip2_list[0])
    return dist


def is_valid(int_zip):
    search = SearchEngine()
    zipcode = search.by_zipcode(int(int_zip))
    if zipcode.zipcode and zipcode.lat and zipcode.lng:
        return True
    else:
        return False


def robust_get_dist(int_zip1=None, int_zip2=None, city1=None, state1=None, city2=None, state2=None):
    search = SearchEngine()
    try:
        if is_valid(int_zip1) and is_valid(int_zip1):
            dist = get_dist_by_zip(int_zip1, int_zip2)
        else:
            dist = get_dist_by_city_state(city1, state1, city2, state2)
    except:
        dist = -1 # invalid value
    return dist


def calc_dist(row):
    """For each row of a df"""
    return robust_get_dist(int_zip1=row['PET_ZIP'], int_zip2=row['zip'],
                           city1=row['PET_CITY'], state1=row['PET_STATE'],
                           city2=row['city'], state2=row['state'])

