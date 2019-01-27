from collections import Counter
from collections import defaultdict
import fuzzywuzzy as fuzz
import pandas as pd

def load():
    csv_checked = 'data/1000_checked.csv'
    csv_to_check = 'data/1000_to_check.csv'
    df_checked = pd.read_csv(csv_checked)
    df_to_check = pd.read_csv(csv_to_check)
    return df_checked, df_to_check

class Matcher(object):
    def __init__(self):
        pass

    def preprocess(self, name):
        name = name.lower().replace('.', '').replace(',', '').replace('&', '').strip()
        return name

    def get_counter(self, source_firms):
        word_list = [w for word in source_firms for w in self.preprocess(word).split(' ')]
        counter = Counter(word_list)
        return counter

    def find_keys(self, name, counter, most_common=False):
        """Find the least common word in name according to counter"""
        words = self.preprocess(name).split(' ')
        words = [x for x in words if x and len(x) > 1]
        freq_to_words = defaultdict(list)
        for word in words:
            freq_to_words[counter[word]].append(word)
        if most_common:
            key_count, keys = sorted(freq_to_words.items())[-1]
        else:
            key_count, keys = sorted(freq_to_words.items())[0]
        return key_count, keys

    def match(self, name, pool):
        counter = self.get_counter(source_firms)
        _, keys = self.find_keys(name, counter=counter)
        print('keys: ', keys)

        matches = []
        for key in keys:
            candidates = [x for x in pool if key in x.lower().split(' ')]
            scores = [fuzz.partial_ratio(self.preprocess(name), self.preprocess(x)) for x in candidates]
            scores_to_names = defaultdict(list)
            for score, candidate in zip(scores, candidates):
                scores_to_names[score].append(candidate)
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