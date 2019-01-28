from collections import Counter
from collections import defaultdict
from fuzzywuzzy import fuzz
import pandas as pd
from uszipcode import SearchEngine
from tqdm import tqdm

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


def robust_get_dist(int_zip1=None, int_zip2=None, city1=None, state1=None, city2=None, state2=None):
    search = SearchEngine()
    try:
        if search.by_zipcode(int(int_zip1)).zipcode is None or search.by_zipcode(int(int_zip1)).zipcode is None:
            dist = get_dist_by_city_state(city1, state1, city2, state2)
        else:
            dist = get_dist_by_zip(int_zip1, int_zip2)
    except:
        dist = -1 # invalid value
    return dist


def calc_dist(row):
    """For each row of a df"""
    return robust_get_dist(int_zip1=row['PET_ZIP'], int_zip2=row['zip'],
                           city1=row['PET_CITY'], state1=row['PET_STATE'],
                           city2=row['city'], state2=row['state'])


def load_csv_and_process(csv_path):
    df = pd.read_csv(csv_path)
    df = df.drop('hfr_name', axis=1)
    df = df.rename(index=str, columns={'PET_FIRM_NAME': 'name2', 'firm': 'name1'})
    # df['dist'] = df.apply(calc_dist, axis=1)
    return df


def load():
    csv_checked = 'data/1000_checked.csv'
    csv_to_check = 'data/1000_to_check.csv'
    csv_all = 'data/A_to_B.csv'
    df_checked = load_csv_and_process(csv_checked)
    print('loaded df_checked')
    df_to_check = load_csv_and_process(csv_to_check)
    print('loaded df_to_check')
    df_all = load_csv_and_process(csv_all)
    print('loaded df_all')
    return df_checked, df_to_check, df_all


STOP_WORDS = [
    'group', 'gr', 'grp',
    'llc',
    'co',
    'inc',
    'lp'
]


NAME_MAPPER = {
    'management': 'mgt',
    'managements': 'mgt',
}


def preprocess(name):
    name = name.lower().replace('.', ' ').replace(',', ' ').replace('&', ' ').replace('(', ' ').replace(')', ' ').strip()
    fields = []
    for x in name.split(' '):
        if x and x not in STOP_WORDS:
            if x in NAME_MAPPER:
                x = NAME_MAPPER[x]
            fields.append(x)
    name = ' '.join(fields)

    return name


class Matcher(object):
    def __init__(self, all_source_firms, score_thresh=80, dist_thresh=20):
        self.counter = self.get_counter(all_source_firms)
        self.score_thresh = score_thresh
        self.dist_thresh = dist_thresh

    def get_counter(self, source_firms):
        word_list = [w for word in source_firms for w in preprocess(word).split(' ')]
        counter = Counter(word_list)
        return counter

    def find_keys(self, name, counter, most_common=False):
        """Find the least common word in name according to counter"""
        words = preprocess(name).split(' ')
        words = [x for x in words if x and len(x) > 1]
        freq_to_words = defaultdict(list)
        for word in words:
            freq_to_words[counter[word]].append(word)
        if most_common:
            key_count, keys = sorted(freq_to_words.items())[-1]
        else:
            key_count, keys = sorted(freq_to_words.items())[0]
        return key_count, keys

    def postprocess(self, matches):
        """

        :param matches: a list of dict, each dict has score as key and list of matches as val
        :return:
        """
        flat_matches = []
        for match in matches:
            for score, name_list in match.items():
                for name in name_list:
                    flat_matches.append((name, score))
        flat_matches = sorted(list(set(flat_matches)))
        return flat_matches

    def match_once(self, name, pool):
        """Find name in pool, given name in source_firms

        :param name: one element in source_firms
        :param pool: list of tuples (index, name)
        :param all_source_firms:
        :param thresh:
        :return:
        """
        _, keys = self.find_keys(name, counter=self.counter)
        # print('keys {} in name "{}" '.format(keys, name))

        matches = []
        for key in keys:
            # candidates = [x for x in pool if key in x.lower().split(' ')]
            candidates = [x for x in pool if key in x[1].lower()] # some spacing may be missing
            # print('candidate', candidates)
            scores = [fuzz.partial_ratio(preprocess(name), preprocess(x[1])) for x in candidates]
            scores_to_names = defaultdict(list)
            for score, candidate in zip(scores, candidates):
                scores_to_names[score].append(candidate)
            # print('scores to names', scores_to_names)
            filtered_scores_to_names = {k: v for k, v in scores_to_names.items() if k > self.score_thresh}
            matches.append(filtered_scores_to_names)

        matches = self.postprocess(matches)
        return matches

    def process(self, df, output_csv_path=None):
        """Match name in name1 col of df in name2 col

        :param df: has two columns, 'name1' and 'name2'
        :return:
        """

        names_to_match = df['name1'].unique().tolist()
        df_pred = pd.DataFrame()
        for name in tqdm(names_to_match[:]):
            df_pool = df[df['name1'] == name]
            df_pool['dist'] = df_pool.apply(calc_dist, axis=1)
            # df_pool['dist'] = 0

            df_pool = df_pool[df_pool['dist'] <= self.dist_thresh]
            pool = list(df_pool['name2'].items())
            matches = self.match_once(name, pool)
            # print(matches)
            index_list_pred = [x[0][0] for x in matches]
            # print('index_list_pred', index_list_pred)
            df_pred = df_pred.append(df.loc[index_list_pred])
            # print(len(index_list_pred))

        # write to csv
        if output_csv_path is not None:
            df_pred.to_csv(output_csv_path, index_label='index')


class MatcherTest(object):
    def __init__(self):
        pass

    def __call__(self, *args, **kwargs):
        df_checked, df_to_check, df_all = load()
        all_source_firms = df_all['name1'].unique().tolist()
        matcher = Matcher(all_source_firms=all_source_firms)

        output_csv_path = 'data/1000_pred.csv'
        matcher.process(df_to_check, output_csv_path=output_csv_path)


class MatchEvaluator(object):
    def __init__(self):
        pass

    def process(self, names_to_match, df_pred, df_checked):
        for name in names_to_match:
            index_list_pred = df_pred[df_pred['name1'] == name].index.tolist()
            index_list_checked = df_checked[df_checked['name1'] == name].index.tolist()
            index_list_checked = [int(x) for x in index_list_checked]
            if index_list_checked != index_list_pred:
                print('==============', name, '==============')
                print('pred', index_list_pred)
                print('gt', index_list_checked)



class MatchEvaluatorTest(object):
    def __init__(self):
        pass

    def __call__(self, *args, **kwargs):
        csv_pred = 'data/1000_pred.csv'
        df_pred = pd.read_csv(csv_pred, index_col='index')
        df_checked, df_to_check, df_all = load()

        names_to_match = df_to_check['name1'].unique().tolist()
        assert len(names_to_match) == 100

        evaluator = MatchEvaluator()
        evaluator.process(names_to_match, df_pred, df_checked)



if __name__ == '__main__':
    MatcherTest()()
    # MatchEvaluatorTest()()