from collections import Counter
from collections import defaultdict
from fuzzywuzzy import fuzz
import pandas as pd

def load():
    csv_checked = 'data/1000_checked.csv'
    csv_to_check = 'data/1000_to_check.csv'
    df_checked = pd.read_csv(csv_checked).drop('hfr_name', axis=1).rename(
        index=str, columns={'PET_FIRM_NAME': 'name2', 'firm': 'name1'})
    df_to_check = pd.read_csv(csv_to_check).drop('hfr_name', axis=1).rename(
        index=str, columns={'PET_FIRM_NAME': 'name2', 'firm': 'name1'})
    return df_checked, df_to_check


STOP_WORDS = [
    'group', 'gr', 'grp',
    'llc',
    'co',
    'inc'
]


def preprocess(name):
    name = name.lower().replace('.', ' ').replace(',', ' ').replace('&', ' ').strip()
    name = ' '.join([x for x in name.split(' ') if x and x not in STOP_WORDS])
    return name


class Matcher(object):
    def __init__(self):
        pass

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

    def match(self, name, pool, source_firms):
        counter = self.get_counter(source_firms)
        _, keys = self.find_keys(name, counter=counter)
        print('keys: ', keys)

        matches = []
        for key in keys:
            # candidates = [x for x in pool if key in x.lower().split(' ')]
            candidates = [x for x in pool if key in x.lower()] # some spacing may be missing
            print('candidate', candidates)
            scores = [fuzz.partial_ratio(preprocess(name), preprocess(x)) for x in candidates]
            scores_to_names = defaultdict(list)
            for score, candidate in zip(scores, candidates):
                scores_to_names[score].append(candidate)
            print('scores to names', scores_to_names)
            matches.append(sorted(scores_to_names.items(), reverse=True)[0])
        return matches


class MatcherTest(object):
    def __index__(self):
        pass

    def __call__(self, *args, **kwargs):
        df_checked, df_to_check = load()

        matcher = Matcher()
        name = 'Hamer Trading, Inc.'

        # matcher.match(name, pool)


if __name__ == '__main__':
    MatcherTest()()