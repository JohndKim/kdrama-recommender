import pandas as pd  # dataframe library
from sklearn.feature_extraction.text import \
    TfidfVectorizer  # vectorizes the data
from sklearn.metrics.pairwise import \
    cosine_similarity  # finds similarity between vectors

filename = 'kdrama-data/csv/kdrama_data.csv'
# filename = r"C:\Users\John Kim\Desktop\kdrama_data.csv"

label_weights = {
        "keywords": 0.4,    
        "genres": 0.3,
        "actors": 0.2,
        "director": 0.05,
        "screenwriter": 0.05,
    }

df = pd.read_csv(filename)
df = df[['title', 'description', 'keywords', 'genres', 'actors', 'director', 'screenwriter']]

def remove_chars(string):
    if isinstance(string, str) == False:
        return string
    remove_list = ["[", "]", "'"]
    for remove in remove_list:
        string = string.replace(remove, "")
    return string

def get_info(title):
    df = pd.read_csv(filename)
    fill_na()
    index = search_kdrama(title)
    
    row = df.loc[index]
    dicti = row.to_dict()
    # removes unnecessary characters
    columns = ['keywords', 'genres', 'actors']
    for column in columns:
        dicti[column] = remove_chars(dicti[column]) 
    return dicti

def get_desc_word_count(desc):
    word_list = desc.split(' ')
    word_count = len(word_list)
    return word_count

def get_titles():
    np_titles = df['title'].to_numpy()
    title_list = np_titles.tolist()
    return title_list

def kdrama_exists(title, klist):
    if title is None:
        return False
    for kdrama in klist:
        if title.lower() == kdrama.lower(): return True
    return False
    
def fill_na():
    """replaces na values with an empty string"""
    df.replace("N/A", "")
    for label in df.columns:
        df[label] = df[label].fillna('') # fills N/A values with ""

def get_indices():
    indices = pd.Series(df.index, index=df['title'])
    return indices[~indices.index.duplicated(keep='last')]

def og_cos_sim():
    """the similarity scores used to get the initial top x kdramas"""
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['keywords'] + " " + df['genres']
    + " " + df['actors'] + " " + df['director'] + " " + df['screenwriter'])
    return cosine_similarity(tfidf_matrix, tfidf_matrix)

def search_kdrama(kdrama_name):
    """searches for kdrama with matching name and returns top result"""
    # return get_indices()[get_indices().index.str.contains(kdrama_name, regex=False, na=False)][0]
    return get_indices()[get_indices().index.str.contains(kdrama_name.lower(), case=False, regex=False, na=False)][0]



def get_recommended_kdramas(target_kdrama_index, kdrama_similarities, kdramas_df, rec_num):
    """returns the top (rec_num) recommended kdramas based on keywords, genres, actors, director, director
    and screenwriter (we recalculate their similarity score by using our own 'weights' :omg:)"""

    # should set a max on how many recommended kdrama you can get (maybe like 25 or 50?)
    similarity_scores = pd.DataFrame(kdrama_similarities[target_kdrama_index], columns=["score"])
    kdrama_indices = similarity_scores.sort_values("score", ascending=False)[1:rec_num+1].index # gets top 10 (we can change this)
    return kdramas_df['title'].iloc[kdrama_indices].values # converts to array

def get_score(og_name, rec_name, sim):
    """gets the similarity score of a kdrama based on ONE aspect (e.g. only keywords)"""
    rec_index = search_kdrama(rec_name)
    scores = sim[search_kdrama(og_name)]
    return scores[rec_index]

def vectorize_kdrama(col_name):
    """vectorizes the kdrama based on ONE aspect (e.g. only keywords)"""
    tfidf = TfidfVectorizer(stop_words='english')
    return tfidf.fit_transform(df[col_name])

def find_similarity(matrix):
    """finds the similarity between this matrix's kdrama and everything else"""
    return cosine_similarity(matrix, matrix)

def create_similarity_data(name, rec_num):
    """creates a dictionary of arrays with the top 10 similar kdramas"""
    similarity_data = {
        "titles": [],
        "keywords": [],
        "genres": [],
        "actors": [],
        "director": [],
        "screenwriter": [],
    }

    target_index = search_kdrama(name)
    top_ten = get_recommended_kdramas(target_index, og_cos_sim(), df, rec_num).tolist()

    # gets the top 10 for each category


    for label in label_weights.keys():
        if label == "actors": break
        vec = vectorize_kdrama(label)
        sim = find_similarity(vec)
        k_list = get_recommended_kdramas(target_index, sim, df, rec_num)

        for kdrama in k_list:
            if kdrama not in top_ten: top_ten.append(kdrama)

    if name in top_ten: top_ten.remove(name)

    # for every kdrama, calculate weighted score and add to dictionary
    for kdrama in top_ten:
        # adds this title to dictionary
        similarity_data["titles"].append(kdrama)

        for label in label_weights.keys():
            vec = vectorize_kdrama(label)
            sim = find_similarity(vec)
            label_score = get_score(name, kdrama, sim) * label_weights[label]
            # print(label_score)
            similarity_data[label].append(label_score)
    
    return similarity_data

def get_top_rec_kdrama(name, sort_label, rec_num):
    """reorders the top recommended kdramas and converts to a dataframe with
    'link', 'title', 'rank', 'score', 'sim score'"""
    fill_na()

    # if rec_num.isdigit() == False: rec_num = 10
    rec_num = int(rec_num)
    if (rec_num < 5): rec_num = 5
    if (rec_num > 20): rec_num = 20



    data = create_similarity_data(name, rec_num)
    new_df = pd.DataFrame(data)
    new_df['sim_score'] = new_df.sum(axis=1, numeric_only=True)
    new_df = new_df.sort_values("sim_score", ascending=False)
    # print(new_df)
    kdrama_list = new_df['titles'].values.tolist()
    # kdrama_list = kdrama_list[:10]

    # singles out similarity scores, convert to percent and round to 1dp (e.g. 34.3%)
    sim_scores = new_df['sim_score'].reset_index(drop=True)
    sim_scores.loc[:,] *= 100
    sim_scores = sim_scores.round(decimals = 1)

    # sim_scores = sim_scores.iloc[:10]
    # print(kdrama_list)
    # print(sim_scores)

    df = pd.read_csv(filename)
    fill_na()
    df = df[['link', 'title', 'rank', 'score']]

    for kdrama in kdrama_list:
        if kdrama == kdrama_list[0]:
            full_df = df.loc[df['title'] == kdrama]
            continue
        row = df.loc[df['title'] == kdrama]
        full_df = pd.concat([full_df, row], ignore_index=True)


    merged_df = pd.concat([full_df, sim_scores], axis=1, ignore_index=True)
    merged_df.columns = ['link', 'title', 'rank', 'score', 'sim score']

    if sort_label == "rank":
        merged_df = merged_df.sort_values(sort_label, ascending=True)
    else: merged_df = merged_df.sort_values(sort_label, ascending=False)
    merged_df = merged_df.reset_index(drop=True)
    merged_df = merged_df.iloc[:rec_num]

    dicti = merged_df.to_dict()
    return dicti


# get_top_rec_kdrama("Move to Heaven")
# search_kdrama("heaven")

def get_top(name):
    """reorders the top recommended kdramas and converts to a dataframe"""
    fill_na()

    titles_recs = []

    data = create_similarity_data(name, 20)
    new_df = pd.DataFrame(data)
    new_df['sim_score'] = new_df.sum(axis=1, numeric_only=True)
    new_df = new_df.sort_values("sim_score", ascending=False)
    # print(new_df)
    kdrama_list = new_df['titles'].values.tolist()
    # kdrama_list = kdrama_list[:10]

    # singles out similarity scores, convert to percent and round to 1dp (e.g. 34.3%)
    sim_scores = new_df['sim_score'].reset_index(drop=True)
    sim_scores.loc[:,] *= 100
    sim_scores = sim_scores.round(decimals = 1)
    sim_list = sim_scores.tolist()

    if (sim_list[0] == 100):
        titles_recs.append(kdrama_list[1:21])
        titles_recs.append(sim_list[1:21])
    else:
        titles_recs.append(kdrama_list[:20])
        titles_recs.append(sim_list[:20])

    print(titles_recs)
    return titles_recs

def get_rec(title, sort_label, rec_num):
    

    rec_file = 'csv/recs.csv'
    rec_df = pd.read_csv(rec_file)

    index = search_kdrama(title)
    row = rec_df.loc[index]

    recs = row['recommendations']
    sims = row['similarity']
    ranks = []
    scores = []

    for name in recs:
        # get rank, score, and sim score
        index = search_kdrama(name)
        row = df.loc[index]
        ranks.append(row['rank'])
        scores.append(row['score'])

    dictionary = {
        "titles": recs,
        "ranks": ranks,
        "scores": scores,
        "sim scores": sims
    }

    dict_df = pd.DataFrame(dictionary)

    if sort_label == "rank":
        dict_df = dict_df.sort_values(sort_label, ascending=True)
    else: dict_df = dict_df.sort_values(sort_label, ascending=False)
    dict_df = dict_df.reset_index(drop=True)
    dict_df = dict_df.iloc[:rec_num]

    dictionary = dict_df.to_dict()

    return dictionary
